"""
Comprehensive Error Handling - Sprint 4
Enhanced error handling for real-time features and production monitoring
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any, Dict, Optional, Union

from app.core.logging_config import get_logger, log_error
from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DataError, IntegrityError, SQLAlchemyError
from websockets.exceptions import ConnectionClosedError, WebSocketException


class ErrorCategory(str, Enum):
    """Categories of errors for better organization and handling"""

    # Database errors
    DATABASE_CONNECTION = "database_connection"
    DATABASE_INTEGRITY = "database_integrity"
    DATABASE_QUERY = "database_query"

    # Authentication/Authorization
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    TOKEN_VALIDATION = "token_validation"

    # WebSocket errors
    WEBSOCKET_CONNECTION = "websocket_connection"
    WEBSOCKET_MESSAGE = "websocket_message"
    WEBSOCKET_BROADCAST = "websocket_broadcast"

    # Activity tracking errors
    ACTIVITY_LOGGING = "activity_logging"
    ACTIVITY_SESSION = "activity_session"
    ACTIVITY_VALIDATION = "activity_validation"

    # Real-time integration
    REALTIME_INTEGRATION = "realtime_integration"
    PRESENCE_UPDATE = "presence_update"
    CHANNEL_MANAGEMENT = "channel_management"

    # API validation
    REQUEST_VALIDATION = "request_validation"
    RESPONSE_VALIDATION = "response_validation"
    PARAMETER_VALIDATION = "parameter_validation"

    # External services
    EXTERNAL_SERVICE = "external_service"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"

    # System errors
    SYSTEM = "system"
    CONFIGURATION = "configuration"
    RESOURCE_EXHAUSTION = "resource_exhaustion"

    # Business logic
    BUSINESS_LOGIC = "business_logic"
    COMPATIBILITY_CALCULATION = "compatibility_calculation"
    REVELATION_PROCESSING = "revelation_processing"


class DinnerAppException(Exception):
    """Base exception for Dinner App with enhanced error tracking"""

    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        retry_after: Optional[int] = None,
        error_code: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.details = details or {}
        self.user_message = user_message or "An unexpected error occurred"
        self.retry_after = retry_after
        self.error_code = error_code or f"{category.value}_error"
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/API responses"""
        return {
            "error_code": self.error_code,
            "category": self.category.value,
            "message": self.message,
            "user_message": self.user_message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "retry_after": self.retry_after,
        }


class DatabaseError(DinnerAppException):
    """Database-related errors"""

    def __init__(
        self,
        message: str,
        original_error: Optional[Exception] = None,
        **kwargs,
    ):
        super().__init__(
            message,
            category=ErrorCategory.DATABASE_CONNECTION,
            user_message="Database temporarily unavailable. Please try again later.",
            **kwargs,
        )
        self.original_error = original_error


class WebSocketError(DinnerAppException):
    """WebSocket-related errors"""

    def __init__(self, message: str, connection_id: Optional[str] = None, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.WEBSOCKET_CONNECTION,
            user_message="Connection issue occurred. Please refresh and try again.",
            **kwargs,
        )
        if connection_id:
            self.details["connection_id"] = connection_id


class ActivityTrackingError(DinnerAppException):
    """Activity tracking-related errors"""

    def __init__(self, message: str, activity_type: Optional[str] = None, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.ACTIVITY_LOGGING,
            user_message="Activity tracking temporarily unavailable.",
            **kwargs,
        )
        if activity_type:
            self.details["activity_type"] = activity_type


class ValidationError(DinnerAppException):
    """Request validation errors"""

    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.REQUEST_VALIDATION,
            user_message="Invalid request data provided.",
            **kwargs,
        )
        if field:
            self.details["invalid_field"] = field


