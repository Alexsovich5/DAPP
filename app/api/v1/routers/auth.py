from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.core.security import (
    verify_password,
    create_access_token,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.models.user import User
from app.schemas.auth import UserCreate, Token, LoginResponse, User as UserSchema
from app.api.v1.deps import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=LoginResponse)
def register(user_in: UserCreate, db: Session = Depends(get_db)) -> Any:
    """Register a new user and return login response."""
    try:
        # Check if user exists by email
        existing_user = db.query(User).filter(User.email == user_in.email).first()
        if existing_user:
            logger.warning(f"User already exists: {user_in.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

        # Check if username exists
        existing_username = (
            db.query(User).filter(User.username == user_in.username).first()
        )
        if existing_username:
            logger.warning(f"Username already exists: {user_in.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this username already exists",
            )

        # Password validation
        if len(user_in.password) < 6:
            logger.warning(f"Password too short for user: {user_in.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 6 characters long",
            )

        # Create new user with enhanced fields
        logger.info(f"Creating new user: {user_in.email}")
        hashed_password = get_password_hash(user_in.password)

        # Create user with all provided fields
        new_user = User(
            email=user_in.email,
            username=user_in.username,
            hashed_password=hashed_password,
            is_active=True,
            first_name=user_in.first_name,
            last_name=user_in.last_name,
            date_of_birth=user_in.date_of_birth,
            gender=user_in.gender,
            location=user_in.location,
            dietary_preferences=user_in.dietary_preferences or [],
            interests=user_in.cuisine_preferences or [],
            is_profile_complete=False,
        )

        # Use a single transaction
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Generate access token for immediate login
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": new_user.email}, expires_delta=access_token_expires
        )

        logger.info(f"Successfully created user: {new_user.email}")
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user=new_user
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user account: {str(e)}",
        )


@router.post("/login", response_model=LoginResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    request: Request = None,
) -> Any:
    """
    OAuth2 compatible token login.
    Get an access token and user data for future requests.
    """
    # Log login attempt (without password)
    client_host = request.client.host if request else "unknown"
    logger.info(f"Login attempt for user: {form_data.username} from {client_host}")

    # First try to find user by email
    # (since form_data.username field is used for both)
    try:
        user = db.query(User).filter(User.email == form_data.username).first()

        # If not found by email, try username
        if not user:
            user = db.query(User).filter(User.username == form_data.username).first()
    except Exception as e:
        logger.error(f"Database error during user lookup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service temporarily unavailable",
        )

    # Verify credentials
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Failed login attempt for: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        logger.warning(f"Inactive user login attempt: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    # Generate access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    logger.info(f"Successful login for user: {user.email}")
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user
    )


@router.get("/me", response_model=UserSchema)
def get_current_user_info(current_user: User = Depends(get_current_user)) -> Any:
    """Get current user information."""
    return current_user


@router.options("/login")
@router.options("/register")
async def handle_auth_options():
    """Handle OPTIONS requests for authentication endpoints"""
    return {"message": "OK"}
