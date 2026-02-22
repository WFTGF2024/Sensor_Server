"""
File Controller - 文件控制器
处理文件上传、下载、列表、更新和删除等操作
"""
from flask import Blueprint, request, jsonify, session, send_file, current_app
from services.file_service import FileService
from errors import (
    ValidationError, NotFoundError, AuthenticationError, 
    FileOperationError, ServerError, safe_int
)
import os

download_bp = Blueprint('download', __name__)
file_service = FileService()


def get_current_user_id():
    """
    获取当前登录用户的ID
    
    Returns:
        int: 用户ID
        
    Raises:
        AuthenticationError: 如果用户未登录
    """
    if 'user_id' not in session:
        raise AuthenticationError("请先登录")
    return session['user_id']


@download_bp.route('/upload', methods=['POST'])
def upload_file():
    """
    POST /download/upload
    上传文件
    
    Required: file (multipart/form-data)
    Optional: file_permission (private/public), description
    
    Returns:
        JSON response with file information
        
    Error Responses:
        401: 未登录
        400: 文件无效或参数错误
        413: 文件大小超过限制
        500: 服务器内部错误
    """
    try:
        user_id = get_current_user_id()
        
        # 检查请求是否包含文件部分
        if not request.files:
            raise ValidationError("请求中未包含文件数据")
        
        # 检查是否有文件
        if 'file' not in request.files:
            raise ValidationError("请选择要上传的文件")
        
        file = request.files['file']
        
        # 检查文件名是否为空
        if not file or file.filename == '':
            raise ValidationError("文件名不能为空")
        
        # 检查文件名是否安全
        filename = file.filename
        if not filename or len(filename) > 255:
            raise ValidationError("文件名无效或过长（最大255字符）")
        
        # 获取可选参数
        file_permission = request.form.get('file_permission', 'private')
        if file_permission not in ('private', 'public'):
            raise ValidationError("file_permission 必须是 'private' 或 'public'")
        
        description = request.form.get('description', '')
        if description and len(description) > 1000:
            raise ValidationError("描述不能超过1000个字符")
        
        try:
            result = file_service.upload_file(
                user_id=user_id,
                file=file,
                file_permission=file_permission,
                description=description
            )
            
            current_app.logger.info(f"文件上传成功: user_id={user_id}, file_id={result['file_id']}, filename={result['file_name']}")
            
            return jsonify({
                "success": True,
                "message": "文件上传成功",
                "file_id": result['file_id'],
                "file_name": result['file_name'],
                "file_permission": result['file_permission'],
                "description": result['description'],
                "file_hash": result['file_hash'],
                "file_size": result['file_size'],
                "file_size_formatted": result['file_size_formatted'],
                "uploaded_at": result['uploaded_at']
            }), 201
            
        except ValidationError:
            raise
        except Exception as e:
            current_app.logger.error(f"文件上传失败: user_id={user_id}, error={str(e)}", exc_info=True)
            raise FileOperationError(f"文件上传失败: {str(e)}")
            
    except AuthenticationError:
        raise
    except ValidationError:
        raise
    except Exception as e:
        current_app.logger.error(f"上传接口异常: {str(e)}", exc_info=True)
        raise ServerError("上传过程中发生错误")


@download_bp.route('/files', methods=['GET'])
def list_files():
    """
    GET /download/files
    获取当前用户的文件列表
    
    Query Parameters:
        page: 页码（默认1）
        page_size: 每页数量（默认20）
    
    Returns:
        JSON response with file list
        
    Error Responses:
        401: 未登录
        500: 服务器内部错误
    """
    try:
        user_id = get_current_user_id()
        
        # 获取分页参数
        page = safe_int(request.args.get('page', 1), 'page', default=1, min_val=1)
        page_size = safe_int(request.args.get('page_size', 20), 'page_size', default=20, min_val=1, max_val=100)
        
        try:
            files = file_service.list_files(user_id)
            
            # 分页处理
            total = len(files)
            start = (page - 1) * page_size
            end = start + page_size
            files = files[start:end]
            
            return jsonify({
                "success": True,
                "files": files,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": (total + page_size - 1) // page_size if total > 0 else 0
                }
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"获取文件列表失败: user_id={user_id}, error={str(e)}", exc_info=True)
            raise ServerError("获取文件列表失败")
            
    except AuthenticationError:
        raise
    except Exception as e:
        current_app.logger.error(f"文件列表接口异常: {str(e)}", exc_info=True)
        raise ServerError("获取文件列表时发生错误")


