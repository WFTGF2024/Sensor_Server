"""
Unit tests for membership module.
"""

import pytest
from datetime import datetime, timedelta
from membership import (
    get_user_membership,
    check_storage_limit,
    check_file_size_limit,
    check_file_count_limit,
    update_user_storage_usage,
    format_bytes,
    log_membership_action
)


@pytest.fixture
def mock_membership_data():
    """Mock membership data for testing."""
    return {
        "membership_id": 1,
        "user_id": 1,
        "level_id": 1,
        "level_name": "普通用户",
        "level_code": "free",
        "storage_limit": 1073741824,  # 1GB
        "max_file_size": 52428800,     # 50MB
        "max_file_count": 100,
        "storage_used": 524288000,     # 500MB
        "file_count": 10,
        "points_earned": 0,
        "start_date": datetime.now(),
        "end_date": None,
        "is_active": True,
        "download_speed_limit": 0,
        "upload_speed_limit": 0,
        "daily_download_limit": 0,
        "daily_upload_limit": 0,
        "can_share_files": False,
        "can_create_public_links": False,
        "priority": 1,
        "is_storage_full": False,
        "storage_usage_percentage": 48.83,
        "end_date_formatted": "永久"
    }


def test_format_bytes():
    """Test bytes formatting function."""
    assert format_bytes(1024) == "1.00 KB"
    assert format_bytes(1048576) == "1.00 MB"
    assert format_bytes(1073741824) == "1.00 GB"
    assert format_bytes(1099511627776) == "1.00 TB"
    assert format_bytes(500) == "500.00 B"
    assert format_bytes(1536) == "1.50 KB"


def test_check_storage_limit_within_limit(mock_db_connection):
    """Test storage limit check when within limit."""
    mock_conn, mock_cursor = mock_db_connection
    
    with pytest.mock.patch('membership.get_db', return_value=mock_conn):
        mock_cursor.fetchone.return_value = {
            "storage_used": 524288000,  # 500MB
            "storage_limit": 1073741824  # 1GB
        }
        
        is_allowed, current_used, storage_limit, message = check_storage_limit(1, 104857600)  # 100MB
        
        assert is_allowed is True
        assert current_used == 524288000
        assert storage_limit == 1073741824
        assert "存储空间充足" in message


def test_check_storage_limit_exceeded(mock_db_connection):
    """Test storage limit check when limit is exceeded."""
    mock_conn, mock_cursor = mock_db_connection
    
    with pytest.mock.patch('membership.get_db', return_value=mock_conn):
        mock_cursor.fetchone.return_value = {
            "storage_used": 1048576000,  # 1GB
            "storage_limit": 1073741824  # 1GB
        }
        
        is_allowed, current_used, storage_limit, message = check_storage_limit(1, 104857600)  # 100MB
        
        assert is_allowed is False
        assert current_used == 1048576000
        assert storage_limit == 1073741824
        assert "存储空间不足" in message


def test_check_file_size_limit_within_limit(mock_db_connection):
    """Test file size limit check when within limit."""
    mock_conn, mock_cursor = mock_db_connection
    
    with pytest.mock.patch('membership.get_db', return_value=mock_conn):
        mock_cursor.fetchone.return_value = {
            "max_file_size": 52428800  # 50MB
        }
        
        is_allowed, max_file_size, message = check_file_size_limit(1, 10485760)  # 10MB
        
        assert is_allowed is True
        assert max_file_size == 52428800
        assert "文件大小符合要求" in message


def test_check_file_size_limit_exceeded(mock_db_connection):
    """Test file size limit check when limit is exceeded."""
    mock_conn, mock_cursor = mock_db_connection
    
    with pytest.mock.patch('membership.get_db', return_value=mock_conn):
        mock_cursor.fetchone.return_value = {
            "max_file_size": 52428800  # 50MB
        }
        
        is_allowed, max_file_size, message = check_file_size_limit(1, 104857600)  # 100MB
        
        assert is_allowed is False
        assert max_file_size == 52428800
        assert "文件大小超过限制" in message


def test_check_file_count_limit_within_limit(mock_db_connection):
    """Test file count limit check when within limit."""
    mock_conn, mock_cursor = mock_db_connection
    
    with pytest.mock.patch('membership.get_db', return_value=mock_conn):
        mock_cursor.fetchone.return_value = {
            "file_count": 50,
            "max_file_count": 100
        }
        
        is_allowed, current_count, max_count, message = check_file_count_limit(1)
        
        assert is_allowed is True
        assert current_count == 50
        assert max_count == 100
        assert "文件数量符合要求" in message


def test_check_file_count_limit_exceeded(mock_db_connection):
    """Test file count limit check when limit is exceeded."""
    mock_conn, mock_cursor = mock_db_connection
    
    with pytest.mock.patch('membership.get_db', return_value=mock_conn):
        mock_cursor.fetchone.return_value = {
            "file_count": 100,
            "max_file_count": 100
        }
        
        is_allowed, current_count, max_count, message = check_file_count_limit(1)
        
        assert is_allowed is False
        assert current_count == 100
        assert max_count == 100
        assert "文件数量已达到上限" in message


