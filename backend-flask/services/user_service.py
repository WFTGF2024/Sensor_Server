"""
User Service - 用户业务逻辑层
"""
from repositories.user_repository import UserRepository
from errors import NotFoundError


class UserService:
    """用户业务逻辑类"""
    
    def __init__(self):
        self.user_repo = UserRepository()
    
    def get_all_users(self, include_membership: bool = False) -> list:
        """
        获取所有用户
        
        Args:
            include_membership: 是否包含会员信息
            
        Returns:
            用户列表
        """
        return self.user_repo.get_all(include_membership=include_membership)
    
    def get_user_count(self) -> int:
        """
        获取用户总数
        
        Returns:
            用户数量
        """
        return self.user_repo.count()
