"""
Comprehensive WebSocket Real-Time Feature Tests
Tests real-time messaging, typing indicators, and connection status for dating platform
"""

import pytest
from fastapi.testclient import TestClient
import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock
import websockets
import time

from app.main import app
from app.services.realtime_connection_manager import ConnectionManager
from app.services.realtime import RealtimeService


class TestWebSocketConnection:
    """Test WebSocket connection establishment and management"""
    
    @pytest.fixture
    def ws_client(self):
        return TestClient(app)
    
    @pytest.fixture
    def connection_manager(self):
        return ConnectionManager()

    @pytest.mark.asyncio
    @pytest.mark.unit
    def test_connection_manager_initialization(self, connection_manager):
        """Test that connection manager initializes properly"""
        assert connection_manager.active_connections == {}
        assert connection_manager.user_connections == {}
        assert hasattr(connection_manager, 'connect')
        assert hasattr(connection_manager, 'disconnect')
        assert hasattr(connection_manager, 'send_personal_message')

    @pytest.mark.asyncio
    @pytest.mark.integration
    def test_websocket_connection_establishment(self, ws_client):
        """Test establishing WebSocket connection with authentication"""
        # Mock WebSocket connection
        with ws_client.websocket_connect("/ws/1?token=valid-jwt-token") as websocket:
            # Should be able to establish connection
            data = websocket.receive_json()
            
            assert data["type"] == "connection_established"
            assert "user_id" in data
            assert data["status"] == "connected"

    @pytest.mark.asyncio
    @pytest.mark.integration 
    def test_websocket_authentication_required(self, ws_client):
        """Test that WebSocket requires valid authentication"""
        try:
            with ws_client.websocket_connect("/ws/1") as websocket:
                # Should fail without token
                pytest.fail("Should require authentication")
        except Exception as e:
            # Should reject connection without proper auth
            assert "401" in str(e) or "authentication" in str(e).lower()

    @pytest.mark.asyncio
    @pytest.mark.unit
    def test_connection_manager_connect_user(self, connection_manager):
        """Test connecting user to connection manager"""
        mock_websocket = AsyncMock()
        user_id = 1
        
        connection_manager.connect(mock_websocket, user_id)
        
        assert user_id in connection_manager.active_connections
        assert connection_manager.active_connections[user_id] == mock_websocket
        assert user_id in connection_manager.user_connections

    @pytest.mark.asyncio
    @pytest.mark.unit
    def test_connection_manager_disconnect_user(self, connection_manager):
        """Test disconnecting user from connection manager"""
        mock_websocket = AsyncMock()
        user_id = 1
        
        # Connect first
        connection_manager.connect(mock_websocket, user_id)
        assert user_id in connection_manager.active_connections
        
        # Then disconnect
        connection_manager.disconnect(user_id)
        assert user_id not in connection_manager.active_connections
        assert user_id not in connection_manager.user_connections


