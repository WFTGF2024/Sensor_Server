import os
from datetime import datetime
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
    Ensure and return the path to the user's upload folder.
    Subfolder is named by the user_id under UPLOAD_ROOT.
    """
    root = current_app.config['UPLOAD_ROOT']
    folder = os.path.join(root, str(user_id))
    os.makedirs(folder, exist_ok=True)
    return folder

@download_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'user_id' not in session:
        return jsonify({"error": "Authentication required"}), 401
    user_id = session['user_id']

    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    permission = request.form.get('file_permission', '').lower()
    if permission not in ALLOWED_PERMISSIONS:
        return jsonify({"error": "file_permission must be 'public' or 'private'"}), 400
    description = request.form.get('description')

    filename = secure_filename(file.filename)
    user_folder = _get_user_folder(user_id)
    dest_path = os.path.join(user_folder, filename)
    file.save(dest_path)

    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO files
              (user_id, file_name, file_path, description, file_permission)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, filename, dest_path, description, permission))
        file_id = cur.lastrowid

        if permission == 'public':
            cur.execute("""
                INSERT INTO file_public (file_id, user_id, file_path)
                VALUES (%s, %s, %s)
            """, (file_id, user_id, dest_path))
    db.commit()

    return jsonify({
        "message": "Upload successful",
        "file_id": file_id,
        "file_name": filename,
        "file_permission": permission,
        "description": description,
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
            SELECT file_id, file_name, updated_at, description, file_permission
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
        cur.execute("""
            SELECT file_name, file_path
              FROM files
             WHERE file_id = %s AND user_id = %s
        """, (file_id, user_id))
        row = cur.fetchone()

    if not row:
        return jsonify({"error": "File not found"}), 404

    return send_file(
        row['file_path'],
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

        if new_name and new_name != old_name:
            secure_new = secure_filename(new_name)
            user_folder = _get_user_folder(user_id)
            new_path = os.path.join(user_folder, secure_new)
            os.rename(old_path, new_path)
            updates += ["file_name = %s", "file_path = %s"]
            params += [secure_new, new_path]

        if new_perm and new_perm != old_perm:
            updates.append("file_permission = %s")
            params.append(new_perm)

        if updates:
            params.append(file_id)
            cur.execute("UPDATE files SET " + ", ".join(updates) + " WHERE file_id = %s", tuple(params))

            if new_perm:
                if new_perm == 'public':
                    cur.execute("""
                        INSERT IGNORE INTO file_public (file_id, user_id, file_path)
                        VALUES (%s, %s, %s)
                    """, (file_id, user_id, new_path))
                else:
                    cur.execute("DELETE FROM file_public WHERE file_id = %s", (file_id,))
    db.commit()

    return jsonify({"message": "Update successful"}), 200

@download_bp.route('/file/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    if 'user_id' not in session:
        return jsonify({"error": "Authentication required"}), 401
    user_id = session['user_id']

    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            SELECT file_path
              FROM files
             WHERE file_id = %s AND user_id = %s
        """, (file_id, user_id))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "File not found"}), 404

        path = row['file_path']
        cur.execute("DELETE FROM files WHERE file_id = %s", (file_id,))
    db.commit()

    try:
        os.remove(path)
    except OSError:
        pass

    return jsonify({"message": "Delete successful"}), 200
