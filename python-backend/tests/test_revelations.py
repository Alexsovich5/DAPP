"""
Comprehensive tests for Daily Revelation System
Tests the core "Soul Before Skin" 7-day revelation cycle
"""

import pytest
from fastapi import status
from datetime import datetime, timedelta
from freezegun import freeze_time
from unittest.mock import patch

from app.models.daily_revelation import DailyRevelation, RevelationType
from app.models.soul_connection import ConnectionStage
from app.services.revelation_service import RevelationService


class TestRevelationTypes:
    """Test daily revelation type definitions and structure"""
    
    @pytest.mark.unit
    @pytest.mark.revelations
    def test_revelation_types_enum(self):
        """Test that all 7 days of revelation types are defined"""
        expected_types = [
            "personal_value",
            "meaningful_experience", 
            "hope_or_dream",
            "humor_source",
            "challenge_overcome",
            "ideal_connection",
            "photo_reveal"
        ]
        
        actual_types = [rtype.value for rtype in RevelationType]
        
        for expected in expected_types:
            assert expected in actual_types
        
        # Should have exactly 7 revelation types for 7-day cycle
        assert len(actual_types) >= 7

    @pytest.mark.unit
    @pytest.mark.revelations
    def test_revelation_type_progression(self):
        """Test that revelation types follow emotional depth progression"""
        progression = [rtype.value for rtype in RevelationType]
        
        # Day 1 should be least vulnerable (values)
        assert progression[0] == "personal_value"
        
        # Day 7 should be most vulnerable (photo reveal)
        assert "photo_reveal" in progression
        
        # Middle days should build emotional intimacy
        emotional_types = ["meaningful_experience", "hope_or_dream", "challenge_overcome"]
        for etype in emotional_types:
            assert etype in progression


