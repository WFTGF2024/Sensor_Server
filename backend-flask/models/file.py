"""
File Model - 文件模型
"""
from datetime import datetime
from typing import Optional


class File:
    """文件模型"""
    
    def __init__(self, file_id: int = None, user_id: int = None,
                 file_name: str = None, file_path: str = None,
                 description: str = None, file_permission: str = 'private',
                 file_hash: str = None, file_size: int = 0,
                 updated_at: Optional[datetime] = None):
        self.file_id = file_id
        self.user_id = user_id
        self.file_name = file_name
        self.file_path = file_path
        self.description = description
        self.file_permission = file_permission
        self.file_hash = file_hash
        self.file_size = file_size
        self.updated_at = updated_at
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'file_id': self.file_id,
            'user_id': self.user_id,
            'file_name': self.file_name,
            'file_path': self.file_path,
            'description': self.description,
            'file_permission': self.file_permission,
            'file_hash': self.file_hash,
            'file_size': self.file_size,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
