"""
User Safety Service Tests - High-impact coverage for safety features
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from app.services.user_safety_simplified import (
    UserSafetyService,
    SafetyStatus,
    ReportCategory,
)
from app.models.user import User


class TestUserSafetyService:
    """Test user safety service functionality"""

    def test_service_initialization(self):
        """Test safety service initializes correctly"""
        db_mock = Mock()
        service = UserSafetyService(db_mock)
        
        assert service.db == db_mock
        assert hasattr(service, 'report_user')
        assert hasattr(service, 'block_user')

    def test_report_categories_enum(self):
        """Test that report categories are properly defined"""
        categories = [
            ReportCategory.HARASSMENT,
            ReportCategory.INAPPROPRIATE_CONTENT,
            ReportCategory.FAKE_PROFILE,
            ReportCategory.SPAM,
            ReportCategory.SAFETY_CONCERN
        ]
        
        for category in categories:
            assert isinstance(category.value, str)
            assert len(category.value) > 0

    def test_safety_status_enum(self):
        """Test that safety status values are properly defined"""
        statuses = [
            SafetyStatus.ACTIVE,
            SafetyStatus.RESTRICTED,
            SafetyStatus.SUSPENDED,
            SafetyStatus.BANNED
        ]
        
        for status in statuses:
            assert isinstance(status.value, str)
            assert len(status.value) > 0


class TestReportingFunctionality:
    """Test user reporting functionality"""

    def test_report_user_basic(self):
        """Test basic user reporting functionality"""
        db_mock = Mock()
        service = UserSafetyService(db_mock)
        
        # Mock database operations
        db_mock.add = Mock()
        db_mock.commit = Mock()
        db_mock.query.return_value.filter.return_value.first.return_value = None
        
        reporter_id = 1
        reported_id = 2
        category = ReportCategory.HARASSMENT
        description = "Inappropriate messages"
        
        with patch('app.services.user_safety_simplified.UserReport') as mock_report:
            mock_report_instance = Mock()
            mock_report.return_value = mock_report_instance
            
            result = service.report_user(reporter_id, reported_id, category, description)
            
            # Verify report was created
            mock_report.assert_called_once_with(
                reporter_id=reporter_id,
                reported_user_id=reported_id,
                category=category,
                description=description
            )
            
            # Verify database operations
            db_mock.add.assert_called_once_with(mock_report_instance)
            db_mock.commit.assert_called_once()
            
            assert result is True

    def test_report_user_duplicate_prevention(self):
        """Test prevention of duplicate reports"""
        db_mock = Mock()
        service = UserSafetyService(db_mock)
        
        # Mock existing report
        existing_report = Mock()
        db_mock.query.return_value.filter.return_value.first.return_value = existing_report
        
        result = service.report_user(1, 2, ReportCategory.SPAM, "Test")
        
        # Should not create new report
        assert result is False
        db_mock.add.assert_not_called()

    def test_report_self_prevention(self):
        """Test prevention of self-reporting"""
        db_mock = Mock()
        service = UserSafetyService(db_mock)
        
        # Try to report self
        result = service.report_user(1, 1, ReportCategory.HARASSMENT, "Test")
        
        assert result is False
        db_mock.add.assert_not_called()

    def test_get_user_reports(self):
        """Test retrieving reports for a user"""
        db_mock = Mock()
        service = UserSafetyService(db_mock)
        
        # Mock reports
        mock_reports = [Mock(), Mock(), Mock()]
        db_mock.query.return_value.filter.return_value.all.return_value = mock_reports
        
        reports = service.get_user_reports(user_id=123)
        
        assert reports == mock_reports
        db_mock.query.assert_called_once()

    def test_get_report_statistics(self):
        """Test getting report statistics"""
        db_mock = Mock()
        service = UserSafetyService(db_mock)
        
        # Mock different report counts
        db_mock.query.return_value.filter.return_value.count.side_effect = [5, 2, 1, 1, 1]
        
        stats = service.get_report_statistics(user_id=123)
        
        assert isinstance(stats, dict)
        assert "total_reports" in stats
        assert "harassment" in stats
        assert stats["total_reports"] == 5


class TestBlockingFunctionality:
    """Test user blocking functionality"""

    def test_block_user_success(self):
        """Test successful user blocking"""
        db_mock = Mock()
        service = UserSafetyService(db_mock)
        
        # Mock no existing block
        db_mock.query.return_value.filter.return_value.first.return_value = None
        db_mock.add = Mock()
        db_mock.commit = Mock()
        
        with patch('app.services.user_safety_simplified.BlockedUser') as mock_block:
            mock_block_instance = Mock()
            mock_block.return_value = mock_block_instance
            
            result = service.block_user(blocker_id=1, blocked_id=2)
            
            mock_block.assert_called_once_with(blocker_id=1, blocked_user_id=2)
            db_mock.add.assert_called_once_with(mock_block_instance)
            db_mock.commit.assert_called_once()
            
            assert result is True

    def test_block_user_already_blocked(self):
        """Test blocking already blocked user"""
        db_mock = Mock()
        service = UserSafetyService(db_mock)
        
        # Mock existing block
        existing_block = Mock()
        db_mock.query.return_value.filter.return_value.first.return_value = existing_block
        
        result = service.block_user(blocker_id=1, blocked_id=2)
        
        assert result is False
        db_mock.add.assert_not_called()

    def test_block_self_prevention(self):
        """Test prevention of self-blocking"""
        db_mock = Mock()
        service = UserSafetyService(db_mock)
        
        result = service.block_user(blocker_id=1, blocked_id=1)
        
        assert result is False
        db_mock.add.assert_not_called()

    def test_unblock_user(self):
        """Test unblocking a user"""
        db_mock = Mock()
        service = UserSafetyService(db_mock)
        
        # Mock existing block
        existing_block = Mock()
        db_mock.query.return_value.filter.return_value.first.return_value = existing_block
        db_mock.delete = Mock()
        db_mock.commit = Mock()
        
        result = service.unblock_user(blocker_id=1, blocked_id=2)
        
        db_mock.delete.assert_called_once_with(existing_block)
        db_mock.commit.assert_called_once()
        assert result is True

    def test_unblock_user_not_blocked(self):
        """Test unblocking user that wasn't blocked"""
        db_mock = Mock()
        service = UserSafetyService(db_mock)
        
        # Mock no existing block
        db_mock.query.return_value.filter.return_value.first.return_value = None
        
        result = service.unblock_user(blocker_id=1, blocked_id=2)
        
        assert result is False
        db_mock.delete.assert_not_called()

    def test_get_blocked_users(self):
        """Test getting list of blocked users"""
        db_mock = Mock()
        service = UserSafetyService(db_mock)
        
        # Mock blocked users
        mock_blocks = [Mock(), Mock()]
        db_mock.query.return_value.filter.return_value.all.return_value = mock_blocks
        
        blocked = service.get_blocked_users(blocker_id=1)
        
        assert blocked == mock_blocks

    def test_is_user_blocked(self):
        """Test checking if user is blocked"""
        db_mock = Mock()
        service = UserSafetyService(db_mock)
        
        # Test blocked scenario
        existing_block = Mock()
        db_mock.query.return_value.filter.return_value.first.return_value = existing_block
        
        assert service.is_user_blocked(blocker_id=1, potential_blocked_id=2) is True
        
        # Test not blocked scenario
        db_mock.query.return_value.filter.return_value.first.return_value = None
        
        assert service.is_user_blocked(blocker_id=1, potential_blocked_id=3) is False