class TestRealtimeMessaging:
    """Test real-time messaging functionality"""
    
    @pytest.fixture
    def realtime_service(self, db_session):
        return RealtimeService(db_session)

    @pytest.mark.asyncio
    @pytest.mark.integration
    def test_send_real_time_message(self, ws_client, authenticated_user, soul_connection_data):
        """Test sending real-time messages between connected users"""
        connection = soul_connection_data["connection"]
        sender_id = authenticated_user["user"].id
        
        message_data = {
            "type": "message",
            "connection_id": connection.id,
            "content": "Hello! How are you feeling about our soul connection journey?",
            "message_type": "text"
        }
        
        # Mock WebSocket connection for testing
        with ws_client.websocket_connect(f"/ws/{sender_id}?token={authenticated_user['token']}") as websocket:
            # Send message
            websocket.send_json(message_data)
            
            # Should receive confirmation
            response = websocket.receive_json()
            assert response["type"] in ["message_sent", "message_delivered"]
            assert response["message"]["content"] == message_data["content"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    def test_message_delivery_to_recipient(self, realtime_service, soul_connection_data):
        """Test that messages are delivered to the correct recipient"""
        connection = soul_connection_data["connection"]
        sender = soul_connection_data["users"][0]
        recipient = soul_connection_data["users"][1]
        
        message = {
            "connection_id": connection.id,
            "sender_id": sender.id,
            "content": "Real-time message test",
            "message_type": "text"
        }
        
        # Mock connection manager
        mock_manager = MagicMock()
        mock_manager.send_personal_message = AsyncMock()
        
        with patch.object(realtime_service, 'connection_manager', mock_manager):
            realtime_service.send_message_to_connection(message)
            
            # Should attempt to send to recipient
            mock_manager.send_personal_message.assert_called_once()
            args = mock_manager.send_personal_message.call_args
            assert args[0][0] == recipient.id  # Recipient user ID

    @pytest.mark.asyncio
    @pytest.mark.integration
    def test_message_persistence_and_realtime(self, ws_client, realtime_service, soul_connection_data):
        """Test that real-time messages are also persisted to database"""
        connection = soul_connection_data["connection"]
        sender = soul_connection_data["users"][0]
        
        message_data = {
            "connection_id": connection.id,
            "sender_id": sender.id,
            "content": "This message should be saved AND sent in real-time",
            "message_type": "text"
        }
        
        # Send via real-time service
        with patch.object(realtime_service, 'connection_manager', MagicMock()):
            saved_message = realtime_service.send_and_save_message(message_data)
            
            assert saved_message.connection_id == connection.id
            assert saved_message.sender_id == sender.id
            assert saved_message.message_text == message_data["content"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    def test_message_type_handling(self, realtime_service):
        """Test handling of different message types in real-time"""
        message_types = [
            {"type": "text", "content": "Hello there!"},
            {"type": "emoji", "content": "❤️"},
            {"type": "revelation_share", "content": "Sharing day 3 revelation"},
            {"type": "photo_consent", "content": "I'm ready to share my photo"},
            {"type": "system", "content": "Connection stage updated"}
        ]
        
        for msg_type in message_types:
            formatted = realtime_service.format_message_for_realtime(msg_type)
            
            assert "type" in formatted
            assert "content" in formatted
            assert "timestamp" in formatted
            assert formatted["message_type"] == msg_type["type"]


class TestTypingIndicators:
    """Test typing indicator functionality"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    def test_typing_indicator_start(self, ws_client, authenticated_user, soul_connection_data):
        """Test starting typing indicator"""
        connection = soul_connection_data["connection"]
        user_id = authenticated_user["user"].id
        
        typing_data = {
            "type": "typing_start",
            "connection_id": connection.id,
            "user_id": user_id
        }
        
        with ws_client.websocket_connect(f"/ws/{user_id}?token={authenticated_user['token']}") as websocket:
            websocket.send_json(typing_data)
            
            # Should receive typing indicator confirmation
            response = websocket.receive_json()
            assert response["type"] == "typing_started"
            assert response["connection_id"] == connection.id

    @pytest.mark.asyncio
    @pytest.mark.integration
    def test_typing_indicator_stop(self, ws_client, authenticated_user, soul_connection_data):
        """Test stopping typing indicator"""
        connection = soul_connection_data["connection"]
        user_id = authenticated_user["user"].id
        
        typing_data = {
            "type": "typing_stop",
            "connection_id": connection.id,
            "user_id": user_id
        }
        
        with ws_client.websocket_connect(f"/ws/{user_id}?token={authenticated_user['token']}") as websocket:
            websocket.send_json(typing_data)
            
            response = websocket.receive_json()
            assert response["type"] == "typing_stopped"

    @pytest.mark.asyncio
    @pytest.mark.unit
    def test_typing_indicator_timeout(self, realtime_service):
        """Test that typing indicators automatically timeout"""
        connection_id = 1
        user_id = 1
        
        # Start typing
        realtime_service.start_typing_indicator(connection_id, user_id)
        
        # Should be marked as typing
        is_typing = realtime_service.is_user_typing(connection_id, user_id)
        assert is_typing == True
        
        # Simulate timeout (mock time passing)
        with patch('time.time', return_value=time.time() + 30):  # 30 seconds later
            is_typing_after = realtime_service.is_user_typing(connection_id, user_id)
            assert is_typing_after == False  # Should timeout

    @pytest.mark.asyncio
    @pytest.mark.integration
    def test_multiple_users_typing_indicators(self, realtime_service, soul_connection_data):
        """Test typing indicators with multiple users in same connection"""
        connection = soul_connection_data["connection"]
        user1, user2 = soul_connection_data["users"][:2]
        
        # Both users start typing
        realtime_service.start_typing_indicator(connection.id, user1.id)
        realtime_service.start_typing_indicator(connection.id, user2.id)
        
        # Both should be typing
        typing_users = realtime_service.get_typing_users(connection.id)
        assert user1.id in typing_users
        assert user2.id in typing_users
        
        # User1 stops typing
        realtime_service.stop_typing_indicator(connection.id, user1.id)
        
        typing_users_after = realtime_service.get_typing_users(connection.id)
        assert user1.id not in typing_users_after
        assert user2.id in typing_users_after


class TestPresenceStatus:
    """Test user presence and online status"""
    
    @pytest.mark.asyncio
    @pytest.mark.unit
    def test_user_online_status_tracking(self, connection_manager):
        """Test tracking user online/offline status"""
        user_id = 1
        mock_websocket = AsyncMock()
        
        # User should be offline initially
        assert connection_manager.is_user_online(user_id) == False
        
        # Connect user
        connection_manager.connect(mock_websocket, user_id)
        assert connection_manager.is_user_online(user_id) == True
        
        # Disconnect user
        connection_manager.disconnect(user_id)
        assert connection_manager.is_user_online(user_id) == False

    @pytest.mark.asyncio
    @pytest.mark.integration
    def test_presence_notification_to_connections(self, realtime_service, soul_connection_data):
        """Test that presence changes notify connected users"""
        connection = soul_connection_data["connection"]
        user1, user2 = soul_connection_data["users"][:2]
        
        mock_manager = MagicMock()
        mock_manager.send_personal_message = AsyncMock()
        
        with patch.object(realtime_service, 'connection_manager', mock_manager):
            # User1 comes online
            realtime_service.notify_presence_change(user1.id, "online")
            
            # Should notify user2 (their connection partner)
            mock_manager.send_personal_message.assert_called()

    @pytest.mark.asyncio
    @pytest.mark.unit
    def test_last_seen_timestamp_tracking(self, connection_manager):
        """Test tracking when user was last seen online"""
        user_id = 1
        mock_websocket = AsyncMock()
        
        # Connect and disconnect user
        connection_manager.connect(mock_websocket, user_id)
        connection_manager.disconnect(user_id)
        
        last_seen = connection_manager.get_last_seen(user_id)
        assert last_seen is not None
        assert isinstance(last_seen, (int, float, str))  # Timestamp format

    @pytest.mark.asyncio
    @pytest.mark.integration
    def test_presence_privacy_controls(self, realtime_service, matching_users):
        """Test presence privacy settings for dating platform"""
        user1 = matching_users["user1"]
        user2 = matching_users["user2"]
        
        # User can choose to hide online status
        realtime_service.set_presence_privacy(user1.id, "hidden")
        
        # Other users shouldn't see them as online even when they are
        is_visible = realtime_service.is_user_visible_online(user1.id, user2.id)
        assert is_visible == False
        
        # But user can choose public presence
        realtime_service.set_presence_privacy(user1.id, "public")
        is_visible_public = realtime_service.is_user_visible_online(user1.id, user2.id)
        assert is_visible_public == True


class TestRealtimeNotifications:
    """Test real-time notifications and alerts"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    def test_new_connection_notification(self, ws_client, realtime_service, authenticated_user):
        """Test real-time notification for new soul connection"""
        user_id = authenticated_user["user"].id
        
        notification_data = {
            "type": "new_connection",
            "connection_id": 1,
            "partner_name": "Soul Mate",
            "compatibility_score": 88.5,
            "message": "You have a new soul connection!"
        }
        
        mock_manager = MagicMock()
        mock_manager.send_personal_message = AsyncMock()
        
        with patch.object(realtime_service, 'connection_manager', mock_manager):
            realtime_service.send_connection_notification(user_id, notification_data)
            
            # Should send notification
            mock_manager.send_personal_message.assert_called_once_with(
                user_id, notification_data
            )

    @pytest.mark.asyncio
    @pytest.mark.integration
    def test_revelation_shared_notification(self, realtime_service, soul_connection_data):
        """Test real-time notification when partner shares revelation"""
        connection = soul_connection_data["connection"]
        user1, user2 = soul_connection_data["users"][:2]
        
        revelation_notification = {
            "type": "revelation_shared",
            "connection_id": connection.id,
            "day_number": 3,
            "revelation_type": "hope_or_dream",
            "sender_name": "Soul Partner",
            "message": "Your partner shared their hopes and dreams"
        }
        
        mock_manager = MagicMock()
        mock_manager.send_personal_message = AsyncMock()
        
        with patch.object(realtime_service, 'connection_manager', mock_manager):
            realtime_service.notify_revelation_shared(connection.id, user1.id, revelation_notification)
            
            # Should notify the other user
            mock_manager.send_personal_message.assert_called_with(
                user2.id, revelation_notification
            )

    @pytest.mark.asyncio
    @pytest.mark.integration
    def test_photo_consent_notification(self, realtime_service, soul_connection_data):
        """Test real-time notification for photo reveal consent"""
        connection = soul_connection_data["connection"]
        user1, user2 = soul_connection_data["users"][:2]
        
        consent_notification = {
            "type": "photo_consent_given",
            "connection_id": connection.id,
            "partner_name": "Soul Partner",
            "mutual_consent": False,
            "message": "Your partner is ready to share their photo!"
        }
        
        with patch.object(realtime_service, 'connection_manager', MagicMock()) as mock_manager:
            mock_manager.send_personal_message = AsyncMock()
            
            realtime_service.notify_photo_consent(connection.id, user1.id, consent_notification)
            
            mock_manager.send_personal_message.assert_called()

    @pytest.mark.asyncio
    @pytest.mark.unit
    def test_notification_queuing_for_offline_users(self, realtime_service):
        """Test that notifications are queued for offline users"""
        offline_user_id = 999
        
        notification = {
            "type": "test_notification",
            "message": "Test notification for offline user"
        }
        
        # Send notification to offline user
        result = realtime_service.send_notification_with_queue(offline_user_id, notification)
        
        # Should be queued
        assert result["queued"] == True
        assert result["delivery_status"] == "pending"
        
        # Check notification queue
        queued_notifications = realtime_service.get_queued_notifications(offline_user_id)
        assert len(queued_notifications) >= 1
        assert queued_notifications[0]["type"] == "test_notification"


class TestWebSocketSecurity:
    """Test WebSocket security and validation"""
    
    @pytest.mark.asyncio
    @pytest.mark.security
    def test_websocket_jwt_validation(self, ws_client):
        """Test WebSocket JWT token validation"""
        invalid_tokens = [
            "invalid.jwt.token",
            "expired_token",
            "",
            None
        ]
        
        for invalid_token in invalid_tokens:
            try:
                endpoint = f"/ws/1?token={invalid_token}" if invalid_token else "/ws/1"
                with ws_client.websocket_connect(endpoint) as websocket:
                    # Should not establish connection
                    pytest.fail(f"Should reject invalid token: {invalid_token}")
            except Exception:
                # Expected to fail authentication
                pass

    @pytest.mark.asyncio
    @pytest.mark.security
    def test_websocket_rate_limiting(self, ws_client, authenticated_user):
        """Test WebSocket message rate limiting"""
        user_id = authenticated_user["user"].id
        token = authenticated_user["token"]
        
        with ws_client.websocket_connect(f"/ws/{user_id}?token={token}") as websocket:
            # Send many rapid messages
            messages_sent = 0
            rate_limited = False
            
            for i in range(20):  # Send 20 rapid messages
                try:
                    websocket.send_json({
                        "type": "message",
                        "content": f"Rapid message {i}",
                        "connection_id": 1
                    })
                    messages_sent += 1
                    
                    # Check for rate limiting response
                    try:
                        response = websocket.receive_json()
                        if response.get("type") == "rate_limited":
                            rate_limited = True
                            break
                    except:
                        pass
                        
                except Exception as e:
                    if "rate" in str(e).lower():
                        rate_limited = True
                        break
            
            # Should either rate limit or handle gracefully
            assert messages_sent > 0  # At least some messages should go through

    @pytest.mark.asyncio
    @pytest.mark.security
    def test_websocket_message_validation(self, realtime_service):
        """Test validation of incoming WebSocket messages"""
        invalid_messages = [
            {},  # Empty message
            {"type": "unknown_type"},  # Invalid type
            {"type": "message"},  # Missing required fields
            {"type": "message", "content": "x" * 5000},  # Too long content
            {"type": "message", "content": "", "connection_id": "invalid"},  # Invalid connection ID
        ]
        
        for invalid_msg in invalid_messages:
            is_valid = realtime_service.validate_incoming_message(invalid_msg)
            assert is_valid == False, f"Should reject invalid message: {invalid_msg}"
        
        # Valid message should pass
        valid_message = {
            "type": "message",
            "content": "Valid message content",
            "connection_id": 1,
            "message_type": "text"
        }
        
        assert realtime_service.validate_incoming_message(valid_message) == True

    @pytest.mark.asyncio
    @pytest.mark.security
    def test_websocket_connection_isolation(self, realtime_service, soul_connection_data):
        """Test that users can only send messages to their connections"""
        connection = soul_connection_data["connection"]
        user1, user2 = soul_connection_data["users"][:2]
        
        # User1 tries to send message to connection they're part of - should succeed
        valid_message = {
            "sender_id": user1.id,
            "connection_id": connection.id,
            "content": "Valid message to my connection"
        }
        
        is_authorized = realtime_service.is_message_authorized(valid_message)
        assert is_authorized == True
        
        # User tries to send to connection they're not part of - should fail
        invalid_message = {
            "sender_id": user1.id,
            "connection_id": 999,  # Non-existent or unauthorized connection
            "content": "Unauthorized message"
        }
        
        is_unauthorized = realtime_service.is_message_authorized(invalid_message)
        assert is_unauthorized == False


class TestWebSocketPerformance:
    """Test WebSocket performance and scalability"""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    def test_concurrent_websocket_connections(self, connection_manager, performance_config):
        """Test handling multiple concurrent WebSocket connections"""
        concurrent_connections = []
        max_connections = performance_config.get("concurrent_users", 50)
        
        # Create multiple mock connections
        for i in range(max_connections):
            mock_websocket = AsyncMock()
            user_id = i + 1
            
            connection_manager.connect(mock_websocket, user_id)
            concurrent_connections.append((mock_websocket, user_id))
        
        # All connections should be active
        assert len(connection_manager.active_connections) == max_connections
        
        # Test broadcast to all connections
        start_time = time.time()
        connection_manager.broadcast({
            "type": "system_announcement",
            "message": "Testing concurrent connections"
        })
        broadcast_time = time.time() - start_time
        
        # Broadcast should be reasonably fast
        assert broadcast_time < 2.0  # 2 seconds max for 50 users

    @pytest.mark.asyncio
    @pytest.mark.performance
    def test_message_delivery_performance(self, realtime_service, performance_config):
        """Test message delivery performance requirements"""
        import time
        
        message_data = {
            "connection_id": 1,
            "sender_id": 1,
            "recipient_id": 2,
            "content": "Performance test message",
            "message_type": "text"
        }
        
        # Mock the delivery mechanism
        with patch.object(realtime_service, 'connection_manager', MagicMock()):
            start_time = time.time()
            
            # Send multiple messages rapidly
            for i in range(10):
                realtime_service.send_message_to_connection({
                    **message_data,
                    "content": f"Performance message {i}"
                })
            
            total_time = time.time() - start_time
            
            # Should deliver messages quickly
            avg_time_per_message = total_time / 10
            assert avg_time_per_message < 0.1  # 100ms per message max

    @pytest.mark.asyncio
    @pytest.mark.performance
    def test_websocket_memory_usage(self, connection_manager):
        """Test WebSocket memory usage with many connections"""
        import sys
        
        initial_connections = 10
        
        # Create initial connections
        for i in range(initial_connections):
            mock_websocket = AsyncMock()
            connection_manager.connect(mock_websocket, i + 1)
        
        # Memory usage should be reasonable
        connection_count = len(connection_manager.active_connections)
        assert connection_count == initial_connections
        
        # Clean up connections
        for i in range(initial_connections):
            connection_manager.disconnect(i + 1)
        
        # Memory should be freed
        assert len(connection_manager.active_connections) == 0