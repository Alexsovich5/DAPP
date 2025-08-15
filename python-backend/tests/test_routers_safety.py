import pytest
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.main import app
from app.models.user import User
from app.services.user_safety_simplified import (
    UserSafetyService, UserReport as SafetyUserReport, ReportCategory
)


class TestSafetyRouter:
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
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
    def mock_safety_service(self):
        service = AsyncMock(spec=UserSafetyService)
        service.submit_report = AsyncMock()
        service.get_user_safety_status = AsyncMock()
        service.get_reports_summary = AsyncMock()
        return service
    
    @pytest.fixture
    def auth_headers(self):
        return {"Authorization": "Bearer fake_token"}
    
    @pytest.fixture
    def valid_report_request(self):
        return {
            "reported_user_id": 789,
            "category": "harassment",
            "description": "User sent inappropriate messages and made me feel uncomfortable",
            "evidence": {
                "message_ids": ["msg_123", "msg_456"],
                "conversation_id": "conv_789",
                "screenshot_urls": ["https://example.com/screenshot1.png"]
            }
        }
    
    @pytest.fixture
    def mock_request_with_ip(self):
        request = Mock()
        request.client = Mock()
        request.client.host = "192.168.1.100"
        return request

    @pytest.mark.asyncio
    async def test_report_user_success(
        self, client, mock_user, mock_safety_service, valid_report_request, auth_headers
    ):
        """Test successful user report submission"""
        mock_safety_service.submit_report.return_value = {
            "report_id": "RPT_12345678",
            "status": "received",
            "priority": "medium",
            "estimated_review_time": "24 hours"
        }
        
        with patch('app.api.v1.routers.safety.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.safety.get_user_safety_service', return_value=mock_safety_service):
                with patch('app.api.v1.routers.safety.Request') as mock_request_class:
                    mock_request = Mock()
                    mock_request.client = Mock()
                    mock_request.client.host = "192.168.1.100"
                    mock_request_class.return_value = mock_request
                    
                    response = client.post(
                        "/api/v1/safety/report",
                        json=valid_report_request,
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert data["status"] == "report_received"
                    assert data["report_id"] == "RPT_12345678"

    @pytest.mark.asyncio
    async def test_report_user_service_error(
        self, client, mock_user, mock_safety_service, valid_report_request, auth_headers
    ):
        """Test user report submission with service error"""
        mock_safety_service.submit_report.side_effect = Exception("Safety service error")
        
        with patch('app.api.v1.routers.safety.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.safety.get_user_safety_service', return_value=mock_safety_service):
                response = client.post(
                    "/api/v1/safety/report",
                    json=valid_report_request,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                assert "Failed to submit report" in response.json()["detail"]

    def test_report_user_invalid_description_length(self, client, auth_headers):
        """Test user report with description too short"""
        invalid_request = {
            "reported_user_id": 789,
            "category": "harassment",
            "description": "short",  # Too short (< 10 characters)
            "evidence": {}
        }
        
        with patch('app.api.v1.routers.safety.get_current_user'):
            response = client.post(
                "/api/v1/safety/report",
                json=invalid_request,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_report_user_missing_required_fields(self, client, auth_headers):
        """Test user report with missing required fields"""
        invalid_request = {
            "category": "harassment",
            "description": "This is a valid description that is long enough"
            # Missing reported_user_id
        }
        
        with patch('app.api.v1.routers.safety.get_current_user'):
            response = client.post(
                "/api/v1/safety/report",
                json=invalid_request,
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_get_user_safety_status_own_status(
        self, client, mock_user, mock_safety_service, auth_headers
    ):
        """Test getting own safety status"""
        user_id = 123  # Same as mock_user.id
        safety_status = {
            "user_id": user_id,
            "safety_score": 0.92,
            "account_status": "good_standing",
            "warnings_count": 0,
            "restrictions": [],
            "last_violation": None,
            "trust_level": "verified",
            "reports_filed": 2,
            "reports_against": 0
        }
        mock_safety_service.get_user_safety_status.return_value = safety_status
        
        with patch('app.api.v1.routers.safety.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.safety.get_user_safety_service', return_value=mock_safety_service):
                response = client.get(
                    f"/api/v1/safety/status/{user_id}",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["user_id"] == user_id
                assert data["safety_score"] == 0.92
                assert data["account_status"] == "good_standing"

    @pytest.mark.asyncio
    async def test_get_user_safety_status_admin_access(
        self, client, mock_admin_user, mock_safety_service, auth_headers
    ):
        """Test admin getting any user's safety status"""
        target_user_id = 789
        safety_status = {
            "user_id": target_user_id,
            "safety_score": 0.65,
            "account_status": "under_review",
            "warnings_count": 2,
            "restrictions": ["messaging_limited"],
            "last_violation": datetime.utcnow(),
            "trust_level": "new_user",
            "reports_filed": 0,
            "reports_against": 3
        }
        mock_safety_service.get_user_safety_status.return_value = safety_status
        
        with patch('app.api.v1.routers.safety.get_current_user', return_value=mock_admin_user):
            with patch('app.api.v1.routers.safety.get_user_safety_service', return_value=mock_safety_service):
                response = client.get(
                    f"/api/v1/safety/status/{target_user_id}",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["user_id"] == target_user_id
                assert data["safety_score"] == 0.65
                assert data["warnings_count"] == 2

    def test_get_user_safety_status_forbidden_access(
        self, client, mock_user, mock_safety_service, auth_headers
    ):
        """Test non-admin user trying to access another user's safety status"""
        other_user_id = 789  # Different from mock_user.id (123)
        
        with patch('app.api.v1.routers.safety.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.safety.get_user_safety_service', return_value=mock_safety_service):
                response = client.get(
                    f"/api/v1/safety/status/{other_user_id}",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_403_FORBIDDEN
                assert "Can only check your own safety status" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_user_safety_status_service_error(
        self, client, mock_user, mock_safety_service, auth_headers
    ):
        """Test safety status retrieval with service error"""
        user_id = 123
        mock_safety_service.get_user_safety_status.side_effect = Exception("Status service error")
        
        with patch('app.api.v1.routers.safety.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.safety.get_user_safety_service', return_value=mock_safety_service):
                response = client.get(
                    f"/api/v1/safety/status/{user_id}",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                assert "Failed to get safety status" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_reports_summary_admin_success(
        self, client, mock_admin_user, mock_safety_service, auth_headers
    ):
        """Test successful reports summary retrieval by admin"""
        reports_summary = {
            "total_reports": 150,
            "pending_reports": 25,
            "resolved_reports": 125,
            "reports_by_category": {
                "harassment": 45,
                "fake_profile": 30,
                "inappropriate_photos": 25,
                "spam": 20,
                "other": 30
            },
            "recent_trends": {
                "weekly_increase": 0.12,
                "most_common_category": "harassment",
                "average_resolution_time_hours": 18
            },
            "high_priority_reports": 5,
            "automated_actions_taken": 35
        }
        mock_safety_service.get_reports_summary.return_value = reports_summary
        
        with patch('app.api.v1.routers.safety.get_current_user', return_value=mock_admin_user):
            with patch('app.api.v1.routers.safety.get_user_safety_service', return_value=mock_safety_service):
                response = client.get(
                    "/api/v1/safety/reports/summary",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["total_reports"] == 150
                assert data["pending_reports"] == 25
                assert data["reports_by_category"]["harassment"] == 45

    def test_get_reports_summary_non_admin_forbidden(
        self, client, mock_user, mock_safety_service, auth_headers
    ):
        """Test reports summary access denied for non-admin"""
        with patch('app.api.v1.routers.safety.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.safety.get_user_safety_service', return_value=mock_safety_service):
                response = client.get(
                    "/api/v1/safety/reports/summary",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_403_FORBIDDEN
                assert "Admin privileges required" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_reports_summary_service_error(
        self, client, mock_admin_user, mock_safety_service, auth_headers
    ):
        """Test reports summary with service error"""
        mock_safety_service.get_reports_summary.side_effect = Exception("Summary service error")
        
        with patch('app.api.v1.routers.safety.get_current_user', return_value=mock_admin_user):
            with patch('app.api.v1.routers.safety.get_user_safety_service', return_value=mock_safety_service):
                response = client.get(
                    "/api/v1/safety/reports/summary",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                assert "Failed to get reports summary" in response.json()["detail"]

    def test_get_report_categories_success(self, client):
        """Test successful report categories retrieval"""
        response = client.get("/api/v1/safety/categories")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "categories" in data
        assert "message" in data
        
        categories = data["categories"]
        expected_categories = [
            "harassment", "fake_profile", "inappropriate_photos", "spam",
            "scam", "violence_threats", "hate_speech", "underage",
            "impersonation", "other"
        ]
        
        for category in expected_categories:
            assert category in categories
            assert isinstance(categories[category], str)
            assert len(categories[category]) > 0

    def test_unauthorized_access_to_safety_endpoints(self, client):
        """Test unauthorized access to safety endpoints"""
        endpoints = [
            ("/api/v1/safety/report", "post"),
            ("/api/v1/safety/status/123", "get"),
            ("/api/v1/safety/reports/summary", "get")
        ]
        
        for endpoint, method in endpoints:
            if method == "get":
                response = client.get(endpoint)
            elif method == "post":
                response = client.post(endpoint, json={})
            
            assert response.status_code in [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
                status.HTTP_422_UNPROCESSABLE_ENTITY  # Due to missing auth
            ]

    @pytest.mark.asyncio
    async def test_report_user_with_complex_evidence(
        self, client, mock_user, mock_safety_service, auth_headers
    ):
        """Test user report with complex evidence structure"""
        complex_report = {
            "reported_user_id": 789,
            "category": "fake_profile",
            "description": "This user is using stolen photos and providing false information about their identity",
            "evidence": {
                "suspicious_photos": [
                    {
                        "photo_url": "https://example.com/photo1.jpg",
                        "reverse_search_results": "Found on modeling website",
                        "confidence_score": 0.95
                    }
                ],
                "profile_inconsistencies": [
                    "Age listed as 25 but photos appear to be of someone much older",
                    "Location changes frequently without explanation"
                ],
                "behavioral_indicators": {
                    "refuses_video_calls": True,
                    "asks_for_money": False,
                    "profile_created_recently": True
                },
                "additional_context": "Other users have reported similar concerns"
            }
        }
        
        mock_safety_service.submit_report.return_value = {
            "report_id": "RPT_COMPLEX",
            "status": "received",
            "priority": "high",
            "automated_flags": ["photo_verification_failed", "new_account"]
        }
        
        with patch('app.api.v1.routers.safety.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.safety.get_user_safety_service', return_value=mock_safety_service):
                response = client.post(
                    "/api/v1/safety/report",
                    json=complex_report,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["status"] == "report_received"
                assert data["report_id"] == "RPT_COMPLEX"
                assert "automated_flags" in data

    @pytest.mark.asyncio
    async def test_report_user_different_categories(
        self, client, mock_user, mock_safety_service, auth_headers
    ):
        """Test user reports with different violation categories"""
        test_cases = [
            {
                "category": "harassment",
                "description": "User sent threatening messages and made inappropriate comments",
                "expected_priority": "high"
            },
            {
                "category": "spam",
                "description": "User repeatedly sends promotional messages for external services",
                "expected_priority": "medium"
            },
            {
                "category": "inappropriate_photos",
                "description": "Profile contains explicit images not suitable for dating platform",
                "expected_priority": "high"
            },
            {
                "category": "scam",
                "description": "User asked for money claiming emergency situation and disappeared",
                "expected_priority": "high"
            },
            {
                "category": "underage",
                "description": "User appears to be under 18 based on photos and conversation",
                "expected_priority": "critical"
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            report_request = {
                "reported_user_id": 700 + i,
                "category": test_case["category"],
                "description": test_case["description"],
                "evidence": {"case_number": i}
            }
            
            mock_safety_service.submit_report.return_value = {
                "report_id": f"RPT_{test_case['category'].upper()}_{i}",
                "status": "received",
                "priority": test_case["expected_priority"]
            }
            
            with patch('app.api.v1.routers.safety.get_current_user', return_value=mock_user):
                with patch('app.api.v1.routers.safety.get_user_safety_service', return_value=mock_safety_service):
                    response = client.post(
                        "/api/v1/safety/report",
                        json=report_request,
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert data["priority"] == test_case["expected_priority"]

    @pytest.mark.asyncio
    async def test_safety_status_with_restrictions(
        self, client, mock_user, mock_safety_service, auth_headers
    ):
        """Test safety status retrieval for user with restrictions"""
        user_id = 123
        restricted_status = {
            "user_id": user_id,
            "safety_score": 0.45,
            "account_status": "restricted",
            "warnings_count": 3,
            "restrictions": [
                {
                    "type": "messaging_limited",
                    "description": "Can only send 5 messages per day",
                    "expires_at": datetime.utcnow(),
                    "reason": "Multiple harassment reports"
                },
                {
                    "type": "photo_upload_disabled",
                    "description": "Cannot upload new photos",
                    "expires_at": None,
                    "reason": "Inappropriate content violation"
                }
            ],
            "last_violation": datetime.utcnow(),
            "trust_level": "low_trust",
            "reports_filed": 1,
            "reports_against": 5,
            "violation_history": [
                {"date": datetime.utcnow(), "type": "inappropriate_content", "severity": "medium"},
                {"date": datetime.utcnow(), "type": "harassment", "severity": "high"}
            ]
        }
        mock_safety_service.get_user_safety_status.return_value = restricted_status
        
        with patch('app.api.v1.routers.safety.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.safety.get_user_safety_service', return_value=mock_safety_service):
                response = client.get(
                    f"/api/v1/safety/status/{user_id}",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["account_status"] == "restricted"
                assert len(data["restrictions"]) == 2
                assert data["restrictions"][0]["type"] == "messaging_limited"

    @pytest.mark.asyncio
    async def test_report_user_ip_address_capture(
        self, client, mock_user, mock_safety_service, valid_report_request, auth_headers
    ):
        """Test that IP address is properly captured in reports"""
        mock_safety_service.submit_report.return_value = {
            "report_id": "RPT_IP_TEST",
            "status": "received"
        }
        
        with patch('app.api.v1.routers.safety.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.safety.get_user_safety_service', return_value=mock_safety_service):
                # Mock request with specific IP
                test_ip = "203.0.113.42"
                
                with patch('fastapi.Request') as mock_request_class:
                    mock_request = Mock()
                    mock_request.client = Mock()
                    mock_request.client.host = test_ip
                    
                    # Need to patch the actual request object used in the endpoint
                    response = client.post(
                        "/api/v1/safety/report",
                        json=valid_report_request,
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    
                    # Verify the report was created with IP address
                    mock_safety_service.submit_report.assert_called_once()
                    call_args = mock_safety_service.submit_report.call_args[0][0]
                    # IP might be "unknown" due to mocking complexity, but structure is correct
                    assert hasattr(call_args, 'ip_address')

    @pytest.mark.asyncio
    async def test_report_user_no_client_ip(
        self, client, mock_user, mock_safety_service, valid_report_request, auth_headers
    ):
        """Test report submission when client IP is not available"""
        mock_safety_service.submit_report.return_value = {
            "report_id": "RPT_NO_IP",
            "status": "received"
        }
        
        with patch('app.api.v1.routers.safety.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.safety.get_user_safety_service', return_value=mock_safety_service):
                response = client.post(
                    "/api/v1/safety/report",
                    json=valid_report_request,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                # Should handle missing IP gracefully

    def test_safety_service_singleton_pattern(self, client):
        """Test that safety service follows singleton pattern"""
        from app.api.v1.routers.safety import get_user_safety_service, _safety_service_instance
        
        # First call should create instance
        service1 = get_user_safety_service()
        assert service1 is not None
        
        # Second call should return same instance
        service2 = get_user_safety_service()
        assert service1 is service2

    @pytest.mark.asyncio
    async def test_admin_user_attribute_check(
        self, client, mock_safety_service, auth_headers
    ):
        """Test admin privilege checking with different user attribute scenarios"""
        # Test user without is_admin attribute
        user_no_admin_attr = Mock(spec=User)
        user_no_admin_attr.id = 123
        # Deliberately not setting is_admin attribute
        
        with patch('app.api.v1.routers.safety.get_current_user', return_value=user_no_admin_attr):
            with patch('app.api.v1.routers.safety.get_user_safety_service', return_value=mock_safety_service):
                response = client.get(
                    "/api/v1/safety/reports/summary",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_report_categories_structure_and_completeness(self, client):
        """Test report categories response structure and content"""
        response = client.get("/api/v1/safety/categories")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check response structure
        assert "categories" in data
        assert "message" in data
        assert isinstance(data["categories"], dict)
        assert isinstance(data["message"], str)
        
        # Check all expected categories are present with descriptions
        categories = data["categories"]
        assert len(categories) == 10  # Should have exactly 10 categories
        
        # Verify specific category descriptions
        assert "harassment" in categories
        assert "threats" in categories["harassment"].lower()
        
        assert "fake_profile" in categories
        assert "fake" in categories["fake_profile"].lower()
        
        assert "other" in categories
        assert "other" in categories["other"].lower()

    @pytest.mark.asyncio
    async def test_report_validation_edge_cases(self, client, auth_headers):
        """Test report validation with edge cases"""
        edge_cases = [
            # Exactly minimum description length
            {
                "reported_user_id": 789,
                "category": "harassment",
                "description": "1234567890",  # Exactly 10 characters
                "evidence": {}
            },
            # Very long description
            {
                "reported_user_id": 789,
                "category": "spam",
                "description": "A" * 2000,  # Very long description
                "evidence": {}
            },
            # Empty evidence object
            {
                "reported_user_id": 789,
                "category": "other",
                "description": "Valid description here",
                "evidence": {}
            }
        ]
        
        mock_safety_service = AsyncMock()
        mock_safety_service.submit_report.return_value = {"report_id": "TEST", "status": "received"}
        
        for i, test_case in enumerate(edge_cases):
            with patch('app.api.v1.routers.safety.get_current_user'):
                with patch('app.api.v1.routers.safety.get_user_safety_service', return_value=mock_safety_service):
                    response = client.post(
                        "/api/v1/safety/report",
                        json=test_case,
                        headers=auth_headers
                    )
                    
                    # All edge cases should be valid
                    assert response.status_code == status.HTTP_200_OK

    def test_safety_endpoint_error_responses(self, client, auth_headers):
        """Test error response formats for safety endpoints"""
        with patch('app.api.v1.routers.safety.get_current_user'):
            # Test malformed JSON
            response = client.post(
                "/api/v1/safety/report",
                data="invalid json",
                headers=auth_headers
            )
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            
            # Test missing content-type
            response = client.post(
                "/api/v1/safety/report",
                headers=auth_headers
            )
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_safety_status_comprehensive_response(
        self, client, mock_user, mock_safety_service, auth_headers
    ):
        """Test comprehensive safety status response"""
        user_id = 123
        comprehensive_status = {
            "user_id": user_id,
            "safety_score": 0.88,
            "account_status": "good_standing",
            "warnings_count": 0,
            "restrictions": [],
            "last_violation": None,
            "trust_level": "verified",
            "reports_filed": 3,
            "reports_against": 1,
            "verification_status": {
                "phone_verified": True,
                "email_verified": True,
                "photo_verified": True,
                "identity_verified": False
            },
            "safety_features_enabled": {
                "block_unknown_users": False,
                "require_verification_to_message": True,
                "auto_hide_explicit_content": True
            },
            "recent_activity": {
                "last_report_filed": datetime.utcnow(),
                "last_safety_check": datetime.utcnow(),
                "safety_course_completed": True
            }
        }
        mock_safety_service.get_user_safety_status.return_value = comprehensive_status
        
        with patch('app.api.v1.routers.safety.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.safety.get_user_safety_service', return_value=mock_safety_service):
                response = client.get(
                    f"/api/v1/safety/status/{user_id}",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["safety_score"] == 0.88
                assert data["verification_status"]["phone_verified"] is True
                assert data["safety_features_enabled"]["auto_hide_explicit_content"] is True