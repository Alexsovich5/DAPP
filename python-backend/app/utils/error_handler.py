from fastapi import HTTPException, status
from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


class APIError(HTTPException):
    def __init__(
        self,
        status_code: int,
        detail: Any = None,
        headers: Optional[dict] = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            detail=detail,
            headers=headers,
        )


class NotFoundError(APIError):
    def __init__(self, detail: str = "Resource not found") -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class UnauthorizedError(APIError):
    def __init__(self, detail: str = "Not authenticated") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class ForbiddenError(APIError):
    def __init__(self, detail: str = "Permission denied") -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class CustomValidationError(APIError):
    def __init__(self, detail: str = "Validation error") -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail
        )


class BadRequestError(APIError):
    def __init__(self, detail: str = "Bad request") -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


async def validation_error_handler(request: Request, exc: ValidationError):
    """
    Custom exception handler for Pydantic validation errors
    Provides detailed information about validation failures
    """
    logger.error(f"Validation error: {exc.errors()}")

    # Simplified error response format that Angular can easily parse
    error_details = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        error_details.append(
            {"field": field_path, "message": error["msg"], "type": error["type"]}
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": error_details,
            "message": "Validation failed",
            "type": "validation_error",
        },
        headers={
            # Ensure CORS headers on error responses
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Accept, Authorization, Content-Type",
        },
    )