class TestSafetyStatusManagement:
    """Test safety status management"""

    def test_update_user_safety_status(self):
        """Test updating user safety status"""
        db_mock = Mock()
        service = UserSafetyService(db_mock)
        
        # Mock user
        mock_user = Mock(spec=User)
        db_mock.query.return_value.filter.return_value.first.return_value = mock_user
        db_mock.commit = Mock()
        
        result = service.update_user_safety_status(
            user_id=123, 
            status=SafetyStatus.RESTRICTED,
            reason="Multiple reports received"
        )
        
        assert mock_user.safety_status == SafetyStatus.RESTRICTED
        db_mock.commit.assert_called_once()
        assert result is True

    def test_update_nonexistent_user_status(self):
        """Test updating status for non-existent user"""
        db_mock = Mock()
        service = UserSafetyService(db_mock)
        
        # Mock no user found
        db_mock.query.return_value.filter.return_value.first.return_value = None
        
        result = service.update_user_safety_status(
            user_id=999,
            status=SafetyStatus.BANNED,
            reason="Test"
        )
        
        assert result is False
        db_mock.commit.assert_not_called()

    def test_get_user_safety_status(self):
        """Test getting user safety status"""
        db_mock = Mock()
        service = UserSafetyService(db_mock)
        
        # Mock user with status
        mock_user = Mock(spec=User)
        mock_user.safety_status = SafetyStatus.ACTIVE
        db_mock.query.return_value.filter.return_value.first.return_value = mock_user
        
        status = service.get_user_safety_status(user_id=123)
        
        assert status == SafetyStatus.ACTIVE

    def test_bulk_safety_operations(self):
        """Test bulk safety operations for efficiency"""
        db_mock = Mock()
        service = UserSafetyService(db_mock)
        
        user_ids = [1, 2, 3, 4, 5]
        
        # Mock bulk update
        db_mock.query.return_value.filter.return_value.update.return_value = len(user_ids)
        db_mock.commit = Mock()
        
        result = service.bulk_update_safety_status(
            user_ids=user_ids,
            status=SafetyStatus.SUSPENDED,
            reason="Bulk moderation action"
        )
        
        assert result == len(user_ids)
        db_mock.commit.assert_called_once()