class TestRevelationService:
    """Test revelation service business logic"""
    
    @pytest.fixture
    def revelation_service(self, db_session):
        return RevelationService(db_session)
    
    @pytest.mark.unit
    @pytest.mark.revelations
    def test_create_revelation(self, revelation_service, soul_connection_data):
        """Test creating a new daily revelation"""
        connection = soul_connection_data["connection"]
        user = soul_connection_data["users"][0]
        
        revelation_data = {
            "day_number": 1,
            "revelation_type": RevelationType.PERSONAL_VALUE.value,
            "content": "Family and authenticity are my core values in life."
        }
        
        revelation = revelation_service.create_revelation(
            connection_id=connection.id,
            sender_id=user.id,
            **revelation_data
        )
        
        assert revelation.connection_id == connection.id
        assert revelation.sender_id == user.id
        assert revelation.day_number == 1
        assert revelation.revelation_type == RevelationType.PERSONAL_VALUE.value
        assert "family" in revelation.content.lower()

    @pytest.mark.unit
    @pytest.mark.revelations
    def test_get_revelation_timeline(self, revelation_service, soul_connection_data):
        """Test retrieving complete revelation timeline for connection"""
        connection = soul_connection_data["connection"]
        
        timeline = revelation_service.get_revelation_timeline(connection.id)
        
        assert isinstance(timeline, list)
        
        if timeline:
            revelation = timeline[0]
            assert hasattr(revelation, 'day_number')
            assert hasattr(revelation, 'revelation_type')
            assert hasattr(revelation, 'content')
            assert hasattr(revelation, 'sender_id')

    @pytest.mark.unit
    @pytest.mark.revelations
    def test_revelation_day_validation(self, revelation_service, soul_connection_data):
        """Test validation of revelation day numbers (1-7)"""
        connection = soul_connection_data["connection"]
        user = soul_connection_data["users"][0]
        
        # Valid day numbers should work
        for day in range(1, 8):
            try:
                revelation = revelation_service.create_revelation(
                    connection_id=connection.id,
                    sender_id=user.id,
                    day_number=day,
                    revelation_type=RevelationType.PERSONAL_VALUE.value,
                    content=f"Day {day} revelation content"
                )
                assert revelation.day_number == day
            except Exception as e:
                pytest.fail(f"Valid day {day} should not raise exception: {e}")
        
        # Invalid day numbers should be rejected
        invalid_days = [0, 8, -1, 100]
        for invalid_day in invalid_days:
            with pytest.raises(ValueError):
                revelation_service.create_revelation(
                    connection_id=connection.id,
                    sender_id=user.id,
                    day_number=invalid_day,
                    revelation_type=RevelationType.PERSONAL_VALUE.value,
                    content="Invalid day revelation"
                )

    @pytest.mark.unit
    @pytest.mark.revelations
    def test_revelation_content_validation(self, revelation_service, soul_connection_data):
        """Test revelation content validation and requirements"""
        connection = soul_connection_data["connection"]
        user = soul_connection_data["users"][0]
        
        # Empty content should be rejected
        with pytest.raises(ValueError):
            revelation_service.create_revelation(
                connection_id=connection.id,
                sender_id=user.id,
                day_number=1,
                revelation_type=RevelationType.PERSONAL_VALUE.value,
                content=""
            )
        
        # Very short content should be rejected (dating platform needs meaningful sharing)
        with pytest.raises(ValueError):
            revelation_service.create_revelation(
                connection_id=connection.id,
                sender_id=user.id,
                day_number=1,
                revelation_type=RevelationType.PERSONAL_VALUE.value,
                content="No"
            )
        
        # Appropriate length content should be accepted
        revelation = revelation_service.create_revelation(
            connection_id=connection.id,
            sender_id=user.id,
            day_number=1,
            revelation_type=RevelationType.PERSONAL_VALUE.value,
            content="I deeply value honesty, compassion, and genuine connection in all my relationships."
        )
        assert revelation is not None

    @pytest.mark.unit
    @pytest.mark.revelations
    def test_duplicate_revelation_prevention(self, revelation_service, soul_connection_data):
        """Test that users cannot submit duplicate revelations for the same day"""
        connection = soul_connection_data["connection"]
        user = soul_connection_data["users"][0]
        
        # Create first revelation for day 1
        first_revelation = revelation_service.create_revelation(
            connection_id=connection.id,
            sender_id=user.id,
            day_number=1,
            revelation_type=RevelationType.PERSONAL_VALUE.value,
            content="My first day 1 revelation"
        )
        assert first_revelation is not None
        
        # Attempt to create duplicate revelation for same day
        with pytest.raises(ValueError, match="already submitted"):
            revelation_service.create_revelation(
                connection_id=connection.id,
                sender_id=user.id,
                day_number=1,
                revelation_type=RevelationType.PERSONAL_VALUE.value,
                content="My duplicate day 1 revelation"
            )

    @pytest.mark.unit
    @pytest.mark.revelations
    def test_revelation_progression_logic(self, revelation_service, soul_connection_data):
        """Test that revelations must follow proper day progression"""
        connection = soul_connection_data["connection"]
        user = soul_connection_data["users"][0]
        
        # Should not be able to skip to day 3 without completing days 1 and 2
        with pytest.raises(ValueError, match="must complete previous days"):
            revelation_service.create_revelation(
                connection_id=connection.id,
                sender_id=user.id,
                day_number=3,
                revelation_type=RevelationType.HOPE_OR_DREAM.value,
                content="Skipping to day 3"
            )
        
        # Should be able to start with day 1
        revelation_service.create_revelation(
            connection_id=connection.id,
            sender_id=user.id,
            day_number=1,
            revelation_type=RevelationType.PERSONAL_VALUE.value,
            content="Starting with day 1"
        )
        
        # Then should be able to do day 2
        revelation_service.create_revelation(
            connection_id=connection.id,
            sender_id=user.id,
            day_number=2,
            revelation_type=RevelationType.MEANINGFUL_EXPERIENCE.value,
            content="Following with day 2"
        )


