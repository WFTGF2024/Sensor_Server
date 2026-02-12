"""
File Controller - 文件控制器
"""
from flask import Blueprint, request, jsonify, session, send_file
from services.file_service import FileService
from errors import ValidationError, NotFoundError, AuthenticationError

download_bp = Blueprint('download', __name__)
file_service = FileService()


@download_bp.route('/upload', methods=['POST'])
def upload_file():
    """
    POST /download/upload
    上传文件
    
    Required: file (multipart/form-data)
    Optional: file_permission, description
    
    Returns:
        JSON response with file information
    """
    if 'user_id' not in session:
        raise AuthenticationError("Authentication required")
    
    user_id = session['user_id']
    
    # 检查是否有文件
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400
    
    file_permission = request.form.get('file_permission', 'private')
    description = request.form.get('description')
    
    try:
        result = file_service.upload_file(
            user_id=user_id,
            file=file,
            file_permission=file_permission,
            description=description
        )
        
        return jsonify({
            "message": "Upload successful",
            "file_id": result['file_id'],
            "file_name": result['file_name'],
            "file_permission": result['file_permission'],
            "description": result['description'],
            "file_hash": result['file_hash'],
            "file_size": result['file_size'],
            "file_size_formatted": result['file_size_formatted'],
            "uploaded_at": result['uploaded_at']
        }), 201
        
    except ValidationError as e:
        raise e


@download_bp.route('/files', methods=['GET'])
def list_files():
    """
    GET /download/files
    获取用户文件列表
    
    Returns:
        JSON response with file list
    """
    if 'user_id' not in session:
        raise AuthenticationError("Authentication required")

    user_id = session['user_id']

    files = file_service.list_files(user_id)

    return jsonify(files), 200


@download_bp.route('/public', methods=['GET'])
def list_public_files():
    """
    GET /download/public
    获取所有公开文件列表

    Returns:
        JSON response with public file list
    """
    files = file_service.list_public_files()

    return jsonify(files), 200


@download_bp.route('/download/<int:file_id>', methods=['GET'])
def download_file(file_id):
    """
    GET /download/download/<file_id>
    下载文件
    
    Returns:
        File download
    """
    if 'user_id' not in session:
        raise AuthenticationError("Authentication required")
    
    user_id = session['user_id']
    
    try:
        file = file_service.get_file(user_id, file_id)
        
        file_path = file['file_path']
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=file['file_name']
        )
        
    except NotFoundError as e:
        raise e


@download_bp.route('/file/<int:file_id>', methods=['PUT'])
def update_file_metadata(file_id):
    """
    PUT /download/file/<file_id>
    更新文件元数据
    
    Optional fields: file_name, file_permission, description
    
    Returns:
        JSON response with success message
    """
    if 'user_id' not in session:
        raise AuthenticationError("Authentication required")
    
    user_id = session['user_id']
    data = request.get_json() or {}
    
    try:
        file_service.update_file(
            user_id=user_id,
            file_id=file_id,
            file_name=data.get('file_name'),
            file_permission=data.get('file_permission'),
            description=data.get('description')
        )
        
        return jsonify({"message": "Update successful"}), 200
        
    except (ValidationError, NotFoundError) as e:
        raise e


@download_bp.route('/file/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    """
    DELETE /download/file/<file_id>
    删除文件
    
    Returns:
        JSON response with success message
    """
    if 'user_id' not in session:
        raise AuthenticationError("Authentication required")
    
    user_id = session['user_id']
    
    try:
        file_service.delete_file(user_id, file_id)
        
        return jsonify({"message": "Delete successful"}), 200
        
    except NotFoundError as e:
        raise e
