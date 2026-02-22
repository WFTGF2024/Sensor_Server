"""
Error handling utilities for Sensor_Flask application.
Provides standardized error responses with detailed information.
"""

from flask import jsonify, current_app
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


class RequestEntityTooLargeError(APIError):
    """Raised when request entity is too large."""
    def __init__(self, message="File size exceeds the maximum allowed limit"):
        super().__init__(message, 413, 'REQUEST_ENTITY_TOO_LARGE')


class RateLimitError(APIError):
    """Raised when rate limit is exceeded."""
    def __init__(self, message="Rate limit exceeded"):
        super().__init__(message, 429, 'RATE_LIMIT_EXCEEDED')


class ServerError(APIError):
    """Raised for internal server errors."""
    def __init__(self, message="Internal server error", details=None):
        super().__init__(message, 500, 'INTERNAL_SERVER_ERROR', details)


class ServiceUnavailableError(APIError):
    """Raised when a service is temporarily unavailable."""
    def __init__(self, message="Service temporarily unavailable"):
        super().__init__(message, 503, 'SERVICE_UNAVAILABLE')


class DatabaseError(APIError):
    """Raised when a database operation fails."""
    def __init__(self, message="Database operation failed", details=None):
        super().__init__(message, 500, 'DATABASE_ERROR', details)


class FileOperationError(APIError):
    """Raised when a file operation fails."""
    def __init__(self, message="File operation failed", details=None):
        super().__init__(message, 500, 'FILE_OPERATION_ERROR', details)


class StorageLimitExceededError(APIError):
    """Raised when storage limit is exceeded."""
    def __init__(self, message="Storage limit exceeded", details=None):
        super().__init__(message, 507, 'STORAGE_LIMIT_EXCEEDED', details)


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
    
    # Handle werkzeug HTTP exceptions
    try:
        from werkzeug.exceptions import HTTPException
        if isinstance(error, HTTPException):
            error_map = {
                400: ValidationError,
                401: AuthenticationError,
                403: AuthorizationError,
                404: NotFoundError,
                405: ValidationError,
                409: ConflictError,
                413: RequestEntityTooLargeError,
                429: RateLimitError,
                500: ServerError,
                503: ServiceUnavailableError,
            }
            error_class = error_map.get(error.code, APIError)
            return create_error_response(error_class(error.description or str(error)))
    except ImportError:
        pass
    
    # Handle other common exceptions
    if isinstance(error, ValueError):
        return create_error_response(ValidationError(str(error)))
    
    if isinstance(error, KeyError):
        return create_error_response(ValidationError(f"Missing required field: {str(error)}"))
    
    if isinstance(error, TypeError):
        return create_error_response(ValidationError(f"Invalid type: {str(error)}"))
    
    if isinstance(error, PermissionError):
        return create_error_response(AuthorizationError("Permission denied"))
    
    if isinstance(error, FileNotFoundError):
        return create_error_response(NotFoundError("File not found"))
    
    if isinstance(error, OSError):
        return create_error_response(FileOperationError(f"File system error: {str(error)}"))
    
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
        """Handle all custom API errors."""
        app.logger.error(f"API Error [{error.error_code}]: {error.message}")
        return create_error_response(error)
    
    @app.errorhandler(400)
    def handle_bad_request(error):
        """Handle bad request errors."""
        app.logger.warning(f"Bad request: {error}")
        return create_error_response(ValidationError(str(error.description) if hasattr(error, 'description') else "Bad request"))
    
    @app.errorhandler(401)
    def handle_unauthorized(error):
        """Handle unauthorized errors."""
        app.logger.warning(f"Unauthorized: {error}")
        return create_error_response(AuthenticationError("Authentication required"))
    
    @app.errorhandler(403)
    def handle_forbidden(error):
        """Handle forbidden errors."""
        app.logger.warning(f"Forbidden: {error}")
        return create_error_response(AuthorizationError("Access denied"))
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle not found errors."""
        return create_error_response(NotFoundError("Endpoint not found"))
    
    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """Handle method not allowed errors."""
        return create_error_response(
            APIError("Method not allowed", 405, 'METHOD_NOT_ALLOWED')
        )
    
    @app.errorhandler(408)
    def handle_request_timeout(error):
        """Handle request timeout errors."""
        app.logger.warning(f"Request timeout: {error}")
        return create_error_response(
            APIError("Request timeout", 408, 'REQUEST_TIMEOUT')
        )
    
    @app.errorhandler(409)
    def handle_conflict(error):
        """Handle conflict errors."""
        app.logger.warning(f"Conflict: {error}")
        return create_error_response(ConflictError(str(error.description) if hasattr(error, 'description') else "Resource conflict"))
    
    @app.errorhandler(413)
    def handle_request_entity_too_large(error):
        """Handle request entity too large errors."""
        app.logger.warning(f"Request entity too large: {error}")
        max_size = app.config.get('MAX_CONTENT_LENGTH', 0)
        max_size_mb = max_size / (1024 * 1024) if max_size else 0
        return create_error_response(
            RequestEntityTooLargeError(f"File size exceeds the maximum allowed limit ({max_size_mb:.1f}MB)")
        )
    
    @app.errorhandler(415)
    def handle_unsupported_media_type(error):
        """Handle unsupported media type errors."""
        app.logger.warning(f"Unsupported media type: {error}")
        return create_error_response(
            ValidationError("Unsupported media type")
        )
    
    @app.errorhandler(422)
    def handle_unprocessable_entity(error):
        """Handle unprocessable entity errors."""
        app.logger.warning(f"Unprocessable entity: {error}")
        return create_error_response(ValidationError(str(error.description) if hasattr(error, 'description') else "Validation failed"))
    
    @app.errorhandler(429)
    def handle_rate_limit_exceeded(error):
        """Handle rate limit exceeded errors."""
        app.logger.warning(f"Rate limit exceeded: {error}")
        return create_error_response(RateLimitError("Too many requests, please try again later"))
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle internal server errors."""
        # Log the internal error
        app.logger.error(f"Internal server error: {error}", exc_info=True)
        
        # In production, don't expose internal details
        if app.config.get('ENV') == 'production':
            return create_error_response(ServerError())
        else:
            return create_error_response(
                ServerError("Internal server error - check logs for details")
            )
    
    @app.errorhandler(502)
    def handle_bad_gateway(error):
        """Handle bad gateway errors."""
        app.logger.error(f"Bad gateway: {error}")
        return create_error_response(ServiceUnavailableError("Service temporarily unavailable"))
    
    @app.errorhandler(503)
    def handle_service_unavailable(error):
        """Handle service unavailable errors."""
        app.logger.error(f"Service unavailable: {error}")
        return create_error_response(ServiceUnavailableError())
    
    @app.errorhandler(504)
    def handle_gateway_timeout(error):
        """Handle gateway timeout errors."""
        app.logger.error(f"Gateway timeout: {error}")
        return create_error_response(ServiceUnavailableError("Request timeout, please try again"))
    
    # Catch-all for unhandled exceptions
    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        """Handle all unhandled exceptions."""
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
    if data is None:
        raise ValidationError("Request body is required", details={"required_fields": required_fields})
    
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


