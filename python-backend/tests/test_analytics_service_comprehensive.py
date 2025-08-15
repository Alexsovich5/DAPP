import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import json
import uuid
from dataclasses import asdict

from app.services.analytics import (
    AnalyticsService, 
    AnalyticsEvent, 
    EventType, 
    EventCategory,
    track_request_event
)


class TestAnalyticsService:
    
    @pytest.fixture
    def mock_clickhouse(self):
        mock_client = Mock()
        mock_client.execute = Mock()
        return mock_client
    
    @pytest.fixture 
    def mock_redis(self):
        mock_redis = Mock()
        mock_redis.xadd = Mock()
        mock_redis.lpush = Mock()
        mock_redis.ltrim = Mock()
        mock_redis.pipeline = Mock()
        mock_redis.hincrby = Mock()
        mock_redis.sadd = Mock()
        mock_redis.expire = Mock()
        mock_redis.hgetall = Mock()
        mock_redis.scard = Mock()
        
        # Mock pipeline
        mock_pipe = Mock()
        mock_pipe.hincrby = Mock()
        mock_pipe.sadd = Mock()
        mock_pipe.expire = Mock()
        mock_pipe.execute = Mock()
        mock_redis.pipeline.return_value = mock_pipe
        
        return mock_redis
    
    @pytest.fixture
    def analytics_service(self, mock_clickhouse, mock_redis):
        with patch('app.services.analytics.AnalyticsService._load_geoip_database') as mock_geoip:
            mock_geoip.return_value = None
            service = AnalyticsService(mock_clickhouse, mock_redis)
            return service
    
    @pytest.fixture
    def sample_event(self):
        return AnalyticsEvent(
            event_id=str(uuid.uuid4()),
            user_id=123,
            session_id="test_session_123",
            event_type=EventType.PAGE_VIEW,
            event_category=EventCategory.USER_BEHAVIOR,
            properties={"page_url": "/dashboard"},
            timestamp=datetime.utcnow(),
            page_url="/dashboard",
            referrer="https://google.com",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            ip_address="192.168.1.1"
        )

    @pytest.mark.asyncio
    async def test_track_event_success(self, analytics_service, sample_event, mock_clickhouse, mock_redis):
        """Test successful event tracking"""
        result = await analytics_service.track_event(sample_event)
        
        assert result is True
        mock_clickhouse.execute.assert_called_once()
        mock_redis.xadd.assert_called()
        mock_redis.lpush.assert_called()

    @pytest.mark.asyncio
    async def test_track_event_failure(self, analytics_service, sample_event, mock_clickhouse):
        """Test event tracking failure handling"""
        mock_clickhouse.execute.side_effect = Exception("Database error")
        
        result = await analytics_service.track_event(sample_event)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_enrich_event_with_user_agent(self, analytics_service, sample_event):
        """Test event enrichment with user agent parsing"""
        with patch('app.services.analytics.parse_user_agent') as mock_parse:
            mock_ua = Mock()
            mock_ua.is_mobile = False
            mock_ua.is_tablet = False
            mock_ua.is_pc = True
            mock_ua.browser.family = "Chrome"
            mock_ua.browser.version_string = "91.0"
            mock_ua.os.family = "Windows"
            mock_ua.os.version_string = "10"
            mock_parse.return_value = mock_ua
            
            enriched = await analytics_service._enrich_event(sample_event)
            
            assert enriched['device_type'] == 'desktop'
            assert enriched['browser'] == 'Chrome'
            assert enriched['os'] == 'Windows'

    @pytest.mark.asyncio
    async def test_enrich_event_with_geoip(self, mock_clickhouse, mock_redis, sample_event):
        """Test event enrichment with GeoIP data"""
        mock_geoip_reader = Mock()
        mock_response = Mock()
        mock_response.country.iso_code = "US"
        mock_response.city.name = "San Francisco"
        mock_response.location.latitude = 37.7749
        mock_response.location.longitude = -122.4194
        mock_geoip_reader.city.return_value = mock_response
        
        with patch('app.services.analytics.AnalyticsService._load_geoip_database') as mock_load:
            mock_load.return_value = mock_geoip_reader
            service = AnalyticsService(mock_clickhouse, mock_redis)
            
            enriched = await service._enrich_event(sample_event)
            
            assert enriched['country'] == 'US'
            assert enriched['city'] == 'San Francisco'
            assert enriched['latitude'] == 37.7749
            assert enriched['longitude'] == -122.4194

    def test_get_device_type_mobile(self, analytics_service):
        """Test device type detection for mobile"""
        mock_ua = Mock()
        mock_ua.is_mobile = True
        mock_ua.is_tablet = False
        mock_ua.is_pc = False
        
        device_type = analytics_service._get_device_type(mock_ua)
        assert device_type == 'mobile'

    def test_get_device_type_tablet(self, analytics_service):
        """Test device type detection for tablet"""
        mock_ua = Mock()
        mock_ua.is_mobile = False
        mock_ua.is_tablet = True
        mock_ua.is_pc = False
        
        device_type = analytics_service._get_device_type(mock_ua)
        assert device_type == 'tablet'

    def test_get_device_type_desktop(self, analytics_service):
        """Test device type detection for desktop"""
        mock_ua = Mock()
        mock_ua.is_mobile = False
        mock_ua.is_tablet = False
        mock_ua.is_pc = True
        
        device_type = analytics_service._get_device_type(mock_ua)
        assert device_type == 'desktop'

    def test_get_device_type_unknown(self, analytics_service):
        """Test device type detection for unknown"""
        mock_ua = Mock()
        mock_ua.is_mobile = False
        mock_ua.is_tablet = False
        mock_ua.is_pc = False
        
        device_type = analytics_service._get_device_type(mock_ua)
        assert device_type == 'unknown'

    @pytest.mark.asyncio
    async def test_store_event_clickhouse(self, analytics_service, mock_clickhouse):
        """Test storing event in ClickHouse"""
        event_data = {
            'event_id': 'test-id',
            'user_id': 123,
            'session_id': 'session-123',
            'event_type': EventType.PAGE_VIEW,
            'event_category': EventCategory.USER_BEHAVIOR,
            'page_url': '/test',
            'properties': {'key': 'value'},
            'timestamp': datetime.utcnow(),
            'date': datetime.utcnow().date()
        }
        
        await analytics_service._store_event_clickhouse(event_data)
        
        mock_clickhouse.execute.assert_called_once()
        args = mock_clickhouse.execute.call_args
        assert "INSERT INTO user_events VALUES" in args[0][0]

    @pytest.mark.asyncio
    async def test_store_event_redis(self, analytics_service, mock_redis):
        """Test storing event in Redis"""
        event_data = {
            'event_id': 'test-id',
            'event_category': EventCategory.USER_BEHAVIOR,
            'timestamp': datetime.utcnow()
        }
        
        await analytics_service._store_event_redis(event_data)
        
        mock_redis.xadd.assert_called_once()
        mock_redis.lpush.assert_called_once()
        mock_redis.ltrim.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_real_time_metrics(self, analytics_service, mock_redis):
        """Test updating real-time metrics"""
        event_data = {
            'event_type': 'page_view',
            'user_id': 123
        }
        
        await analytics_service._update_real_time_metrics(event_data)
        
        # Verify pipeline was used
        mock_redis.pipeline.assert_called_once()
        pipeline = mock_redis.pipeline.return_value
        pipeline.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_category_metrics_matching(self, analytics_service, mock_redis):
        """Test updating category-specific metrics for matching events"""
        pipe = mock_redis.pipeline.return_value
        event_data = {
            'event_type': 'profile_like',
            'properties': {}
        }
        
        await analytics_service._update_category_metrics(event_data, pipe, "2023-01-01-12", "2023-01-01")
        
        pipe.hincrby.assert_called()

    @pytest.mark.asyncio
    async def test_update_category_metrics_revenue(self, analytics_service, mock_redis):
        """Test updating category-specific metrics for revenue events"""
        pipe = mock_redis.pipeline.return_value
        event_data = {
            'event_type': 'purchase_made',
            'properties': {'amount_cents': 1000}
        }
        
        await analytics_service._update_category_metrics(event_data, pipe, "2023-01-01-12", "2023-01-01")
        
        # Verify revenue was tracked
        calls = pipe.hincrby.call_args_list
        revenue_calls = [call for call in calls if 'revenue_cents' in str(call)]
        assert len(revenue_calls) >= 2  # hourly and daily

    @pytest.mark.asyncio
    async def test_get_real_time_metrics(self, analytics_service, mock_redis):
        """Test retrieving real-time metrics"""
        # Mock Redis responses
        mock_redis.hgetall.return_value = {b'events:page_view': b'100', b'messages_sent': b'50'}
        mock_redis.scard.return_value = 25
        
        metrics = await analytics_service.get_real_time_metrics()
        
        assert 'timestamp' in metrics
        assert 'hourly' in metrics
        assert 'daily' in metrics
        assert metrics['hourly']['active_users'] == 25
        assert metrics['hourly']['metrics']['events:page_view'] == 100

    @pytest.mark.asyncio
    async def test_track_page_view(self, analytics_service, mock_clickhouse, mock_redis):
        """Test convenience method for tracking page views"""
        result = await analytics_service.track_page_view(
            user_id=123,
            session_id="session-123",
            page_url="/dashboard",
            referrer="https://google.com",
            user_agent="Mozilla/5.0...",
            ip_address="192.168.1.1"
        )
        
        assert result is True
        mock_clickhouse.execute.assert_called()

    @pytest.mark.asyncio
    async def test_track_profile_interaction(self, analytics_service, mock_clickhouse, mock_redis):
        """Test tracking profile interactions"""
        result = await analytics_service.track_profile_interaction(
            viewer_id=123,
            viewed_id=456,
            interaction_type="like",
            compatibility_score=0.85,
            session_id="session-123"
        )
        
        assert result is True
        # Verify both general event and specific profile interaction were stored
        assert mock_clickhouse.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_track_match_created(self, analytics_service, mock_clickhouse, mock_redis):
        """Test tracking match creation events"""
        result = await analytics_service.track_match_created(
            user1_id=123,
            user2_id=456,
            match_type="soul_connection",
            compatibility_score=0.92,
            algorithm_version="v2.0"
        )
        
        assert result is True
        assert mock_clickhouse.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_track_revelation_event(self, analytics_service, mock_clickhouse, mock_redis):
        """Test tracking revelation events"""
        result = await analytics_service.track_revelation_event(
            user_id=123,
            match_id=789,
            revelation_day=3,
            revelation_type="personal_value",
            content_length=250
        )
        
        assert result is True
        assert mock_clickhouse.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_get_user_journey_metrics(self, analytics_service, mock_clickhouse):
        """Test retrieving user journey metrics"""
        # Mock ClickHouse response
        mock_events = [
            ('page_view', 'user_behavior', '{}', datetime.utcnow(), datetime.utcnow().date()),
            ('profile_like', 'matching', '{}', datetime.utcnow(), datetime.utcnow().date())
        ]
        mock_clickhouse.execute.return_value = mock_events
        
        with patch.object(analytics_service, '_calculate_conversion_funnel', return_value={}):
            with patch.object(analytics_service, '_calculate_engagement_score', return_value=75.5):
                metrics = await analytics_service.get_user_journey_metrics(123)
        
        assert metrics['user_id'] == 123
        assert metrics['total_events'] == 2
        assert metrics['engagement_score'] == 75.5
        assert 'user_behavior' in metrics['event_categories']

    @pytest.mark.asyncio
    async def test_calculate_conversion_funnel(self, analytics_service, mock_clickhouse):
        """Test conversion funnel calculation"""
        # Mock ClickHouse responses for different funnel steps
        mock_clickhouse.execute.return_value = [(datetime.utcnow(),)]
        
        funnel = await analytics_service._calculate_conversion_funnel(123)
        
        # Verify all funnel steps are included
        expected_steps = [
            'register', 'onboarding_completed', 'first_profile_view',
            'first_like', 'first_match', 'first_message',
            'first_revelation', 'photo_revealed', 'subscription_started'
        ]
        
        for step in expected_steps:
            assert step in funnel

    @pytest.mark.asyncio
    async def test_calculate_engagement_score(self, analytics_service, mock_clickhouse):
        """Test engagement score calculation"""
        # Mock ClickHouse response: total_events, active_days, matching_events, messaging_events, revelation_events
        mock_clickhouse.execute.return_value = [(50, 5, 20, 15, 10)]
        
        score = await analytics_service._calculate_engagement_score(123)
        
        assert isinstance(score, float)
        assert 0 <= score <= 100

    @pytest.mark.asyncio
    async def test_calculate_engagement_score_no_data(self, analytics_service, mock_clickhouse):
        """Test engagement score calculation with no data"""
        mock_clickhouse.execute.return_value = []
        
        score = await analytics_service._calculate_engagement_score(123)
        
        assert score == 0.0

    @pytest.mark.asyncio
    async def test_store_profile_interaction_error_handling(self, analytics_service, mock_clickhouse):
        """Test error handling in profile interaction storage"""
        mock_clickhouse.execute.side_effect = Exception("Database error")
        
        # Should not raise exception, only log error
        await analytics_service._store_profile_interaction(123, 456, "like", 0.8, datetime.utcnow())

    @pytest.mark.asyncio
    async def test_store_matching_event_error_handling(self, analytics_service, mock_clickhouse):
        """Test error handling in matching event storage"""
        mock_clickhouse.execute.side_effect = Exception("Database error")
        
        # Should not raise exception, only log error
        await analytics_service._store_matching_event(123, 456, "soul_connection", 0.9, "v2.0")

    @pytest.mark.asyncio
    async def test_store_revelation_event_error_handling(self, analytics_service, mock_clickhouse):
        """Test error handling in revelation event storage"""
        mock_clickhouse.execute.side_effect = Exception("Database error")
        
        # Should not raise exception, only log error
        await analytics_service._store_revelation_event(123, 789, 3, "personal_value", 250)

    @pytest.mark.asyncio
    async def test_geoip_database_loading_failure(self, mock_clickhouse, mock_redis):
        """Test GeoIP database loading failure"""
        with patch('geoip2.database.Reader') as mock_reader:
            mock_reader.side_effect = Exception("File not found")
            
            service = AnalyticsService(mock_clickhouse, mock_redis)
            assert service.geoip_reader is None

    @pytest.mark.asyncio
    async def test_enrich_event_geoip_error(self, analytics_service, sample_event):
        """Test event enrichment with GeoIP error"""
        mock_geoip_reader = Mock()
        mock_geoip_reader.city.side_effect = Exception("IP not found")
        analytics_service.geoip_reader = mock_geoip_reader
        
        # Should not raise exception
        enriched = await analytics_service._enrich_event(sample_event)
        
        # Should have basic enrichment without location data
        assert 'date' in enriched
        assert 'hour' in enriched
        assert 'country' not in enriched

    @pytest.mark.asyncio
    async def test_track_request_event_helper(self, mock_clickhouse, mock_redis):
        """Test track_request_event helper function"""
        with patch('app.services.analytics.AnalyticsService._load_geoip_database'):
            analytics_service = AnalyticsService(mock_clickhouse, mock_redis)
            
            result = await track_request_event(
                user_id=123,
                session_id="session-123",
                request_path="/api/profiles",
                request_method="GET",
                analytics_service=analytics_service
            )
            
            assert result is True

    def test_event_type_enum_values(self):
        """Test EventType enum has expected values"""
        assert EventType.PAGE_VIEW.value == "page_view"
        assert EventType.PROFILE_LIKE.value == "profile_like"
        assert EventType.REVELATION_CREATED.value == "revelation_created"
        assert EventType.MATCH_CREATED.value == "match_created"

    def test_event_category_enum_values(self):
        """Test EventCategory enum has expected values"""
        assert EventCategory.USER_BEHAVIOR.value == "user_behavior"
        assert EventCategory.MATCHING.value == "matching"
        assert EventCategory.REVELATION.value == "revelation"
        assert EventCategory.SAFETY.value == "safety"

    def test_analytics_event_dataclass(self):
        """Test AnalyticsEvent dataclass structure"""
        event = AnalyticsEvent(
            event_id="test-id",
            user_id=123,
            session_id="session-123",
            event_type=EventType.PAGE_VIEW,
            event_category=EventCategory.USER_BEHAVIOR,
            properties={"key": "value"},
            timestamp=datetime.utcnow()
        )
        
        event_dict = asdict(event)
        assert event_dict['event_id'] == "test-id"
        assert event_dict['user_id'] == 123
        assert event_dict['properties']['key'] == "value"

    @pytest.mark.asyncio
    async def test_concurrent_event_tracking(self, analytics_service, mock_clickhouse, mock_redis):
        """Test concurrent event tracking"""
        events = []
        for i in range(5):
            event = AnalyticsEvent(
                event_id=str(uuid.uuid4()),
                user_id=i,
                session_id=f"session-{i}",
                event_type=EventType.PAGE_VIEW,
                event_category=EventCategory.USER_BEHAVIOR,
                properties={},
                timestamp=datetime.utcnow()
            )
            events.append(event)
        
        # Track all events concurrently
        tasks = [analytics_service.track_event(event) for event in events]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert all(results)
        assert mock_clickhouse.execute.call_count == 5

    @pytest.mark.asyncio
    async def test_real_time_metrics_error_handling(self, analytics_service, mock_redis):
        """Test real-time metrics error handling"""
        mock_redis.hgetall.side_effect = Exception("Redis error")
        
        metrics = await analytics_service.get_real_time_metrics()
        
        assert metrics == {}

    @pytest.mark.asyncio
    async def test_user_journey_metrics_error_handling(self, analytics_service, mock_clickhouse):
        """Test user journey metrics error handling"""
        mock_clickhouse.execute.side_effect = Exception("Database error")
        
        metrics = await analytics_service.get_user_journey_metrics(123)
        
        assert metrics == {}

    @pytest.mark.asyncio
    async def test_engagement_score_error_handling(self, analytics_service, mock_clickhouse):
        """Test engagement score calculation error handling"""
        mock_clickhouse.execute.side_effect = Exception("Database error")
        
        score = await analytics_service._calculate_engagement_score(123)
        
        assert score == 0.0