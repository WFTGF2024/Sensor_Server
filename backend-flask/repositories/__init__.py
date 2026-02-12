"""
Repositories package - 数据库接口层
"""

from .user_repository import UserRepository
from .membership_repository import (
    MembershipLevelRepository,
    UserMembershipRepository,
    MembershipBenefitRepository,
    MembershipLogRepository
)
from .file_repository import FileRepository
from .point_repository import PointRecordRepository

# 为了向后兼容，创建别名
MembershipRepository = UserMembershipRepository
PointRepository = PointRecordRepository

__all__ = [
    'UserRepository',
    'MembershipRepository',
    'MembershipLevelRepository',
    'UserMembershipRepository',
    'MembershipBenefitRepository',
    'MembershipLogRepository',
    'FileRepository',
    'PointRepository',
    'PointRecordRepository'
]
