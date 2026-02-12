"""
Point Repository - 积分数据访问层
"""

from typing import Optional, List, Dict, Any
from db import get_db


class PointRecordRepository:
    """积分记录仓储类"""
    
    def create(self, user_id: int, points_change: int, points_after: int,
               change_type: str, description: str, related_id: Optional[int] = None) -> int:
        """
        创建积分记录
        
        Args:
            user_id: 用户ID
            points_change: 积分变化（正数为增加，负数为减少）
            points_after: 变化后的积分余额
            change_type: 变化类型
            description: 描述
            related_id: 关联ID（可选）
            
        Returns:
            新创建的记录ID
        """
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("""
                INSERT INTO point_records
                (user_id, points_change, points_after, change_type, description, related_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, points_change, points_after, change_type, description, related_id))
            record_id = cur.lastrowid
            db.commit()
            return record_id
        finally:
            cur.close()
    
    def find_by_user_id(self, user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """
        查找用户的积分记录
        
        Args:
            user_id: 用户ID
            limit: 返回数量限制
            
        Returns:
            积分记录列表
        """
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("""
                SELECT record_id, user_id, points_change, points_after, change_type, description, related_id, created_at
                FROM point_records
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, limit))
            return [dict(row) for row in cur.fetchall()]
        finally:
            cur.close()
    
    def find_by_type(self, user_id: int, change_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        根据变化类型查找积分记录
        
        Args:
            user_id: 用户ID
            change_type: 变化类型
            limit: 返回数量限制
            
        Returns:
            积分记录列表
        """
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("""
                SELECT record_id, user_id, points_change, points_after, change_type, description, related_id, created_at
                FROM point_records
                WHERE user_id = ? AND change_type = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, change_type, limit))
            return [dict(row) for row in cur.fetchall()]
        finally:
            cur.close()
    
    def get_total_points_by_type(self, user_id: int, change_type: str) -> int:
        """
        获取用户某类型的积分总额
        
        Args:
            user_id: 用户ID
            change_type: 变化类型
            
        Returns:
            积分总额
        """
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("""
                SELECT COALESCE(SUM(points_change), 0) as total_points
                FROM point_records
                WHERE user_id = ? AND change_type = ?
            """, (user_id, change_type))
            result = cur.fetchone()
            return result['total_points'] if result else 0
        finally:
            cur.close()
