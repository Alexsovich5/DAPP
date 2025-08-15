import pytest
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.main import app
from app.models.user import User
from app.models.ui_personalization_models import (
    UserUIProfile, UIInteractionLog, UIPersonalizationEvent, UIPersonalizationInsight
)


class TestUIPersonalizationRouter:
    
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
    def mock_ui_profile(self):
        profile = Mock(spec=UserUIProfile)
        profile.id = 456
        profile.user_id = 123
        profile.primary_device_type = "mobile"
        profile.preferred_theme = "dark"
        profile.font_size_preference = "medium"
        profile.animation_preference = "enabled"
        profile.layout_density = "comfortable"
        profile.interaction_speed = "normal"
        profile.navigation_pattern = "tab_focused"
        profile.personalization_score = 0.78
        profile.screen_reader_enabled = False
        profile.keyboard_navigation_primary = False
        profile.high_contrast_enabled = False
        profile.reduce_motion_enabled = False
        profile.updated_at = datetime.utcnow()
        profile.get_current_preferences.return_value = {
            "theme": "dark",
            "font_size": "medium",
            "animations": "enabled"
        }
        profile.update_personalization_score = Mock()
        return profile
    
    @pytest.fixture
    def mock_ui_personalization_engine(self):
        engine = AsyncMock()
        engine.get_or_create_ui_profile = AsyncMock()
        engine.track_user_interaction = AsyncMock()
        engine.generate_ui_personalizations = AsyncMock()
        engine._analyze_user_behavior = AsyncMock()
        engine.adaptation_thresholds = {"confidence_threshold": 0.7}
        return engine
    
    @pytest.fixture
    def auth_headers(self):
        return {"Authorization": "Bearer fake_token"}
    
    @pytest.fixture
    def mock_insights(self):
        insights = []
        for i in range(3):
            insight = Mock(spec=UIPersonalizationInsight)
            insight.id = i + 1
            insight.insight_type = f"type_{i}"
            insight.insight_category = "usability"
            insight.title = f"Insight {i + 1}"
            insight.description = f"Description for insight {i + 1}"
            insight.recommended_action = f"Action {i + 1}"
            insight.implementation_priority = "medium"
            insight.confidence_score = 0.8
            insight.expected_impact = 0.6
            insight.generated_at = datetime.utcnow()
            insight.acted_upon = False
            insights.append(insight)
        return insights
    
    @pytest.fixture
    def mock_interactions(self):
        interactions = []
        for i in range(5):
            interaction = Mock(spec=UIInteractionLog)
            interaction.id = i + 1
            interaction.ui_profile_id = 456
            interaction.session_id = f"session_{i}"
            interaction.device_type = "mobile"
            interaction.page_route = f"/page_{i}"
            interaction.error_occurred = i % 2 == 0  # Every other interaction has error
            interaction.interaction_timestamp = datetime.utcnow() - timedelta(hours=i)
            interactions.append(interaction)
        return interactions

    @pytest.mark.asyncio
    async def test_get_ui_profile_success(
        self, client, mock_db, mock_user, mock_ui_profile, mock_ui_personalization_engine, auth_headers
    ):
        """Test successful UI profile retrieval"""
        mock_ui_personalization_engine.get_or_create_ui_profile.return_value = mock_ui_profile
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.api.v1.routers.ui_personalization.ui_personalization_engine', mock_ui_personalization_engine):
                    response = client.get(
                        "/api/v1/ui-personalization/profile",
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert data["id"] == 456
                    assert data["user_id"] == 123
                    assert data["primary_device_type"] == "mobile"
                    assert data["preferred_theme"] == "dark"
                    assert data["personalization_score"] == 0.78

    @pytest.mark.asyncio
    async def test_get_ui_profile_service_error(
        self, client, mock_db, mock_user, mock_ui_personalization_engine, auth_headers
    ):
        """Test UI profile retrieval with service error"""
        mock_ui_personalization_engine.get_or_create_ui_profile.side_effect = Exception("Profile error")
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.api.v1.routers.ui_personalization.ui_personalization_engine', mock_ui_personalization_engine):
                    response = client.get(
                        "/api/v1/ui-personalization/profile",
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                    assert "Failed to retrieve UI profile" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_track_user_interaction_success(
        self, client, mock_db, mock_user, mock_ui_personalization_engine, auth_headers
    ):
        """Test successful user interaction tracking"""
        interaction_data = {
            "interaction_type": "click",
            "element": "profile_button",
            "page_route": "/dashboard",
            "device_type": "mobile",
            "session_id": "session_123",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.api.v1.routers.ui_personalization.ui_personalization_engine', mock_ui_personalization_engine):
                    response = client.post(
                        "/api/v1/ui-personalization/track-interaction",
                        json=interaction_data,
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert data["success"] is True
                    assert "Interaction tracked successfully" in data["message"]

    @pytest.mark.asyncio
    async def test_track_user_interaction_error(
        self, client, mock_db, mock_user, auth_headers
    ):
        """Test user interaction tracking with error"""
        interaction_data = {
            "interaction_type": "click",
            "element": "button"
        }
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.api.v1.routers.ui_personalization.ui_personalization_engine') as mock_engine:
                    # Force an exception in background task setup
                    with patch('app.api.v1.routers.ui_personalization.BackgroundTasks') as mock_bg:
                        mock_bg.side_effect = Exception("Background task error")
                        
                        response = client.post(
                            "/api/v1/ui-personalization/track-interaction",
                            json=interaction_data,
                            headers=auth_headers
                        )
                        
                        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                        assert "Failed to track interaction" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_generate_ui_personalizations_success(
        self, client, mock_db, mock_user, mock_ui_personalization_engine, auth_headers
    ):
        """Test successful UI personalization generation"""
        request_data = {
            "current_context": {
                "page": "/dashboard",
                "device_type": "mobile",
                "time_of_day": "evening"
            }
        }
        
        mock_personalizations = {
            "theme_adjustment": {
                "confidence": 0.85,
                "recommendation": "dark_mode"
            },
            "layout_optimization": {
                "confidence": 0.72,
                "recommendation": "compact_layout"
            }
        }
        mock_ui_personalization_engine.generate_ui_personalizations.return_value = mock_personalizations
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.api.v1.routers.ui_personalization.ui_personalization_engine', mock_ui_personalization_engine):
                    with patch('app.api.v1.routers.ui_personalization.datetime') as mock_datetime:
                        mock_datetime.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
                        
                        response = client.post(
                            "/api/v1/ui-personalization/generate-adaptations",
                            json=request_data,
                            headers=auth_headers
                        )
                        
                        assert response.status_code == status.HTTP_200_OK
                        data = response.json()
                        assert data["user_id"] == 123
                        assert "personalizations" in data
                        assert "confidence_score" in data

    @pytest.mark.asyncio
    async def test_generate_ui_personalizations_error(
        self, client, mock_db, mock_user, mock_ui_personalization_engine, auth_headers
    ):
        """Test UI personalization generation with error"""
        request_data = {
            "current_context": {
                "page": "/dashboard"
            }
        }
        
        mock_ui_personalization_engine.generate_ui_personalizations.side_effect = Exception("Generation error")
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.api.v1.routers.ui_personalization.ui_personalization_engine', mock_ui_personalization_engine):
                    response = client.post(
                        "/api/v1/ui-personalization/generate-adaptations",
                        json=request_data,
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                    assert "Failed to generate UI personalizations" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_personalization_insights_success(
        self, client, mock_db, mock_user, mock_ui_profile, mock_insights, mock_ui_personalization_engine, auth_headers
    ):
        """Test successful personalization insights retrieval"""
        mock_ui_personalization_engine.get_or_create_ui_profile.return_value = mock_ui_profile
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_insights
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.api.v1.routers.ui_personalization.ui_personalization_engine', mock_ui_personalization_engine):
                    response = client.get(
                        "/api/v1/ui-personalization/insights",
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert len(data) == 3
                    assert data[0]["id"] == 1
                    assert data[0]["title"] == "Insight 1"

    @pytest.mark.asyncio
    async def test_get_personalization_insights_no_existing_insights(
        self, client, mock_db, mock_user, mock_ui_profile, mock_ui_personalization_engine, auth_headers
    ):
        """Test personalization insights when no existing insights"""
        mock_ui_personalization_engine.get_or_create_ui_profile.return_value = mock_ui_profile
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        # Mock generate_initial_insights function
        mock_initial_insights = [Mock(spec=UIPersonalizationInsight)]
        mock_initial_insights[0].id = 1
        mock_initial_insights[0].insight_type = "welcome"
        mock_initial_insights[0].insight_category = "onboarding"
        mock_initial_insights[0].title = "Welcome Insight"
        mock_initial_insights[0].description = "Welcome description"
        mock_initial_insights[0].recommended_action = "Get started"
        mock_initial_insights[0].implementation_priority = "low"
        mock_initial_insights[0].confidence_score = 1.0
        mock_initial_insights[0].expected_impact = 0.2
        mock_initial_insights[0].generated_at = datetime.utcnow()
        mock_initial_insights[0].acted_upon = False
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.api.v1.routers.ui_personalization.ui_personalization_engine', mock_ui_personalization_engine):
                    with patch('app.api.v1.routers.ui_personalization.generate_initial_insights', return_value=mock_initial_insights):
                        response = client.get(
                            "/api/v1/ui-personalization/insights",
                            headers=auth_headers
                        )
                        
                        assert response.status_code == status.HTTP_200_OK
                        data = response.json()
                        assert len(data) == 1
                        assert data[0]["title"] == "Welcome Insight"

    @pytest.mark.asyncio
    async def test_get_ui_analytics_success(
        self, client, mock_db, mock_user, mock_ui_profile, mock_interactions, mock_ui_personalization_engine, auth_headers
    ):
        """Test successful UI analytics retrieval"""
        mock_ui_personalization_engine.get_or_create_ui_profile.return_value = mock_ui_profile
        mock_db.query.return_value.filter.return_value.all.return_value = mock_interactions
        
        mock_behavior_analysis = {
            "efficiency_metrics": {"average_task_completion": 2.5},
            "performance_sensitivity": {"sensitive_to_slow_loading": True},
            "accessibility_needs": {"needs_high_contrast": False},
            "interaction_types": {"primary_style": "touch_focused"},
            "engagement_patterns": {"low_engagement": False}
        }
        mock_ui_personalization_engine._analyze_user_behavior.return_value = mock_behavior_analysis
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.api.v1.routers.ui_personalization.ui_personalization_engine', mock_ui_personalization_engine):
                    with patch('app.api.v1.routers.ui_personalization.generate_analytics_recommendations', return_value=["Recommendation 1"]):
                        response = client.get(
                            "/api/v1/ui-personalization/analytics?days=7",
                            headers=auth_headers
                        )
                        
                        assert response.status_code == status.HTTP_200_OK
                        data = response.json()
                        assert data["user_id"] == 123
                        assert data["analysis_period_days"] == 7
                        assert data["total_interactions"] == 5
                        assert data["error_rate"] == 0.6  # 3 out of 5 interactions had errors

    @pytest.mark.asyncio
    async def test_update_ui_preferences_success(
        self, client, mock_db, mock_user, mock_ui_profile, mock_ui_personalization_engine, auth_headers
    ):
        """Test successful UI preferences update"""
        mock_ui_personalization_engine.get_or_create_ui_profile.return_value = mock_ui_profile
        
        preferences = {
            "preferred_theme": "light",
            "font_size_preference": "large",
            "animation_preference": "disabled"
        }
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.api.v1.routers.ui_personalization.ui_personalization_engine', mock_ui_personalization_engine):
                    response = client.put(
                        "/api/v1/ui-personalization/preferences",
                        json=preferences,
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert data["success"] is True
                    assert data["message"] == "Updated 3 preferences"
                    assert len(data["updated_fields"]) == 3

    @pytest.mark.asyncio
    async def test_update_ui_preferences_invalid_fields(
        self, client, mock_db, mock_user, mock_ui_profile, mock_ui_personalization_engine, auth_headers
    ):
        """Test UI preferences update with invalid fields"""
        mock_ui_personalization_engine.get_or_create_ui_profile.return_value = mock_ui_profile
        
        preferences = {
            "invalid_field": "value",
            "another_invalid": "value2"
        }
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.api.v1.routers.ui_personalization.ui_personalization_engine', mock_ui_personalization_engine):
                    response = client.put(
                        "/api/v1/ui-personalization/preferences",
                        json=preferences,
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert data["success"] is True
                    assert data["message"] == "Updated 0 preferences"
                    assert len(data["updated_fields"]) == 0

    @pytest.mark.asyncio
    async def test_update_ui_preferences_database_error(
        self, client, mock_db, mock_user, mock_ui_profile, mock_ui_personalization_engine, auth_headers
    ):
        """Test UI preferences update with database error"""
        mock_ui_personalization_engine.get_or_create_ui_profile.return_value = mock_ui_profile
        mock_db.commit.side_effect = Exception("Database error")
        
        preferences = {
            "preferred_theme": "light"
        }
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.api.v1.routers.ui_personalization.ui_personalization_engine', mock_ui_personalization_engine):
                    response = client.put(
                        "/api/v1/ui-personalization/preferences",
                        json=preferences,
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                    assert "Failed to update UI preferences" in response.json()["detail"]
                    mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_personalization_feedback_success(
        self, client, mock_db, mock_user, mock_ui_profile, mock_ui_personalization_engine, auth_headers
    ):
        """Test successful personalization feedback submission"""
        mock_ui_personalization_engine.get_or_create_ui_profile.return_value = mock_ui_profile
        
        feedback = {
            "satisfaction_score": 0.8,
            "comments": "Great personalization!",
            "feature": "theme_adaptation"
        }
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.api.v1.routers.ui_personalization.ui_personalization_engine', mock_ui_personalization_engine):
                    response = client.post(
                        "/api/v1/ui-personalization/feedback",
                        json=feedback,
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert data["success"] is True
                    assert "Feedback recorded successfully" in data["message"]

    @pytest.mark.asyncio
    async def test_submit_personalization_feedback_low_satisfaction(
        self, client, mock_db, mock_user, mock_ui_profile, mock_ui_personalization_engine, auth_headers
    ):
        """Test personalization feedback with low satisfaction score"""
        mock_ui_personalization_engine.get_or_create_ui_profile.return_value = mock_ui_profile
        
        feedback = {
            "satisfaction_score": 0.4,  # Low satisfaction
            "comments": "Not working well",
            "feature": "layout_optimization"
        }
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.api.v1.routers.ui_personalization.ui_personalization_engine', mock_ui_personalization_engine):
                    response = client.post(
                        "/api/v1/ui-personalization/feedback",
                        json=feedback,
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert data["success"] is True
                    # Should create an insight for low satisfaction
                    mock_db.add.assert_called()

    @pytest.mark.asyncio
    async def test_get_active_ab_tests_success(
        self, client, mock_db, mock_user, mock_ui_profile, mock_ui_personalization_engine, auth_headers
    ):
        """Test successful active A/B tests retrieval"""
        mock_ui_personalization_engine.get_or_create_ui_profile.return_value = mock_ui_profile
        
        mock_ab_tests = []
        for i in range(2):
            test = Mock()
            test.id = i + 1
            test.test_name = f"test_{i}"
            test.test_variant = f"variant_{i}"
            test.test_category = "ui_optimization"
            test.enrolled_at = datetime.utcnow()
            test.session_count = 5
            mock_ab_tests.append(test)
        
        mock_db.query.return_value.filter.return_value.all.return_value = mock_ab_tests
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.api.v1.routers.ui_personalization.ui_personalization_engine', mock_ui_personalization_engine):
                    response = client.get(
                        "/api/v1/ui-personalization/ab-tests",
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert len(data["active_tests"]) == 2
                    assert data["active_tests"][0]["test_name"] == "test_0"

    @pytest.mark.asyncio
    async def test_trigger_real_time_adaptation_success(
        self, client, mock_db, mock_user, mock_ui_profile, mock_ui_personalization_engine, auth_headers
    ):
        """Test successful real-time adaptation trigger"""
        mock_ui_personalization_engine.get_or_create_ui_profile.return_value = mock_ui_profile
        
        mock_adaptations = {
            "theme_adjustment": {
                "confidence": 0.85,
                "recommendation": "dark_mode"
            },
            "layout_optimization": {
                "confidence": 0.6,  # Below threshold
                "recommendation": "compact_layout"
            }
        }
        mock_ui_personalization_engine.generate_ui_personalizations.return_value = mock_adaptations
        
        context = {
            "page": "/profile",
            "device_type": "mobile",
            "time_of_day": "night"
        }
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.api.v1.routers.ui_personalization.ui_personalization_engine', mock_ui_personalization_engine):
                    response = client.post(
                        "/api/v1/ui-personalization/real-time-adaptation",
                        json=context,
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert data["success"] is True
                    assert data["adaptation_count"] == 1  # Only high-confidence adaptation
                    assert "theme_adjustment" in data["adaptations"]
                    assert "layout_optimization" not in data["adaptations"]

    def test_unauthorized_access(self, client):
        """Test unauthorized access to personalization endpoints"""
        endpoints = [
            ("/api/v1/ui-personalization/profile", "get"),
            ("/api/v1/ui-personalization/track-interaction", "post"),
            ("/api/v1/ui-personalization/generate-adaptations", "post"),
            ("/api/v1/ui-personalization/insights", "get"),
            ("/api/v1/ui-personalization/analytics", "get"),
            ("/api/v1/ui-personalization/preferences", "put"),
            ("/api/v1/ui-personalization/feedback", "post"),
            ("/api/v1/ui-personalization/ab-tests", "get"),
            ("/api/v1/ui-personalization/real-time-adaptation", "post")
        ]
        
        for endpoint, method in endpoints:
            if method == "get":
                response = client.get(endpoint)
            elif method == "post":
                response = client.post(endpoint, json={})
            elif method == "put":
                response = client.put(endpoint, json={})
            
            assert response.status_code in [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
                status.HTTP_422_UNPROCESSABLE_ENTITY  # Due to missing auth
            ]

    @pytest.mark.asyncio
    async def test_get_ui_analytics_custom_period(
        self, client, mock_db, mock_user, mock_ui_profile, mock_interactions, mock_ui_personalization_engine, auth_headers
    ):
        """Test UI analytics with custom analysis period"""
        mock_ui_personalization_engine.get_or_create_ui_profile.return_value = mock_ui_profile
        mock_db.query.return_value.filter.return_value.all.return_value = mock_interactions
        mock_ui_personalization_engine._analyze_user_behavior.return_value = {}
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.api.v1.routers.ui_personalization.ui_personalization_engine', mock_ui_personalization_engine):
                    with patch('app.api.v1.routers.ui_personalization.generate_analytics_recommendations', return_value=[]):
                        response = client.get(
                            "/api/v1/ui-personalization/analytics?days=90",
                            headers=auth_headers
                        )
                        
                        assert response.status_code == status.HTTP_200_OK
                        data = response.json()
                        assert data["analysis_period_days"] == 90

    def test_get_ui_analytics_invalid_days_parameter(self, client, auth_headers):
        """Test UI analytics with invalid days parameter"""
        with patch('app.api.v1.deps.get_current_user'):
            response = client.get(
                "/api/v1/ui-personalization/analytics?days=100",  # Above maximum
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_track_interaction_request_validation(self, client, auth_headers):
        """Test interaction tracking with invalid request data"""
        invalid_data = {
            "invalid_field": "value"
        }
        
        with patch('app.api.v1.deps.get_current_user'):
            response = client.post(
                "/api/v1/ui-personalization/track-interaction",
                json=invalid_data,
                headers=auth_headers
            )
            
            # Might pass validation depending on schema flexibility
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]

    @pytest.mark.asyncio
    async def test_generate_initial_insights_mobile_device(
        self, client, mock_db, mock_user, mock_ui_personalization_engine, auth_headers
    ):
        """Test initial insights generation for mobile device"""
        mobile_profile = Mock(spec=UserUIProfile)
        mobile_profile.id = 456
        mobile_profile.primary_device_type = "mobile"
        
        mock_ui_personalization_engine.get_or_create_ui_profile.return_value = mobile_profile
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.api.v1.routers.ui_personalization.ui_personalization_engine', mock_ui_personalization_engine):
                    with patch('app.api.v1.routers.ui_personalization.generate_initial_insights') as mock_gen:
                        mock_insights = [Mock()]
                        mock_insights[0].id = 1
                        mock_insights[0].insight_type = "device_optimization"
                        mock_insights[0].insight_category = "usability"
                        mock_insights[0].title = "Mobile-Optimized Experience"
                        mock_insights[0].description = "Mobile optimization"
                        mock_insights[0].recommended_action = "Use mobile features"
                        mock_insights[0].implementation_priority = "medium"
                        mock_insights[0].confidence_score = 0.8
                        mock_insights[0].expected_impact = 0.3
                        mock_insights[0].generated_at = datetime.utcnow()
                        mock_insights[0].acted_upon = False
                        mock_gen.return_value = mock_insights
                        
                        response = client.get(
                            "/api/v1/ui-personalization/insights",
                            headers=auth_headers
                        )
                        
                        assert response.status_code == status.HTTP_200_OK
                        data = response.json()
                        assert len(data) == 1
                        assert data[0]["insight_type"] == "device_optimization"

    @pytest.mark.asyncio
    async def test_ui_profile_accessibility_settings(
        self, client, mock_db, mock_user, mock_ui_personalization_engine, auth_headers
    ):
        """Test UI profile with accessibility settings enabled"""
        accessible_profile = Mock(spec=UserUIProfile)
        accessible_profile.id = 456
        accessible_profile.user_id = 123
        accessible_profile.primary_device_type = "desktop"
        accessible_profile.preferred_theme = "high_contrast"
        accessible_profile.font_size_preference = "large"
        accessible_profile.animation_preference = "disabled"
        accessible_profile.layout_density = "spacious"
        accessible_profile.interaction_speed = "slow"
        accessible_profile.navigation_pattern = "keyboard_focused"
        accessible_profile.personalization_score = 0.85
        accessible_profile.screen_reader_enabled = True
        accessible_profile.keyboard_navigation_primary = True
        accessible_profile.high_contrast_enabled = True
        accessible_profile.reduce_motion_enabled = True
        accessible_profile.updated_at = datetime.utcnow()
        accessible_profile.get_current_preferences.return_value = {
            "accessibility_mode": True,
            "high_contrast": True
        }
        
        mock_ui_personalization_engine.get_or_create_ui_profile.return_value = accessible_profile
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.api.v1.routers.ui_personalization.ui_personalization_engine', mock_ui_personalization_engine):
                    response = client.get(
                        "/api/v1/ui-personalization/profile",
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert data["accessibility_settings"]["screen_reader_enabled"] is True
                    assert data["accessibility_settings"]["keyboard_navigation_primary"] is True
                    assert data["accessibility_settings"]["high_contrast_enabled"] is True
                    assert data["accessibility_settings"]["reduce_motion_enabled"] is True

    @pytest.mark.asyncio
    async def test_error_logging_in_endpoints(
        self, client, mock_db, mock_user, mock_ui_personalization_engine, auth_headers
    ):
        """Test that errors are properly logged in personalization endpoints"""
        mock_ui_personalization_engine.get_or_create_ui_profile.side_effect = Exception("Test error")
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.api.v1.routers.ui_personalization.ui_personalization_engine', mock_ui_personalization_engine):
                    with patch('app.api.v1.routers.ui_personalization.logger') as mock_logger:
                        response = client.get(
                            "/api/v1/ui-personalization/profile",
                            headers=auth_headers
                        )
                        
                        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                        mock_logger.error.assert_called_once()
                        error_msg = mock_logger.error.call_args[0][0]
                        assert "Error retrieving UI profile" in error_msg

    @pytest.mark.asyncio
    async def test_insights_limit_parameter(
        self, client, mock_db, mock_user, mock_ui_profile, mock_ui_personalization_engine, auth_headers
    ):
        """Test personalization insights with limit parameter"""
        mock_ui_personalization_engine.get_or_create_ui_profile.return_value = mock_ui_profile
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.api.v1.routers.ui_personalization.ui_personalization_engine', mock_ui_personalization_engine):
                    with patch('app.api.v1.routers.ui_personalization.generate_initial_insights', return_value=[]):
                        response = client.get(
                            "/api/v1/ui-personalization/insights?limit=5",
                            headers=auth_headers
                        )
                        
                        assert response.status_code == status.HTTP_200_OK
                        # Verify limit was passed to query
                        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.assert_called_with(5)

    def test_insights_invalid_limit_parameter(self, client, auth_headers):
        """Test personalization insights with invalid limit parameter"""
        with patch('app.api.v1.deps.get_current_user'):
            response = client.get(
                "/api/v1/ui-personalization/insights?limit=100",  # Above maximum
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY