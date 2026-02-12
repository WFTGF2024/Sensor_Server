"""
Membership Service - 会员业务逻辑层
"""
from datetime import datetime, timedelta
from repositories.membership_repository import (
    MembershipLevelRepository, UserMembershipRepository,
    MembershipBenefitRepository, MembershipLogRepository
)
from repositories.user_repository import UserRepository
from errors import ValidationError, NotFoundError, ConflictError
from utils.formatters import format_bytes


class MembershipService:
    """会员业务逻辑类"""
    
    def __init__(self):
        self.level_repo = MembershipLevelRepository()
        self.user_membership_repo = UserMembershipRepository()
        self.benefit_repo = MembershipBenefitRepository()
        self.log_repo = MembershipLogRepository()
        self.user_repo = UserRepository()
    
    def get_user_membership(self, user_id: int) -> dict:
        """
        获取用户会员信息

        Args:
            user_id: 用户ID

        Returns:
            会员信息
        """
        membership = self.user_membership_repo.find_active_by_user_id(user_id)

        if not membership:
            # 返回默认免费用户信息
            default_level = self.level_repo.get_default_level()

            # 获取用户实际的文件统计数据
            from repositories.file_repository import FileRepository
            file_repo = FileRepository()
            actual_storage_used = file_repo.get_user_total_size(user_id)
            actual_file_count = file_repo.get_user_file_count(user_id)

            storage_limit = default_level['storage_limit'] if default_level else 1073741824
            max_file_size = default_level['max_file_size'] if default_level else 52428800
            max_file_count = default_level['max_file_count'] if default_level else 100

            # 计算存储使用百分比
            storage_usage_percentage = (actual_storage_used / storage_limit * 100) if storage_limit > 0 else 0

            return {
                'membership_id': None,
                'user_id': user_id,
                'level_id': default_level['level_id'] if default_level else None,
                'level_name': default_level['level_name'] if default_level else '普通用户',
                'level_code': default_level['level_code'] if default_level else 'free',
                'storage_limit': storage_limit,
                'max_file_size': max_file_size,
                'max_file_count': max_file_count,
                'storage_used': actual_storage_used,
                'file_count': actual_file_count,
                'is_storage_full': actual_storage_used >= storage_limit,
                'storage_usage_percentage': round(storage_usage_percentage, 2),
                'start_date': None,
                'end_date': None,
                'end_date_formatted': '永久',
                'is_active': True,
                'download_speed_limit': 0,
                'upload_speed_limit': 0,
                'daily_download_limit': 0,
                'daily_upload_limit': 0,
                'can_share_files': True,  # 普通用户也可以分享文件
                'can_create_public_links': False,
                'priority': 1,
                'points_earned': 0
            }

        return membership
    
    def check_storage_limit(self, user_id: int, file_size: int) -> tuple:
        """
        检查用户存储容量是否足够
        
        Args:
            user_id: 用户ID
            file_size: 文件大小（字节）
            
        Returns:
            (is_allowed: bool, current_used: int, storage_limit: int, message: str)
        """
        membership = self.get_user_membership(user_id)
        current_used = membership.get('storage_used', 0)
        storage_limit = membership.get('storage_limit', 1073741824)
        
        if current_used + file_size > storage_limit:
            used_mb = current_used / (1024 * 1024)
            limit_mb = storage_limit / (1024 * 1024)
            file_mb = file_size / (1024 * 1024)
            return False, current_used, storage_limit, f"存储空间不足。当前使用: {used_mb:.2f}MB，限制: {limit_mb:.2f}MB，需要: {file_mb:.2f}MB"
        
        return True, current_used, storage_limit, "存储空间充足"
    
    def check_file_size_limit(self, user_id: int, file_size: int) -> tuple:
        """
        检查文件大小是否在会员限制内
        
        Args:
            user_id: 用户ID
            file_size: 文件大小（字节）
            
        Returns:
            (is_allowed: bool, max_file_size: int, message: str)
        """
        membership = self.get_user_membership(user_id)
        max_file_size = membership.get('max_file_size', 52428800)
        
        if file_size > max_file_size:
            file_mb = file_size / (1024 * 1024)
            max_mb = max_file_size / (1024 * 1024)
            return False, max_file_size, f"文件大小超过限制。当前文件: {file_mb:.2f}MB，最大允许: {max_mb:.2f}MB"
        
        return True, max_file_size, "文件大小符合要求"
    
    def check_file_count_limit(self, user_id: int) -> tuple:
        """
        检查文件数量是否在会员限制内
        
        Args:
            user_id: 用户ID
            
        Returns:
            (is_allowed: bool, current_count: int, max_count: int, message: str)
        """
        membership = self.get_user_membership(user_id)
        current_count = membership.get('file_count', 0)
        max_count = membership.get('max_file_count', 100)
        
        if current_count >= max_count:
            return False, current_count, max_count, f"文件数量已达到上限。当前: {current_count}个，最大: {max_count}个"
        
        return True, current_count, max_count, "文件数量符合要求"
    
    def get_all_levels(self) -> list:
        """
        获取所有会员等级
        
        Returns:
            会员等级列表
        """
        levels = self.level_repo.get_all_active()
        
        # 格式化存储信息
        for level in levels:
            level['storage_limit_formatted'] = format_bytes(level['storage_limit'])
            level['max_file_size_formatted'] = format_bytes(level['max_file_size'])
        
        return levels
    
    def upgrade_membership(self, user_id: int, level_id: int, duration_days: int,
                          payment_method: str = None, transaction_id: str = None) -> dict:
        """
        升级会员
        
        Args:
            user_id: 用户ID
            level_id: 会员等级ID
            duration_days: 有效期（天），-1表示永久
            payment_method: 支付方式
            transaction_id: 交易ID
            
        Returns:
            升级后的会员信息
            
        Raises:
            NotFoundError: 会员等级不存在
        """
        # 验证会员等级是否存在
        new_level = self.level_repo.find_by_id(level_id)
        if not new_level:
            raise NotFoundError("会员等级不存在")
        
        # 获取当前会员信息
        current_membership = self.get_user_membership(user_id)
        old_level_id = current_membership.get('level_id')
        
        # 计算结束时间
        start_date = datetime.now()
        if duration_days == -1:  # 永久会员
            end_date = None
        else:
            end_date = start_date + timedelta(days=duration_days)
        
        # 更新或创建会员记录
        if current_membership.get('membership_id'):
            # 更新现有会员
            self.user_membership_repo.update(
                current_membership['membership_id'],
                {
                    'level_id': level_id,
                    'start_date': start_date,
                    'end_date': end_date,
                    'is_active': True
                }
            )
        else:
            # 创建新会员记录
            self.user_membership_repo.create(user_id, level_id, start_date, end_date)
        
        # 记录操作日志
        self.log_repo.create(
            user_id=user_id,
            action_type='upgrade',
            action_detail=f'升级到 {new_level["level_name"]} ({new_level["level_code"]})',
            old_level_id=old_level_id,
            new_level_id=level_id,
            operator_id=user_id
        )
        
        # 获取更新后的会员信息
        return self.get_user_membership(user_id)
    
    def renew_membership(self, user_id: int, duration_days: int,
                        payment_method: str = None, transaction_id: str = None) -> dict:
        """
        续费会员
        
        Args:
            user_id: 用户ID
            duration_days: 续费天数
            payment_method: 支付方式
            transaction_id: 交易ID
            
        Returns:
            续费后的会员信息
            
        Raises:
            ConflictError: 没有会员
        """
        # 获取当前会员信息
        current_membership = self.get_user_membership(user_id)
        
        if not current_membership.get('membership_id'):
            raise ConflictError("您还没有会员，请先开通会员")
        
        # 计算新的结束时间
        if current_membership.get('end_date'):
            # 如果是有限期会员，从当前结束时间延长
            new_end_date = current_membership['end_date'] + timedelta(days=duration_days)
            
            # 更新会员结束时间
            self.user_membership_repo.update(
                current_membership['membership_id'],
                {'end_date': new_end_date}
            )
        else:
            # 如果是永久会员，不需要续费
            return current_membership
        
        # 记录操作日志
        self.log_repo.create(
            user_id=user_id,
            action_type='renew',
            action_detail=f'续费 {duration_days} 天',
            new_level_id=current_membership.get('level_id'),
            operator_id=user_id
        )
        
        # 获取更新后的会员信息
        return self.get_user_membership(user_id)
    
    def get_storage_stats(self, user_id: int) -> dict:
        """
        获取用户存储统计信息

        Args:
            user_id: 用户ID

        Returns:
            存储统计信息
        """
        stats = self.user_membership_repo.get_storage_stats(user_id)

        if not stats:
            # 返回默认统计信息，但要基于实际文件数据
            default_level = self.level_repo.get_default_level()

            # 获取用户实际的文件统计数据
            from repositories.file_repository import FileRepository
            file_repo = FileRepository()
            actual_storage_used = file_repo.get_user_total_size(user_id)
            actual_file_count = file_repo.get_user_file_count(user_id)

            storage_limit = default_level['storage_limit'] if default_level else 1073741824
            max_file_size = default_level['max_file_size'] if default_level else 52428800
            max_file_count = default_level['max_file_count'] if default_level else 100

            # 计算存储使用百分比
            storage_usage_percentage = (actual_storage_used / storage_limit * 100) if storage_limit > 0 else 0

            return {
                'storage_used': actual_storage_used,
                'storage_used_formatted': format_bytes(actual_storage_used),
                'storage_limit': storage_limit,
                'storage_limit_formatted': format_bytes(storage_limit),
                'storage_available': storage_limit - actual_storage_used,
                'storage_available_formatted': format_bytes(storage_limit - actual_storage_used),
                'storage_usage_percentage': round(storage_usage_percentage, 2),
                'is_storage_full': actual_storage_used >= storage_limit,
                'file_count': actual_file_count,
                'max_file_count': max_file_count,
                'max_file_size': max_file_size,
                'max_file_size_formatted': format_bytes(max_file_size),
                'level_name': default_level['level_name'] if default_level else '普通用户',
                'level_code': default_level['level_code'] if default_level else 'free',
                'can_share_files': True  # 普通用户也可以分享文件
            }

        # 格式化返回数据
        return {
            'storage_used': stats['storage_used'],
            'storage_used_formatted': format_bytes(stats['storage_used']),
            'storage_limit': stats['storage_limit'],
            'storage_limit_formatted': format_bytes(stats['storage_limit']),
            'storage_available': stats['storage_limit'] - stats['storage_used'],
            'storage_available_formatted': format_bytes(stats['storage_limit'] - stats['storage_used']),
            'storage_usage_percentage': stats['storage_usage_percentage'],
            'is_storage_full': bool(stats['is_storage_full']),
            'file_count': stats['file_count'],
            'max_file_count': stats['max_file_count'],
            'max_file_size': stats['max_file_size'],
            'max_file_size_formatted': format_bytes(stats['max_file_size']),
            'level_name': stats['level_name'],
            'level_code': stats['level_code']
        }
    
    def get_benefits(self, user_id: int) -> dict:
        """
        获取用户会员权益
        
        Args:
            user_id: 用户ID
            
        Returns:
            会员权益信息
        """
        membership = self.get_user_membership(user_id)
        level_id = membership.get('level_id')
        
        benefits = self.benefit_repo.find_by_level_id(level_id)
        
        return {
            'level_name': membership['level_name'],
            'level_code': membership['level_code'],
            'benefits': benefits
        }