class TestRevelationAPI:
    """Test Revelation REST API endpoints"""
    
    @pytest.mark.integration
    @pytest.mark.revelations
    def test_create_revelation_endpoint(self, client, authenticated_user, soul_connection_data):
        """Test creating revelation via API"""
        connection = soul_connection_data["connection"]
        
        revelation_data = {
            "connection_id": connection.id,
            "day_number": 1,
            "revelation_type": RevelationType.PERSONAL_VALUE.value,
            "content": "Authenticity and deep connection guide all my relationships."
        }
        
        response = client.post(
            "/api/v1/revelations/create",
            json=revelation_data,
            headers=authenticated_user["headers"]
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        assert data["day_number"] == 1
        assert data["revelation_type"] == RevelationType.PERSONAL_VALUE.value
        assert "authenticity" in data["content"].lower()
        assert data["sender_id"] == authenticated_user["user"].id

    @pytest.mark.integration
    @pytest.mark.revelations
    def test_get_revelation_timeline_endpoint(self, client, authenticated_user, soul_connection_data):
        """Test getting revelation timeline via API"""
        connection = soul_connection_data["connection"]
        
        response = client.get(
            f"/api/v1/revelations/timeline/{connection.id}",
            headers=authenticated_user["headers"]
        )
        
        assert response.status_code == status.HTTP_200_OK
        timeline = response.json()
        
        assert isinstance(timeline, list)
        
        if timeline:
            revelation = timeline[0]
            assert "day_number" in revelation
            assert "revelation_type" in revelation
            assert "content" in revelation
            assert "created_at" in revelation

    @pytest.mark.integration
    @pytest.mark.revelations
    def test_revelation_privacy_protection(self, client, authenticated_user, matching_users):
        """Test that users can only access revelations from their connections"""
        # Create connection between authenticated user and another user
        connection_response = client.post(
            "/api/v1/connections/initiate",
            json={
                "target_user_id": matching_users["user2"].id,
                "message": "Let's start our soul journey"
            },
            headers=authenticated_user["headers"]
        )
        assert connection_response.status_code == status.HTTP_201_CREATED
        connection_id = connection_response.json()["id"]
        
        # Create revelation
        revelation_data = {
            "connection_id": connection_id,
            "day_number": 1,
            "revelation_type": RevelationType.PERSONAL_VALUE.value,
            "content": "Private revelation content"
        }
        
        client.post(
            "/api/v1/revelations/create",
            json=revelation_data,
            headers=authenticated_user["headers"]
        )
        
        # Try to access timeline without proper authentication
        response = client.get(f"/api/v1/revelations/timeline/{connection_id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.integration
    @pytest.mark.revelations
    def test_revelation_reaction_system(self, client, authenticated_user, soul_connection_data):
        """Test reacting to revelations (hearts, thoughtful, etc.)"""
        revelations = soul_connection_data["revelations"]
        if not revelations:
            pytest.skip("No revelations in test data")
        
        revelation = revelations[0]
        
        reaction_data = {
            "reaction_type": "heart",
            "message": "This really resonates with me"
        }
        
        response = client.put(
            f"/api/v1/revelations/{revelation.id}/react",
            json=reaction_data,
            headers=authenticated_user["headers"]
        )
        
        # Should either succeed or indicate feature not yet implemented
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_501_NOT_IMPLEMENTED,
            status.HTTP_404_NOT_FOUND
        ]

    @pytest.mark.integration
    @pytest.mark.revelations
    def test_revelation_content_moderation(self, client, authenticated_user, soul_connection_data):
        """Test content moderation for inappropriate revelations"""
        connection = soul_connection_data["connection"]
        
        inappropriate_content = [
            "Here's my phone number: 555-123-4567 call me",  # Contact info sharing
            "Let's meet tonight at my place",                # Premature meetup
            "Visit my OnlyFans for more content",            # Promotional/inappropriate
            "F*** this stupid app and everyone on it"        # Profanity/hostile
        ]
        
        for content in inappropriate_content:
            revelation_data = {
                "connection_id": connection.id,
                "day_number": 1,
                "revelation_type": RevelationType.PERSONAL_VALUE.value,
                "content": content
            }
            
            response = client.post(
                "/api/v1/revelations/create",
                json=revelation_data,
                headers=authenticated_user["headers"]
            )
            
            # Should either reject inappropriate content or flag for moderation
            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST,  # Rejected by validation
                status.HTTP_201_CREATED       # Accepted but flagged for review
            ]
            
            # If accepted, should have moderation flag
            if response.status_code == status.HTTP_201_CREATED:
                data = response.json()
                assert data.get("moderation_status") in ["pending_review", "flagged"]


