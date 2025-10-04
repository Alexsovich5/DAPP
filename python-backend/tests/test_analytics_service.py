#!/usr/bin/env python3
"""
Analytics Service Tests
Tests for user behavior analytics and insights generation
"""

import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from app.models.daily_revelation import DailyRevelation
from app.models.message import Message
from app.models.soul_connection import ConnectionStage, SoulConnection
from app.models.user import User
from app.services.analytics_service import AnalyticsEventType, AnalyticsService
from sqlalchemy.orm import Session


@pytest.fixture
def service():
    """Create analytics service instance"""
    return AnalyticsService()


@pytest.fixture
def mock_db():
    """Create mock database session"""
    db = Mock(spec=Session)
    db.query = Mock()
    db.add = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    return db


@pytest.fixture
def test_user():
    """Create test user"""
    user = Mock(spec=User)
    user.id = 1
    user.username = "testuser"
    user.created_at = datetime.now() - timedelta(days=30)
    user.last_login = datetime.now() - timedelta(hours=2)
    user.is_active = True
    return user


@pytest.fixture
def test_connection():
    """Create test connection"""
    connection = Mock(spec=SoulConnection)
    connection.id = 1
    connection.user1_id = 1
    connection.user2_id = 2
    connection.compatibility_score = 85.0
    connection.total_messages_exchanged = 150
    connection.connection_stage = ConnectionStage.DEEPER_CONNECTION
    connection.created_at = datetime.now() - timedelta(days=14)
    return connection


