# Sensor_Flask API Documentation

## Overview

This document provides comprehensive API documentation for the Sensor_Flask backend service. The API follows RESTful conventions and uses JSON for request and response bodies.

**Base URL**: `http://localhost:5000` or `http://120.79.25.184:5000`

## Authentication

Most endpoints require authentication via session-based login. Include session cookies in your requests after logging in.

## Response Format

All responses follow this standard format:

### Success Response
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { ... }
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "status": 400,
    "details": { ... }
  }
}
```

## HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | OK - Request successful |
| 201 | Created - Resource created successfully |
| 400 | Bad Request - Invalid request data |
| 401 | Unauthorized - Authentication required |
| 403 | Forbidden - Authorization failed |
| 404 | Not Found - Resource not found |
| 409 | Conflict - Resource already exists |
| 413 | Request Entity Too Large - File size exceeds limit |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server error |
| 503 | Service Unavailable - Service temporarily unavailable |

---

## API Endpoints

### Authentication Endpoints (`/api/auth`)

#### 1. Register User

Register a new user account.

**Endpoint**: `POST /api/auth/register`

**Request Body**:
```json
{
  "username": "string (required, 3-50 chars, alphanumeric and underscore only)",
  "password": "string (required, 6-100 chars)",
  "email": "string (optional, valid email format)",
  "phone": "string (optional, Chinese mobile format)",
  "qq": "string (optional, max 20 chars)",
  "wechat": "string (optional, max 50 chars)"
}
```

**Success Response** (201):
```json
{
  "success": true,
  "message": "注册成功",
  "user_id": 1,
  "username": "testuser"
}
```

**Error Responses**:
- `400 VALIDATION_ERROR`: Invalid username format, password too short, or invalid email/phone
- `409 CONFLICT`: Username, email, or phone already taken

**Example Request**:
```bash
curl -X POST http://120.79.25.184:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "securepass123",
    "email": "test@example.com"
  }'
