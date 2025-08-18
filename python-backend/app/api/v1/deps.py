from fastapi import Depends, HTTPException, status, Request
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from typing import Optional
import logging
from app.core.database import get_db
from app.core.security import oauth2_scheme, SECRET_KEY, ALGORITHM
from app.models.user import User

# Configure logging
logger = logging.getLogger(__name__)


async def get_current_user(
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


async def get_current_user_websocket(token: str, db: Session) -> Optional[User]:
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
