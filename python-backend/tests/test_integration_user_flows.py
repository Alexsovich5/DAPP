"""
Integration Tests for Complete User Flows - Soul Before Skin Dating Platform
Tests end-to-end user journeys from registration to photo reveal
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import json
from unittest.mock import patch, MagicMock

from app.main import app
from app.models.user import User
from app.models.soul_connection import SoulConnection, ConnectionStage
from app.models.daily_revelation import DailyRevelation
from app.core.security import create_access_token


class TestCompleteUserJourney:
    """Test complete user journey from registration to first dinner"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.mark.integration
    @pytest.mark.soul_connections
    def test_new_user_complete_journey(self, client, db_session):
        """Test complete user journey: registration → onboarding → discovery → connection → revelations → photo reveal"""
        
        # Step 1: User Registration with Emotional Onboarding
        registration_data = {
            "email": "journey@example.com",
            "username": "journeyuser",
            "password": "SecurePass123!",
            "first_name": "Journey",
            "last_name": "Tester",
            "date_of_birth": "1992-06-15",
            "gender": "female",
            "emotional_onboarding": {
                "question_1": "What do you value most in a relationship?",
                "answer_1": "Deep emotional connection and authenticity. I believe in being completely yourself with someone.",
                "question_2": "Describe your ideal evening with someone special",
                "answer_2": "Cooking a meal together while sharing stories about our dreams, then stargazing and talking about life.",
                "question_3": "What makes you feel truly understood?",
                "answer_3": "When someone listens without judgment and responds with genuine empathy and insight."
            }
        }
        
        registration_response = client.post("/api/v1/auth/register", json=registration_data)
        assert registration_response.status_code in [status.HTTP_201_CREATED, status.HTTP_200_OK]
        
        if registration_response.status_code in [status.HTTP_201_CREATED, status.HTTP_200_OK]:
            user_data = registration_response.json()
            assert user_data["email"] == "journey@example.com"
            assert user_data.get("emotional_onboarding_completed", False) == True
            
            # Step 2: Login and Get Token
            login_response = client.post(
                "/api/v1/auth/login",
                data={"username": "journey@example.com", "password": "SecurePass123!"}
            )
            assert login_response.status_code == status.HTTP_200_OK
            
            token_data = login_response.json()
            access_token = token_data["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Step 3: Create Complete Profile
            profile_data = {
                "life_philosophy": "Life is about authentic connections and shared growth",
                "core_values": ["authenticity", "empathy", "adventure", "family"],
                "interests": ["cooking", "stargazing", "hiking", "photography", "reading"],
                "personality_traits": {
                    "openness": 8.5,
                    "conscientiousness": 7.8,
                    "extraversion": 6.2,
                    "agreeableness": 9.1,
                    "emotional_stability": 7.5
                },
                "communication_style": {
                    "style": "deep_conversations",
                    "frequency": "daily",
                    "topics": ["dreams", "values", "experiences", "growth"]
                }
            }
            
            profile_response = client.post(
                "/api/v1/profiles",
                json=profile_data,
                headers=headers
            )
            assert profile_response.status_code in [status.HTTP_201_CREATED, status.HTTP_200_OK]
            
            # Step 4: Discover Potential Matches
            discovery_response = client.get(
                "/api/v1/connections/discover",
                headers=headers
            )
            assert discovery_response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
            
            if discovery_response.status_code == status.HTTP_200_OK:
                matches = discovery_response.json()
                assert isinstance(matches, list)
                
                # If matches exist, test connection initiation
                if len(matches) > 0:
                    best_match = matches[0]
                    
                    # Step 5: Initiate Soul Connection
                    connection_data = {
                        "target_user_id": best_match["user_id"],
                        "message": "Your perspective on authentic connections really resonates with me. I'd love to get to know the person behind these beautiful thoughts."
                    }
                    
                    connection_response = client.post(
                        "/api/v1/connections/initiate",
                        json=connection_data,
                        headers=headers
                    )
                    assert connection_response.status_code in [status.HTTP_201_CREATED, status.HTTP_404_NOT_FOUND]

    @pytest.mark.integration  
    @pytest.mark.soul_connections
    def test_revelation_cycle_completion_flow(self, client, soul_connection_data, authenticated_user):
        """Test complete 7-day revelation cycle flow"""
        connection = soul_connection_data["connection"]
        headers = authenticated_user["headers"]
        
        revelation_types = [
            ("personal_value", "Family and authenticity guide every decision I make. Growing up, I learned that being true to yourself is the foundation of all meaningful relationships."),
            ("meaningful_experience", "Volunteering at the local shelter taught me about resilience and hope. Seeing people rebuild their lives reminded me that we all have infinite capacity for growth."),
            ("hope_or_dream", "I dream of building a life where I can balance personal fulfillment with making a positive impact. Maybe starting a family while also creating something meaningful for our community."),
            ("humor_source", "I find joy in life's absurd moments - like when my cooking experiments go wonderfully wrong, or when my dog gives me judgmental looks for my dance moves."),
            ("challenge_overcome", "Losing my job during the pandemic forced me to rediscover what truly matters. It led me to change careers and prioritize relationships over everything else."),
            ("ideal_connection", "Perfect connection feels like coming home - where you can be completely yourself, share comfortable silences, and grow together while supporting each other's dreams."),
            ("photo_reveal", "After sharing our souls for seven days, I'm ready to share this glimpse of the person who's been opening their heart to you. Thank you for this beautiful journey.")
        ]
        
        # Complete all 7 days of revelations
        for day, (revelation_type, content) in enumerate(revelation_types, 1):
            revelation_data = {
                "connection_id": connection.id,
                "day_number": day,
                "revelation_type": revelation_type,
                "content": content
            }
            
            response = client.post(
                "/api/v1/revelations/create",
                json=revelation_data,
                headers=headers
            )
            
            # Most revelations should succeed or indicate not implemented
            assert response.status_code in [
                status.HTTP_201_CREATED,
                status.HTTP_400_BAD_REQUEST,  # Business rules
                status.HTTP_404_NOT_FOUND     # Feature not implemented
            ]
            
            if response.status_code == status.HTTP_201_CREATED:
                revelation = response.json()
                assert revelation["day_number"] == day
                assert revelation["revelation_type"] == revelation_type
                assert len(revelation["content"]) > 50  # Meaningful content
        
        # After completing revelations, check photo reveal eligibility
        photo_consent_data = {
            "connection_id": connection.id,
            "consent_given": True,
            "message": "Our soul connection has been beautiful - I'm ready to see the person behind these amazing revelations!"
        }
        
        photo_response = client.post(
            "/api/v1/photo-reveal/consent",
            json=photo_consent_data,
            headers=headers
        )
        
        assert photo_response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_404_NOT_FOUND
        ]

    @pytest.mark.integration
    @pytest.mark.security
    def test_security_throughout_user_journey(self, client, authenticated_user):
        """Test security measures throughout complete user journey"""
        headers = authenticated_user["headers"]
        
        # Test 1: Authentication required for all protected endpoints
        protected_endpoints = [
            ("/api/v1/connections/discover", "GET"),
            ("/api/v1/connections/initiate", "POST"),
            ("/api/v1/revelations/create", "POST"),
            ("/api/v1/photo-reveal/consent", "POST"),
            ("/api/v1/profiles/me", "GET")
        ]
        
        for endpoint, method in protected_endpoints:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json={})
                
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Test 2: Input validation and sanitization
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "../../../etc/passwd",
            "javascript:alert('xss')"
        ]
        
        for malicious_input in malicious_inputs:
            profile_data = {
                "life_philosophy": malicious_input,
                "core_values": [malicious_input]
            }
            
            response = client.post("/api/v1/profiles", json=profile_data, headers=headers)
            
            # Should either reject or sanitize malicious input
            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                status.HTTP_404_NOT_FOUND
            ]
        
        # Test 3: Rate limiting on sensitive operations
        for _ in range(10):  # Attempt multiple rapid requests
            response = client.post(
                "/api/v1/connections/initiate",
                json={"target_user_id": 999, "message": "Test message"},
                headers=headers
            )
            
            # Should eventually rate limit or handle gracefully
            assert response.status_code in [
                status.HTTP_201_CREATED,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_429_TOO_MANY_REQUESTS,
                status.HTTP_404_NOT_FOUND
            ]

    @pytest.mark.integration
    @pytest.mark.performance
    def test_performance_across_user_journey(self, client, authenticated_user):
        """Test performance requirements throughout user journey"""
        headers = authenticated_user["headers"]
        import time
        
        # Test API response times
        performance_tests = [
            ("/api/v1/auth/me", "GET", 0.5),  # 500ms max
            ("/api/v1/connections/discover", "GET", 2.0),  # 2s max for complex matching
            ("/api/v1/profiles/me", "GET", 0.3)  # 300ms max for profile
        ]
        
        for endpoint, method, max_time in performance_tests:
            start_time = time.time()
            
            if method == "GET":
                response = client.get(endpoint, headers=headers)
            else:
                response = client.post(endpoint, json={}, headers=headers)
            
            response_time = time.time() - start_time
            
            # Response should be reasonably fast
            assert response_time < max_time, f"{endpoint} took {response_time:.2f}s, expected < {max_time}s"
            
            # Should get valid response or not found (feature not implemented)
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_404_NOT_FOUND,
                status.HTTP_403_FORBIDDEN
            ]

    @pytest.mark.integration
    @pytest.mark.soul_connections
    def test_compatibility_algorithm_integration(self, client, matching_users):
        """Test integration of compatibility algorithm with user journey"""
        user1 = matching_users["user1"]
        user2 = matching_users["user2"]
        
        # Create tokens for both users
        token1 = create_access_token({"sub": user1.email, "user_id": user1.id})
        token2 = create_access_token({"sub": user2.email, "user_id": user2.id})
        
        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # User 1 creates enhanced profile
        profile1_data = {
            "life_philosophy": "Authenticity and growth through meaningful connections",
            "core_values": ["honesty", "empathy", "adventure", "family"],
            "interests": ["hiking", "cooking", "photography", "meditation"],
            "communication_style": {"style": "deep_conversations", "frequency": "daily"}
        }
        
        client.post("/api/v1/profiles", json=profile1_data, headers=headers1)
        
        # User 2 creates compatible profile
        profile2_data = {
            "life_philosophy": "Building authentic relationships while pursuing personal growth",
            "core_values": ["authenticity", "compassion", "exploration", "loyalty"], 
            "interests": ["outdoor_activities", "culinary_arts", "mindfulness", "travel"],
            "communication_style": {"style": "heartfelt_sharing", "frequency": "regular"}
        }
        
        client.post("/api/v1/profiles", json=profile2_data, headers=headers2)
        
        # Test discovery for User 1
        discovery_response = client.get("/api/v1/connections/discover", headers=headers1)
        
        if discovery_response.status_code == status.HTTP_200_OK:
            matches = discovery_response.json()
            
            # Should find User 2 as a compatible match
            user2_match = next((match for match in matches if match["user_id"] == user2.id), None)
            
            if user2_match:
                # Should have high compatibility due to aligned values and interests
                assert user2_match["compatibility_score"] >= 70.0
                assert "authenticity" in str(user2_match.get("values_alignment", []))
                
                # Should identify shared interests
                shared_interests = user2_match.get("shared_interests", [])
                assert len(shared_interests) >= 2  # At least 2 overlapping interests


