from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework import status
import uuid
import logging


logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """Custom exception handler for DRF that formats all errors consistently."""
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # If this is an unexpected error, log it and create a generic response
    if response is None:
        logger.exception(f"Unexpected error: {str(exc)}")
        
        response_data = {
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "request_id": str(uuid.uuid4())
            }
        }
        
        return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # For expected exceptions, format the response
    request = context.get("request")
    request_id = str(uuid.uuid4())

    # Log the error with request details
    logger.error(
        f"API Error: {exc.__class__.__name__} - {str(exc)} - "
        f"URL: {request.path} - Method: {request.method} - "
        f"User: {request.user} - Request ID: {request_id}"
    )

    # Format the response
    error_data = {
        "error": {
            "code": getattr(exc, "default_code", exc.__class__.__name__).upper(),
            "message": str(exc),
            "request_id": request_id
        }
    }

    # Add validation errors if they exist
    if hasattr(exc, "detail") and isinstance(exc.detail, dict):
        error_data["error"]["details"] = [
            {"field": field, "message": str(error[0]) if isinstance(error, list) else str(error)}
            for field, error in exc.detail.items()
        ]

    response.data = error_data
    return response


# # api/exceptions.py
# from rest_framework.exceptions import APIException
# from rest_framework import status

# class ValidationError(APIException):
#     status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
#     default_detail = "Invalid input data"
#     default_code = "validation_error"

# class ResourceNotFoundError(APIException):
#     status_code = status.HTTP_404_NOT_FOUND
#     default_detail = "The requested resource was not found"
#     default_code = "resource_not_found"

# class DuplicateResourceError(APIException):
#     status_code = status.HTTP_409_CONFLICT
#     default_detail = "Resource already exists"
#     default_code = "duplicate_resource"

# class AuthorizationError(APIException):
#     status_code = status.HTTP_403_FORBIDDEN
#     default_detail = "Not authorized to perform this action"
#     default_code = "authorization_error"

# class RateLimitError(APIException):
#     status_code = status.HTTP_429_TOO_MANY_REQUESTS
#     default_detail = "Rate limit exceeded"
#     default_code = "rate_limit_exceeded"
