import pytest
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.main import app
from app.models.user import User


class TestAnalyticsRouter:
    
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
        user.is_admin = False
        return user
    
    @pytest.fixture
    def mock_admin_user(self):
        admin = Mock(spec=User)
        admin.id = 456
        admin.email = "admin@example.com"
        admin.username = "admin"
        admin.is_admin = True
        return admin
    
    @pytest.fixture
    def mock_analytics_service(self):
        service = AsyncMock()
        service.get_real_time_metrics = AsyncMock()
        service.get_user_journey_metrics = AsyncMock()
        service.get_business_metrics = AsyncMock()
        service.get_matching_analytics = AsyncMock()
        service.track_event = AsyncMock()
        service.get_a_b_test_results = AsyncMock()
        service.track_a_b_test_event = AsyncMock()
        service.export_user_data = AsyncMock()
        service.delete_user_data = AsyncMock()
        return service
    
    @pytest.fixture
    def auth_headers(self):
        return {"Authorization": "Bearer fake_token"}
    
    @pytest.fixture
    def mock_realtime_metrics(self):
        return {
            "timestamp": datetime.utcnow(),
            "hourly": {
                "active_users": 150,
                "new_registrations": 12,
                "matches_created": 45,
                "messages_sent": 230
            },
            "daily": {
                "active_users": 890,
                "new_registrations": 78,
                "matches_created": 234,
                "messages_sent": 1520
            }
        }
    
    @pytest.fixture
    def mock_user_journey(self):
        return {
            "user_id": 123,
            "total_events": 45,
            "first_seen": datetime.utcnow() - timedelta(days=30),
            "last_seen": datetime.utcnow() - timedelta(hours=2),
            "days_active": 15,
            "event_categories": {
                "profile_view": 10,
                "match_action": 8,
                "message_sent": 15,
                "photo_reveal": 3
            },
            "conversion_funnel": {
                "registration": datetime.utcnow() - timedelta(days=30),
                "first_match": datetime.utcnow() - timedelta(days=25),
                "first_message": datetime.utcnow() - timedelta(days=22),
                "photo_reveal": datetime.utcnow() - timedelta(days=10)
            },
            "engagement_score": 0.78
        }
    
    @pytest.fixture
    def mock_business_metrics(self):
        return {
            "period": "daily",
            "active_users": 890,
            "new_registrations": 78,
            "matches_created": 234,
            "conversations_started": 156,
            "photo_reveals": 45,
            "revenue_cents": 450000,
            "engagement_rate": 0.72
        }
    
    @pytest.fixture
    def mock_matching_analytics(self):
        return {
            "period": "daily",
            "total_interactions": 1250,
            "like_rate": 0.65,
            "match_rate": 0.32,
            "conversation_rate": 0.78,
            "avg_compatibility_score": 0.76,
            "algorithm_performance": {
                "precision": 0.82,
                "recall": 0.74,
                "f1_score": 0.78
            }
        }
    
    @pytest.fixture
    def mock_ab_test_results(self):
        return {
            "experiment_id": "revelation_timing_v2",
            "variants": [
                {
                    "variant": "control",
                    "participants": 500,
                    "conversion_rate": 0.15,
                    "confidence_interval": [0.12, 0.18]
                },
                {
                    "variant": "optimized_timing",
                    "participants": 500,
                    "conversion_rate": 0.22,
                    "confidence_interval": [0.19, 0.25]
                }
            ],
            "statistical_significance": True,
            "confidence_level": 0.95,
            "recommendation": "deploy_optimized_timing"
        }

    @pytest.mark.asyncio
    async def test_get_realtime_metrics_success(
        self, client, mock_analytics_service, mock_admin_user, mock_realtime_metrics, auth_headers
    ):
        """Test successful real-time metrics retrieval"""
        mock_analytics_service.get_real_time_metrics.return_value = mock_realtime_metrics
        
        with patch('app.api.v1.deps.get_current_admin_user', return_value=mock_admin_user):
            with patch('app.api.v1.routers.analytics.get_analytics_service', return_value=mock_analytics_service):
                response = client.get(
                    "/api/v1/analytics/metrics/realtime",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["hourly"]["active_users"] == 150
                assert data["daily"]["active_users"] == 890

    def test_get_realtime_metrics_admin_required(self, client, mock_user, auth_headers):
        """Test real-time metrics access denied for non-admin"""
        with patch('app.api.v1.deps.get_current_admin_user') as mock_admin:
            mock_admin.side_effect = Exception("Admin required")
            
            response = client.get(
                "/api/v1/analytics/metrics/realtime",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @pytest.mark.asyncio
    async def test_get_realtime_metrics_no_data(
        self, client, mock_analytics_service, mock_admin_user, auth_headers
    ):
        """Test real-time metrics when no data available"""
        mock_analytics_service.get_real_time_metrics.return_value = None
        
        with patch('app.api.v1.deps.get_current_admin_user', return_value=mock_admin_user):
            with patch('app.api.v1.routers.analytics.get_analytics_service', return_value=mock_analytics_service):
                response = client.get(
                    "/api/v1/analytics/metrics/realtime",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_404_NOT_FOUND
                assert "No metrics available" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_realtime_metrics_service_error(
        self, client, mock_analytics_service, mock_admin_user, auth_headers
    ):
        """Test real-time metrics with service error"""
        mock_analytics_service.get_real_time_metrics.side_effect = Exception("Service error")
        
        with patch('app.api.v1.deps.get_current_admin_user', return_value=mock_admin_user):
            with patch('app.api.v1.routers.analytics.get_analytics_service', return_value=mock_analytics_service):
                response = client.get(
                    "/api/v1/analytics/metrics/realtime",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                assert "Failed to retrieve metrics" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_user_journey_admin_success(
        self, client, mock_analytics_service, mock_admin_user, mock_user_journey, auth_headers
    ):
        """Test successful admin user journey retrieval"""
        target_user_id = 789
        mock_analytics_service.get_user_journey_metrics.return_value = mock_user_journey
        
        with patch('app.api.v1.deps.get_current_admin_user', return_value=mock_admin_user):
            with patch('app.api.v1.routers.analytics.get_analytics_service', return_value=mock_analytics_service):
                response = client.get(
                    f"/api/v1/analytics/user-journey/{target_user_id}",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["user_id"] == 123
                assert data["total_events"] == 45
                assert data["engagement_score"] == 0.78

    @pytest.mark.asyncio
    async def test_get_user_journey_admin_not_found(
        self, client, mock_analytics_service, mock_admin_user, auth_headers
    ):
        """Test admin user journey retrieval for non-existent user"""
        target_user_id = 999
        mock_analytics_service.get_user_journey_metrics.return_value = None
        
        with patch('app.api.v1.deps.get_current_admin_user', return_value=mock_admin_user):
            with patch('app.api.v1.routers.analytics.get_analytics_service', return_value=mock_analytics_service):
                response = client.get(
                    f"/api/v1/analytics/user-journey/{target_user_id}",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_404_NOT_FOUND
                assert "User journey data not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_my_journey_success(
        self, client, mock_analytics_service, mock_user, mock_user_journey, auth_headers
    ):
        """Test successful user's own journey retrieval"""
        mock_analytics_service.get_user_journey_metrics.return_value = mock_user_journey
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.analytics.get_analytics_service', return_value=mock_analytics_service):
                response = client.get(
                    "/api/v1/analytics/user-journey/me",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["user_id"] == 123
                assert data["total_events"] == 45

    @pytest.mark.asyncio
    async def test_get_my_journey_no_data(
        self, client, mock_analytics_service, mock_user, auth_headers
    ):
        """Test user's own journey when no data exists"""
        mock_analytics_service.get_user_journey_metrics.return_value = None
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.analytics.get_analytics_service', return_value=mock_analytics_service):
                response = client.get(
                    "/api/v1/analytics/user-journey/me",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["user_id"] == 123
                assert data["total_events"] == 0
                assert data["engagement_score"] == 0.0

    @pytest.mark.asyncio
    async def test_get_business_metrics_default_period(
        self, client, mock_analytics_service, mock_admin_user, mock_business_metrics, auth_headers
    ):
        """Test business metrics with default daily period"""
        mock_analytics_service.get_business_metrics.return_value = mock_business_metrics
        
        with patch('app.api.v1.deps.get_current_admin_user', return_value=mock_admin_user):
            with patch('app.api.v1.routers.analytics.get_analytics_service', return_value=mock_analytics_service):
                response = client.get(
                    "/api/v1/analytics/business-metrics",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["period"] == "daily"
                assert data["active_users"] == 890
                assert data["revenue_cents"] == 450000

    @pytest.mark.asyncio
    async def test_get_business_metrics_custom_period(
        self, client, mock_analytics_service, mock_admin_user, auth_headers
    ):
        """Test business metrics with custom weekly period"""
        weekly_metrics = {
            "period": "weekly",
            "active_users": 2500,
            "new_registrations": 180,
            "matches_created": 890,
            "conversations_started": 567,
            "photo_reveals": 234,
            "revenue_cents": 1250000,
            "engagement_rate": 0.68
        }
        mock_analytics_service.get_business_metrics.return_value = weekly_metrics
        
        with patch('app.api.v1.deps.get_current_admin_user', return_value=mock_admin_user):
            with patch('app.api.v1.routers.analytics.get_analytics_service', return_value=mock_analytics_service):
                response = client.get(
                    "/api/v1/analytics/business-metrics?period=weekly",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["period"] == "weekly"
                assert data["active_users"] == 2500

    def test_get_business_metrics_invalid_period(self, client, mock_admin_user, auth_headers):
        """Test business metrics with invalid period parameter"""
        with patch('app.api.v1.deps.get_current_admin_user', return_value=mock_admin_user):
            response = client.get(
                "/api/v1/analytics/business-metrics?period=invalid",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_get_business_metrics_with_date_range(
        self, client, mock_analytics_service, mock_admin_user, mock_business_metrics, auth_headers
    ):
        """Test business metrics with custom date range"""
        mock_analytics_service.get_business_metrics.return_value = mock_business_metrics
        
        start_date = "2024-01-01T00:00:00Z"
        end_date = "2024-01-07T23:59:59Z"
        
        with patch('app.api.v1.deps.get_current_admin_user', return_value=mock_admin_user):
            with patch('app.api.v1.routers.analytics.get_analytics_service', return_value=mock_analytics_service):
                response = client.get(
                    f"/api/v1/analytics/business-metrics?start_date={start_date}&end_date={end_date}",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_get_matching_analytics_success(
        self, client, mock_analytics_service, mock_admin_user, mock_matching_analytics, auth_headers
    ):
        """Test successful matching analytics retrieval"""
        mock_analytics_service.get_matching_analytics.return_value = mock_matching_analytics
        
        with patch('app.api.v1.deps.get_current_admin_user', return_value=mock_admin_user):
            with patch('app.api.v1.routers.analytics.get_analytics_service', return_value=mock_analytics_service):
                response = client.get(
                    "/api/v1/analytics/matching-analytics",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["like_rate"] == 0.65
                assert data["match_rate"] == 0.32
                assert data["algorithm_performance"]["precision"] == 0.82

    @pytest.mark.asyncio
    async def test_track_custom_event_success(
        self, client, mock_analytics_service, mock_user, auth_headers
    ):
        """Test successful custom event tracking"""
        mock_analytics_service.track_event.return_value = True
        
        event_data = {
            "event_type": "profile_view",
            "event_category": "user_interaction",
            "properties": {
                "viewed_user_id": 456,
                "viewing_duration_seconds": 30
            }
        }
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.analytics.get_analytics_service', return_value=mock_analytics_service):
                response = client.post(
                    "/api/v1/analytics/track-event",
                    json=event_data,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["status"] == "success"
                assert "Event tracked successfully" in data["message"]

    @pytest.mark.asyncio
    async def test_track_custom_event_invalid_type(
        self, client, mock_analytics_service, mock_user, auth_headers
    ):
        """Test custom event tracking with invalid event type"""
        mock_analytics_service.track_event.return_value = True
        
        event_data = {
            "event_type": "invalid_event_type",
            "event_category": "user_interaction",
            "properties": {}
        }
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.analytics.get_analytics_service', return_value=mock_analytics_service):
                with patch('app.api.v1.routers.analytics.EventType') as mock_event_type:
                    mock_event_type.side_effect = ValueError("Invalid event type")
                    
                    response = client.post(
                        "/api/v1/analytics/track-event",
                        json=event_data,
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_400_BAD_REQUEST
                    assert "Invalid event type" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_track_custom_event_service_failure(
        self, client, mock_analytics_service, mock_user, auth_headers
    ):
        """Test custom event tracking with service failure"""
        mock_analytics_service.track_event.return_value = False
        
        event_data = {
            "event_type": "profile_view",
            "event_category": "user_interaction",
            "properties": {}
        }
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.analytics.get_analytics_service', return_value=mock_analytics_service):
                response = client.post(
                    "/api/v1/analytics/track-event",
                    json=event_data,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                assert "Failed to track event" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_ab_test_results_success(
        self, client, mock_analytics_service, mock_admin_user, mock_ab_test_results, auth_headers
    ):
        """Test successful A/B test results retrieval"""
        experiment_id = "revelation_timing_v2"
        mock_analytics_service.get_a_b_test_results.return_value = mock_ab_test_results
        
        with patch('app.api.v1.deps.get_current_admin_user', return_value=mock_admin_user):
            with patch('app.api.v1.routers.analytics.get_analytics_service', return_value=mock_analytics_service):
                response = client.get(
                    f"/api/v1/analytics/a-b-tests/{experiment_id}",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["experiment_id"] == experiment_id
                assert data["statistical_significance"] is True
                assert len(data["variants"]) == 2

    @pytest.mark.asyncio
    async def test_get_ab_test_results_not_found(
        self, client, mock_analytics_service, mock_admin_user, auth_headers
    ):
        """Test A/B test results for non-existent experiment"""
        experiment_id = "non_existent_test"
        mock_analytics_service.get_a_b_test_results.return_value = None
        
        with patch('app.api.v1.deps.get_current_admin_user', return_value=mock_admin_user):
            with patch('app.api.v1.routers.analytics.get_analytics_service', return_value=mock_analytics_service):
                response = client.get(
                    f"/api/v1/analytics/a-b-tests/{experiment_id}",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_404_NOT_FOUND
                assert "A/B test not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_track_ab_test_event_success(
        self, client, mock_analytics_service, mock_user, auth_headers
    ):
        """Test successful A/B test event tracking"""
        mock_analytics_service.track_a_b_test_event.return_value = True
        
        test_data = {
            "experiment_id": "revelation_timing_v2",
            "variant": "optimized_timing",
            "event_type": "conversion",
            "metric_value": 1.0
        }
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.analytics.get_analytics_service', return_value=mock_analytics_service):
                response = client.post(
                    "/api/v1/analytics/a-b-tests/track",
                    json=test_data,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["status"] == "success"
                assert "A/B test event tracked" in data["message"]

    @pytest.mark.asyncio
    async def test_track_ab_test_event_failure(
        self, client, mock_analytics_service, mock_user, auth_headers
    ):
        """Test A/B test event tracking failure"""
        mock_analytics_service.track_a_b_test_event.return_value = False
        
        test_data = {
            "experiment_id": "revelation_timing_v2",
            "variant": "control",
            "event_type": "conversion",
            "metric_value": 0.0
        }
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.analytics.get_analytics_service', return_value=mock_analytics_service):
                response = client.post(
                    "/api/v1/analytics/a-b-tests/track",
                    json=test_data,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                assert "Failed to track A/B test event" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_export_user_analytics_data_success(
        self, client, mock_analytics_service, mock_admin_user, auth_headers
    ):
        """Test successful user analytics data export"""
        user_id = 789
        export_data = {
            "events": [
                {"type": "profile_view", "timestamp": "2024-01-01T10:00:00Z"},
                {"type": "match_action", "timestamp": "2024-01-01T11:00:00Z"}
            ],
            "metrics": {
                "total_events": 2,
                "engagement_score": 0.75
            }
        }
        mock_analytics_service.export_user_data.return_value = export_data
        
        with patch('app.api.v1.deps.get_current_admin_user', return_value=mock_admin_user):
            with patch('app.api.v1.routers.analytics.get_analytics_service', return_value=mock_analytics_service):
                response = client.get(
                    f"/api/v1/analytics/export/user-data/{user_id}",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["user_id"] == user_id
                assert "export_timestamp" in data
                assert data["data"] == export_data

    @pytest.mark.asyncio
    async def test_delete_user_analytics_data_success(
        self, client, mock_analytics_service, mock_admin_user, auth_headers
    ):
        """Test successful user analytics data deletion"""
        user_id = 789
        mock_analytics_service.delete_user_data.return_value = True
        
        with patch('app.api.v1.deps.get_current_admin_user', return_value=mock_admin_user):
            with patch('app.api.v1.routers.analytics.get_analytics_service', return_value=mock_analytics_service):
                response = client.delete(
                    f"/api/v1/analytics/user-data/{user_id}",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["status"] == "success"
                assert f"Analytics data deleted for user {user_id}" in data["message"]

    @pytest.mark.asyncio
    async def test_delete_user_analytics_data_failure(
        self, client, mock_analytics_service, mock_admin_user, auth_headers
    ):
        """Test user analytics data deletion failure"""
        user_id = 789
        mock_analytics_service.delete_user_data.return_value = False
        
        with patch('app.api.v1.deps.get_current_admin_user', return_value=mock_admin_user):
            with patch('app.api.v1.routers.analytics.get_analytics_service', return_value=mock_analytics_service):
                response = client.delete(
                    f"/api/v1/analytics/user-data/{user_id}",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                assert "Failed to delete user data" in response.json()["detail"]

    def test_analytics_health_check_success(self, client):
        """Test successful analytics health check"""
        response = client.get("/api/v1/analytics/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "services" in data
        assert data["services"]["clickhouse"] == "connected"
        assert data["services"]["redis"] == "connected"

    def test_analytics_health_check_failure(self, client):
        """Test analytics health check failure"""
        with patch('app.api.v1.routers.analytics.logger') as mock_logger:
            # Simulate health check failure by raising exception
            with patch('app.api.v1.routers.analytics.datetime') as mock_datetime:
                mock_datetime.utcnow.side_effect = Exception("Health check failed")
                
                response = client.get("/api/v1/analytics/health")
                
                assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
                assert "Analytics service unhealthy" in response.json()["detail"]
                mock_logger.error.assert_called_once()

    def test_unauthorized_access_to_admin_endpoints(self, client, auth_headers):
        """Test unauthorized access to admin-only endpoints"""
        admin_endpoints = [
            "/api/v1/analytics/metrics/realtime",
            "/api/v1/analytics/user-journey/123",
            "/api/v1/analytics/business-metrics",
            "/api/v1/analytics/matching-analytics",
            "/api/v1/analytics/a-b-tests/test_id",
            "/api/v1/analytics/export/user-data/123"
        ]
        
        for endpoint in admin_endpoints:
            response = client.get(endpoint, headers=auth_headers)
            # Should fail due to admin requirement
            assert response.status_code in [
                status.HTTP_401_UNAUTHORIZED, 
                status.HTTP_403_FORBIDDEN,
                status.HTTP_500_INTERNAL_SERVER_ERROR  # If get_current_admin_user raises exception
            ]

    @pytest.mark.asyncio
    async def test_analytics_service_dependency_error(self, client, mock_admin_user, auth_headers):
        """Test analytics service dependency not configured"""
        with patch('app.api.v1.deps.get_current_admin_user', return_value=mock_admin_user):
            # Don't patch get_analytics_service - let it raise the 503 error
            response = client.get(
                "/api/v1/analytics/metrics/realtime",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            assert "Analytics service not configured" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_track_event_with_custom_user_id(
        self, client, mock_analytics_service, mock_user, auth_headers
    ):
        """Test event tracking with custom user ID"""
        mock_analytics_service.track_event.return_value = True
        
        event_data = {
            "event_type": "profile_view",
            "event_category": "user_interaction",
            "user_id": 999,  # Different from current user
            "properties": {"custom_field": "value"}
        }
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.analytics.get_analytics_service', return_value=mock_analytics_service):
                response = client.post(
                    "/api/v1/analytics/track-event",
                    json=event_data,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_business_metrics_date_calculations(
        self, client, mock_analytics_service, mock_admin_user, mock_business_metrics, auth_headers
    ):
        """Test business metrics default date range calculations"""
        mock_analytics_service.get_business_metrics.return_value = mock_business_metrics
        
        test_cases = [
            ("daily", 1),
            ("weekly", 7),
            ("monthly", 30)
        ]
        
        for period, expected_days in test_cases:
            with patch('app.api.v1.deps.get_current_admin_user', return_value=mock_admin_user):
                with patch('app.api.v1.routers.analytics.get_analytics_service', return_value=mock_analytics_service):
                    response = client.get(
                        f"/api/v1/analytics/business-metrics?period={period}",
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK

    def test_request_validation_errors(self, client, mock_user, auth_headers):
        """Test request validation for various endpoints"""
        invalid_requests = [
            # Invalid event tracking data
            {
                "endpoint": "/api/v1/analytics/track-event",
                "method": "post",
                "data": {"invalid": "data"}
            },
            # Invalid A/B test tracking data
            {
                "endpoint": "/api/v1/analytics/a-b-tests/track",
                "method": "post",
                "data": {"incomplete": "data"}
            }
        ]
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            for req in invalid_requests:
                if req["method"] == "post":
                    response = client.post(req["endpoint"], json=req["data"], headers=auth_headers)
                else:
                    response = client.get(req["endpoint"], headers=auth_headers)
                
                assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_logging_in_analytics_endpoints(
        self, client, mock_analytics_service, mock_admin_user, auth_headers
    ):
        """Test that errors are properly logged in analytics endpoints"""
        mock_analytics_service.get_real_time_metrics.side_effect = Exception("Test error")
        
        with patch('app.api.v1.deps.get_current_admin_user', return_value=mock_admin_user):
            with patch('app.api.v1.routers.analytics.get_analytics_service', return_value=mock_analytics_service):
                with patch('app.api.v1.routers.analytics.logger') as mock_logger:
                    response = client.get(
                        "/api/v1/analytics/metrics/realtime",
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                    mock_logger.error.assert_called_once()
                    error_msg = mock_logger.error.call_args[0][0]
                    assert "Failed to get real-time metrics" in error_msg

    @pytest.mark.asyncio
    async def test_user_journey_edge_cases(
        self, client, mock_analytics_service, mock_user, auth_headers
    ):
        """Test user journey endpoint edge cases"""
        # Test with user who has extensive activity
        extensive_journey = {
            "user_id": 123,
            "total_events": 1000,
            "first_seen": datetime.utcnow() - timedelta(days=365),
            "last_seen": datetime.utcnow(),
            "days_active": 200,
            "event_categories": {
                "profile_view": 300,
                "match_action": 150,
                "message_sent": 400,
                "photo_reveal": 50,
                "premium_feature": 100
            },
            "conversion_funnel": {
                "registration": datetime.utcnow() - timedelta(days=365),
                "first_match": datetime.utcnow() - timedelta(days=350),
                "first_message": datetime.utcnow() - timedelta(days=340),
                "photo_reveal": datetime.utcnow() - timedelta(days=300),
                "premium_subscription": datetime.utcnow() - timedelta(days=200)
            },
            "engagement_score": 0.95
        }
        
        mock_analytics_service.get_user_journey_metrics.return_value = extensive_journey
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.analytics.get_analytics_service', return_value=mock_analytics_service):
                response = client.get(
                    "/api/v1/analytics/user-journey/me",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["total_events"] == 1000
                assert data["days_active"] == 200
                assert data["engagement_score"] == 0.95

    @pytest.mark.asyncio
    async def test_business_metrics_response_completeness(
        self, client, mock_analytics_service, mock_admin_user, auth_headers
    ):
        """Test business metrics response includes all required fields"""
        complete_metrics = {
            "period": "daily",
            "active_users": 890,
            "new_registrations": 78,
            "matches_created": 234,
            "conversations_started": 156,
            "photo_reveals": 45,
            "revenue_cents": 450000,
            "engagement_rate": 0.72
        }
        mock_analytics_service.get_business_metrics.return_value = complete_metrics
        
        with patch('app.api.v1.deps.get_current_admin_user', return_value=mock_admin_user):
            with patch('app.api.v1.routers.analytics.get_analytics_service', return_value=mock_analytics_service):
                response = client.get(
                    "/api/v1/analytics/business-metrics",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                
                # Verify all required fields are present
                required_fields = [
                    "period", "active_users", "new_registrations", 
                    "matches_created", "conversations_started", "photo_reveals",
                    "revenue_cents", "engagement_rate"
                ]
                for field in required_fields:
                    assert field in data
                    assert data[field] is not None