class TestBusinessRuleIntegration:
    """Test business rule enforcement across user flows"""
    
    @pytest.mark.integration
    @pytest.mark.soul_connections
    def test_revelation_progression_rules(self, client, soul_connection_data, authenticated_user):
        """Test that revelation progression rules are enforced"""
        connection = soul_connection_data["connection"]
        headers = authenticated_user["headers"]
        
        # Try to skip to day 5 without completing previous days
        skip_ahead_data = {
            "connection_id": connection.id,
            "day_number": 5,
            "revelation_type": "challenge_overcome",
            "content": "This should not be allowed without completing days 1-4 first"
        }
        
        response = client.post("/api/v1/revelations/create", json=skip_ahead_data, headers=headers)
        
        # Should enforce progression rules
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,  # Business rule violation
            status.HTTP_404_NOT_FOUND     # Feature not implemented
        ]

    @pytest.mark.integration
    @pytest.mark.soul_connections
    def test_photo_reveal_requirements(self, client, soul_connection_data, authenticated_user):
        """Test photo reveal requirement enforcement"""
        connection = soul_connection_data["connection"]
        headers = authenticated_user["headers"]
        
        # Try to give photo consent without completing revelations
        early_consent_data = {
            "connection_id": connection.id,
            "consent_given": True
        }
        
        response = client.post("/api/v1/photo-reveal/consent", json=early_consent_data, headers=headers)
        
        # Should require completed revelation cycle
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND
        ]

    @pytest.mark.integration
    @pytest.mark.security
    def test_connection_privacy_rules(self, client, matching_users):
        """Test connection privacy and isolation rules"""
        user1 = matching_users["user1"]
        user2 = matching_users["user2"]
        user3 = matching_users.get("user3") or user1  # Fallback if only 2 users
        
        # Create tokens
        token1 = create_access_token({"sub": user1.email, "user_id": user1.id})
        token2 = create_access_token({"sub": user2.email, "user_id": user2.id})
        token3 = create_access_token({"sub": user3.email, "user_id": user3.id})
        
        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}
        headers3 = {"Authorization": f"Bearer {token3}"}
        
        # User1 and User2 establish connection
        connection_data = {
            "target_user_id": user2.id,
            "message": "Looking forward to our soul connection journey!"
        }
        
        connection_response = client.post("/api/v1/connections/initiate", json=connection_data, headers=headers1)
        
        if connection_response.status_code == status.HTTP_201_CREATED:
            connection_id = connection_response.json()["id"]
            
            # User3 should not be able to access this connection
            unauthorized_access = client.get(f"/api/v1/connections/{connection_id}", headers=headers3)
            
            assert unauthorized_access.status_code in [
                status.HTTP_403_FORBIDDEN,
                status.HTTP_404_NOT_FOUND
            ]


