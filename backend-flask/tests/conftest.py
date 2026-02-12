"""
Pytest configuration and fixtures for Sensor_Flask tests.
"""

import pytest
import tempfile
import os
import sys
from unittest.mock import Mock, patch

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def test_client():
    """Create a test client for the Flask application."""
    # Set test environment
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['FLASK_SECRET_KEY'] = 'test-secret-key'
    
    from app import create_app
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        yield client

@pytest.fixture
def test_db_config():
    """Provide test database configuration."""
    return {
        "host": "localhost",
        "user": "test_user",
        "password": "test_password",
        "database": "modality_test",
        "charset": "utf8mb4",
        "use_unicode": True
    }

@pytest.fixture
def mock_db_connection():
    """Create a mock database connection."""
    mock_conn = Mock()
    mock_cursor = Mock()
    
    # Create proper context manager behavior
    cursor_context = Mock()
    cursor_context.__enter__ = Mock(return_value=mock_cursor)
    cursor_context.__exit__ = Mock(return_value=False)
    mock_conn.cursor.return_value = cursor_context
    
    return mock_conn, mock_cursor

@pytest.fixture
def test_user_data():
    """Provide test user data."""
    return {
        "username": "testuser",
        "password": "testpassword123",
        "email": "test@example.com",
        "phone": "1234567890",
        "qq": "123456",
        "wechat": "testwechat"
    }

@pytest.fixture
def test_file_data():
    """Provide test file data."""
    return {
        "file_name": "test.txt",
        "file_permission": "private",
        "file_size": 1024,
        "file_hash": "a" * 64  # Mock SHA-256 hash
    }

@pytest.fixture
def temp_upload_dir():
    """Create a temporary upload directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture
def authenticated_session(test_client, test_user_data):
    """Create an authenticated session for testing."""
    # Mock the database to return a user
    with patch('auth.get_db') as mock_get_db:
        mock_conn = Mock()
        mock_cursor = Mock()
        
        # Create proper context manager behavior
        cursor_context = Mock()
        cursor_context.__enter__ = Mock(return_value=mock_cursor)
        cursor_context.__exit__ = Mock(return_value=False)
        mock_conn.cursor.return_value = cursor_context
        
        mock_get_db.return_value = mock_conn
        
        # Mock user query
        mock_cursor.fetchone.return_value = {
            "user_id": 1,
            "username": test_user_data["username"],
            "password": "$pbkdf2-sha256$29000$...",  # Mock hashed password
            "email": test_user_data["email"],
            "phone": test_user_data["phone"],
            "qq": test_user_data["qq"],
            "wechat": test_user_data["wechat"],
            "point": 0
        }
        
        # Perform login
        with test_client.session_transaction() as session:
            session['user_id'] = 1
            session['username'] = test_user_data["username"]
        
        yield test_client