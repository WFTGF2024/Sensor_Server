# auth.py

import os
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    # Only username and password are mandatory
    for field in ('username', 'password'):
        if not data.get(field):
            return jsonify({"error": f"Missing field: {field}"}), 400

    username = data['username']
    raw_password = data['password']
    email = data.get('email')
    phone = data.get('phone')
    qq = data.get('qq')
    wechat = data.get('wechat')

    hashed_pw = generate_password_hash(raw_password, method='pbkdf2:sha256', salt_length=16)

    db = get_db()
    with db.cursor() as cur:
        # Check username uniqueness
        cur.execute("SELECT user_id FROM users WHERE username=%s", (username,))
        if cur.fetchone():
            return jsonify({"error": "Username already taken"}), 409

        # Optional uniqueness checks for email and phone
        if email:
            cur.execute("SELECT user_id FROM users WHERE email=%s", (email,))
            if cur.fetchone():
                return jsonify({"error": "Email already taken"}), 409
        if phone:
            cur.execute("SELECT user_id FROM users WHERE phone=%s", (phone,))
            if cur.fetchone():
                return jsonify({"error": "Phone already taken"}), 409

        # Create user
        cur.execute("""
            INSERT INTO users
              (username, password, email, phone, qq, wechat, point)
            VALUES (%s, %s, %s, %s, %s, %s, 0)
        """, (username, hashed_pw, email, phone, qq, wechat))
        user_id = cur.lastrowid

        # Initialize login status
        cur.execute("INSERT INTO user_login_status (user_id) VALUES (%s)", (user_id,))
        db.commit()

    return jsonify({"message": "Registration successful", "user_id": user_id}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT user_id, password FROM users WHERE username=%s", (username,))
        user = cur.fetchone()

    if not user or not check_password_hash(user['password'], password):
        return jsonify({"error": "Invalid credentials"}), 401

    # Set session
    session.clear()
    session['user_id'] = user['user_id']
    session['username'] = username

    # Update login status
    with db.cursor() as cur:
        cur.execute("UPDATE user_login_status SET login_status=1 WHERE user_id=%s", (user['user_id'],))
        db.commit()

    return jsonify({"message": "Login successful", "user_id": user['user_id']}), 200


@auth_bp.route('/logout', methods=['POST'])
def logout():
    user_id = session.get('user_id')
    db = get_db()
    if user_id:
        with db.cursor() as cur:
            cur.execute("UPDATE user_login_status SET login_status=0 WHERE user_id=%s", (user_id,))
            db.commit()
    session.clear()
    return jsonify({"message": "Logged out successfully", "user_id": user_id}), 200


@auth_bp.route('/user', methods=['PATCH'])
def update_profile():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json() or {}
    updates = {}
    db = get_db()
    with db.cursor() as cur:
        # Unique checks for email and phone
        if 'email' in data:
            cur.execute("SELECT 1 FROM users WHERE email=%s AND user_id<>%s", (data['email'], user_id))
            if cur.fetchone():
                return jsonify({"error": "Email already taken"}), 409
            updates['email'] = data['email']
        if 'phone' in data:
            cur.execute("SELECT 1 FROM users WHERE phone=%s AND user_id<>%s", (data['phone'], user_id))
            if cur.fetchone():
                return jsonify({"error": "Phone already taken"}), 409
            updates['phone'] = data['phone']

        # Other profile fields
        for field in ('qq', 'wechat'):
            if field in data:
                updates[field] = data[field]

        # Password change
        if 'password' in data:
            updates['password'] = generate_password_hash(data['password'], method='pbkdf2:sha256', salt_length=16)

        if not updates:
            return jsonify({"message": "No valid fields to update"}), 400

        # Build and execute update
        set_clause = ", ".join(f"{col}=%s" for col in updates)
        params = list(updates.values()) + [user_id]
        sql = f"UPDATE users SET {set_clause} WHERE user_id=%s"
        cur.execute(sql, params)
        db.commit()

    return jsonify({"message": "Profile updated successfully", "updated": list(updates.keys())}), 200


@auth_bp.route('/questions', methods=['GET'])
def get_security_questions():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT question1, question2 FROM user_questions WHERE user_id=%s", (user_id,))
        row = cur.fetchone()

    if not row or not row.get('question1'):
        return jsonify({"message": "Security questions not set"}), 200

    result = {"question1": row['question1']}
    if row.get('question2'):
        result['question2'] = row['question2']
    return jsonify(result), 200


@auth_bp.route('/questions/verify', methods=['POST'])
def verify_security_answers():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json() or {}
    if 'answer1' not in data:
        return jsonify({"error": "answer1 required"}), 400

    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT answer1, answer2 FROM user_questions WHERE user_id=%s", (user_id,))
        row = cur.fetchone()

    if not row or not row.get('answer1'):
        return jsonify({"error": "Security questions not set"}), 400

    match = (data['answer1'] == row['answer1'])
    if row.get('answer2') is not None:
        if 'answer2' not in data:
            return jsonify({"error": "answer2 required"}), 400
        match = match and (data['answer2'] == row['answer2'])

    return jsonify({"match": match}), 200


@auth_bp.route('/reset_password', methods=['POST'])
def reset_password():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json() or {}
    if 'new_password' not in data or 'answer1' not in data:
        return jsonify({"error": "new_password and answer1 required"}), 400

    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT answer1, answer2 FROM user_questions WHERE user_id=%s", (user_id,))
        row = cur.fetchone()

    if not row or not row.get('answer1'):
        return jsonify({"error": "Security questions not set"}), 400

    if data['answer1'] != row['answer1']:
        return jsonify({"error": "Security answer1 incorrect"}), 403
    if row.get('answer2') is not None:
        if 'answer2' not in data or data['answer2'] != row['answer2']:
            return jsonify({"error": "Security answer2 incorrect"}), 403

    new_hashed = generate_password_hash(data['new_password'], method='pbkdf2:sha256', salt_length=16)
    with db.cursor() as cur:
        cur.execute("UPDATE users SET password=%s WHERE user_id=%s", (new_hashed, user_id))
        db.commit()

    return jsonify({"message": "Password reset successful"}), 200


@auth_bp.route('/questions', methods=['PUT'])
def upsert_security_questions():
    """
    PUT /auth/questions
    - If no existing questions: insert new question1/answer1 (and optional question2/answer2).
    - If questions exist: require old_answer1 or old_answer2, verify it,
      then update both question1/answer1 and question2/answer2 in one call.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json() or {}
    db = get_db()

    with db.cursor() as cur:
        # Fetch any existing answers
        cur.execute("SELECT answer1, answer2 FROM user_questions WHERE user_id=%s", (user_id,))
        existing = cur.fetchone()

        if existing and existing.get('answer1'):
            # Verify one old answer
            if 'old_answer1' not in data and 'old_answer2' not in data:
                return jsonify({"error": "Must provide old_answer1 or old_answer2"}), 400

            verified = False
            if 'old_answer1' in data and data['old_answer1'] == existing['answer1']:
                verified = True
            if existing.get('answer2') and 'old_answer2' in data and data['old_answer2'] == existing['answer2']:
                verified = True
            if not verified:
                return jsonify({"error": "Old answer verification failed"}), 403

        # Validate new question/answer pairs
        if ('question1' in data) ^ ('answer1' in data):
            return jsonify({"error": "Both question1 and answer1 are required"}), 400
        if ('question2' in data) ^ ('answer2' in data):
            return jsonify({"error": "Both question2 and answer2 are required"}), 400
        if 'question1' not in data and 'question2' not in data:
            return jsonify({"error": "At least one question/answer pair must be provided"}), 400

        cols, vals = [], []
        for i in (1, 2):
            qk, ak = f"question{i}", f"answer{i}"
            if qk in data:
                cols.extend([qk, ak])
                vals.extend([data[qk], data[ak]])

        col_list = ", ".join(cols)
        placeholder_list = ", ".join(["%s"] * len(vals))
        update_list = ", ".join(f"{c}=VALUES({c})" for c in cols)

        sql = (
            f"INSERT INTO user_questions (user_id, {col_list}) "
            f"VALUES (%s, {placeholder_list}) "
            f"ON DUPLICATE KEY UPDATE {update_list}"
        )
        params = [user_id] + vals
        cur.execute(sql, params)
        db.commit()

    action = "updated" if existing and existing.get('answer1') else "set"
    return jsonify({"message": f"Security questions {action}"}), 200
@auth_bp.route('/change_password', methods=['POST'])
def change_password():
    """
    POST /auth/change_password
    Body JSON must include:
      - current_password
      - new_password
    Verifies current_password before updating.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json() or {}
    if 'current_password' not in data or 'new_password' not in data:
        return jsonify({"error": "Both current_password and new_password are required"}), 400

    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT password FROM users WHERE user_id=%s", (user_id,))
        row = cur.fetchone()

    if not row or not check_password_hash(row['password'], data['current_password']):
        return jsonify({"error": "Current password incorrect"}), 403

    new_hashed = generate_password_hash(data['new_password'], method='pbkdf2:sha256', salt_length=16)
    with db.cursor() as cur:
        cur.execute("UPDATE users SET password=%s WHERE user_id=%s", (new_hashed, user_id))
        db.commit()

    return jsonify({"message": "Password changed successfully"}), 200
    
    
@auth_bp.route('/delete_account', methods=['POST'])
def delete_account():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json() or {}
    pwd = data.get('password')
    if not pwd:
        return jsonify({"error": "Password required"}), 400

    db = get_db()
    # verify current password
    with db.cursor() as cur:
        cur.execute("SELECT password FROM users WHERE user_id=%s", (user_id,))
        row = cur.fetchone()
        if not row or not check_password_hash(row['password'], pwd):
            return jsonify({"error": "Password incorrect"}), 403

    # delete user (cascades to user_questions); also clean login status
    with db.cursor() as cur:
        cur.execute("DELETE FROM user_login_status WHERE user_id=%s", (user_id,))
        cur.execute("DELETE FROM users WHERE user_id=%s", (user_id,))
        db.commit()

    session.clear()
    return jsonify({"message": "Account deleted successfully"}), 200
