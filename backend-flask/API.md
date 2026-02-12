# Sensor_Flask API Documentation

## Overview

This document provides comprehensive API documentation for the Sensor_Flask backend service. The API follows RESTful conventions and uses JSON for request and response bodies.

**Base URL**: `http://localhost:5000`

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
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Server error |

## API Endpoints

### Authentication Endpoints

#### 1. Register User

Register a new user account.

**Endpoint**: `POST /auth/register`

**Request Body**:
```json
{
  "username": "string (required, min 3 chars)",
  "password": "string (required, min 6 chars)",
  "email": "string (optional, valid email)",
  "phone": "string (optional)",
  "qq": "string (optional)",
  "wechat": "string (optional)"
}
```

**Success Response** (201):
```json
{
  "success": true,
  "message": "User registered successfully",
  "user_id": 1,
  "username": "testuser"
}
```

**Error Responses**:
- `400 VALIDATION_ERROR`: Missing required fields or weak password
- `409 CONFLICT`: Username, email, or phone already taken

**Example Request**:
```bash
curl -X POST http://localhost:5000/auth/register \
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

**Endpoint**: `POST /auth/login`

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
  "message": "Login successful",
  "user": {
    "user_id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "phone": "1234567890",
    "qq": "123456",
    "wechat": "testwechat",
    "point": 0
  }
}
```

**Error Responses**:
- `400 VALIDATION_ERROR`: Missing required fields
- `401 AUTHENTICATION_ERROR`: Invalid username or password

**Example Request**:
```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "securepass123"
  }' \
  -c cookies.txt
```

---

#### 3. Logout

Clear user session.

**Endpoint**: `POST /auth/logout`

**Authentication**: Required

**Success Response** (200):
```json
{
  "success": true,
  "message": "Logout successful"
}
```

**Error Responses**:
- `401 AUTHENTICATION_ERROR`: No active session

**Example Request**:
```bash
curl -X POST http://localhost:5000/auth/logout \
  -b cookies.txt
```

---

#### 4. Get User Profile

Get current user's profile information.

**Endpoint**: `GET /auth/user`

**Authentication**: Required

**Success Response** (200):
```json
{
  "success": true,
  "user": {
    "user_id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "phone": "1234567890",
    "qq": "123456",
    "wechat": "testwechat",
    "point": 100
  }
}
```

**Error Responses**:
- `401 AUTHENTICATION_ERROR`: Authentication required
- `404 NOT_FOUND`: User not found

**Example Request**:
```bash
curl -X GET http://localhost:5000/auth/user \
  -b cookies.txt
```

---

#### 5. Update Profile

Update user profile information.

**Endpoint**: `PUT /auth/profile`

**Authentication**: Required

**Request Body**:
```json
{
  "email": "string (optional)",
  "phone": "string (optional)",
  "qq": "string (optional)",
  "wechat": "string (optional)"
}
```

**Success Response** (200):
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "user": {
    "user_id": 1,
    "username": "testuser",
    "email": "newemail@example.com",
    "phone": "9876543210",
    "qq": "654321",
    "wechat": "newwechat",
    "point": 100
  }
}
```

**Error Responses**:
- `400 VALIDATION_ERROR`: No fields provided or invalid data
- `401 AUTHENTICATION_ERROR`: Authentication required
- `409 CONFLICT`: Email or phone already taken by another user

**Example Request**:
```bash
curl -X PUT http://localhost:5000/auth/profile \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newemail@example.com",
    "phone": "9876543210"
  }' \
  -b cookies.txt
```

---

#### 6. Change Password

Change user password.

**Endpoint**: `PUT /auth/password`

**Authentication**: Required

**Request Body**:
```json
{
  "current_password": "string (required)",
  "new_password": "string (required, min 6 chars)"
}
```

**Success Response** (200):
```json
{
  "success": true,
  "message": "Password changed successfully"
}
```

**Error Responses**:
- `400 VALIDATION_ERROR`: Missing fields or weak new password
- `401 AUTHENTICATION_ERROR`: Authentication required
- `403 AUTHORIZATION_ERROR`: Current password incorrect

**Example Request**:
```bash
curl -X PUT http://localhost:5000/auth/password \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "oldpass123",
    "new_password": "newpass456"
  }' \
  -b cookies.txt
```

---

#### 7. Delete Account

Delete user account.

**Endpoint**: `DELETE /auth/account`

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
  "message": "Account deleted successfully"
}
```

**Error Responses**:
- `400 VALIDATION_ERROR`: Missing password
- `401 AUTHENTICATION_ERROR`: Authentication required
- `403 AUTHORIZATION_ERROR`: Incorrect password

**Example Request**:
```bash
curl -X DELETE http://localhost:5000/auth/account \
  -H "Content-Type: application/json" \
  -d '{
    "password": "mypassword123"
  }' \
  -b cookies.txt
```

---

### File Management Endpoints

#### 8. Upload File

Upload a file to the server.

**Endpoint**: `POST /download/upload`

