"""
File Repository - 文件数据访问层
"""

import time
from typing import Optional, List, Dict, Any
from db import get_db
from utils import CacheManager, performance_monitor


class FileRepository:
    """文件仓储类"""
    
    def find_by_id(self, file_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID查找文件
        
        Args:
            file_id: 文件ID
            
        Returns:
            文件字典，不存在返回None
        """
        # 尝试从缓存获取
        cached_file = CacheManager.get_file(file_id)
        if cached_file is not None:
            performance_monitor.record_cache_hit("file", f"file:{file_id}")
            return cached_file
        
        performance_monitor.record_cache_miss("file", f"file:{file_id}")
        
        # 记录数据库查询开始时间
        start_time = time.time()
        
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("""
                SELECT file_id, user_id, file_name, file_path, description,
                       file_permission, file_hash, file_size, updated_at
                FROM files
                WHERE file_id = ?
            """, (file_id,))
            file = cur.fetchone()
            
            # 记录数据库查询性能
            duration = time.time() - start_time
            performance_monitor.record_database_query("select", duration, success=file is not None)
            
            # 如果找到文件，存入缓存
            if file:
                CacheManager.cache_file(file_id, file)
            
            return dict(file) if file else None
        finally:
            cur.close()
    
    def find_by_id_and_user_id(self, file_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """
        根据文件ID和用户ID查找文件
        
        Args:
            file_id: 文件ID
            user_id: 用户ID
            
        Returns:
            文件字典，不存在返回None
        """
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("""
                SELECT file_id, user_id, file_name, file_path, description,
                       file_permission, file_hash, file_size, updated_at
                FROM files
                WHERE file_id = ? AND user_id = ?
            """, (file_id, user_id))
            file = cur.fetchone()
            return dict(file) if file else None
        finally:
            cur.close()
    
    def find_by_hash(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """
        根据文件哈希查找文件
        
        Args:
            file_hash: 文件哈希值
            
        Returns:
            文件字典，不存在返回None
        """
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("""
                SELECT file_id, user_id, file_name, file_path, description,
                       file_permission, file_hash, file_size, updated_at
                FROM files
                WHERE file_hash = ?
            """, (file_hash,))
            file = cur.fetchone()
            return dict(file) if file else None
        finally:
            cur.close()
    
    def create(self, file_data: Dict[str, Any]) -> int:
        """
        创建文件记录
        
        Args:
            file_data: 文件数据字典
            
        Returns:
            新创建的文件ID
        """
        # 记录数据库查询开始时间
        start_time = time.time()
        
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("""
                INSERT INTO files
                (user_id, file_name, file_path, description, file_permission, file_hash, file_size)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                file_data['user_id'],
                file_data['file_name'],
                file_data['file_path'],
                file_data.get('description'),
                file_data.get('file_permission', 'private'),
                file_data['file_hash'],
                file_data['file_size']
            ))
            file_id = cur.lastrowid
            db.commit()
            
            # 记录数据库查询性能
            duration = time.time() - start_time
            performance_monitor.record_database_query("insert", duration, success=True)
            
            return file_id
        finally:
            cur.close()
    
    def update(self, file_id: int, user_id: int, file_data: Dict[str, Any]) -> bool:
        """
        更新文件信息
        
        Args:
            file_id: 文件ID
            user_id: 用户ID
            file_data: 要更新的文件数据
            
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
            
            if 'file_name' in file_data:
                updates.append("file_name = ?")
                params.append(file_data['file_name'])
            
            if 'file_path' in file_data:
                updates.append("file_path = ?")
                params.append(file_data['file_path'])
            
            if 'file_permission' in file_data:
                updates.append("file_permission = ?")
                params.append(file_data['file_permission'])
            
            if 'description' in file_data:
                updates.append("description = ?")
                params.append(file_data['description'])
            
            if updates:
                params.extend([file_id, user_id])
                cur.execute(
                    f"UPDATE files SET {', '.join(updates)} WHERE file_id = ? AND user_id = ?",
                    tuple(params)
                )
                db.commit()
                
                # 记录数据库查询性能
                duration = time.time() - start_time
                success = cur.rowcount > 0
                performance_monitor.record_database_query("update", duration, success)
                
                # 如果更新成功，使缓存失效
                if success:
                    CacheManager.invalidate_file(file_id)
                
                return success
            return False
        finally:
            cur.close()
    
    def delete(self, file_id: int, user_id: int) -> bool:
        """
        删除文件
        
        Args:
            file_id: 文件ID
            user_id: 用户ID
            
        Returns:
            是否删除成功
        """
        # 记录数据库查询开始时间
        start_time = time.time()
        
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute(
                "DELETE FROM files WHERE file_id = ? AND user_id = ?",
                (file_id, user_id)
            )
            db.commit()
            
            # 记录数据库查询性能
            duration = time.time() - start_time
            success = cur.rowcount > 0
            performance_monitor.record_database_query("delete", duration, success)
            
            # 如果删除成功，使缓存失效
            if success:
                CacheManager.invalidate_file(file_id)
            
            return success
        finally:
            cur.close()
    
    def get_by_user_id(self, user_id: int, permission: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取用户的所有文件
        
        Args:
            user_id: 用户ID
            permission: 权限过滤（可选）
            
        Returns:
            文件列表
        """
        db = get_db()
        cur = db.cursor()
        try:
            if permission:
                cur.execute("""
                    SELECT file_id, file_name, updated_at, description,
                           file_permission, file_hash, file_size
                    FROM files
                    WHERE user_id = ? AND file_permission = ?
                    ORDER BY updated_at DESC
                """, (user_id, permission))
            else:
                cur.execute("""
                    SELECT file_id, file_name, updated_at, description,
                           file_permission, file_hash, file_size
                    FROM files
                    WHERE user_id = ?
                    ORDER BY updated_at DESC
                """, (user_id,))
            return [dict(row) for row in cur.fetchall()]
        finally:
            cur.close()
    
    def get_user_total_size(self, user_id: int) -> int:
        """
        获取用户的总文件大小
        
        Args:
            user_id: 用户ID
            
        Returns:
            总文件大小（字节）
        """
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("""
                SELECT COALESCE(SUM(file_size), 0) as total_size
                FROM files
                WHERE user_id = ?
            """, (user_id,))
            result = cur.fetchone()
            return result['total_size'] if result else 0
        finally:
            cur.close()
    
    def get_user_file_count(self, user_id: int) -> int:
        """
        获取用户的文件数量
        
        Args:
            user_id: 用户ID
            
        Returns:
            文件数量
        """
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("""
                SELECT COUNT(*) as count
                FROM files
                WHERE user_id = ?
            """, (user_id,))
            result = cur.fetchone()
            return result['count'] if result else 0
        finally:
            cur.close()
    
    def count_by_user_id(self, user_id: int) -> int:
        """
        统计用户的文件数量

        Args:
            user_id: 用户ID

        Returns:
            文件数量
        """
        return self.get_user_file_count(user_id)

    def get_public_files(self) -> List[Dict[str, Any]]:
        """
        获取所有公开文件

        Returns:
            公开文件列表
        """
        db = get_db()
        cur = db.cursor()
        try:
            cur.execute("""
                SELECT f.file_id, f.file_name, f.updated_at, f.description,
                       f.file_permission, f.file_hash, f.file_size,
                       u.username
                FROM files f
                JOIN users u ON f.user_id = u.user_id
                WHERE f.file_permission = 'public'
                ORDER BY f.updated_at DESC
            """)
            return [dict(row) for row in cur.fetchall()]
        finally:
            cur.close()
