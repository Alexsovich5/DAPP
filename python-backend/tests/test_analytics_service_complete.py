import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from collections import defaultdict, Counter

from app.services.analytics_service import (
    AnalyticsService, 
    EngagementMetrics,
    ConnectionMetrics, 
    UserJourneyAnalytics,
    SystemHealthMetrics,
    analytics_service
)
from app.models.soul_analytics import AnalyticsEventType
from app.models.user import User
from app.models.soul_connection import SoulConnection
from app.models.daily_revelation import DailyRevelation
from app.models.message import Message


class TestAnalyticsService:
    
    @pytest.fixture
    def service(self):
        return AnalyticsService()
    
    @pytest.fixture
    def mock_db(self):
        mock_db = Mock()
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.rollback = Mock()
        mock_db.query = Mock()
        return mock_db
    
    @pytest.fixture
    def mock_user(self):
        user = Mock(spec=User)
        user.id = 123
        user.created_at = datetime.utcnow() - timedelta(days=10)
        user.emotional_onboarding_completed = True
        user.is_profile_complete = True
        user.total_swipes = 5
        user.total_messages_sent = 3
        user.total_revelations_shared = 2
        return user
    
    @pytest.fixture
    def sample_event_data(self):
        return {
            "device_type": "mobile",
            "browser_info": "Chrome/91.0",
            "timezone": "UTC",
            "country_code": "US",
            "emotional_state": "curious"
        }

    @pytest.mark.asyncio
    async def test_track_user_event_success(self, service, mock_db, mock_user, sample_event_data):
        """Test successful user event tracking"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = await service.track_user_event(
            user_id=123,
            event_type=AnalyticsEventType.PAGE_VIEW,
            event_data=sample_event_data,
            db=mock_db,
            session_id="session_123",
            connection_id=None
        )
        
        assert result is True
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_track_user_event_with_swipe_action(self, service, mock_db, mock_user, sample_event_data):
        """Test tracking swipe action event"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = await service.track_user_event(
            user_id=123,
            event_type=AnalyticsEventType.SWIPE_ACTION,
            event_data=sample_event_data,
            db=mock_db
        )
        
        assert result is True
        assert mock_user.total_swipes == 6  # Incremented from 5

    @pytest.mark.asyncio
    async def test_track_user_event_with_message_sent(self, service, mock_db, mock_user, sample_event_data):
        """Test tracking message sent event"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = await service.track_user_event(
            user_id=123,
            event_type=AnalyticsEventType.MESSAGE_SENT,
            event_data=sample_event_data,
            db=mock_db
        )
        
        assert result is True
        assert mock_user.total_messages_sent == 4  # Incremented from 3

    @pytest.mark.asyncio
    async def test_track_user_event_with_revelation_shared(self, service, mock_db, mock_user, sample_event_data):
        """Test tracking revelation shared event"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = await service.track_user_event(
            user_id=123,
            event_type=AnalyticsEventType.REVELATION_SHARED,
            event_data=sample_event_data,
            db=mock_db
        )
        
        assert result is True
        assert mock_user.total_revelations_shared == 3  # Incremented from 2

    @pytest.mark.asyncio
    async def test_track_user_event_with_connection(self, service, mock_db, mock_user, sample_event_data):
        """Test tracking event with connection_id"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        with patch.object(service, '_update_emotional_journey', new_callable=AsyncMock) as mock_update:
            result = await service.track_user_event(
                user_id=123,
                event_type=AnalyticsEventType.REVELATION_SHARED,
                event_data=sample_event_data,
                db=mock_db,
                connection_id=456
            )
            
            assert result is True
            mock_update.assert_called_once_with(
                123, 456, AnalyticsEventType.REVELATION_SHARED, sample_event_data, mock_db
            )

    @pytest.mark.asyncio
    async def test_track_user_event_error_handling(self, service, mock_db, sample_event_data):
        """Test error handling in user event tracking"""
        mock_db.add.side_effect = Exception("Database error")
        
        result = await service.track_user_event(
            user_id=123,
            event_type=AnalyticsEventType.PAGE_VIEW,
            event_data=sample_event_data,
            db=mock_db
        )
        
        assert result is False
        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_calculate_user_engagement_score(self, service, mock_db):
        """Test user engagement score calculation"""
        # Mock analytics events
        mock_events = []
        for i in range(10):
            event = Mock()
            event.created_at = datetime.utcnow() - timedelta(days=i)
            event.event_type = AnalyticsEventType.PAGE_VIEW.value
            mock_events.append(event)
        
        # Add some diverse events
        for event_type in [AnalyticsEventType.REVELATION_SHARED, AnalyticsEventType.MESSAGE_SENT]:
            event = Mock()
            event.created_at = datetime.utcnow() - timedelta(days=1)
            event.event_type = event_type.value
            mock_events.append(event)
        
        mock_db.query.return_value.filter.return_value.all.return_value = mock_events
        
        score = await service.calculate_user_engagement_score(123, mock_db)
        
        assert isinstance(score, float)
        assert 0 <= score <= 100

    @pytest.mark.asyncio
    async def test_calculate_user_engagement_score_no_events(self, service, mock_db):
        """Test engagement score with no events"""
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        score = await service.calculate_user_engagement_score(123, mock_db)
        
        assert score == 0.0

    @pytest.mark.asyncio
    async def test_calculate_user_engagement_score_error(self, service, mock_db):
        """Test engagement score calculation error handling"""
        mock_db.query.side_effect = Exception("Database error")
        
        score = await service.calculate_user_engagement_score(123, mock_db)
        
        assert score == 0.0

    @pytest.mark.asyncio
    async def test_get_user_journey_funnel(self, service, mock_db):
        """Test user journey funnel calculation"""
        # Mock query chain for different metrics
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        
        # Set up return values for different filter chains
        def setup_query_chain(count_value):
            chain = Mock()
            chain.filter.return_value = chain
            chain.count.return_value = count_value
            chain.distinct.return_value = chain
            return chain
        
        # Mock different query results
        mock_query.filter.side_effect = [
            setup_query_chain(100),  # total_users
            setup_query_chain(80),   # onboarded_users
            setup_query_chain(70),   # profile_complete_users
            setup_query_chain(60),   # first_swipe_users
            setup_query_chain(50),   # first_match_users
            setup_query_chain(40),   # first_message_users
            setup_query_chain(30),   # revelation_users
            setup_query_chain(20)    # photo_reveal_users
        ]
        
        result = await service.get_user_journey_funnel(mock_db, days=30)
        
        assert isinstance(result, UserJourneyAnalytics)
        assert result.onboarding_completion_rate == 80.0
        assert result.profile_completion_rate == 70.0
        assert result.first_swipe_rate == 60.0
        assert result.first_match_rate == 50.0
        assert result.first_message_rate == 40.0
        assert result.revelation_sharing_rate == 30.0
        assert result.photo_reveal_rate == 20.0

    @pytest.mark.asyncio
    async def test_get_user_journey_funnel_no_users(self, service, mock_db):
        """Test user journey funnel with no users"""
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        
        result = await service.get_user_journey_funnel(mock_db)
        
        assert isinstance(result, UserJourneyAnalytics)
        assert result.onboarding_completion_rate == 0
        assert result.profile_completion_rate == 0

    @pytest.mark.asyncio
    async def test_get_user_journey_funnel_error(self, service, mock_db):
        """Test user journey funnel error handling"""
        mock_db.query.side_effect = Exception("Database error")
        
        result = await service.get_user_journey_funnel(mock_db)
        
        assert isinstance(result, UserJourneyAnalytics)
        # Should return empty analytics
        assert result.onboarding_completion_rate == 0

    @pytest.mark.asyncio
    async def test_get_engagement_metrics(self, service, mock_db):
        """Test engagement metrics calculation"""
        # Mock retention rates calculation
        with patch.object(service, '_calculate_retention_rates', return_value={"day_1": 80.0, "day_7": 60.0, "day_30": 40.0}):
            # Mock query results
            mock_query = Mock()
            mock_db.query.return_value = mock_query
            
            # Set up distinct and count queries
            mock_query.filter.return_value.distinct.return_value.count.side_effect = [100, 200, 300]  # DAU, WAU, MAU
            mock_query.filter.return_value.count.return_value = 150  # total sessions
            mock_query.filter.return_value.group_by.return_value.having.return_value.count.return_value = 50  # single session users
            
            result = await service.get_engagement_metrics(mock_db)
            
            assert isinstance(result, EngagementMetrics)
            assert result.daily_active_users == 100
            assert result.weekly_active_users == 200
            assert result.monthly_active_users == 300
            assert result.total_sessions == 150
            assert result.bounce_rate == (50 / 300) * 100  # single_session / MAU
            assert result.retention_rates["day_1"] == 80.0

    @pytest.mark.asyncio
    async def test_get_engagement_metrics_error(self, service, mock_db):
        """Test engagement metrics error handling"""
        mock_db.query.side_effect = Exception("Database error")
        
        result = await service.get_engagement_metrics(mock_db)
        
        assert isinstance(result, EngagementMetrics)
        assert result.daily_active_users == 0

    @pytest.mark.asyncio
    async def test_get_connection_metrics(self, service, mock_db):
        """Test connection metrics calculation"""
        # Mock query results
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        
        # Setup different query chains
        mock_query.count.return_value = 100  # total connections
        mock_query.filter.return_value.count.side_effect = [50, 30, 20]  # active, revelations, photo reveals
        mock_query.filter.return_value.scalar.side_effect = [85.5, 2.5]  # avg compatibility, avg time to message
        
        result = await service.get_connection_metrics(mock_db)
        
        assert isinstance(result, ConnectionMetrics)
        assert result.total_connections == 100
        assert result.active_connections == 50
        assert result.completed_revelations == 30
        assert result.photo_reveals == 20
        assert result.average_compatibility_score == 85.5
        assert result.connection_success_rate == 20.0  # 20/100 * 100
        assert result.average_time_to_first_message == 2.5 / 3600  # Convert to hours

    @pytest.mark.asyncio
    async def test_get_connection_metrics_error(self, service, mock_db):
        """Test connection metrics error handling"""
        mock_db.query.side_effect = Exception("Database error")
        
        result = await service.get_connection_metrics(mock_db)
        
        assert isinstance(result, ConnectionMetrics)
        assert result.total_connections == 0

    @pytest.mark.asyncio
    async def test_get_system_health_metrics(self, service, mock_db):
        """Test system health metrics calculation"""
        # Mock performance metrics
        mock_metrics = []
        for i, (name, value) in enumerate([
            ("api_response_time_auth", 100),
            ("api_response_time_profile", 150),
            ("db_query_time", 50),
            ("error_rate_auth", 0.5),
            ("error_rate_matching", 0.2)
        ]):
            metric = Mock()
            metric.metric_name = name
            metric.metric_value = str(value)
            mock_metrics.append(metric)
        
        mock_db.query.return_value.filter.return_value.all.return_value = mock_metrics
        
        result = await service.get_system_health_metrics(mock_db)
        
        assert isinstance(result, SystemHealthMetrics)
        assert "api_response_time_auth" in result.api_response_times
        assert "db_query_time" in result.database_performance
        assert "error_rate_auth" in result.error_rates
        assert result.user_satisfaction_scores["overall_satisfaction"] == 4.2

    @pytest.mark.asyncio
    async def test_get_system_health_metrics_error(self, service, mock_db):
        """Test system health metrics error handling"""
        mock_db.query.side_effect = Exception("Database error")
        
        result = await service.get_system_health_metrics(mock_db)
        
        assert isinstance(result, SystemHealthMetrics)
        assert result.api_response_times == {}

    @pytest.mark.asyncio
    async def test_generate_user_insights(self, service, mock_db, mock_user):
        """Test user insights generation"""
        # Mock user query
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Mock events query
        mock_events = [Mock() for _ in range(5)]
        for i, event in enumerate(mock_events):
            event.created_at = datetime.utcnow() - timedelta(days=i)
            event.event_type = AnalyticsEventType.PAGE_VIEW.value
        
        mock_db.query.return_value.filter.return_value.all.return_value = mock_events
        
        # Mock connections query
        mock_connections = [Mock() for _ in range(3)]
        for i, conn in enumerate(mock_connections):
            conn.status = "active" if i < 2 else "inactive"
            conn.photo_revealed_at = datetime.utcnow() if i == 0 else None
        
        # Setup query side effects
        query_calls = [mock_events, mock_connections]
        mock_db.query.return_value.filter.side_effect = [
            Mock(return_value=Mock(all=lambda: query_calls[0])),
            Mock(return_value=query_calls[1])
        ]
        
        with patch.object(service, 'calculate_user_engagement_score', return_value=75.5):
            with patch.object(service, '_generate_user_recommendations', return_value=["rec1", "rec2"]):
                with patch.object(service, '_get_user_milestones', return_value=[]):
                    with patch.object(service, '_get_user_trends', return_value={"trend": "increasing"}):
                        result = await service.generate_user_insights(123, mock_db)
        
        assert "engagement" in result
        assert "connections" in result
        assert "recommendations" in result
        assert result["engagement"]["score"] == 75.5
        assert result["connections"]["total"] == 3
        assert result["connections"]["successful"] == 1
        assert result["connections"]["active"] == 2

    @pytest.mark.asyncio
    async def test_generate_user_insights_user_not_found(self, service, mock_db):
        """Test user insights when user not found"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = await service.generate_user_insights(123, mock_db)
        
        assert result == {}

    @pytest.mark.asyncio
    async def test_generate_user_insights_error(self, service, mock_db, mock_user):
        """Test user insights generation error handling"""
        mock_db.query.side_effect = Exception("Database error")
        
        result = await service.generate_user_insights(123, mock_db)
        
        assert result == {}

    @pytest.mark.asyncio
    async def test_track_system_performance(self, service, mock_db):
        """Test system performance tracking"""
        result = await service.track_system_performance(
            metric_name="api_response_time",
            value=125.5,
            component="auth",
            db=mock_db
        )
        
        assert result is True
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_track_system_performance_error(self, service, mock_db):
        """Test system performance tracking error handling"""
        mock_db.add.side_effect = Exception("Database error")
        
        result = await service.track_system_performance(
            metric_name="api_response_time",
            value=125.5,
            component="auth",
            db=mock_db
        )
        
        assert result is False
        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_retention_metrics_new_user(self, service, mock_db, mock_user):
        """Test updating retention metrics for new user"""
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_user,  # User query
            None        # Retention query (new record)
        ]
        
        result = await service.update_user_retention_metrics(123, mock_db)
        
        assert result is True
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_retention_metrics_existing_user(self, service, mock_db, mock_user):
        """Test updating retention metrics for existing user"""
        mock_retention = Mock()
        mock_retention.days_since_registration = 5
        mock_retention.is_active_day_1 = False
        mock_retention.is_active_day_7 = False
        mock_retention.is_active_day_30 = False
        
        # Mock activity query (has activity)
        mock_activity = Mock()
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_user,      # User query
            mock_retention, # Retention query
            mock_activity,  # Day 1 activity
            mock_activity,  # Day 7 activity
        ]
        
        # Mock connection queries
        mock_db.query.return_value.filter.side_effect = [
            Mock(return_value=Mock(first=lambda: Mock()))  # Has connections
        ]
        
        result = await service.update_user_retention_metrics(123, mock_db)
        
        assert result is True
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_retention_metrics_user_not_found(self, service, mock_db):
        """Test updating retention metrics when user not found"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = await service.update_user_retention_metrics(123, mock_db)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_update_user_retention_metrics_error(self, service, mock_db, mock_user):
        """Test retention metrics update error handling"""
        mock_db.query.side_effect = Exception("Database error")
        
        result = await service.update_user_retention_metrics(123, mock_db)
        
        assert result is False
        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_emotional_journey(self, service, mock_db):
        """Test emotional journey update"""
        # Mock existing journey
        mock_journey = Mock()
        mock_journey.interaction_count = 5
        mock_journey.haptic_triggers = 2
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_journey
        
        event_data = {"emotional_state": "excited"}
        
        await service._update_emotional_journey(
            123, 456, AnalyticsEventType.CONNECTION_INITIATED, event_data, mock_db
        )
        
        assert mock_journey.interaction_count == 6

    @pytest.mark.asyncio
    async def test_update_emotional_journey_new_record(self, service, mock_db):
        """Test emotional journey update with new record"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        event_data = {"emotional_state": "curious"}
        
        await service._update_emotional_journey(
            123, 456, AnalyticsEventType.REVELATION_SHARED, event_data, mock_db
        )
        
        mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_emotional_journey_haptic_feedback(self, service, mock_db):
        """Test emotional journey with haptic feedback event"""
        mock_journey = Mock()
        mock_journey.interaction_count = 0
        mock_journey.haptic_triggers = 0
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_journey
        
        await service._update_emotional_journey(
            123, 456, AnalyticsEventType.HAPTIC_FEEDBACK_TRIGGERED, {}, mock_db
        )
        
        assert mock_journey.haptic_triggers == 1

    @pytest.mark.asyncio
    async def test_update_emotional_journey_unmapped_event(self, service, mock_db):
        """Test emotional journey with unmapped event type"""
        await service._update_emotional_journey(
            123, 456, AnalyticsEventType.PAGE_VIEW, {}, mock_db
        )
        
        # Should not call database operations
        mock_db.query.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_emotional_journey_error(self, service, mock_db):
        """Test emotional journey update error handling"""
        mock_db.query.side_effect = Exception("Database error")
        
        # Should not raise exception
        await service._update_emotional_journey(
            123, 456, AnalyticsEventType.CONNECTION_INITIATED, {}, mock_db
        )

    @pytest.mark.asyncio
    async def test_calculate_retention_rates(self, service, mock_db):
        """Test retention rates calculation"""
        mock_retention_data = []
        for i in range(10):
            retention = Mock()
            retention.is_active_day_1 = i < 8
            retention.is_active_day_7 = i < 6
            retention.is_active_day_30 = i < 4
            mock_retention_data.append(retention)
        
        mock_db.query.return_value.all.return_value = mock_retention_data
        
        result = await service._calculate_retention_rates(mock_db)
        
        assert result["day_1"] == 80.0  # 8/10 * 100
        assert result["day_7"] == 60.0  # 6/10 * 100
        assert result["day_30"] == 40.0  # 4/10 * 100

    @pytest.mark.asyncio
    async def test_calculate_retention_rates_no_data(self, service, mock_db):
        """Test retention rates with no data"""
        mock_db.query.return_value.all.return_value = []
        
        result = await service._calculate_retention_rates(mock_db)
        
        assert result == {"day_1": 0.0, "day_7": 0.0, "day_30": 0.0}

    @pytest.mark.asyncio
    async def test_calculate_retention_rates_error(self, service, mock_db):
        """Test retention rates calculation error handling"""
        mock_db.query.side_effect = Exception("Database error")
        
        result = await service._calculate_retention_rates(mock_db)
        
        assert result == {"day_1": 0.0, "day_7": 0.0, "day_30": 0.0}

    def test_get_engagement_level(self, service):
        """Test engagement level determination"""
        assert service._get_engagement_level(90) == "High"
        assert service._get_engagement_level(70) == "Medium"
        assert service._get_engagement_level(50) == "Low"
        assert service._get_engagement_level(30) == "Very Low"

    def test_get_most_used_feature(self, service):
        """Test most used feature identification"""
        events = []
        for _ in range(3):
            event = Mock()
            event.event_type = AnalyticsEventType.PAGE_VIEW.value
            events.append(event)
        
        for _ in range(5):
            event = Mock()
            event.event_type = AnalyticsEventType.SWIPE_ACTION.value
            events.append(event)
        
        result = service._get_most_used_feature(events)
        
        assert result == AnalyticsEventType.SWIPE_ACTION.value

    def test_get_most_used_feature_no_events(self, service):
        """Test most used feature with no events"""
        result = service._get_most_used_feature([])
        
        assert result == "None"

    @pytest.mark.asyncio
    async def test_generate_user_recommendations_low_activity(self, service, mock_db):
        """Test recommendations for low activity user"""
        events = [Mock() for _ in range(5)]  # Less than 10 events
        connections = []
        
        recommendations = await service._generate_user_recommendations(123, events, connections, mock_db)
        
        assert "Try exploring more features" in recommendations[0]
        assert "Complete your profile" in recommendations[1]

    @pytest.mark.asyncio
    async def test_generate_user_recommendations_no_revelations(self, service, mock_db):
        """Test recommendations for user with no revelations"""
        events = []
        for _ in range(15):
            event = Mock()
            event.event_type = AnalyticsEventType.PAGE_VIEW.value
            events.append(event)
        
        connections = [Mock()]
        
        recommendations = await service._generate_user_recommendations(123, events, connections, mock_db)
        
        assert any("soul revelation" in rec for rec in recommendations)

    @pytest.mark.asyncio
    async def test_generate_user_recommendations_photo_reveal(self, service, mock_db):
        """Test recommendations for photo reveal"""
        events = []
        for _ in range(15):
            event = Mock()
            event.event_type = AnalyticsEventType.REVELATION_SHARED.value
            events.append(event)
        
        connections = []
        for _ in range(2):
            conn = Mock()
            conn.status = "active"
            conn.photo_revealed_at = None
            connections.append(conn)
        
        recommendations = await service._generate_user_recommendations(123, events, connections, mock_db)
        
        assert any("sharing photos" in rec for rec in recommendations)

    @pytest.mark.asyncio
    async def test_get_user_milestones(self, service, mock_db, mock_user):
        """Test user milestones retrieval"""
        mock_user.emotional_onboarding_completed = True
        mock_user.total_revelations_shared = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = await service._get_user_milestones(123, mock_db)
        
        assert len(result) == 2
        assert result[0]["type"] == "onboarding_complete"
        assert result[1]["type"] == "first_revelation"

    @pytest.mark.asyncio
    async def test_get_user_milestones_user_not_found(self, service, mock_db):
        """Test user milestones when user not found"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = await service._get_user_milestones(123, mock_db)
        
        assert result == []

    @pytest.mark.asyncio
    async def test_get_user_trends(self, service, mock_db):
        """Test user trends calculation"""
        # Mock weekly activity counts
        week_counts = [10, 8, 12, 15]  # Increasing trend
        mock_db.query.return_value.filter.return_value.count.side_effect = week_counts
        
        result = await service._get_user_trends(123, mock_db)
        
        assert result["weekly_activity"] == [15, 12, 8, 10]  # Reversed
        assert result["trend"] == "increasing"

    def test_global_service_instance(self):
        """Test global service instance"""
        assert analytics_service is not None
        assert isinstance(analytics_service, AnalyticsService)

    def test_dataclass_structures(self):
        """Test dataclass structures"""
        engagement = EngagementMetrics(
            daily_active_users=100,
            weekly_active_users=500,
            monthly_active_users=2000,
            average_session_duration=30.5,
            total_sessions=3000,
            bounce_rate=15.2,
            retention_rates={"day_1": 80.0}
        )
        
        assert engagement.daily_active_users == 100
        assert engagement.retention_rates["day_1"] == 80.0
        
        connection = ConnectionMetrics(
            total_connections=100,
            active_connections=80,
            completed_revelations=150,
            photo_reveals=60,
            average_compatibility_score=85.5,
            connection_success_rate=75.0,
            average_time_to_first_message=2.5
        )
        
        assert connection.total_connections == 100
        assert connection.average_compatibility_score == 85.5

    def test_empty_data_methods(self, service):
        """Test empty data methods"""
        empty_journey = service._empty_journey_analytics()
        assert empty_journey.onboarding_completion_rate == 0
        
        empty_engagement = service._empty_engagement_metrics()
        assert empty_engagement.daily_active_users == 0
        
        empty_connection = service._empty_connection_metrics()
        assert empty_connection.total_connections == 0
        
        empty_health = service._empty_system_health_metrics()
        assert empty_health.api_response_times == {}

    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test service initialization"""
        service = AnalyticsService()
        
        assert service.event_cache == {}
        assert service.batch_size == 100