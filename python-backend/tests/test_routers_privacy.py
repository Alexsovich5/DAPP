import pytest
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import uuid

from app.main import app
from app.models.user import User
from app.services.privacy_compliance import (
    PrivacyComplianceService, DataCategory, DataSubjectRight, 
    ProcessingPurpose, PrivacyRequest
)


class TestPrivacyRouter:
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        user = Mock(spec=User)
        user.id = 123
        user.email = "test@example.com"
        user.username = "testuser"
        return user
    
    @pytest.fixture
    def mock_privacy_service(self):
        service = AsyncMock(spec=PrivacyComplianceService)
        service.collect_user_consent = AsyncMock()
        service.withdraw_consent = AsyncMock()
        service.get_privacy_dashboard_data = AsyncMock()
        service.process_data_subject_request = AsyncMock()
        service.get_request_info = AsyncMock()
        service.get_user_privacy_requests = AsyncMock()
        return service
    
    @pytest.fixture
    def auth_headers(self):
        return {"Authorization": "Bearer fake_token"}
    
    @pytest.fixture
    def valid_consent_request(self):
        return {
            "categories": ["analytics", "marketing", "location_services"]
        }
    
    @pytest.fixture
    def valid_consent_withdrawal_request(self):
        return {
            "data_category": "profile_data",
            "processing_purpose": "marketing"
        }
    
    @pytest.fixture
    def valid_data_subject_request(self):
        return {
            "request_type": "access",
            "data_categories": ["profile_data", "interaction_data"],
            "notes": "Please provide all my data"
        }
    
    @pytest.fixture
    def valid_rectification_request(self):
        return {
            "field_name": "email",
            "current_value": "wrong@email.com",
            "correct_value": "correct@email.com",
            "reason": "Typo in email address"
        }
    
    @pytest.fixture
    def valid_privacy_preferences(self):
        return {
            "marketing_emails": False,
            "push_notifications": True,
            "location_sharing": False,
            "analytics_participation": True,
            "data_sharing_research": False
        }

    @pytest.mark.asyncio
    async def test_grant_consent_success(
        self, client, mock_user, mock_privacy_service, valid_consent_request, auth_headers
    ):
        """Test successful consent granting"""
        mock_privacy_service.collect_user_consent.return_value = {
            "consent_id": "consent_123",
            "categories_granted": ["analytics", "marketing", "location_services"],
            "timestamp": datetime.utcnow()
        }
        
        with patch('app.api.v1.routers.privacy.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.privacy.get_privacy_service', return_value=mock_privacy_service):
                response = client.post(
                    "/api/v1/privacy/consent",
                    json=valid_consent_request,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["success"] is True
                assert "Consent preferences updated successfully" in data["message"]
                assert "data" in data

    @pytest.mark.asyncio
    async def test_grant_consent_service_error(
        self, client, mock_user, mock_privacy_service, valid_consent_request, auth_headers
    ):
        """Test consent granting with service error"""
        mock_privacy_service.collect_user_consent.side_effect = Exception("Service error")
        
        with patch('app.api.v1.routers.privacy.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.privacy.get_privacy_service', return_value=mock_privacy_service):
                response = client.post(
                    "/api/v1/privacy/consent",
                    json=valid_consent_request,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                assert "Failed to update consent preferences" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_withdraw_consent_success(
        self, client, mock_user, mock_privacy_service, valid_consent_withdrawal_request, auth_headers
    ):
        """Test successful consent withdrawal"""
        mock_privacy_service.withdraw_consent.return_value = {
            "success": True,
            "withdrawal_id": "withdrawal_123",
            "effective_date": datetime.utcnow()
        }
        
        with patch('app.api.v1.routers.privacy.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.privacy.get_privacy_service', return_value=mock_privacy_service):
                response = client.delete(
                    "/api/v1/privacy/consent",
                    json=valid_consent_withdrawal_request,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["success"] is True
                assert "Consent withdrawn successfully" in data["message"]

    @pytest.mark.asyncio
    async def test_withdraw_consent_failure(
        self, client, mock_user, mock_privacy_service, valid_consent_withdrawal_request, auth_headers
    ):
        """Test consent withdrawal failure"""
        mock_privacy_service.withdraw_consent.return_value = {
            "success": False,
            "error": "Cannot withdraw required consent"
        }
        
        with patch('app.api.v1.routers.privacy.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.privacy.get_privacy_service', return_value=mock_privacy_service):
                response = client.delete(
                    "/api/v1/privacy/consent",
                    json=valid_consent_withdrawal_request,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_400_BAD_REQUEST
                assert "Cannot withdraw required consent" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_withdraw_consent_invalid_category(
        self, client, mock_user, mock_privacy_service, auth_headers
    ):
        """Test consent withdrawal with invalid category"""
        invalid_request = {
            "data_category": "invalid_category",
            "processing_purpose": "marketing"
        }
        
        with patch('app.api.v1.routers.privacy.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.privacy.get_privacy_service', return_value=mock_privacy_service):
                response = client.delete(
                    "/api/v1/privacy/consent",
                    json=invalid_request,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_400_BAD_REQUEST
                assert "Invalid category or purpose" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_privacy_dashboard_success(
        self, client, mock_user, mock_privacy_service, auth_headers
    ):
        """Test successful privacy dashboard retrieval"""
        dashboard_data = {
            "consent_status": {
                "analytics": {"granted": True, "date": datetime.utcnow()},
                "marketing": {"granted": False, "date": None}
            },
            "data_categories": {
                "profile_data": {"size_mb": 2.5, "last_updated": datetime.utcnow()},
                "interaction_data": {"size_mb": 1.2, "last_updated": datetime.utcnow()}
            },
            "privacy_requests": {
                "total": 3,
                "pending": 1,
                "completed": 2
            },
            "data_retention": {
                "profile_data": "7 years",
                "messages": "3 years"
            }
        }
        mock_privacy_service.get_privacy_dashboard_data.return_value = dashboard_data
        
        with patch('app.api.v1.routers.privacy.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.privacy.get_privacy_service', return_value=mock_privacy_service):
                response = client.get(
                    "/api/v1/privacy/dashboard",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["success"] is True
                assert "data" in data
                assert data["data"]["consent_status"]["analytics"]["granted"] is True

    @pytest.mark.asyncio
    async def test_submit_data_subject_access_request(
        self, client, mock_user, mock_privacy_service, auth_headers
    ):
        """Test data subject access request submission"""
        access_request = {
            "request_type": "access",
            "data_categories": ["profile_data"],
            "notes": "Need my data for review"
        }
        
        with patch('app.api.v1.routers.privacy.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.privacy.get_privacy_service', return_value=mock_privacy_service):
                response = client.post(
                    "/api/v1/privacy/data-subject-request",
                    json=access_request,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["success"] is True
                assert data["status"] == "processing"
                assert "request_id" in data
                assert data["estimated_completion"] == "30 days"

    @pytest.mark.asyncio
    async def test_submit_data_subject_erasure_request(
        self, client, mock_user, mock_privacy_service, auth_headers
    ):
        """Test data subject erasure request submission"""
        erasure_request = {
            "request_type": "erasure",
            "data_categories": ["profile_data", "interaction_data"],
            "notes": "Please delete all my data"
        }
        
        mock_privacy_service.process_data_subject_request.return_value = {
            "success": True,
            "processing_id": "proc_123"
        }
        
        with patch('app.api.v1.routers.privacy.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.privacy.get_privacy_service', return_value=mock_privacy_service):
                response = client.post(
                    "/api/v1/privacy/data-subject-request",
                    json=erasure_request,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["success"] is True
                assert "request_id" in data

    @pytest.mark.asyncio
    async def test_submit_invalid_data_subject_request(
        self, client, mock_user, mock_privacy_service, auth_headers
    ):
        """Test data subject request with invalid type"""
        invalid_request = {
            "request_type": "invalid_type",
            "data_categories": ["profile_data"],
            "notes": "Invalid request"
        }
        
        with patch('app.api.v1.routers.privacy.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.privacy.get_privacy_service', return_value=mock_privacy_service):
                response = client.post(
                    "/api/v1/privacy/data-subject-request",
                    json=invalid_request,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_400_BAD_REQUEST
                assert "Invalid request type" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_download_data_export_success(
        self, client, mock_user, mock_privacy_service, auth_headers
    ):
        """Test successful data export download"""
        request_id = "DSR_12345678"
        request_info = {
            "user_id": 123,
            "status": "completed",
            "file_path": "/tmp/export_123.zip"
        }
        mock_privacy_service.get_request_info.return_value = request_info
        
        with patch('app.api.v1.routers.privacy.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.privacy.get_privacy_service', return_value=mock_privacy_service):
                with patch('app.api.v1.routers.privacy.FileResponse') as mock_file_response:
                    mock_file_response.return_value = Mock()
                    
                    response = client.get(
                        f"/api/v1/privacy/data-export/{request_id}",
                        headers=auth_headers
                    )
                    
                    # FileResponse would be returned, we mock it
                    mock_file_response.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_data_export_not_found(
        self, client, mock_user, mock_privacy_service, auth_headers
    ):
        """Test data export download for non-existent request"""
        request_id = "DSR_INVALID"
        mock_privacy_service.get_request_info.return_value = None
        
        with patch('app.api.v1.routers.privacy.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.privacy.get_privacy_service', return_value=mock_privacy_service):
                response = client.get(
                    f"/api/v1/privacy/data-export/{request_id}",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_404_NOT_FOUND
                assert "Request not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_download_data_export_wrong_user(
        self, client, mock_user, mock_privacy_service, auth_headers
    ):
        """Test data export download for request belonging to different user"""
        request_id = "DSR_12345678"
        request_info = {
            "user_id": 999,  # Different user
            "status": "completed",
            "file_path": "/tmp/export_999.zip"
        }
        mock_privacy_service.get_request_info.return_value = request_info
        
        with patch('app.api.v1.routers.privacy.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.privacy.get_privacy_service', return_value=mock_privacy_service):
                response = client.get(
                    f"/api/v1/privacy/data-export/{request_id}",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_404_NOT_FOUND
                assert "Request not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_download_data_export_not_completed(
        self, client, mock_user, mock_privacy_service, auth_headers
    ):
        """Test data export download for incomplete request"""
        request_id = "DSR_12345678"
        request_info = {
            "user_id": 123,
            "status": "processing",  # Not completed
            "file_path": None
        }
        mock_privacy_service.get_request_info.return_value = request_info
        
        with patch('app.api.v1.routers.privacy.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.privacy.get_privacy_service', return_value=mock_privacy_service):
                response = client.get(
                    f"/api/v1/privacy/data-export/{request_id}",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_400_BAD_REQUEST
                assert "Request not yet completed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_privacy_preferences_success(
        self, client, mock_user, mock_privacy_service, valid_privacy_preferences, auth_headers
    ):
        """Test successful privacy preferences update"""
        mock_privacy_service.collect_user_consent.return_value = {"success": True}
        mock_privacy_service.withdraw_consent.return_value = {"success": True}
        
        with patch('app.api.v1.routers.privacy.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.privacy.get_privacy_service', return_value=mock_privacy_service):
                response = client.put(
                    "/api/v1/privacy/preferences",
                    json=valid_privacy_preferences,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["success"] is True
                assert "Privacy preferences updated successfully" in data["message"]
                assert data["updates_applied"] > 0

    @pytest.mark.asyncio
    async def test_update_privacy_preferences_partial_update(
        self, client, mock_user, mock_privacy_service, auth_headers
    ):
        """Test privacy preferences update with only some fields"""
        partial_preferences = {
            "marketing_emails": False,
            "analytics_participation": True
        }
        
        mock_privacy_service.collect_user_consent.return_value = {"success": True}
        mock_privacy_service.withdraw_consent.return_value = {"success": True}
        
        with patch('app.api.v1.routers.privacy.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.privacy.get_privacy_service', return_value=mock_privacy_service):
                response = client.put(
                    "/api/v1/privacy/preferences",
                    json=partial_preferences,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["success"] is True
                assert data["updates_applied"] == 2

    @pytest.mark.asyncio
    async def test_request_data_rectification_success(
        self, client, mock_user, mock_privacy_service, valid_rectification_request, auth_headers
    ):
        """Test successful data rectification request"""
        mock_privacy_service.process_data_subject_request.return_value = {
            "success": True,
            "processing_id": "rect_123"
        }
        
        with patch('app.api.v1.routers.privacy.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.privacy.get_privacy_service', return_value=mock_privacy_service):
                response = client.post(
                    "/api/v1/privacy/rectification",
                    json=valid_rectification_request,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["success"] is True
                assert "Data rectification request submitted successfully" in data["message"]
                assert "request_id" in data
                assert data["estimated_completion"] == "48 hours"

    @pytest.mark.asyncio
    async def test_get_privacy_requests_success(
        self, client, mock_user, mock_privacy_service, auth_headers
    ):
        """Test successful privacy requests history retrieval"""
        privacy_requests = [
            {
                "request_id": "DSR_12345678",
                "request_type": "access",
                "status": "completed",
                "requested_at": datetime.utcnow(),
                "processed_at": datetime.utcnow()
            },
            {
                "request_id": "DSR_87654321",
                "request_type": "rectification",
                "status": "processing",
                "requested_at": datetime.utcnow(),
                "processed_at": None
            }
        ]
        mock_privacy_service.get_user_privacy_requests.return_value = privacy_requests
        
        with patch('app.api.v1.routers.privacy.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.privacy.get_privacy_service', return_value=mock_privacy_service):
                response = client.get(
                    "/api/v1/privacy/requests",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["success"] is True
                assert len(data["requests"]) == 2
                assert data["requests"][0]["request_type"] == "access"

    @pytest.mark.asyncio
    async def test_request_account_deletion_success(
        self, client, mock_user, mock_privacy_service, auth_headers
    ):
        """Test successful account deletion request"""
        with patch('app.api.v1.routers.privacy.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.privacy.get_privacy_service', return_value=mock_privacy_service):
                response = client.delete(
                    "/api/v1/privacy/account",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["success"] is True
                assert "Account deletion request submitted" in data["message"]
                assert "request_id" in data
                assert "what_happens_next" in data
                assert len(data["what_happens_next"]) > 0

    def test_get_privacy_policy_success(self, client):
        """Test successful privacy policy retrieval"""
        response = client.get("/api/v1/privacy/policy")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "privacy_policy" in data
        policy = data["privacy_policy"]
        assert "version" in policy
        assert "effective_date" in policy
        assert "key_points" in policy
        assert "legal_basis" in policy
        assert "data_retention" in policy

    def test_unauthorized_access_to_privacy_endpoints(self, client):
        """Test unauthorized access to privacy endpoints"""
        endpoints = [
            ("/api/v1/privacy/consent", "post"),
            ("/api/v1/privacy/consent", "delete"),
            ("/api/v1/privacy/dashboard", "get"),
            ("/api/v1/privacy/data-subject-request", "post"),
            ("/api/v1/privacy/data-export/TEST_ID", "get"),
            ("/api/v1/privacy/preferences", "put"),
            ("/api/v1/privacy/rectification", "post"),
            ("/api/v1/privacy/requests", "get"),
            ("/api/v1/privacy/account", "delete")
        ]
        
        for endpoint, method in endpoints:
            if method == "get":
                response = client.get(endpoint)
            elif method == "post":
                response = client.post(endpoint, json={})
            elif method == "put":
                response = client.put(endpoint, json={})
            elif method == "delete":
                response = client.delete(endpoint)
            
            assert response.status_code in [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
                status.HTTP_422_UNPROCESSABLE_ENTITY  # Due to missing auth or validation
            ]

    def test_request_validation_errors(self, client, auth_headers):
        """Test request validation for various endpoints"""
        invalid_requests = [
            # Invalid consent request - missing categories
            {
                "endpoint": "/api/v1/privacy/consent",
                "method": "post",
                "data": {}
            },
            # Invalid consent withdrawal - missing required fields
            {
                "endpoint": "/api/v1/privacy/consent",
                "method": "delete",
                "data": {"data_category": "profile_data"}  # Missing processing_purpose
            },
            # Invalid rectification request - missing fields
            {
                "endpoint": "/api/v1/privacy/rectification",
                "method": "post",
                "data": {"field_name": "email"}  # Missing other required fields
            }
        ]
        
        with patch('app.api.v1.routers.privacy.get_current_user'):
            for req in invalid_requests:
                if req["method"] == "post":
                    response = client.post(req["endpoint"], json=req["data"], headers=auth_headers)
                elif req["method"] == "delete":
                    response = client.delete(req["endpoint"], json=req["data"], headers=auth_headers)
                
                assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_consent_request_empty_categories(
        self, client, mock_user, mock_privacy_service, auth_headers
    ):
        """Test consent request with empty categories list"""
        empty_consent_request = {
            "categories": []
        }
        
        mock_privacy_service.collect_user_consent.return_value = {
            "consent_id": "consent_empty",
            "categories_granted": [],
            "timestamp": datetime.utcnow()
        }
        
        with patch('app.api.v1.routers.privacy.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.privacy.get_privacy_service', return_value=mock_privacy_service):
                response = client.post(
                    "/api/v1/privacy/consent",
                    json=empty_consent_request,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_data_subject_request_invalid_categories(
        self, client, mock_user, mock_privacy_service, auth_headers
    ):
        """Test data subject request with invalid data categories"""
        invalid_request = {
            "request_type": "access",
            "data_categories": ["invalid_category"],
            "notes": "Test request"
        }
        
        with patch('app.api.v1.routers.privacy.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.privacy.get_privacy_service', return_value=mock_privacy_service):
                response = client.post(
                    "/api/v1/privacy/data-subject-request",
                    json=invalid_request,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_400_BAD_REQUEST
                assert "Invalid data category" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_privacy_service_dependency_injection(
        self, client, mock_user, auth_headers
    ):
        """Test privacy service dependency injection"""
        with patch('app.api.v1.routers.privacy.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.privacy.get_privacy_service') as mock_get_service:
                mock_service = AsyncMock()
                mock_service.get_privacy_dashboard_data.return_value = {"test": "data"}
                mock_get_service.return_value = mock_service
                
                response = client.get(
                    "/api/v1/privacy/dashboard",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                mock_get_service.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_logging_in_privacy_endpoints(
        self, client, mock_user, mock_privacy_service, auth_headers
    ):
        """Test that errors are properly logged in privacy endpoints"""
        mock_privacy_service.get_privacy_dashboard_data.side_effect = Exception("Test error")
        
        with patch('app.api.v1.routers.privacy.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.privacy.get_privacy_service', return_value=mock_privacy_service):
                with patch('app.api.v1.routers.privacy.logger') as mock_logger:
                    response = client.get(
                        "/api/v1/privacy/dashboard",
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                    mock_logger.error.assert_called_once()
                    error_msg = mock_logger.error.call_args[0][0]
                    assert "Error fetching privacy dashboard" in error_msg

    @pytest.mark.asyncio
    async def test_background_task_processing(
        self, client, mock_user, mock_privacy_service, auth_headers
    ):
        """Test background task processing for data subject requests"""
        access_request = {
            "request_type": "access",
            "data_categories": ["profile_data"],
            "notes": "Background processing test"
        }
        
        with patch('app.api.v1.routers.privacy.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.privacy.get_privacy_service', return_value=mock_privacy_service):
                with patch('app.api.v1.routers.privacy.BackgroundTasks') as mock_bg_tasks:
                    mock_bg_instance = Mock()
                    mock_bg_tasks.return_value = mock_bg_instance
                    
                    response = client.post(
                        "/api/v1/privacy/data-subject-request",
                        json=access_request,
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    # Background task should be added for access requests

    @pytest.mark.asyncio
    async def test_privacy_policy_error_handling(self, client):
        """Test privacy policy endpoint error handling"""
        with patch('app.api.v1.routers.privacy.logger') as mock_logger:
            # Force an exception in the privacy policy endpoint
            with patch('app.api.v1.routers.privacy.datetime') as mock_datetime:
                mock_datetime.side_effect = Exception("Policy error")
                
                response = client.get("/api/v1/privacy/policy")
                
                assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                assert "Failed to fetch privacy policy" in response.json()["detail"]
                mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_data_export_file_not_found(
        self, client, mock_user, mock_privacy_service, auth_headers
    ):
        """Test data export download when file path is missing"""
        request_id = "DSR_12345678"
        request_info = {
            "user_id": 123,
            "status": "completed",
            "file_path": None  # No file path
        }
        mock_privacy_service.get_request_info.return_value = request_info
        
        with patch('app.api.v1.routers.privacy.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.privacy.get_privacy_service', return_value=mock_privacy_service):
                response = client.get(
                    f"/api/v1/privacy/data-export/{request_id}",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_404_NOT_FOUND
                assert "Export file not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_rectification_request_processing(
        self, client, mock_user, mock_privacy_service, auth_headers
    ):
        """Test rectification request processing"""
        rectification_request = {
            "field_name": "date_of_birth",
            "current_value": "1990-01-01",
            "correct_value": "1991-01-01",
            "reason": "Incorrect birth year"
        }
        
        mock_privacy_service.process_data_subject_request.return_value = {
            "success": True,
            "processing_id": "rect_456"
        }
        
        with patch('app.api.v1.routers.privacy.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.privacy.get_privacy_service', return_value=mock_privacy_service):
                response = client.post(
                    "/api/v1/privacy/rectification",
                    json=rectification_request,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["success"] is True
                assert "RECT_" in data["request_id"]  # Should have rectification prefix

    @pytest.mark.asyncio
    async def test_account_deletion_request_id_generation(
        self, client, mock_user, mock_privacy_service, auth_headers
    ):
        """Test account deletion request ID generation"""
        with patch('app.api.v1.routers.privacy.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.privacy.get_privacy_service', return_value=mock_privacy_service):
                response = client.delete(
                    "/api/v1/privacy/account",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert "DEL_" in data["request_id"]  # Should have deletion prefix

    def test_privacy_preferences_none_values(
        self, client, mock_user, mock_privacy_service, auth_headers
    ):
        """Test privacy preferences update with None values"""
        preferences_with_none = {
            "marketing_emails": None,
            "push_notifications": True,
            "location_sharing": None,
            "analytics_participation": False
        }
        
        mock_privacy_service.collect_user_consent.return_value = {"success": True}
        mock_privacy_service.withdraw_consent.return_value = {"success": True}
        
        with patch('app.api.v1.routers.privacy.get_current_user', return_value=mock_user):
            with patch('app.api.v1.routers.privacy.get_privacy_service', return_value=mock_privacy_service):
                response = client.put(
                    "/api/v1/privacy/preferences",
                    json=preferences_with_none,
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                # Should only process non-None values
                assert data["updates_applied"] == 2  # Only non-None values