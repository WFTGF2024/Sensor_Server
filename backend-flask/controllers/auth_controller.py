"""
Auth Controller - 认证控制器
处理用户注册、登录、登出、资料更新等认证相关操作
"""
from flask import Blueprint, request, jsonify, session, current_app
from services.auth_service import AuthService
from errors import (
    AuthenticationError, ValidationError, AuthorizationError, 
    NotFoundError, ConflictError, ServerError, safe_str
)
from utils.formatters import format_bytes
import re

auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()


def validate_username(username):
    """验证用户名格式"""
    if not username:
        raise ValidationError("用户名不能为空")
    
    username = username.strip()
    
    if len(username) < 3:
        raise ValidationError("用户名至少需要3个字符")
    
    if len(username) > 50:
        raise ValidationError("用户名不能超过50个字符")
    
    # 只允许字母、数字、下划线
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        raise ValidationError("用户名只能包含字母、数字和下划线")
    
    return username


def validate_password(password):
    """验证密码格式"""
    if not password:
        raise ValidationError("密码不能为空")
    
    if len(password) < 6:
        raise ValidationError("密码至少需要6个字符")
    
    if len(password) > 100:
        raise ValidationError("密码不能超过100个字符")
    
    return password


def validate_email(email):
    """验证邮箱格式"""
    if not email:
        return None
    
    email = email.strip()
    
    if len(email) > 100:
        raise ValidationError("邮箱地址过长")
    
    # 简单的邮箱格式验证
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValidationError("邮箱格式不正确")
    
    return email


def validate_phone(phone):
    """验证手机号格式"""
    if not phone:
        return None
    
    phone = phone.strip()
    
    # 简单的手机号验证（中国大陆）
    if not re.match(r'^1[3-9]\d{9}$', phone):
        raise ValidationError("手机号格式不正确")
    
    return phone


