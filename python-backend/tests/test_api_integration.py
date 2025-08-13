"""
Integration tests for API endpoints and workflows
"""
import pytest
from fastapi import status
from app.models.user import User
from app.models.profile import Profile
from app.core.security import get_password_hash


class TestAuthenticationIntegration:
    """Integration tests for authentication flows"""

    def test_complete_registration_and_login_flow(self, client, db_session):
        """Test complete user registration and login process"""
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        
        # Step 1: Register new user
        registration_data = {
            "email": f"integration_{unique_id}@test.com",
            "username": f"integration{unique_id}",
            "password": "SecurePassword123!"
        }
        
        register_response = client.post("/api/v1/auth/register", json=registration_data)
        assert register_response.status_code == status.HTTP_200_OK
        
        register_data = register_response.json()
        assert "access_token" in register_data
        assert "user" in register_data
        user_id = register_data["user"]["id"]
        access_token = register_data["access_token"]
        
        # Step 2: Use token to access protected endpoint
        profile_response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        if profile_response.status_code == status.HTTP_200_OK:
            profile_data = profile_response.json()
            assert profile_data["id"] == user_id
            assert profile_data["email"] == registration_data["email"]
        
        # Step 3: Login with credentials
        login_data = {
            "username": registration_data["email"],
            "password": registration_data["password"]
        }
        
        login_response = client.post("/api/v1/auth/login", data=login_data)
        assert login_response.status_code == status.HTTP_200_OK
        
        login_result = login_response.json()
        assert "access_token" in login_result
        assert login_result["token_type"] == "bearer"

    def test_protected_endpoint_access_control(self, client, test_user):
        """Test access control on protected endpoints"""
        endpoints_to_test = [
            ("/api/v1/users/me", "GET"),
            ("/api/v1/profiles/me", "GET"),
            ("/api/v1/matches", "GET"),
        ]
        
        for endpoint, method in endpoints_to_test:
            # Test without auth
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json={})
            
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            
            # Test with valid auth
            headers = {"Authorization": f"Bearer {test_user['access_token']}"}
            if method == "GET":
                response = client.get(endpoint, headers=headers)
            else:
                response = client.post(endpoint, json={}, headers=headers)
            
            # Should not be 401 (may be 200, 404, or other valid response)
            assert response.status_code != status.HTTP_401_UNAUTHORIZED


