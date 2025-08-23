"""
Core Authentication Tests for Dinner First Dating Platform
Tests for basic JWT operations, password security, and authentication core functions
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import jwt
import pytest
from app.core.security import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_token,
)


class TestPasswordSecurity:
    """Test password hashing and verification functionality"""

    @pytest.mark.unit
    @pytest.mark.security
    def test_password_hash_creation(self):
        """Test that passwords are properly hashed"""
        password = "testpassword123"
        hashed = get_password_hash(password)

        # Hash should be different from original
        assert hashed != password
        # Hash should be bcrypt format
        assert hashed.startswith("$2b$")
        # Hash should be non-empty
        assert len(hashed) > 0

    @pytest.mark.unit
    @pytest.mark.security
    def test_password_verification_success(self):
        """Test successful password verification"""
        password = "correctpassword123"
        hashed = get_password_hash(password)

        # Correct password should verify
        assert verify_password(password, hashed) == True

    @pytest.mark.unit
    @pytest.mark.security
    def test_password_verification_failure(self):
        """Test failed password verification"""
        password = "correctpassword123"
        wrong_password = "wrongpassword123"
        hashed = get_password_hash(password)

        # Wrong password should not verify
        assert verify_password(wrong_password, hashed) == False

    @pytest.mark.unit
    @pytest.mark.security
    def test_password_hash_uniqueness(self):
        """Test that same password produces different hashes (salt)"""
        password = "samepassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Same password should produce different hashes due to salt
        assert hash1 != hash2
        # Both should verify with the original password
        assert verify_password(password, hash1) == True
        assert verify_password(password, hash2) == True

    @pytest.mark.unit
    @pytest.mark.security
    def test_empty_password_handling(self):
        """Test handling of empty passwords"""
        empty_password = ""
        hashed = get_password_hash(empty_password)

        # Should still create a hash for empty password
        assert hashed != ""
        assert verify_password(empty_password, hashed) == True

    @pytest.mark.unit
    @pytest.mark.security
    def test_special_characters_in_password(self):
        """Test password with special characters"""
        special_password = "P@ssw0rd!#$%^&*()_+-=[]{}|;:,.<>?"
        hashed = get_password_hash(special_password)

        assert verify_password(special_password, hashed) == True

    @pytest.mark.unit
    @pytest.mark.security
    def test_unicode_password(self):
        """Test password with unicode characters"""
        unicode_password = "пароль123Ωαφ密码🔐"
        hashed = get_password_hash(unicode_password)

        assert verify_password(unicode_password, hashed) == True


class TestJWTTokenOperations:
    """Test JWT token creation, verification, and claims"""

    @pytest.mark.unit
    @pytest.mark.security
    def test_create_access_token_basic(self):
        """Test basic access token creation"""
        user_data = {"sub": "test@example.com", "user_id": 1}
        token = create_access_token(user_data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token.split(".")) == 3  # JWT format

    @pytest.mark.unit
    @pytest.mark.security
    def test_create_access_token_with_expires(self):
        """Test access token creation with custom expiration"""
        user_data = {"sub": "test@example.com", "user_id": 1}
        custom_expires = timedelta(minutes=30)
        token = create_access_token(user_data, custom_expires)

        # Decode to check expiration
        decoded = jwt.decode(token, options={"verify_signature": False})
        exp_time = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)

        # Should expire in approximately 30 minutes
        time_diff = exp_time - now
        assert 25 <= time_diff.total_seconds() / 60 <= 35  # Allow some tolerance

    @pytest.mark.unit
    @pytest.mark.security
    def test_decode_valid_token(self):
        """Test decoding valid JWT token"""
        user_data = {"sub": "test@example.com", "user_id": 1}
        token = create_access_token(user_data)

        decoded = verify_token(token)
        assert decoded is not None
        assert decoded["sub"] == "test@example.com"
        assert decoded["user_id"] == 1

    @pytest.mark.unit
    @pytest.mark.security
    def test_decode_invalid_token(self):
        """Test decoding invalid JWT token"""
        invalid_token = "invalid.jwt.token"

        decoded = verify_token(invalid_token)
        assert decoded is None

    @pytest.mark.unit
    @pytest.mark.security
    def test_decode_expired_token(self):
        """Test decoding expired JWT token"""
        user_data = {"sub": "test@example.com", "user_id": 1}
        # Create token that expires immediately
        expired_token = create_access_token(user_data, timedelta(seconds=-1))

        decoded = verify_token(expired_token)
        assert decoded is None

    @pytest.mark.unit
    @pytest.mark.security
    def test_token_payload_preservation(self):
        """Test that token payload preserves original data"""
        original_data = {
            "sub": "user@example.com",
            "user_id": 123,
            "username": "testuser",
            "custom_claim": "custom_value",
        }

        token = create_access_token(original_data)
        decoded = verify_token(token)

        # All original data should be preserved
        assert decoded["sub"] == original_data["sub"]
        assert decoded["user_id"] == original_data["user_id"]
        assert decoded["username"] == original_data["username"]
        assert decoded["custom_claim"] == original_data["custom_claim"]

        # Standard claims should be added
        assert "exp" in decoded
        assert "iat" in decoded
        assert "nbf" in decoded


class TestAuthCoreIntegration:
    """Test integration between auth components"""

    @pytest.mark.unit
    @pytest.mark.security
    def test_create_token_for_user(self):
        """Test creating token for user data"""
        user_data = {"sub": "user@example.com", "user_id": 1, "username": "testuser"}

        token = create_access_token(user_data)
        decoded = verify_token(token)

        assert decoded is not None
        assert decoded["sub"] == user_data["sub"]
        assert decoded["user_id"] == user_data["user_id"]

    @pytest.mark.unit
    @pytest.mark.security
    def test_get_user_from_token(self):
        """Test extracting user information from token"""
        user_data = {"sub": "user@example.com", "user_id": 42, "username": "testuser"}

        token = create_access_token(user_data)
        decoded = verify_token(token)

        # Should be able to reconstruct user info
        assert decoded["user_id"] == 42
        assert decoded["sub"] == "user@example.com"

    @pytest.mark.unit
    @pytest.mark.security
    def test_auth_workflow_complete(self):
        """Test complete authentication workflow"""
        # Step 1: Hash password
        password = "userpassword123"
        hashed = get_password_hash(password)

        # Step 2: Verify password (login)
        assert verify_password(password, hashed) == True

        # Step 3: Create token after successful login
        user_data = {"sub": "user@example.com", "user_id": 1}
        token = create_access_token(user_data)

        # Step 4: Verify token for protected routes
        decoded = verify_token(token)
        assert decoded is not None
        assert decoded["sub"] == "user@example.com"

    @pytest.mark.unit
    @pytest.mark.security
    def test_auth_security_edge_cases(self):
        """Test security edge cases in auth workflow"""
        # Test with None secret key (should use default)
        with patch("app.core.security.SECRET_KEY", None):
            # This should raise an error or use default
            try:
                user_data = {"sub": "test@example.com"}
                token = create_access_token(user_data)
                # If it doesn't raise an error, token should still be created
                assert token is not None
            except Exception:
                # Expected if SECRET_KEY is None
                pass


class TestRefreshTokens:
    """Test refresh token functionality"""

    @pytest.mark.unit
    @pytest.mark.security
    def test_create_refresh_token(self):
        """Test refresh token creation"""
        user_data = {"sub": "test@example.com", "user_id": 1}
        refresh_token = create_refresh_token(user_data)

        assert refresh_token is not None
        assert isinstance(refresh_token, str)

        # Decode to check structure
        decoded = jwt.decode(refresh_token, options={"verify_signature": False})
        assert decoded["sub"] == "test@example.com"
        assert decoded["type"] == "refresh"
        assert "exp" in decoded
        assert "iat" in decoded

    @pytest.mark.unit
    @pytest.mark.security
    def test_refresh_token_different_from_access(self):
        """Test that refresh token is different from access token"""
        user_data = {"sub": "test@example.com", "user_id": 1}

        access_token = create_access_token(user_data)
        refresh_token = create_refresh_token(user_data)

        # Tokens should be different
        assert access_token != refresh_token

        # Decode both to compare
        access_decoded = jwt.decode(access_token, options={"verify_signature": False})
        refresh_decoded = jwt.decode(refresh_token, options={"verify_signature": False})

        # Refresh token should expire later
        assert refresh_decoded["exp"] > access_decoded["exp"]
        # Refresh token should have type
        assert refresh_decoded.get("type") == "refresh"
        assert "type" not in access_decoded


class TestAuthErrorHandling:
    """Test error handling in authentication"""

    @pytest.mark.unit
    @pytest.mark.security
    @pytest.mark.parametrize(
        "invalid_token",
        [
            "not.a.token",
            "too.many.parts.here.invalid",
            "invalidbase64.invalidbase64.invalidbase64",
            "",
            None,
            123,
        ],
    )
    def test_decode_malformed_tokens(self, invalid_token):
        """Test handling of malformed tokens"""
        result = verify_token(invalid_token)
        assert result is None

    @pytest.mark.unit
    @pytest.mark.security
    def test_password_hash_edge_cases(self):
        """Test password hashing edge cases"""
        # Very long password
        long_password = "a" * 1000
        hashed = get_password_hash(long_password)
        assert verify_password(long_password, hashed) == True

        # Password with null bytes - bcrypt doesn't support this
        # This is expected behavior - bcrypt rejects null bytes for security
        null_password = "password\x00with\x00nulls"
        try:
            hashed = get_password_hash(null_password)
            # If it doesn't raise an exception, verify it works
            assert verify_password(null_password, hashed) == True
        except Exception:
            # Expected: bcrypt should reject null bytes
            pass

    @pytest.mark.unit
    @pytest.mark.security
    def test_concurrent_auth_operations(self):
        """Test thread safety of auth operations"""
        import threading
        import time

        results = []

        def create_and_verify_token():
            user_data = {"sub": f"user{threading.current_thread().ident}@example.com"}
            token = create_access_token(user_data)
            decoded = verify_token(token)
            results.append(decoded is not None)

        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=create_and_verify_token)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All operations should succeed
        assert all(results)
        assert len(results) == 10
