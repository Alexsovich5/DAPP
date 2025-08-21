from fastapi import Depends, HTTPException, status, Request, Header
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from typing import Optional
import logging
from app.core.database import get_db
from app.core.security import oauth2_scheme, SECRET_KEY, ALGORITHM, validate_csrf_token
from app.models.user import User

# Configure logging
logger = logging.getLogger(__name__)


def get_current_user(
    request: Request = None,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    """
    Validate JWT token and return the current authenticated user.
    This dependency is used to protect API endpoints.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Handle missing token
    if not token:
        logger.warning("No authorization token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get client info for logging
    client_host = request.client.host if request else "unknown"

    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            logger.warning(f"Token missing 'sub' claim from {client_host}")
            raise credentials_exception

        # Log token validation
        logger.debug(f"Validated token for {email} from {client_host}")

    except JWTError as e:
        logger.warning(f"JWT validation error from {client_host}: {str(e)}")
        raise credentials_exception

    # Get user from database
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        logger.warning(f"User not found for validated token: {email}")
        raise credentials_exception

    # Check if user is active
    if not user.is_active:
        logger.warning(f"Inactive user attempted access: {email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )

    return user


def get_current_user_websocket(token: str, db: Session) -> Optional[User]:
    """
    Validate JWT token for WebSocket connections and return the current user.
    Returns None if authentication fails (no exceptions for WebSocket).
    """
    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            logger.warning("WebSocket token missing 'sub' claim")
            return None

        # Get user from database
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            logger.warning(f"WebSocket user not found for validated token: {email}")
            return None

        # Check if user is active
        if not user.is_active:
            logger.warning(f"WebSocket inactive user attempted access: {email}")
            return None

        return user

    except JWTError as e:
        logger.warning(f"WebSocket JWT validation error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"WebSocket authentication error: {str(e)}")
        return None


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get the current active user (depends on get_current_user).
    This is a convenience dependency for endpoints that require active users.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def validate_csrf_protection(
    request: Request,
    current_user: User = Depends(get_current_user),
    x_csrf_token: Optional[str] = Header(None, alias="X-CSRF-Token")
) -> User:
    """
    Validate CSRF token for state-changing operations.
    
    This dependency should be used for POST, PUT, PATCH, DELETE operations
    that modify user data or perform sensitive actions.
    
    Args:
        request: FastAPI request object
        current_user: Authenticated user from get_current_user
        x_csrf_token: CSRF token from X-CSRF-Token header
        
    Returns:
        Authenticated user if CSRF validation passes
        
    Raises:
        HTTPException: If CSRF token is missing or invalid
    """
    # Skip CSRF validation for safe methods (GET, HEAD, OPTIONS)
    if request.method in ["GET", "HEAD", "OPTIONS"]:
        return current_user
    
    # Require CSRF token for state-changing operations
    if not x_csrf_token:
        logger.warning(f"Missing CSRF token for {request.method} {request.url.path} from user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token required for this operation",
            headers={"X-CSRF-Required": "true"}
        )
    
    # Validate CSRF token
    if not validate_csrf_token(x_csrf_token, current_user.id):
        logger.warning(f"Invalid CSRF token for {request.method} {request.url.path} from user {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token",
            headers={"X-CSRF-Required": "true"}
        )
    
    logger.debug(f"CSRF validation passed for user {current_user.id}")
    return current_user