@download_bp.route('/public', methods=['GET'])
def list_public_files():
    """
    GET /download/public
    获取所有公开文件列表
    
    Query Parameters:
        page: 页码（默认1）
        page_size: 每页数量（默认20）
    
    Returns:
        JSON response with public file list
        
    Error Responses:
        500: 服务器内部错误
    """
    try:
        # 获取分页参数
        page = safe_int(request.args.get('page', 1), 'page', default=1, min_val=1)
        page_size = safe_int(request.args.get('page_size', 20), 'page_size', default=20, min_val=1, max_val=100)
        
        try:
            files = file_service.list_public_files()
            
            # 分页处理
            total = len(files)
            start = (page - 1) * page_size
            end = start + page_size
            files = files[start:end]
            
            return jsonify({
                "success": True,
                "files": files,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": (total + page_size - 1) // page_size if total > 0 else 0
                }
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"获取公开文件列表失败: error={str(e)}", exc_info=True)
            raise ServerError("获取公开文件列表失败")
            
    except Exception as e:
        current_app.logger.error(f"公开文件列表接口异常: {str(e)}", exc_info=True)
        raise ServerError("获取公开文件列表时发生错误")


@download_bp.route('/download/<int:file_id>', methods=['GET'])
def download_file(file_id):
    """
    GET /download/download/<file_id>
    下载文件
    
    Args:
        file_id: 文件ID
    
    Returns:
        File download
        
    Error Responses:
        401: 未登录
        404: 文件不存在
        500: 服务器内部错误
    """
    try:
        user_id = get_current_user_id()
        
        # 验证file_id
        if file_id <= 0:
            raise ValidationError("无效的文件ID")
        
        try:
            file = file_service.get_file(user_id, file_id)
            
            file_path = file['file_path']
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                current_app.logger.error(f"文件不存在于磁盘: file_path={file_path}")
                raise NotFoundError("文件不存在或已被删除")
            
            current_app.logger.info(f"文件下载: user_id={user_id}, file_id={file_id}, filename={file['file_name']}")
            
            return send_file(
                file_path,
                as_attachment=True,
                download_name=file['file_name']
            )
            
        except NotFoundError:
            raise
        except PermissionError:
            current_app.logger.error(f"文件访问权限错误: file_id={file_id}")
            raise FileOperationError("无法访问该文件")
        except Exception as e:
            current_app.logger.error(f"文件下载失败: user_id={user_id}, file_id={file_id}, error={str(e)}", exc_info=True)
            raise FileOperationError(f"文件下载失败: {str(e)}")
            
    except AuthenticationError:
        raise
    except NotFoundError:
        raise
    except ValidationError:
        raise
    except Exception as e:
        current_app.logger.error(f"下载接口异常: {str(e)}", exc_info=True)
        raise ServerError("下载过程中发生错误")


@download_bp.route('/file/<int:file_id>', methods=['GET'])
def get_file_info(file_id):
    """
    GET /download/file/<file_id>
    获取文件详情
    
    Args:
        file_id: 文件ID
    
    Returns:
        JSON response with file information
        
    Error Responses:
        401: 未登录
        404: 文件不存在
        500: 服务器内部错误
    """
    try:
        user_id = get_current_user_id()
        
        if file_id <= 0:
            raise ValidationError("无效的文件ID")
        
        try:
            file = file_service.get_file(user_id, file_id)
            
            return jsonify({
                "success": True,
                "file": file
            }), 200
            
        except NotFoundError:
            raise
        except Exception as e:
            current_app.logger.error(f"获取文件信息失败: user_id={user_id}, file_id={file_id}, error={str(e)}", exc_info=True)
            raise ServerError("获取文件信息失败")
            
    except AuthenticationError:
        raise
    except NotFoundError:
        raise
    except ValidationError:
        raise
    except Exception as e:
        current_app.logger.error(f"文件详情接口异常: {str(e)}", exc_info=True)
        raise ServerError("获取文件详情时发生错误")


