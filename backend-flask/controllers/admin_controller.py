"""
Admin Controller - 管理员控制器
"""
from flask import Blueprint, request, jsonify, session, current_app
from functools import wraps
from services.user_service import UserService
from services.auth_service import AuthService
from errors import AuthenticationError, AuthorizationError, NotFoundError, ValidationError
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
    """
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    search = request.args.get('search', '', type=str)

    # 限制每页最大数量
    page_size = min(page_size, 100)

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
                    "total_pages": (total + page_size - 1) // page_size
                }
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"获取用户列表失败: {str(e)}")
        raise e


@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user_detail(user_id):
    """
    GET /admin/users/<user_id>
    获取用户详情（管理员权限）

    Returns:
        JSON response with user details
    """
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

    except NotFoundError as e:
        raise e


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """
    DELETE /admin/users/<user_id>
    删除用户（管理员权限）

    Returns:
        JSON response with success message
    """
    # 不能删除自己
    if user_id == session.get('user_id'):
        raise ValidationError("不能删除自己的账户")

    try:
        auth_service.delete_account(user_id, admin_delete=True)

        return jsonify({
            "success": True,
            "message": "用户已删除"
        }), 200

    except NotFoundError as e:
        raise e


@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@admin_required
def reset_user_password(user_id):
    """
    POST /admin/users/<user_id>/reset-password
    重置用户密码（管理员权限）

    Request Body:
        new_password: 新密码

    Returns:
        JSON response with success message
    """
    data = request.get_json() or {}
    new_password = data.get('new_password')

    if not new_password:
        raise ValidationError("新密码不能为空")

    if len(new_password) < 6:
        raise ValidationError("密码长度至少6位")

    try:
        auth_service.admin_reset_password(user_id, new_password)

        return jsonify({
            "success": True,
            "message": "密码已重置"
        }), 200

    except NotFoundError as e:
        raise e


@admin_bp.route('/stats', methods=['GET'])
@admin_required
def get_stats():
    """
    GET /admin/stats
    获取系统统计数据（管理员权限）

    Returns:
        JSON response with system statistics
    """
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
        current_app.logger.error(f"获取统计数据失败: {str(e)}")
        raise e


@admin_bp.route('/users/<int:user_id>/membership', methods=['PUT'])
@admin_required
def update_user_membership(user_id):
    """
    PUT /admin/users/<user_id>/membership
    更新用户会员等级（管理员权限）

    Request Body:
        level_id: 会员等级ID
        duration_days: 有效天数（可选，不填则为永久）

    Returns:
        JSON response with success message
    """
    data = request.get_json() or {}
    level_id = data.get('level_id')
    duration_days = data.get('duration_days')

    if not level_id:
        raise ValidationError("会员等级不能为空")

    try:
        from services.membership_service import MembershipService
        membership_service = MembershipService()
        membership_service.admin_update_membership(user_id, level_id, duration_days)

        return jsonify({
            "success": True,
            "message": "会员等级已更新"
        }), 200

    except Exception as e:
        current_app.logger.error(f"更新会员等级失败: {str(e)}")
        raise e