```

---

#### 2. Login

Authenticate user and create session.

**Endpoint**: `POST /api/auth/login`

**Request Body**:
```json
{
  "username": "string (required)",
  "password": "string (required)"
}
```

**Success Response** (200):
```json
{
  "success": true,
  "message": "登录成功",
  "user": {
    "user_id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "phone": "13800138000",
    "qq": "123456",
    "wechat": "testwechat",
    "is_admin": false,
    "membership": {
      "level_code": "free",
      "level_name": "普通用户",
      "storage_used": 0,
      "storage_limit": 1073741824,
      "storage_used_formatted": "0 B",
      "storage_limit_formatted": "1.00 GB",
      "max_file_size": 52428800,
      "max_file_size_formatted": "50.00 MB"
    }
  }
}
```

**Error Responses**:
- `400 VALIDATION_ERROR`: Missing username or password
- `401 AUTHENTICATION_ERROR`: Invalid username or password

---

#### 3. Logout

Clear user session.

**Endpoint**: `POST /api/auth/logout`

**Authentication**: Required

**Success Response** (200):
```json
{
  "success": true,
  "message": "登出成功"
}
```

**Error Responses**:
- `401 AUTHENTICATION_ERROR`: No active session

---

#### 4. Get User Profile

Get current user's profile information.

**Endpoint**: `GET /api/auth/user`

**Authentication**: Required

**Success Response** (200):
```json
{
  "success": true,
  "user": {
    "user_id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "phone": "13800138000",
    "qq": "123456",
    "wechat": "testwechat",
    "membership": { ... }
  }
}
```

**Error Responses**:
- `401 AUTHENTICATION_ERROR`: Authentication required
- `404 NOT_FOUND`: User not found

---

#### 5. Update Profile

Update user profile information.

**Endpoint**: `PUT /api/auth/user` or `PUT /api/auth/profile`

**Authentication**: Required

**Request Body**:
```json
{
  "email": "string (optional, valid email)",
  "phone": "string (optional, Chinese mobile format)",
  "qq": "string (optional, max 20 chars)",
  "wechat": "string (optional, max 50 chars)"
}
```

**Success Response** (200):
```json
{
  "success": true,
  "message": "资料更新成功",
  "user": { ... }
}
```

**Error Responses**:
- `400 VALIDATION_ERROR`: Invalid email or phone format
- `401 AUTHENTICATION_ERROR`: Authentication required
- `409 CONFLICT`: Email or phone already taken

---

#### 6. Change Password

Change user password.

**Endpoint**: `PUT /api/auth/password`

**Authentication**: Required

**Request Body**:
```json
{
  "current_password": "string (required)",
  "new_password": "string (required, 6-100 chars)"
}
```

**Success Response** (200):
```json
{
  "success": true,
  "message": "密码修改成功"
}
```

**Error Responses**:
- `400 VALIDATION_ERROR`: New password too short or same as current
- `401 AUTHENTICATION_ERROR`: Current password incorrect

---

#### 7. Delete Account

Delete user account.

**Endpoint**: `DELETE /api/auth/account`

**Authentication**: Required

**Request Body**:
```json
{
  "password": "string (required)"
}
```

**Success Response** (200):
```json
{
  "success": true,
  "message": "账户已删除"
}
```

**Error Responses**:
- `400 VALIDATION_ERROR`: Missing password
- `401 AUTHENTICATION_ERROR`: Incorrect password

---

#### 8. Check Username Availability

Check if a username is available.

**Endpoint**: `POST /api/auth/check-username`

**Request Body**:
```json
{
  "username": "string (required)"
}
```

**Success Response** (200):
```json
{
  "success": true,
  "available": true,
  "message": "用户名可用"
}
```

---

#### 9. Check Session Status

Check current session status.

**Endpoint**: `GET /api/auth/session`

**Success Response** (200):
```json
{
  "success": true,
  "authenticated": true,
  "user_id": 1,
  "username": "testuser",
  "is_admin": false
}
```

---

### File Management Endpoints (`/api/download`)

#### 10. Upload File

Upload a file to the server.

**Endpoint**: `POST /api/download/upload`

**Authentication**: Required

**Request**: Multipart form data
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | file | Yes | The file to upload |
| file_permission | string | No | `private` (default) or `public` |
| description | string | No | File description (max 1000 chars) |

**Success Response** (201):
```json
{
  "success": true,
  "message": "文件上传成功",
  "file_id": 1,
  "file_name": "example.zip",
  "file_permission": "private",
  "description": "",
  "file_hash": "a1b2c3d4e5f6...",
  "file_size": 1048576,
  "file_size_formatted": "1.00 MB",
  "uploaded_at": "2026-02-22 12:00:00"
}
```

**Error Responses**:
- `400 VALIDATION_ERROR`: No file provided, empty filename, or invalid permission
- `401 AUTHENTICATION_ERROR`: Authentication required
- `413 REQUEST_ENTITY_TOO_LARGE`: File size exceeds limit (256MB)
- `500 FILE_OPERATION_ERROR`: Upload failed

**Example Request**:
```bash
curl -X POST http://120.79.25.184:5000/api/download/upload \
  -F "file=@/path/to/file.zip" \
  -F "file_permission=private" \
  -F "description=My file" \
  -b cookies.txt
