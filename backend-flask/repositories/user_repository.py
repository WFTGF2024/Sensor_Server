"""
User Repository - 用户数据访问层
"""

import time
from typing import Optional, List, Dict, Any
from datetime import datetime
from db import get_db
from utils import CacheManager, performance_monitor


class UserRepository:
    """用户数据访问类"""

    def find_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID查找用户

        Args:
            user_id: 用户ID

        Returns:
            用户字典，不存在返回None
        """
        # 尝试从缓存获取
        cached_user = CacheManager.get_user(user_id)
        if cached_user is not None:
            performance_monitor.record_cache_hit("user", f"user:{user_id}")
            return cached_user

        performance_monitor.record_cache_miss("user", f"user:{user_id}")

        # 记录数据库查询开始时间
        start_time = time.time()

        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("""
                SELECT user_id, username, password, email, phone, qq, wechat, is_admin
                FROM users
                WHERE user_id = ?
            """, (user_id,))
            user = cur.fetchone()

            # 记录数据库查询性能
            duration = time.time() - start_time
            performance_monitor.record_database_query("select", duration, success=user is not None)

            # 如果找到用户，存入缓存
            if user:
                # 转换为字典
                user_dict = dict(user)
                # 不缓存密码
                user_for_cache = user_dict.copy()
                if 'password' in user_for_cache:
                    del user_for_cache['password']
                CacheManager.cache_user(user_id, user_for_cache)

            return dict(user) if user else None
        finally:
            cur.close()

    def find_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        根据用户名查找用户

        Args:
            username: 用户名

        Returns:
            用户字典，不存在返回None
        """
        # 记录数据库查询开始时间
        start_time = time.time()

        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("""
                SELECT user_id, username, password, email, phone, qq, wechat, is_admin
                FROM users
                WHERE username = ?
            """, (username,))
            user = cur.fetchone()

            # 记录数据库查询性能
            duration = time.time() - start_time
            performance_monitor.record_database_query("select", duration, success=user is not None)

            return dict(user) if user else None
        finally:
            cur.close()

    def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        根据邮箱查找用户

        Args:
            email: 邮箱

        Returns:
            用户字典，不存在返回None
        """
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("""
                SELECT user_id, username, password, email, phone, qq, wechat
                FROM users
                WHERE email = ?
            """, (email,))
            user = cur.fetchone()
            return dict(user) if user else None
        finally:
            cur.close()

    def find_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """
        根据手机号查找用户

        Args:
            phone: 手机号

        Returns:
            用户字典，不存在返回None
        """
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("""
                SELECT user_id, username, password, email, phone, qq, wechat
                FROM users
                WHERE phone = ?
            """, (phone,))
            user = cur.fetchone()
            return dict(user) if user else None
        finally:
            cur.close()

    def create(self, user_data: Dict[str, Any]) -> int:
        """
        创建新用户

        Args:
            user_data: 用户数据字典

        Returns:
            新创建的用户ID
        """
        # 记录数据库查询开始时间
        start_time = time.time()

        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("""
                INSERT INTO users
                (username, password, email, phone, qq, wechat)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_data['username'],
                user_data['password'],
                user_data.get('email'),
                user_data.get('phone'),
                user_data.get('qq'),
                user_data.get('wechat')
            ))
            user_id = cur.lastrowid
            db.commit()

            # 记录数据库查询性能
            duration = time.time() - start_time
            performance_monitor.record_database_query("insert", duration, success=True)

            return user_id
        finally:
            cur.close()

    def update(self, user_id: int, user_data: Dict[str, Any]) -> bool:
        """
        更新用户信息

        Args:
            user_id: 用户ID
            user_data: 要更新的用户数据

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

            for field in ['email', 'phone', 'qq', 'wechat']:
                if field in user_data:
                    updates.append(f"{field} = ?")
                    params.append(user_data[field])

            if updates:
                params.append(user_id)
                cur.execute(
                    f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?",
                    tuple(params)
                )
                db.commit()

                # 记录数据库查询性能
                duration = time.time() - start_time
                success = cur.rowcount > 0
                performance_monitor.record_database_query("update", duration, success)

                # 如果更新成功，使缓存失效
                if success:
                    CacheManager.invalidate_user(user_id)

                return success
            return False
        finally:
            cur.close()

    def update_password(self, user_id: int, password_hash: str) -> bool:
        """
        更新用户密码

        Args:
            user_id: 用户ID
            password_hash: 密码哈希值

        Returns:
            是否更新成功
        """
        # 记录数据库查询开始时间
        start_time = time.time()

        db = get_db()
        cur = db.cursor()
        try:
            cur.execute(
                "UPDATE users SET password = ? WHERE user_id = ?",
                (password_hash, user_id)
            )
            db.commit()

            # 记录数据库查询性能
            duration = time.time() - start_time
            success = cur.rowcount > 0
            performance_monitor.record_database_query("update", duration, success)

            # 如果更新成功，使缓存失效
            if success:
                CacheManager.invalidate_user(user_id)

            return success
        finally:
            cur.close()

    def update_points(self, user_id: int, points: int) -> bool:
        """
        更新用户积分

        Args:
            user_id: 用户ID
            points: 积分值

        Returns:
            是否更新成功
        """
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute(
                "UPDATE users SET point = ? WHERE user_id = ?",
                (points, user_id)
            )
            db.commit()
            return cur.rowcount > 0
        finally:
            cur.close()

    def delete(self, user_id: int) -> bool:
        """
        删除用户

        Args:
            user_id: 用户ID

        Returns:
            是否删除成功
        """
        # 记录数据库查询开始时间
        start_time = time.time()

        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            db.commit()

            # 记录数据库查询性能
            duration = time.time() - start_time
            success = cur.rowcount > 0
            performance_monitor.record_database_query("delete", duration, success)

            # 如果删除成功，使缓存失效
            if success:
                CacheManager.invalidate_user(user_id)

            return success
        finally:
            cur.close()

    def get_all(self, include_membership: bool = False) -> List[Dict[str, Any]]:
        """
        获取所有用户

        Args:
            include_membership: 是否包含会员信息

        Returns:
            用户列表
        """
        db = get_db()
        cur = db.cursor()
        try:
            if include_membership:
                cur.execute("""
                    SELECT
                        u.user_id, u.username, u.email, u.phone, u.qq, u.wechat,
                        ml.level_name, ml.level_code,
                        um.storage_used, um.file_count,
                        CASE
                            WHEN um.end_date IS NULL THEN '永久'
                            ELSE strftime('%Y-%m-%d', um.end_date)
                        END AS membership_end_date
                    FROM users u
                    LEFT JOIN user_memberships um ON u.user_id = um.user_id AND um.is_active = 1
                    LEFT JOIN membership_levels ml ON um.level_id = ml.level_id
                    ORDER BY u.user_id
                """)
            else:
                cur.execute("""
                    SELECT user_id, username, email, phone, qq, wechat
                    FROM users
                    ORDER BY user_id
                """)
            return [dict(row) for row in cur.fetchall()]
        finally:
            cur.close()

    def count(self) -> int:
        """
        获取用户总数

        Returns:
            用户数量
        """
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("SELECT COUNT(*) as count FROM users")
            result = cur.fetchone()
            return result['count'] if result else 0
        finally:
            cur.close()

    def get_membership_stats(self) -> dict:
        """
        获取会员统计信息

        Returns:
            会员统计信息
        """
        db = get_db()
        cur = db.cursor()
        try:
            # 按会员等级统计用户数
            cur.execute("""
                SELECT
                    ml.level_name,
                    ml.level_code,
                    COUNT(um.user_id) as user_count
                FROM membership_levels ml
                LEFT JOIN user_memberships um ON ml.level_id = um.level_id AND um.is_active = 1
                GROUP BY ml.level_id
                ORDER BY ml.display_order
            """)
            level_stats = [dict(row) for row in cur.fetchall()]

            # 获取总存储使用量
            cur.execute("""
                SELECT COALESCE(SUM(storage_used), 0) as total_storage
                FROM user_memberships
                WHERE is_active = 1
            """)
            total_storage = cur.fetchone()['total_storage']

            return {
                'level_stats': level_stats,
                'total_storage': total_storage
            }
        finally:
            cur.close()


class LoginStatusRepository:
    """登录状态仓储类"""

    def create(self, user_id: int, ip_address: str) -> bool:
        """
        创建登录状态记录

        Args:
            user_id: 用户ID
            ip_address: IP地址

        Returns:
            是否创建成功
        """
        db = get_db()
        cur = db.cursor()
        try:
            # SQLite 不支持 ON DUPLICATE KEY UPDATE，使用 INSERT OR REPLACE
            cur.execute("""
                INSERT OR REPLACE INTO user_login_status (user_id, login_time, ip_address)
                VALUES (?, datetime('now'), ?)
            """, (user_id, ip_address))
            db.commit()
            return True
        finally:
            cur.close()

    def delete_by_user_id(self, user_id: int) -> bool:
        """
        删除用户的登录状态

        Args:
            user_id: 用户ID

        Returns:
            是否删除成功
        """
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute(
                "DELETE FROM user_login_status WHERE user_id = ?",
                (user_id,)
            )
            db.commit()
            return cur.rowcount > 0
        finally:
            cur.close()

    def find_by_user_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        根据用户ID查找登录状态

        Args:
            user_id: 用户ID

        Returns:
            登录状态字典，不存在返回None
        """
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("""
                SELECT user_id, login_time, ip_address
                FROM user_login_status
                WHERE user_id = ?
            """, (user_id,))
            user = cur.fetchone()
            return dict(user) if user else None
        finally:
            cur.close()
