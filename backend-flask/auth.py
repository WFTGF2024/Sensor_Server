# auth.py - User authentication module with improved error handling

import os
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db
from errors import (
    ValidationError, AuthenticationError, AuthorizationError, 
    NotFoundError, ConflictError, validate_required_fields
)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    POST /auth/register
    Register a new user.
    
    Required fields: username, password
    Optional fields: email, phone, qq, wechat
    
    Returns:
        JSON response with user_id and success message
    """
    data = request.get_json() or {}
    
    # Validate required fields
    try:
        validate_required_fields(
            data, 
            ['username', 'password'],
            {'username': 'Username for the new account', 'password': 'Password for the new account'}
        )
    except ValidationError as e:
        raise e
    
    username = data['username']
    raw_password = data['password']
    email = data.get('email')
    phone = data.get('phone')
    qq = data.get('qq')
    wechat = data.get('wechat')
    
    # Validate password strength (basic check)
    if len(raw_password) < 6:
        raise ValidationError(
            "Password must be at least 6 characters long",
            details={"min_length": 6, "actual_length": len(raw_password)}
        )
    
    hashed_pw = generate_password_hash(raw_password, method='pbkdf2:sha256', salt_length=16)
    
    db = get_db()
    try:
        with db.cursor() as cur:
            # Check username uniqueness
            cur.execute("SELECT user_id FROM users WHERE username=%s", (username,))
            if cur.fetchone():
                raise ConflictError(f"Username '{username}' is already taken")
            
            # Optional uniqueness checks for email and phone
            if email:
                cur.execute("SELECT user_id FROM users WHERE email=%s", (email,))
                if cur.fetchone():
                    raise ConflictError(f"Email '{email}' is already registered")
            
            if phone:
                cur.execute("SELECT user_id FROM users WHERE phone=%s", (phone,))
                if cur.fetchone():
                    raise ConflictError(f"Phone number '{phone}' is already registered")
            
            # Create user
            cur.execute("""
                INSERT INTO users
                  (username, password, email, phone, qq, wechat, point)
                VALUES (%s, %s, %s, %s, %s, %s, 0)
            """, (username, hashed_pw, email, phone, qq, wechat))
            user_id = cur.lastrowid
            
            # Create login status record
            cur.execute("""
                INSERT INTO user_login_status (user_id, login_time, ip_address)
                VALUES (%s, NOW(), %s)
            """, (user_id, request.remote_addr))
            
            db.commit()
            
            # Set session
            session['user_id'] = user_id
            session['username'] = username
            
            return jsonify({
                "success": True,
                "message": "User registered successfully",
                "user_id": user_id,
                "username": username
            }), 201
            
    except Exception as e:
        db.rollback()
        raise

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    POST /auth/login
    Authenticate user and create session.
    
    Required fields: username, password
    
    Returns:
        JSON response with user information
    """
    data = request.get_json() or {}
    
    # Validate required fields
    try:
        validate_required_fields(
            data,
            ['username', 'password'],
            {'username': 'Username for login', 'password': 'Password for login'}
        )
    except ValidationError as e:
        raise e
    
    username = data['username']
    password = data['password']
    
    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            SELECT user_id, username, password, email, phone, qq, wechat, point
            FROM users
            WHERE username=%s
        """, (username,))
        user = cur.fetchone()
    
    if not user or not check_password_hash(user['password'], password):
        raise AuthenticationError("Invalid username or password")
    
    # Update login status
    with db.cursor() as cur:
        cur.execute("""
            INSERT INTO user_login_status (user_id, login_time, ip_address)
            VALUES (%s, NOW(), %s)
            ON DUPLICATE KEY UPDATE
                login_time = NOW(),
                ip_address = %s
        """, (user['user_id'], request.remote_addr, request.remote_addr))
        db.commit()
    
    # Set session
    session['user_id'] = user['user_id']
    session['username'] = user['username']
    
    # Remove password from response
    user.pop('password', None)
    
    return jsonify({
        "success": True,
        "message": "Login successful",
        "user": user
    }), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    POST /auth/logout
    Clear user session.
    
    Returns:
        JSON response with success message
    """
    if 'user_id' not in session:
        raise AuthenticationError("No active session to logout from")
    
    user_id = session['user_id']
    
    # Clear login status
    db = get_db()
    with db.cursor() as cur:
        cur.execute("DELETE FROM user_login_status WHERE user_id=%s", (user_id,))
        db.commit()
    
    # Clear session
    session.clear()
    
    return jsonify({
        "success": True,
        "message": "Logout successful"
    }), 200

