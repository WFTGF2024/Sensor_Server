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

    username     = data['username']
    raw_password = data['password']
    email        = data.get('email')    # optional
    phone        = data.get('phone')    # optional
    qq           = data.get('qq')
    wechat       = data.get('wechat')

    hashed_pw = generate_password_hash(
        raw_password,
        method='pbkdf2:sha256',
        salt_length=16
    )

    db = get_db()
    with db.cursor() as cur:
        cur.execute(
            "SELECT user_id FROM users WHERE username=%s",
            (username,)
        )
        if cur.fetchone():
            return jsonify({"error": "Username already taken"}), 409

        if email:
            cur.execute(
                "SELECT user_id FROM users WHERE email=%s",
                (email,)
            )
            if cur.fetchone():
                return jsonify({"error": "Email already taken"}), 409

        if phone:
            cur.execute(
                "SELECT user_id FROM users WHERE phone=%s",
                (phone,)
            )
            if cur.fetchone():
                return jsonify({"error": "Phone already taken"}), 409

        cur.execute(
            """
            INSERT INTO users
              (username, password, email, phone, qq, wechat, point)
            VALUES
              (%s, %s, %s, %s, %s, %s, %s)
            """,
            (username, hashed_pw, email, phone, qq, wechat, 0)
        )
        user_id = cur.lastrowid

        # 5) Insert initial record into login status table
        cur.execute(
            "INSERT INTO user_login_status (user_id) VALUES (%s)",
            (user_id,)
        )

        db.commit()

    return jsonify({
        "message": "Registration successful",
        "user_id": user_id
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    db = get_db()
    with db.cursor() as cur:
        # 1) fetch user
        cur.execute(
            "SELECT user_id, password FROM users WHERE username=%s",
            (username,)
        )
        user = cur.fetchone()

        # 2) verify credentials
        if not user or not check_password_hash(user['password'], password):
            return jsonify({"error": "Invalid credentials"}), 401

        user_id = user['user_id']

        # 3) set session
        session.clear()
        session['user_id']  = user_id
        session['username'] = username

        # 4) update login status to "online" (1)
        cur.execute(
            "UPDATE user_login_status "
            "SET login_status = 1 "
            "WHERE user_id = %s",
            (user_id,)
        )

        # 5) persist
        db.commit()

    return jsonify({
        "message": "Login successful",
        "user_id": user_id
    }), 200


@auth_bp.route('/logout', methods=['POST'])
def logout():
    user_id = session.get('user_id')
    db = get_db()
    with db.cursor() as cur:
        if user_id:
            cur.execute(
                "UPDATE user_login_status "
                "SET login_status = 0 "
                "WHERE user_id = %s",
                (user_id,)
            )
            db.commit()

    session.clear()
    return jsonify({
        "message": "Logged out successfully",
        "user_id": user_id
    }), 200


@auth_bp.route('/user', methods=['PATCH'])
def update_profile():
    """
    PATCH /auth/user
    Body (JSON): any of:
      - email
      - phone
      - qq
      - wechat
      - password
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json() or {}
    allowed = ('email', 'phone', 'qq', 'wechat', 'password')
    updates = {}
    params = []

    db = get_db()
    with db.cursor() as cur:
        # Unique checks for email/phone
        if 'email' in data:
            cur.execute("SELECT 1 FROM users WHERE email=%s AND user_id<>%s",
                        (data['email'], user_id))
            if cur.fetchone():
                return jsonify({"error": "Email already taken"}), 409
            updates['email'] = data['email']

        if 'phone' in data:
            cur.execute("SELECT 1 FROM users WHERE phone=%s AND user_id<>%s",
                        (data['phone'], user_id))
            if cur.fetchone():
                return jsonify({"error": "Phone already taken"}), 409
            updates['phone'] = data['phone']

        # Other simple fields
        for f in ('qq', 'wechat'):
            if f in data:
                updates[f] = data[f]

        # Password needs hashing
        if 'password' in data:
            hashed = generate_password_hash(
                data['password'], method='pbkdf2:sha256', salt_length=16
            )
            updates['password'] = hashed

        if not updates:
            return jsonify({"message": "No valid fields to update"}), 400

        # Build dynamic SQL
        set_clause = ", ".join(f"{col}=%s" for col in updates)
        params = list(updates.values()) + [user_id]
        sql = f"UPDATE users SET {set_clause} WHERE user_id=%s"
        cur.execute(sql, params)
        db.commit()

    return jsonify({
        "message": "Profile updated successfully",
        "updated": list(updates.keys())
    }), 200


@auth_bp.route('/questions', methods=['PUT'])
def upsert_security_questions():
    """
    PUT /auth/questions
    Body (JSON): must include pairs
      - question1 & answer1
      - optionally question2 & answer2
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json() or {}

    # Validate presence of pairs
    if ('question1' in data) ^ ('answer1' in data):
        return jsonify({"error": "Both question1 and answer1 are required together"}), 400
    if ('question2' in data) ^ ('answer2' in data):
        return jsonify({"error": "Both question2 and answer2 are required together"}), 400

    # At least one pair required
    if 'question1' not in data and 'question2' not in data:
        return jsonify({"error": "At least one question/answer pair must be provided"}), 400

    # Prepare columns & values
    cols = []
    vals = []
    for i in (1, 2):
        q = f"question{i}"
        a = f"answer{i}"
        if q in data:
            cols.extend([q, a])
            vals.extend([data[q], data[a]])

    # Build INSERT ... ON DUPLICATE KEY UPDATE
    col_list = ", ".join(cols)
    placeholder_list = ", ".join(["%s"] * len(vals))
    update_list = ", ".join(f"{c}=VALUES({c})" for c in cols)

    sql = (
        f"INSERT INTO user_questions (user_id, {col_list}) "
        f"VALUES (%s, {placeholder_list}) "
        f"ON DUPLICATE KEY UPDATE {update_list}"
    )
    params = [user_id] + vals

    db = get_db()
    with db.cursor() as cur:
        cur.execute(sql, params)
        db.commit()

    return jsonify({
        "message": "Security questions set/updated successfully",
        "questions": cols
    }), 200
