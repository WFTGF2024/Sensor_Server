"""
Membership Controller - 会员控制器
处理会员信息查询、升级、续费等操作
"""
from flask import Blueprint, request, jsonify, session, current_app
from services.membership_service import MembershipService
from errors import (
    AuthenticationError, ValidationError, NotFoundError, 
    ConflictError, ServerError, safe_int
)
from utils.formatters import format_bytes

membership_bp = Blueprint('membership', __name__, url_prefix='/membership')
membership_service = MembershipService()


def get_current_user_id():
    """获取当前登录用户的ID"""
    if 'user_id' not in session:
        raise AuthenticationError("请先登录")
    return session['user_id']


@membership_bp.route('/info', methods=['GET'])
def get_membership_info():
    """
    GET /membership/info
    获取当前用户的会员信息
    
    Returns:
        JSON response with membership details
        
    Error Responses:
        401: 未登录
        404: 用户不存在
        500: 服务器内部错误
    """
    try:
        user_id = get_current_user_id()
        
        try:
            membership = membership_service.get_user_membership(user_id)
            
            # 格式化存储信息
            membership['storage_used_formatted'] = format_bytes(membership.get('storage_used', 0))
            membership['storage_limit_formatted'] = format_bytes(membership.get('storage_limit', 0))
            membership['max_file_size_formatted'] = format_bytes(membership.get('max_file_size', 0))
            
            return jsonify({
                "success": True,
                "membership": membership
            }), 200
            
        except NotFoundError:
            raise
        except Exception as e:
            current_app.logger.error(f"获取会员信息失败: user_id={user_id}, error={str(e)}", exc_info=True)
            raise ServerError("获取会员信息失败")
            
    except AuthenticationError:
        raise
    except NotFoundError:
        raise
    except Exception as e:
        current_app.logger.error(f"会员信息接口异常: {str(e)}", exc_info=True)
        raise ServerError("获取会员信息时发生错误")


