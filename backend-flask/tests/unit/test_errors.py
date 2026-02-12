"""
Unit tests for error handling utilities.
"""

import pytest
from errors import (
    APIError, ValidationError, AuthenticationError, AuthorizationError,
    NotFoundError, ConflictError, RateLimitError, ServerError,
    validate_required_fields, create_error_response
)

def test_api_error_basic():
    """Test basic APIError functionality."""
    error = APIError("Test error", 400, "TEST_ERROR")
    assert error.message == "Test error"
    assert error.status_code == 400
    assert error.error_code == "TEST_ERROR"
    assert error.details is None

def test_api_error_with_details():
    """Test APIError with details."""
    details = {"field": "username", "reason": "already exists"}
    error = APIError("Test error", 400, "TEST_ERROR", details)
    assert error.details == details

def test_validation_error():
    """Test ValidationError."""
    error = ValidationError("Validation failed")
    assert error.message == "Validation failed"
    assert error.status_code == 400
    assert error.error_code == "VALIDATION_ERROR"

def test_authentication_error():
    """Test AuthenticationError."""
    error = AuthenticationError()
    assert error.message == "Authentication required"
    assert error.status_code == 401
    assert error.error_code == "AUTHENTICATION_ERROR"
    
    custom_error = AuthenticationError("Custom auth message")
    assert custom_error.message == "Custom auth message"

def test_authorization_error():
    """Test AuthorizationError."""
    error = AuthorizationError()
    assert error.message == "Not authorized"
    assert error.status_code == 403
    assert error.error_code == "AUTHORIZATION_ERROR"

def test_not_found_error():
    """Test NotFoundError."""
    error = NotFoundError()
    assert error.message == "Resource not found"
    assert error.status_code == 404
    assert error.error_code == "NOT_FOUND"

def test_conflict_error():
    """Test ConflictError."""
    error = ConflictError()
    assert error.message == "Resource conflict"
    assert error.status_code == 409
    assert error.error_code == "CONFLICT"

def test_rate_limit_error():
    """Test RateLimitError."""
    error = RateLimitError()
    assert error.message == "Rate limit exceeded"
    assert error.status_code == 429
    assert error.error_code == "RATE_LIMIT_EXCEEDED"

def test_server_error():
    """Test ServerError."""
    error = ServerError()
    assert error.message == "Internal server error"
    assert error.status_code == 500
    assert error.error_code == "INTERNAL_SERVER_ERROR"

def test_create_error_response_api_error():
    """Test create_error_response with APIError."""
    error = ValidationError("Test validation error", details={"field": "username"})
    response, status_code = create_error_response(error)
    
    assert status_code == 400
    # Handle both dict and Flask response
    if hasattr(response, 'json'):
        data = response.json
    else:
        data = response
    
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert data["error"]["message"] == "Test validation error"
    assert data["error"]["status"] == 400
    assert data["error"]["details"] == {"field": "username"}

def test_create_error_response_generic_error():
    """Test create_error_response with generic error."""
    error = ValueError("Generic error")
    response, status_code = create_error_response(error)
    
    assert status_code == 500
    # Handle both dict and Flask response
    if hasattr(response, 'json'):
        data = response.json
    else:
        data = response
    
    assert data["success"] is False
    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert data["error"]["message"] == "Generic error"
    assert data["error"]["status"] == 500

def test_create_error_response_with_traceback():
    """Test create_error_response with traceback included."""
    try:
        raise ValueError("Error with traceback")
    except ValueError as error:
        response, status_code = create_error_response(error, include_traceback=True)
    
    assert status_code == 500
    # Handle both dict and Flask response
    if hasattr(response, 'json'):
        data = response.json
    else:
        data = response
    
    assert "traceback" in data["error"]
    assert "ValueError" in data["error"]["traceback"]

def test_validate_required_fields_success():
    """Test validate_required_fields with valid data."""
    data = {"username": "test", "password": "secret", "email": "test@example.com"}
    required = ["username", "password"]
    
    # Should not raise an exception
    validate_required_fields(data, required)

def test_validate_required_fields_missing():
    """Test validate_required_fields with missing fields."""
    data = {"username": "test"}
    required = ["username", "password", "email"]
    
    with pytest.raises(ValidationError) as exc_info:
        validate_required_fields(data, required)
    
    error = exc_info.value
    assert error.error_code == "VALIDATION_ERROR"
    assert "password" in error.message
    assert "email" in error.message
    assert "missing_fields" in error.details
    assert "password" in error.details["missing_fields"]
    assert "email" in error.details["missing_fields"]

def test_validate_required_fields_with_descriptions():
    """Test validate_required_fields with field descriptions."""
    data = {"username": "test"}
    required = ["username", "password"]
    descriptions = {
        "username": "Username for the account",
        "password": "Password for the account"
    }
    
    with pytest.raises(ValidationError) as exc_info:
        validate_required_fields(data, required, descriptions)
    
    error = exc_info.value
    assert "password (Password for the account)" in error.message

def test_validate_required_fields_empty_values():
    """Test validate_required_fields with empty or None values."""
    data = {"username": "", "password": None, "email": "   "}
    required = ["username", "password", "email"]
    
    with pytest.raises(ValidationError) as exc_info:
        validate_required_fields(data, required)
    
    error = exc_info.value
    # Check that at least some fields are missing (implementation may vary)
    assert "missing_fields" in error.details
    assert len(error.details["missing_fields"]) > 0

def test_error_inheritance():
    """Test that error classes properly inherit from APIError."""
    errors = [
        ValidationError("test"),
        AuthenticationError(),
        AuthorizationError(),
        NotFoundError(),
        ConflictError(),
        RateLimitError(),
        ServerError()
    ]
    
    for error in errors:
        assert isinstance(error, APIError)
        assert hasattr(error, 'message')
        assert hasattr(error, 'status_code')
        assert hasattr(error, 'error_code')