def get_current_user_id():
    """获取当前登录用户的ID"""
    if 'user_id' not in session:
        raise AuthenticationError("请先登录")
    return session['user_id']


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    POST /auth/register
    注册新用户

    Required fields: username, password
    Optional fields: email, phone, qq, wechat

    Returns:
        JSON response with user_id and success message
        
    Error Responses:
        400: 参数验证失败
        409: 用户名已存在
        500: 服务器内部错误
    """
    try:
        data = request.get_json()
        if data is None:
            data = {}
        
        # 验证必填字段
        username = data.get('username')
        password = data.get('password')
        
        username = validate_username(username)
        password = validate_password(password)
        
        # 验证可选字段
        email = validate_email(data.get('email'))
        phone = validate_phone(data.get('phone'))
        
        qq = safe_str(data.get('qq'), 'qq', default=None, max_len=20)
        wechat = safe_str(data.get('wechat'), 'wechat', default=None, max_len=50)
        
        # 记录请求信息用于调试（不记录密码）
        current_app.logger.info(f"注册请求: username={username}, email={email}, phone={phone}")

        try:
            result = auth_service.register(
                username=username,
                password=password,
                email=email,
                phone=phone,
                qq=qq,
                wechat=wechat
            )

            # 设置session
            session['user_id'] = result['user_id']
            session['username'] = result['username']
            session.permanent = True

            current_app.logger.info(f"用户注册成功: user_id={result['user_id']}, username={username}")

            return jsonify({
                "success": True,
                "message": "注册成功",
                "user_id": result['user_id'],
                "username": result['username']
            }), 201

        except (ValidationError, ConflictError):
            raise
        except Exception as e:
            current_app.logger.error(f"注册失败: username={username}, error={str(e)}", exc_info=True)
            raise ServerError("注册失败，请稍后重试")

    except ValidationError:
        raise
    except ConflictError:
        raise
    except Exception as e:
        current_app.logger.error(f"注册接口异常: {str(e)}", exc_info=True)
        raise ServerError("注册过程中发生错误")


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    POST /auth/login
    用户登录

    Required fields: username, password

    Returns:
        JSON response with user information
        
    Error Responses:
        400: 参数验证失败
        401: 用户名或密码错误
        500: 服务器内部错误
    """
    try:
        data = request.get_json()
        if data is None:
            data = {}
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            raise ValidationError("用户名和密码不能为空")
        
        username = username.strip()
        
        if not username:
            raise ValidationError("用户名不能为空")

        try:
            user = auth_service.login(
                username=username,
                password=password,
                ip_address=request.remote_addr
            )

            # 设置session
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['is_admin'] = user.get('is_admin', False)
            session.permanent = True

            # 格式化会员信息
            membership = user.get('membership', {})
            if membership:
                membership['storage_used_formatted'] = format_bytes(membership.get('storage_used', 0))
                membership['storage_limit_formatted'] = format_bytes(membership.get('storage_limit', 0))
                membership['max_file_size_formatted'] = format_bytes(membership.get('max_file_size', 0))

            current_app.logger.info(f"用户登录成功: user_id={user['user_id']}, username={username}, ip={request.remote_addr}")

            return jsonify({
                "success": True,
                "message": "登录成功",
                "user": user
            }), 200

        except AuthenticationError:
            raise
        except Exception as e:
            current_app.logger.error(f"登录失败: username={username}, error={str(e)}", exc_info=True)
            raise AuthenticationError("登录失败，请稍后重试")

    except ValidationError:
        raise
    except AuthenticationError:
        raise
    except Exception as e:
        current_app.logger.error(f"登录接口异常: {str(e)}", exc_info=True)
        raise ServerError("登录过程中发生错误")


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    POST /auth/logout
    用户登出

    Returns:
        JSON response with success message
        
    Error Responses:
        401: 未登录
        500: 服务器内部错误
    """
    try:
        if 'user_id' not in session:
            raise AuthenticationError("当前没有登录会话")

        user_id = session['user_id']
        username = session.get('username', 'unknown')
        
        try:
            auth_service.logout(user_id)
        except Exception as e:
            current_app.logger.warning(f"登出服务调用失败: user_id={user_id}, error={str(e)}")

        # 清除session
        session.clear()
        
        current_app.logger.info(f"用户登出成功: user_id={user_id}, username={username}")

        return jsonify({
            "success": True,
            "message": "登出成功"
        }), 200

    except AuthenticationError:
        raise
    except Exception as e:
        current_app.logger.error(f"登出接口异常: {str(e)}", exc_info=True)
        raise ServerError("登出过程中发生错误")


@auth_bp.route('/profile', methods=['PUT'])
def update_profile():
    """
    PUT /auth/profile
    更新用户资料

    Optional fields: email, phone, qq, wechat

    Returns:
        JSON response with updated user information
        
    Error Responses:
        401: 未登录
        400: 参数验证失败
        409: 邮箱或手机号已被使用
        500: 服务器内部错误
    """
    try:
        user_id = get_current_user_id()
        
        data = request.get_json()
        if data is None:
            data = {}
        
        # 验证可选字段
        email = validate_email(data.get('email'))
        phone = validate_phone(data.get('phone'))
        qq = safe_str(data.get('qq'), 'qq', default=None, max_len=20)
        wechat = safe_str(data.get('wechat'), 'wechat', default=None, max_len=50)

        try:
            user = auth_service.update_profile(
                user_id=user_id,
                email=email,
                phone=phone,
                qq=qq,
                wechat=wechat
            )

            # 格式化会员信息
            membership = user.get('membership', {})
            if membership:
                membership['storage_used_formatted'] = format_bytes(membership.get('storage_used', 0))
                membership['storage_limit_formatted'] = format_bytes(membership.get('storage_limit', 0))
                membership['max_file_size_formatted'] = format_bytes(membership.get('max_file_size', 0))

            current_app.logger.info(f"用户资料更新成功: user_id={user_id}")

            return jsonify({
                "success": True,
                "message": "资料更新成功",
                "user": user
            }), 200

        except (ValidationError, ConflictError, NotFoundError):
            raise
        except Exception as e:
            current_app.logger.error(f"资料更新失败: user_id={user_id}, error={str(e)}", exc_info=True)
            raise ServerError("资料更新失败")

    except AuthenticationError:
        raise
    except ValidationError:
        raise
    except ConflictError:
        raise
    except NotFoundError:
        raise
    except Exception as e:
        current_app.logger.error(f"资料更新接口异常: {str(e)}", exc_info=True)
        raise ServerError("更新资料时发生错误")


@auth_bp.route('/password', methods=['PUT'])
def change_password():
    """
    PUT /auth/password
    修改密码

    Required fields: current_password (or old_password), new_password

    Returns:
        JSON response with success message
        
    Error Responses:
        401: 未登录或当前密码错误
        400: 参数验证失败
        500: 服务器内部错误
    """
    try:
        user_id = get_current_user_id()
        
        data = request.get_json()
        if data is None:
            raise ValidationError("请求体不能为空")
        
        # 支持 current_password 和 old_password 两种参数名
        current_password = data.get('current_password') or data.get('old_password')
        if not current_password:
            raise ValidationError("请输入当前密码")
        
        new_password = data.get('new_password')
        new_password = validate_password(new_password)
        
        # 检查新密码不能与旧密码相同
        if current_password == new_password:
            raise ValidationError("新密码不能与当前密码相同")

        try:
            auth_service.change_password(
                user_id=user_id,
                current_password=current_password,
                new_password=new_password
            )

            current_app.logger.info(f"密码修改成功: user_id={user_id}")

            return jsonify({
                "success": True,
                "message": "密码修改成功"
            }), 200

        except AuthenticationError:
            raise
        except ValidationError:
            raise
        except Exception as e:
            current_app.logger.error(f"密码修改失败: user_id={user_id}, error={str(e)}", exc_info=True)
            raise ServerError("密码修改失败")

    except AuthenticationError:
        raise
    except ValidationError:
        raise
    except Exception as e:
        current_app.logger.error(f"密码修改接口异常: {str(e)}", exc_info=True)
        raise ServerError("修改密码时发生错误")


@auth_bp.route('/account', methods=['DELETE'])
def delete_account():
    """
    DELETE /auth/account
    删除账户

    Required fields: password

    Returns:
        JSON response with success message
        
    Error Responses:
        401: 未登录或密码错误
        500: 服务器内部错误
    """
    try:
        user_id = get_current_user_id()
        
        data = request.get_json()
        if data is None:
            raise ValidationError("请求体不能为空")
        
        password = data.get('password')
        if not password:
            raise ValidationError("请输入密码以确认删除")

        try:
            auth_service.delete_account(
                user_id=user_id,
                password=password
            )

            session.clear()
            
            current_app.logger.info(f"账户删除成功: user_id={user_id}")

            return jsonify({
                "success": True,
                "message": "账户已删除"
            }), 200

        except AuthenticationError:
            raise
        except Exception as e:
            current_app.logger.error(f"账户删除失败: user_id={user_id}, error={str(e)}", exc_info=True)
            raise ServerError("账户删除失败")

    except AuthenticationError:
        raise
    except ValidationError:
        raise
    except Exception as e:
        current_app.logger.error(f"账户删除接口异常: {str(e)}", exc_info=True)
        raise ServerError("删除账户时发生错误")


@auth_bp.route('/user', methods=['GET', 'PUT'])
def get_profile():
    """
    GET /auth/user - 获取当前用户资料
    PUT /auth/user - 更新当前用户资料

    Returns:
        JSON response with user information
        
    Error Responses:
        401: 未登录
        404: 用户不存在
        500: 服务器内部错误
    """
    try:
        user_id = get_current_user_id()

        # 处理 PUT 请求（更新用户资料）
        if request.method == 'PUT':
            data = request.get_json()
            if data is None:
                data = {}
            
            # 验证可选字段
            email = validate_email(data.get('email'))
            phone = validate_phone(data.get('phone'))
            qq = safe_str(data.get('qq'), 'qq', default=None, max_len=20)
            wechat = safe_str(data.get('wechat'), 'wechat', default=None, max_len=50)

            try:
                user = auth_service.update_profile(
                    user_id=user_id,
                    email=email,
                    phone=phone,
                    qq=qq,
                    wechat=wechat
                )

                # 格式化会员信息
                membership = user.get('membership', {})
                if membership:
                    membership['storage_used_formatted'] = format_bytes(membership.get('storage_used', 0))
                    membership['storage_limit_formatted'] = format_bytes(membership.get('storage_limit', 0))
                    membership['max_file_size_formatted'] = format_bytes(membership.get('max_file_size', 0))

                current_app.logger.info(f"用户资料更新成功: user_id={user_id}")

                return jsonify({
                    "success": True,
                    "message": "资料更新成功",
                    "user": user
                }), 200

            except (ValidationError, ConflictError, NotFoundError):
                raise
            except Exception as e:
                current_app.logger.error(f"资料更新失败: user_id={user_id}, error={str(e)}", exc_info=True)
                raise ServerError("资料更新失败")

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

        except NotFoundError:
            raise
        except Exception as e:
            current_app.logger.error(f"获取用户资料失败: user_id={user_id}, error={str(e)}", exc_info=True)
            raise ServerError("获取用户资料失败")

    except AuthenticationError:
        raise
    except NotFoundError:
        raise
    except ValidationError:
        raise
    except ConflictError:
        raise
    except Exception as e:
        current_app.logger.error(f"用户资料接口异常: {str(e)}", exc_info=True)
        raise ServerError("处理用户资料时发生错误")


@auth_bp.route('/check-username', methods=['POST'])
def check_username():
    """
    POST /auth/check-username
    检查用户名是否可用

    Required fields: username

    Returns:
        JSON response with availability status
        
    Error Responses:
        400: 参数验证失败
        500: 服务器内部错误
    """
    try:
        data = request.get_json()
        if data is None:
            raise ValidationError("请求体不能为空")
        
        username = data.get('username')
        username = validate_username(username)
        
        try:
            # 尝试检查用户名是否存在
            is_available = auth_service.check_username_available(username)
            
            return jsonify({
                "success": True,
                "available": is_available,
                "message": "用户名可用" if is_available else "用户名已被使用"
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"检查用户名失败: username={username}, error={str(e)}", exc_info=True)
            raise ServerError("检查用户名失败")
            
    except ValidationError:
        raise
    except Exception as e:
        current_app.logger.error(f"检查用户名接口异常: {str(e)}", exc_info=True)
        raise ServerError("检查用户名时发生错误")


@auth_bp.route('/session', methods=['GET'])
def check_session():
    """
    GET /auth/session
    检查当前会话状态

    Returns:
        JSON response with session status
        
    Error Responses:
        401: 未登录
    """
    try:
        if 'user_id' not in session:
            return jsonify({
                "success": False,
                "authenticated": False,
                "message": "未登录"
            }), 200
        
        user_id = session['user_id']
        username = session.get('username', '')
        is_admin = session.get('is_admin', False)
        
        return jsonify({
            "success": True,
            "authenticated": True,
            "user_id": user_id,
            "username": username,
            "is_admin": is_admin
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"检查会话接口异常: {str(e)}", exc_info=True)
        raise ServerError("检查会话时发生错误")