@download_bp.route('/file/<int:file_id>', methods=['PUT'])
def update_file_metadata(file_id):
    """
    PUT /download/file/<file_id>
    更新文件元数据
    
    Args:
        file_id: 文件ID
    
    Optional fields: file_name, file_permission, description
    
    Returns:
        JSON response with success message
        
    Error Responses:
        401: 未登录
        404: 文件不存在
        400: 参数错误
        500: 服务器内部错误
    """
    try:
        user_id = get_current_user_id()
        
        if file_id <= 0:
            raise ValidationError("无效的文件ID")
        
        data = request.get_json()
        if data is None:
            data = {}
        
        # 验证参数
        file_name = data.get('file_name')
        if file_name is not None:
            if not file_name or len(file_name) > 255:
                raise ValidationError("文件名无效或过长（最大255字符）")
        
        file_permission = data.get('file_permission')
        if file_permission is not None and file_permission not in ('private', 'public'):
            raise ValidationError("file_permission 必须是 'private' 或 'public'")
        
        description = data.get('description')
        if description is not None and len(description) > 1000:
            raise ValidationError("描述不能超过1000个字符")
        
        try:
            file_service.update_file(
                user_id=user_id,
                file_id=file_id,
                file_name=file_name,
                file_permission=file_permission,
                description=description
            )
            
            current_app.logger.info(f"文件更新成功: user_id={user_id}, file_id={file_id}")
            
            return jsonify({
                "success": True,
                "message": "文件信息更新成功"
            }), 200
            
        except NotFoundError:
            raise
        except ValidationError:
            raise
        except Exception as e:
            current_app.logger.error(f"文件更新失败: user_id={user_id}, file_id={file_id}, error={str(e)}", exc_info=True)
            raise FileOperationError(f"文件更新失败: {str(e)}")
            
    except AuthenticationError:
        raise
    except NotFoundError:
        raise
    except ValidationError:
        raise
    except Exception as e:
        current_app.logger.error(f"文件更新接口异常: {str(e)}", exc_info=True)
        raise ServerError("更新文件时发生错误")


@download_bp.route('/file/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    """
    DELETE /download/file/<file_id>
    删除文件
    
    Args:
        file_id: 文件ID
    
    Returns:
        JSON response with success message
        
    Error Responses:
        401: 未登录
        404: 文件不存在
        500: 服务器内部错误
    """
    try:
        user_id = get_current_user_id()
        
        if file_id <= 0:
            raise ValidationError("无效的文件ID")
        
        try:
            file_service.delete_file(user_id, file_id)
            
            current_app.logger.info(f"文件删除成功: user_id={user_id}, file_id={file_id}")
            
            return jsonify({
                "success": True,
                "message": "文件删除成功"
            }), 200
            
        except NotFoundError:
            raise
        except Exception as e:
            current_app.logger.error(f"文件删除失败: user_id={user_id}, file_id={file_id}, error={str(e)}", exc_info=True)
            raise FileOperationError(f"文件删除失败: {str(e)}")
            
    except AuthenticationError:
        raise
    except NotFoundError:
        raise
    except ValidationError:
        raise
    except Exception as e:
        current_app.logger.error(f"文件删除接口异常: {str(e)}", exc_info=True)
        raise ServerError("删除文件时发生错误")


@download_bp.route('/search', methods=['GET'])
def search_files():
    """
    GET /download/search
    搜索文件
    
    Query Parameters:
        keyword: 搜索关键词
        page: 页码（默认1）
        page_size: 每页数量（默认20）
    
    Returns:
        JSON response with search results
        
    Error Responses:
        401: 未登录
        400: 参数错误
        500: 服务器内部错误
    """
    try:
        user_id = get_current_user_id()
        
        keyword = request.args.get('keyword', '').strip()
        if not keyword:
            raise ValidationError("请输入搜索关键词")
        
        if len(keyword) > 100:
            raise ValidationError("搜索关键词不能超过100个字符")
        
        # 获取分页参数
        page = safe_int(request.args.get('page', 1), 'page', default=1, min_val=1)
        page_size = safe_int(request.args.get('page_size', 20), 'page_size', default=20, min_val=1, max_val=100)
        
        try:
            # 获取用户所有文件并过滤
            all_files = file_service.list_files(user_id)
            
            # 搜索过滤
            keyword_lower = keyword.lower()
            files = [f for f in all_files if 
                     keyword_lower in (f.get('file_name', '') or '').lower() or
                     keyword_lower in (f.get('description', '') or '').lower()]
            
            # 分页处理
            total = len(files)
            start = (page - 1) * page_size
            end = start + page_size
            files = files[start:end]
            
            return jsonify({
                "success": True,
                "files": files,
                "keyword": keyword,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": (total + page_size - 1) // page_size if total > 0 else 0
                }
            }), 200
            
        except Exception as e:
            current_app.logger.error(f"文件搜索失败: user_id={user_id}, keyword={keyword}, error={str(e)}", exc_info=True)
            raise ServerError("文件搜索失败")
            
    except AuthenticationError:
        raise
    except ValidationError:
        raise
    except Exception as e:
        current_app.logger.error(f"文件搜索接口异常: {str(e)}", exc_info=True)
        raise ServerError("搜索文件时发生错误")
