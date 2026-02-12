"""
Integration tests for authentication endpoints.
"""

import pytest
import json
from unittest.mock import Mock, patch
from werkzeug.security import generate_password_hash

def test_register_endpoint_success(test_client, test_user_data, mock_db_connection):
    """Test successful user registration."""
    mock_conn, mock_cursor = mock_db_connection
    
    with patch('auth.get_db', return_value=mock_conn):
        # Mock database queries
        mock_cursor.fetchone.side_effect = [None, None, None]  # No existing user
        mock_cursor.lastrowid = 1
        
        response = test_client.post(
            '/auth/register',
            data=json.dumps(test_user_data),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = response.get_json()
        
        assert data["success"] is True
        assert data["message"] == "User registered successfully"
        assert data["user_id"] == 1
        assert data["username"] == test_user_data["username"]
        
        # Verify session was set
        with test_client.session_transaction() as session:
            assert session['user_id'] == 1
            assert session['username'] == test_user_data["username"]

def test_register_endpoint_missing_fields(test_client):
    """Test registration with missing required fields."""
    # Missing password
    data = {"username": "testuser"}
    response = test_client.post(
        '/auth/register',
        data=json.dumps(data),
        content_type='application/json'
    )
    
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "password" in data["error"]["message"].lower()
    assert "missing_fields" in data["error"]["details"]

def test_register_endpoint_weak_password(test_client):
    """Test registration with weak password."""
    data = {
        "username": "testuser",
        "password": "123"  # Too short
    }
    
    response = test_client.post(
        '/auth/register',
        data=json.dumps(data),
        content_type='application/json'
    )
    
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "6 characters" in data["error"]["message"]

def test_register_endpoint_username_taken(test_client, test_user_data, mock_db_connection):
    """Test registration with taken username."""
    mock_conn, mock_cursor = mock_db_connection
    
    with patch('auth.get_db', return_value=mock_conn):
        # Mock that username already exists
        mock_cursor.fetchone.return_value = {"user_id": 1}
        
        response = test_client.post(
            '/auth/register',
            data=json.dumps(test_user_data),
            content_type='application/json'
        )
        
        assert response.status_code == 409
        data = response.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "CONFLICT"
        assert "already taken" in data["error"]["message"]

def test_login_endpoint_success(test_client, test_user_data, mock_db_connection):
    """Test successful login."""
    mock_conn, mock_cursor = mock_db_connection
    
    with patch('auth.get_db', return_value=mock_conn):
        # Mock user query with hashed password
        hashed_password = generate_password_hash(
            test_user_data["password"],
            method='pbkdf2:sha256',
            salt_length=16
        )
        
        mock_cursor.fetchone.return_value = {
            "user_id": 1,
            "username": test_user_data["username"],
            "password": hashed_password,
            "email": test_user_data["email"],
            "phone": test_user_data["phone"],
            "qq": test_user_data["qq"],
            "wechat": test_user_data["wechat"],
            "point": 0
        }
        
        response = test_client.post(
            '/auth/login',
            data=json.dumps({
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["success"] is True
        assert data["message"] == "Login successful"
        assert data["user"]["user_id"] == 1
        assert data["user"]["username"] == test_user_data["username"]
        assert "password" not in data["user"]  # Password should not be in response
        
        # Verify session was set
        with test_client.session_transaction() as session:
            assert session['user_id'] == 1
            assert session['username'] == test_user_data["username"]

def test_login_endpoint_invalid_credentials(test_client, mock_db_connection):
    """Test login with invalid credentials."""
    mock_conn, mock_cursor = mock_db_connection
    
    with patch('auth.get_db', return_value=mock_conn):
        # Mock user not found
        mock_cursor.fetchone.return_value = None
        
        response = test_client.post(
            '/auth/login',
            data=json.dumps({
                "username": "nonexistent",
                "password": "wrongpassword"
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 401
        data = response.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"
        assert "invalid" in data["error"]["message"].lower()

def test_login_endpoint_missing_fields(test_client):
    """Test login with missing fields."""
    # Missing password
    response = test_client.post(
        '/auth/login',
        data=json.dumps({"username": "testuser"}),
        content_type='application/json'
    )
    
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"

def test_logout_endpoint_success(authenticated_session):
    """Test successful logout."""
    client = authenticated_session
    
    response = client.post('/auth/logout')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["message"] == "Logout successful"
    
    # Verify session was cleared
    with client.session_transaction() as session:
        assert 'user_id' not in session
        assert 'username' not in session

def test_logout_endpoint_no_session(test_client):
    """Test logout without active session."""
    response = test_client.post('/auth/logout')
    
    assert response.status_code == 401
    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "AUTHENTICATION_ERROR"

def test_get_profile_endpoint_success(authenticated_session, mock_db_connection):
    """Test successful profile retrieval."""
    client = authenticated_session
    mock_conn, mock_cursor = mock_db_connection
    
    with patch('auth.get_db', return_value=mock_conn):
        # Mock user query
        mock_cursor.fetchone.return_value = {
            "user_id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "phone": "1234567890",
            "qq": "123456",
            "wechat": "testwechat",
            "point": 100
        }
        
        response = client.get('/auth/user')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["success"] is True
        assert data["user"]["user_id"] == 1
        assert data["user"]["username"] == "testuser"
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["point"] == 100

def test_get_profile_endpoint_unauthenticated(test_client):
    """Test profile retrieval without authentication."""
    response = test_client.get('/auth/user')
    
    assert response.status_code == 401
    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "AUTHENTICATION_ERROR"

def test_update_profile_endpoint_success(authenticated_session, mock_db_connection):
    """Test successful profile update."""
    client = authenticated_session
    mock_conn, mock_cursor = mock_db_connection
    
    with patch('auth.get_db', return_value=mock_conn):
        # Mock no conflicts and updated user data
        mock_cursor.fetchone.side_effect = [None, None, {
            "user_id": 1,
            "username": "testuser",
            "email": "newemail@example.com",
            "phone": "9876543210",
            "qq": "123456",
            "wechat": "testwechat",
            "point": 100
        }]
        
        update_data = {
            "email": "newemail@example.com",
            "phone": "9876543210"
        }
        
        response = client.put(
            '/auth/profile',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["success"] is True
        assert data["message"] == "Profile updated successfully"

def test_update_profile_endpoint_no_fields(authenticated_session):
    """Test profile update with no fields provided."""
    client = authenticated_session
    
    response = client.put(
        '/auth/profile',
        data=json.dumps({}),
        content_type='application/json'
    )
    
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "at least one field" in data["error"]["message"].lower()

def test_update_profile_endpoint_email_conflict(authenticated_session, mock_db_connection):
    """Test profile update with email conflict."""
    client = authenticated_session
    mock_conn, mock_cursor = mock_db_connection
    
    with patch('auth.get_db', return_value=mock_conn):
        # Mock email already taken by another user
        mock_cursor.fetchone.return_value = {"user_id": 2}
        
        update_data = {"email": "taken@example.com"}
        
        response = client.put(
            '/auth/profile',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 409
        data = response.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "CONFLICT"
        assert "already registered" in data["error"]["message"]

def test_change_password_endpoint_success(authenticated_session, mock_db_connection):
    """Test successful password change."""
    client = authenticated_session
    mock_conn, mock_cursor = mock_db_connection
    
    with patch('auth.get_db', return_value=mock_conn):
        # Mock current password verification
        hashed_password = generate_password_hash(
            "oldpassword123",
            method='pbkdf2:sha256',
            salt_length=16
        )
        mock_cursor.fetchone.return_value = {"password": hashed_password}
        
        password_data = {
            "current_password": "oldpassword123",
            "new_password": "newpassword456"
        }
        
        response = client.put(
            '/auth/password',
            data=json.dumps(password_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["message"] == "Password changed successfully"

def test_change_password_endpoint_wrong_current_password(authenticated_session, mock_db_connection):
    """Test password change with wrong current password."""
    client = authenticated_session
    mock_conn, mock_cursor = mock_db_connection
    
    with patch('auth.get_db', return_value=mock_conn):
        # Mock password verification failure
        hashed_password = generate_password_hash(
            "correctpassword",
            method='pbkdf2:sha256',
            salt_length=16
        )
        mock_cursor.fetchone.return_value = {"password": hashed_password}
        
        password_data = {
            "current_password": "wrongpassword",
            "new_password": "newpassword456"
        }
        
        response = client.put(
            '/auth/password',
            data=json.dumps(password_data),
            content_type='application/json'
        )
        
        assert response.status_code == 403
        data = response.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "AUTHORIZATION_ERROR"
        assert "incorrect" in data["error"]["message"].lower()

def test_change_password_endpoint_weak_new_password(authenticated_session, mock_db_connection):
    """Test password change with weak new password."""
    client = authenticated_session
    mock_conn, mock_cursor = mock_db_connection
    
    with patch('auth.get_db', return_value=mock_conn):
        # Mock current password verification
        hashed_password = generate_password_hash(
            "oldpassword123",
            method='pbkdf2:sha256',
            salt_length=16
        )
        mock_cursor.fetchone.return_value = {"password": hashed_password}
        
        password_data = {
            "current_password": "oldpassword123",
            "new_password": "123"  # Too short
        }
        
        response = client.put(
            '/auth/password',
            data=json.dumps(password_data),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "6 characters" in data["error"]["message"]

def test_delete_account_endpoint_success(authenticated_session, mock_db_connection):
    """Test successful account deletion."""
    client = authenticated_session
    mock_conn, mock_cursor = mock_db_connection
    
    with patch('auth.get_db', return_value=mock_conn):
        # Mock password verification
        hashed_password = generate_password_hash(
            "mypassword123",
            method='pbkdf2:sha256',
            salt_length=16
        )
        mock_cursor.fetchone.return_value = {"password": hashed_password}
        
        delete_data = {"password": "mypassword123"}
        
        response = client.delete(
            '/auth/account',
            data=json.dumps(delete_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["message"] == "Account deleted successfully"
        
        # Verify session was cleared
        with client.session_transaction() as session:
            assert 'user_id' not in session
            assert 'username' not in session

def test_delete_account_endpoint_wrong_password(authenticated_session, mock_db_connection):
    """Test account deletion with wrong password."""
    client = authenticated_session
    mock_conn, mock_cursor = mock_db_connection
    
    with patch('auth.get_db', return_value=mock_conn):
        # Mock password verification failure
        hashed_password = generate_password_hash(
            "correctpassword",
            method='pbkdf2:sha256',
            salt_length=16
        )
        mock_cursor.fetchone.return_value = {"password": hashed_password}
        
        delete_data = {"password": "wrongpassword"}
        
        response = client.delete(
            '/auth/account',
            data=json.dumps(delete_data),
            content_type='application/json'
        )
        
        assert response.status_code == 403
        data = response.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "AUTHORIZATION_ERROR"
        assert "incorrect" in data["error"]["message"].lower()