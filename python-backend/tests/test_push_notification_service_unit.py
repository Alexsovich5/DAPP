"""
Unit tests for push notification service functionality
Tests notification sending, device management, and messaging without external dependencies
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from app.services.push_notification import (
    PushNotificationService,
    NotificationResult,
    NotificationChannel,
    NotificationPriority,
    DeviceType
)


@pytest.mark.unit
class TestPushNotificationService:
    """Test suite for PushNotificationService class"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def notification_service(self, mock_db):
        """Create PushNotificationService instance"""
        return PushNotificationService(mock_db)
    
    def test_service_initialization(self, notification_service, mock_db):
        """Test PushNotificationService initialization"""
        assert notification_service.db == mock_db
        assert hasattr(notification_service, 'fcm_client')
        assert hasattr(notification_service, 'apns_client')
    
    def test_validate_device_token_valid(self, notification_service):
        """Test device token validation with valid token"""
        valid_token = "a" * 64  # Valid FCM token length
        
        result = notification_service.validate_device_token(valid_token, DeviceType.ANDROID)
        
        assert result is True
    
    def test_validate_device_token_invalid(self, notification_service):
        """Test device token validation with invalid token"""
        invalid_tokens = [
            "",  # Empty
            "short",  # Too short
            None,  # None
            "a" * 200  # Too long
        ]
        
        for token in invalid_tokens:
            result = notification_service.validate_device_token(token, DeviceType.ANDROID)
            assert result is False
    
    def test_register_device_success(self, notification_service, mock_db):
        """Test successful device registration"""
        user_id = 123
        device_token = "valid_token_123456"
        device_type = DeviceType.ANDROID
        
        result = notification_service.register_device(user_id, device_token, device_type)
        
        assert result is True
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_register_device_invalid_token(self, notification_service, mock_db):
        """Test device registration with invalid token"""
        user_id = 123
        invalid_token = ""
        device_type = DeviceType.ANDROID
        
        result = notification_service.register_device(user_id, invalid_token, device_type)
        
        assert result is False
        mock_db.add.assert_not_called()
    
    def test_register_device_database_error(self, notification_service, mock_db):
        """Test device registration with database error"""
        user_id = 123
        device_token = "valid_token_123456"
        device_type = DeviceType.ANDROID
        
        mock_db.add.side_effect = Exception("Database error")
        mock_db.rollback = Mock()
        
        result = notification_service.register_device(user_id, device_token, device_type)
        
        assert result is False
        mock_db.rollback.assert_called_once()
    
    def test_unregister_device_success(self, notification_service, mock_db):
        """Test successful device unregistration"""
        device_token = "token_to_remove"
        
        # Mock finding the device
        mock_device = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_device
        
        result = notification_service.unregister_device(device_token)
        
        assert result is True
        mock_db.delete.assert_called_once_with(mock_device)
        mock_db.commit.assert_called_once()
    
    def test_unregister_device_not_found(self, notification_service, mock_db):
        """Test device unregistration when device not found"""
        device_token = "nonexistent_token"
        
        # Mock not finding the device
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = notification_service.unregister_device(device_token)
        
        assert result is False
        mock_db.delete.assert_not_called()
    
    def test_get_user_devices(self, notification_service, mock_db):
        """Test getting devices for a user"""
        user_id = 123
        
        # Mock user devices
        mock_devices = [Mock(), Mock()]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_devices
        
        devices = notification_service.get_user_devices(user_id)
        
        assert len(devices) == 2
        assert devices == mock_devices
    
    def test_get_user_devices_none_found(self, notification_service, mock_db):
        """Test getting devices when user has none"""
        user_id = 999
        
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        devices = notification_service.get_user_devices(user_id)
        
        assert isinstance(devices, list)
        assert len(devices) == 0
    
    @pytest.mark.asyncio
    async def test_send_notification_single_user_success(self, notification_service, mock_db):
        """Test sending notification to single user successfully"""
        user_id = 123
        title = "Test Notification"
        body = "This is a test"
        
        # Mock user device
        mock_device = Mock()
        mock_device.token = "device_token_123"
        mock_device.device_type = DeviceType.ANDROID
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_device]
        
        # Mock FCM client
        with patch.object(notification_service, '_send_fcm_notification', new_callable=AsyncMock) as mock_fcm:
            mock_fcm.return_value = NotificationResult(success=True, message="Sent")
            
            result = await notification_service.send_notification(user_id, title, body)
        
        assert result.success is True
        assert result.sent_count == 1
        assert result.failed_count == 0
    
    @pytest.mark.asyncio
    async def test_send_notification_no_devices(self, notification_service, mock_db):
        """Test sending notification when user has no devices"""
        user_id = 123
        title = "Test Notification"
        body = "This is a test"
        
        # Mock no devices
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = await notification_service.send_notification(user_id, title, body)
        
        assert result.success is False
        assert result.sent_count == 0
        assert "No devices" in result.message
    
    @pytest.mark.asyncio
    async def test_send_notification_multiple_devices(self, notification_service, mock_db):
        """Test sending notification to user with multiple devices"""
        user_id = 123
        title = "Test Notification"
        body = "This is a test"
        
        # Mock multiple devices
        mock_android_device = Mock()
        mock_android_device.token = "android_token"
        mock_android_device.device_type = DeviceType.ANDROID
        
        mock_ios_device = Mock()
        mock_ios_device.token = "ios_token"
        mock_ios_device.device_type = DeviceType.IOS
        
        mock_db.query.return_value.filter.return_value.all.return_value = [
            mock_android_device, mock_ios_device
        ]
        
        # Mock both FCM and APNS
        with patch.object(notification_service, '_send_fcm_notification', new_callable=AsyncMock) as mock_fcm, \
             patch.object(notification_service, '_send_apns_notification', new_callable=AsyncMock) as mock_apns:
            
            mock_fcm.return_value = NotificationResult(success=True, message="FCM sent")
            mock_apns.return_value = NotificationResult(success=True, message="APNS sent")
            
            result = await notification_service.send_notification(user_id, title, body)
        
        assert result.success is True
        assert result.sent_count == 2
        assert result.failed_count == 0
    
    @pytest.mark.asyncio
    async def test_send_notification_partial_failure(self, notification_service, mock_db):
        """Test sending notification with partial failures"""
        user_id = 123
        title = "Test Notification"
        body = "This is a test"
        
        # Mock two devices
        mock_device1 = Mock()
        mock_device1.token = "token1"
        mock_device1.device_type = DeviceType.ANDROID
        
        mock_device2 = Mock()
        mock_device2.token = "token2"
        mock_device2.device_type = DeviceType.ANDROID
        
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_device1, mock_device2]
        
        with patch.object(notification_service, '_send_fcm_notification', new_callable=AsyncMock) as mock_fcm:
            # First succeeds, second fails
            mock_fcm.side_effect = [
                NotificationResult(success=True, message="Sent"),
                NotificationResult(success=False, message="Failed")
            ]
            
            result = await notification_service.send_notification(user_id, title, body)
        
        assert result.sent_count == 1
        assert result.failed_count == 1
        assert result.success is False  # Partial failure
    
    @pytest.mark.asyncio
    async def test_send_fcm_notification_success(self, notification_service):
        """Test FCM notification sending success"""
        token = "fcm_token_123"
        title = "Test Title"
        body = "Test Body"
        data = {"key": "value"}
        
        with patch('pyfcm.FCMNotification') as mock_fcm_class:
            mock_fcm_instance = Mock()
            mock_fcm_class.return_value = mock_fcm_instance
            mock_fcm_instance.notify_single_device.return_value = {
                'success': 1,
                'failure': 0,
                'canonical_ids': 0,
                'results': [{'message_id': '123'}]
            }
            
            result = await notification_service._send_fcm_notification(token, title, body, data)
        
        assert result.success is True
        assert "successfully" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_send_fcm_notification_failure(self, notification_service):
        """Test FCM notification sending failure"""
        token = "invalid_token"
        title = "Test Title"
        body = "Test Body"
        
        with patch('pyfcm.FCMNotification') as mock_fcm_class:
            mock_fcm_instance = Mock()
            mock_fcm_class.return_value = mock_fcm_instance
            mock_fcm_instance.notify_single_device.return_value = {
                'success': 0,
                'failure': 1,
                'results': [{'error': 'InvalidRegistration'}]
            }
            
            result = await notification_service._send_fcm_notification(token, title, body)
        
        assert result.success is False
        assert "failed" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_send_fcm_notification_exception(self, notification_service):
        """Test FCM notification with exception"""
        token = "token_123"
        title = "Test Title"
        body = "Test Body"
        
        with patch('pyfcm.FCMNotification') as mock_fcm_class:
            mock_fcm_instance = Mock()
            mock_fcm_class.return_value = mock_fcm_instance
            mock_fcm_instance.notify_single_device.side_effect = Exception("Network error")
            
            result = await notification_service._send_fcm_notification(token, title, body)
        
        assert result.success is False
        assert "error" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_send_apns_notification_success(self, notification_service):
        """Test APNS notification sending success"""
        token = "apns_token_123"
        title = "Test Title"
        body = "Test Body"
        data = {"key": "value"}
        
        with patch('aioapns.APNs') as mock_apns_class:
            mock_apns_instance = Mock()
            mock_apns_class.return_value = mock_apns_instance
            mock_apns_instance.send_notification = AsyncMock()
            
            result = await notification_service._send_apns_notification(token, title, body, data)
        
        assert result.success is True
        mock_apns_instance.send_notification.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_apns_notification_exception(self, notification_service):
        """Test APNS notification with exception"""
        token = "token_123"
        title = "Test Title"
        body = "Test Body"
        
        with patch('aioapns.APNs') as mock_apns_class:
            mock_apns_instance = Mock()
            mock_apns_class.return_value = mock_apns_instance
            mock_apns_instance.send_notification = AsyncMock(side_effect=Exception("APNS error"))
            
            result = await notification_service._send_apns_notification(token, title, body)
        
        assert result.success is False
        assert "error" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_send_bulk_notification(self, notification_service, mock_db):
        """Test sending bulk notifications to multiple users"""
        user_ids = [123, 456, 789]
        title = "Bulk Notification"
        body = "This is sent to everyone"
        
        # Mock devices for each user
        for i, user_id in enumerate(user_ids):
            mock_device = Mock()
            mock_device.token = f"token_{user_id}"
            mock_device.device_type = DeviceType.ANDROID
            
            # Mock database query per user
            mock_query = Mock()
            mock_query.filter.return_value.all.return_value = [mock_device]
            
            if i == 0:
                mock_db.query.return_value = mock_query
            else:
                mock_db.query.return_value = mock_query
        
        with patch.object(notification_service, 'send_notification', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = NotificationResult(success=True, sent_count=1, failed_count=0)
            
            results = await notification_service.send_bulk_notification(user_ids, title, body)
        
        assert len(results) == len(user_ids)
        assert mock_send.call_count == len(user_ids)
    
    def test_create_notification_payload_basic(self, notification_service):
        """Test creating basic notification payload"""
        title = "Test Title"
        body = "Test Body"
        
        payload = notification_service.create_notification_payload(title, body)
        
        assert payload['title'] == title
        assert payload['body'] == body
        assert 'data' in payload
        assert 'priority' in payload
    
    def test_create_notification_payload_with_data(self, notification_service):
        """Test creating notification payload with custom data"""
        title = "Test Title"
        body = "Test Body"
        custom_data = {"user_id": 123, "type": "message"}
        
        payload = notification_service.create_notification_payload(title, body, data=custom_data)
        
        assert payload['title'] == title
        assert payload['body'] == body
        assert payload['data'] == custom_data
    
    def test_create_notification_payload_high_priority(self, notification_service):
        """Test creating high priority notification payload"""
        title = "Urgent"
        body = "This is urgent"
        
        payload = notification_service.create_notification_payload(
            title, body, priority=NotificationPriority.HIGH
        )
        
        assert payload['priority'] == NotificationPriority.HIGH.value
    
    def test_format_notification_for_channel(self, notification_service):
        """Test formatting notification for different channels"""
        base_payload = {
            'title': 'Test',
            'body': 'Message',
            'data': {'key': 'value'}
        }
        
        # Test FCM formatting
        fcm_payload = notification_service.format_notification_for_channel(
            base_payload, NotificationChannel.FCM
        )
        assert 'notification' in fcm_payload
        assert 'data' in fcm_payload
        
        # Test APNS formatting
        apns_payload = notification_service.format_notification_for_channel(
            base_payload, NotificationChannel.APNS
        )
        assert 'aps' in apns_payload
        assert 'alert' in apns_payload['aps']
    
    def test_should_send_notification_user_preferences(self, notification_service, mock_db):
        """Test notification sending based on user preferences"""
        user_id = 123
        notification_type = "message"
        
        # Mock user preferences allowing notifications
        mock_user = Mock()
        mock_user.notification_preferences = {"messages": True}
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        should_send = notification_service.should_send_notification(user_id, notification_type)
        
        assert should_send is True
    
    def test_should_send_notification_user_disabled(self, notification_service, mock_db):
        """Test notification not sent when user disabled them"""
        user_id = 123
        notification_type = "message"
        
        # Mock user preferences disallowing notifications
        mock_user = Mock()
        mock_user.notification_preferences = {"messages": False}
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        should_send = notification_service.should_send_notification(user_id, notification_type)
        
        assert should_send is False
    
    def test_should_send_notification_no_user(self, notification_service, mock_db):
        """Test notification handling when user not found"""
        user_id = 999
        notification_type = "message"
        
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        should_send = notification_service.should_send_notification(user_id, notification_type)
        
        assert should_send is False
    
    def test_log_notification_sent(self, notification_service, mock_db):
        """Test logging sent notification"""
        user_id = 123
        title = "Test"
        body = "Message"
        success = True
        
        notification_service.log_notification(user_id, title, body, success)
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_log_notification_failed(self, notification_service, mock_db):
        """Test logging failed notification"""
        user_id = 123
        title = "Test"
        body = "Message"
        success = False
        
        notification_service.log_notification(user_id, title, body, success)
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_get_notification_history(self, notification_service, mock_db):
        """Test getting notification history for user"""
        user_id = 123
        
        mock_notifications = [Mock(), Mock(), Mock()]
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_notifications
        
        history = notification_service.get_notification_history(user_id, limit=10)
        
        assert len(history) == 3
        assert history == mock_notifications
    
    def test_cleanup_expired_tokens(self, notification_service, mock_db):
        """Test cleanup of expired device tokens"""
        cutoff_date = datetime.utcnow()
        
        # Mock expired tokens
        mock_db.query.return_value.filter.return_value.delete.return_value = 5
        
        deleted_count = notification_service.cleanup_expired_tokens(cutoff_date)
        
        assert deleted_count == 5
        mock_db.commit.assert_called_once()


@pytest.mark.unit
class TestNotificationResult:
    """Test suite for NotificationResult class"""
    
    def test_notification_result_success(self):
        """Test NotificationResult for successful notification"""
        result = NotificationResult(
            success=True,
            message="Notification sent successfully",
            sent_count=1,
            failed_count=0
        )
        
        assert result.success is True
        assert result.sent_count == 1
        assert result.failed_count == 0
        assert "successfully" in result.message
    
    def test_notification_result_failure(self):
        """Test NotificationResult for failed notification"""
        result = NotificationResult(
            success=False,
            message="Failed to send notification",
            sent_count=0,
            failed_count=1
        )
        
        assert result.success is False
        assert result.sent_count == 0
        assert result.failed_count == 1
        assert "failed" in result.message.lower()


@pytest.mark.unit
class TestNotificationEnums:
    """Test suite for notification enums"""
    
    def test_notification_channel_values(self):
        """Test NotificationChannel enum values"""
        assert NotificationChannel.FCM.value == "fcm"
        assert NotificationChannel.APNS.value == "apns"
        assert NotificationChannel.WEB_PUSH.value == "web_push"
    
    def test_notification_priority_values(self):
        """Test NotificationPriority enum values"""
        assert NotificationPriority.LOW.value == "low"
        assert NotificationPriority.NORMAL.value == "normal"
        assert NotificationPriority.HIGH.value == "high"
    
    def test_device_type_values(self):
        """Test DeviceType enum values"""
        assert DeviceType.ANDROID.value == "android"
        assert DeviceType.IOS.value == "ios"
        assert DeviceType.WEB.value == "web"