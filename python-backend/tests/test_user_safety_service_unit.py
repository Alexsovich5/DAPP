"""
Unit tests for user safety service functionality  
Tests safety reporting, validation, and user protection without external dependencies
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from app.services.user_safety_simplified import (
    UserSafetyService,
    UserReport,
    ReportCategory,
    ReportStatus,
    ActionType
)


@pytest.mark.unit
@pytest.mark.security
class TestUserSafetyService:
    """Test suite for UserSafetyService class"""
    
    @pytest.fixture
    def safety_service(self):
        """Create UserSafetyService instance"""
        return UserSafetyService()
    
    def test_safety_service_initialization(self, safety_service):
        """Test UserSafetyService initialization"""
        assert hasattr(safety_service, 'reports')
        assert hasattr(safety_service, 'actions')
        assert isinstance(safety_service.reports, list)
        assert isinstance(safety_service.actions, list)
    
    @pytest.mark.asyncio
    async def test_submit_report_valid(self, safety_service):
        """Test submitting a valid report"""
        report = UserReport(
            reporter_id=123,
            reported_user_id=456,
            category=ReportCategory.HARASSMENT,
            description="User sent inappropriate messages",
            evidence_urls=[],
            reported_at=datetime.utcnow()
        )
        
        result = await safety_service.submit_report(report)
        
        assert result["success"] is True
        assert "report_id" in result
        assert len(safety_service.reports) == 1
    
    @pytest.mark.asyncio
    async def test_submit_report_self_report(self, safety_service):
        """Test submitting report against oneself (should fail)"""
        report = UserReport(
            reporter_id=123,
            reported_user_id=123,  # Same user
            category=ReportCategory.SPAM,
            description="Self report",
            evidence_urls=[],
            reported_at=datetime.utcnow()
        )
        
        result = await safety_service.submit_report(report)
        
        assert result["success"] is False
        assert "cannot report yourself" in result["error"].lower()
        assert len(safety_service.reports) == 0
    
    @pytest.mark.asyncio
    async def test_submit_report_too_many_recent(self, safety_service):
        """Test submitting too many reports in 24 hours"""
        # Add multiple recent reports to trigger rate limit
        recent_time = datetime.utcnow()
        for i in range(6):  # Exceeds limit of 5
            report_data = {
                "reporter_id": 123,
                "reported_user_id": 400 + i,
                "category": "spam",
                "description": f"Spam report {i}",
                "reported_at": recent_time.isoformat()
            }
            safety_service.reports.append(report_data)
        
        new_report = UserReport(
            reporter_id=123,
            reported_user_id=500,
            category=ReportCategory.SPAM,
            description="Another spam report",
            evidence_urls=[],
            reported_at=datetime.utcnow()
        )
        
        result = await safety_service.submit_report(new_report)
        
        assert result["success"] is False
        assert "too many reports" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_submit_report_duplicate_user(self, safety_service):
        """Test submitting multiple reports for same user"""
        # Add multiple reports for same user
        recent_time = datetime.utcnow()
        for i in range(3):  # Exceeds limit of 2
            report_data = {
                "reporter_id": 123,
                "reported_user_id": 456,  # Same reported user
                "category": "harassment",
                "description": f"Harassment report {i}",
                "reported_at": recent_time.isoformat()
            }
            safety_service.reports.append(report_data)
        
        new_report = UserReport(
            reporter_id=123,
            reported_user_id=456,  # Same user again
            category=ReportCategory.HARASSMENT,
            description="Another harassment report",
            evidence_urls=[],
            reported_at=datetime.utcnow()
        )
        
        result = await safety_service.submit_report(new_report)
        
        assert result["success"] is False
        assert "already reported this user" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_submit_report_violence_threats_immediate_action(self, safety_service):
        """Test submitting violence threats report triggers immediate action"""
        report = UserReport(
            reporter_id=123,
            reported_user_id=456,
            category=ReportCategory.VIOLENCE_THREATS,
            description="User threatened violence",
            evidence_urls=[],
            reported_at=datetime.utcnow()
        )
        
        result = await safety_service.submit_report(report)
        
        assert result["success"] is True
        assert result.get("immediate_action_taken") is True
        assert len(safety_service.actions) == 1
        assert safety_service.actions[0]["action_type"] == ActionType.TEMPORARY_SUSPENSION
    
    @pytest.mark.asyncio
    async def test_submit_report_underage_immediate_action(self, safety_service):
        """Test submitting underage report triggers immediate action"""
        report = UserReport(
            reporter_id=123,
            reported_user_id=456,
            category=ReportCategory.UNDERAGE,
            description="User appears to be underage",
            evidence_urls=[],
            reported_at=datetime.utcnow()
        )
        
        result = await safety_service.submit_report(report)
        
        assert result["success"] is True
        assert result.get("immediate_action_taken") is True
        assert len(safety_service.actions) == 1
    
    @pytest.mark.asyncio
    async def test_submit_report_multiple_harassment_action(self, safety_service):
        """Test multiple harassment reports trigger action"""
        # Add existing harassment report
        existing_report = {
            "reporter_id": 100,
            "reported_user_id": 456,
            "category": "harassment",
            "description": "Previous harassment",
            "reported_at": datetime.utcnow().isoformat()
        }
        safety_service.reports.append(existing_report)
        
        # Submit another harassment report for same user
        report = UserReport(
            reporter_id=123,
            reported_user_id=456,
            category=ReportCategory.HARASSMENT,
            description="More harassment from this user",
            evidence_urls=[],
            reported_at=datetime.utcnow()
        )
        
        result = await safety_service.submit_report(report)
        
        assert result["success"] is True
        assert result.get("immediate_action_taken") is True
        assert len(safety_service.actions) == 1
        assert safety_service.actions[0]["action_type"] == ActionType.MESSAGE_RESTRICTION
    
    def test_get_reports_for_user(self, safety_service):
        """Test getting reports for a specific user"""
        # Add test reports
        reports_data = [
            {
                "id": "RPT_123",
                "reporter_id": 100,
                "reported_user_id": 456,
                "category": "spam",
                "description": "Spam messages",
                "status": "pending",
                "reported_at": datetime.utcnow().isoformat()
            },
            {
                "id": "RPT_124", 
                "reporter_id": 200,
                "reported_user_id": 456,  # Same reported user
                "category": "harassment",
                "description": "Harassment behavior",
                "status": "pending",
                "reported_at": datetime.utcnow().isoformat()
            },
            {
                "id": "RPT_125",
                "reporter_id": 300,
                "reported_user_id": 789,  # Different user
                "category": "fake_profile",
                "description": "Fake profile",
                "status": "pending",
                "reported_at": datetime.utcnow().isoformat()
            }
        ]
        safety_service.reports.extend(reports_data)
        
        user_reports = safety_service.get_reports_for_user(456)
        
        assert len(user_reports) == 2
        assert all(report["reported_user_id"] == 456 for report in user_reports)
    
    def test_get_reports_for_user_none_found(self, safety_service):
        """Test getting reports when user has none"""
        user_reports = safety_service.get_reports_for_user(999)
        
        assert len(user_reports) == 0
        assert isinstance(user_reports, list)
    
    def test_get_report_by_id_found(self, safety_service):
        """Test getting report by ID when it exists"""
        report_data = {
            "id": "RPT_TEST123",
            "reporter_id": 100,
            "reported_user_id": 456,
            "category": "spam",
            "description": "Test report",
            "status": "pending",
            "reported_at": datetime.utcnow().isoformat()
        }
        safety_service.reports.append(report_data)
        
        found_report = safety_service.get_report_by_id("RPT_TEST123")
        
        assert found_report is not None
        assert found_report["id"] == "RPT_TEST123"
        assert found_report["category"] == "spam"
    
    def test_get_report_by_id_not_found(self, safety_service):
        """Test getting report by ID when it doesn't exist"""
        found_report = safety_service.get_report_by_id("RPT_NONEXISTENT")
        
        assert found_report is None
    
    def test_update_report_status_found(self, safety_service):
        """Test updating report status when report exists"""
        report_data = {
            "id": "RPT_UPDATE",
            "reporter_id": 100,
            "reported_user_id": 456,
            "category": "spam",
            "description": "Test report",
            "status": "pending",
            "reported_at": datetime.utcnow().isoformat()
        }
        safety_service.reports.append(report_data)
        
        result = safety_service.update_report_status("RPT_UPDATE", ReportStatus.RESOLVED, "Issue resolved")
        
        assert result is True
        assert safety_service.reports[0]["status"] == "resolved"
        assert safety_service.reports[0]["resolution_notes"] == "Issue resolved"
    
    def test_update_report_status_not_found(self, safety_service):
        """Test updating report status when report doesn't exist"""
        result = safety_service.update_report_status("RPT_NONEXISTENT", ReportStatus.RESOLVED, "Notes")
        
        assert result is False
    
    def test_get_pending_reports(self, safety_service):
        """Test getting all pending reports"""
        reports_data = [
            {
                "id": "RPT_1",
                "status": "pending",
                "reported_at": datetime.utcnow().isoformat()
            },
            {
                "id": "RPT_2",
                "status": "resolved",
                "reported_at": datetime.utcnow().isoformat()
            },
            {
                "id": "RPT_3",
                "status": "pending",
                "reported_at": datetime.utcnow().isoformat()
            }
        ]
        safety_service.reports.extend(reports_data)
        
        pending_reports = safety_service.get_pending_reports()
        
        assert len(pending_reports) == 2
        assert all(report["status"] == "pending" for report in pending_reports)
    
    def test_get_actions_for_user(self, safety_service):
        """Test getting actions taken for a specific user"""
        actions_data = [
            {
                "id": "ACT_1",
                "user_id": 456,
                "action_type": ActionType.WARNING,
                "reason": "First warning",
                "taken_at": datetime.utcnow().isoformat()
            },
            {
                "id": "ACT_2",
                "user_id": 789,  # Different user
                "action_type": ActionType.TEMPORARY_SUSPENSION,
                "reason": "Suspension",
                "taken_at": datetime.utcnow().isoformat()
            },
            {
                "id": "ACT_3",
                "user_id": 456,  # Same user as first
                "action_type": ActionType.MESSAGE_RESTRICTION,
                "reason": "Message restriction",
                "taken_at": datetime.utcnow().isoformat()
            }
        ]
        safety_service.actions.extend(actions_data)
        
        user_actions = safety_service.get_actions_for_user(456)
        
        assert len(user_actions) == 2
        assert all(action["user_id"] == 456 for action in user_actions)
    
    def test_is_user_restricted_true(self, safety_service):
        """Test checking if user is restricted when they are"""
        action_data = {
            "id": "ACT_RESTRICT",
            "user_id": 456,
            "action_type": ActionType.TEMPORARY_SUSPENSION,
            "reason": "Policy violation",
            "taken_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat()
        }
        safety_service.actions.append(action_data)
        
        is_restricted = safety_service.is_user_restricted(456)
        
        assert is_restricted is True
    
    def test_is_user_restricted_false(self, safety_service):
        """Test checking if user is restricted when they aren't"""
        is_restricted = safety_service.is_user_restricted(999)
        
        assert is_restricted is False
    
    def test_is_user_restricted_expired_action(self, safety_service):
        """Test user restriction check with expired action"""
        action_data = {
            "id": "ACT_EXPIRED",
            "user_id": 456,
            "action_type": ActionType.TEMPORARY_SUSPENSION,
            "reason": "Expired suspension",
            "taken_at": (datetime.utcnow() - timedelta(days=10)).isoformat(),
            "expires_at": (datetime.utcnow() - timedelta(days=1)).isoformat()  # Expired
        }
        safety_service.actions.append(action_data)
        
        is_restricted = safety_service.is_user_restricted(456)
        
        assert is_restricted is False


