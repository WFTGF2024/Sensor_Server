"""
Integration tests for membership endpoints.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock


def test_get_membership_info_success(authenticated_session, mock_db_connection):
    """Test successful membership info retrieval."""
    client = authenticated_session
    mock_conn, mock_cursor = mock_db_connection
    
    with patch('membership.get_db', return_value=mock_conn):
        # Mock membership query
        mock_cursor.fetchone.return_value = {
            "membership_id": 1,
            "user_id": 1,
            "level_id": 1,
            "level_name": "普通用户",
            "level_code": "free",
            "storage_limit": 1073741824,
            "max_file_size": 52428800,
            "max_file_count": 100,
            "storage_used": 524288000,
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
        
        response = client.get('/membership/info')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["success"] is True
        assert "membership" in data
        assert data["membership"]["level_name"] == "普通用户"
        assert data["membership"]["level_code"] == "free"
        assert "storage_used_formatted" in data["membership"]
        assert "storage_limit_formatted" in data["membership"]


def test_get_membership_levels_success(test_client, mock_db_connection):
    """Test successful membership levels listing."""
    mock_conn, mock_cursor = mock_db_connection
    
    with patch('membership.get_db', return_value=mock_conn):
        # Mock membership levels query
        mock_cursor.fetchall.return_value = [
            {
                "level_id": 1,
                "level_name": "普通用户",
                "level_code": "free",
                "display_order": 1,
                "description": "免费用户，基础功能",
                "storage_limit": 1073741824,
                "max_file_size": 52428800,
                "max_file_count": 100,
                "download_speed_limit": 0,
                "upload_speed_limit": 0,
                "daily_download_limit": 0,
                "daily_upload_limit": 0,
                "can_share_files": False,
                "can_create_public_links": False,
                "priority": 1,
                "is_active": True
            },
            {
                "level_id": 2,
                "level_name": "白银会员",
                "level_code": "silver",
                "display_order": 2,
                "description": "白银会员，更多存储空间",
                "storage_limit": 5368709120,
                "max_file_size": 104857600,
                "max_file_count": 500,
                "download_speed_limit": 0,
                "upload_speed_limit": 0,
                "daily_download_limit": 0,
                "daily_upload_limit": 0,
                "can_share_files": True,
                "can_create_public_links": False,
                "priority": 2,
                "is_active": True
            }
        ]
        
        response = test_client.get('/membership/levels')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["success"] is True
        assert "levels" in data
        assert len(data["levels"]) == 2
        assert data["levels"][0]["level_code"] == "free"
        assert data["levels"][1]["level_code"] == "silver"


def test_upgrade_membership_success(authenticated_session, mock_db_connection):
    """Test successful membership upgrade."""
    client = authenticated_session
    mock_conn, mock_cursor = mock_db_connection
    
    with patch('membership.get_db', return_value=mock_conn):
        # Mock level query
        mock_cursor.fetchone.side_effect = [
            # First call: get level info
            {
                "level_id": 2,
                "level_name": "白银会员",
                "level_code": "silver",
                "storage_limit": 5368709120,
                "max_file_size": 104857600,
                "max_file_count": 500
            }
        ]
        
        upgrade_data = {
            "level_id": 2,
            "duration_days": 30
        }
        
        response = client.post(
            '/membership/upgrade',
            data=json.dumps(upgrade_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["success"] is True
        assert "message" in data
        assert "membership" in data


def test_upgrade_membership_missing_fields(authenticated_session):
    """Test membership upgrade with missing required fields."""
    client = authenticated_session
    
    response = client.post(
        '/membership/upgrade',
        data=json.dumps({"level_id": 2}),
        content_type='application/json'
    )
    
    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_upgrade_membership_invalid_level(authenticated_session, mock_db_connection):
    """Test membership upgrade with invalid level."""
    client = authenticated_session
    mock_conn, mock_cursor = mock_db_connection
    
    with patch('membership.get_db', return_value=mock_conn):
        # Mock level not found
        mock_cursor.fetchone.return_value = None
        
        upgrade_data = {
            "level_id": 999,
            "duration_days": 30
        }
        
        response = client.post(
            '/membership/upgrade',
            data=json.dumps(upgrade_data),
            content_type='application/json'
        )
        
        assert response.status_code == 404
        data = response.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "NOT_FOUND"


def test_renew_membership_success(authenticated_session, mock_db_connection):
    """Test successful membership renewal."""
    client = authenticated_session
    mock_conn, mock_cursor = mock_db_connection
    
    with patch('membership.get_db', return_value=mock_conn):
        # Mock existing membership
        end_date = datetime.now() + timedelta(days=10)
        mock_cursor.fetchone.return_value = {
            "membership_id": 1,
            "user_id": 1,
            "level_id": 2,
            "level_name": "白银会员",
            "level_code": "silver",
            "storage_limit": 5368709120,
            "max_file_size": 104857600,
            "max_file_count": 500,
            "storage_used": 0,
            "file_count": 0,
            "points_earned": 0,
            "start_date": datetime.now(),
            "end_date": end_date,
            "is_active": True,
            "download_speed_limit": 0,
            "upload_speed_limit": 0,
            "daily_download_limit": 0,
            "daily_upload_limit": 0,
            "can_share_files": True,
            "can_create_public_links": False,
            "priority": 2,
            "is_storage_full": False,
            "storage_usage_percentage": 0.0,
            "end_date_formatted": end_date.strftime('%Y-%m-%d')
        }
        
        renew_data = {
            "duration_days": 30
        }
        
        response = client.post(
            '/membership/renew',
            data=json.dumps(renew_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["success"] is True
        assert "message" in data


def test_renew_permanent_membership(authenticated_session, mock_db_connection):
    """Test renewing permanent membership (should return success message)."""
    client = authenticated_session
    mock_conn, mock_cursor = mock_db_connection
    
    with patch('membership.get_db', return_value=mock_conn):
        # Mock permanent membership (end_date is None)
        mock_cursor.fetchone.return_value = {
            "membership_id": 1,
            "user_id": 1,
            "level_id": 4,
            "level_name": "钻石会员",
            "level_code": "diamond",
            "storage_limit": 53687091200,
            "max_file_size": 1073741824,
            "max_file_count": 10000,
            "storage_used": 0,
            "file_count": 0,
            "points_earned": 0,
            "start_date": datetime.now(),
            "end_date": None,
            "is_active": True,
            "download_speed_limit": 0,
            "upload_speed_limit": 0,
            "daily_download_limit": 1000,
            "daily_upload_limit": 500,
            "can_share_files": True,
            "can_create_public_links": True,
            "priority": 4,
            "is_storage_full": False,
            "storage_usage_percentage": 0.0,
            "end_date_formatted": "永久"
        }
        
        renew_data = {
            "duration_days": 30
        }
        
        response = client.post(
            '/membership/renew',
            data=json.dumps(renew_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["success"] is True
        assert "永久会员" in data["message"]


def test_get_storage_stats_success(authenticated_session, mock_db_connection):
    """Test successful storage statistics retrieval."""
    client = authenticated_session
    mock_conn, mock_cursor = mock_db_connection
    
    with patch('membership.get_db', return_value=mock_conn):
        # Mock membership query
        mock_cursor.fetchone.return_value = {
            "membership_id": 1,
            "user_id": 1,
            "level_id": 1,
            "level_name": "普通用户",
            "level_code": "free",
            "storage_limit": 1073741824,
            "max_file_size": 52428800,
            "max_file_count": 100,
            "storage_used": 524288000,
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
        
        response = client.get('/membership/storage-stats')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["success"] is True
        assert "stats" in data
        assert data["stats"]["storage_used"] == 524288000
        assert data["stats"]["storage_limit"] == 1073741824
        assert "storage_used_formatted" in data["stats"]
        assert "storage_limit_formatted" in data["stats"]
        assert "storage_available" in data["stats"]
        assert data["stats"]["storage_usage_percentage"] == 48.83


def test_get_benefits_success(authenticated_session, mock_db_connection):
    """Test successful benefits retrieval."""
    client = authenticated_session
    mock_conn, mock_cursor = mock_db_connection
    
    with patch('membership.get_db', return_value=mock_conn):
        # Mock membership query
        mock_cursor.fetchone.return_value = {
            "membership_id": 1,
            "user_id": 1,
            "level_id": 2,
            "level_name": "白银会员",
            "level_code": "silver",
            "storage_limit": 5368709120,
            "max_file_size": 104857600,
            "max_file_count": 500,
            "storage_used": 0,
            "file_count": 0,
            "points_earned": 0,
            "start_date": datetime.now(),
            "end_date": None,
            "is_active": True,
            "download_speed_limit": 0,
            "upload_speed_limit": 0,
            "daily_download_limit": 0,
            "daily_upload_limit": 0,
            "can_share_files": True,
            "can_create_public_links": False,
            "priority": 2,
            "is_storage_full": False,
            "storage_usage_percentage": 0.0,
            "end_date_formatted": "永久"
        }
        
        # Mock benefits query
        mock_cursor.fetchall.return_value = [
            {
                "benefit_type": "storage_limit",
                "benefit_value": "5GB",
                "description": "存储容量5GB",
                "is_active": True
            },
            {
                "benefit_type": "max_file_size",
                "benefit_value": "100MB",
                "description": "单文件最大100MB",
                "is_active": True
            },
            {
                "benefit_type": "can_share_files",
                "benefit_value": "true",
                "description": "可以分享文件",
                "is_active": True
            }
        ]
        
        response = client.get('/membership/benefits')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["success"] is True
        assert "level_name" in data
        assert "level_code" in data
        assert "benefits" in data
        assert len(data["benefits"]) == 3
        assert data["level_name"] == "白银会员"


def test_membership_endpoints_unauthenticated(test_client):
    """Test membership endpoints without authentication."""
    endpoints = [
        ('GET', '/membership/info'),
        ('GET', '/membership/levels'),
        ('POST', '/membership/upgrade'),
        ('POST', '/membership/renew'),
        ('GET', '/membership/storage-stats'),
        ('GET', '/membership/benefits')
    ]
    
    for method, endpoint in endpoints:
        if method == 'GET':
            response = test_client.get(endpoint)
        elif method == 'POST':
            response = test_client.post(
                endpoint,
                data=json.dumps({}),
                content_type='application/json'
            )
        
        assert response.status_code == 401
        data = response.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"
