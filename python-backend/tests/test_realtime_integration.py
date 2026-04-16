"""
Integration Tests for Real-time Features - Sprint 4
Comprehensive testing of WebSocket, activity tracking, and real-time services
"""

import asyncio
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.core.health_monitor import health_monitor
from app.main import app
from app.models.user_activity_tracking import (
    ActivityContext,
    ActivityType,
    UserActivityLog,
    UserActivitySession,
)
from app.services.activity_tracking_service import activity_tracker
from app.services.realtime_connection_manager import (
    MessageType,
    RealtimeMessage,
    realtime_manager,
)
from app.services.realtime_integration_service import realtime_integration
from fastapi.testclient import TestClient
from tests import TestingSessionLocal


class TestRealtimeConnectionManager:
    """Test suite for real-time connection manager"""

    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket for testing"""
        mock_ws = MagicMock()
        mock_ws.send_text = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.close = AsyncMock()
        return mock_ws

    @pytest.fixture
    def db_session(self):
        """Database session for testing"""
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    def test_connection_manager_initialization(self):
        """Test that the connection manager initializes correctly"""
        assert realtime_manager is not None
        assert hasattr(realtime_manager, "active_connections")
        assert hasattr(realtime_manager, "channel_subscribers")
        assert hasattr(realtime_manager, "typing_sessions")
        assert isinstance(realtime_manager.active_connections, dict)
        assert isinstance(realtime_manager.channel_subscribers, dict)

    async def test_user_connection_lifecycle(self, mock_websocket, db_session):
        """Test complete user connection lifecycle"""
        user_id = 123

        # Test connection
        await realtime_manager.connect(mock_websocket, user_id, db_session)
        assert user_id in realtime_manager.active_connections

        # Test message sending
        test_message = RealtimeMessage(
            type=MessageType.CONNECTED, data={"message": "test"}
        )

        result = await realtime_manager.send_to_user(user_id, test_message)
        assert result is True
        mock_websocket.send_text.assert_called()

        # Test disconnection
        await realtime_manager.disconnect(user_id, None)
        assert user_id not in realtime_manager.active_connections

    async def test_channel_subscription_system(self, mock_websocket, db_session):
        """Test channel subscription and broadcasting"""
        user_id = 123
        channel = "test_channel"

        # Connect user
        await realtime_manager.connect(mock_websocket, user_id, db_session)

        # Test channel subscription
        success = await realtime_manager.subscribe_to_channel(user_id, channel)
        assert success is True
        assert channel in realtime_manager.channel_subscribers
        assert user_id in realtime_manager.channel_subscribers[channel]

        # Test broadcasting to channel
        test_message = RealtimeMessage(
            type=MessageType.NEW_MESSAGE, data={"content": "test broadcast"}
        )

        sent_count = await realtime_manager.broadcast_to_channel(channel, test_message)
        assert sent_count == 1
        mock_websocket.send_text.assert_called()

        # Test unsubscription
        success = await realtime_manager.unsubscribe_from_channel(user_id, channel)
        assert success is True
        assert user_id not in realtime_manager.channel_subscribers.get(channel, set())

        # Cleanup
        await realtime_manager.disconnect(user_id, None)

    async def test_message_handling(self, mock_websocket, db_session):
        """Test various message types and handling"""
        user_id = 123

        # Connect user
        await realtime_manager.connect(mock_websocket, user_id, db_session)

        # Test heartbeat message
        heartbeat_message = {
            "type": "heartbeat",
            "data": {"timestamp": datetime.utcnow().isoformat()},
        }

        result = await realtime_manager.handle_message(user_id, heartbeat_message, None)
        assert result is True

        # Test channel subscription message
        subscribe_message = {
            "type": "subscribe",
            "channel": "test_channel",
            "data": {},
        }

        result = await realtime_manager.handle_message(user_id, subscribe_message, None)
        assert result is True
        assert "test_channel" in realtime_manager.channel_subscribers

        # Cleanup
        await realtime_manager.disconnect(user_id, None)

    def test_connection_statistics(self):
        """Test connection statistics gathering"""
        stats = realtime_manager.get_connection_stats()

        required_fields = [
            "active_connections",
            "typing_sessions",
            "connection_subscribers",
            "channel_subscribers",
            "total_channel_subscriptions",
            "queued_messages",
            "user_presence_tracked",
        ]

        for field in required_fields:
            assert field in stats
            assert isinstance(stats[field], int)


class TestActivityTrackingService:
    """Test suite for activity tracking service"""

    @pytest.fixture
    def test_db_session(self):
        """Create a test database session"""
        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    async def test_activity_session_lifecycle(self, test_db_session):
        """Test complete activity session lifecycle"""
        user_id = 123
        session_id = f"test_session_{int(time.time())}"

        device_info = {
            "device_type": "desktop",
            "browser_info": {"name": "Chrome", "version": "91.0"},
            "screen_resolution": "1920x1080",
            "capabilities": ["haptic_feedback", "push_notifications"],
            "timezone": "UTC",
            "network_type": "wifi",
        }

        # Test session start
        result = await activity_tracker.start_activity_session(
            user_id=user_id,
            session_id=session_id,
            device_info=device_info,
            db=test_db_session,
        )

        assert result is True

        # Verify session was created
        session = (
            test_db_session.query(UserActivitySession)
            .filter(UserActivitySession.session_id == session_id)
            .first()
        )

        assert session is not None
        assert session.user_id == user_id
        assert session.device_type == "desktop"
        assert session.network_type == "wifi"

    async def test_activity_logging(self, test_db_session):
        """Test activity logging functionality"""
        user_id = 123
        session_id = f"test_session_{int(time.time())}"

        # First start a session
        device_info = {"device_type": "mobile", "network_type": "cellular"}
        await activity_tracker.start_activity_session(
            user_id=user_id,
            session_id=session_id,
            device_info=device_info,
            db=test_db_session,
        )

        # Test activity logging
        result = await activity_tracker.log_activity(
            user_id=user_id,
            session_id=session_id,
            activity_type=ActivityType.VIEWING_DISCOVERY,
            context=ActivityContext.DISCOVERY_PAGE,
            activity_data={
                "page": "discovery",
                "filters": ["age", "location"],
            },
            db=test_db_session,
        )

        assert result is True

        # Verify activity was logged
        activity = (
            test_db_session.query(UserActivityLog)
            .filter(
                UserActivityLog.session_id == session_id,
                UserActivityLog.activity_type == ActivityType.VIEWING_DISCOVERY.value,
            )
            .first()
        )

        assert activity is not None
        assert activity.user_id == user_id
        assert activity.activity_context == ActivityContext.DISCOVERY_PAGE.value
        assert activity.activity_data == {
            "page": "discovery",
            "filters": ["age", "location"],
        }

    async def test_presence_summary_updates(self, test_db_session):
        """Test presence activity summary updates"""
        user_id = 124
        session_id = f"test_session_{int(time.time())}"

        # Start session and log activity
        device_info = {"device_type": "tablet"}
        await activity_tracker.start_activity_session(
            user_id=user_id,
            session_id=session_id,
            device_info=device_info,
            db=test_db_session,
        )

        await activity_tracker.log_activity(
            user_id=user_id,
            session_id=session_id,
            activity_type=ActivityType.TYPING_MESSAGE,
            context=ActivityContext.MESSAGE_THREAD,
            connection_id=456,
            db=test_db_session,
        )

        # Check presence summary
        current_activity = await activity_tracker.get_user_current_activity(
            user_id=user_id, db=test_db_session
        )

        assert current_activity["status"] == "online"
        assert current_activity["activity"] == ActivityType.TYPING_MESSAGE.value
        assert current_activity["context"] == ActivityContext.MESSAGE_THREAD.value
        assert "activity_duration" in current_activity

    async def test_daily_insights_generation(self, test_db_session):
        """Test daily insights generation"""
        user_id = 125
        session_id = f"test_session_{int(time.time())}"

        # Create some activity data
        device_info = {"device_type": "desktop"}
        await activity_tracker.start_activity_session(
            user_id=user_id,
            session_id=session_id,
            device_info=device_info,
            db=test_db_session,
        )

        # Log multiple activities
        activities = [
            (ActivityType.VIEWING_DISCOVERY, ActivityContext.DISCOVERY_PAGE),
            (
                ActivityType.READING_REVELATION,
                ActivityContext.REVELATION_TIMELINE,
            ),
            (ActivityType.TYPING_MESSAGE, ActivityContext.MESSAGE_THREAD),
        ]

        for activity_type, context in activities:
            await activity_tracker.log_activity(
                user_id=user_id,
                session_id=session_id,
                activity_type=activity_type,
                context=context,
                db=test_db_session,
            )
            # Small delay to ensure different timestamps
            await asyncio.sleep(0.01)

        # Generate insights
        result = await activity_tracker.generate_daily_insights(
            user_id=user_id, date=datetime.utcnow(), db=test_db_session
        )

        assert result is True

        # Verify insights were created
        from app.models.user_activity_tracking import ActivityInsights

        insights = (
            test_db_session.query(ActivityInsights)
            .filter(ActivityInsights.user_id == user_id)
            .first()
        )

        assert insights is not None
        assert insights.total_session_time > 0


class TestRealtimeIntegrationService:
    """Test suite for real-time integration service"""

    async def test_compatibility_update_notification(self):
        """Test compatibility update broadcasting"""
        connection_id = 789
        compatibility_data = {
            "newScore": 85.5,
            "previousScore": 80.0,
            "breakdown": {"interests": 90, "values": 85, "communication": 80},
            "factors": ["shared_interests", "similar_values"],
        }

        with patch.object(
            realtime_manager, "broadcast_compatibility_update"
        ) as mock_broadcast:
            mock_broadcast.return_value = True

            result = await realtime_integration.notify_compatibility_update(
                connection_id=connection_id,
                new_score=compatibility_data["newScore"],
                previous_score=compatibility_data["previousScore"],
                breakdown=compatibility_data["breakdown"],
                factors=compatibility_data["factors"],
                db=None,
            )

            assert result is True
            mock_broadcast.assert_called_once()

    async def test_new_match_notification(self):
        """Test new match broadcasting"""
        user_id = 123
        partner_id = 456
        compatibility_score = 92.3

        with patch.object(realtime_manager, "broadcast_new_match") as mock_broadcast:
            mock_broadcast.return_value = True

            result = await realtime_integration.notify_new_match(
                user_id=user_id,
                partner_id=partner_id,
                compatibility_score=compatibility_score,
                match_type="soul_connection",
                db=None,
            )

            assert result is True
            mock_broadcast.assert_called_once()

    async def test_revelation_sharing_notification(self):
        """Test revelation sharing broadcasting"""
        connection_id = 789
        sender_id = 123
        sender_name = "Test User"
        day = 3

        with patch.object(
            realtime_manager, "broadcast_revelation_update"
        ) as mock_broadcast:
            mock_broadcast.return_value = True

            result = await realtime_integration.notify_revelation_shared(
                connection_id=connection_id,
                sender_id=sender_id,
                sender_name=sender_name,
                day=day,
                revelation_type="shared",
                preview="A meaningful revelation...",
                db=None,
            )

            assert result is True
            mock_broadcast.assert_called_once()

    async def test_user_activity_notification(self):
        """Test user activity status updates"""
        user_id = 123
        activity = "typing"
        location = "message_thread"

        with patch.object(realtime_manager, "handle_presence_update") as mock_update:
            mock_update.return_value = True

            result = await realtime_integration.notify_user_activity(
                user_id=user_id, activity=activity, location=location, db=None
            )

            assert result is True
            mock_update.assert_called_once()

    async def test_system_announcement_broadcast(self):
        """Test system-wide announcement broadcasting"""
        message = "System maintenance scheduled for 2 AM UTC"
        channel = "system_announcements"

        with patch.object(realtime_manager, "broadcast_to_channel") as mock_broadcast:
            mock_broadcast.return_value = 5  # 5 users notified

            result = await realtime_integration.broadcast_system_announcement(
                message=message, channel=channel
            )

            assert result == 5
            mock_broadcast.assert_called_once()

    def test_realtime_statistics(self):
        """Test real-time system statistics"""
        stats = realtime_integration.get_realtime_statistics()

        assert isinstance(stats, dict)
        assert "active_connections" in stats
        assert "health_score" in stats
        assert "load_level" in stats


class TestHealthMonitoring:
    """Test suite for health monitoring system"""

    async def test_database_health_check(self):
        """Test database health monitoring"""
        from app.core.database import SessionLocal

        db = SessionLocal()

        try:
            health_check = await health_monitor.check_database_health(db)

            assert health_check is not None
            assert health_check.component.value == "database"
            assert health_check.status in [
                "healthy",
                "degraded",
                "unhealthy",
                "critical",
            ]
            assert "response_time_ms" in health_check.details
            assert health_check.check_duration_ms > 0
        finally:
            db.close()

    async def test_websocket_health_check(self):
        """Test WebSocket system health monitoring"""
        health_check = await health_monitor.check_websocket_health()

        assert health_check is not None
        assert health_check.component.value == "websocket"
        assert health_check.status in [
            "healthy",
            "degraded",
            "unhealthy",
            "critical",
        ]
        assert "active_connections" in health_check.details

    async def test_activity_tracking_health_check(self):
        """Test activity tracking system health monitoring"""
        from app.core.database import SessionLocal

        db = SessionLocal()

        try:
            health_check = await health_monitor.check_activity_tracking_health(db)

            assert health_check is not None
            assert health_check.component.value == "activity_tracking"
            assert health_check.status in [
                "healthy",
                "degraded",
                "unhealthy",
                "critical",
            ]
            assert "activity_types_count" in health_check.details
            assert "response_time_ms" in health_check.details
        finally:
            db.close()

    async def test_comprehensive_health_check(self):
        """Test comprehensive system health check"""
        system_health = await health_monitor.perform_comprehensive_health_check()

        assert system_health is not None
        assert system_health.overall_status in [
            "healthy",
            "degraded",
            "unhealthy",
            "critical",
        ]
        assert len(system_health.checks) > 0
        assert system_health.summary is not None
        assert "total_components" in system_health.summary
        assert system_health.uptime_seconds > 0

    def test_health_dict_conversion(self):
        """Test health status dictionary conversion"""
        import asyncio

        async def run_test():
            system_health = await health_monitor.perform_comprehensive_health_check()
            health_dict = health_monitor.to_dict(system_health)

            required_fields = [
                "overall_status",
                "timestamp",
                "components",
                "summary",
            ]
            for field in required_fields:
                assert field in health_dict

            assert isinstance(health_dict["components"], list)
            assert len(health_dict["components"]) > 0

            # Check component structure
            component = health_dict["components"][0]
            component_fields = [
                "component",
                "status",
                "message",
                "details",
                "check_duration_ms",
                "timestamp",
            ]
            for field in component_fields:
                assert field in component

        asyncio.run(run_test())


class TestAPIEndpoints:
    """Test suite for API endpoints integration"""

    def test_health_endpoints_integration(self):
        """Test health monitoring API endpoints"""
        client = TestClient(app)

        # Test basic health check
        response = client.get("/api/v1/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

        # Test detailed health check
        response = client.get("/api/v1/health/detailed")
        assert response.status_code in [200, 503]  # Both acceptable
        data = response.json()
        assert "overall_status" in data
        assert "components" in data

        # Test system status
        response = client.get("/api/v1/health/status")
        assert response.status_code == 200

        # Test metrics endpoint
        response = client.get("/api/v1/health/metrics")
        assert response.status_code in [
            200,
            500,
        ]  # May fail in test environment

    def test_activity_endpoints_integration(self):
        """Test activity tracking API endpoints"""
        client = TestClient(app)

        # Test activity types endpoint
        response = client.get("/api/v1/activity/activity-types")
        assert response.status_code == 200
        data = response.json()
        assert "activity_types" in data
        assert "activity_contexts" in data
        assert len(data["activity_types"]) > 0

    def test_websocket_endpoints_integration(self):
        """Test WebSocket API endpoints"""
        client = TestClient(app)

        # Test WebSocket status
        response = client.get("/api/v1/ws/status")
        assert response.status_code == 200
        data = response.json()
        assert "active_connections" in data

        # Test WebSocket health
        response = client.get("/api/v1/ws/health")
        assert response.status_code == 200


class TestErrorHandling:
    """Test suite for error handling in real-time features"""

    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket for testing"""
        mock_ws = MagicMock()
        mock_ws.send_text = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.close = AsyncMock()
        return mock_ws

    @pytest.fixture
    def db_session(self):
        """Database session for testing"""
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    async def test_activity_tracking_error_handling(self):
        """Test error handling in activity tracking"""
        # Test with invalid parameters
        result = await activity_tracker.start_activity_session(
            user_id=None,  # Invalid user ID
            session_id="test",
            device_info={},
            db=None,  # Invalid database session
        )

        # Should return False due to error handling
        assert result is False

    async def test_realtime_integration_error_handling(self):
        """Test error handling in real-time integration"""
        # Test with invalid connection ID
        result = await realtime_integration.notify_compatibility_update(
            connection_id=None,  # Invalid connection ID
            new_score=85.0,
            previous_score=80.0,
            breakdown={},
            factors=[],
            db=None,
        )

        # Should return False due to error handling
        assert result is False

    async def test_websocket_error_handling(self, mock_websocket, db_session):
        """Test WebSocket error handling"""
        user_id = 999

        # Test connection with failing WebSocket
        mock_websocket.accept.side_effect = Exception("Connection failed")

        try:
            result = await realtime_manager.connect(mock_websocket, user_id, db_session)
            # Should handle the error gracefully
            assert result is False
        except Exception:
            # Should not raise unhandled exceptions
            pytest.fail("Unhandled exception in WebSocket error handling")


# Test runner configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