@auth_bp.route('/profile', methods=['PUT'])
def update_profile():
    """
    PUT /auth/profile
    Update user profile information.
    
    Optional fields: email, phone, qq, wechat
    
    Returns:
        JSON response with updated user information
    """
    if 'user_id' not in session:
        raise AuthenticationError("Authentication required")
    
    user_id = session['user_id']
    data = request.get_json() or {}
    
    # Validate at least one field is provided
    updatable_fields = ['email', 'phone', 'qq', 'wechat']
    if not any(field in data for field in updatable_fields):
        raise ValidationError(
            "At least one field must be provided for update",
            details={"updatable_fields": updatable_fields}
        )
    
    db = get_db()
    try:
        with db.cursor() as cur:
            # Check for uniqueness conflicts
            if 'email' in data and data['email']:
                cur.execute(
                    "SELECT user_id FROM users WHERE email=%s AND user_id != %s",
                    (data['email'], user_id)
                )
                if cur.fetchone():
                    raise ConflictError(f"Email '{data['email']}' is already registered by another user")
            
            if 'phone' in data and data['phone']:
                cur.execute(
                    "SELECT user_id FROM users WHERE phone=%s AND user_id != %s",
                    (data['phone'], user_id)
                )
                if cur.fetchone():
                    raise ConflictError(f"Phone number '{data['phone']}' is already registered by another user")
            
            # Build update query
            updates = []
            params = []
            
            for field in updatable_fields:
                if field in data:
                    updates.append(f"{field} = %s")
                    params.append(data[field])
            
            if updates:
                params.append(user_id)
                cur.execute(
                    f"UPDATE users SET {', '.join(updates)} WHERE user_id = %s",
                    tuple(params)
                )
                db.commit()
        
        # Get updated user info
        with db.cursor() as cur:
            cur.execute("""
                SELECT user_id, username, email, phone, qq, wechat, point
                FROM users
                WHERE user_id=%s
            """, (user_id,))
            user = cur.fetchone()
        
        return jsonify({
            "success": True,
            "message": "Profile updated successfully",
            "user": user
        }), 200
        
    except Exception as e:
        db.rollback()
        raise

@auth_bp.route('/password', methods=['PUT'])
def change_password():
    """
    PUT /auth/password
    Change user password.
    
    Required fields: current_password, new_password
    
    Returns:
        JSON response with success message
    """
    if 'user_id' not in session:
        raise AuthenticationError("Authentication required")
    
    user_id = session['user_id']
    data = request.get_json() or {}
    
    # Validate required fields
    try:
        validate_required_fields(
            data,
            ['current_password', 'new_password'],
            {
                'current_password': 'Current password for verification',
                'new_password': 'New password to set'
            }
        )
    except ValidationError as e:
        raise e
    
    current_password = data['current_password']
    new_password = data['new_password']
    
    # Validate new password strength
    if len(new_password) < 6:
        raise ValidationError(
            "New password must be at least 6 characters long",
            details={"min_length": 6, "actual_length": len(new_password)}
        )
    
    db = get_db()
    with db.cursor() as cur:
        cur.execute("SELECT password FROM users WHERE user_id=%s", (user_id,))
        row = cur.fetchone()
    
    if not row or not check_password_hash(row['password'], current_password):
        raise AuthorizationError("Current password is incorrect")
    
    new_hashed = generate_password_hash(new_password, method='pbkdf2:sha256', salt_length=16)
    
    with db.cursor() as cur:
        cur.execute("UPDATE users SET password=%s WHERE user_id=%s", (new_hashed, user_id))
        db.commit()
    
    return jsonify({
        "success": True,
        "message": "Password changed successfully"
    }), 200

@auth_bp.route('/account', methods=['DELETE'])
def delete_account():
    """
    DELETE /auth/account
    Delete user account.
    
    Required fields: password
    
    Returns:
        JSON response with success message
    """
    if 'user_id' not in session:
        raise AuthenticationError("Authentication required")
    
    user_id = session['user_id']
    data = request.get_json() or {}
    
    # Validate required field
    try:
        validate_required_fields(
            data,
            ['password'],
            {'password': 'Password for verification'}
        )
    except ValidationError as e:
        raise e
    
    password = data['password']
    
    db = get_db()
    with db.cursor() as cur:
        # Verify current password
        cur.execute("SELECT password FROM users WHERE user_id=%s", (user_id,))
        row = cur.fetchone()
        
        if not row or not check_password_hash(row['password'], password):
            raise AuthorizationError("Password is incorrect")
        
        # Delete user (cascades to user_questions); also clean login status
        cur.execute("DELETE FROM user_login_status WHERE user_id=%s", (user_id,))
        cur.execute("DELETE FROM users WHERE user_id=%s", (user_id,))
        db.commit()
    
    session.clear()
    
    return jsonify({
        "success": True,
        "message": "Account deleted successfully"
    }), 200

@auth_bp.route('/user', methods=['GET'])
def get_profile():
    """
    GET /auth/user
    Get current user profile information.
    
    Returns:
        JSON response with user information
    """
    if 'user_id' not in session:
        raise AuthenticationError("Authentication required")
    
    user_id = session['user_id']
    
    db = get_db()
    with db.cursor() as cur:
        cur.execute("""
            SELECT user_id, username, email, phone, qq, wechat, point
            FROM users
            WHERE user_id=%s
        """, (user_id,))
        user = cur.fetchone()
    
    if not user:
        raise NotFoundError("User not found")
    
    return jsonify({
        "success": True,
        "user": user
    }), 200