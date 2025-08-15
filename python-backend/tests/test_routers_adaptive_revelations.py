import pytest
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session
from datetime import datetime

from app.main import app
from app.models.user import User
from app.models.soul_connection import SoulConnection
from app.models.daily_revelation import DailyRevelation


class TestAdaptiveRevelationsRouter:
    
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
        return user
    
    @pytest.fixture
    def mock_partner(self):
        partner = Mock(spec=User)
        partner.id = 456
        partner.email = "partner@example.com"
        partner.username = "partner"
        return partner
    
    @pytest.fixture
    def mock_connection(self, mock_user, mock_partner):
        connection = Mock(spec=SoulConnection)
        connection.id = 789
        connection.user1_id = mock_user.id
        connection.user2_id = mock_partner.id
        connection.connection_stage = "soul_discovery"
        connection.reveal_day = 1
        return connection
    
    @pytest.fixture
    def mock_revelation(self, mock_user, mock_connection):
        revelation = Mock(spec=DailyRevelation)
        revelation.id = 100
        revelation.user_id = mock_user.id
        revelation.connection_id = mock_connection.id
        revelation.day_number = 1
        revelation.content = "This is my revelation content"
        revelation.revelation_type = "values_and_beliefs"
        return revelation
    
    @pytest.fixture
    def auth_headers(self):
        return {"Authorization": "Bearer fake_token"}
    
    @pytest.fixture
    def valid_revelation_request(self, mock_connection):
        return {
            "connection_id": mock_connection.id,
            "revelation_day": 3,
            "count": 3,
            "preferred_themes": ["values_and_beliefs", "personal_growth"],
            "user_context": {
                "current_mood": "reflective",
                "available_time": "medium"
            }
        }
    
    @pytest.fixture
    def mock_adaptive_prompts(self):
        return [
            {
                "prompt_id": "prompt_1",
                "template": "Share a value that guides your life decisions.",
                "theme": "values_and_beliefs",
                "difficulty_level": "medium",
                "estimated_time_minutes": 10,
                "personalization_score": 0.85,
                "context_relevance": 0.9
            },
            {
                "prompt_id": "prompt_2", 
                "template": "Describe a moment when you felt truly understood.",
                "theme": "emotional_connection",
                "difficulty_level": "high",
                "estimated_time_minutes": 15,
                "personalization_score": 0.78,
                "context_relevance": 0.82
            }
        ]

    @pytest.mark.asyncio
    async def test_generate_adaptive_revelation_prompts_success(
        self, client, mock_db, mock_user, mock_connection, valid_revelation_request, 
        mock_adaptive_prompts, auth_headers
    ):
        """Test successful adaptive revelation prompt generation"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_connection
        
        with patch('app.core.auth.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.services.adaptive_revelation_service.adaptive_revelation_engine.generate_adaptive_revelation_prompts', 
                          return_value=mock_adaptive_prompts):
                    response = client.post(
                        "/api/v1/adaptive-revelations/generate",
                        json=valid_revelation_request,
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert len(data) == 2
                    assert data[0]["prompt_id"] == "prompt_1"
                    assert data[0]["theme"] == "values_and_beliefs"
                    assert data[1]["prompt_id"] == "prompt_2"

    @pytest.mark.asyncio
    async def test_generate_adaptive_revelation_prompts_connection_not_found(
        self, client, mock_db, mock_user, valid_revelation_request, auth_headers
    ):
        """Test revelation prompt generation with non-existent connection"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with patch('app.core.auth.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                response = client.post(
                    "/api/v1/adaptive-revelations/generate",
                    json=valid_revelation_request,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_404_NOT_FOUND
                assert "Connection not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_generate_adaptive_revelation_prompts_invalid_day(
        self, client, mock_db, mock_user, mock_connection, auth_headers
    ):
        """Test revelation prompt generation with invalid revelation day"""
        invalid_request = {
            "connection_id": mock_connection.id,
            "revelation_day": 8,  # Invalid day
            "count": 3
        }
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_connection
        
        with patch('app.core.auth.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                response = client.post(
                    "/api/v1/adaptive-revelations/generate",
                    json=invalid_request,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_400_BAD_REQUEST
                assert "must be between 1 and 7" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_generate_adaptive_revelation_prompts_service_error(
        self, client, mock_db, mock_user, mock_connection, valid_revelation_request, auth_headers
    ):
        """Test revelation prompt generation with service error"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_connection
        
        with patch('app.core.auth.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.services.adaptive_revelation_service.adaptive_revelation_engine.generate_adaptive_revelation_prompts',
                          side_effect=Exception("Service error")):
                    response = client.post(
                        "/api/v1/adaptive-revelations/generate",
                        json=valid_revelation_request,
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                    assert "Failed to generate adaptive revelation prompts" in response.json()["detail"]

    def test_get_available_revelation_themes_success(self, client, mock_user, auth_headers):
        """Test successful retrieval of revelation themes"""
        mock_themes = {
            "values_and_beliefs": {
                "description": "Explore your core values and beliefs",
                "communication_style": "reflective",
                "requires_high_compatibility": False,
                "templates": [
                    {"template": "What value guides your decisions?"},
                    {"template": "Describe your core belief system."}
                ]
            },
            "personal_growth": {
                "description": "Share your growth journey",
                "communication_style": "inspiring",
                "requires_high_compatibility": True,
                "templates": [
                    {"template": "What changed you recently?"}
                ]
            }
        }
        
        with patch('app.core.auth.get_current_user', return_value=mock_user):
            with patch('app.services.adaptive_revelation_service.adaptive_revelation_engine.revelation_themes', 
                      {3: mock_themes}):
                with patch('app.services.adaptive_revelation_service.adaptive_revelation_engine.depth_progression',
                          {3: {"emotional_intensity": 0.7}}):
                    response = client.get(
                        "/api/v1/adaptive-revelations/themes/3",
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert len(data) == 2
                    assert data[0]["name"] == "values_and_beliefs"
                    assert data[0]["description"] == "Explore your core values and beliefs"
                    assert data[0]["emotional_intensity"] == 0.7

    def test_get_available_revelation_themes_invalid_day(self, client, mock_user, auth_headers):
        """Test revelation themes retrieval with invalid day"""
        with patch('app.core.auth.get_current_user', return_value=mock_user):
            response = client.get(
                "/api/v1/adaptive-revelations/themes/0",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "must be between 1 and 7" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_revelation_timing_recommendations_success(
        self, client, mock_db, mock_user, mock_connection, auth_headers
    ):
        """Test successful timing recommendations retrieval"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_connection
        
        mock_context = {"user_activity_pattern": "evening", "connection_momentum": "high"}
        mock_timing = {
            "recommended_hours": [18, 19, 20, 21],
            "optimal_day_time": "evening",
            "reasoning": "Based on your activity patterns and connection momentum",
            "urgency": "medium"
        }
        
        with patch('app.core.auth.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.services.adaptive_revelation_service.adaptive_revelation_engine._build_revelation_context',
                          return_value=mock_context):
                    with patch('app.services.adaptive_revelation_service.adaptive_revelation_engine._get_timing_recommendation',
                              return_value=mock_timing):
                        response = client.get(
                            f"/api/v1/adaptive-revelations/timing-recommendations/{mock_connection.id}",
                            headers=auth_headers
                        )
                        
                        assert response.status_code == status.HTTP_200_OK
                        data = response.json()
                        assert data["connection_id"] == mock_connection.id
                        assert data["optimal_day_time"] == "evening"
                        assert data["urgency"] == "medium"

    @pytest.mark.asyncio
    async def test_get_revelation_timing_recommendations_no_access(
        self, client, mock_db, mock_user, auth_headers
    ):
        """Test timing recommendations with no connection access"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with patch('app.core.auth.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                response = client.get(
                    "/api/v1/adaptive-revelations/timing-recommendations/999",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_404_NOT_FOUND
                assert "Connection not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_submit_revelation_feedback_success(
        self, client, mock_db, mock_user, mock_revelation, auth_headers
    ):
        """Test successful feedback submission"""
        feedback_request = {
            "revelation_id": mock_revelation.id,
            "content_id": "prompt_123",
            "helpful_score": 4,
            "engagement_score": 5,
            "emotional_resonance": 4,
            "timing_appropriateness": 3,
            "comments": "Very thoughtful prompt that made me reflect deeply"
        }
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_revelation
        
        with patch('app.core.auth.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.services.personalization_service.personalization_engine.record_content_feedback',
                          return_value=True):
                    response = client.post(
                        "/api/v1/adaptive-revelations/feedback",
                        json=feedback_request,
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert data["success"] is True
                    assert "improve future revelation prompts" in data["message"]

    @pytest.mark.asyncio
    async def test_submit_revelation_feedback_revelation_not_found(
        self, client, mock_db, mock_user, auth_headers
    ):
        """Test feedback submission with non-existent revelation"""
        feedback_request = {
            "revelation_id": 999,
            "content_id": "prompt_123",
            "helpful_score": 4,
            "engagement_score": 5,
            "emotional_resonance": 4,
            "timing_appropriateness": 3
        }
        
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with patch('app.core.auth.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                response = client.post(
                    "/api/v1/adaptive-revelations/feedback",
                    json=feedback_request,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_404_NOT_FOUND
                assert "Revelation not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_submit_revelation_feedback_service_failure(
        self, client, mock_db, mock_user, mock_revelation, auth_headers
    ):
        """Test feedback submission with service failure"""
        feedback_request = {
            "revelation_id": mock_revelation.id,
            "content_id": "prompt_123",
            "helpful_score": 4,
            "engagement_score": 5,
            "emotional_resonance": 4,
            "timing_appropriateness": 3
        }
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_revelation
        
        with patch('app.core.auth.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.services.personalization_service.personalization_engine.record_content_feedback',
                          return_value=False):
                    response = client.post(
                        "/api/v1/adaptive-revelations/feedback",
                        json=feedback_request,
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                    assert "Failed to record feedback" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_revelation_analytics_success(
        self, client, mock_db, mock_user, mock_connection, auth_headers
    ):
        """Test successful revelation analytics retrieval"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_connection
        
        # Mock revelations
        mock_revelations = []
        for i in range(1, 4):  # 3 completed days
            rev = Mock()
            rev.day_number = i
            rev.content = f"Revelation {i} content with multiple words here"
            rev.revelation_type = "values_and_beliefs" if i % 2 else "personal_growth"
            mock_revelations.append(rev)
        
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_revelations
        
        mock_patterns = {
            "engagement_trend": "increasing",
            "preferred_types": ["values_and_beliefs", "personal_growth", "future_dreams"]
        }
        
        with patch('app.core.auth.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.services.adaptive_revelation_service.adaptive_revelation_engine._analyze_user_revelation_patterns',
                          return_value=mock_patterns):
                    response = client.get(
                        f"/api/v1/adaptive-revelations/analytics/{mock_connection.id}",
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert data["connection_id"] == mock_connection.id
                    assert data["completed_revelation_days"] == 3
                    assert data["total_revelations_shared"] == 3
                    assert data["engagement_trend"] == "increasing"
                    assert len(data["most_successful_themes"]) == 3

    @pytest.mark.asyncio
    async def test_get_revelation_analytics_no_revelations(
        self, client, mock_db, mock_user, mock_connection, auth_headers
    ):
        """Test revelation analytics with no revelations"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_connection
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        mock_patterns = {
            "engagement_trend": "developing",
            "preferred_types": []
        }
        
        with patch('app.core.auth.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.services.adaptive_revelation_service.adaptive_revelation_engine._analyze_user_revelation_patterns',
                          return_value=mock_patterns):
                    response = client.get(
                        f"/api/v1/adaptive-revelations/analytics/{mock_connection.id}",
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert data["completed_revelation_days"] == 0
                    assert data["total_revelations_shared"] == 0
                    assert data["average_words_per_revelation"] == 0.0

    @pytest.mark.asyncio
    async def test_get_revelation_progress_success(
        self, client, mock_db, mock_user, mock_partner, mock_connection, auth_headers
    ):
        """Test successful revelation progress retrieval"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_connection
        
        # Mock user revelations (days 1, 2, 3)
        user_revelations = []
        for day in [1, 2, 3]:
            rev = Mock()
            rev.day_number = day
            user_revelations.append(rev)
        
        # Mock partner revelations (days 1, 2)
        partner_revelations = []
        for day in [1, 2]:
            rev = Mock()
            rev.day_number = day
            partner_revelations.append(rev)
        
        # Setup query mocking to return different results based on filter
        def mock_query_filter(*args, **kwargs):
            mock_query = Mock()
            if hasattr(args[0], 'user_id') and args[0].user_id == mock_user.id:
                mock_query.all.return_value = user_revelations
            else:
                mock_query.all.return_value = partner_revelations
            return mock_query
        
        mock_db.query.return_value.filter.side_effect = mock_query_filter
        
        with patch('app.core.auth.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                response = client.get(
                    f"/api/v1/adaptive-revelations/progress/{mock_connection.id}",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["connection_id"] == mock_connection.id
                assert data["current_revelation_day"] == 4  # max(3, 2) + 1
                assert data["user_progress"]["total_completed"] == 3
                assert data["partner_progress"]["total_completed"] == 2
                assert data["mutual_completion"]["completed_together"] == [1, 2]
                assert data["mutual_completion"]["waiting_for_partner"] == [3]
                assert data["can_proceed_to_photo_reveal"] is False
                assert data["days_until_photo_reveal"] == 5  # 7 - min(3, 2)

    @pytest.mark.asyncio
    async def test_get_revelation_progress_completed_cycle(
        self, client, mock_db, mock_user, mock_partner, mock_connection, auth_headers
    ):
        """Test revelation progress when both users completed all 7 days"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_connection
        
        # Both users completed all 7 days
        all_days_revelations = []
        for day in range(1, 8):
            rev = Mock()
            rev.day_number = day
            all_days_revelations.append(rev)
        
        mock_db.query.return_value.filter.return_value.all.return_value = all_days_revelations
        
        with patch('app.core.auth.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                response = client.get(
                    f"/api/v1/adaptive-revelations/progress/{mock_connection.id}",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["can_proceed_to_photo_reveal"] is True
                assert data["days_until_photo_reveal"] == 0
                assert data["user_progress"]["next_day"] is None
                assert data["partner_progress"]["next_day"] is None

    def test_get_revelation_progress_unauthorized(self, client, mock_db, mock_user, auth_headers):
        """Test revelation progress with unauthorized access"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with patch('app.core.auth.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                response = client.get(
                    "/api/v1/adaptive-revelations/progress/999",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_404_NOT_FOUND
                assert "Connection not found" in response.json()["detail"]

    def test_generate_adaptive_revelation_prompts_missing_fields(self, client, auth_headers):
        """Test revelation prompt generation with missing required fields"""
        incomplete_request = {
            "connection_id": 123,
            # Missing revelation_day and count
        }
        
        response = client.post(
            "/api/v1/adaptive-revelations/generate",
            json=incomplete_request,
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_submit_revelation_feedback_invalid_scores(self, client, auth_headers):
        """Test feedback submission with invalid score values"""
        invalid_feedback = {
            "revelation_id": 100,
            "content_id": "prompt_123",
            "helpful_score": 6,  # Assuming 1-5 scale
            "engagement_score": -1,  # Invalid negative
            "emotional_resonance": 4,
            "timing_appropriateness": 3
        }
        
        response = client.post(
            "/api/v1/adaptive-revelations/feedback",
            json=invalid_feedback,
            headers=auth_headers
        )
        
        # Would depend on validation in the schema
        assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST]

    @pytest.mark.asyncio
    async def test_get_revelation_themes_empty_day(self, client, mock_user, auth_headers):
        """Test revelation themes retrieval for day with no themes"""
        with patch('app.core.auth.get_current_user', return_value=mock_user):
            with patch('app.services.adaptive_revelation_service.adaptive_revelation_engine.revelation_themes', 
                      {5: {}}):  # Empty themes for day 5
                with patch('app.services.adaptive_revelation_service.adaptive_revelation_engine.depth_progression',
                          {5: {"emotional_intensity": 0.8}}):
                    response = client.get(
                        "/api/v1/adaptive-revelations/themes/5",
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert len(data) == 0

    @pytest.mark.asyncio
    async def test_connection_access_validation_user2(
        self, client, mock_db, mock_user, mock_partner, valid_revelation_request, auth_headers
    ):
        """Test connection access when current user is user2 in connection"""
        # Setup connection where current user is user2
        connection = Mock(spec=SoulConnection)
        connection.id = 789
        connection.user1_id = mock_partner.id  # Partner is user1
        connection.user2_id = mock_user.id     # Current user is user2
        
        mock_db.query.return_value.filter.return_value.first.return_value = connection
        
        with patch('app.core.auth.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.services.adaptive_revelation_service.adaptive_revelation_engine.generate_adaptive_revelation_prompts',
                          return_value=[]):
                    response = client.post(
                        "/api/v1/adaptive-revelations/generate",
                        json=valid_revelation_request,
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_error_logging_in_endpoints(self, client, mock_db, mock_user, mock_connection, valid_revelation_request, auth_headers):
        """Test that errors are properly logged in endpoints"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_connection
        
        with patch('app.core.auth.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.services.adaptive_revelation_service.adaptive_revelation_engine.generate_adaptive_revelation_prompts',
                          side_effect=Exception("Test error")):
                    with patch('app.api.v1.routers.adaptive_revelations.logger') as mock_logger:
                        response = client.post(
                            "/api/v1/adaptive-revelations/generate",
                            json=valid_revelation_request,
                            headers=auth_headers
                        )
                        
                        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                        mock_logger.error.assert_called_once()
                        error_msg = mock_logger.error.call_args[0][0]
                        assert "Error generating adaptive revelation prompts" in error_msg

    def test_revelation_day_boundary_values(self, client, mock_user, auth_headers):
        """Test revelation day validation with boundary values"""
        test_cases = [
            (0, status.HTTP_400_BAD_REQUEST),
            (1, status.HTTP_200_OK),
            (7, status.HTTP_200_OK),
            (8, status.HTTP_400_BAD_REQUEST),
            (-1, status.HTTP_400_BAD_REQUEST),
            (100, status.HTTP_400_BAD_REQUEST)
        ]
        
        with patch('app.core.auth.get_current_user', return_value=mock_user):
            with patch('app.services.adaptive_revelation_service.adaptive_revelation_engine.revelation_themes', {}):
                for day, expected_status in test_cases:
                    response = client.get(
                        f"/api/v1/adaptive-revelations/themes/{day}",
                        headers=auth_headers
                    )
                    
                    assert response.status_code == expected_status

    @pytest.mark.asyncio
    async def test_revelation_analytics_theme_distribution(
        self, client, mock_db, mock_user, mock_connection, auth_headers
    ):
        """Test revelation analytics theme distribution calculation"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_connection
        
        # Mock revelations with different themes
        mock_revelations = []
        themes = ["values_and_beliefs", "values_and_beliefs", "personal_growth", "future_dreams", "values_and_beliefs"]
        for i, theme in enumerate(themes, 1):
            rev = Mock()
            rev.day_number = i
            rev.content = f"Content for day {i}"
            rev.revelation_type = theme
            mock_revelations.append(rev)
        
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_revelations
        
        with patch('app.core.auth.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.services.adaptive_revelation_service.adaptive_revelation_engine._analyze_user_revelation_patterns',
                          return_value={"engagement_trend": "developing", "preferred_types": []}):
                    response = client.get(
                        f"/api/v1/adaptive-revelations/analytics/{mock_connection.id}",
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert data["theme_distribution"]["values_and_beliefs"] == 3
                    assert data["theme_distribution"]["personal_growth"] == 1
                    assert data["theme_distribution"]["future_dreams"] == 1