@pytest.mark.unit
class TestUserReport:
    """Test suite for UserReport dataclass"""
    
    def test_user_report_creation(self):
        """Test UserReport creation with all fields"""
        report = UserReport(
            reporter_id=123,
            reported_user_id=456,
            category=ReportCategory.HARASSMENT,
            description="User sent inappropriate messages",
            evidence_urls=["https://example.com/evidence1.jpg"],
            reported_at=datetime.utcnow()
        )
        
        assert report.reporter_id == 123
        assert report.reported_user_id == 456
        assert report.category == ReportCategory.HARASSMENT
        assert report.description == "User sent inappropriate messages"
        assert len(report.evidence_urls) == 1
        assert isinstance(report.reported_at, datetime)


@pytest.mark.unit
class TestReportCategory:
    """Test suite for ReportCategory enum"""
    
    def test_report_category_values(self):
        """Test ReportCategory enum values"""
        assert ReportCategory.HARASSMENT.value == "harassment"
        assert ReportCategory.FAKE_PROFILE.value == "fake_profile"
        assert ReportCategory.INAPPROPRIATE_PHOTOS.value == "inappropriate_photos"
        assert ReportCategory.SPAM.value == "spam"
        assert ReportCategory.SCAM.value == "scam"
        assert ReportCategory.VIOLENCE_THREATS.value == "violence_threats"
        assert ReportCategory.HATE_SPEECH.value == "hate_speech"
        assert ReportCategory.UNDERAGE.value == "underage"
        assert ReportCategory.IMPERSONATION.value == "impersonation"
        assert ReportCategory.OTHER.value == "other"


@pytest.mark.unit
class TestReportStatus:
    """Test suite for ReportStatus enum"""
    
    def test_report_status_values(self):
        """Test ReportStatus enum values"""
        assert ReportStatus.PENDING.value == "pending"
        assert ReportStatus.IN_REVIEW.value == "in_review"
        assert ReportStatus.RESOLVED.value == "resolved"
        assert ReportStatus.DISMISSED.value == "dismissed"
        assert ReportStatus.ESCALATED.value == "escalated"


@pytest.mark.unit
class TestActionType:
    """Test suite for ActionType enum"""
    
    def test_action_type_values(self):
        """Test ActionType enum values"""
        assert ActionType.WARNING.value == "warning"
        assert ActionType.TEMPORARY_SUSPENSION.value == "temporary_suspension"
        assert ActionType.PERMANENT_BAN.value == "permanent_ban"
        assert ActionType.PROFILE_RESTRICTION.value == "profile_restriction"
        assert ActionType.MESSAGE_RESTRICTION.value == "message_restriction"
        assert ActionType.PHOTO_REMOVAL.value == "photo_removal"
        assert ActionType.PROFILE_REVIEW.value == "profile_review"
        assert ActionType.NO_ACTION.value == "no_action"


@pytest.mark.integration
@pytest.mark.security
class TestUserSafetyServiceIntegration:
    """Integration test scenarios for UserSafetyService"""
    
    @pytest.fixture
    def safety_service(self):
        """Create UserSafetyService instance"""
        return UserSafetyService()
    
    @pytest.mark.asyncio
    async def test_report_lifecycle(self, safety_service):
        """Test complete report lifecycle"""
        # Submit report
        report = UserReport(
            reporter_id=123,
            reported_user_id=456,
            category=ReportCategory.SPAM,
            description="User sending spam messages",
            evidence_urls=[],
            reported_at=datetime.utcnow()
        )
        
        submit_result = await safety_service.submit_report(report)
        assert submit_result["success"] is True
        report_id = submit_result["report_id"]
        
        # Verify report exists
        found_report = safety_service.get_report_by_id(report_id)
        assert found_report is not None
        assert found_report["status"] == "pending"
        
        # Update status to in review
        update_result = safety_service.update_report_status(
            report_id, ReportStatus.IN_REVIEW, "Under investigation"
        )
        assert update_result is True
        
        # Verify status updated
        updated_report = safety_service.get_report_by_id(report_id)
        assert updated_report["status"] == "in_review"
        assert updated_report["resolution_notes"] == "Under investigation"
        
        # Resolve report
        final_update = safety_service.update_report_status(
            report_id, ReportStatus.RESOLVED, "Issue resolved - user warned"
        )
        assert final_update is True
        
        # Verify final status
        final_report = safety_service.get_report_by_id(report_id)
        assert final_report["status"] == "resolved"
    
    @pytest.mark.asyncio
    async def test_escalation_workflow(self, safety_service):
        """Test report escalation for serious violations"""
        # Submit multiple serious reports to trigger escalation
        serious_categories = [
            ReportCategory.VIOLENCE_THREATS,
            ReportCategory.UNDERAGE,
            ReportCategory.HATE_SPEECH
        ]
        
        results = []
        for i, category in enumerate(serious_categories):
            report = UserReport(
                reporter_id=100 + i,
                reported_user_id=456,  # Same reported user
                category=category,
                description=f"Serious violation: {category.value}",
                evidence_urls=[],
                reported_at=datetime.utcnow()
            )
            
            result = await safety_service.submit_report(report)
            results.append(result)
        
        # Check that immediate actions were taken
        serious_reports = [r for r in results if r.get("immediate_action_taken")]
        assert len(serious_reports) >= 2  # Violence threats and underage should trigger actions
        
        # Verify actions were recorded
        user_actions = safety_service.get_actions_for_user(456)
        assert len(user_actions) >= 2
        
        # Verify user is now restricted
        assert safety_service.is_user_restricted(456) is True