class AuthenticationError(DinnerAppException):
    """Authentication-related errors"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.AUTHENTICATION,
            user_message="Authentication required. Please log in again.",
            **kwargs,
        )


class RealtimeIntegrationError(DinnerAppException):
    """Real-time integration errors"""

    def __init__(self, message: str, integration_type: Optional[str] = None, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.REALTIME_INTEGRATION,
            user_message="Real-time features temporarily unavailable.",
            **kwargs,
        )
        if integration_type:
            self.details["integration_type"] = integration_type


def handle_database_error(
    error: Exception, context: Optional[Dict] = None
) -> DatabaseError:
    """Convert SQLAlchemy errors to our custom DatabaseError"""

    context = context or {}

    if isinstance(error, IntegrityError):
        return DatabaseError(
            f"Data integrity constraint violated: {str(error)}",
            original_error=error,
            category=ErrorCategory.DATABASE_INTEGRITY,
            user_message="Data conflict occurred. Please check your input.",
            details=context,
            error_code="integrity_constraint_violation",
        )

    elif isinstance(error, DataError):
        return DatabaseError(
            f"Invalid data format: {str(error)}",
            original_error=error,
            category=ErrorCategory.DATABASE_QUERY,
            user_message="Invalid data format provided.",
            details=context,
            error_code="invalid_data_format",
        )

    else:
        return DatabaseError(
            f"Database operation failed: {str(error)}",
            original_error=error,
            details=context,
        )


def handle_websocket_error(
    error: Exception, context: Optional[Dict] = None
) -> WebSocketError:
    """Convert WebSocket errors to our custom WebSocketError"""

    context = context or {}

    if isinstance(error, ConnectionClosedError):
        return WebSocketError(
            f"WebSocket connection closed: {error.code} - {error.reason}",
            category=ErrorCategory.WEBSOCKET_CONNECTION,
            user_message="Connection lost. Attempting to reconnect...",
            details={
                **context,
                "close_code": error.code,
                "close_reason": error.reason,
            },
            error_code="websocket_connection_closed",
            retry_after=5,
        )

    elif isinstance(error, WebSocketException):
        return WebSocketError(
            f"WebSocket error: {str(error)}",
            details=context,
            error_code="websocket_communication_error",
        )

    else:
        return WebSocketError(
            f"WebSocket operation failed: {str(error)}", details=context
        )


async def safe_execute(
    operation_name: str,
    coro_or_func,
    *args,
    logger: Optional[logging.Logger] = None,
    context: Optional[Dict] = None,
    fallback_value: Any = None,
    max_retries: int = 0,
    retry_delay: float = 1.0,
    **kwargs,
) -> Any:
    """
    Safely execute an operation with comprehensive error handling

    Args:
        operation_name: Name of the operation for logging
        coro_or_func: Coroutine or function to execute
        *args: Arguments for the function
        logger: Logger instance
        context: Additional context for logging
        fallback_value: Value to return on failure
        max_retries: Maximum number of retries
        retry_delay: Delay between retries in seconds
        **kwargs: Keyword arguments for the function

    Returns:
        Operation result or fallback_value
    """

    if logger is None:
        logger = get_logger("app.core.error_handlers")

    context = context or {}

    for attempt in range(max_retries + 1):
        try:
            start_time = datetime.utcnow()

            # Execute operation
            if asyncio.iscoroutinefunction(coro_or_func):
                result = await coro_or_func(*args, **kwargs)
            else:
                result = coro_or_func(*args, **kwargs)

            # Log successful execution
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.debug(
                f"Operation '{operation_name}' completed successfully",
                extra={
                    **context,
                    "operation": operation_name,
                    "duration_ms": duration,
                    "attempt": attempt + 1,
                },
            )

            return result

        except Exception as error:
            # Determine if we should retry
            should_retry = attempt < max_retries and not isinstance(
                error, (ValidationError, AuthenticationError)
            )

            # Log error
            log_error(
                logger,
                error,
                context={
                    **context,
                    "operation": operation_name,
                    "attempt": attempt + 1,
                    "max_retries": max_retries,
                    "will_retry": should_retry,
                },
                error_type=f"{operation_name}_error",
            )

            if should_retry:
                logger.info(
                    f"Retrying operation '{operation_name}' in {retry_delay}s (attempt {attempt + 2}/{max_retries + 1})",
                    extra={
                        **context,
                        "operation": operation_name,
                        "retry_delay": retry_delay,
                    },
                )
                await asyncio.sleep(retry_delay)
                continue
            else:
                # No more retries or non-retryable error
                logger.error(
                    f"Operation '{operation_name}' failed permanently after {attempt + 1} attempts",
                    extra={
                        **context,
                        "operation": operation_name,
                        "attempts": attempt + 1,
                    },
                )
                return fallback_value


def error_handler_decorator(
    operation_name: str,
    category: ErrorCategory = ErrorCategory.SYSTEM,
    user_message: Optional[str] = None,
    fallback_value: Any = None,
    log_level: int = logging.ERROR,
):
    """
    Decorator for comprehensive error handling

    Args:
        operation_name: Name of the operation
        category: Error category
        user_message: User-friendly error message
        fallback_value: Value to return on error
        log_level: Logging level for errors
    """

    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(f"app.{func.__module__}")

            try:
                start_time = datetime.utcnow()
                result = await func(*args, **kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000

                logger.debug(
                    f"{operation_name} completed successfully in {duration:.2f}ms",
                    extra={
                        "operation": operation_name,
                        "duration_ms": duration,
                        "function": func.__name__,
                    },
                )
                return result

            except Exception as error:
                # Convert to our custom exception if needed
                if isinstance(error, DinnerAppException):
                    custom_error = error
                elif isinstance(error, SQLAlchemyError):
                    custom_error = handle_database_error(error)
                elif isinstance(error, WebSocketException):
                    custom_error = handle_websocket_error(error)
                else:
                    custom_error = DinnerAppException(
                        f"{operation_name} failed: {str(error)}",
                        category=category,
                        user_message=user_message
                        or f"{operation_name} temporarily unavailable",
                    )

                # Log the error
                logger.log(
                    log_level,
                    f"{operation_name} failed: {custom_error.message}",
                    exc_info=True,
                    extra={
                        "operation": operation_name,
                        "error_category": custom_error.category.value,
                        "error_code": custom_error.error_code,
                        "function": func.__name__,
                    },
                )

                return fallback_value

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_logger(f"app.{func.__module__}")

            try:
                start_time = datetime.utcnow()
                result = func(*args, **kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds() * 1000

                logger.debug(
                    f"{operation_name} completed successfully in {duration:.2f}ms",
                    extra={
                        "operation": operation_name,
                        "duration_ms": duration,
                        "function": func.__name__,
                    },
                )
                return result

            except Exception as error:
                # Convert to our custom exception if needed
                if isinstance(error, DinnerAppException):
                    custom_error = error
                elif isinstance(error, SQLAlchemyError):
                    custom_error = handle_database_error(error)
                elif isinstance(error, WebSocketException):
                    custom_error = handle_websocket_error(error)
                else:
                    custom_error = DinnerAppException(
                        f"{operation_name} failed: {str(error)}",
                        category=category,
                        user_message=user_message
                        or f"{operation_name} temporarily unavailable",
                    )

                # Log the error
                logger.log(
                    log_level,
                    f"{operation_name} failed: {custom_error.message}",
                    exc_info=True,
                    extra={
                        "operation": operation_name,
                        "error_category": custom_error.category.value,
                        "error_code": custom_error.error_code,
                        "function": func.__name__,
                    },
                )

                return fallback_value

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


async def create_error_response(
    error: Union[Exception, DinnerAppException],
    request_id: Optional[str] = None,
) -> JSONResponse:
    """
    Create a standardized error response for API endpoints

    Args:
        error: Exception to convert
        request_id: Request ID for tracing

    Returns:
        JSONResponse with error details
    """

    if isinstance(error, DinnerAppException):
        custom_error = error
    elif isinstance(error, ValidationError):
        custom_error = ValidationError(str(error))
    elif isinstance(error, SQLAlchemyError):
        custom_error = handle_database_error(error)
    else:
        custom_error = DinnerAppException(
            str(error),
            user_message="An unexpected error occurred. Please try again.",
        )

    # Determine HTTP status code
    status_code_map = {
        ErrorCategory.AUTHENTICATION: status.HTTP_401_UNAUTHORIZED,
        ErrorCategory.AUTHORIZATION: status.HTTP_403_FORBIDDEN,
        ErrorCategory.REQUEST_VALIDATION: status.HTTP_400_BAD_REQUEST,
        ErrorCategory.DATABASE_INTEGRITY: status.HTTP_409_CONFLICT,
        ErrorCategory.RATE_LIMIT: status.HTTP_429_TOO_MANY_REQUESTS,
        ErrorCategory.EXTERNAL_SERVICE: status.HTTP_503_SERVICE_UNAVAILABLE,
        ErrorCategory.TIMEOUT: status.HTTP_504_GATEWAY_TIMEOUT,
    }

    http_status = status_code_map.get(
        custom_error.category, status.HTTP_500_INTERNAL_SERVER_ERROR
    )

    response_data = {
        "success": False,
        "error": {
            "code": custom_error.error_code,
            "message": custom_error.user_message,
            "category": custom_error.category.value,
            "timestamp": custom_error.timestamp.isoformat(),
        },
    }

    if request_id:
        response_data["request_id"] = request_id

    if custom_error.retry_after:
        response_data["retry_after"] = custom_error.retry_after

    # Add debug info in development
    import os

    if os.getenv("ENVIRONMENT", "development") == "development":
        response_data["debug"] = {
            "technical_message": custom_error.message,
            "details": custom_error.details,
        }

    return JSONResponse(
        status_code=http_status,
        content=response_data,
        headers=(
            {"Retry-After": str(custom_error.retry_after)}
            if custom_error.retry_after
            else None
        ),
    )
