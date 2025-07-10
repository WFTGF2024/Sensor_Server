import os, hashlib, zipfile, tempfile, shutil
from datetime import datetime
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.utils import secure_filename
from db import get_db

from flask import (
    Blueprint, request, jsonify, session,
    current_app, send_file
)
from werkzeug.utils import secure_filename

from db import get_db

download_bp = Blueprint('download', __name__, url_prefix='/download')

ALLOWED_PERMISSIONS = {'public', 'private'}

def _get_user_folder(user_id):
    """
    Ensure the user's upload folder exists and return its path.
    The folder is named by the user_id under UPLOAD_ROOT.
    """
    root = current_app.config['UPLOAD_ROOT']
    folder = os.path.join(root, str(user_id))
    os.makedirs(folder, exist_ok=True)
    return folder

@download_bp.route('/upload', methods=['POST'])
def upload_file():
    # 检查登录
    if 'user_id' not in session:
        return jsonify({"error": "Authentication required"}), 401
    user_id = session['user_id']

    # 确保有文件
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    filename = secure_filename(file.filename)
    user_folder = _get_user_folder(user_id)
    dest_path = os.path.join(user_folder, filename)

    # 处理 ZIP 包：保存 -> 解压 -> 对解压后所有文件二进制读取计算哈希 -> 删除解压目录
    if filename.lower().endswith('.zip'):
        # 保存压缩包
        file.save(dest_path)
        file_size = os.path.getsize(dest_path)

        # 解压到临时目录，二进制读取所有文件计算 SHA-256
        temp_dir = tempfile.mkdtemp(dir=user_folder)
        try:
            with zipfile.ZipFile(dest_path, 'r') as zip_ref:
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
            file_hash = hasher.hexdigest()
        finally:
            shutil.rmtree(temp_dir)

    else:
        # 按大小阈值分流计算哈希和大小
        threshold = current_app.config.get('IN_MEMORY_UPLOAD_LIMIT', 256 * 1024 * 1024)
        total_size = request.content_length or 0

        if total_size <= threshold:
            data = file.read()               # 二进制数据
            hasher = hashlib.sha256()
            hasher.update(data)
            file_hash = hasher.hexdigest()
            file_size = len(data)
            file.seek(0)
            file.save(dest_path)
        else:
            file.save(dest_path)
            hasher = hashlib.sha256()
            file_size = 0
            with open(dest_path, 'rb') as f:
                while True:
                    chunk = f.read(8 * 1024 * 1024)
                    if not chunk:
                        break
                    hasher.update(chunk)
                    file_size += len(chunk)
            file_hash = hasher.hexdigest()

    # 查重
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT file_id FROM files WHERE file_hash = %s", (file_hash,))
        if cur.fetchone():
            if os.path.exists(dest_path):
                os.remove(dest_path)
            return jsonify({"error": "file already exists"}), 400

    # 权限校验
    permission = request.form.get('file_permission', 'private').lower()
    if permission not in ALLOWED_PERMISSIONS:
        if os.path.exists(dest_path):
            os.remove(dest_path)
        return jsonify({"error": "file_permission must be 'public' or 'private'"}), 400
    description = request.form.get('description')

    # 插入 files 表，由触发器维护 file_public 和 user_storage
    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO files
              (user_id, file_name, file_path, description, file_permission, file_hash, file_size)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id,
            filename,
            dest_path,
            description,
            permission,
            file_hash,
            file_size
        ))
        file_id = cur.lastrowid
        db.commit()

    return jsonify({
        "message": "Upload successful",
        "file_id": file_id,
        "file_name": filename,
        "file_permission": permission,
        "description": description,
        "file_hash": file_hash,
        "file_size": file_size,
        "uploaded_at": datetime.utcnow().isoformat() + 'Z'
    }), 201


@download_bp.route('/files', methods=['GET'])
def list_files():
    if 'user_id' not in session:
        return jsonify({"error": "Authentication required"}), 401
    user_id = session['user_id']

    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            SELECT file_id, file_name, updated_at, description,
                   file_permission, file_hash, file_size
              FROM files
             WHERE user_id = %s
             ORDER BY updated_at DESC
        """, (user_id,))
        files = cur.fetchall()

    for rec in files:
        if isinstance(rec.get('updated_at'), datetime):
            rec['updated_at'] = rec['updated_at'].isoformat()
    return jsonify(files), 200

@download_bp.route('/download/<int:file_id>', methods=['GET'])
def download_file(file_id):
    if 'user_id' not in session:
        return jsonify({"error": "Authentication required"}), 401
    user_id = session['user_id']

    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "SELECT file_name, file_path FROM files WHERE file_id = %s AND user_id = %s",
            (file_id, user_id)
        )
        row = cur.fetchone()

    if not row:
        return jsonify({"error": "File not found"}), 404

    path = row['file_path']
    if not os.path.exists(path):
        current_app.logger.warning(f"Missing file on disk: {path}")
        return jsonify({"error": "File not found on server"}), 404

    return send_file(
        path,
        as_attachment=True,
        download_name=row['file_name']
    )

@download_bp.route('/file/<int:file_id>', methods=['PUT'])
def update_file_metadata(file_id):
    if 'user_id' not in session:
        return jsonify({"error": "Authentication required"}), 401
    user_id = session['user_id']
    data = request.get_json() or {}

    new_name = data.get('file_name')
    new_perm = data.get('file_permission')
    if new_name is None and new_perm is None:
        return jsonify({"error": "Nothing to update"}), 400
    if new_perm and new_perm not in ALLOWED_PERMISSIONS:
        return jsonify({"error": "file_permission must be 'public' or 'private'"}), 400

    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            SELECT file_name, file_path, file_permission
              FROM files
             WHERE file_id = %s AND user_id = %s
        """, (file_id, user_id))
        record = cur.fetchone()
        if not record:
            return jsonify({"error": "File not found"}), 404

        old_name = record['file_name']
        old_path = record['file_path']
        old_perm = record['file_permission']

        updates, params = [], []
        new_path = old_path

        # 重命名
        if new_name and new_name != old_name:
            secure_new = secure_filename(new_name)
            user_folder = _get_user_folder(user_id)
            new_path = os.path.join(user_folder, secure_new)
            os.rename(old_path, new_path)
            updates += ["file_name = %s", "file_path = %s"]
            params += [secure_new, new_path]

        # 更新权限（由触发器同步到 file_public）
        if new_perm and new_perm != old_perm:
            updates.append("file_permission = %s")
            params.append(new_perm)

        if updates:
            params.append(file_id)
            cur.execute(
                "UPDATE files SET " + ", ".join(updates) + " WHERE file_id = %s",
                tuple(params)
            )
            db.commit()

    return jsonify({"message": "Update successful"}), 200

@download_bp.route('/file/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    if 'user_id' not in session:
        return jsonify({"error": "Authentication required"}), 401
    user_id = session['user_id']

    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "SELECT file_path FROM files WHERE file_id = %s AND user_id = %s",
            (file_id, user_id)
        )
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "File not found"}), 404
        path = row['file_path']

        # 删除 files，触发器会同步更新 user_storage & file_public
        cur.execute("DELETE FROM files WHERE file_id = %s", (file_id,))
        db.commit()

    try:
        os.remove(path)
    except OSError:
        pass

    return jsonify({"message": "Delete successful"}), 200