```

---

#### 11. List Files

Get list of current user's files.

**Endpoint**: `GET /api/download/files`

**Authentication**: Required

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | int | 1 | Page number |
| page_size | int | 20 | Items per page (max 100) |

**Success Response** (200):
```json
{
  "success": true,
  "files": [
    {
      "file_id": 1,
      "file_name": "example.zip",
      "file_size": 1048576,
      "file_permission": "private",
      "description": "",
      "download_count": 0,
      "created_at": "2026-02-22 12:00:00"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 1,
    "total_pages": 1
  }
}
```

---

#### 12. List Public Files

Get list of all public files.

**Endpoint**: `GET /api/download/public`

**Authentication**: Not required

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | int | 1 | Page number |
| page_size | int | 20 | Items per page (max 100) |

**Success Response** (200):
```json
{
  "success": true,
  "files": [ ... ],
  "pagination": { ... }
}
```

---

#### 13. Get File Info

Get detailed information about a specific file.

**Endpoint**: `GET /api/download/file/<file_id>`

**Authentication**: Required

**Success Response** (200):
```json
{
  "success": true,
  "file": {
    "file_id": 1,
    "file_name": "example.zip",
    "file_size": 1048576,
    "file_path": "/path/to/file",
    "file_permission": "private",
    "description": "",
    "file_hash": "a1b2c3d4...",
    "download_count": 0,
    "created_at": "2026-02-22 12:00:00"
  }
}
```

**Error Responses**:
- `401 AUTHENTICATION_ERROR`: Authentication required
- `404 NOT_FOUND`: File not found

---

#### 14. Download File

Download a file by ID.

**Endpoint**: `GET /api/download/download/<file_id>`

**Authentication**: Required

**Success Response**: File content with appropriate headers

**Error Responses**:
- `401 AUTHENTICATION_ERROR`: Authentication required
- `404 NOT_FOUND`: File not found or deleted from disk
- `500 FILE_OPERATION_ERROR`: Download failed

---

#### 15. Update File

Update file metadata.

**Endpoint**: `PUT /api/download/file/<file_id>`

**Authentication**: Required

**Request Body**:
```json
{
  "file_name": "string (optional, max 255 chars)",
  "file_permission": "public|private (optional)",
  "description": "string (optional, max 1000 chars)"
}
```

**Success Response** (200):
```json
{
  "success": true,
  "message": "文件信息更新成功"
}
```

**Error Responses**:
- `400 VALIDATION_ERROR`: Invalid parameters
- `401 AUTHENTICATION_ERROR`: Authentication required
- `404 NOT_FOUND`: File not found

---

#### 16. Delete File

Delete a file.

**Endpoint**: `DELETE /api/download/file/<file_id>`

**Authentication**: Required

**Success Response** (200):
```json
{
  "success": true,
  "message": "文件删除成功"
}
```

**Error Responses**:
- `401 AUTHENTICATION_ERROR`: Authentication required
- `404 NOT_FOUND`: File not found

---

#### 17. Search Files

Search files by keyword.

**Endpoint**: `GET /api/download/search`

**Authentication**: Required

**Query Parameters**:
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| keyword | string | Yes | Search keyword (max 100 chars) |
| page | int | No | Page number (default 1) |
| page_size | int | No | Items per page (default 20, max 100) |

**Success Response** (200):
```json
{
  "success": true,
  "files": [ ... ],
  "keyword": "search_term",
  "pagination": { ... }
}
```

---

### Membership Endpoints (`/api/membership`)

#### 18. Get Membership Info

Get current user's membership information.

**Endpoint**: `GET /api/membership/info`

**Authentication**: Required

**Success Response** (200):
```json
{
  "success": true,
  "membership": {
    "level_id": 1,
    "level_code": "free",
    "level_name": "普通用户",
    "storage_used": 0,
    "storage_limit": 1073741824,
    "storage_used_formatted": "0 B",
    "storage_limit_formatted": "1.00 GB",
    "max_file_size": 52428800,
    "max_file_size_formatted": "50.00 MB",
    "max_file_count": 100,
    "start_date": null,
    "end_date": null
  }
}
```

---

#### 19. List Membership Levels

Get all available membership levels.

**Endpoint**: `GET /api/membership/levels`

**Authentication**: Not required

**Success Response** (200):
```json
{
  "success": true,
  "levels": [
    {
      "level_id": 1,
      "level_code": "free",
      "level_name": "普通用户",
      "storage_limit": 1073741824,
      "storage_limit_formatted": "1.00 GB",
      "max_file_size": 52428800,
      "max_file_size_formatted": "50.00 MB",
      "max_file_count": 100
    }
  ]
}
```

---

#### 20. Upgrade Membership

Upgrade to a higher membership level.

**Endpoint**: `POST /api/membership/upgrade`

**Authentication**: Required

**Request Body**:
```json
{
  "level_id": "int (required)",
  "duration_days": "int (optional, 1-3650 days)",
  "payment_method": "string (optional, max 50 chars)",
  "transaction_id": "string (optional, max 100 chars)"
}
```

**Success Response** (200):
```json
{
  "success": true,
  "message": "会员升级成功，当前等级：黄金会员",
  "membership": { ... }
}
```

---

#### 21. Renew Membership

Renew current membership.

**Endpoint**: `POST /api/membership/renew`

**Authentication**: Required

**Request Body**:
```json
{
  "duration_days": "int (required, 1-3650 days)",
  "payment_method": "string (optional)",
  "transaction_id": "string (optional)"
}
```

---

#### 22. Get Storage Stats

Get user storage statistics.

**Endpoint**: `GET /api/membership/storage-stats`

**Authentication**: Required

**Success Response** (200):
```json
{
  "success": true,
  "stats": {
    "storage_used": 1048576,
    "storage_limit": 1073741824,
    "storage_used_formatted": "1.00 MB",
    "storage_limit_formatted": "1.00 GB",
    "usage_percentage": 0.1,
    "file_count": 5
  }
}
```

---

#### 23. Get Membership Benefits

Get current user's membership benefits.

**Endpoint**: `GET /api/membership/benefits`

**Authentication**: Required

**Success Response** (200):
```json
{
  "success": true,
  "level_name": "黄金会员",
  "level_code": "gold",
  "benefits": [
    {
      "benefit_id": 1,
      "benefit_type": "storage",
      "description": "10GB 存储空间"
    }
  ]
}
```

---

#### 24. Get Membership History

Get membership change history.

**Endpoint**: `GET /api/membership/history`

**Authentication**: Required

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | int | 1 | Page number |
| page_size | int | 20 | Items per page (max 100) |

---

#### 25. Cancel Auto-Renewal

Cancel membership auto-renewal.

**Endpoint**: `POST /api/membership/cancel`

**Authentication**: Required

**Success Response** (200):
```json
{
  "success": true,
  "message": "已取消自动续费",
  "membership": { ... }
}
```

---

### Admin Endpoints (`/api/admin`)

All admin endpoints require authentication and admin privileges.

#### 26. Get All Users

Get paginated list of all users.

**Endpoint**: `GET /api/admin/users`

**Authentication**: Required (Admin)

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | int | 1 | Page number |
| page_size | int | 20 | Items per page (max 100) |
| search | string | "" | Search by username/email/phone |

**Success Response** (200):
```json
{
  "success": true,
  "data": {
    "users": [ ... ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 100,
      "total_pages": 5
    }
  }
}
```

---

#### 27. Get User Detail

Get detailed information about a specific user.

**Endpoint**: `GET /api/admin/users/<user_id>`

**Authentication**: Required (Admin)

---

#### 28. Delete User

Delete a user account.

**Endpoint**: `DELETE /api/admin/users/<user_id>`

**Authentication**: Required (Admin)

**Note**: Cannot delete yourself.

**Success Response** (200):
```json
{
  "success": true,
  "message": "用户已删除"
}
```

---

#### 29. Reset User Password

Reset a user's password.

**Endpoint**: `POST /api/admin/users/<user_id>/reset-password`

**Authentication**: Required (Admin)

**Request Body**:
```json
{
  "new_password": "string (required, 6-100 chars)"
}
```

---

#### 30. Update User Membership

Update a user's membership level.

**Endpoint**: `PUT /api/admin/users/<user_id>/membership`

**Authentication**: Required (Admin)

**Request Body**:
```json
{
  "level_id": "int (required)",
  "duration_days": "int (optional, 1-3650 days)"
}
```

---

#### 31. Update User Status

Enable or disable a user account.

**Endpoint**: `PUT /api/admin/users/<user_id>/status`

**Authentication**: Required (Admin)

**Request Body**:
```json
{
  "is_active": "boolean (required)"
}
```

---

#### 32. Get User Files

Get files uploaded by a specific user.

**Endpoint**: `GET /api/admin/users/<user_id>/files`

**Authentication**: Required (Admin)

---

#### 33. Get System Statistics

Get system-wide statistics.

**Endpoint**: `GET /api/admin/stats`

**Authentication**: Required (Admin)

**Success Response** (200):
```json
{
  "success": true,
  "data": {
    "total_users": 100,
    "membership_stats": {
      "free": 80,
      "silver": 10,
      "gold": 8,
      "diamond": 2
    }
  }
}
```

---

### Monitor Endpoints (`/api/monitor`)

#### 34. Health Check

Check system health status.

**Endpoint**: `GET /api/monitor/health`

**Authentication**: Not required

**Success Response** (200):
```json
{
  "status": "healthy",
  "timestamp": "2026-02-22T12:00:00",
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "upload_directory": "healthy"
  }
}
```

---

#### 35. Get Request Statistics

Get request performance statistics.

**Endpoint**: `GET /api/monitor/stats/requests`

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| time_window | int | 3600 | Time window in seconds (max 86400) |

---

#### 36. Get Cache Statistics

Get cache performance statistics.

**Endpoint**: `GET /api/monitor/stats/cache`

---

#### 37. Get Database Statistics

Get database performance statistics.

**Endpoint**: `GET /api/monitor/stats/database`

---

#### 38. Get System Statistics

Get system resource statistics.

**Endpoint**: `GET /api/monitor/stats/system`

**Success Response** (200):
```json
{
  "success": true,
  "data": {
    "cpu_percent": 25.5,
    "memory_percent": 60.2,
    "disk_usage_percent": 45.0,
    "process_memory_mb": 150.5,
    "active_threads": 10
  }
}
```

---

#### 39. Get All Statistics

Get all statistics in one request.

**Endpoint**: `GET /api/monitor/stats/all`

---

#### 40. Get Monitor Configuration

Get monitoring configuration.

**Endpoint**: `GET /api/monitor/config`

---

#### 41. Clear Cache

Clear all caches.

**Endpoint**: `POST /api/monitor/cache/clear`

**Authentication**: Required (Admin)

**Success Response** (200):
```json
{
  "success": true,
  "message": "缓存清除成功",
  "data": {
    "application_cache_cleared": 10,
    "redis_cache_cleared": 50,
    "total_cleared": 60
  }
}
```

---

#### 42. Get System Alerts

Get system alerts and warnings.

**Endpoint**: `GET /api/monitor/alerts`

**Success Response** (200):
```json
{
  "success": true,
  "data": {
    "alerts": [
      {
        "level": "warning",
        "type": "high_cpu_usage",
        "message": "CPU使用率较高: 85%",
        "value": 85
      }
    ],
    "count": 1,
    "critical_count": 0,
    "warning_count": 1
  }
}
```

---

#### 43. Get Prometheus Metrics

Get metrics in Prometheus format.

**Endpoint**: `GET /api/monitor/metrics`

**Response**: Plain text Prometheus format

---

#### 44. Get Recent Logs

Get recent log entries.

**Endpoint**: `GET /api/monitor/logs`

**Authentication**: Required (Admin)

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| lines | int | 100 | Number of lines (max 1000) |
| level | string | "" | Filter by log level (DEBUG/INFO/WARNING/ERROR) |

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request validation failed |
| `AUTHENTICATION_ERROR` | 401 | Authentication required or failed |
| `AUTHORIZATION_ERROR` | 403 | User not authorized for this action |
| `NOT_FOUND` | 404 | Requested resource not found |
| `METHOD_NOT_ALLOWED` | 405 | HTTP method not allowed |
| `CONFLICT` | 409 | Resource already exists or conflicts |
| `REQUEST_ENTITY_TOO_LARGE` | 413 | File size exceeds limit |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_SERVER_ERROR` | 500 | Server error |
| `DATABASE_ERROR` | 500 | Database operation failed |
| `FILE_OPERATION_ERROR` | 500 | File operation failed |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |
| `STORAGE_LIMIT_EXCEEDED` | 507 | Storage limit exceeded |

