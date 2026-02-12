"""
Membership Model - 会员模型
"""
from datetime import datetime
from typing import Optional


class MembershipLevel:
    """会员等级模型"""
    
    def __init__(self, level_id: int = None, level_name: str = None,
                 level_code: str = None, display_order: int = None,
                 description: str = None, storage_limit: int = None,
                 max_file_size: int = None, max_file_count: int = None,
                 download_speed_limit: int = None, upload_speed_limit: int = None,
                 daily_download_limit: int = None, daily_upload_limit: int = None,
                 can_share_files: bool = False, can_create_public_links: bool = False,
                 priority: int = 1, is_active: bool = True):
        self.level_id = level_id
        self.level_name = level_name
        self.level_code = level_code
        self.display_order = display_order
        self.description = description
        self.storage_limit = storage_limit
        self.max_file_size = max_file_size
        self.max_file_count = max_file_count
        self.download_speed_limit = download_speed_limit
        self.upload_speed_limit = upload_speed_limit
        self.daily_download_limit = daily_download_limit
        self.daily_upload_limit = daily_upload_limit
        self.can_share_files = can_share_files
        self.can_create_public_links = can_create_public_links
        self.priority = priority
        self.is_active = is_active
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'level_id': self.level_id,
            'level_name': self.level_name,
            'level_code': self.level_code,
            'display_order': self.display_order,
            'description': self.description,
            'storage_limit': self.storage_limit,
            'max_file_size': self.max_file_size,
            'max_file_count': self.max_file_count,
            'download_speed_limit': self.download_speed_limit,
            'upload_speed_limit': self.upload_speed_limit,
            'daily_download_limit': self.daily_download_limit,
            'daily_upload_limit': self.daily_upload_limit,
            'can_share_files': self.can_share_files,
            'can_create_public_links': self.can_create_public_links,
            'priority': self.priority,
            'is_active': self.is_active
        }


class UserMembership:
    """用户会员关系模型"""
    
    def __init__(self, membership_id: int = None, user_id: int = None,
                 level_id: int = None, start_date: Optional[datetime] = None,
                 end_date: Optional[datetime] = None, is_active: bool = True,
                 storage_used: int = 0, file_count: int = 0, points_earned: int = 0):
        self.membership_id = membership_id
        self.user_id = user_id
        self.level_id = level_id
        self.start_date = start_date
        self.end_date = end_date
        self.is_active = is_active
        self.storage_used = storage_used
        self.file_count = file_count
        self.points_earned = points_earned
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'membership_id': self.membership_id,
            'user_id': self.user_id,
            'level_id': self.level_id,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_active': self.is_active,
            'storage_used': self.storage_used,
            'file_count': self.file_count,
            'points_earned': self.points_earned
        }


class MembershipBenefit:
    """会员权益模型"""
    
    def __init__(self, benefit_id: int = None, level_id: int = None,
                 benefit_type: str = None, benefit_value: str = None,
                 description: str = None, is_active: bool = True):
        self.benefit_id = benefit_id
        self.level_id = level_id
        self.benefit_type = benefit_type
        self.benefit_value = benefit_value
        self.description = description
        self.is_active = is_active
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'benefit_id': self.benefit_id,
            'level_id': self.level_id,
            'benefit_type': self.benefit_type,
            'benefit_value': self.benefit_value,
            'description': self.description,
            'is_active': self.is_active
        }


class MembershipLog:
    """会员操作日志模型"""
    
    def __init__(self, log_id: int = None, user_id: int = None,
                 action_type: str = None, action_detail: str = None,
                 old_level_id: Optional[int] = None, new_level_id: Optional[int] = None,
                 operator_id: Optional[int] = None, ip_address: str = None,
                 created_at: Optional[datetime] = None):
        self.log_id = log_id
        self.user_id = user_id
        self.action_type = action_type
        self.action_detail = action_detail
        self.old_level_id = old_level_id
        self.new_level_id = new_level_id
        self.operator_id = operator_id
        self.ip_address = ip_address
        self.created_at = created_at
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'log_id': self.log_id,
            'user_id': self.user_id,
            'action_type': self.action_type,
            'action_detail': self.action_detail,
            'old_level_id': self.old_level_id,
            'new_level_id': self.new_level_id,
            'operator_id': self.operator_id,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