class TestSafetyAnalytics:
    """Test safety analytics and reporting"""

    def test_get_safety_metrics(self):
        """Test getting safety metrics for analytics"""
        db_mock = Mock()
        service = UserSafetyService(db_mock)
        
        # Mock various counts
        db_mock.query.return_value.count.side_effect = [100, 25, 10, 5]
        
        # Mock date filtering
        db_mock.query.return_value.filter.return_value.count.side_effect = [15, 8, 3, 1]
        
        metrics = service.get_safety_metrics(days=30)
        
        assert isinstance(metrics, dict)
        assert "total_reports" in metrics
        assert "recent_reports" in metrics

    def test_identify_high_risk_users(self):
        """Test identifying users with multiple reports"""
        db_mock = Mock()
        service = UserSafetyService(db_mock)
        
        # Mock high-risk users query
        mock_users = [Mock(), Mock()]
        db_mock.query.return_value.group_by.return_value.having.return_value.all.return_value = mock_users
        
        high_risk = service.identify_high_risk_users(report_threshold=3)
        
        assert high_risk == mock_users

    def test_safety_trend_analysis(self):
        """Test safety trend analysis over time"""
        db_mock = Mock()
        service = UserSafetyService(db_mock)
        
        # Mock trend data
        mock_trend_data = [
            (datetime.now() - timedelta(days=1), 5),
            (datetime.now() - timedelta(days=2), 3),
            (datetime.now() - timedelta(days=3), 8),
        ]
        db_mock.query.return_value.filter.return_value.group_by.return_value.all.return_value = mock_trend_data
        
        trends = service.get_safety_trends(days=7)
        
        assert isinstance(trends, list)
        assert len(trends) == 3


class TestSafetyIntegration:
    """Integration tests for safety service"""

    def test_report_to_block_workflow(self):
        """Test complete workflow from report to block"""
        db_mock = Mock()
        service = UserSafetyService(db_mock)
        
        # Mock successful report
        db_mock.query.return_value.filter.return_value.first.return_value = None
        db_mock.add = Mock()
        db_mock.commit = Mock()
        
        with patch('app.services.user_safety_simplified.UserReport'), \
             patch('app.services.user_safety_simplified.BlockedUser'):
            
            # Report user
            report_result = service.report_user(
                reporter_id=1,
                reported_id=2,
                category=ReportCategory.HARASSMENT,
                description="Inappropriate behavior"
            )
            
            assert report_result is True
            
            # Block user
            block_result = service.block_user(blocker_id=1, blocked_id=2)
            
            assert block_result is True
            
            # Verify both operations called database
            assert db_mock.add.call_count == 2
            assert db_mock.commit.call_count == 2

    def test_edge_case_safety_operations(self):
        """Test edge cases in safety operations"""
        db_mock = Mock()
        service = UserSafetyService(db_mock)
        
        # Test with None values
        assert service.report_user(None, 1, ReportCategory.SPAM, "test") is False
        assert service.block_user(1, None) is False
        
        # Test with same user IDs
        assert service.report_user(1, 1, ReportCategory.SPAM, "test") is False
        assert service.block_user(1, 1) is False
        
        # Test with empty descriptions
        result = service.report_user(1, 2, ReportCategory.SPAM, "")
        # Should handle gracefully (may accept empty description)
        assert isinstance(result, bool)

    def test_concurrent_safety_operations(self):
        """Test handling of concurrent safety operations"""
        db_mock = Mock()
        service = UserSafetyService(db_mock)
        
        # Mock database error (e.g., integrity constraint)
        db_mock.add = Mock()
        db_mock.commit.side_effect = Exception("Integrity constraint violation")
        db_mock.rollback = Mock()
        
        with patch('app.services.user_safety_simplified.UserReport'):
            result = service.report_user(1, 2, ReportCategory.SPAM, "test")
            
            # Should handle database errors gracefully
            db_mock.rollback.assert_called_once()
            assert result is False  # Or however the service handles errors