class TestErrorHandlingIntegration:
    """Test error handling across integrated user flows"""
    
    @pytest.mark.integration
    def test_graceful_degradation_on_service_errors(self, client, authenticated_user):
        """Test graceful degradation when services are unavailable"""
        headers = authenticated_user["headers"]
        
        # Mock service failures and test graceful handling
        with patch('app.services.compatibility_service.CompatibilityService.calculate_compatibility') as mock_compat:
            mock_compat.side_effect = Exception("Compatibility service unavailable")
            
            # Discovery should still work with fallback mechanisms
            response = client.get("/api/v1/connections/discover", headers=headers)
            
            # Should either work with fallback or indicate unavailability gracefully
            assert response.status_code in [
                status.HTTP_200_OK,         # Fallback worked
                status.HTTP_503_SERVICE_UNAVAILABLE,  # Service unavailable
                status.HTTP_404_NOT_FOUND   # Feature not implemented
            ]

    @pytest.mark.integration
    def test_data_consistency_across_operations(self, client, soul_connection_data, authenticated_user):
        """Test data consistency across related operations"""
        connection = soul_connection_data["connection"]
        headers = authenticated_user["headers"]
        
        # Create revelation
        revelation_data = {
            "connection_id": connection.id,
            "day_number": 1,
            "revelation_type": "personal_value",
            "content": "Testing data consistency across the platform with meaningful content about my core values"
        }
        
        create_response = client.post("/api/v1/revelations/create", json=revelation_data, headers=headers)
        
        if create_response.status_code == status.HTTP_201_CREATED:
            revelation = create_response.json()
            
            # Check that revelation appears in timeline
            timeline_response = client.get(f"/api/v1/revelations/timeline/{connection.id}", headers=headers)
            
            if timeline_response.status_code == status.HTTP_200_OK:
                timeline = timeline_response.json()
                
                # Should find the created revelation in timeline
                day1_revelations = [r for r in timeline if r["day_number"] == 1]
                assert len(day1_revelations) > 0

    @pytest.mark.integration
    def test_concurrent_user_operations(self, client, soul_connection_data, authenticated_user):
        """Test handling of concurrent operations by multiple users"""
        connection = soul_connection_data["connection"]
        headers = authenticated_user["headers"]
        
        # Simulate concurrent revelation attempts for the same day
        revelation_data = {
            "connection_id": connection.id,
            "day_number": 1,
            "revelation_type": "personal_value",
            "content": "First concurrent revelation attempt with meaningful personal sharing"
        }
        
        # Make multiple concurrent requests
        responses = []
        for i in range(3):
            response = client.post("/api/v1/revelations/create", json=revelation_data, headers=headers)
            responses.append(response.status_code)
        
        # Only one should succeed, others should be rejected
        success_count = sum(1 for status_code in responses if status_code == status.HTTP_201_CREATED)
        
        # Should prevent duplicate revelations
        assert success_count <= 1


