"""
Membership Repository - 会员数据访问层
"""

import time
from typing import Optional, List, Dict, Any
from datetime import datetime
from db import get_db
from utils import CacheManager, performance_monitor


class MembershipLevelRepository:
    """会员等级仓储类"""
    
    def find_by_id(self, level_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID查找会员等级
        
        Args:
            level_id: 会员等级ID
            
        Returns:
            会员等级字典，不存在返回None
        """
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("""
                SELECT level_id, level_name, level_code, display_order, description,
                       storage_limit, max_file_size, max_file_count,
                       download_speed_limit, upload_speed_limit,
                       daily_download_limit, daily_upload_limit,
                       can_share_files, can_create_public_links,
                       priority, is_active
                FROM membership_levels
                WHERE level_id = ?
            """, (level_id,))
            level = cur.fetchone()
            return dict(level) if level else None
        finally:
            cur.close()
    
    def find_by_code(self, level_code: str) -> Optional[Dict[str, Any]]:
        """
        根据代码查找会员等级
        
        Args:
            level_code: 会员等级代码
            
        Returns:
            会员等级字典，不存在返回None
        """
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("""
                SELECT level_id, level_name, level_code, display_order, description,
                       storage_limit, max_file_size, max_file_count,
                       download_speed_limit, upload_speed_limit,
                       daily_download_limit, daily_upload_limit,
                       can_share_files, can_create_public_links,
                       priority, is_active
                FROM membership_levels
                WHERE level_code = ?
            """, (level_code,))
            level = cur.fetchone()
            return dict(level) if level else None
        finally:
            cur.close()
    
    def get_all_active(self) -> List[Dict[str, Any]]:
        """
        获取所有激活的会员等级
        
        Returns:
            会员等级列表
        """
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("""
                SELECT level_id, level_name, level_code, display_order, description,
                       storage_limit, max_file_size, max_file_count,
                       download_speed_limit, upload_speed_limit,
                       daily_download_limit, daily_upload_limit,
                       can_share_files, can_create_public_links,
                       priority, is_active
                FROM membership_levels
                WHERE is_active = 1
                ORDER BY display_order, priority
            """)
            return [dict(row) for row in cur.fetchall()]
        finally:
            cur.close()
    
    def get_default_level(self) -> Optional[Dict[str, Any]]:
        """
        获取默认会员等级（免费用户）
        
        Returns:
            默认会员等级字典
        """
        return self.find_by_code('free')


class UserMembershipRepository:
    """用户会员关系仓储类"""
    
    def find_active_by_user_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        根据用户ID查找激活的会员
        
        Args:
            user_id: 用户ID
            
        Returns:
            会员信息字典，不存在返回None
        """
        # 尝试从缓存获取
        cached_membership = CacheManager.get_membership(user_id)
        if cached_membership is not None:
            performance_monitor.record_cache_hit("membership", f"membership:{user_id}")
            return cached_membership
        
        performance_monitor.record_cache_miss("membership", f"membership:{user_id}")
        
        # 记录数据库查询开始时间
        start_time = time.time()
        
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("""
                SELECT 
                    um.membership_id, um.user_id, um.level_id,
                    um.start_date, um.end_date, um.is_active,
                    um.storage_used, um.file_count, um.points_earned,
                    ml.level_name, ml.level_code,
                    ml.storage_limit, ml.max_file_size, ml.max_file_count,
                    ml.download_speed_limit, ml.upload_speed_limit,
                    ml.daily_download_limit, ml.daily_upload_limit,
                    ml.can_share_files, ml.can_create_public_links, ml.priority,
                    CASE 
                        WHEN um.end_date IS NULL THEN '永久'
                        ELSE strftime('%Y-%m-%d %H:%M:%S', um.end_date)
                    END AS end_date_formatted,
                    CASE 
                        WHEN um.storage_used >= ml.storage_limit THEN 1
                        ELSE 0
                    END AS is_storage_full,
                    ROUND((um.storage_used * 1.0 / ml.storage_limit) * 100, 2) AS storage_usage_percentage
                FROM user_memberships um
                INNER JOIN membership_levels ml ON um.level_id = ml.level_id
                WHERE um.user_id = ? AND um.is_active = 1
            """, (user_id,))
            membership = cur.fetchone()
            
            # 记录数据库查询性能
            duration = time.time() - start_time
            performance_monitor.record_database_query("select", duration, success=membership is not None)
            
            # 如果找到会员信息，存入缓存
            if membership:
                CacheManager.cache_membership(user_id, membership)
            
            return dict(membership) if membership else None
        finally:
            cur.close()
    
    def create(self, user_id: int, level_id: int, start_date: datetime, 
               end_date: Optional[datetime] = None) -> int:
        """
        创建用户会员记录
        
        Args:
            user_id: 用户ID
            level_id: 会员等级ID
            start_date: 开始时间
            end_date: 结束时间（None表示永久）
            
        Returns:
            新创建的会员记录ID
        """
        # 记录数据库查询开始时间
        start_time = time.time()
        
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("""
                INSERT INTO user_memberships
                (user_id, level_id, start_date, end_date, is_active)
                VALUES (?, ?, ?, ?, 1)
            """, (user_id, level_id, start_date, end_date))
            membership_id = cur.lastrowid
            db.commit()
            
            # 记录数据库查询性能
            duration = time.time() - start_time
            performance_monitor.record_database_query("insert", duration, success=True)
            
            # 使缓存失效
            CacheManager.invalidate_membership(user_id)
            
            return membership_id
        finally:
            cur.close()
    
    def update(self, membership_id: int, membership_data: Dict[str, Any]) -> bool:
        """
        更新会员信息
        
        Args:
            membership_id: 会员记录ID
            membership_data: 要更新的会员数据
            
        Returns:
            是否更新成功
        """
        # 记录数据库查询开始时间
        start_time = time.time()
        
        db = get_db()
        cur = db.cursor()
        try:
            # 构建更新语句
            updates = []
            params = []
            
            if 'level_id' in membership_data:
                updates.append("level_id = ?")
                params.append(membership_data['level_id'])
            
            if 'start_date' in membership_data:
                updates.append("start_date = ?")
                params.append(membership_data['start_date'])
            
            if 'end_date' in membership_data:
                updates.append("end_date = ?")
                params.append(membership_data['end_date'])
            
            if 'is_active' in membership_data:
                updates.append("is_active = ?")
                params.append(1 if membership_data['is_active'] else 0)
            
            if updates:
                params.append(membership_id)
                cur.execute(
                    f"UPDATE user_memberships SET {', '.join(updates)} WHERE membership_id = ?",
                    tuple(params)
                )
                db.commit()
                
                # 记录数据库查询性能
                duration = time.time() - start_time
                performance_monitor.record_database_query("update", duration, success=True)
                
                # 使缓存失效
                cur.execute("SELECT user_id FROM user_memberships WHERE membership_id = ?", (membership_id,))
                result = cur.fetchone()
                if result:
                    CacheManager.invalidate_membership(result['user_id'])
                
                return True
            return False
        finally:
            cur.close()
    
    def update_storage_usage(self, user_id: int, file_size: int, 
                            increment: bool = True) -> bool:
        """
        更新用户存储使用量
        
        Args:
            user_id: 用户ID
            file_size: 文件大小
            increment: 是否增加（True）或减少（False）
            
        Returns:
            是否更新成功
        """
        db = get_db()
        cur = db.cursor()
        try:
            if increment:
                cur.execute("""
                    UPDATE user_memberships
                    SET storage_used = storage_used + ?,
                        file_count = file_count + 1
                    WHERE user_id = ? AND is_active = 1
                """, (file_size, user_id))
            else:
                cur.execute("""
                    UPDATE user_memberships
                    SET storage_used = MAX(0, storage_used - ?),
                        file_count = MAX(0, file_count - 1)
                    WHERE user_id = ? AND is_active = 1
                """, (file_size, user_id))
            db.commit()
            return cur.rowcount > 0
        finally:
            cur.close()
    
    def deactivate_by_user_id(self, user_id: int) -> bool:
        """
        停用用户的会员
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否停用成功
        """
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute(
                "UPDATE user_memberships SET is_active = 0 WHERE user_id = ?",
                (user_id,)
            )
            db.commit()
            return cur.rowcount > 0
        finally:
            cur.close()
    
    def get_storage_stats(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        获取用户存储统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            存储统计字典
        """
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("""
                SELECT 
                    um.user_id,
                    um.level_id,
                    um.storage_used,
                    um.file_count,
                    ml.storage_limit,
                    ml.max_file_size,
                    ml.max_file_count,
                    ml.level_name,
                    ml.level_code,
                    CASE 
                        WHEN um.storage_used >= ml.storage_limit THEN 1
                        ELSE 0
                    END AS is_storage_full,
                    ROUND((um.storage_used * 1.0 / ml.storage_limit) * 100, 2) AS storage_usage_percentage,
                    CASE 
                        WHEN um.end_date IS NULL THEN '永久'
                        ELSE strftime('%Y-%m-%d', um.end_date)
                    END AS membership_end_date,
                    um.is_active AS membership_active
                FROM user_memberships um
                INNER JOIN membership_levels ml ON um.level_id = ml.level_id
                WHERE um.user_id = ? AND um.is_active = 1
            """, (user_id,))
            stats = cur.fetchone()
            return dict(stats) if stats else None
        finally:
            cur.close()


class MembershipBenefitRepository:
    """会员权益仓储类"""
    
    def find_by_level_id(self, level_id: int) -> List[Dict[str, Any]]:
        """
        根据会员等级ID查找权益
        
        Args:
            level_id: 会员等级ID
            
        Returns:
            权益列表
        """
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("""
                SELECT benefit_id, level_id, benefit_type, benefit_value, description, is_active
                FROM membership_benefits
                WHERE level_id = ? AND is_active = 1
                ORDER BY benefit_type
            """, (level_id,))
            return [dict(row) for row in cur.fetchall()]
        finally:
            cur.close()


class MembershipLogRepository:
    """会员操作日志仓储类"""
    
    def create(self, user_id: int, action_type: str, action_detail: str,
               old_level_id: Optional[int] = None, new_level_id: Optional[int] = None,
               operator_id: Optional[int] = None, ip_address: Optional[str] = None) -> int:
        """
        创建会员操作日志
        
        Args:
            user_id: 用户ID
            action_type: 操作类型
            action_detail: 操作详情
            old_level_id: 原会员等级ID
            new_level_id: 新会员等级ID
            operator_id: 操作人ID
            ip_address: IP地址
            
        Returns:
            新创建的日志记录ID
        """
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("""
                INSERT INTO membership_logs
                (user_id, action_type, action_detail, old_level_id, new_level_id, operator_id, ip_address)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, action_type, action_detail, old_level_id, new_level_id, operator_id, ip_address))
            log_id = cur.lastrowid
            db.commit()
            return log_id
        finally:
            cur.close()
    
    def find_recent_by_user_id(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """
        查找用户最近的操作日志
        
        Args:
            user_id: 用户ID
            limit: 返回数量限制
            
        Returns:
            日志列表
        """
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("""
                SELECT log_id, user_id, action_type, action_detail,
                       old_level_id, new_level_id, operator_id, ip_address, created_at
                FROM membership_logs
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, limit))
            return [dict(row) for row in cur.fetchall()]
        finally:
            cur.close()
