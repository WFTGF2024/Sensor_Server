"""
Admin Controller - 管理员控制器
处理管理员相关的用户管理、系统统计等操作
"""
from flask import Blueprint, request, jsonify, session, current_app
from functools import wraps
from services.user_service import UserService
from services.auth_service import AuthService
from errors import (
    AuthenticationError, AuthorizationError, NotFoundError, 
    ValidationError, ServerError, safe_int, safe_str
)
from utils.formatters import format_bytes

admin_bp = Blueprint('admin', __name__)
user_service = UserService()
auth_service = AuthService()


def admin_required(f):
    """
    管理员权限验证装饰器
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查是否登录
        if 'user_id' not in session:
            raise AuthenticationError("请先登录")

        # 检查是否是管理员
        if not session.get('is_admin', False):
            raise AuthorizationError("需要管理员权限")

        return f(*args, **kwargs)
    return decorated_function


def get_current_user_id():
    """获取当前登录用户的ID"""
    if 'user_id' not in session:
        raise AuthenticationError("请先登录")
    return session['user_id']


@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    """
    GET /admin/users
    获取所有用户列表（管理员权限）

    Query Parameters:
        page: 页码（默认1）
        page_size: 每页数量（默认20）
        search: 搜索关键词（可选）

    Returns:
        JSON response with user list and pagination info
        
    Error Responses:
        401: 未登录
        403: 无管理员权限
        500: 服务器内部错误
    """
    try:
        # 获取分页参数
        page = safe_int(request.args.get('page', 1), 'page', default=1, min_val=1)
        page_size = safe_int(request.args.get('page_size', 20), 'page_size', default=20, min_val=1, max_val=100)
        search = safe_str(request.args.get('search', ''), 'search', default='', max_len=100)

        try:
            # 获取用户列表
            users = user_service.get_all_users(include_membership=True)

            # 搜索过滤
            if search:
                search_lower = search.lower()
                users = [u for u in users if
                         search_lower in (u.get('username', '') or '').lower() or
                         search_lower in (u.get('email', '') or '').lower() or
                         search_lower in (u.get('phone', '') or '')]

            # 计算总数
            total = len(users)

            # 分页
            start = (page - 1) * page_size
            end = start + page_size
            users = users[start:end]

            # 格式化用户数据
            for user in users:
                if 'storage_used' in user:
                    user['storage_used_formatted'] = format_bytes(user.get('storage_used', 0))

            return jsonify({
                "success": True,
                "data": {
                    "users": users,
                    "pagination": {
                        "page": page,
                        "page_size": page_size,
                        "total": total,
                        "total_pages": (total + page_size - 1) // page_size if total > 0 else 0
                    }
                }
            }), 200

        except Exception as e:
            current_app.logger.error(f"获取用户列表失败: {str(e)}", exc_info=True)
            raise ServerError("获取用户列表失败")

    except AuthenticationError:
        raise
    except AuthorizationError:
        raise
    except Exception as e:
        current_app.logger.error(f"用户列表接口异常: {str(e)}", exc_info=True)
        raise ServerError("获取用户列表时发生错误")


@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user_detail(user_id):
    """
    GET /admin/users/<user_id>
    获取用户详情（管理员权限）

    Args:
        user_id: 用户ID

    Returns:
        JSON response with user details
        
    Error Responses:
        401: 未登录
        403: 无管理员权限
        404: 用户不存在
        500: 服务器内部错误
    """
    try:
        if user_id <= 0:
            raise ValidationError("无效的用户ID")

        try:
            user = auth_service.get_profile(user_id)

            # 格式化会员信息
            membership = user.get('membership', {})
            if membership:
                membership['storage_used_formatted'] = format_bytes(membership.get('storage_used', 0))
                membership['storage_limit_formatted'] = format_bytes(membership.get('storage_limit', 0))
                membership['max_file_size_formatted'] = format_bytes(membership.get('max_file_size', 0))

            return jsonify({
                "success": True,
                "user": user
            }), 200

        except NotFoundError:
            raise
        except Exception as e:
            current_app.logger.error(f"获取用户详情失败: user_id={user_id}, error={str(e)}", exc_info=True)
            raise ServerError("获取用户详情失败")

    except AuthenticationError:
        raise
    except AuthorizationError:
        raise
    except NotFoundError:
        raise
    except ValidationError:
        raise
    except Exception as e:
        current_app.logger.error(f"用户详情接口异常: {str(e)}", exc_info=True)
        raise ServerError("获取用户详情时发生错误")


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """
    DELETE /admin/users/<user_id>
    删除用户（管理员权限）

    Args:
        user_id: 用户ID

    Returns:
        JSON response with success message
        
    Error Responses:
        401: 未登录
        403: 无管理员权限或尝试删除自己
        404: 用户不存在
        500: 服务器内部错误
    """
    try:
        current_user_id = get_current_user_id()
        
        if user_id <= 0:
            raise ValidationError("无效的用户ID")

        # 不能删除自己
        if user_id == current_user_id:
            raise ValidationError("不能删除自己的账户")

        try:
            auth_service.delete_account(user_id, admin_delete=True)
            
            current_app.logger.info(f"管理员删除用户: admin_id={current_user_id}, deleted_user_id={user_id}")

            return jsonify({
                "success": True,
                "message": "用户已删除"
            }), 200

        except NotFoundError:
            raise
        except Exception as e:
            current_app.logger.error(f"删除用户失败: user_id={user_id}, error={str(e)}", exc_info=True)
            raise ServerError("删除用户失败")

    except AuthenticationError:
        raise
    except AuthorizationError:
        raise
    except NotFoundError:
        raise
    except ValidationError:
        raise
    except Exception as e:
        current_app.logger.error(f"删除用户接口异常: {str(e)}", exc_info=True)
        raise ServerError("删除用户时发生错误")


@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@admin_required
def reset_user_password(user_id):
    """
    POST /admin/users/<user_id>/reset-password
    重置用户密码（管理员权限）

    Args:
        user_id: 用户ID

    Request Body:
        new_password: 新密码

    Returns:
        JSON response with success message
        
    Error Responses:
        401: 未登录
        403: 无管理员权限
        404: 用户不存在
        400: 参数验证失败
        500: 服务器内部错误
    """
    try:
        if user_id <= 0:
            raise ValidationError("无效的用户ID")
        
        data = request.get_json()
        if data is None:
            raise ValidationError("请求体不能为空")
        
        new_password = data.get('new_password')

        if not new_password:
            raise ValidationError("新密码不能为空")

        if len(new_password) < 6:
            raise ValidationError("密码长度至少6位")
        
        if len(new_password) > 100:
            raise ValidationError("密码长度不能超过100位")

        try:
            auth_service.admin_reset_password(user_id, new_password)
            
            current_user_id = get_current_user_id()
            current_app.logger.info(f"管理员重置用户密码: admin_id={current_user_id}, user_id={user_id}")

            return jsonify({
                "success": True,
                "message": "密码已重置"
            }), 200

        except NotFoundError:
            raise
        except Exception as e:
            current_app.logger.error(f"重置密码失败: user_id={user_id}, error={str(e)}", exc_info=True)
            raise ServerError("重置密码失败")

    except AuthenticationError:
        raise
    except AuthorizationError:
        raise
    except NotFoundError:
        raise
    except ValidationError:
        raise
    except Exception as e:
        current_app.logger.error(f"重置密码接口异常: {str(e)}", exc_info=True)
        raise ServerError("重置密码时发生错误")


@admin_bp.route('/stats', methods=['GET'])
@admin_required
def get_stats():
    """
    GET /admin/stats
    获取系统统计数据（管理员权限）

    Returns:
        JSON response with system statistics
        
    Error Responses:
        401: 未登录
        403: 无管理员权限
        500: 服务器内部错误
    """
    try:
        try:
            # 获取用户总数
            total_users = user_service.get_user_count()

            # 获取会员统计
            membership_stats = user_service.get_membership_stats()

            return jsonify({
                "success": True,
                "data": {
                    "total_users": total_users,
                    "membership_stats": membership_stats
                }
            }), 200

        except Exception as e:
            current_app.logger.error(f"获取统计数据失败: {str(e)}", exc_info=True)
            raise ServerError("获取统计数据失败")

    except AuthenticationError:
        raise
    except AuthorizationError:
        raise
    except Exception as e:
        current_app.logger.error(f"统计数据接口异常: {str(e)}", exc_info=True)
        raise ServerError("获取统计数据时发生错误")


@admin_bp.route('/users/<int:user_id>/membership', methods=['PUT'])
@admin_required
def update_user_membership(user_id):
    """
    PUT /admin/users/<user_id>/membership
    更新用户会员等级（管理员权限）

    Args:
        user_id: 用户ID

    Request Body:
        level_id: 会员等级ID
        duration_days: 有效天数（可选，不填则为永久）

    Returns:
        JSON response with success message
        
    Error Responses:
        401: 未登录
        403: 无管理员权限
        404: 用户或会员等级不存在
        400: 参数验证失败
        500: 服务器内部错误
    """
    try:
        if user_id <= 0:
            raise ValidationError("无效的用户ID")
        
        data = request.get_json()
        if data is None:
            raise ValidationError("请求体不能为空")
        
        level_id = data.get('level_id')
        duration_days = data.get('duration_days')

        if not level_id:
            raise ValidationError("会员等级不能为空")
        
        level_id = safe_int(level_id, 'level_id', min_val=1)
        
        if duration_days is not None:
            duration_days = safe_int(duration_days, 'duration_days', min_val=1, max_val=3650)

        try:
            from services.membership_service import MembershipService
            membership_service = MembershipService()
            membership_service.admin_update_membership(user_id, level_id, duration_days)
            
            current_user_id = get_current_user_id()
            current_app.logger.info(f"管理员更新会员等级: admin_id={current_user_id}, user_id={user_id}, level_id={level_id}")

            return jsonify({
                "success": True,
                "message": "会员等级已更新"
            }), 200

        except NotFoundError:
            raise
        except ValidationError:
            raise
        except Exception as e:
            current_app.logger.error(f"更新会员等级失败: user_id={user_id}, error={str(e)}", exc_info=True)
            raise ServerError("更新会员等级失败")

    except AuthenticationError:
        raise
    except AuthorizationError:
        raise
    except NotFoundError:
        raise
    except ValidationError:
        raise
    except Exception as e:
        current_app.logger.error(f"更新会员等级接口异常: {str(e)}", exc_info=True)
        raise ServerError("更新会员等级时发生错误")


@admin_bp.route('/users/<int:user_id>/status', methods=['PUT'])
@admin_required
def update_user_status(user_id):
    """
    PUT /admin/users/<user_id>/status
    更新用户状态（启用/禁用）（管理员权限）

    Args:
        user_id: 用户ID

    Request Body:
        is_active: 是否启用（true/false）

    Returns:
        JSON response with success message
        
    Error Responses:
        401: 未登录
        403: 无管理员权限或尝试禁用自己
        404: 用户不存在
        400: 参数验证失败
        500: 服务器内部错误
    """
    try:
        current_user_id = get_current_user_id()
        
        if user_id <= 0:
            raise ValidationError("无效的用户ID")

        # 不能禁用自己
        if user_id == current_user_id:
            raise ValidationError("不能修改自己的状态")

        data = request.get_json()
        if data is None:
            raise ValidationError("请求体不能为空")
        
        is_active = data.get('is_active')
        if is_active is None:
            raise ValidationError("is_active 参数不能为空")
        
        if not isinstance(is_active, bool):
            # 尝试转换
            if isinstance(is_active, str):
                is_active = is_active.lower() in ('true', '1', 'yes')
            else:
                is_active = bool(is_active)

        try:
            user_service.update_user_status(user_id, is_active)
            
            current_app.logger.info(f"管理员更新用户状态: admin_id={current_user_id}, user_id={user_id}, is_active={is_active}")

            return jsonify({
                "success": True,
                "message": f"用户已{'启用' if is_active else '禁用'}"
            }), 200

        except NotFoundError:
            raise
        except Exception as e:
            current_app.logger.error(f"更新用户状态失败: user_id={user_id}, error={str(e)}", exc_info=True)
            raise ServerError("更新用户状态失败")

    except AuthenticationError:
        raise
    except AuthorizationError:
        raise
    except NotFoundError:
        raise
    except ValidationError:
        raise
    except Exception as e:
        current_app.logger.error(f"更新用户状态接口异常: {str(e)}", exc_info=True)
        raise ServerError("更新用户状态时发生错误")


@admin_bp.route('/users/<int:user_id>/files', methods=['GET'])
@admin_required
def get_user_files(user_id):
    """
    GET /admin/users/<user_id>/files
    获取用户的文件列表（管理员权限）

    Args:
        user_id: 用户ID

    Returns:
        JSON response with user's file list
        
    Error Responses:
        401: 未登录
        403: 无管理员权限
        404: 用户不存在
        500: 服务器内部错误
    """
    try:
        if user_id <= 0:
            raise ValidationError("无效的用户ID")
        
        # 获取分页参数
        page = safe_int(request.args.get('page', 1), 'page', default=1, min_val=1)
        page_size = safe_int(request.args.get('page_size', 20), 'page_size', default=20, min_val=1, max_val=100)

        try:
            from services.file_service import FileService
            file_service = FileService()
            files = file_service.list_files(user_id)
            
            # 分页处理
            total = len(files)
            start = (page - 1) * page_size
            end = start + page_size
            files = files[start:end]

            return jsonify({
                "success": True,
                "files": files,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": (total + page_size - 1) // page_size if total > 0 else 0
                }
            }), 200

        except NotFoundError:
            raise
        except Exception as e:
            current_app.logger.error(f"获取用户文件列表失败: user_id={user_id}, error={str(e)}", exc_info=True)
            raise ServerError("获取用户文件列表失败")

    except AuthenticationError:
        raise
    except AuthorizationError:
        raise
    except NotFoundError:
        raise
    except ValidationError:
        raise
    except Exception as e:
        current_app.logger.error(f"用户文件列表接口异常: {str(e)}", exc_info=True)
        raise ServerError("获取用户文件列表时发生错误")