**Authentication**: Required

**Request**: Multipart form data with file

**Success Response** (201):
```json
{
  "success": true,
  "message": "File uploaded successfully",
  "file": {
    "file_id": 1,
    "file_name": "example.txt",
    "file_size": 1024,
    "file_hash": "a1b2c3d4...",
    "upload_time": "2025-01-01T12:00:00"
  }
}
```

**Error Responses**:
- `401 AUTHENTICATION_ERROR`: Authentication required
- `400 VALIDATION_ERROR`: No file provided or invalid file

**Example Request**:
```bash
curl -X POST http://localhost:5000/download/upload \
  -F "file=@/path/to/file.txt" \
  -b cookies.txt
```

---

#### 9. List Files

Get list of user's files.

**Endpoint**: `GET /download/files`

**Authentication**: Required

**Query Parameters**:
- `permission` (optional): Filter by permission (`public` or `private`)

**Success Response** (200):
```json
{
  "success": true,
  "files": [
    {
      "file_id": 1,
      "file_name": "example.txt",
      "file_size": 1024,
      "file_permission": "private",
      "upload_time": "2025-01-01T12:00:00"
    }
  ]
}
```

**Error Responses**:
- `401 AUTHENTICATION_ERROR`: Authentication required

**Example Request**:
```bash
curl -X GET http://localhost:5000/download/files \
  -b cookies.txt
```

---

#### 10. Download File

Download a file by ID.

**Endpoint**: `GET /download/file/<file_id>`

**Authentication**: Required (for private files)

**Success Response**: File content

**Error Responses**:
- `401 AUTHENTICATION_ERROR`: Authentication required for private file
- `403 AUTHORIZATION_ERROR`: Not authorized to access this file
- `404 NOT_FOUND`: File not found

**Example Request**:
```bash
curl -X GET http://localhost:5000/download/file/1 \
  -b cookies.txt \
  -o downloaded_file.txt
```

---

#### 11. Update File

Update file information.

**Endpoint**: `POST /download/file/<file_id>`

**Authentication**: Required

**Request Body**:
```json
{
  "file_name": "string (optional)",
  "file_permission": "public|private (optional)"
}
```

**Success Response** (200):
```json
{
  "success": true,
  "message": "Update successful"
}
```

**Error Responses**:
- `400 VALIDATION_ERROR`: Invalid permission or no fields to update
- `401 AUTHENTICATION_ERROR`: Authentication required
- `404 NOT_FOUND`: File not found

**Example Request**:
```bash
curl -X POST http://localhost:5000/download/file/1 \
  -H "Content-Type: application/json" \
  -d '{
    "file_name": "newname.txt",
    "file_permission": "public"
  }' \
  -b cookies.txt
```

---

#### 12. Delete File

Delete a file.

**Endpoint**: `DELETE /download/file/<file_id>`

**Authentication**: Required

**Success Response** (200):
```json
{
  "success": true,
  "message": "Delete successful"
}
```

**Error Responses**:
- `401 AUTHENTICATION_ERROR`: Authentication required
- `404 NOT_FOUND`: File not found

**Example Request**:
```bash
curl -X DELETE http://localhost:5000/download/file/1 \
  -b cookies.txt
```

---

### System Endpoints

#### 13. List All Users

Get list of all users (admin endpoint).

**Endpoint**: `GET /users`

**Authentication**: Required

**Success Response** (200):
```json
[
  {
    "user_id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "phone": "1234567890",
    "point": 100,
    "qq": "123456",
    "wechat": "testwechat"
  }
]
```

**Example Request**:
```bash
curl -X GET http://localhost:5000/users \
  -b cookies.txt
```

---

## Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Request validation failed |
| `AUTHENTICATION_ERROR` | Authentication required or failed |
| `AUTHORIZATION_ERROR` | User not authorized for this action |
| `NOT_FOUND` | Requested resource not found |
| `CONFLICT` | Resource already exists or conflicts with existing data |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `INTERNAL_SERVER_ERROR` | Server error |
| `METHOD_NOT_ALLOWED` | HTTP method not allowed for this endpoint |

## Rate Limiting

The API implements rate limiting to prevent abuse:
- **Window**: 10 seconds
- **Max Calls**: 1000 requests per window

If rate limit is exceeded, the server will return a `429` status code.

## File Upload Limitations

- **Maximum file size**: 16MB (configurable)
- **Allowed permissions**: `public`, `private`
- **File naming**: Automatic sanitization for security

## Security Features

1. **Password Hashing**: Using PBKDF2-SHA256 with salt
2. **Session Management**: Secure session-based authentication
3. **File Security**: Filename sanitization and permission-based access
4. **Rate Limiting**: Protection against malicious calls
5. **Input Validation**: Comprehensive request validation

## Testing

See the `tests/` directory for comprehensive test suites:
- Unit tests for core functionality
- Integration tests for API endpoints

Run tests using:
```bash
./run_tests.sh
```

## Support

For issues or questions, please refer to the project README.md or contact the development team.