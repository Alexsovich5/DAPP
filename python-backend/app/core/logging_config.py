"""
Comprehensive Logging Configuration - Sprint 4
Enhanced logging for real-time features and production monitoring
"""

import json
import logging
import logging.config
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""

    def __init__(self):
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "connection_id"):
            log_entry["connection_id"] = record.connection_id
        if hasattr(record, "session_id"):
            log_entry["session_id"] = record.session_id
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "activity_type"):
            log_entry["activity_type"] = record.activity_type
        if hasattr(record, "error_type"):
            log_entry["error_type"] = record.error_type
        if hasattr(record, "performance_ms"):
            log_entry["performance_ms"] = record.performance_ms

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


class ContextFilter(logging.Filter):
    """Filter to add request context to log records"""

    def filter(self, record):
        # Add default values if not present
        if not hasattr(record, "user_id"):
            record.user_id = None
        if not hasattr(record, "request_id"):
            record.request_id = None
        if not hasattr(record, "session_id"):
            record.session_id = None
        return True


def setup_logging(
    environment: str = "development",
    log_level: str = "INFO",
    enable_structured_logging: bool = False,
):
    """
    Setup comprehensive logging configuration

    Args:
        environment: development, staging, or production
        log_level: DEBUG, INFO, WARNING, ERROR, CRITICAL
        enable_structured_logging: Enable JSON structured logs
    """

    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Base configuration
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "format": "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(funcName)s() | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "simple": {"format": "%(levelname)-8s | %(name)s | %(message)s"},
            "structured": {"()": StructuredFormatter},
        },
        "filters": {"context_filter": {"()": ContextFilter}},
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": (
                    "structured" if enable_structured_logging else "detailed"
                ),
                "filters": ["context_filter"],
                "stream": sys.stdout,
            },
            "file_all": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": (
                    "structured" if enable_structured_logging else "detailed"
                ),
                "filters": ["context_filter"],
                "filename": "logs/app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
            "file_error": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": (
                    "structured" if enable_structured_logging else "detailed"
                ),
                "filters": ["context_filter"],
                "filename": "logs/error.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10,
            },
            "file_websocket": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": (
                    "structured" if enable_structured_logging else "detailed"
                ),
                "filters": ["context_filter"],
                "filename": "logs/websocket.log",
                "maxBytes": 5242880,  # 5MB
                "backupCount": 3,
            },
            "file_activity": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": (
                    "structured" if enable_structured_logging else "detailed"
                ),
                "filters": ["context_filter"],
                "filename": "logs/activity.log",
                "maxBytes": 5242880,  # 5MB
                "backupCount": 3,
            },
            "file_performance": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": (
                    "structured" if enable_structured_logging else "detailed"
                ),
                "filters": ["context_filter"],
                "filename": "logs/performance.log",
                "maxBytes": 5242880,  # 5MB
                "backupCount": 3,
            },
        },
        "loggers": {
            # Application loggers
            "app": {
                "level": "DEBUG",
                "handlers": ["console", "file_all"],
                "propagate": False,
            },
            "app.services.realtime_connection_manager": {
                "level": "DEBUG",
                "handlers": ["console", "file_websocket"],
                "propagate": False,
            },
            "app.services.activity_tracking_service": {
                "level": "DEBUG",
                "handlers": ["console", "file_activity"],
                "propagate": False,
            },
            "app.services.realtime_integration_service": {
                "level": "DEBUG",
                "handlers": ["console", "file_websocket"],
                "propagate": False,
            },
            "app.middleware.middleware": {
                "level": "INFO",
                "handlers": ["console", "file_performance"],
                "propagate": False,
            },
            "app.api": {
                "level": "INFO",
                "handlers": ["console", "file_all"],
                "propagate": False,
            },
            # Third-party loggers
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "fastapi": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "level": "WARNING",
                "handlers": ["file_all"],
                "propagate": False,
            },
            "websockets": {
                "level": "INFO",
                "handlers": ["file_websocket"],
                "propagate": False,
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console", "file_all", "file_error"],
        },
    }

    # Environment-specific adjustments
    if environment == "production":
        # More conservative logging in production
        config["handlers"]["console"]["level"] = "WARNING"
        config["loggers"]["sqlalchemy.engine"]["level"] = "ERROR"
        enable_structured_logging = True

    elif environment == "development":
        # More verbose logging in development
        config["handlers"]["console"]["level"] = "DEBUG"
        config["loggers"]["sqlalchemy.engine"]["level"] = "INFO"

    logging.config.dictConfig(config)

    # Log startup message
    logger = logging.getLogger("app.core.logging")
    logger.info(
        f"Logging configured for {environment} environment",
        extra={
            "log_level": log_level,
            "structured_logging": enable_structured_logging,
            "logs_directory": str(logs_dir.absolute()),
        },
    )


def get_logger(name: str, **context) -> logging.Logger:
    """
    Get a logger with optional context

    Args:
        name: Logger name
        **context: Additional context (user_id, connection_id, etc.)

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)

    # Create a custom adapter that adds context
    class ContextAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            # Add context to extra
            extra = kwargs.get("extra", {})
            extra.update(self.extra)
            kwargs["extra"] = extra
            return msg, kwargs

    return ContextAdapter(logger, context)


def log_error(
    logger: logging.Logger,
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    error_type: str = "unknown",
):
    """
    Log an error with comprehensive context

    Args:
        logger: Logger instance
        error: Exception to log
        context: Additional context
        error_type: Type of error for categorization
    """
    extra = {
        "error_type": error_type,
        "exception_class": error.__class__.__name__,
    }

    if context:
        extra.update(context)

    logger.error(f"{error_type}: {str(error)}", exc_info=True, extra=extra)


def log_performance(
    logger: logging.Logger,
    operation: str,
    duration_ms: float,
    context: Optional[Dict[str, Any]] = None,
):
    """
    Log performance metrics

    Args:
        logger: Logger instance
        operation: Operation name
        duration_ms: Duration in milliseconds
        context: Additional context
    """
    extra = {"performance_ms": duration_ms, "operation": operation}

    if context:
        extra.update(context)

    # Log level based on duration
    if duration_ms > 5000:  # > 5s
        level = logging.WARNING
        message = f"SLOW: {operation} took {duration_ms:.2f}ms"
    elif duration_ms > 1000:  # > 1s
        level = logging.INFO
        message = f"MEDIUM: {operation} took {duration_ms:.2f}ms"
    else:
        level = logging.DEBUG
        message = f"FAST: {operation} took {duration_ms:.2f}ms"

    logger.log(level, message, extra=extra)


# Initialize logging on import
environment = os.getenv("ENVIRONMENT", "development")
log_level = os.getenv("LOG_LEVEL", "INFO")
structured_logging = os.getenv("STRUCTURED_LOGGING", "false").lower() == "true"

setup_logging(
    environment=environment,
    log_level=log_level,
    enable_structured_logging=structured_logging,
)
