import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from dotenv import load_dotenv
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Security Constants
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-jwt")
if SECRET_KEY == "your-secret-key-for-jwt":
    logger.warning(
        "Using default insecure SECRET_KEY. Set a secure SECRET_KEY "
        "environment variable for production."
    )

ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
# Default to 24 hours
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# Create password context for hashing with secure rounds
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    # Use secure bcrypt rounds for production (12 is industry standard)
    bcrypt__rounds=12,
)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # Add standard JWT claims
    now = datetime.now(timezone.utc)
    to_encode.update(
        {
            "exp": expire,
            "iat": now,
            "nbf": now,
        }  # Issued at time  # Not before time
    )

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT refresh token with longer expiration."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Refresh tokens expire after 7 days by default
        expire = datetime.now(timezone.utc) + timedelta(days=7)

    # Add standard JWT claims
    now = datetime.now(timezone.utc)
    to_encode.update(
        {
            "exp": expire,
            "iat": now,  # Issued at time
            "nbf": now,  # Not before time
            "type": "refresh",  # Token type
        }
    )

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode a JWT token."""
    # Handle invalid input types
    if not isinstance(token, str) or not token:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Check if token has required claims
        if "sub" not in payload or "exp" not in payload:
            return None
        return payload
    except JWTError as e:
        logger.debug(f"Token verification failed: {e}")
        return None


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def validate_password_strength(password: str) -> bool:
    """Validate password strength for security requirements."""
    if len(password) < 8:
        return False

    # Check for common weak password patterns (as substrings)
    weak_patterns = ["password", "qwerty", "12345678", "abc123"]
    password_lower = password.lower()
    for pattern in weak_patterns:
        if pattern in password_lower:
            return False

    # Password should not be all digits or all letters
    if password.isdigit() or password.isalpha():
        return False

    # Check for repeated characters
    if len(set(password)) < 4:  # Too many repeated characters
        return False

    return True
