#!/usr/bin/env python3
"""
Auth Router Tests
Tests for authentication endpoints including register, login, and token management
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from app.api.v1.deps import get_db
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models.user import User
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError


def get_mock_db():
    """Mock database dependency"""
    mock_db = Mock()
    mock_db.query = Mock()
    mock_db.add = Mock()
    mock_db.commit = Mock()
    mock_db.refresh = Mock()
    mock_db.rollback = Mock()
    return mock_db


@pytest.fixture
def client():
    """Create test client with mocked database"""
    app.dependency_overrides[get_db] = get_mock_db
    yield TestClient(app)
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def mock_user():
    user = Mock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.username = "testuser"
    user.first_name = "Test"
    user.last_name = "User"
    user.hashed_password = get_password_hash("password123")
    user.is_active = True
    user.is_verified = False
    user.created_at = datetime.now()
    return user


class TestAuthRouter:
    """Test authentication endpoints"""

    def test_register_success(self, client):
        """Test successful user registration"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "SecurePassword123!",
                "first_name": "New",
                "last_name": "User",
                "date_of_birth": "1990-01-01",
                "gender": "male",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data

    def test_register_duplicate_email(self, client):
        """Test registration with duplicate email"""
        with patch("app.api.v1.routers.auth_router.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            mock_db.add.side_effect = IntegrityError("", "", "")

            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "existing@example.com",
                    "username": "newuser",
                    "password": "SecurePassword123!",
                    "first_name": "New",
                    "last_name": "User",
                    "date_of_birth": "1990-01-01",
                    "gender": "male",
                },
            )

            assert response.status_code == 400
            assert "already registered" in response.json()["detail"].lower()

    def test_login_success(self, client, mock_user):
        """Test successful login"""
        with patch("app.api.v1.routers.auth_router.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = (
                mock_user
            )

            with patch("app.core.security.verify_password", return_value=True):
                response = client.post(
                    "/api/v1/auth/login",
                    data={"username": "test@example.com", "password": "password123"},
                )

                assert response.status_code == 200
                data = response.json()
                assert "access_token" in data
                assert "refresh_token" in data
                assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        with patch("app.api.v1.routers.auth_router.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = None

            response = client.post(
                "/api/v1/auth/login",
                data={"username": "wrong@example.com", "password": "wrongpassword"},
            )

            assert response.status_code == 401
            assert "incorrect" in response.json()["detail"].lower()

    def test_login_inactive_user(self, client, mock_user):
        """Test login with inactive user"""
        mock_user.is_active = False

        with patch("app.api.v1.routers.auth_router.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = (
                mock_user
            )

            with patch("app.core.security.verify_password", return_value=True):
                response = client.post(
                    "/api/v1/auth/login",
                    data={"username": "test@example.com", "password": "password123"},
                )

                assert response.status_code == 400
                assert "inactive" in response.json()["detail"].lower()

    def test_refresh_token_success(self, client):
        """Test token refresh"""
        refresh_token = create_access_token(
            data={"sub": "1"}, expires_delta=timedelta(days=7)
        )

        with patch("app.api.v1.routers.auth_router.decode_token") as mock_decode:
            mock_decode.return_value = {"sub": "1"}

            with patch("app.api.v1.routers.auth_router.get_db") as mock_get_db:
                mock_db = Mock()
                mock_get_db.return_value = mock_db
                mock_user = Mock()
                mock_user.id = 1
                mock_db.query.return_value.filter.return_value.first.return_value = (
                    mock_user
                )

                response = client.post(
                    "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
                )

                assert response.status_code == 200
                data = response.json()
                assert "access_token" in data
                assert data["token_type"] == "bearer"

    def test_refresh_token_invalid(self, client):
        """Test refresh with invalid token"""
        with patch("app.api.v1.routers.auth_router.decode_token", return_value=None):
            response = client.post(
                "/api/v1/auth/refresh", json={"refresh_token": "invalid_token"}
            )

            assert response.status_code == 401
            assert "invalid" in response.json()["detail"].lower()

    def test_get_current_user(self, client, mock_user):
        """Test getting current user info"""
        access_token = create_access_token(data={"sub": "1"})

        with patch("app.api.v1.deps.get_current_user", return_value=mock_user):
            response = client.get(
                "/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["email"] == mock_user.email
            assert data["username"] == mock_user.username
            assert data["id"] == mock_user.id

    def test_get_current_user_unauthorized(self, client):
        """Test getting current user without auth"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
        assert "not authenticated" in response.json()["detail"].lower()

    def test_logout(self, client, mock_user):
        """Test logout endpoint"""
        access_token = create_access_token(data={"sub": "1"})

        with patch("app.api.v1.deps.get_current_user", return_value=mock_user):
            response = client.post(
                "/api/v1/auth/logout",
                headers={"Authorization": f"Bearer {access_token}"},
            )

            assert response.status_code == 200
            assert response.json()["message"] == "Successfully logged out"

    def test_verify_email(self, client):
        """Test email verification"""
        with patch("app.api.v1.routers.auth_router.decode_token") as mock_decode:
            mock_decode.return_value = {"sub": "1", "purpose": "email_verification"}

            with patch("app.api.v1.routers.auth_router.get_db") as mock_get_db:
                mock_db = Mock()
                mock_get_db.return_value = mock_db
                mock_user = Mock()
                mock_user.is_verified = False
                mock_db.query.return_value.filter.return_value.first.return_value = (
                    mock_user
                )

                response = client.post(
                    "/api/v1/auth/verify-email", json={"token": "verification_token"}
                )

                assert response.status_code == 200
                assert mock_user.is_verified is True
                mock_db.commit.assert_called()

    def test_request_password_reset(self, client, mock_user):
        """Test password reset request"""
        with patch("app.api.v1.routers.auth_router.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = (
                mock_user
            )

            with patch("app.api.v1.routers.auth_router.send_reset_email") as mock_send:
                response = client.post(
                    "/api/v1/auth/forgot-password", json={"email": "test@example.com"}
                )

                assert response.status_code == 200
                assert "sent" in response.json()["message"].lower()
                mock_send.assert_called()

    def test_reset_password(self, client):
        """Test password reset"""
        with patch("app.api.v1.routers.auth_router.decode_token") as mock_decode:
            mock_decode.return_value = {"sub": "1", "purpose": "password_reset"}

            with patch("app.api.v1.routers.auth_router.get_db") as mock_get_db:
                mock_db = Mock()
                mock_get_db.return_value = mock_db
                mock_user = Mock()
                mock_db.query.return_value.filter.return_value.first.return_value = (
                    mock_user
                )

                response = client.post(
                    "/api/v1/auth/reset-password",
                    json={
                        "token": "reset_token",
                        "new_password": "NewSecurePassword123!",
                    },
                )

                assert response.status_code == 200
                assert "reset" in response.json()["message"].lower()
                mock_db.commit.assert_called()


class TestAuthValidation:
    """Test authentication validation"""

    def test_password_strength_validation(self, client):
        """Test weak password rejection"""
        with patch("app.api.v1.routers.auth_router.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db

            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "test@example.com",
                    "username": "testuser",
                    "password": "weak",
                    "first_name": "Test",
                    "last_name": "User",
                    "date_of_birth": "1990-01-01",
                    "gender": "male",
                },
            )

            assert response.status_code == 422

    def test_email_format_validation(self, client):
        """Test invalid email format"""
        with patch("app.api.v1.routers.auth_router.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db

            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "invalid-email",
                    "username": "testuser",
                    "password": "SecurePassword123!",
                    "first_name": "Test",
                    "last_name": "User",
                    "date_of_birth": "1990-01-01",
                    "gender": "male",
                },
            )

            assert response.status_code == 422

    def test_age_validation(self, client):
        """Test underage user rejection"""
        with patch("app.api.v1.routers.auth_router.get_db") as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db

            # Use a date that makes user under 18
            underage_date = (datetime.now() - timedelta(days=365 * 17)).strftime(
                "%Y-%m-%d"
            )

            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "test@example.com",
                    "username": "testuser",
                    "password": "SecurePassword123!",
                    "first_name": "Test",
                    "last_name": "User",
                    "date_of_birth": underage_date,
                    "gender": "male",
                },
            )

            assert response.status_code == 400
            assert "18" in response.json()["detail"]