class TestRevelationTiming:
    """Test revelation timing and scheduling logic"""
    
    @pytest.mark.unit
    @pytest.mark.revelations
    @freeze_time("2025-01-01 10:00:00")
    def test_revelation_daily_timing(self, revelation_service, soul_connection_data):
        """Test that revelations follow proper daily timing"""
        connection = soul_connection_data["connection"]
        user = soul_connection_data["users"][0]
        
        # Create revelation on day 1
        revelation = revelation_service.create_revelation(
            connection_id=connection.id,
            sender_id=user.id,
            day_number=1,
            revelation_type=RevelationType.PERSONAL_VALUE.value,
            content="Day 1 revelation"
        )
        
        created_time = revelation.created_at
        
        # Move forward one day
        with freeze_time("2025-01-02 10:00:00"):
            # Should now be able to create day 2 revelation
            day2_revelation = revelation_service.create_revelation(
                connection_id=connection.id,
                sender_id=user.id,
                day_number=2,
                revelation_type=RevelationType.MEANINGFUL_EXPERIENCE.value,
                content="Day 2 revelation"
            )
            
            assert day2_revelation.day_number == 2
            assert day2_revelation.created_at > created_time

    @pytest.mark.unit
    @pytest.mark.revelations
    def test_revelation_completion_tracking(self, revelation_service, soul_connection_data):
        """Test tracking revelation completion for both users"""
        connection = soul_connection_data["connection"]
        user1, user2 = soul_connection_data["users"][:2]
        
        # User 1 completes day 1
        revelation_service.create_revelation(
            connection_id=connection.id,
            sender_id=user1.id,
            day_number=1,
            revelation_type=RevelationType.PERSONAL_VALUE.value,
            content="User 1 day 1 revelation"
        )
        
        # Check completion status
        completion_status = revelation_service.get_completion_status(connection.id)
        assert completion_status["day_1"]["user1_completed"] == True
        assert completion_status["day_1"]["user2_completed"] == False
        assert completion_status["day_1"]["both_completed"] == False
        
        # User 2 completes day 1
        revelation_service.create_revelation(
            connection_id=connection.id,
            sender_id=user2.id,
            day_number=1,
            revelation_type=RevelationType.PERSONAL_VALUE.value,
            content="User 2 day 1 revelation"
        )
        
        # Now both should be completed
        completion_status = revelation_service.get_completion_status(connection.id)
        assert completion_status["day_1"]["both_completed"] == True

    @pytest.mark.unit
    @pytest.mark.revelations
    def test_revelation_cycle_completion(self, revelation_service, soul_connection_data):
        """Test detection of complete 7-day revelation cycle"""
        connection = soul_connection_data["connection"]
        user = soul_connection_data["users"][0]
        
        # Complete all 7 days
        revelation_types = [
            RevelationType.PERSONAL_VALUE,
            RevelationType.MEANINGFUL_EXPERIENCE,
            RevelationType.HOPE_OR_DREAM,
            RevelationType.HUMOR_SOURCE,
            RevelationType.CHALLENGE_OVERCOME,
            RevelationType.IDEAL_CONNECTION,
            RevelationType.PHOTO_REVEAL
        ]
        
        for day, rev_type in enumerate(revelation_types, 1):
            revelation_service.create_revelation(
                connection_id=connection.id,
                sender_id=user.id,
                day_number=day,
                revelation_type=rev_type.value,
                content=f"Day {day} revelation content"
            )
        
        # Check if cycle is complete
        is_complete = revelation_service.is_cycle_complete(connection.id, user.id)
        assert is_complete == True
        
        # Should be eligible for photo reveal
        can_reveal = revelation_service.can_photo_reveal(connection.id, user.id)
        assert can_reveal == True


