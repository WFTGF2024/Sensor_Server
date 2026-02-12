"""
Membership Controller - 会员控制器
"""
from flask import Blueprint, jsonify, session
from services.membership_service import MembershipService
from errors import AuthenticationError, ValidationError, NotFoundError, ConflictError
from utils.formatters import format_bytes

membership_bp = Blueprint('membership', __name__, url_prefix='/membership')
membership_service = MembershipService()


@membership_bp.route('/info', methods=['GET'])
def get_membership_info():
    """
    GET /membership/info
    获取当前用户的会员信息
    
    Returns:
        JSON response with membership details
    """
    if 'user_id' not in session:
        raise AuthenticationError("Authentication required")
    
    user_id = session['user_id']
    membership = membership_service.get_user_membership(user_id)
    
    # 格式化存储信息
    membership['storage_used_formatted'] = format_bytes(membership['storage_used'])
    membership['storage_limit_formatted'] = format_bytes(membership['storage_limit'])
    membership['max_file_size_formatted'] = format_bytes(membership['max_file_size'])
    
    return jsonify({
        "success": True,
        "membership": membership
    }), 200


@membership_bp.route('/levels', methods=['GET'])
def list_membership_levels():
    """
    GET /membership/levels
    获取所有会员等级列表
    
    Returns:
        JSON response with all membership levels
    """
    levels = membership_service.get_all_levels()
    
    return jsonify({
        "success": True,
        "levels": levels
    }), 200


@membership_bp.route('/upgrade', methods=['POST'])
def upgrade_membership():
    """
    POST /membership/upgrade
    升级会员
    
    Required fields: level_id, duration_days
    Optional fields: payment_method, transaction_id
    
    Returns:
        JSON response with upgrade result
    """
    if 'user_id' not in session:
        raise AuthenticationError("Authentication required")
    
    user_id = session['user_id']
    data = request.get_json() or {}
    
    try:
        membership = membership_service.upgrade_membership(
            user_id=user_id,
            level_id=data.get('level_id'),
            duration_days=data.get('duration_days'),
            payment_method=data.get('payment_method'),
            transaction_id=data.get('transaction_id')
        )
        
        # 格式化存储信息
        membership['storage_used_formatted'] = format_bytes(membership['storage_used'])
        membership['storage_limit_formatted'] = format_bytes(membership['storage_limit'])
        membership['max_file_size_formatted'] = format_bytes(membership['max_file_size'])
        
        return jsonify({
            "success": True,
            "message": f"会员升级成功，当前等级：{membership['level_name']}",
            "membership": membership
        }), 200
        
    except (ValidationError, NotFoundError) as e:
        raise e


@membership_bp.route('/renew', methods=['POST'])
def renew_membership():
    """
    POST /membership/renew
    续费会员
    
    Required fields: duration_days
    Optional fields: payment_method, transaction_id
    
    Returns:
        JSON response with renewal result
    """
    if 'user_id' not in session:
        raise AuthenticationError("Authentication required")
    
    user_id = session['user_id']
    data = request.get_json() or {}
    
    try:
        membership = membership_service.renew_membership(
            user_id=user_id,
            duration_days=data.get('duration_days'),
            payment_method=data.get('payment_method'),
            transaction_id=data.get('transaction_id')
        )
        
        # 格式化存储信息
        membership['storage_used_formatted'] = format_bytes(membership['storage_used'])
        membership['storage_limit_formatted'] = format_bytes(membership['storage_limit'])
        membership['max_file_size_formatted'] = format_bytes(membership['max_file_size'])
        
        return jsonify({
            "success": True,
            "message": f"会员续费成功，有效期至：{membership['end_date_formatted']}",
            "membership": membership
        }), 200
        
    except ConflictError as e:
        raise e


@membership_bp.route('/storage-stats', methods=['GET'])
def get_storage_stats():
    """
    GET /membership/storage-stats
    获取用户存储统计信息
    
    Returns:
        JSON response with storage statistics
    """
    if 'user_id' not in session:
        raise AuthenticationError("Authentication required")
    
    user_id = session['user_id']
    stats = membership_service.get_storage_stats(user_id)
    
    return jsonify({
        "success": True,
        "stats": stats
    }), 200


@membership_bp.route('/benefits', methods=['GET'])
def get_benefits():
    """
    GET /membership/benefits
    获取当前用户的会员权益详情
    
    Returns:
        JSON response with benefits list
    """
    if 'user_id' not in session:
        raise AuthenticationError("Authentication required")
    
    user_id = session['user_id']
    benefits = membership_service.get_benefits(user_id)
    
    return jsonify({
        "success": True,
        "level_name": benefits['level_name'],
        "level_code": benefits['level_code'],
        "benefits": benefits['benefits']
    }), 200
