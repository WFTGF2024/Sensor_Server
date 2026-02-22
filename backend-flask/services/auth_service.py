"""
Auth Service - 认证业务逻辑层
"""
from werkzeug.security import generate_password_hash, check_password_hash
from repositories.user_repository import UserRepository, LoginStatusRepository
from repositories.membership_repository import UserMembershipRepository, MembershipLevelRepository
from errors import ValidationError, AuthenticationError, ConflictError, NotFoundError
from utils.validators import validate_password_strength, validate_email, validate_phone, validate_username


class AuthService:
    """认证业务逻辑类"""
    
    def __init__(self):
        self.user_repo = UserRepository()
        self.login_status_repo = LoginStatusRepository()
        self.membership_repo = UserMembershipRepository()
        self.level_repo = MembershipLevelRepository()
    
    def register(self, username: str, password: str, email: str = None,
                 phone: str = None, qq: str = None, wechat: str = None) -> dict:
        """
        用户注册
        
        Args:
            username: 用户名
            password: 密码
            email: 邮箱
            phone: 手机号
            qq: QQ号
            wechat: 微信号
            
        Returns:
            注册成功的用户信息
            
        Raises:
            ValidationError: 验证失败
            ConflictError: 用户名/邮箱/手机号已存在
        """
        # 验证用户名
        valid, msg = validate_username(username)
        if not valid:
            raise ValidationError(msg)
        
        # 验证密码强度
        valid, msg = validate_password_strength(password)
        if not valid:
            raise ValidationError(msg)
        
        # 验证邮箱
        valid, msg = validate_email(email)
        if not valid:
            raise ValidationError(msg)
        
        # 验证手机号
        valid, msg = validate_phone(phone)
        if not valid:
            raise ValidationError(msg)
        
        # 检查用户名是否存在
        if self.user_repo.find_by_username(username):
            raise ConflictError(f"用户名 '{username}' 已被占用")
        
        # 检查邮箱是否存在
        if email and self.user_repo.find_by_email(email):
            raise ConflictError(f"邮箱 '{email}' 已被注册")
        
        # 检查手机号是否存在
        if phone and self.user_repo.find_by_phone(phone):
            raise ConflictError(f"手机号 '{phone}' 已被注册")
        
        # 创建用户
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
        user_data = {
            'username': username,
            'password': hashed_pw,
            'email': email,
            'phone': phone,
            'qq': qq,
            'wechat': wechat,
            'point': 0
        }
        user_id = self.user_repo.create(user_data)
        
        # 创建登录状态
        self.login_status_repo.create(user_id, '')
        
        return {
            'user_id': user_id,
            'username': username
        }
    
    def login(self, username: str, password: str, ip_address: str = None) -> dict:
        """
        用户登录
        
        Args:
            username: 用户名
            password: 密码
            ip_address: IP地址
            
        Returns:
            登录成功的用户信息
            
        Raises:
            AuthenticationError: 认证失败
        """
        # 查找用户
        user = self.user_repo.find_by_username(username)
        if not user:
            raise AuthenticationError("用户名或密码错误")
        
        # 验证密码
        if not check_password_hash(user['password'], password):
            raise AuthenticationError("用户名或密码错误")
        
        # 更新登录状态
        self.login_status_repo.create(user['user_id'], ip_address or '')
        
        # 获取会员信息
        membership = self.get_user_membership_info(user['user_id'])
        
        # 返回用户信息（不包含密码）
        user.pop('password', None)
        user['membership'] = membership
        
        return user
    
    def logout(self, user_id: int) -> None:
        """
        用户登出
        
        Args:
            user_id: 用户ID
            
        Raises:
            AuthenticationError: 未登录
        """
        self.login_status_repo.delete_by_user_id(user_id)
    
    def update_profile(self, user_id: int, email: str = None, phone: str = None,
                       qq: str = None, wechat: str = None) -> dict:
        """
        更新用户资料
        
        Args:
            user_id: 用户ID
            email: 邮箱
            phone: 手机号
            qq: QQ号
            wechat: 微信号
            
        Returns:
            更新后的用户信息
            
        Raises:
            ValidationError: 验证失败
            ConflictError: 邮箱/手机号已被其他用户使用
        """
        # 验证邮箱
        valid, msg = validate_email(email)
        if not valid:
            raise ValidationError(msg)
        
        # 验证手机号
        valid, msg = validate_phone(phone)
        if not valid:
            raise ValidationError(msg)
        
        # 检查邮箱冲突
        if email:
            existing = self.user_repo.find_by_email(email)
            if existing and existing['user_id'] != user_id:
                raise ConflictError(f"邮箱 '{email}' 已被其他用户注册")
        
        # 检查手机号冲突
        if phone:
            existing = self.user_repo.find_by_phone(phone)
            if existing and existing['user_id'] != user_id:
                raise ConflictError(f"手机号 '{phone}' 已被其他用户注册")
        
        # 更新用户信息
        user_data = {}
        if email is not None:
            user_data['email'] = email
        if phone is not None:
            user_data['phone'] = phone
        if qq is not None:
            user_data['qq'] = qq
        if wechat is not None:
            user_data['wechat'] = wechat
        
        if user_data:
            self.user_repo.update(user_id, user_data)
        
        # 获取更新后的用户信息
        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise NotFoundError("用户不存在")
        
        # 获取会员信息
        membership = self.get_user_membership_info(user_id)
        user['membership'] = membership
        
        return user
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> None:
        """
        修改密码
        
        Args:
            user_id: 用户ID
            current_password: 当前密码
            new_password: 新密码
            
        Raises:
            ValidationError: 验证失败
            AuthenticationError: 当前密码错误
        """
        # 验证新密码强度
        valid, msg = validate_password_strength(new_password)
        if not valid:
            raise ValidationError(msg)
        
        # 验证当前密码
        user = self.user_repo.find_by_id(user_id)
        if not user or not check_password_hash(user['password'], current_password):
            raise AuthenticationError("当前密码错误")
        
        # 更新密码
        new_hashed = generate_password_hash(new_password, method='pbkdf2:sha256', salt_length=16)
        self.user_repo.update_password(user_id, new_hashed)
    
    def delete_account(self, user_id: int, password: str = None, admin_delete: bool = False) -> None:
        """
        删除账户

        Args:
            user_id: 用户ID
            password: 密码
            admin_delete: 是否是管理员删除

        Raises:
            AuthenticationError: 密码错误
        """
        # 管理员删除不需要验证密码
        if not admin_delete:
            # 验证密码
            user = self.user_repo.find_by_id(user_id)
            if not user or not check_password_hash(user['password'], password):
                raise AuthenticationError("密码错误")

        # 删除登录状态
        self.login_status_repo.delete_by_user_id(user_id)

        # 删除用户
        self.user_repo.delete(user_id)

    def admin_reset_password(self, user_id: int, new_password: str) -> None:
        """
        管理员重置用户密码

        Args:
            user_id: 用户ID
            new_password: 新密码

        Raises:
            NotFoundError: 用户不存在
            ValidationError: 密码验证失败
        """
        # 验证新密码强度
        valid, msg = validate_password_strength(new_password)
        if not valid:
            raise ValidationError(msg)

        # 检查用户是否存在
        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise NotFoundError("用户不存在")

        # 更新密码
        new_hashed = generate_password_hash(new_password, method='pbkdf2:sha256', salt_length=16)
        self.user_repo.update_password(user_id, new_hashed)
    
    def get_profile(self, user_id: int) -> dict:
        """
        获取用户资料
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户信息
            
        Raises:
            NotFoundError: 用户不存在
        """
        user = self.user_repo.find_by_id(user_id)
        if not user:
            raise NotFoundError("用户不存在")
        
        user.pop('password', None)
        
        # 获取会员信息
        membership = self.get_user_membership_info(user_id)
        user['membership'] = membership
        
        return user
    
    def get_user_membership_info(self, user_id: int) -> dict:
        """
        获取用户会员信息

        Args:
            user_id: 用户ID

        Returns:
            会员信息
        """
        membership = self.membership_repo.find_active_by_user_id(user_id)

        if not membership:
            # 返回默认免费用户信息
            default_level = self.level_repo.get_default_level()
            return {
                'level_id': default_level['level_id'] if default_level else None,
                'level_name': default_level['level_name'] if default_level else '普通用户',
                'level_code': default_level['level_code'] if default_level else 'free',
                'storage_used': 0,
                'storage_limit': default_level['storage_limit'] if default_level else 1073741824,
                'file_count': 0,
                'max_file_count': default_level['max_file_count'] if default_level else 100,
                'max_file_size': default_level['max_file_size'] if default_level else 52428800,
                'end_date': None,
                'end_date_formatted': '永久',
                'is_active': True,
                'storage_usage_percentage': 0.0,
                'is_storage_full': False,
                'can_share_files': True  # 普通用户也可以分享文件
            }

        # 格式化返回数据
        return {
            'level_id': membership['level_id'],
            'level_name': membership['level_name'],
            'level_code': membership['level_code'],
            'storage_used': membership['storage_used'],
            'storage_limit': membership['storage_limit'],
            'file_count': membership['file_count'],
            'max_file_count': membership['max_file_count'],
            'max_file_size': membership['max_file_size'],
            'end_date': membership['end_date'],
            'end_date_formatted': membership['end_date_formatted'],
            'is_active': membership['is_active'],
            'storage_usage_percentage': membership['storage_usage_percentage'],
            'is_storage_full': membership['is_storage_full'],
            'can_share_files': membership.get('can_share_files', False)
        }