class TestAnalyticsServiceCore:
    """Test core analytics functionality"""

    @pytest.mark.asyncio
    async def test_track_user_event(self, service, mock_db):
        """Test tracking user event"""
        result = await service.track_user_event(
            user_id=1,
            event_type=AnalyticsEventType.LOGIN,
            event_data={"ip": "127.0.0.1", "device_type": "mobile"},
            db=mock_db,
        )

        assert isinstance(result, bool)
        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_get_engagement_metrics(self, service, test_user, mock_db):
        """Test getting engagement metrics"""
        # Mock various database queries that the method makes
        mock_db.query.return_value.filter.return_value.count.return_value = 5
        mock_db.query.return_value.scalar.return_value = 100

        # Mock the all() method to return an empty list for retention calculations
        mock_db.query.return_value.filter.return_value.all.return_value = []

        metrics = await service.get_engagement_metrics(db=mock_db)

        # The service returns an EngagementMetrics object, not a dict
        assert hasattr(metrics, "daily_active_users")
        assert hasattr(metrics, "weekly_active_users")
        assert hasattr(metrics, "monthly_active_users")

    @pytest.mark.asyncio
    async def test_calculate_user_engagement_score(self, service, mock_db):
        """Test calculating user engagement score"""
        # This method exists in the actual service
        score = await service.calculate_user_engagement_score(user_id=1, db=mock_db)

        assert isinstance(score, (int, float))
        assert 0 <= score <= 100

    @pytest.mark.asyncio
    async def test_get_connection_metrics(self, service, mock_db):
        """Test getting connection metrics"""
        # Mock connection data
        mock_db.query.return_value.filter.return_value.count.return_value = 10

        metrics = await service.get_connection_metrics(connection_id=1, db=mock_db)

        assert isinstance(metrics, dict)

    @pytest.mark.asyncio
    async def test_generate_connection_insights(
        self, service, test_connection, mock_db
    ):
        """Test generating connection insights"""
        mock_db.query.return_value.filter.return_value.first.return_value = (
            test_connection
        )
        mock_db.query.return_value.filter.return_value.count.return_value = 10

        insights = await service.generate_connection_insights(
            connection_id=1, db=mock_db
        )

        assert isinstance(insights, dict)
        assert "communication_frequency" in insights
        assert "engagement_trend" in insights
        assert "milestone_progress" in insights

    @pytest.mark.asyncio
    async def test_track_revelation_completion(self, service, mock_db):
        """Test tracking revelation completion rates"""
        mock_revelations = [Mock(spec=DailyRevelation) for _ in range(7)]
        mock_db.query.return_value.filter.return_value.all.return_value = (
            mock_revelations
        )

        completion_rate = await service.track_revelation_completion(
            connection_id=1, db=mock_db
        )

        assert isinstance(completion_rate, float)
        assert 0 <= completion_rate <= 100

    @pytest.mark.asyncio
    async def test_analyze_message_patterns(self, service, mock_db):
        """Test analyzing messaging patterns"""
        mock_messages = []
        for i in range(20):
            msg = Mock(spec=Message)
            msg.created_at = datetime.now() - timedelta(hours=i)
            msg.sender_id = 1 if i % 2 == 0 else 2
            msg.message_text = f"Test message {i}"
            mock_messages.append(msg)

        mock_db.query.return_value.filter.return_value.all.return_value = mock_messages

        patterns = await service.analyze_message_patterns(connection_id=1, db=mock_db)

        assert isinstance(patterns, dict)
        assert "average_response_time" in patterns
        assert "message_balance" in patterns
        assert "peak_activity_hours" in patterns

    @pytest.mark.asyncio
    async def test_calculate_user_retention(self, service, mock_db):
        """Test calculating user retention metrics"""
        # Mock users who logged in different periods
        mock_db.query.return_value.filter.return_value.count.side_effect = [
            100,
            85,
            70,
            60,
        ]

        retention = await service.calculate_user_retention(
            cohort_date=datetime.now() - timedelta(days=30), db=mock_db
        )

        assert isinstance(retention, dict)
        assert "day_1" in retention
        assert "day_7" in retention
        assert "day_30" in retention
        assert all(0 <= v <= 100 for v in retention.values())

    @pytest.mark.asyncio
    async def test_generate_user_journey_map(self, service, test_user, mock_db):
        """Test generating user journey map"""
        mock_db.query.return_value.filter.return_value.first.return_value = test_user

        # Mock various activities
        mock_activities = [
            {"type": "registration", "timestamp": datetime.now() - timedelta(days=30)},
            {
                "type": "profile_completion",
                "timestamp": datetime.now() - timedelta(days=29),
            },
            {"type": "first_match", "timestamp": datetime.now() - timedelta(days=25)},
            {"type": "first_message", "timestamp": datetime.now() - timedelta(days=24)},
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = (
            mock_activities
        )

        journey = await service.generate_user_journey_map(user_id=1, db=mock_db)

        assert isinstance(journey, list)
        assert len(journey) > 0
        assert all("type" in event and "timestamp" in event for event in journey)

    @pytest.mark.asyncio
    async def test_identify_power_users(self, service, mock_db):
        """Test identifying power users"""
        mock_users = []
        for i in range(10):
            user = Mock(spec=User)
            user.id = i + 1
            user.total_connections = 10 + i
            user.messages_sent = 100 + (i * 20)
            mock_users.append(user)

        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_users[
            :5
        ]

        power_users = await service.identify_power_users(limit=5, db=mock_db)

        assert len(power_users) == 5
        assert all("user_id" in u and "engagement_score" in u for u in power_users)

    @pytest.mark.asyncio
    async def test_calculate_conversion_funnel(self, service, mock_db):
        """Test calculating conversion funnel metrics"""
        # Mock funnel stages
        mock_db.query.return_value.count.return_value = 1000  # Total registrations
        mock_db.query.return_value.filter.side_effect = [
            Mock(count=Mock(return_value=800)),  # Completed profile
            Mock(count=Mock(return_value=600)),  # First match
            Mock(count=Mock(return_value=400)),  # First message
            Mock(count=Mock(return_value=200)),  # Photo reveal
        ]

        funnel = await service.calculate_conversion_funnel(db=mock_db)

        assert isinstance(funnel, dict)
        assert "registration" in funnel
        assert "profile_completion" in funnel
        assert "first_match" in funnel
        assert funnel["registration"] == 100  # 100% baseline

    @pytest.mark.asyncio
    async def test_predict_churn_risk(self, service, test_user, mock_db):
        """Test predicting user churn risk"""
        mock_db.query.return_value.filter.return_value.first.return_value = test_user

        # Mock low activity indicators
        mock_db.query.return_value.filter.return_value.count.return_value = (
            2  # Few logins
        )

        risk = await service.predict_churn_risk(user_id=1, db=mock_db)

        assert isinstance(risk, dict)
        assert "risk_score" in risk
        assert "risk_level" in risk
        assert 0 <= risk["risk_score"] <= 100
        assert risk["risk_level"] in ["low", "medium", "high"]

    @pytest.mark.asyncio
    async def test_generate_weekly_report(self, service, mock_db):
        """Test generating weekly analytics report"""
        # Mock various metrics
        mock_db.query.return_value.filter.return_value.count.side_effect = [
            100,
            50,
            200,
            150,
        ]
        mock_db.query.return_value.filter.return_value.scalar.return_value = 85.5

        report = await service.generate_weekly_report(db=mock_db)

        assert isinstance(report, dict)
        assert "new_users" in report
        assert "active_connections" in report
        assert "average_compatibility" in report
        assert "total_messages" in report
        assert "week_over_week_growth" in report


class TestAnalyticsServiceSegmentation:
    """Test user segmentation and cohort analysis"""

    @pytest.mark.asyncio
    async def test_segment_users_by_behavior(self, service, mock_db):
        """Test segmenting users by behavior patterns"""
        mock_users = []
        for i in range(20):
            user = Mock(spec=User)
            user.id = i + 1
            user.activity_level = "high" if i < 5 else "medium" if i < 15 else "low"
            mock_users.append(user)

        mock_db.query.return_value.all.return_value = mock_users

        segments = await service.segment_users_by_behavior(db=mock_db)

        assert isinstance(segments, dict)
        assert "high_engagement" in segments
        assert "medium_engagement" in segments
        assert "low_engagement" in segments

    @pytest.mark.asyncio
    async def test_cohort_analysis(self, service, mock_db):
        """Test cohort analysis"""
        cohort_date = datetime.now() - timedelta(days=30)

        # Mock cohort data
        mock_db.query.return_value.filter.return_value.count.side_effect = [100, 85, 70]

        analysis = await service.perform_cohort_analysis(
            cohort_date=cohort_date, metric="retention", db=mock_db
        )

        assert isinstance(analysis, dict)
        assert "cohort_size" in analysis
        assert "retention_curve" in analysis

    @pytest.mark.asyncio
    async def test_identify_user_personas(self, service, mock_db):
        """Test identifying user personas"""
        mock_profiles = []
        for i in range(30):
            profile = Mock()
            profile.user_id = i + 1
            profile.interests = ["music", "travel"] if i < 10 else ["sports", "gaming"]
            profile.communication_style = "deep" if i < 15 else "casual"
            mock_profiles.append(profile)

        mock_db.query.return_value.all.return_value = mock_profiles

        personas = await service.identify_user_personas(db=mock_db)

        assert isinstance(personas, list)
        assert len(personas) > 0
        assert all("persona_name" in p and "characteristics" in p for p in personas)


class TestAnalyticsServicePerformance:
    """Test performance analytics"""

    @pytest.mark.asyncio
    async def test_calculate_response_times(self, service, mock_db):
        """Test calculating system response times"""
        mock_logs = []
        for i in range(100):
            log = Mock()
            log.endpoint = f"/api/endpoint{i % 5}"
            log.response_time_ms = 50 + (i % 50)
            mock_logs.append(log)

        mock_db.query.return_value.filter.return_value.all.return_value = mock_logs

        response_times = await service.calculate_response_times(
            time_period="24h", db=mock_db
        )

        assert isinstance(response_times, dict)
        assert "average" in response_times
        assert "p95" in response_times
        assert "p99" in response_times

    @pytest.mark.asyncio
    async def test_monitor_error_rates(self, service, mock_db):
        """Test monitoring error rates"""
        mock_db.query.return_value.filter.return_value.count.side_effect = [
            1000,
            50,
        ]  # Total requests, errors

        error_rate = await service.monitor_error_rates(time_period="1h", db=mock_db)

        assert isinstance(error_rate, dict)
        assert "error_percentage" in error_rate
        assert "total_errors" in error_rate
        assert error_rate["error_percentage"] == 5.0


class TestAnalyticsServiceExport:
    """Test data export functionality"""

    @pytest.mark.asyncio
    async def test_export_user_data(self, service, test_user, mock_db):
        """Test exporting user data"""
        mock_db.query.return_value.filter.return_value.first.return_value = test_user

        export = await service.export_user_data(user_id=1, format="json", db=mock_db)

        assert isinstance(export, str)
        data = json.loads(export)
        assert "user_id" in data
        assert "username" in data

    @pytest.mark.asyncio
    async def test_generate_csv_report(self, service, mock_db):
        """Test generating CSV report"""
        mock_data = [
            {"date": "2024-01-01", "users": 100, "connections": 50},
            {"date": "2024-01-02", "users": 110, "connections": 55},
        ]

        with patch.object(service, "_get_report_data", return_value=mock_data):
            csv_content = await service.generate_csv_report(
                report_type="daily_metrics", db=mock_db
            )

        assert isinstance(csv_content, str)
        assert "date,users,connections" in csv_content


class TestAnalyticsServiceErrorHandling:
    """Test error handling"""

    @pytest.mark.asyncio
    async def test_handle_database_error(self, service, mock_db):
        """Test handling database errors"""
        mock_db.query.side_effect = Exception("Database connection error")

        with pytest.raises(Exception, match="Database connection error"):
            await service.get_user_engagement_metrics(user_id=1, days=30, db=mock_db)

    @pytest.mark.asyncio
    async def test_handle_invalid_date_range(self, service, mock_db):
        """Test handling invalid date ranges"""
        with pytest.raises(ValueError, match="Invalid date range"):
            await service.calculate_metrics_for_period(
                start_date=datetime.now(),
                end_date=datetime.now() - timedelta(days=1),
                db=mock_db,
            )

    @pytest.mark.asyncio
    async def test_handle_missing_user(self, service, mock_db):
        """Test handling missing user data"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = await service.get_user_engagement_metrics(
            user_id=999, days=30, db=mock_db
        )

        assert result is None or result == {}
