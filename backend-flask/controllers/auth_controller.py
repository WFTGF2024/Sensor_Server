"""
Auth Controller - 认证控制器
"""
from flask import Blueprint, request, jsonify, session
from services.auth_service import AuthService
from errors import AuthenticationError, ValidationError, AuthorizationError, NotFoundError, ConflictError
from utils.formatters import format_bytes

auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    POST /auth/register
    注册新用户
    
    Required fields: username, password
    Optional fields: email, phone, qq, wechat
    
    Returns:
        JSON response with user_id and success message
    """
    data = request.get_json() or {}
    
    try:
        result = auth_service.register(
            username=data.get('username'),
            password=data.get('password'),
            email=data.get('email'),
            phone=data.get('phone'),
            qq=data.get('qq'),
            wechat=data.get('wechat')
        )

        # 设置session
        session['user_id'] = result['user_id']
        session['username'] = result['username']
        session.permanent = True  # 设置为永久会话，有效期由 PERMANENT_SESSION_LIFETIME 控制

        return jsonify({
            "success": True,
            "message": "User registered successfully",
            "user_id": result['user_id'],
            "username": result['username']
        }), 201
        
    except (ValidationError, AuthenticationError, ConflictError) as e:
        raise e


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    POST /auth/login
    用户登录
    
    Required fields: username, password
    
    Returns:
        JSON response with user information
    """
    data = request.get_json() or {}
    
    try:
        user = auth_service.login(
            username=data.get('username'),
            password=data.get('password'),
            ip_address=request.remote_addr
        )

        # 设置session
        session['user_id'] = user['user_id']
        session['username'] = user['username']
        session.permanent = True  # 设置为永久会话，有效期由 PERMANENT_SESSION_LIFETIME 控制

        # 格式化会员信息
        membership = user.get('membership', {})
        if membership:
            membership['storage_used_formatted'] = format_bytes(membership.get('storage_used', 0))
            membership['storage_limit_formatted'] = format_bytes(membership.get('storage_limit', 0))
            membership['max_file_size_formatted'] = format_bytes(membership.get('max_file_size', 0))
        
        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": user
        }), 200
        
    except AuthenticationError as e:
        raise e


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    POST /auth/logout
    用户登出
    
    Returns:
        JSON response with success message
    """
    if 'user_id' not in session:
        raise AuthenticationError("No active session to logout from")
    
    user_id = session['user_id']
    auth_service.logout(user_id)
    
    # 清除session
    session.clear()
    
    return jsonify({
        "success": True,
        "message": "Logout successful"
    }), 200


@auth_bp.route('/profile', methods=['PUT'])
def update_profile():
    """
    PUT /auth/profile
    更新用户资料
    
    Optional fields: email, phone, qq, wechat
    
    Returns:
        JSON response with updated user information
    """
    if 'user_id' not in session:
        raise AuthenticationError("Authentication required")
    
    user_id = session['user_id']
    data = request.get_json() or {}
    
    try:
        user = auth_service.update_profile(
            user_id=user_id,
            email=data.get('email'),
            phone=data.get('phone'),
            qq=data.get('qq'),
            wechat=data.get('wechat')
        )
        
        # 格式化会员信息
        membership = user.get('membership', {})
        if membership:
            membership['storage_used_formatted'] = format_bytes(membership.get('storage_used', 0))
            membership['storage_limit_formatted'] = format_bytes(membership.get('storage_limit', 0))
            membership['max_file_size_formatted'] = format_bytes(membership.get('max_file_size', 0))
        
        return jsonify({
            "success": True,
            "message": "Profile updated successfully",
            "user": user
        }), 200
        
    except (ValidationError, ConflictError, NotFoundError) as e:
        raise e


@auth_bp.route('/password', methods=['PUT'])
def change_password():
    """
    PUT /auth/password
    修改密码

    Required fields: current_password (or old_password), new_password

    Returns:
        JSON response with success message
    """
    if 'user_id' not in session:
        raise AuthenticationError("Authentication required")

    user_id = session['user_id']
    data = request.get_json() or {}

    try:
        # 支持 current_password 和 old_password 两种参数名
        current_password = data.get('current_password') or data.get('old_password')
        if not current_password:
            raise ValidationError("Current password is required")

        auth_service.change_password(
            user_id=user_id,
            current_password=current_password,
            new_password=data.get('new_password')
        )

        return jsonify({
            "success": True,
            "message": "Password changed successfully"
        }), 200

    except (ValidationError, AuthenticationError) as e:
        raise e


@auth_bp.route('/account', methods=['DELETE'])
def delete_account():
    """
    DELETE /auth/account
    删除账户
    
    Required fields: password
    
    Returns:
        JSON response with success message
    """
    if 'user_id' not in session:
        raise AuthenticationError("Authentication required")
    
    user_id = session['user_id']
    data = request.get_json() or {}
    
    try:
        auth_service.delete_account(
            user_id=user_id,
            password=data.get('password')
        )
        
        session.clear()
        
        return jsonify({
            "success": True,
            "message": "Account deleted successfully"
        }), 200
        
    except AuthenticationError as e:
        raise e


@auth_bp.route('/user', methods=['GET', 'PUT'])
def get_profile():
    """
    GET /auth/user - 获取当前用户资料
    PUT /auth/user - 更新当前用户资料

    Returns:
        JSON response with user information
    """
    if 'user_id' not in session:
        raise AuthenticationError("Authentication required")

    user_id = session['user_id']

    # 处理 PUT 请求（更新用户资料）
    if request.method == 'PUT':
        data = request.get_json() or {}

        try:
            user = auth_service.update_profile(
                user_id=user_id,
                email=data.get('email'),
                phone=data.get('phone'),
                qq=data.get('qq'),
                wechat=data.get('wechat')
            )

            # 格式化会员信息
            membership = user.get('membership', {})
            if membership:
                membership['storage_used_formatted'] = format_bytes(membership.get('storage_used', 0))
                membership['storage_limit_formatted'] = format_bytes(membership.get('storage_limit', 0))
                membership['max_file_size_formatted'] = format_bytes(membership.get('max_file_size', 0))

            return jsonify({
                "success": True,
                "message": "Profile updated successfully",
                "user": user
            }), 200

        except (ValidationError, ConflictError, NotFoundError) as e:
            raise e

    # 处理 GET 请求（获取用户资料）
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
