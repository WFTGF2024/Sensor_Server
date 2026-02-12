"""
Point Model - 积分模型
"""
from datetime import datetime
from typing import Optional


class PointRecord:
    """积分记录模型"""
    
    def __init__(self, record_id: int = None, user_id: int = None,
                 points_change: int = 0, points_after: int = 0,
                 change_type: str = None, description: str = None,
                 related_id: Optional[int] = None, created_at: Optional[datetime] = None):
        self.record_id = record_id
        self.user_id = user_id
        self.points_change = points_change
        self.points_after = points_after
        self.change_type = change_type
        self.description = description
        self.related_id = related_id
        self.created_at = created_at
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'record_id': self.record_id,
            'user_id': self.user_id,
            'points_change': self.points_change,
            'points_after': self.points_after,
            'change_type': self.change_type,
            'description': self.description,
            'related_id': self.related_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
