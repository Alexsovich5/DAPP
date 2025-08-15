import pytest
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.api.v1.routers.onboarding import OnboardingData


class TestOnboardingRouter:
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_user(self):
        user = Mock(spec=User)
        user.id = 123
        user.email = "test@example.com"
        user.username = "testuser"
        user.emotional_onboarding_completed = False
        user.interests = []
        user.is_profile_complete = False
        return user
    
    @pytest.fixture
    def valid_onboarding_data(self):
        return {
            "relationship_values": "I value honesty, trust, and emotional connection above all else.",
            "ideal_evening": "A quiet dinner followed by a deep conversation under the stars.",
            "feeling_understood": "When someone listens without judgment and asks thoughtful questions.",
            "core_values": {
                "honesty": 0.9,
                "empathy": 0.8,
                "adventure": 0.7,
                "stability": 0.6
            },
            "personality_traits": {
                "openness": 0.8,
                "conscientiousness": 0.7,
                "extraversion": 0.6,
                "agreeableness": 0.9,
                "neuroticism": 0.3
            },
            "communication_style": {
                "direct": 0.7,
                "emotional": 0.8,
                "analytical": 0.6,
                "supportive": 0.9
            },
            "interests": ["travel", "photography", "hiking", "cooking", "reading"]
        }
    
    @pytest.fixture
    def auth_headers(self):
        return {"Authorization": "Bearer fake_token"}

    def test_onboarding_data_model(self, valid_onboarding_data):
        """Test OnboardingData model validation"""
        onboarding_data = OnboardingData(**valid_onboarding_data)
        
        assert onboarding_data.relationship_values == valid_onboarding_data["relationship_values"]
        assert onboarding_data.ideal_evening == valid_onboarding_data["ideal_evening"]
        assert onboarding_data.feeling_understood == valid_onboarding_data["feeling_understood"]
        assert onboarding_data.core_values == valid_onboarding_data["core_values"]
        assert onboarding_data.personality_traits == valid_onboarding_data["personality_traits"]
        assert onboarding_data.communication_style == valid_onboarding_data["communication_style"]
        assert onboarding_data.interests == valid_onboarding_data["interests"]

    def test_complete_onboarding_success(self, client, mock_db, mock_user, valid_onboarding_data, auth_headers):
        """Test successful onboarding completion"""
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                response = client.post(
                    "/api/v1/onboarding/complete",
                    json=valid_onboarding_data,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                
                # Verify user was updated
                assert mock_user.emotional_onboarding_completed is True
                assert mock_user.interests == valid_onboarding_data["interests"]
                
                # Verify database operations
                mock_db.commit.assert_called_once()
                mock_db.refresh.assert_called_once_with(mock_user)

    def test_complete_onboarding_missing_fields(self, client, auth_headers):
        """Test onboarding completion with missing required fields"""
        incomplete_data = {
            "relationship_values": "I value honesty",
            "ideal_evening": "A quiet dinner",
            # Missing required fields
        }
        
        with patch('app.api.v1.deps.get_current_user'):
            response = client.post(
                "/api/v1/onboarding/complete",
                json=incomplete_data,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_complete_onboarding_invalid_data_types(self, client, auth_headers):
        """Test onboarding completion with invalid data types"""
        invalid_data = {
            "relationship_values": "I value honesty",
            "ideal_evening": "A quiet dinner",
            "feeling_understood": "When someone listens",
            "core_values": "not_a_dict",  # Should be dict
            "personality_traits": ["not_a_dict"],  # Should be dict
            "communication_style": 123,  # Should be dict
            "interests": "not_a_list"  # Should be list
        }
        
        with patch('app.api.v1.deps.get_current_user'):
            response = client.post(
                "/api/v1/onboarding/complete",
                json=invalid_data,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_complete_onboarding_empty_strings(self, client, mock_user, auth_headers):
        """Test onboarding completion with empty string values"""
        empty_data = {
            "relationship_values": "",
            "ideal_evening": "",
            "feeling_understood": "",
            "core_values": {},
            "personality_traits": {},
            "communication_style": {},
            "interests": []
        }
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db') as mock_get_db:
                mock_db = Mock()
                mock_get_db.return_value = mock_db
                
                response = client.post(
                    "/api/v1/onboarding/complete",
                    json=empty_data,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                assert mock_user.emotional_onboarding_completed is True
                assert mock_user.interests == []

    def test_complete_onboarding_database_error(self, client, mock_db, mock_user, valid_onboarding_data, auth_headers):
        """Test onboarding completion with database error"""
        mock_db.commit.side_effect = Exception("Database error")
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                response = client.post(
                    "/api/v1/onboarding/complete",
                    json=valid_onboarding_data,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                assert "Failed to complete onboarding" in response.json()["detail"]
                
                # Verify rollback was called
                mock_db.rollback.assert_called_once()

    def test_complete_onboarding_unauthorized(self, client, valid_onboarding_data):
        """Test onboarding completion without authentication"""
        response = client.post(
            "/api/v1/onboarding/complete",
            json=valid_onboarding_data
        )
        
        # Should be unauthorized without proper authentication
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_complete_onboarding_comprehensive_interests(self, client, mock_db, mock_user, auth_headers):
        """Test onboarding completion with comprehensive interests list"""
        comprehensive_data = {
            "relationship_values": "Deep emotional connection and mutual growth",
            "ideal_evening": "Exploring a new city together and trying local cuisine",
            "feeling_understood": "Through genuine empathy and shared experiences",
            "core_values": {
                "authenticity": 0.95,
                "growth": 0.9,
                "adventure": 0.85,
                "compassion": 0.9,
                "creativity": 0.8
            },
            "personality_traits": {
                "openness": 0.9,
                "conscientiousness": 0.8,
                "extraversion": 0.7,
                "agreeableness": 0.85,
                "neuroticism": 0.2
            },
            "communication_style": {
                "direct": 0.8,
                "emotional": 0.9,
                "analytical": 0.7,
                "supportive": 0.95,
                "playful": 0.8
            },
            "interests": [
                "travel", "photography", "hiking", "cooking", "reading",
                "music", "art", "dancing", "wine_tasting", "yoga",
                "meditation", "volunteering", "learning_languages",
                "podcasts", "board_games", "theater"
            ]
        }
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                response = client.post(
                    "/api/v1/onboarding/complete",
                    json=comprehensive_data,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                assert len(mock_user.interests) == 16

    def test_get_onboarding_status_completed(self, client, auth_headers):
        """Test getting onboarding status for completed user"""
        completed_user = Mock(spec=User)
        completed_user.emotional_onboarding_completed = True
        completed_user.interests = ["travel", "photography"]
        completed_user.is_profile_complete = True
        
        with patch('app.api.v1.deps.get_current_user', return_value=completed_user):
            response = client.get(
                "/api/v1/onboarding/status",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["completed"] is True
            assert data["has_interests"] is True
            assert data["profile_complete"] is True

    def test_get_onboarding_status_incomplete(self, client, mock_user, auth_headers):
        """Test getting onboarding status for incomplete user"""
        mock_user.emotional_onboarding_completed = False
        mock_user.interests = None
        mock_user.is_profile_complete = False
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            response = client.get(
                "/api/v1/onboarding/status",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["completed"] is False
            assert data["has_interests"] is False
            assert data["profile_complete"] is False

    def test_get_onboarding_status_partial(self, client, auth_headers):
        """Test getting onboarding status for partially completed user"""
        partial_user = Mock(spec=User)
        partial_user.emotional_onboarding_completed = False
        partial_user.interests = ["travel"]
        partial_user.is_profile_complete = True
        
        with patch('app.api.v1.deps.get_current_user', return_value=partial_user):
            response = client.get(
                "/api/v1/onboarding/status",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["completed"] is False
            assert data["has_interests"] is True
            assert data["profile_complete"] is True

    def test_get_onboarding_status_unauthorized(self, client):
        """Test getting onboarding status without authentication"""
        response = client.get("/api/v1/onboarding/status")
        
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    def test_get_onboarding_status_null_values(self, client, auth_headers):
        """Test getting onboarding status with null/None values"""
        null_user = Mock(spec=User)
        null_user.emotional_onboarding_completed = None
        null_user.interests = None
        null_user.is_profile_complete = None
        
        with patch('app.api.v1.deps.get_current_user', return_value=null_user):
            response = client.get(
                "/api/v1/onboarding/status",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["completed"] is False
            assert data["has_interests"] is False
            assert data["profile_complete"] is False

    def test_handle_onboarding_complete_options(self, client):
        """Test OPTIONS request handling for onboarding complete endpoint"""
        response = client.options("/api/v1/onboarding/complete")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "OK"

    def test_complete_onboarding_with_special_characters(self, client, mock_db, mock_user, auth_headers):
        """Test onboarding completion with special characters in text fields"""
        special_char_data = {
            "relationship_values": "I value honesty, trust, & emotional connection! 💕",
            "ideal_evening": "Café dinner with crème brûlée & a walk in the parc 🌟",
            "feeling_understood": "When someone truly 'gets' me & doesn't judge 🤗",
            "core_values": {
                "honesty": 0.9,
                "empathy": 0.8
            },
            "personality_traits": {
                "openness": 0.8
            },
            "communication_style": {
                "direct": 0.7
            },
            "interests": ["café-hopping", "français", "日本語", "coração"]
        }
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                response = client.post(
                    "/api/v1/onboarding/complete",
                    json=special_char_data,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                assert mock_user.emotional_onboarding_completed is True

    def test_complete_onboarding_large_text_fields(self, client, mock_db, mock_user, auth_headers):
        """Test onboarding completion with very long text fields"""
        long_text = "This is a very long text that represents a detailed user response. " * 50
        
        large_data = {
            "relationship_values": long_text,
            "ideal_evening": long_text,
            "feeling_understood": long_text,
            "core_values": {f"value_{i}": 0.5 for i in range(20)},
            "personality_traits": {f"trait_{i}": 0.5 for i in range(15)},
            "communication_style": {f"style_{i}": 0.5 for i in range(10)},
            "interests": [f"interest_{i}" for i in range(50)]
        }
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                response = client.post(
                    "/api/v1/onboarding/complete",
                    json=large_data,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                assert len(mock_user.interests) == 50

    def test_complete_onboarding_numeric_ranges(self, client, mock_db, mock_user, auth_headers):
        """Test onboarding completion with various numeric ranges for scores"""
        numeric_range_data = {
            "relationship_values": "Testing numeric ranges",
            "ideal_evening": "Testing numeric ranges",
            "feeling_understood": "Testing numeric ranges",
            "core_values": {
                "min_value": 0.0,
                "max_value": 1.0,
                "mid_value": 0.5,
                "high_precision": 0.123456789
            },
            "personality_traits": {
                "zero": 0.0,
                "one": 1.0,
                "decimal": 0.7777
            },
            "communication_style": {
                "test_range": 0.33333
            },
            "interests": ["testing", "numeric", "ranges"]
        }
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                response = client.post(
                    "/api/v1/onboarding/complete",
                    json=numeric_range_data,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK

    def test_complete_onboarding_already_completed(self, client, mock_db, auth_headers):
        """Test onboarding completion for user who already completed it"""
        already_completed_user = Mock(spec=User)
        already_completed_user.id = 123
        already_completed_user.email = "completed@example.com"
        already_completed_user.emotional_onboarding_completed = True
        already_completed_user.interests = ["existing", "interests"]
        
        new_data = {
            "relationship_values": "New values",
            "ideal_evening": "New evening",
            "feeling_understood": "New understanding",
            "core_values": {"new": 0.8},
            "personality_traits": {"new": 0.7},
            "communication_style": {"new": 0.6},
            "interests": ["new", "interests"]
        }
        
        with patch('app.api.v1.deps.get_current_user', return_value=already_completed_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                response = client.post(
                    "/api/v1/onboarding/complete",
                    json=new_data,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                # Should update interests even if already completed
                assert already_completed_user.interests == ["new", "interests"]

    def test_endpoint_cors_headers(self, client):
        """Test that CORS headers are properly handled"""
        response = client.options("/api/v1/onboarding/complete")
        
        assert response.status_code == status.HTTP_200_OK
        # CORS headers would typically be handled by middleware

    def test_complete_onboarding_response_format(self, client, mock_db, mock_user, valid_onboarding_data, auth_headers):
        """Test that onboarding completion returns proper user schema"""
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                response = client.post(
                    "/api/v1/onboarding/complete",
                    json=valid_onboarding_data,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                
                # Response should be a user object with proper fields
                user_data = response.json()
                assert isinstance(user_data, dict)
                # The exact fields depend on the UserSchema implementation

    def test_onboarding_status_response_format(self, client, mock_user, auth_headers):
        """Test that onboarding status returns proper format"""
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            response = client.get(
                "/api/v1/onboarding/status",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            
            # Should have all required fields
            assert "completed" in data
            assert "has_interests" in data
            assert "profile_complete" in data
            
            # All fields should be boolean
            assert isinstance(data["completed"], bool)
            assert isinstance(data["has_interests"], bool)
            assert isinstance(data["profile_complete"], bool)

    def test_complete_onboarding_logging(self, client, mock_db, mock_user, valid_onboarding_data, auth_headers):
        """Test that onboarding completion logs appropriately"""
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.api.v1.routers.onboarding.logger') as mock_logger:
                    response = client.post(
                        "/api/v1/onboarding/complete",
                        json=valid_onboarding_data,
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    
                    # Should log start and completion
                    assert mock_logger.info.call_count >= 2
                    call_args = [call[0][0] for call in mock_logger.info.call_args_list]
                    assert any("Completing onboarding" in msg for msg in call_args)
                    assert any("Onboarding completed successfully" in msg for msg in call_args)

    def test_complete_onboarding_error_logging(self, client, mock_db, mock_user, valid_onboarding_data, auth_headers):
        """Test that onboarding errors are logged appropriately"""
        mock_db.commit.side_effect = Exception("Test database error")
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.api.v1.routers.onboarding.logger') as mock_logger:
                    response = client.post(
                        "/api/v1/onboarding/complete",
                        json=valid_onboarding_data,
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                    
                    # Should log error
                    mock_logger.error.assert_called_once()
                    error_msg = mock_logger.error.call_args[0][0]
                    assert "Error completing onboarding" in error_msg
                    assert "Test database error" in error_msg