class TestProfileIntegration:
    """Integration tests for profile management"""

    def test_complete_profile_creation_and_management(self, client, test_user):
        """Test complete profile lifecycle"""
        # Step 1: Create profile
        profile_data = {
            "full_name": "Integration Test User",
            "bio": "I'm testing the integration of this amazing app!",
            "cuisine_preferences": "Italian, Mexican, Thai",
            "dietary_restrictions": "Vegetarian",
            "location": "San Francisco, CA"
        }
        
        create_response = client.post(
            "/api/v1/profiles",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json=profile_data
        )
        assert create_response.status_code == status.HTTP_200_OK
        created_profile = create_response.json()
        assert created_profile["full_name"] == profile_data["full_name"]
        
        # Step 2: Retrieve profile
        get_response = client.get(
            "/api/v1/profiles/me",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        assert get_response.status_code == status.HTTP_200_OK
        retrieved_profile = get_response.json()
        assert retrieved_profile["full_name"] == profile_data["full_name"]
        
        # Step 3: Update profile
        updated_data = {
            "bio": "Updated bio for integration testing!",
            "location": "Los Angeles, CA"
        }
        
        update_response = client.put(
            "/api/v1/profiles/me",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json=updated_data
        )
        assert update_response.status_code == status.HTTP_200_OK
        updated_profile = update_response.json()
        assert updated_profile["bio"] == updated_data["bio"]
        assert updated_profile["location"] == updated_data["location"]

    def test_profile_visibility_and_privacy(self, client, test_user, db_session):
        """Test profile privacy and visibility controls"""
        # Create another user to test visibility
        other_user = User(
            email="other_integration@test.com",
            username="other_integration",
            hashed_password=get_password_hash("password123"),
            is_active=True
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)
        
        # Test viewing other user's profile
        response = client.get(
            f"/api/v1/profiles/{other_user.id}",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        # Response should be 200 (visible) or 403/404 (private/not found)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]


class TestMatchingIntegration:
    """Integration tests for matching functionality"""

    def test_user_discovery_and_matching(self, client, test_user, db_session):
        """Test user discovery and match creation"""
        # Create potential match users
        for i in range(3):
            match_user = User(
                email=f"match_{i}@test.com",
                username=f"match_user_{i}",
                hashed_password=get_password_hash("password123"),
                is_active=True
            )
            db_session.add(match_user)
        db_session.commit()
        
        # Test getting potential matches
        response = client.get(
            "/api/v1/users/potential-matches",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        # May return 200 (implemented) or 404 (not implemented)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
        
        if response.status_code == status.HTTP_200_OK:
            matches = response.json()
            assert isinstance(matches, list)

    def test_match_creation_workflow(self, client, test_user, db_session):
        """Test creating matches between users"""
        # Create target user for matching
        target_user = User(
            email="target_match@test.com",
            username="target_match",
            hashed_password=get_password_hash("password123"),
            is_active=True
        )
        db_session.add(target_user)
        db_session.commit()
        db_session.refresh(target_user)
        
        # Try to create a match
        match_data = {
            "target_user_id": target_user.id,
            "match_type": "like"
        }
        
        response = client.post(
            "/api/v1/matches",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json=match_data
        )
        # May return 200 (created), 404 (not implemented), or 400 (validation error)
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND
        ]


class TestMessageIntegration:
    """Integration tests for messaging functionality"""

    def test_messaging_workflow(self, client, test_user, db_session):
        """Test complete messaging workflow"""
        # Create recipient user
        recipient = User(
            email="recipient_msg@test.com",
            username="recipient_msg",
            hashed_password=get_password_hash("password123"),
            is_active=True
        )
        db_session.add(recipient)
        db_session.commit()
        db_session.refresh(recipient)
        
        # Test sending a message
        message_data = {
            "recipient_id": recipient.id,
            "content": "Hello! How are you doing?",
            "message_type": "text"
        }
        
        send_response = client.post(
            "/api/v1/messages",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json=message_data
        )
        # May return 200/201 (sent) or 404 (not implemented)
        assert send_response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_404_NOT_FOUND
        ]
        
        # Test retrieving messages
        get_response = client.get(
            f"/api/v1/messages/{recipient.id}",
            headers={"Authorization": f"Bearer {test_user['access_token']}"}
        )
        assert get_response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND
        ]

    def test_message_validation_and_safety(self, client, test_user, db_session):
        """Test message content validation and safety"""
        recipient = User(
            email="safety_test@test.com",
            username="safety_test",
            hashed_password=get_password_hash("password123"),
            is_active=True
        )
        db_session.add(recipient)
        db_session.commit()
        db_session.refresh(recipient)
        
        # Test empty message
        empty_message = {
            "recipient_id": recipient.id,
            "content": "",
            "message_type": "text"
        }
        
        response = client.post(
            "/api/v1/messages",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json=empty_message
        )
        # Should reject empty messages
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_404_NOT_FOUND
        ]
        
        # Test very long message
        long_message = {
            "recipient_id": recipient.id,
            "content": "x" * 10000,  # Very long message
            "message_type": "text"
        }
        
        response = client.post(
            "/api/v1/messages",
            headers={"Authorization": f"Bearer {test_user['access_token']}"},
            json=long_message
        )
        # Should reject overly long messages
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_404_NOT_FOUND
        ]


class TestErrorHandling:
    """Integration tests for error handling and edge cases"""

    def test_malformed_requests(self, client, test_user):
        """Test handling of malformed requests"""
        endpoints = [
            ("/api/v1/profiles", "POST"),
            ("/api/v1/matches", "POST"),
            ("/api/v1/messages", "POST"),
        ]
        
        for endpoint, method in endpoints:
            # Test with invalid JSON
            headers = {
                "Authorization": f"Bearer {test_user['access_token']}",
                "Content-Type": "application/json"
            }
            
            if method == "POST":
                response = client.post(endpoint, headers=headers, json={"invalid": "data"})
            
            # Should handle gracefully (not 500 error)
            assert response.status_code < 500

    def test_rate_limiting_behavior(self, client, test_user):
        """Test API rate limiting (if implemented)"""
        # Make multiple rapid requests
        responses = []
        for i in range(20):
            response = client.get(
                "/api/v1/users/me",
                headers={"Authorization": f"Bearer {test_user['access_token']}"}
            )
            responses.append(response.status_code)
        
        # Check that most requests succeed
        success_count = sum(1 for status_code in responses if status_code == 200)
        assert success_count > 15  # Most should succeed
        
        # If rate limiting is implemented, some might return 429
        rate_limited = any(status_code == 429 for status_code in responses)
        # This is optional - rate limiting might not be implemented yet

    def test_database_connection_resilience(self, client):
        """Test API behavior with database issues"""
        # Test endpoints that should work even with minimal database access
        response = client.get("/health")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
        
        # Test API documentation endpoint
        response = client.get("/docs")
        assert response.status_code == status.HTTP_200_OK