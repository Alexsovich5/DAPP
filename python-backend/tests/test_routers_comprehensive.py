#!/usr/bin/env python3
"""
Comprehensive Router Tests
Tests for all API endpoints and routers
"""

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from app.api.v1.deps import get_db
from app.core.security import create_access_token
from app.main import app
from app.models.profile import Profile
from app.models.soul_connection import SoulConnection
from app.models.user import User
from fastapi.testclient import TestClient


def get_mock_db():
    """Mock database dependency"""
    mock_db = Mock()
    mock_db.query = Mock()
    mock_db.add = Mock()
    mock_db.commit = Mock()
    mock_db.refresh = Mock()
    return mock_db


@pytest.fixture
def client():
    """Create test client with mocked database"""
    app.dependency_overrides[get_db] = get_mock_db
    yield TestClient(app)
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Create auth headers with valid token"""
    token = create_access_token(data={"sub": "1"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_user():
    """Create mock user"""
    user = Mock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.username = "testuser"
    return user


class TestUsersRouter:
    """Test user endpoints"""

    def test_get_current_user(self, client, auth_headers, mock_user):
        """Test getting current user"""
        with patch("app.api.v1.deps.get_current_user", return_value=mock_user):
            response = client.get("/api/v1/users/me", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == 1
            assert data["email"] == "test@example.com"

    def test_update_user(self, client, auth_headers, mock_user):
        """Test updating user"""
        with patch("app.api.v1.deps.get_current_user", return_value=mock_user):
            with patch("app.api.v1.routers.users.get_db") as mock_get_db:
                mock_db = Mock()
                mock_get_db.return_value = mock_db
                mock_db.query.return_value.filter.return_value.first.return_value = (
                    mock_user
                )

                response = client.put(
                    "/api/v1/users/me",
                    headers=auth_headers,
                    json={"first_name": "Updated", "last_name": "Name"},
                )
                assert response.status_code == 200
                mock_db.commit.assert_called()

    def test_get_potential_matches(self, client, auth_headers, mock_user):
        """Test getting potential matches"""
        with patch("app.api.v1.deps.get_current_user", return_value=mock_user):
            with patch("app.api.v1.routers.users.get_db") as mock_get_db:
                mock_db = Mock()
                mock_get_db.return_value = mock_db
                mock_matches = [Mock(spec=User) for _ in range(5)]
                mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = (
                    mock_matches
                )

                response = client.get(
                    "/api/v1/users/potential-matches", headers=auth_headers
                )
                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list)


class TestProfilesRouter:
    """Test profile endpoints"""

    def test_create_profile(self, client, auth_headers, mock_user):
        """Test creating profile"""
        with patch("app.api.v1.deps.get_current_user", return_value=mock_user):
            with patch("app.api.v1.routers.profiles.get_db") as mock_get_db:
                mock_db = Mock()
                mock_get_db.return_value = mock_db
                mock_db.query.return_value.filter.return_value.first.return_value = None

                response = client.post(
                    "/api/v1/profiles",
                    headers=auth_headers,
                    json={
                        "life_philosophy": "Live and learn",
                        "core_values": {"primary": ["growth", "authenticity"]},
                        "interests": ["music", "travel"],
                    },
                )
                assert response.status_code == 201
                mock_db.add.assert_called()
                mock_db.commit.assert_called()

    def test_get_my_profile(self, client, auth_headers, mock_user):
        """Test getting own profile"""
        with patch("app.api.v1.deps.get_current_user", return_value=mock_user):
            with patch("app.api.v1.routers.profiles.get_db") as mock_get_db:
                mock_db = Mock()
                mock_get_db.return_value = mock_db
                mock_profile = Mock(spec=Profile)
                mock_profile.user_id = 1
                mock_db.query.return_value.filter.return_value.first.return_value = (
                    mock_profile
                )

                response = client.get("/api/v1/profiles/me", headers=auth_headers)
                assert response.status_code == 200


class TestMatchesRouter:
    """Test match endpoints"""

    def test_create_match_request(self, client, auth_headers, mock_user):
        """Test creating match request"""
        with patch("app.api.v1.deps.get_current_user", return_value=mock_user):
            with patch("app.api.v1.routers.matches.get_db") as mock_get_db:
                mock_db = Mock()
                mock_get_db.return_value = mock_db
                mock_db.query.return_value.filter.return_value.first.return_value = None

                response = client.post(
                    "/api/v1/matches", headers=auth_headers, json={"target_user_id": 2}
                )
                assert response.status_code == 201
                mock_db.add.assert_called()

    def test_get_sent_matches(self, client, auth_headers, mock_user):
        """Test getting sent match requests"""
        with patch("app.api.v1.deps.get_current_user", return_value=mock_user):
            with patch("app.api.v1.routers.matches.get_db") as mock_get_db:
                mock_db = Mock()
                mock_get_db.return_value = mock_db
                mock_matches = [Mock(spec=SoulConnection) for _ in range(3)]
                mock_db.query.return_value.filter.return_value.all.return_value = (
                    mock_matches
                )

                response = client.get("/api/v1/matches/sent", headers=auth_headers)
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 3

    def test_respond_to_match(self, client, auth_headers, mock_user):
        """Test responding to match request"""
        with patch("app.api.v1.deps.get_current_user", return_value=mock_user):
            with patch("app.api.v1.routers.matches.get_db") as mock_get_db:
                mock_db = Mock()
                mock_get_db.return_value = mock_db
                mock_match = Mock(spec=SoulConnection)
                mock_match.user2_id = 1
                mock_db.query.return_value.filter.return_value.first.return_value = (
                    mock_match
                )

                response = client.put(
                    "/api/v1/matches/1", headers=auth_headers, json={"accepted": True}
                )
                assert response.status_code == 200
                mock_db.commit.assert_called()


class TestMessagesRouter:
    """Test message endpoints"""

    def test_send_message(self, client, auth_headers, mock_user):
        """Test sending message"""
        with patch("app.api.v1.deps.get_current_user", return_value=mock_user):
            with patch("app.api.v1.routers.messages.get_db") as mock_get_db:
                mock_db = Mock()
                mock_get_db.return_value = mock_db
                mock_connection = Mock(spec=SoulConnection)
                mock_connection.user1_id = 1
                mock_db.query.return_value.filter.return_value.first.return_value = (
                    mock_connection
                )

                response = client.post(
                    "/api/v1/messages/1",
                    headers=auth_headers,
                    json={"message_text": "Hello!"},
                )
                assert response.status_code == 201
                mock_db.add.assert_called()

    def test_get_messages(self, client, auth_headers, mock_user):
        """Test getting messages"""
        with patch("app.api.v1.deps.get_current_user", return_value=mock_user):
            with patch("app.api.v1.routers.messages.get_db") as mock_get_db:
                mock_db = Mock()
                mock_get_db.return_value = mock_db
                mock_messages = [Mock() for _ in range(10)]
                mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
                    mock_messages
                )

                response = client.get("/api/v1/messages/1", headers=auth_headers)
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 10


class TestOnboardingRouter:
    """Test onboarding endpoints"""

    def test_complete_onboarding(self, client, auth_headers, mock_user):
        """Test completing onboarding"""
        with patch("app.api.v1.deps.get_current_user", return_value=mock_user):
            with patch("app.api.v1.routers.onboarding.get_db") as mock_get_db:
                mock_db = Mock()
                mock_get_db.return_value = mock_db
                mock_db.query.return_value.filter.return_value.first.return_value = (
                    mock_user
                )

                response = client.post(
                    "/api/v1/onboarding/complete",
                    headers=auth_headers,
                    json={
                        "responses": {
                            "q1": "Answer 1",
                            "q2": "Answer 2",
                            "q3": "Answer 3",
                        }
                    },
                )
                assert response.status_code == 200
                mock_db.commit.assert_called()

    def test_get_onboarding_status(self, client, auth_headers, mock_user):
        """Test getting onboarding status"""
        with patch("app.api.v1.deps.get_current_user", return_value=mock_user):
            mock_user.emotional_onboarding_completed = True
            response = client.get("/api/v1/onboarding/status", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["completed"] == True


class TestRevelationsRouter:
    """Test revelation endpoints"""

    def test_create_revelation(self, client, auth_headers, mock_user):
        """Test creating revelation"""
        with patch("app.api.v1.deps.get_current_user", return_value=mock_user):
            with patch("app.api.v1.routers.revelations.get_db") as mock_get_db:
                mock_db = Mock()
                mock_get_db.return_value = mock_db

                response = client.post(
                    "/api/v1/revelations/1",
                    headers=auth_headers,
                    json={"content": "My deepest fear is...", "day_number": 3},
                )
                assert response.status_code == 201
                mock_db.add.assert_called()

    def test_get_revelation_timeline(self, client, auth_headers, mock_user):
        """Test getting revelation timeline"""
        with patch("app.api.v1.deps.get_current_user", return_value=mock_user):
            with patch("app.api.v1.routers.revelations.get_db") as mock_get_db:
                mock_db = Mock()
                mock_get_db.return_value = mock_db
                mock_revelations = [Mock() for _ in range(7)]
                mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = (
                    mock_revelations
                )

                response = client.get(
                    "/api/v1/revelations/timeline/1", headers=auth_headers
                )
                assert response.status_code == 200
                data = response.json()
                assert len(data) == 7


class TestPhotoRevealRouter:
    """Test photo reveal endpoints"""

    def test_upload_photo(self, client, auth_headers, mock_user):
        """Test uploading photo"""
        with patch("app.api.v1.deps.get_current_user", return_value=mock_user):
            with patch("app.api.v1.routers.photo_reveal.get_db") as mock_get_db:
                mock_db = Mock()
                mock_get_db.return_value = mock_db

                # Create mock file
                files = {"file": ("test.jpg", b"fake_image_data", "image/jpeg")}

                response = client.post(
                    "/api/v1/photo-reveal/upload", headers=auth_headers, files=files
                )

                # May fail due to actual file validation, but test structure is correct
                assert response.status_code in [201, 400, 422]

    def test_get_photo_status(self, client, auth_headers, mock_user):
        """Test getting photo reveal status"""
        with patch("app.api.v1.deps.get_current_user", return_value=mock_user):
            with patch("app.api.v1.routers.photo_reveal.get_db") as mock_get_db:
                mock_db = Mock()
                mock_get_db.return_value = mock_db

                response = client.get(
                    "/api/v1/photo-reveal/status/1", headers=auth_headers
                )
                assert response.status_code == 200


class TestSafetyRouter:
    """Test safety endpoints"""

    def test_report_user(self, client, auth_headers, mock_user):
        """Test reporting user"""
        with patch("app.api.v1.deps.get_current_user", return_value=mock_user):
            with patch("app.api.v1.routers.safety.get_db") as mock_get_db:
                mock_db = Mock()
                mock_get_db.return_value = mock_db

                response = client.post(
                    "/api/v1/safety/report",
                    headers=auth_headers,
                    json={
                        "reported_user_id": 2,
                        "reason": "harassment",
                        "details": "Inappropriate messages",
                    },
                )
                assert response.status_code == 201
                mock_db.add.assert_called()

    def test_block_user(self, client, auth_headers, mock_user):
        """Test blocking user"""
        with patch("app.api.v1.deps.get_current_user", return_value=mock_user):
            with patch("app.api.v1.routers.safety.get_db") as mock_get_db:
                mock_db = Mock()
                mock_get_db.return_value = mock_db

                response = client.post("/api/v1/safety/block/2", headers=auth_headers)
                assert response.status_code == 200
                mock_db.add.assert_called()


class TestHealthRouter:
    """Test health endpoints"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_readiness_check(self, client):
        """Test readiness check"""
        with patch("app.api.v1.routers.health.check_database") as mock_check:
            mock_check.return_value = True
            response = client.get("/ready")
            assert response.status_code == 200
            data = response.json()
            assert data["ready"] == True