@membership_bp.route('/levels', methods=['GET'])
def list_membership_levels():
    """
    GET /membership/levels
    获取所有会员等级列表
    
    Returns:
        JSON response with all membership levels
        
    Error Responses:
        500: 服务器内部错误
    """
    try:
        try:
            levels = membership_service.get_all_levels()
            
            # 格式化数据
            for level in levels:
                if 'storage_limit' in level:
                    level['storage_limit_formatted'] = format_bytes(level.get('storage_limit', 0))
                if 'max_file_size' in level:
                    level['max_file_size_formatted'] = format_bytes(level.get('max_file_size', 0))
            
            return jsonify({
                "success": True,
                "levels": levels
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"获取会员等级列表失败: error={str(e)}", exc_info=True)
            raise ServerError("获取会员等级列表失败")
            
    except Exception as e:
        current_app.logger.error(f"会员等级列表接口异常: {str(e)}", exc_info=True)
        raise ServerError("获取会员等级列表时发生错误")


@membership_bp.route('/upgrade', methods=['POST'])
def upgrade_membership():
    """
    POST /membership/upgrade
    升级会员
    
    Required fields: level_id
    Optional fields: duration_days, payment_method, transaction_id
    
    Returns:
        JSON response with upgrade result
        
    Error Responses:
        401: 未登录
        404: 会员等级不存在
        400: 参数验证失败
        409: 冲突（如已是该等级）
        500: 服务器内部错误
    """
    try:
        user_id = get_current_user_id()
        
        data = request.get_json()
        if data is None:
            raise ValidationError("请求体不能为空")
        
        level_id = data.get('level_id')
        if not level_id:
            raise ValidationError("会员等级不能为空")
        
        level_id = safe_int(level_id, 'level_id', min_val=1)
        
        duration_days = data.get('duration_days')
        if duration_days is not None:
            duration_days = safe_int(duration_days, 'duration_days', min_val=1, max_val=3650)
        
        payment_method = data.get('payment_method')
        if payment_method and len(str(payment_method)) > 50:
            raise ValidationError("支付方式参数过长")
        
        transaction_id = data.get('transaction_id')
        if transaction_id and len(str(transaction_id)) > 100:
            raise ValidationError("交易ID参数过长")
        
        try:
            membership = membership_service.upgrade_membership(
                user_id=user_id,
                level_id=level_id,
                duration_days=duration_days,
                payment_method=payment_method,
                transaction_id=transaction_id
            )
            
            # 格式化存储信息
            membership['storage_used_formatted'] = format_bytes(membership.get('storage_used', 0))
            membership['storage_limit_formatted'] = format_bytes(membership.get('storage_limit', 0))
            membership['max_file_size_formatted'] = format_bytes(membership.get('max_file_size', 0))
            
            current_app.logger.info(f"会员升级成功: user_id={user_id}, level_id={level_id}")
            
            return jsonify({
                "success": True,
                "message": f"会员升级成功，当前等级：{membership.get('level_name', '未知')}",
                "membership": membership
            }), 200
            
        except (ValidationError, NotFoundError, ConflictError):
            raise
        except Exception as e:
            current_app.logger.error(f"会员升级失败: user_id={user_id}, error={str(e)}", exc_info=True)
            raise ServerError("会员升级失败")
            
    except AuthenticationError:
        raise
    except ValidationError:
        raise
    except NotFoundError:
        raise
    except ConflictError:
        raise
    except Exception as e:
        current_app.logger.error(f"会员升级接口异常: {str(e)}", exc_info=True)
        raise ServerError("会员升级时发生错误")


@membership_bp.route('/renew', methods=['POST'])
def renew_membership():
    """
    POST /membership/renew
    续费会员
    
    Required fields: duration_days
    Optional fields: payment_method, transaction_id
    
    Returns:
        JSON response with renewal result
        
    Error Responses:
        401: 未登录
        400: 参数验证失败
        409: 冲突（如非会员无法续费）
        500: 服务器内部错误
    """
    try:
        user_id = get_current_user_id()
        
        data = request.get_json()
        if data is None:
            raise ValidationError("请求体不能为空")
        
        duration_days = data.get('duration_days')
        if not duration_days:
            raise ValidationError("续费天数不能为空")
        
        duration_days = safe_int(duration_days, 'duration_days', min_val=1, max_val=3650)
        
        payment_method = data.get('payment_method')
        if payment_method and len(str(payment_method)) > 50:
            raise ValidationError("支付方式参数过长")
        
        transaction_id = data.get('transaction_id')
        if transaction_id and len(str(transaction_id)) > 100:
            raise ValidationError("交易ID参数过长")
        
        try:
            membership = membership_service.renew_membership(
                user_id=user_id,
                duration_days=duration_days,
                payment_method=payment_method,
                transaction_id=transaction_id
            )
            
            # 格式化存储信息
            membership['storage_used_formatted'] = format_bytes(membership.get('storage_used', 0))
            membership['storage_limit_formatted'] = format_bytes(membership.get('storage_limit', 0))
            membership['max_file_size_formatted'] = format_bytes(membership.get('max_file_size', 0))
            
            current_app.logger.info(f"会员续费成功: user_id={user_id}, duration_days={duration_days}")
            
            return jsonify({
                "success": True,
                "message": f"会员续费成功，有效期至：{membership.get('end_date_formatted', '未知')}",
                "membership": membership
            }), 200
            
        except (ValidationError, ConflictError):
            raise
        except Exception as e:
            current_app.logger.error(f"会员续费失败: user_id={user_id}, error={str(e)}", exc_info=True)
            raise ServerError("会员续费失败")
            
    except AuthenticationError:
        raise
    except ValidationError:
        raise
    except ConflictError:
        raise
    except Exception as e:
        current_app.logger.error(f"会员续费接口异常: {str(e)}", exc_info=True)
        raise ServerError("会员续费时发生错误")


@membership_bp.route('/storage-stats', methods=['GET'])
def get_storage_stats():
    """
    GET /membership/storage-stats
    获取用户存储统计信息
    
    Returns:
        JSON response with storage statistics
        
    Error Responses:
        401: 未登录
        500: 服务器内部错误
    """
    try:
        user_id = get_current_user_id()
        
        try:
            stats = membership_service.get_storage_stats(user_id)
            
            # 格式化数据
            if 'storage_used' in stats:
                stats['storage_used_formatted'] = format_bytes(stats.get('storage_used', 0))
            if 'storage_limit' in stats:
                stats['storage_limit_formatted'] = format_bytes(stats.get('storage_limit', 0))
            
            return jsonify({
                "success": True,
                "stats": stats
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"获取存储统计失败: user_id={user_id}, error={str(e)}", exc_info=True)
            raise ServerError("获取存储统计失败")
            
    except AuthenticationError:
        raise
    except Exception as e:
        current_app.logger.error(f"存储统计接口异常: {str(e)}", exc_info=True)
        raise ServerError("获取存储统计时发生错误")


@membership_bp.route('/benefits', methods=['GET'])
def get_benefits():
    """
    GET /membership/benefits
    获取当前用户的会员权益详情
    
    Returns:
        JSON response with benefits list
        
    Error Responses:
        401: 未登录
        500: 服务器内部错误
    """
    try:
        user_id = get_current_user_id()
        
        try:
            benefits = membership_service.get_benefits(user_id)
            
            return jsonify({
                "success": True,
                "level_name": benefits.get('level_name', '普通用户'),
                "level_code": benefits.get('level_code', 'free'),
                "benefits": benefits.get('benefits', [])
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"获取会员权益失败: user_id={user_id}, error={str(e)}", exc_info=True)
            raise ServerError("获取会员权益失败")
            
    except AuthenticationError:
        raise
    except Exception as e:
        current_app.logger.error(f"会员权益接口异常: {str(e)}", exc_info=True)
        raise ServerError("获取会员权益时发生错误")


@membership_bp.route('/history', methods=['GET'])
def get_membership_history():
    """
    GET /membership/history
    获取会员变更历史
    
    Query Parameters:
        page: 页码（默认1）
        page_size: 每页数量（默认20）
    
    Returns:
        JSON response with membership history
        
    Error Responses:
        401: 未登录
        500: 服务器内部错误
    """
    try:
        user_id = get_current_user_id()
        
        # 获取分页参数
        page = safe_int(request.args.get('page', 1), 'page', default=1, min_val=1)
        page_size = safe_int(request.args.get('page_size', 20), 'page_size', default=20, min_val=1, max_val=100)
        
        try:
            history = membership_service.get_membership_history(user_id)
            
            # 分页处理
            total = len(history)
            start = (page - 1) * page_size
            end = start + page_size
            history = history[start:end]
            
            return jsonify({
                "success": True,
                "history": history,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": (total + page_size - 1) // page_size if total > 0 else 0
                }
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"获取会员历史失败: user_id={user_id}, error={str(e)}", exc_info=True)
            raise ServerError("获取会员历史失败")
            
    except AuthenticationError:
        raise
    except Exception as e:
        current_app.logger.error(f"会员历史接口异常: {str(e)}", exc_info=True)
        raise ServerError("获取会员历史时发生错误")


@membership_bp.route('/cancel', methods=['POST'])
def cancel_membership():
    """
    POST /membership/cancel
    取消会员（取消自动续费）
    
    Returns:
        JSON response with cancellation result
        
    Error Responses:
        401: 未登录
        400: 当前无会员
        500: 服务器内部错误
    """
    try:
        user_id = get_current_user_id()
        
        try:
            result = membership_service.cancel_auto_renew(user_id)
            
            current_app.logger.info(f"取消会员自动续费: user_id={user_id}")
            
            return jsonify({
                "success": True,
                "message": "已取消自动续费",
                "membership": result
            }), 200
            
        except ValidationError:
            raise
        except Exception as e:
            current_app.logger.error(f"取消会员失败: user_id={user_id}, error={str(e)}", exc_info=True)
            raise ServerError("取消会员失败")
            
    except AuthenticationError:
        raise
    except ValidationError:
        raise
    except Exception as e:
        current_app.logger.error(f"取消会员接口异常: {str(e)}", exc_info=True)
        raise ServerError("取消会员时发生错误")
