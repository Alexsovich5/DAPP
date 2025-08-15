import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import uuid
from cryptography.fernet import Fernet
from app.services.privacy_analytics import (
    PrivacyCompliantAnalyticsService,
    ConsentType,
    DataRetentionPeriod,
    PrivacyLevel,
    UserConsent,
    DataRetentionPolicy,
    PrivacyAuditLog
)
class TestPrivacyCompliantAnalyticsService:
    
    @pytest.fixture
    def encryption_key(self):
        return Fernet.generate_key()
    
    @pytest.fixture
    def mock_clickhouse(self):
        return Mock()
    
    @pytest.fixture
    def mock_redis(self):
        mock_redis = Mock()
        mock_redis.hset = Mock()
        mock_redis.hget = Mock()
        mock_redis.hdel = Mock()
        mock_redis.expire = Mock()
        mock_redis.pipeline = Mock()
        return mock_redis
    
    @pytest.fixture
    def privacy_service(self, mock_clickhouse, mock_redis, encryption_key):
        return PrivacyCompliantAnalyticsService(mock_clickhouse, mock_redis, encryption_key)
    
    @pytest.fixture
    def sample_consent(self):
        return UserConsent(
            user_id=123,
            consent_id=str(uuid.uuid4()),
            consent_types=[ConsentType.ANALYTICS, ConsentType.PERSONALIZATION],
            granted_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=730),
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0 Test Browser",
            consent_version="v1.0",
            is_active=True
        )
    def test_service_initialization(self, privacy_service):
        """Test privacy service initialization"""
        assert privacy_service.clickhouse is not None
        assert privacy_service.redis is not None
        assert privacy_service.cipher is not None
        assert len(privacy_service.retention_policies) == 4
        assert len(privacy_service.privacy_level_permissions) == 3
    def test_retention_policies(self, privacy_service):
        """Test data retention policies are properly configured"""
        policies = privacy_service.retention_policies
        
        # Test user events policy
        user_events = policies["user_events"]
        assert user_events.retention_period == DataRetentionPeriod.ONE_YEAR
        assert user_events.anonymization_after == DataRetentionPeriod.SIX_MONTHS
        assert user_events.legal_basis == "legitimate_interest"
        
        # Test profile interactions policy
        profile_interactions = policies["profile_interactions"]
        assert profile_interactions.retention_period == DataRetentionPeriod.SIX_MONTHS
        assert profile_interactions.legal_basis == "consent"
        
        # Test business events policy
        business_events = policies["business_events"]
        assert business_events.retention_period == DataRetentionPeriod.TWO_YEARS
        assert business_events.anonymization_after is None
        assert business_events.legal_basis == "legal_obligation"
    def test_privacy_level_permissions(self, privacy_service):
        """Test privacy level permissions are properly configured"""
        permissions = privacy_service.privacy_level_permissions
        
        # Minimal level should only have functional consent
        assert permissions[PrivacyLevel.MINIMAL] == [ConsentType.FUNCTIONAL]
        
        # Standard level should include analytics and performance
        standard_perms = permissions[PrivacyLevel.STANDARD]
        assert ConsentType.FUNCTIONAL in standard_perms
        assert ConsentType.ANALYTICS in standard_perms
        assert ConsentType.PERFORMANCE in standard_perms
        
        # Enhanced level should include all consent types
        enhanced_perms = permissions[PrivacyLevel.ENHANCED]
        assert len(enhanced_perms) == 5
        assert ConsentType.MARKETING in enhanced_perms
        assert ConsentType.PERSONALIZATION in enhanced_perms
    @pytest.mark.asyncio
    async def test_record_user_consent_success(self, privacy_service, mock_redis):
        """Test successful user consent recording"""
        consent_types = [ConsentType.ANALYTICS, ConsentType.PERSONALIZATION]
        
        with patch.object(privacy_service, '_store_user_consent') as mock_store:
            with patch.object(privacy_service, '_update_user_privacy_level') as mock_update:
                with patch.object(privacy_service, '_log_privacy_action') as mock_log:
                    mock_store.return_value = None
                    mock_update.return_value = None
                    mock_log.return_value = None
                    
                    result = await privacy_service.record_user_consent(
                        123, consent_types, "192.168.1.1", "Mozilla/5.0"
                    )
                    
                    assert isinstance(result, str)
                    assert len(result) == 36  # UUID length
                    mock_store.assert_called_once()
                    mock_update.assert_called_once_with(123, consent_types)
                    mock_log.assert_called_once()
    @pytest.mark.asyncio
    async def test_record_user_consent_with_version(self, privacy_service):
        """Test recording user consent with specific version"""
        consent_types = [ConsentType.ANALYTICS]
        
        with patch.object(privacy_service, '_store_user_consent') as mock_store:
            with patch.object(privacy_service, '_update_user_privacy_level') as mock_update:
                with patch.object(privacy_service, '_log_privacy_action') as mock_log:
                    result = await privacy_service.record_user_consent(
                        123, consent_types, "192.168.1.1", "Mozilla/5.0", "v2.0"
                    )
                    
                    assert isinstance(result, str)
                    # Verify consent version was passed
                    call_args = mock_store.call_args[0][0]
                    assert call_args.consent_version == "v2.0"
    @pytest.mark.asyncio
    async def test_record_user_consent_error(self, privacy_service):
        """Test user consent recording error handling"""
        with patch.object(privacy_service, '_store_user_consent', side_effect=Exception("Store error")):
            with pytest.raises(Exception, match="Store error"):
                await privacy_service.record_user_consent(
                    123, [ConsentType.ANALYTICS], "192.168.1.1", "Mozilla/5.0"
                )
    @pytest.mark.asyncio
    async def test_revoke_user_consent_success(self, privacy_service, sample_consent):
        """Test successful consent revocation"""
        revoke_types = [ConsentType.PERSONALIZATION]
        
        with patch.object(privacy_service, '_get_user_consent', return_value=sample_consent):
            with patch.object(privacy_service, '_store_user_consent') as mock_store:
                with patch.object(privacy_service, '_update_user_privacy_level') as mock_update:
                    with patch.object(privacy_service, '_handle_consent_revocation') as mock_handle:
                        with patch.object(privacy_service, '_log_privacy_action') as mock_log:
                            result = await privacy_service.revoke_user_consent(123, revoke_types)
                            
                            assert result is True
                            mock_store.assert_called_once()
                            mock_update.assert_called_once()
                            mock_handle.assert_called_once_with(123, revoke_types)
                            mock_log.assert_called_once()
                            
                            # Verify consent types were updated
                            updated_consent = mock_store.call_args[0][0]
                            assert ConsentType.PERSONALIZATION not in updated_consent.consent_types
                            assert ConsentType.ANALYTICS in updated_consent.consent_types
    @pytest.mark.asyncio
    async def test_revoke_user_consent_no_existing_consent(self, privacy_service):
        """Test consent revocation when no existing consent"""
        with patch.object(privacy_service, '_get_user_consent', return_value=None):
            result = await privacy_service.revoke_user_consent(123, [ConsentType.ANALYTICS])
            
            assert result is False
    @pytest.mark.asyncio
    async def test_revoke_user_consent_error(self, privacy_service, sample_consent):
        """Test consent revocation error handling"""
        with patch.object(privacy_service, '_get_user_consent', return_value=sample_consent):
            with patch.object(privacy_service, '_store_user_consent', side_effect=Exception("Store error")):
                result = await privacy_service.revoke_user_consent(123, [ConsentType.ANALYTICS])
                
                assert result is False
    @pytest.mark.asyncio
    async def test_process_data_subject_request_access(self, privacy_service):
        """Test data subject access request"""
        mock_result = {"user_data": "test_data"}
        
        with patch.object(privacy_service, '_handle_data_access_request', return_value=mock_result):
            result = await privacy_service.process_data_subject_request(123, "access")
            
            assert result == mock_result
    @pytest.mark.asyncio
    async def test_process_data_subject_request_portability(self, privacy_service):
        """Test data portability request"""
        mock_result = {"export_data": "portable_format"}
        
        with patch.object(privacy_service, '_handle_data_portability_request', return_value=mock_result):
            result = await privacy_service.process_data_subject_request(123, "portability")
            
            assert result == mock_result
    @pytest.mark.asyncio
    async def test_process_data_subject_request_erasure(self, privacy_service):
        """Test data erasure request"""
        mock_result = {"deleted": True}
        
        with patch.object(privacy_service, '_handle_data_erasure_request', return_value=mock_result):
            result = await privacy_service.process_data_subject_request(123, "erasure")
            
            assert result == mock_result
    @pytest.mark.asyncio
    async def test_process_data_subject_request_rectification(self, privacy_service):
        """Test data rectification request"""
        mock_result = {"rectified": True}
        
        with patch.object(privacy_service, '_handle_data_rectification_request', return_value=mock_result):
            result = await privacy_service.process_data_subject_request(123, "rectification")
            
            assert result == mock_result
    @pytest.mark.asyncio
    async def test_process_data_subject_request_unknown_type(self, privacy_service):
        """Test data subject request with unknown type"""
        with pytest.raises(ValueError, match="Unknown request type"):
            await privacy_service.process_data_subject_request(123, "unknown_type")
    @pytest.mark.asyncio
    async def test_process_data_subject_request_error(self, privacy_service):
        """Test data subject request error handling"""
        with patch.object(privacy_service, '_handle_data_access_request', side_effect=Exception("Access error")):
            with pytest.raises(Exception, match="Access error"):
                await privacy_service.process_data_subject_request(123, "access")
    @pytest.mark.asyncio
    async def test_anonymize_user_data_success(self, privacy_service):
        """Test successful user data anonymization"""
        data_types = ["user_events", "profile_interactions"]
        
        with patch.object(privacy_service, '_generate_anonymous_id', return_value="anon_123"):
            with patch.object(privacy_service, '_anonymize_data_type') as mock_anonymize:
                with patch.object(privacy_service, '_log_privacy_action') as mock_log:
                    result = await privacy_service.anonymize_user_data(123, data_types)
                    
                    assert result is True
                    assert mock_anonymize.call_count == 2
                    mock_log.assert_called_once()
    @pytest.mark.asyncio
    async def test_anonymize_user_data_error(self, privacy_service):
        """Test user data anonymization error handling"""
        with patch.object(privacy_service, '_generate_anonymous_id', side_effect=Exception("Anonymization error")):
            result = await privacy_service.anonymize_user_data(123, ["user_events"])
            
            assert result is False
    @pytest.mark.asyncio
    async def test_check_data_processing_consent_valid(self, privacy_service, sample_consent):
        """Test checking valid data processing consent"""
        with patch.object(privacy_service, '_get_user_consent', return_value=sample_consent):
            result = await privacy_service.check_data_processing_consent(123, ConsentType.ANALYTICS)
            
            assert result is True
    @pytest.mark.asyncio
    async def test_check_data_processing_consent_invalid_type(self, privacy_service, sample_consent):
        """Test checking consent for type not granted"""
        with patch.object(privacy_service, '_get_user_consent', return_value=sample_consent):
            result = await privacy_service.check_data_processing_consent(123, ConsentType.MARKETING)
            
            assert result is False
    @pytest.mark.asyncio
    async def test_check_data_processing_consent_no_consent(self, privacy_service):
        """Test checking consent when no consent exists"""
        with patch.object(privacy_service, '_get_user_consent', return_value=None):
            result = await privacy_service.check_data_processing_consent(123, ConsentType.ANALYTICS)
            
            assert result is False
    @pytest.mark.asyncio
    async def test_check_data_processing_consent_inactive(self, privacy_service, sample_consent):
        """Test checking consent when consent is inactive"""
        sample_consent.is_active = False
        
        with patch.object(privacy_service, '_get_user_consent', return_value=sample_consent):
            result = await privacy_service.check_data_processing_consent(123, ConsentType.ANALYTICS)
            
            assert result is False
    @pytest.mark.asyncio
    async def test_check_data_processing_consent_expired(self, privacy_service, sample_consent):
        """Test checking consent when consent is expired"""
        sample_consent.expires_at = datetime.utcnow() - timedelta(days=1)
        
        with patch.object(privacy_service, '_get_user_consent', return_value=sample_consent):
            result = await privacy_service.check_data_processing_consent(123, ConsentType.ANALYTICS)
            
            assert result is False
    def test_consent_type_enum_values(self):
        """Test ConsentType enum values"""
        assert ConsentType.ANALYTICS.value == "analytics"
        assert ConsentType.PERSONALIZATION.value == "personalization"
        assert ConsentType.MARKETING.value == "marketing"
        assert ConsentType.PERFORMANCE.value == "performance"
        assert ConsentType.FUNCTIONAL.value == "functional"
    def test_data_retention_period_enum_values(self):
        """Test DataRetentionPeriod enum values"""
        assert DataRetentionPeriod.SEVEN_DAYS.value == 7
        assert DataRetentionPeriod.THIRTY_DAYS.value == 30
        assert DataRetentionPeriod.SIX_MONTHS.value == 180
        assert DataRetentionPeriod.ONE_YEAR.value == 365
        assert DataRetentionPeriod.TWO_YEARS.value == 730
    def test_privacy_level_enum_values(self):
        """Test PrivacyLevel enum values"""
        assert PrivacyLevel.MINIMAL.value == "minimal"
        assert PrivacyLevel.STANDARD.value == "standard"
        assert PrivacyLevel.ENHANCED.value == "enhanced"
    def test_user_consent_dataclass(self):
        """Test UserConsent dataclass"""
        consent = UserConsent(
            user_id=123,
            consent_id="test-id",
            consent_types=[ConsentType.ANALYTICS],
            granted_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=365),
            ip_address="192.168.1.1",
            user_agent="Test Browser",
            consent_version="v1.0"
        )
        
        assert consent.user_id == 123
        assert consent.consent_id == "test-id"
        assert len(consent.consent_types) == 1
        assert consent.is_active is True  # Default value
    def test_data_retention_policy_dataclass(self):
        """Test DataRetentionPolicy dataclass"""
        policy = DataRetentionPolicy(
            data_type="test_data",
            retention_period=DataRetentionPeriod.ONE_YEAR,
            anonymization_after=DataRetentionPeriod.SIX_MONTHS,
            deletion_criteria={"test": "criteria"},
            legal_basis="consent"
        )
        
        assert policy.data_type == "test_data"
        assert policy.retention_period == DataRetentionPeriod.ONE_YEAR
        assert policy.legal_basis == "consent"
    def test_privacy_audit_log_dataclass(self):
        """Test PrivacyAuditLog dataclass"""
        log = PrivacyAuditLog(
            audit_id="audit-123",
            user_id=123,
            action="consent_granted",
            data_type="user_consent",
            timestamp=datetime.utcnow(),
            details={"test": "details"},
            compliance_check=True
        )
        
        assert log.audit_id == "audit-123"
        assert log.action == "consent_granted"
        assert log.compliance_check is True
    @pytest.mark.asyncio
    async def test_encryption_functionality(self, privacy_service):
        """Test encryption and decryption functionality"""
        test_data = "sensitive user data"
        
        # Encrypt data
        encrypted = privacy_service.cipher.encrypt(test_data.encode())
        
        # Decrypt data
        decrypted = privacy_service.cipher.decrypt(encrypted).decode()
        
        assert decrypted == test_data
        assert encrypted != test_data.encode()
    @pytest.mark.asyncio
    async def test_gdpr_compliance_consent_expiry(self, privacy_service):
        """Test GDPR compliance - consent expires in 2 years"""
        consent_types = [ConsentType.ANALYTICS]
        
        with patch.object(privacy_service, '_store_user_consent') as mock_store:
            with patch.object(privacy_service, '_update_user_privacy_level'):
                with patch.object(privacy_service, '_log_privacy_action'):
                    await privacy_service.record_user_consent(
                        123, consent_types, "192.168.1.1", "Mozilla/5.0"
                    )
                    
                    stored_consent = mock_store.call_args[0][0]
                    expiry_days = (stored_consent.expires_at - stored_consent.granted_at).days
                    
                    # Should be 730 days (2 years) for GDPR compliance
                    assert expiry_days == 730
    def test_legal_basis_mapping(self, privacy_service):
        """Test legal basis mapping for different data types"""
        policies = privacy_service.retention_policies
        
        # Essential functionality should be based on legitimate interest
        assert policies["user_events"].legal_basis == "legitimate_interest"
        
        # Profile interactions should require consent
        assert policies["profile_interactions"].legal_basis == "consent"
        
        # Business records should be legal obligation
        assert policies["business_events"].legal_basis == "legal_obligation"
        
        # Message events should be contract basis
        assert policies["message_events"].legal_basis == "contract"
    @pytest.mark.asyncio
    async def test_consent_granularity(self, privacy_service):
        """Test granular consent management"""
        # User can grant individual consent types
        analytics_only = [ConsentType.ANALYTICS]
        result1 = await privacy_service.record_user_consent(
            123, analytics_only, "192.168.1.1", "Mozilla/5.0"
        )
        
        # User can grant multiple consent types
        multiple_consents = [ConsentType.ANALYTICS, ConsentType.PERSONALIZATION, ConsentType.MARKETING]
        
        with patch.object(privacy_service, '_store_user_consent'):
            with patch.object(privacy_service, '_update_user_privacy_level'):
                with patch.object(privacy_service, '_log_privacy_action'):
                    result2 = await privacy_service.record_user_consent(
                        456, multiple_consents, "192.168.1.2", "Mozilla/5.0"
                    )
        
        assert isinstance(result1, str)
        assert isinstance(result2, str)
    @pytest.mark.asyncio
    async def test_right_to_be_forgotten_compliance(self, privacy_service):
        """Test right to be forgotten (erasure) compliance"""
        with patch.object(privacy_service, '_handle_data_erasure_request') as mock_erasure:
            mock_erasure.return_value = {
                "status": "completed",
                "deleted_records": 150,
                "anonymized_records": 50
            }
            
            result = await privacy_service.process_data_subject_request(123, "erasure")
            
            assert result["status"] == "completed"
            mock_erasure.assert_called_once_with(123)
    @pytest.mark.asyncio
    async def test_data_portability_compliance(self, privacy_service):
        """Test data portability compliance"""
        with patch.object(privacy_service, '_handle_data_portability_request') as mock_portability:
            mock_portability.return_value = {
                "format": "JSON",
                "data": {"profile": {}, "messages": [], "interactions": []},
                "generated_at": datetime.utcnow().isoformat()
            }
            
            result = await privacy_service.process_data_subject_request(123, "portability")
            
            assert result["format"] == "JSON"
            assert "data" in result
            mock_portability.assert_called_once_with(123)
    @pytest.mark.asyncio
    async def test_privacy_level_escalation(self, privacy_service):
        """Test privacy level escalation based on consent"""
        # Minimal consent should result in minimal privacy level
        minimal_consent = [ConsentType.FUNCTIONAL]
        
        with patch.object(privacy_service, '_store_user_consent'):
            with patch.object(privacy_service, '_update_user_privacy_level') as mock_update:
                with patch.object(privacy_service, '_log_privacy_action'):
                    await privacy_service.record_user_consent(
                        123, minimal_consent, "192.168.1.1", "Mozilla/5.0"
                    )
                    
                    mock_update.assert_called_with(123, minimal_consent)
    @pytest.mark.asyncio
    async def test_audit_trail_completeness(self, privacy_service):
        """Test comprehensive audit trail"""
        with patch.object(privacy_service, '_store_user_consent'):
            with patch.object(privacy_service, '_update_user_privacy_level'):
                with patch.object(privacy_service, '_log_privacy_action') as mock_log:
                    # Record consent
                    await privacy_service.record_user_consent(
                        123, [ConsentType.ANALYTICS], "192.168.1.1", "Mozilla/5.0"
                    )
                    
                    # Check audit log was called
                    mock_log.assert_called_with(
                        123, "consent_granted", "user_consent",
                        {"consent_types": ["analytics"]}
                    )
    @pytest.mark.asyncio
    async def test_concurrent_consent_operations(self, privacy_service):
        """Test concurrent consent operations"""
        tasks = []
        
        # Simulate multiple consent operations
        for i in range(5):
            with patch.object(privacy_service, '_store_user_consent'):
                with patch.object(privacy_service, '_update_user_privacy_level'):
                    with patch.object(privacy_service, '_log_privacy_action'):
                        task = privacy_service.record_user_consent(
                            100 + i, [ConsentType.ANALYTICS], "192.168.1.1", "Mozilla/5.0"
                        )
                        tasks.append(task)
        
        # All operations should complete successfully
        results = await asyncio.gather(*tasks)
        assert len(results) == 5
        assert all(isinstance(result, str) for result in results)
    @pytest.mark.asyncio
    async def test_data_minimization_principle(self, privacy_service):
        """Test data minimization principle"""
        # Different privacy levels should have different data collection permissions
        minimal_perms = privacy_service.privacy_level_permissions[PrivacyLevel.MINIMAL]
        standard_perms = privacy_service.privacy_level_permissions[PrivacyLevel.STANDARD]
        enhanced_perms = privacy_service.privacy_level_permissions[PrivacyLevel.ENHANCED]
        
        # Minimal should be subset of standard, standard should be subset of enhanced
        assert set(minimal_perms).issubset(set(standard_perms))
        assert set(standard_perms).issubset(set(enhanced_perms))
        
        # Each level should progressively allow more data collection
        assert len(minimal_perms) < len(standard_perms) < len(enhanced_perms)
    @pytest.mark.asyncio
    async def test_consent_withdrawal_cascade(self, privacy_service, sample_consent):
        """Test consent withdrawal cascades to data handling"""
        revoke_types = [ConsentType.PERSONALIZATION]
        
        with patch.object(privacy_service, '_get_user_consent', return_value=sample_consent):
            with patch.object(privacy_service, '_store_user_consent'):
                with patch.object(privacy_service, '_update_user_privacy_level'):
                    with patch.object(privacy_service, '_handle_consent_revocation') as mock_handle:
                        with patch.object(privacy_service, '_log_privacy_action'):
                            result = await privacy_service.revoke_user_consent(123, revoke_types)
                            
                            assert result is True
                            # Should trigger data handling for revoked consent
                            mock_handle.assert_called_once_with(123, revoke_types)
    def test_retention_policy_consistency(self, privacy_service):
        """Test retention policy consistency and validity"""
        policies = privacy_service.retention_policies
        
        for policy_name, policy in policies.items():
            # All policies should have required fields
            assert policy.data_type == policy_name
            assert isinstance(policy.retention_period, DataRetentionPeriod)
            assert policy.legal_basis in ["consent", "legitimate_interest", "contract", "legal_obligation"]
            assert isinstance(policy.deletion_criteria, dict)
            
            # If anonymization is specified, it should be shorter than retention
            if policy.anonymization_after:
                assert policy.anonymization_after.value < policy.retention_period.value