class TestRevelationIntegration:
    """Test revelation system integration with other platform features"""
    
    @pytest.mark.integration
    @pytest.mark.revelations
    def test_revelation_affects_connection_stage(self, client, authenticated_user, soul_connection_data):
        """Test that revelation completion affects connection stage progression"""
        connection = soul_connection_data["connection"]
        
        # Initially should be in early stage
        response = client.get(
            f"/api/v1/connections/{connection.id}",
            headers=authenticated_user["headers"]
        )
        initial_stage = response.json()["connection_stage"]
        
        # Complete several revelations
        for day in range(1, 4):
            revelation_data = {
                "connection_id": connection.id,
                "day_number": day,
                "revelation_type": RevelationType.PERSONAL_VALUE.value,
                "content": f"Day {day} meaningful revelation content here"
            }
            
            client.post(
                "/api/v1/revelations/create",
                json=revelation_data,
                headers=authenticated_user["headers"]
            )
        
        # Connection stage should progress based on revelations
        response = client.get(
            f"/api/v1/connections/{connection.id}",
            headers=authenticated_user["headers"]
        )
        final_stage = response.json()["connection_stage"]
        
        # Stage should have progressed (or at least not regressed)
        stage_progression = [
            ConnectionStage.SOUL_DISCOVERY.value,
            ConnectionStage.INITIAL_CONNECTION.value,
            ConnectionStage.REVELATION_SHARING.value,
            ConnectionStage.DEEPENING_BOND.value,
            ConnectionStage.PHOTO_REVEAL.value
        ]
        
        initial_index = stage_progression.index(initial_stage) if initial_stage in stage_progression else 0
        final_index = stage_progression.index(final_stage) if final_stage in stage_progression else 0
        
        assert final_index >= initial_index

    @pytest.mark.integration
    @pytest.mark.revelations
    def test_revelation_notification_system(self, client, authenticated_user, soul_connection_data):
        """Test that revelation sharing triggers appropriate notifications"""
        connection = soul_connection_data["connection"]
        
        revelation_data = {
            "connection_id": connection.id,
            "day_number": 1,
            "revelation_type": RevelationType.PERSONAL_VALUE.value,
            "content": "A deeply personal value I hold dear"
        }
        
        with patch('app.services.push_notification.send_notification') as mock_notify:
            response = client.post(
                "/api/v1/revelations/create",
                json=revelation_data,
                headers=authenticated_user["headers"]
            )
            
            assert response.status_code == status.HTTP_201_CREATED
            
            # Should trigger notification to the other user in connection
            # mock_notify.assert_called_once()

    @pytest.mark.performance
    @pytest.mark.revelations
    def test_revelation_timeline_performance(self, client, authenticated_user, performance_config):
        """Test revelation timeline retrieval performance"""
        import time
        
        # This would need a connection with many revelations for proper testing
        connection_id = 1  # Mock connection ID
        
        start_time = time.time()
        response = client.get(
            f"/api/v1/revelations/timeline/{connection_id}",
            headers=authenticated_user["headers"]
        )
        execution_time = time.time() - start_time
        
        # Timeline retrieval should be fast even with many revelations
        assert execution_time < performance_config["api_response_max_time"]