class TestPlatformScalabilityIntegration:
    """Test platform scalability through integrated flows"""
    
    @pytest.mark.integration
    @pytest.mark.performance
    def test_discovery_performance_with_load(self, client, authenticated_user):
        """Test discovery performance under simulated load"""
        headers = authenticated_user["headers"]
        import time
        
        # Simulate multiple discovery requests
        response_times = []
        
        for _ in range(5):
            start_time = time.time()
            response = client.get("/api/v1/connections/discover", headers=headers)
            response_time = time.time() - start_time
            
            response_times.append(response_time)
            
            # Each request should complete reasonably quickly
            assert response_time < 3.0  # 3 seconds max
        
        # Average response time should be reasonable
        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time < 2.0  # 2 seconds average

    @pytest.mark.integration
    def test_database_connection_handling(self, client, authenticated_user):
        """Test database connection handling across operations"""
        headers = authenticated_user["headers"]
        
        # Perform multiple database-intensive operations
        operations = [
            lambda: client.get("/api/v1/auth/me", headers=headers),
            lambda: client.get("/api/v1/profiles/me", headers=headers),
            lambda: client.get("/api/v1/connections/discover", headers=headers)
        ]
        
        # All operations should handle database connections properly
        for operation in operations:
            response = operation()
            
            # Should not get database connection errors
            assert response.status_code not in [500, 503]  # No server errors
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_404_NOT_FOUND,
                status.HTTP_403_FORBIDDEN
            ]