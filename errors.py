"""
Error handling utilities for Sensor_Flask application.
Provides standardized error responses with detailed information.
"""

from flask import jsonify
import traceback
import logging

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Base class for API errors."""
    def __init__(self, message, status_code=400, error_code=None, details=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details

class ValidationError(APIError):
    """Raised when input validation fails."""
    def __init__(self, message, details=None):
        super().__init__(message, 400, 'VALIDATION_ERROR', details)

class AuthenticationError(APIError):
    """Raised when authentication fails."""
    def __init__(self, message="Authentication required"):
        super().__init__(message, 401, 'AUTHENTICATION_ERROR')

class AuthorizationError(APIError):
    """Raised when authorization fails."""
    def __init__(self, message="Not authorized"):
        super().__init__(message, 403, 'AUTHORIZATION_ERROR')

class NotFoundError(APIError):
    """Raised when a resource is not found."""
    def __init__(self, message="Resource not found"):
        super().__init__(message, 404, 'NOT_FOUND')

class ConflictError(APIError):
    """Raised when there's a conflict (e.g., duplicate resource)."""
    def __init__(self, message="Resource conflict"):
        super().__init__(message, 409, 'CONFLICT')

class RateLimitError(APIError):
    """Raised when rate limit is exceeded."""
    def __init__(self, message="Rate limit exceeded"):
        super().__init__(message, 429, 'RATE_LIMIT_EXCEEDED')

class ServerError(APIError):
    """Raised for internal server errors."""
    def __init__(self, message="Internal server error"):
        super().__init__(message, 500, 'INTERNAL_SERVER_ERROR')


def create_error_response(error, include_traceback=False):
    """
    Create a standardized error response.
    
    Args:
        error: Exception or error message
        include_traceback: Whether to include traceback in development
    
    Returns:
        tuple: (response_dict, status_code) or (json_response, status_code) if in Flask context
    """
    if isinstance(error, APIError):
        status_code = error.status_code
        error_code = error.error_code
        message = error.message
        details = error.details
    else:
        status_code = 500
        error_code = 'INTERNAL_SERVER_ERROR'
        message = str(error) if str(error) else "An unexpected error occurred"
        details = None
    
    response = {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
            "status": status_code
        }
    }
    
    # Add details if available
    if details:
        response["error"]["details"] = details
    
    # Include traceback in development mode for debugging
    if include_traceback and status_code == 500:
        response["error"]["traceback"] = traceback.format_exc()
    
    # Try to use jsonify if Flask is available and in app context
    try:
        from flask import jsonify
        return jsonify(response), status_code
    except RuntimeError:
        # Outside Flask context, return dict directly
        return response, status_code


def handle_exception(error):
    """
    Global exception handler for Flask app.
    
    Args:
        error: Exception that was raised
    
    Returns:
        tuple: (json_response, status_code)
    """
    # Log the error
    logger.error(f"Unhandled exception: {error}", exc_info=True)
    
    # Handle specific error types
    if isinstance(error, APIError):
        return create_error_response(error)
    
    # Handle other common exceptions
    if isinstance(error, ValueError):
        return create_error_response(ValidationError(str(error)))
    
    # Default to internal server error
    return create_error_response(ServerError())


def register_error_handlers(app):
    """
    Register error handlers with Flask application.
    
    Args:
        app: Flask application instance
    """
    @app.errorhandler(APIError)
    def handle_api_error(error):
        return create_error_response(error)
    
    @app.errorhandler(404)
    def handle_not_found(error):
        return create_error_response(NotFoundError("Endpoint not found"))
    
    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        return create_error_response(
            APIError("Method not allowed", 405, 'METHOD_NOT_ALLOWED')
        )
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        # Log the internal error
        logger.error(f"Internal server error: {error}", exc_info=True)
        
        # In production, don't expose internal details
        if app.config.get('ENV') == 'production':
            return create_error_response(ServerError())
        else:
            return create_error_response(
                ServerError("Internal server error - check logs for details")
            )
    
    # Catch-all for unhandled exceptions
    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        return handle_exception(error)


def validate_required_fields(data, required_fields, field_descriptions=None):
    """
    Validate that required fields are present in request data.
    
    Args:
        data: Dictionary of request data
        required_fields: List of required field names
        field_descriptions: Optional dict mapping field names to descriptions
    
    Returns:
        None if validation passes
        
    Raises:
        ValidationError if any required field is missing
    """
    missing_fields = []
    
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == '':
            if field_descriptions and field in field_descriptions:
                missing_fields.append(f"{field} ({field_descriptions[field]})")
            else:
                missing_fields.append(field)
    
    if missing_fields:
        details = {
            "missing_fields": missing_fields,
            "required_fields": required_fields
        }
        raise ValidationError(
            f"Missing required fields: {', '.join(missing_fields)}",
            details=details
        )