def validate_file_type(filename, allowed_extensions=None):
    """
    Validate file extension.
    
    Args:
        filename: Name of the file
        allowed_extensions: Set of allowed extensions (e.g., {'zip', 'txt'})
    
    Returns:
        True if valid
        
    Raises:
        ValidationError if file type is not allowed
    """
    if not filename:
        raise ValidationError("Filename is required")
    
    if allowed_extensions is None:
        return True
    
    if '.' not in filename:
        raise ValidationError("File must have an extension")
    
    ext = filename.rsplit('.', 1)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(
            f"File type '.{ext}' is not allowed. Allowed types: {', '.join(allowed_extensions)}",
            details={"allowed_extensions": list(allowed_extensions)}
        )
    
    return True


def safe_int(value, field_name="value", default=None, min_val=None, max_val=None):
    """
    Safely convert a value to integer with validation.
    
    Args:
        value: Value to convert
        field_name: Name of the field for error messages
        default: Default value if conversion fails
        min_val: Minimum allowed value
        max_val: Maximum allowed value
    
    Returns:
        Integer value or default
    
    Raises:
        ValidationError if value cannot be converted and no default provided
    """
    if value is None:
        if default is not None:
            return default
        raise ValidationError(f"{field_name} is required")
    
    try:
        result = int(value)
    except (ValueError, TypeError):
        if default is not None:
            return default
        raise ValidationError(f"{field_name} must be a valid integer")
    
    if min_val is not None and result < min_val:
        raise ValidationError(f"{field_name} must be at least {min_val}")
    
    if max_val is not None and result > max_val:
        raise ValidationError(f"{field_name} must be at most {max_val}")
    
    return result


def safe_str(value, field_name="value", default=None, min_len=None, max_len=None, strip=True):
    """
    Safely handle string value with validation.
    
    Args:
        value: Value to process
        field_name: Name of the field for error messages
        default: Default value if value is empty
        min_len: Minimum length
        max_len: Maximum length
        strip: Whether to strip whitespace
    
    Returns:
        String value or default
    
    Raises:
        ValidationError if validation fails
    """
    if value is None:
        if default is not None:
            return default
        raise ValidationError(f"{field_name} is required")
    
    result = str(value)
    if strip:
        result = result.strip()
    
    if not result and default is not None:
        return default
    
    if not result:
        raise ValidationError(f"{field_name} cannot be empty")
    
    if min_len is not None and len(result) < min_len:
        raise ValidationError(f"{field_name} must be at least {min_len} characters")
    
    if max_len is not None and len(result) > max_len:
        raise ValidationError(f"{field_name} must be at most {max_len} characters")
    
    return result
