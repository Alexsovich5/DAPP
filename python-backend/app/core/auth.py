from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from typing import Optional
import logging

from .security import SECRET_KEY, ALGORITHM, oauth2_scheme, decode_access_token
from .database import get_db
from ..models.user import User

logger = logging.getLogger(__name__)

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_access_token(token)
        if payload is None:
            raise credentials_exception
            
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
        
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current authenticated and active user.
    """
    # Add any additional checks for user status here if needed
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get the current authenticated admin user.
    """
    # Check if user has admin privileges
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin privileges required."
        )
    return current_user


def get_user_from_token(token: str, db: Session) -> Optional[User]:
    """
    Synchronous function to get user from token (for non-async contexts).
    """
    try:
        payload = decode_access_token(token)
        if payload is None:
            return None
            
        user_id: int = payload.get("user_id")
        if user_id is None:
            return None
            
        user = db.query(User).filter(User.id == user_id).first()
        return user
        
    except Exception as e:
        logger.error(f"Error getting user from token: {str(e)}")
        return None