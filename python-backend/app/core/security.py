from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
import os
import logging
import secrets
import hashlib
import hmac

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
# Lower rounds for testing environment for speed
bcrypt_rounds = 4 if os.getenv("TESTING") == "1" else 12
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    # Use secure bcrypt rounds for production (12 is industry standard)
    bcrypt__rounds=bcrypt_rounds,
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
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


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


# CSRF Protection Functions

def generate_csrf_token(user_id: int, session_id: Optional[str] = None) -> str:
    """
    Generate a secure CSRF token for a user session.
    
    Args:
        user_id: The authenticated user's ID
        session_id: Optional session identifier for additional security
        
    Returns:
        A cryptographically secure CSRF token
    """
    # Use timestamp without colons to avoid parsing issues
    timestamp = str(int(datetime.now(timezone.utc).timestamp() * 1000))  # milliseconds
    session = session_id or 'default'
    
    # Generate random component
    random_bytes = secrets.token_bytes(32)
    
    # Create token with HMAC signature using | as separator
    token_data = f"{user_id}|{session}|{timestamp}|{random_bytes.hex()}"
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        token_data.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Combine data and signature
    csrf_token = f"{token_data}|{signature}"
    
    # Base64 encode for safe transmission
    import base64
    return base64.urlsafe_b64encode(csrf_token.encode('utf-8')).decode('utf-8')


def validate_csrf_token(token: str, user_id: int, session_id: Optional[str] = None, 
                       max_age_minutes: int = 60) -> bool:
    """
    Validate a CSRF token for a user session.
    
    Args:
        token: The CSRF token to validate
        user_id: The authenticated user's ID
        session_id: Optional session identifier
        max_age_minutes: Maximum age of token in minutes (default: 60)
        
    Returns:
        True if token is valid, False otherwise
    """
    try:
        # Base64 decode
        import base64
        decoded_token = base64.urlsafe_b64decode(token.encode('utf-8')).decode('utf-8')
        
        # Split token components using | separator
        parts = decoded_token.split('|')
        if len(parts) != 5:  # user_id|session_id|timestamp|random|signature
            return False
        
        token_user_id, token_session_id, timestamp_str, random_hex, provided_signature = parts
        
        # Verify user ID matches
        if int(token_user_id) != user_id:
            return False
        
        # Verify session ID matches (if provided)
        if session_id and token_session_id != session_id:
            return False
        
        # Check token age (timestamp is in milliseconds)
        try:
            token_timestamp_ms = int(timestamp_str)
            current_timestamp_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
            age_ms = current_timestamp_ms - token_timestamp_ms
            age_minutes = age_ms / (1000 * 60)  # Convert to minutes
            
            if age_minutes > max_age_minutes:
                return False
        except ValueError:
            return False
        
        # Verify HMAC signature using | separator
        token_data = f"{token_user_id}|{token_session_id}|{timestamp_str}|{random_hex}"
        expected_signature = hmac.new(
            SECRET_KEY.encode('utf-8'),
            token_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(provided_signature, expected_signature)
        
    except Exception as e:
        logger.warning(f"CSRF token validation error: {str(e)}")
        return False


def get_csrf_token_for_user(user_id: int, session_id: Optional[str] = None) -> str:
    """
    Convenience function to generate CSRF token for authenticated user.
    
    Args:
        user_id: The authenticated user's ID
        session_id: Optional session identifier
        
    Returns:
        A new CSRF token
    """
    return generate_csrf_token(user_id, session_id)
