"""
User Model - 用户模型
"""
from datetime import datetime
from typing import Optional


class User:
    """用户模型"""
    
    def __init__(self, user_id: Optional[int] = None, username: str = None,
                 password: str = None, email: str = None, phone: str = None,
                 qq: str = None, wechat: str = None, point: int = 0):
        self.user_id = user_id
        self.username = username
        self.password = password
        self.email = email
        self.phone = phone
        self.qq = qq
        self.wechat = wechat
        self.point = point
    
    def to_dict(self, include_password: bool = False) -> dict:
        """转换为字典"""
        data = {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'phone': self.phone,
            'qq': self.qq,
            'wechat': self.wechat,
            'point': self.point
        }
        if include_password:
            data['password'] = self.password
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """从字典创建用户对象"""
        return cls(
            user_id=data.get('user_id'),
            username=data.get('username'),
            password=data.get('password'),
            email=data.get('email'),
            phone=data.get('phone'),
            qq=data.get('qq'),
            wechat=data.get('wechat'),
            point=data.get('point', 0)
        )


class LoginStatus:
    """登录状态模型"""
    
    def __init__(self, user_id: int, login_time: Optional[datetime] = None,
                 ip_address: str = None):
        self.user_id = user_id
        self.login_time = login_time
        self.ip_address = ip_address
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'user_id': self.user_id,
            'login_time': self.login_time.isoformat() if self.login_time else None,
            'ip_address': self.ip_address
        }
