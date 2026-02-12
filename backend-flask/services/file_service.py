"""
File Service - 文件业务逻辑层
"""
import os
import hashlib
import zipfile
import tempfile
import shutil
from datetime import datetime
from flask import current_app, request
from werkzeug.utils import secure_filename
from repositories.file_repository import FileRepository
from repositories.membership_repository import UserMembershipRepository
from errors import ValidationError, NotFoundError
from utils.formatters import format_bytes


class FileService:
    """文件业务逻辑类"""
    
    def __init__(self):
        self.file_repo = FileRepository()
        self.membership_repo = UserMembershipRepository()
    
    def _get_user_folder(self, user_id: int) -> str:
        """
        获取用户文件夹路径

        Args:
            user_id: 用户ID

        Returns:
            文件夹路径（绝对路径）
        """
        root = current_app.config['UPLOAD_ROOT']

        # 转换为绝对路径
        if not os.path.isabs(root):
            root = os.path.abspath(os.path.join(os.path.dirname(__file__), root))

        folder = os.path.join(root, str(user_id))
        os.makedirs(folder, exist_ok=True)
        return folder
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """
        计算文件哈希值
        
        Args:
            file_path: 文件路径
            
        Returns:
            SHA-256哈希值
        """
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(8 * 1024 * 1024)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def _calculate_zip_hash(self, zip_path: str) -> str:
        """
        计算ZIP文件内所有文件的哈希值
        
        Args:
            zip_path: ZIP文件路径
            
        Returns:
            SHA-256哈希值
        """
        user_folder = os.path.dirname(zip_path)
        temp_dir = tempfile.mkdtemp(dir=user_folder)
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            hasher = hashlib.sha256()
            for root, _, files in os.walk(temp_dir):
                for name in sorted(files):
                    path = os.path.join(root, name)
                    with open(path, 'rb') as f:
                        while True:
                            chunk = f.read(8 * 1024 * 1024)
                            if not chunk:
                                break
                            hasher.update(chunk)
            return hasher.hexdigest()
        finally:
            shutil.rmtree(temp_dir)
    
    def upload_file(self, user_id: int, file, file_permission: str = 'private',
                    description: str = None) -> dict:
        """
        上传文件
        
        Args:
            user_id: 用户ID
            file: 文件对象
            file_permission: 文件权限
            description: 文件描述
            
        Returns:
            上传成功的文件信息
            
        Raises:
            ValidationError: 验证失败
        """
        # 验证文件权限
        if file_permission not in ['public', 'private']:
            raise ValidationError("file_permission 必须是 'public' 或 'private'")
        
        # 保存文件
        filename = secure_filename(file.filename)
        user_folder = self._get_user_folder(user_id)
        dest_path = os.path.join(user_folder, filename)
        
        # 计算文件大小和哈希
        if filename.lower().endswith('.zip'):
            # ZIP文件特殊处理
            file.save(dest_path)
            file_size = os.path.getsize(dest_path)
            file_hash = self._calculate_zip_hash(dest_path)
        else:
            # 普通文件处理
            threshold = current_app.config.get('IN_MEMORY_UPLOAD_LIMIT', 256 * 1024 * 1024)
            total_size = request.content_length or 0 if hasattr(request, 'content_length') else 0
            
            if total_size <= threshold:
                data = file.read()
                hasher = hashlib.sha256()
                hasher.update(data)
                file_hash = hasher.hexdigest()
                file_size = len(data)
                file.seek(0)
                file.save(dest_path)
            else:
                file.save(dest_path)
                file_size = os.path.getsize(dest_path)
                file_hash = self._calculate_file_hash(dest_path)
        
        # 检查会员限制
        self._check_membership_limits(user_id, file_size, dest_path)
        
        # 检查文件重复
        if self.file_repo.find_by_hash(file_hash):
            if os.path.exists(dest_path):
                os.remove(dest_path)
            raise ValidationError("文件已存在")
        
        # 创建文件记录
        file_data = {
            'user_id': user_id,
            'file_name': filename,
            'file_path': dest_path,
            'description': description,
            'file_permission': file_permission,
            'file_hash': file_hash,
            'file_size': file_size
        }
        file_id = self.file_repo.create(file_data)
        
        # 更新用户存储使用量
        self.membership_repo.update_storage_usage(user_id, file_size, increment=True)
        
        return {
            'file_id': file_id,
            'file_name': filename,
            'file_permission': file_permission,
            'description': description,
            'file_hash': file_hash,
            'file_size': file_size,
            'file_size_formatted': format_bytes(file_size),
            'uploaded_at': datetime.utcnow().isoformat() + 'Z'
        }
    
    def _check_membership_limits(self, user_id: int, file_size: int, file_path: str = None) -> None:
        """
        检查会员限制

        Args:
            user_id: 用户ID
            file_size: 文件大小
            file_path: 文件路径（可选，用于删除超出限制的文件）

        Raises:
            ValidationError: 超过限制
        """
        membership = self.membership_repo.find_active_by_user_id(user_id)

        if not membership:
            # 使用默认免费用户限制
            storage_limit = 1073741824  # 1GB
            max_file_size = 52428800  # 50MB
            max_file_count = 100
            current_used = 0
            current_count = 0
        else:
            storage_limit = membership['storage_limit']
            max_file_size = membership['max_file_size']
            max_file_count = membership['max_file_count']
            current_used = membership['storage_used']
            current_count = membership['file_count']

        # 检查文件大小限制
        if file_size > max_file_size:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            raise ValidationError(
                f"文件大小超过限制。当前文件: {format_bytes(file_size)}，最大允许: {format_bytes(max_file_size)}"
            )

        # 检查存储容量限制
        if current_used + file_size > storage_limit:
            raise ValidationError(
                f"存储空间不足。当前使用: {format_bytes(current_used)}，限制: {format_bytes(storage_limit)}"
            )

        # 检查文件数量限制
        if current_count >= max_file_count:
            raise ValidationError(
                f"文件数量已达到上限。当前: {current_count}个，最大: {max_file_count}个"
            )
    
    def list_files(self, user_id: int) -> list:
        """
        获取用户文件列表

        Args:
            user_id: 用户ID

        Returns:
            文件列表
        """
        files = self.file_repo.get_by_user_id(user_id)

        # 格式化时间
        for file in files:
            if isinstance(file.get('updated_at'), datetime):
                file['updated_at'] = file['updated_at'].isoformat()

        return files

    def list_public_files(self) -> list:
        """
        获取所有公开文件列表

        Returns:
            公开文件列表
        """
        files = self.file_repo.get_public_files()

        # 格式化时间
        for file in files:
            if isinstance(file.get('updated_at'), datetime):
                file['updated_at'] = file['updated_at'].isoformat()

        return files
    
    def get_file(self, user_id: int, file_id: int) -> dict:
        """
        获取文件信息
        
        Args:
            user_id: 用户ID
            file_id: 文件ID
            
        Returns:
            文件信息
            
        Raises:
            NotFoundError: 文件不存在
        """
        file = self.file_repo.find_by_id_and_user_id(file_id, user_id)
        if not file:
            raise NotFoundError("文件不存在")
        
        if isinstance(file.get('updated_at'), datetime):
            file['updated_at'] = file['updated_at'].isoformat()
        
        return file
    
    def update_file(self, user_id: int, file_id: int, file_name: str = None,
                    file_permission: str = None, description: str = None) -> None:
        """
        更新文件信息
        
        Args:
            user_id: 用户ID
            file_id: 文件ID
            file_name: 文件名
            file_permission: 文件权限
            description: 文件描述
            
        Raises:
            ValidationError: 验证失败
            NotFoundError: 文件不存在
        """
        # 验证文件权限
        if file_permission and file_permission not in ['public', 'private']:
            raise ValidationError("file_permission 必须是 'public' 或 'private'")
        
        # 获取文件信息
        file = self.file_repo.find_by_id_and_user_id(file_id, user_id)
        if not file:
            raise NotFoundError("文件不存在")
        
        # 构建更新数据
        file_data = {}
        new_path = file['file_path']
        
        if file_name and file_name != file['file_name']:
            secure_new = secure_filename(file_name)
            user_folder = self._get_user_folder(user_id)
            new_path = os.path.join(user_folder, secure_new)
            os.rename(file['file_path'], new_path)
            file_data['file_name'] = secure_new
            file_data['file_path'] = new_path
        
        if file_permission:
            file_data['file_permission'] = file_permission
        
        if description is not None:
            file_data['description'] = description
        
        # 更新文件记录
        if file_data:
            self.file_repo.update(file_id, user_id, file_data)
    
    def delete_file(self, user_id: int, file_id: int) -> None:
        """
        删除文件
        
        Args:
            user_id: 用户ID
            file_id: 文件ID
            
        Raises:
            NotFoundError: 文件不存在
        """
        # 获取文件信息
        file = self.file_repo.find_by_id_and_user_id(file_id, user_id)
        if not file:
            raise NotFoundError("文件不存在")
        
        file_path = file['file_path']
        file_size = file['file_size']
        
        # 删除数据库记录
        self.file_repo.delete(file_id, user_id)
        
        # 更新用户存储使用量
        self.membership_repo.update_storage_usage(user_id, file_size, increment=False)
        
        # 删除物理文件
        try:
            os.remove(file_path)
        except OSError:
            pass