---

## Rate Limiting

The API implements rate limiting to prevent abuse:
- **Window**: 10 seconds
- **Max Calls**: 1000 requests per window

If rate limit is exceeded, the server will return a `429` status code.

---

## File Upload Limitations

- **Maximum file size**: 256MB (configurable via `MAX_CONTENT_LENGTH`)
- **Allowed permissions**: `public`, `private`
- **File naming**: Automatic sanitization for security
- **Storage limit**: Based on membership level (1GB for free users)

---

## Security Features

1. **Password Hashing**: Using scrypt with salt
2. **Session Management**: Secure session-based authentication with configurable lifetime
3. **File Security**: Filename sanitization and permission-based access
4. **Rate Limiting**: Protection against malicious calls
5. **Input Validation**: Comprehensive request validation
6. **CORS Support**: Configured for cross-origin requests
7. **HTTPS**: Supported via nginx reverse proxy for domain `wftgf.top`

---

## CORS Configuration

The API supports CORS for the following origins:
- `http://localhost:5173`
- `http://127.0.0.1:5173`
- `https://wftgf.top`
- Android clients (all origins with credentials)

---

## Testing

See the `tests/` directory for comprehensive test suites.

Run tests using:
```bash
./run_tests.sh
```

---

## Support

For issues or questions, please refer to the project README.md or contact the development team.