def test_update_user_storage_usage_increment(mock_db_connection):
    """Test updating user storage usage (increment)."""
    mock_conn, mock_cursor = mock_db_connection
    
    with pytest.mock.patch('membership.get_db', return_value=mock_conn):
        update_user_storage_usage(1, 104857600, increment=True)
        
        # Verify UPDATE query was called
        assert mock_cursor.execute.called
        call_args = mock_cursor.execute.call_args[0]
        assert "UPDATE user_memberships" in call_args[0]
        assert "storage_used = storage_used +" in call_args[0]
        assert "file_count = file_count + 1" in call_args[0]


def test_update_user_storage_usage_decrement(mock_db_connection):
    """Test updating user storage usage (decrement)."""
    mock_conn, mock_cursor = mock_db_connection
    
    with pytest.mock.patch('membership.get_db', return_value=mock_conn):
        update_user_storage_usage(1, 104857600, increment=False)
        
        # Verify UPDATE query was called
        assert mock_cursor.execute.called
        call_args = mock_cursor.execute.call_args[0]
        assert "UPDATE user_memberships" in call_args[0]
        assert "GREATEST(0, storage_used -" in call_args[0]
        assert "GREATEST(0, file_count - 1)" in call_args[0]


def test_log_membership_action(mock_db_connection):
    """Test logging membership action."""
    mock_conn, mock_cursor = mock_db_connection
    
    with pytest.mock.patch('membership.get_db', return_value=mock_conn):
        log_membership_action(
            user_id=1,
            action_type='upgrade',
            action_detail='升级到白银会员',
            old_level_id=1,
            new_level_id=2,
            operator_id=1
        )
        
        # Verify INSERT query was called
        assert mock_cursor.execute.called
        call_args = mock_cursor.execute.call_args[0]
        assert "INSERT INTO membership_logs" in call_args[0]


def test_get_user_membership_with_active_membership(mock_db_connection, mock_membership_data):
    """Test getting user membership when user has active membership."""
    mock_conn, mock_cursor = mock_db_connection
    
    with pytest.mock.patch('membership.get_db', return_value=mock_conn):
        mock_cursor.fetchone.return_value = mock_membership_data
        
        membership = get_user_membership(1)
        
        assert membership is not None
        assert membership["user_id"] == 1
        assert membership["level_name"] == "普通用户"
        assert membership["level_code"] == "free"
        assert membership["storage_limit"] == 1073741824


def test_get_user_membership_without_active_membership(mock_db_connection):
    """Test getting user membership when user has no active membership."""
    mock_conn, mock_cursor = mock_db_connection
    
    with pytest.mock.patch('membership.get_db', return_value=mock_conn):
        # First call: no active membership
        mock_cursor.fetchone.side_effect = [
            None,  # No active membership
            {      # Default free level
                "level_id": 1,
                "level_name": "普通用户",
                "level_code": "free",
                "storage_limit": 1073741824,
                "max_file_size": 52428800,
                "max_file_count": 100
            }
        ]
        
        membership = get_user_membership(1)
        
        assert membership is not None
        assert membership["membership_id"] is None
        assert membership["level_name"] == "普通用户"
        assert membership["level_code"] == "free"
        assert membership["storage_used"] == 0
        assert membership["file_count"] == 0


def test_storage_limit_edge_case(mock_db_connection):
    """Test storage limit check at exact boundary."""
    mock_conn, mock_cursor = mock_db_connection
    
    with pytest.mock.patch('membership.get_db', return_value=mock_conn):
        # Exactly at limit
        mock_cursor.fetchone.return_value = {
            "storage_used": 1073741824,  # Exactly 1GB
            "storage_limit": 1073741824  # 1GB
        }
        
        is_allowed, _, _, message = check_storage_limit(1, 1)  # 1 byte
        
        assert is_allowed is False
        assert "存储空间不足" in message


def test_file_size_limit_edge_case(mock_db_connection):
    """Test file size limit check at exact boundary."""
    mock_conn, mock_cursor = mock_db_connection
    
    with pytest.mock.patch('membership.get_db', return_value=mock_conn):
        # Exactly at limit
        mock_cursor.fetchone.return_value = {
            "max_file_size": 52428800  # Exactly 50MB
        }
        
        is_allowed, _, message = check_file_size_limit(1, 52428800)
        
        assert is_allowed is True
        assert "文件大小符合要求" in message


def test_file_count_limit_edge_case(mock_db_connection):
    """Test file count limit check at exact boundary."""
    mock_conn, mock_cursor = mock_db_connection
    
    with pytest.mock.patch('membership.get_db', return_value=mock_conn):
        # One less than limit
        mock_cursor.fetchone.return_value = {
            "file_count": 99,
            "max_file_count": 100
        }
        
        is_allowed, current_count, max_count, message = check_file_count_limit(1)
        
        assert is_allowed is True
        assert current_count == 99
        assert max_count == 100
        assert "文件数量符合要求" in message
