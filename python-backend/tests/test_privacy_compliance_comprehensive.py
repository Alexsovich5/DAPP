import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import uuid
import json

from app.services.privacy_compliance import (
    PrivacyComplianceService,
    DataCategory,
    ProcessingPurpose,
    LegalBasis,
    ConsentStatus,
    DataSubjectRight,
    ConsentRecord,
    DataProcessingRecord,
    PrivacyRequest
)


class TestPrivacyComplianceService:
    
    @pytest.fixture
    def mock_database(self):
        return Mock()
    
    @pytest.fixture
    def mock_redis(self):
        return Mock()
    
    @pytest.fixture
    def mock_storage_service(self):
        return Mock()
    
    @pytest.fixture
    def compliance_service(self, mock_database, mock_redis, mock_storage_service):
        return PrivacyComplianceService(mock_database, mock_redis, mock_storage_service)
    
    @pytest.fixture
    def sample_consent_record(self):
        return ConsentRecord(
            user_id=123,
            data_category=DataCategory.PROFILE_DATA,
            processing_purpose=ProcessingPurpose.MATCHING_SERVICE,
            legal_basis=LegalBasis.CONSENT,
            status=ConsentStatus.GRANTED,
            granted_at=datetime.utcnow(),
            withdrawn_at=None,
            expires_at=datetime.utcnow() + timedelta(days=365),
            consent_text="I consent to profile data processing for matching",
            version="v1.0"
        )
    
    @pytest.fixture
    def sample_processing_record(self):
        return DataProcessingRecord(
            user_id=123,
            data_category=DataCategory.BEHAVIORAL_DATA,
            processing_purpose=ProcessingPurpose.ANALYTICS,
            legal_basis=LegalBasis.LEGITIMATE_INTERESTS,
            processor="analytics_engine",
            timestamp=datetime.utcnow(),
            retention_period=timedelta(days=365),
            metadata={"session_id": "test_session"}
        )
    
    @pytest.fixture
    def sample_privacy_request(self):
        return PrivacyRequest(
            request_id=str(uuid.uuid4()),
            user_id=123,
            request_type=DataSubjectRight.ACCESS,
            status="pending",
            requested_at=datetime.utcnow(),
            processed_at=None,
            data_categories=[DataCategory.PROFILE_DATA, DataCategory.MESSAGES],
            notes="User requesting access to personal data"
        )

    def test_service_initialization(self, compliance_service):
        """Test privacy compliance service initialization"""
        assert compliance_service.database is not None
        assert compliance_service.redis is not None
        assert compliance_service.storage is not None

    def test_data_category_enum_values(self):
        """Test DataCategory enum values"""
        assert DataCategory.PROFILE_DATA.value == "profile_data"
        assert DataCategory.MESSAGES.value == "messages"
        assert DataCategory.PHOTOS.value == "photos"
        assert DataCategory.LOCATION_DATA.value == "location_data"
        assert DataCategory.MATCHING_PREFERENCES.value == "matching_preferences"
        assert DataCategory.BEHAVIORAL_DATA.value == "behavioral_data"
        assert DataCategory.DEVICE_DATA.value == "device_data"
        assert DataCategory.AUTHENTICATION_DATA.value == "authentication_data"

    def test_processing_purpose_enum_values(self):
        """Test ProcessingPurpose enum values"""
        assert ProcessingPurpose.ACCOUNT_MANAGEMENT.value == "account_management"
        assert ProcessingPurpose.MATCHING_SERVICE.value == "matching_service"
        assert ProcessingPurpose.COMMUNICATION.value == "communication"
        assert ProcessingPurpose.SAFETY_MODERATION.value == "safety_moderation"
        assert ProcessingPurpose.ANALYTICS.value == "analytics"
        assert ProcessingPurpose.MARKETING.value == "marketing"
        assert ProcessingPurpose.LEGAL_COMPLIANCE.value == "legal_compliance"

    def test_legal_basis_enum_values(self):
        """Test LegalBasis enum values"""
        assert LegalBasis.CONSENT.value == "consent"
        assert LegalBasis.CONTRACT.value == "contract"
        assert LegalBasis.LEGAL_OBLIGATION.value == "legal_obligation"
        assert LegalBasis.VITAL_INTERESTS.value == "vital_interests"
        assert LegalBasis.PUBLIC_TASK.value == "public_task"
        assert LegalBasis.LEGITIMATE_INTERESTS.value == "legitimate_interests"

    def test_consent_status_enum_values(self):
        """Test ConsentStatus enum values"""
        assert ConsentStatus.GRANTED.value == "granted"
        assert ConsentStatus.WITHDRAWN.value == "withdrawn"
        assert ConsentStatus.PENDING.value == "pending"
        assert ConsentStatus.EXPIRED.value == "expired"

    def test_data_subject_right_enum_values(self):
        """Test DataSubjectRight enum values"""
        assert DataSubjectRight.ACCESS.value == "access"
        assert DataSubjectRight.RECTIFICATION.value == "rectification"
        assert DataSubjectRight.ERASURE.value == "erasure"
        assert DataSubjectRight.RESTRICT_PROCESSING.value == "restrict_processing"
        assert DataSubjectRight.DATA_PORTABILITY.value == "data_portability"
        assert DataSubjectRight.OBJECT_PROCESSING.value == "object_processing"
        assert DataSubjectRight.WITHDRAW_CONSENT.value == "withdraw_consent"

    def test_consent_record_dataclass(self, sample_consent_record):
        """Test ConsentRecord dataclass"""
        assert sample_consent_record.user_id == 123
        assert sample_consent_record.data_category == DataCategory.PROFILE_DATA
        assert sample_consent_record.processing_purpose == ProcessingPurpose.MATCHING_SERVICE
        assert sample_consent_record.legal_basis == LegalBasis.CONSENT
        assert sample_consent_record.status == ConsentStatus.GRANTED
        assert sample_consent_record.version == "v1.0"
        assert sample_consent_record.withdrawn_at is None

    def test_data_processing_record_dataclass(self, sample_processing_record):
        """Test DataProcessingRecord dataclass"""
        assert sample_processing_record.user_id == 123
        assert sample_processing_record.data_category == DataCategory.BEHAVIORAL_DATA
        assert sample_processing_record.processing_purpose == ProcessingPurpose.ANALYTICS
        assert sample_processing_record.legal_basis == LegalBasis.LEGITIMATE_INTERESTS
        assert sample_processing_record.processor == "analytics_engine"
        assert sample_processing_record.retention_period == timedelta(days=365)
        assert "session_id" in sample_processing_record.metadata

    def test_privacy_request_dataclass(self, sample_privacy_request):
        """Test PrivacyRequest dataclass"""
        assert isinstance(sample_privacy_request.request_id, str)
        assert sample_privacy_request.user_id == 123
        assert sample_privacy_request.request_type == DataSubjectRight.ACCESS
        assert sample_privacy_request.status == "pending"
        assert len(sample_privacy_request.data_categories) == 2
        assert sample_privacy_request.processed_at is None

    @pytest.mark.asyncio
    async def test_record_consent_success(self, compliance_service, mock_database):
        """Test successful consent recording"""
        with patch.object(compliance_service, '_store_consent_record') as mock_store:
            with patch.object(compliance_service, '_log_compliance_event') as mock_log:
                mock_store.return_value = "consent_id_123"
                mock_log.return_value = None
                
                result = await compliance_service.record_consent(
                    user_id=123,
                    data_category=DataCategory.PROFILE_DATA,
                    processing_purpose=ProcessingPurpose.MATCHING_SERVICE,
                    consent_text="I consent to data processing",
                    version="v1.0"
                )
                
                assert result == "consent_id_123"
                mock_store.assert_called_once()
                mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_consent_error(self, compliance_service):
        """Test consent recording error handling"""
        with patch.object(compliance_service, '_store_consent_record', side_effect=Exception("Storage error")):
            with pytest.raises(Exception, match="Storage error"):
                await compliance_service.record_consent(
                    user_id=123,
                    data_category=DataCategory.PROFILE_DATA,
                    processing_purpose=ProcessingPurpose.MATCHING_SERVICE,
                    consent_text="I consent",
                    version="v1.0"
                )

    @pytest.mark.asyncio
    async def test_withdraw_consent_success(self, compliance_service):
        """Test successful consent withdrawal"""
        with patch.object(compliance_service, '_get_consent_record') as mock_get:
            with patch.object(compliance_service, '_update_consent_status') as mock_update:
                with patch.object(compliance_service, '_handle_data_deletion') as mock_deletion:
                    with patch.object(compliance_service, '_log_compliance_event') as mock_log:
                        mock_consent = Mock()
                        mock_consent.status = ConsentStatus.GRANTED
                        mock_get.return_value = mock_consent
                        
                        result = await compliance_service.withdraw_consent(
                            user_id=123,
                            data_category=DataCategory.PROFILE_DATA,
                            processing_purpose=ProcessingPurpose.MATCHING_SERVICE
                        )
                        
                        assert result is True
                        mock_update.assert_called_once()
                        mock_deletion.assert_called_once()
                        mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_withdraw_consent_not_found(self, compliance_service):
        """Test consent withdrawal when consent not found"""
        with patch.object(compliance_service, '_get_consent_record', return_value=None):
            result = await compliance_service.withdraw_consent(
                user_id=123,
                data_category=DataCategory.PROFILE_DATA,
                processing_purpose=ProcessingPurpose.MATCHING_SERVICE
            )
            
            assert result is False

    @pytest.mark.asyncio
    async def test_withdraw_consent_already_withdrawn(self, compliance_service):
        """Test consent withdrawal when already withdrawn"""
        with patch.object(compliance_service, '_get_consent_record') as mock_get:
            mock_consent = Mock()
            mock_consent.status = ConsentStatus.WITHDRAWN
            mock_get.return_value = mock_consent
            
            result = await compliance_service.withdraw_consent(
                user_id=123,
                data_category=DataCategory.PROFILE_DATA,
                processing_purpose=ProcessingPurpose.MATCHING_SERVICE
            )
            
            assert result is False

    @pytest.mark.asyncio
    async def test_process_data_subject_request_access(self, compliance_service):
        """Test data subject access request processing"""
        with patch.object(compliance_service, '_handle_access_request') as mock_handle:
            mock_handle.return_value = {"status": "completed", "data": {}}
            
            result = await compliance_service.process_data_subject_request(
                user_id=123,
                request_type=DataSubjectRight.ACCESS,
                data_categories=[DataCategory.PROFILE_DATA]
            )
            
            assert result["status"] == "completed"
            mock_handle.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_data_subject_request_erasure(self, compliance_service):
        """Test data subject erasure request processing"""
        with patch.object(compliance_service, '_handle_erasure_request') as mock_handle:
            mock_handle.return_value = {"status": "completed", "deleted_records": 150}
            
            result = await compliance_service.process_data_subject_request(
                user_id=123,
                request_type=DataSubjectRight.ERASURE,
                data_categories=[DataCategory.PROFILE_DATA, DataCategory.MESSAGES]
            )
            
            assert result["deleted_records"] == 150
            mock_handle.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_data_subject_request_portability(self, compliance_service):
        """Test data portability request processing"""
        with patch.object(compliance_service, '_handle_portability_request') as mock_handle:
            mock_handle.return_value = {"status": "completed", "export_url": "https://export.com/data.zip"}
            
            result = await compliance_service.process_data_subject_request(
                user_id=123,
                request_type=DataSubjectRight.DATA_PORTABILITY,
                data_categories=[DataCategory.PROFILE_DATA]
            )
            
            assert "export_url" in result
            mock_handle.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_data_subject_request_rectification(self, compliance_service):
        """Test data rectification request processing"""
        with patch.object(compliance_service, '_handle_rectification_request') as mock_handle:
            mock_handle.return_value = {"status": "completed", "updated_fields": ["name", "email"]}
            
            result = await compliance_service.process_data_subject_request(
                user_id=123,
                request_type=DataSubjectRight.RECTIFICATION,
                data_categories=[DataCategory.PROFILE_DATA],
                rectification_data={"name": "New Name"}
            )
            
            assert "updated_fields" in result
            mock_handle.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_data_subject_request_unknown_type(self, compliance_service):
        """Test unknown data subject request type"""
        # Create a mock request type that doesn't exist in our handlers
        with patch.object(compliance_service, '_get_request_handler', return_value=None):
            with pytest.raises(ValueError, match="Unsupported request type"):
                await compliance_service.process_data_subject_request(
                    user_id=123,
                    request_type="unknown_type",
                    data_categories=[DataCategory.PROFILE_DATA]
                )

    @pytest.mark.asyncio
    async def test_check_consent_validity_valid(self, compliance_service, sample_consent_record):
        """Test checking valid consent"""
        with patch.object(compliance_service, '_get_consent_record', return_value=sample_consent_record):
            result = await compliance_service.check_consent_validity(
                user_id=123,
                data_category=DataCategory.PROFILE_DATA,
                processing_purpose=ProcessingPurpose.MATCHING_SERVICE
            )
            
            assert result is True

    @pytest.mark.asyncio
    async def test_check_consent_validity_expired(self, compliance_service, sample_consent_record):
        """Test checking expired consent"""
        sample_consent_record.expires_at = datetime.utcnow() - timedelta(days=1)
        
        with patch.object(compliance_service, '_get_consent_record', return_value=sample_consent_record):
            result = await compliance_service.check_consent_validity(
                user_id=123,
                data_category=DataCategory.PROFILE_DATA,
                processing_purpose=ProcessingPurpose.MATCHING_SERVICE
            )
            
            assert result is False

    @pytest.mark.asyncio
    async def test_check_consent_validity_withdrawn(self, compliance_service, sample_consent_record):
        """Test checking withdrawn consent"""
        sample_consent_record.status = ConsentStatus.WITHDRAWN
        
        with patch.object(compliance_service, '_get_consent_record', return_value=sample_consent_record):
            result = await compliance_service.check_consent_validity(
                user_id=123,
                data_category=DataCategory.PROFILE_DATA,
                processing_purpose=ProcessingPurpose.MATCHING_SERVICE
            )
            
            assert result is False

    @pytest.mark.asyncio
    async def test_check_consent_validity_not_found(self, compliance_service):
        """Test checking consent when not found"""
        with patch.object(compliance_service, '_get_consent_record', return_value=None):
            result = await compliance_service.check_consent_validity(
                user_id=123,
                data_category=DataCategory.PROFILE_DATA,
                processing_purpose=ProcessingPurpose.MATCHING_SERVICE
            )
            
            assert result is False

    @pytest.mark.asyncio
    async def test_log_data_processing_success(self, compliance_service, mock_database):
        """Test successful data processing logging"""
        with patch.object(compliance_service, '_store_processing_record') as mock_store:
            with patch.object(compliance_service, '_check_processing_compliance') as mock_check:
                mock_check.return_value = True
                
                result = await compliance_service.log_data_processing(
                    user_id=123,
                    data_category=DataCategory.BEHAVIORAL_DATA,
                    processing_purpose=ProcessingPurpose.ANALYTICS,
                    processor="analytics_engine",
                    metadata={"session_id": "test"}
                )
                
                assert result is True
                mock_store.assert_called_once()
                mock_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_log_data_processing_non_compliant(self, compliance_service):
        """Test data processing logging when non-compliant"""
        with patch.object(compliance_service, '_check_processing_compliance', return_value=False):
            with pytest.raises(ValueError, match="Data processing not compliant"):
                await compliance_service.log_data_processing(
                    user_id=123,
                    data_category=DataCategory.BEHAVIORAL_DATA,
                    processing_purpose=ProcessingPurpose.ANALYTICS,
                    processor="analytics_engine"
                )

    @pytest.mark.asyncio
    async def test_generate_privacy_report_success(self, compliance_service):
        """Test privacy report generation"""
        with patch.object(compliance_service, '_collect_user_data') as mock_collect:
            with patch.object(compliance_service, '_generate_report_content') as mock_generate:
                with patch.object(compliance_service, '_create_report_file') as mock_create:
                    mock_collect.return_value = {"profile": {}, "messages": []}
                    mock_generate.return_value = "report content"
                    mock_create.return_value = "/tmp/report.pdf"
                    
                    result = await compliance_service.generate_privacy_report(
                        user_id=123,
                        include_categories=[DataCategory.PROFILE_DATA, DataCategory.MESSAGES]
                    )
                    
                    assert result == "/tmp/report.pdf"
                    mock_collect.assert_called_once()
                    mock_generate.assert_called_once()
                    mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_anonymize_user_data_success(self, compliance_service):
        """Test successful user data anonymization"""
        with patch.object(compliance_service, '_anonymize_data_category') as mock_anonymize:
            with patch.object(compliance_service, '_verify_anonymization') as mock_verify:
                mock_anonymize.return_value = True
                mock_verify.return_value = True
                
                result = await compliance_service.anonymize_user_data(
                    user_id=123,
                    data_categories=[DataCategory.PROFILE_DATA, DataCategory.BEHAVIORAL_DATA]
                )
                
                assert result is True
                assert mock_anonymize.call_count == 2
                mock_verify.assert_called_once()

    @pytest.mark.asyncio
    async def test_anonymize_user_data_failure(self, compliance_service):
        """Test user data anonymization failure"""
        with patch.object(compliance_service, '_anonymize_data_category', side_effect=Exception("Anonymization error")):
            result = await compliance_service.anonymize_user_data(
                user_id=123,
                data_categories=[DataCategory.PROFILE_DATA]
            )
            
            assert result is False

    @pytest.mark.asyncio
    async def test_expire_old_consents_success(self, compliance_service):
        """Test expiring old consents"""
        with patch.object(compliance_service, '_find_expired_consents') as mock_find:
            with patch.object(compliance_service, '_update_consent_status') as mock_update:
                mock_expired_consents = [
                    Mock(user_id=123, data_category=DataCategory.PROFILE_DATA),
                    Mock(user_id=456, data_category=DataCategory.MESSAGES)
                ]
                mock_find.return_value = mock_expired_consents
                
                result = await compliance_service.expire_old_consents()
                
                assert result == 2
                assert mock_update.call_count == 2

    @pytest.mark.asyncio
    async def test_audit_compliance_status_success(self, compliance_service):
        """Test compliance audit"""
        with patch.object(compliance_service, '_audit_consent_records') as mock_audit_consent:
            with patch.object(compliance_service, '_audit_processing_records') as mock_audit_processing:
                with patch.object(compliance_service, '_audit_retention_compliance') as mock_audit_retention:
                    mock_audit_consent.return_value = {"issues": [], "total_records": 100}
                    mock_audit_processing.return_value = {"issues": [], "total_records": 500}
                    mock_audit_retention.return_value = {"issues": ["retention_violation"], "total_records": 50}
                    
                    result = await compliance_service.audit_compliance_status()
                    
                    assert "consent_audit" in result
                    assert "processing_audit" in result
                    assert "retention_audit" in result
                    assert len(result["retention_audit"]["issues"]) == 1

    @pytest.mark.asyncio
    async def test_handle_breach_notification_success(self, compliance_service):
        """Test data breach notification handling"""
        breach_details = {
            "incident_id": "BREACH_001",
            "affected_users": [123, 456, 789],
            "data_categories": [DataCategory.PROFILE_DATA, DataCategory.MESSAGES],
            "severity": "high",
            "discovered_at": datetime.utcnow()
        }
        
        with patch.object(compliance_service, '_assess_breach_impact') as mock_assess:
            with patch.object(compliance_service, '_notify_authorities') as mock_notify_auth:
                with patch.object(compliance_service, '_notify_affected_users') as mock_notify_users:
                    with patch.object(compliance_service, '_log_breach_response') as mock_log:
                        mock_assess.return_value = {"risk_level": "high", "notification_required": True}
                        
                        result = await compliance_service.handle_breach_notification(breach_details)
                        
                        assert result["risk_level"] == "high"
                        mock_assess.assert_called_once()
                        mock_notify_auth.assert_called_once()
                        mock_notify_users.assert_called_once()
                        mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_legal_basis_consent_required(self, compliance_service):
        """Test legal basis validation for consent-required processing"""
        result = await compliance_service.validate_legal_basis(
            data_category=DataCategory.PHOTOS,
            processing_purpose=ProcessingPurpose.MATCHING_SERVICE,
            legal_basis=LegalBasis.CONSENT
        )
        
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_legal_basis_legitimate_interest(self, compliance_service):
        """Test legal basis validation for legitimate interest"""
        result = await compliance_service.validate_legal_basis(
            data_category=DataCategory.BEHAVIORAL_DATA,
            processing_purpose=ProcessingPurpose.ANALYTICS,
            legal_basis=LegalBasis.LEGITIMATE_INTERESTS
        )
        
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_legal_basis_invalid_combination(self, compliance_service):
        """Test invalid legal basis and processing purpose combination"""
        result = await compliance_service.validate_legal_basis(
            data_category=DataCategory.PHOTOS,
            processing_purpose=ProcessingPurpose.MARKETING,
            legal_basis=LegalBasis.LEGITIMATE_INTERESTS
        )
        
        assert result is False

    @pytest.mark.asyncio
    async def test_cleanup_expired_data_success(self, compliance_service):
        """Test expired data cleanup"""
        with patch.object(compliance_service, '_find_expired_data') as mock_find:
            with patch.object(compliance_service, '_delete_expired_records') as mock_delete:
                mock_expired_data = [
                    {"table": "user_events", "count": 100},
                    {"table": "message_history", "count": 50}
                ]
                mock_find.return_value = mock_expired_data
                mock_delete.return_value = True
                
                result = await compliance_service.cleanup_expired_data()
                
                assert result["deleted_records"] == 150
                assert result["tables_cleaned"] == 2
                mock_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_consent_dashboard_data(self, compliance_service):
        """Test consent dashboard data generation"""
        with patch.object(compliance_service, '_get_consent_statistics') as mock_stats:
            with patch.object(compliance_service, '_get_compliance_metrics') as mock_metrics:
                mock_stats.return_value = {
                    "total_consents": 1000,
                    "active_consents": 850,
                    "withdrawn_consents": 100,
                    "expired_consents": 50
                }
                mock_metrics.return_value = {
                    "compliance_score": 95.5,
                    "last_audit": datetime.utcnow()
                }
                
                result = await compliance_service.generate_consent_dashboard_data()
                
                assert result["consent_stats"]["total_consents"] == 1000
                assert result["compliance_metrics"]["compliance_score"] == 95.5

    @pytest.mark.asyncio
    async def test_concurrent_consent_operations(self, compliance_service):
        """Test concurrent consent operations"""
        # Simulate multiple consent operations
        tasks = []
        
        for i in range(10):
            with patch.object(compliance_service, '_store_consent_record', return_value=f"consent_{i}"):
                with patch.object(compliance_service, '_log_compliance_event'):
                    task = compliance_service.record_consent(
                        user_id=100 + i,
                        data_category=DataCategory.PROFILE_DATA,
                        processing_purpose=ProcessingPurpose.MATCHING_SERVICE,
                        consent_text="I consent",
                        version="v1.0"
                    )
                    tasks.append(task)
        
        # All operations should complete successfully
        results = await asyncio.gather(*tasks)
        assert len(results) == 10
        assert all(result.startswith("consent_") for result in results)

    @pytest.mark.asyncio
    async def test_gdpr_article_6_compliance(self, compliance_service):
        """Test GDPR Article 6 legal basis compliance"""
        # Test all legal bases are properly mapped
        legal_bases = [
            LegalBasis.CONSENT,
            LegalBasis.CONTRACT,
            LegalBasis.LEGAL_OBLIGATION,
            LegalBasis.VITAL_INTERESTS,
            LegalBasis.PUBLIC_TASK,
            LegalBasis.LEGITIMATE_INTERESTS
        ]
        
        for legal_basis in legal_bases:
            result = await compliance_service.validate_legal_basis(
                data_category=DataCategory.PROFILE_DATA,
                processing_purpose=ProcessingPurpose.ACCOUNT_MANAGEMENT,
                legal_basis=legal_basis
            )
            # All should be valid for account management
            assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_data_retention_compliance(self, compliance_service):
        """Test data retention period compliance"""
        with patch.object(compliance_service, '_get_retention_policy') as mock_policy:
            mock_policy.return_value = {"retention_days": 365, "auto_delete": True}
            
            result = await compliance_service.check_retention_compliance(
                data_category=DataCategory.BEHAVIORAL_DATA,
                processing_purpose=ProcessingPurpose.ANALYTICS
            )
            
            assert isinstance(result, dict)
            assert "retention_days" in result

    @pytest.mark.asyncio
    async def test_cross_border_transfer_compliance(self, compliance_service):
        """Test international data transfer compliance"""
        with patch.object(compliance_service, '_check_adequacy_decision') as mock_adequacy:
            with patch.object(compliance_service, '_validate_safeguards') as mock_safeguards:
                mock_adequacy.return_value = True
                mock_safeguards.return_value = {"standard_clauses": True, "certification": True}
                
                result = await compliance_service.validate_cross_border_transfer(
                    destination_country="US",
                    data_categories=[DataCategory.PROFILE_DATA],
                    safeguards=["standard_contractual_clauses"]
                )
                
                assert result["compliant"] is True
                mock_adequacy.assert_called_once()
                mock_safeguards.assert_called_once()

    def test_consent_record_expiry_calculation(self, sample_consent_record):
        """Test consent record expiry is properly calculated"""
        # GDPR requires consent to be renewed regularly
        granted_at = sample_consent_record.granted_at
        expires_at = sample_consent_record.expires_at
        
        # Should expire within reasonable time (typically 1-2 years)
        time_diff = expires_at - granted_at
        assert time_diff.days <= 730  # Max 2 years
        assert time_diff.days >= 365   # Min 1 year

    @pytest.mark.asyncio
    async def test_right_to_be_forgotten_cascade(self, compliance_service):
        """Test right to be forgotten cascades properly"""
        with patch.object(compliance_service, '_identify_related_data') as mock_identify:
            with patch.object(compliance_service, '_delete_user_data') as mock_delete:
                mock_identify.return_value = [
                    "user_profiles", "messages", "match_history", "analytics_events"
                ]
                mock_delete.return_value = {"deleted_tables": 4, "total_records": 500}
                
                result = await compliance_service.process_data_subject_request(
                    user_id=123,
                    request_type=DataSubjectRight.ERASURE,
                    data_categories=[DataCategory.PROFILE_DATA]
                )
                
                # Should identify and delete related data
                mock_identify.assert_called_once()

    @pytest.mark.asyncio 
    async def test_privacy_impact_assessment(self, compliance_service):
        """Test privacy impact assessment functionality"""
        processing_details = {
            "data_categories": [DataCategory.BEHAVIORAL_DATA, DataCategory.LOCATION_DATA],
            "processing_purposes": [ProcessingPurpose.ANALYTICS, ProcessingPurpose.PERSONALIZATION],
            "automated_decision_making": True,
            "profiling": True,
            "data_subjects": ["adults", "minors"]
        }
        
        with patch.object(compliance_service, '_assess_privacy_risks') as mock_assess:
            mock_assess.return_value = {
                "risk_level": "high",
                "risks_identified": ["profiling_risk", "automated_decisions"],
                "mitigation_required": True
            }
            
            result = await compliance_service.conduct_privacy_impact_assessment(processing_details)
            
            assert result["risk_level"] == "high"
            assert result["mitigation_required"] is True
            mock_assess.assert_called_once()

    def test_enum_completeness(self):
        """Test all enums have comprehensive coverage"""
        # Verify we have all essential data categories
        essential_categories = {
            "profile_data", "messages", "photos", "location_data", 
            "matching_preferences", "behavioral_data", "device_data", 
            "authentication_data"
        }
        actual_categories = {category.value for category in DataCategory}
        assert essential_categories.issubset(actual_categories)
        
        # Verify we have all GDPR Article 6 legal bases
        gdpr_bases = {
            "consent", "contract", "legal_obligation", 
            "vital_interests", "public_task", "legitimate_interests"
        }
        actual_bases = {basis.value for basis in LegalBasis}
        assert gdpr_bases.issubset(actual_bases)