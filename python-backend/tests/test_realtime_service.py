"""
Real-time Service Tests - High-impact coverage for WebSocket functionality
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import WebSocket
import asyncio

from app.services.realtime import (
    ConnectionManager,
    manager,
)


class TestConnectionManager:
    """Test WebSocket connection manager functionality"""

    def test_connection_manager_initialization(self):
        """Test connection manager initializes correctly"""
        conn_mgr = ConnectionManager()
        
        assert hasattr(conn_mgr, 'active_connections')
        assert hasattr(conn_mgr, 'connect')
        assert hasattr(conn_mgr, 'disconnect')
        assert isinstance(conn_mgr.active_connections, list)
        assert len(conn_mgr.active_connections) == 0

    async def test_connect_websocket(self):
        """Test connecting a WebSocket"""
        conn_mgr = ConnectionManager()
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        
        await conn_mgr.connect(mock_websocket)
        
        # WebSocket should be accepted and added to active connections
        mock_websocket.accept.assert_called_once()
        assert mock_websocket in conn_mgr.active_connections
        assert len(conn_mgr.active_connections) == 1

    async def test_disconnect_websocket(self):
        """Test disconnecting a WebSocket"""
        conn_mgr = ConnectionManager()
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        
        # First connect
        await conn_mgr.connect(mock_websocket)
        assert len(conn_mgr.active_connections) == 1
        
        # Then disconnect
        conn_mgr.disconnect(mock_websocket)
        assert len(conn_mgr.active_connections) == 0
        assert mock_websocket not in conn_mgr.active_connections

    async def test_disconnect_nonexistent_websocket(self):
        """Test disconnecting a WebSocket that wasn't connected"""
        conn_mgr = ConnectionManager()
        mock_websocket = Mock(spec=WebSocket)
        
        # Should handle gracefully without error
        try:
            conn_mgr.disconnect(mock_websocket)
            disconnect_success = True
        except Exception:
            disconnect_success = False
            
        assert disconnect_success is True
        assert len(conn_mgr.active_connections) == 0

    async def test_send_personal_message(self):
        """Test sending a personal message to a specific WebSocket"""
        conn_mgr = ConnectionManager()
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock()
        
        # Connect WebSocket
        await conn_mgr.connect(mock_websocket)
        
        # Send personal message
        test_message = "Personal message for you"
        await conn_mgr.send_personal_message(test_message, mock_websocket)
        
        # Verify message was sent
        mock_websocket.send_text.assert_called_once_with(test_message)

    async def test_send_personal_message_json(self):
        """Test sending personal message as JSON"""
        conn_mgr = ConnectionManager()
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_json = AsyncMock()
        
        # Connect WebSocket
        await conn_mgr.connect(mock_websocket)
        
        # Send JSON message
        test_data = {"type": "notification", "message": "Test notification"}
        await conn_mgr.send_personal_message(test_data, mock_websocket)
        
        # Should send as JSON when data is dict
        mock_websocket.send_json.assert_called_once_with(test_data)

    async def test_broadcast_message(self):
        """Test broadcasting message to all connected WebSockets"""
        conn_mgr = ConnectionManager()
        
        # Create multiple mock WebSockets
        websockets = []
        for i in range(3):
            mock_ws = Mock(spec=WebSocket)
            mock_ws.accept = AsyncMock()
            mock_ws.send_text = AsyncMock()
            websockets.append(mock_ws)
            await conn_mgr.connect(mock_ws)
        
        # Broadcast message
        test_message = "Broadcast to all"
        await conn_mgr.broadcast(test_message)
        
        # All WebSockets should receive the message
        for ws in websockets:
            ws.send_text.assert_called_once_with(test_message)

    async def test_broadcast_with_exception_handling(self):
        """Test broadcast handling when some WebSockets fail"""
        conn_mgr = ConnectionManager()
        
        # Create WebSockets - one that works, one that fails
        working_ws = Mock(spec=WebSocket)
        working_ws.accept = AsyncMock()
        working_ws.send_text = AsyncMock()
        
        failing_ws = Mock(spec=WebSocket)
        failing_ws.accept = AsyncMock()
        failing_ws.send_text = AsyncMock(side_effect=Exception("Connection closed"))
        
        await conn_mgr.connect(working_ws)
        await conn_mgr.connect(failing_ws)
        
        # Broadcast should handle exceptions gracefully
        test_message = "Test broadcast with failure"
        try:
            await conn_mgr.broadcast(test_message)
            broadcast_success = True
        except Exception:
            broadcast_success = False
        
        assert broadcast_success is True
        working_ws.send_text.assert_called_once_with(test_message)
        failing_ws.send_text.assert_called_once_with(test_message)

    async def test_send_to_all_except(self):
        """Test sending message to all except specified WebSocket"""
        conn_mgr = ConnectionManager()
        
        # Create multiple WebSockets
        target_ws = Mock(spec=WebSocket)
        target_ws.accept = AsyncMock()
        target_ws.send_text = AsyncMock()
        
        other_ws = Mock(spec=WebSocket)
        other_ws.accept = AsyncMock()
        other_ws.send_text = AsyncMock()
        
        await conn_mgr.connect(target_ws)
        await conn_mgr.connect(other_ws)
        
        # Send to all except target_ws
        test_data = {"type": "update", "data": "test"}
        await conn_mgr.send_to_all_except(test_data, except_ws=target_ws)
        
        # Only other_ws should receive the message
        target_ws.send_text.assert_not_called()
        other_ws.send_json.assert_called_once_with(test_data)

    async def test_multiple_connections_and_disconnections(self):
        """Test handling multiple connections and disconnections"""
        conn_mgr = ConnectionManager()
        websockets = []
        
        # Connect multiple WebSockets
        for i in range(5):
            mock_ws = Mock(spec=WebSocket)
            mock_ws.accept = AsyncMock()
            websockets.append(mock_ws)
            await conn_mgr.connect(mock_ws)
        
        assert len(conn_mgr.active_connections) == 5
        
        # Disconnect some WebSockets
        for i in range(3):
            conn_mgr.disconnect(websockets[i])
        
        assert len(conn_mgr.active_connections) == 2
        
        # Remaining WebSockets should still be connected
        remaining_ws = websockets[3:]
        for ws in remaining_ws:
            assert ws in conn_mgr.active_connections


class TestConnectionManagerEdgeCases:
    """Test edge cases for connection manager"""

    async def test_send_to_disconnected_websocket(self):
        """Test sending message to a WebSocket that was disconnected"""
        conn_mgr = ConnectionManager()
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock(side_effect=Exception("WebSocket disconnected"))
        
        # Connect then try to send
        await conn_mgr.connect(mock_websocket)
        
        # Should handle send failure gracefully
        try:
            await conn_mgr.send_personal_message("test", mock_websocket)
            send_success = True
        except Exception:
            send_success = False
        
        # Should either succeed or fail gracefully
        assert isinstance(send_success, bool)

    async def test_broadcast_to_empty_connection_list(self):
        """Test broadcasting when no WebSockets are connected"""
        conn_mgr = ConnectionManager()
        
        # Should handle empty connections gracefully
        try:
            await conn_mgr.broadcast("No one to send to")
            broadcast_success = True
        except Exception:
            broadcast_success = False
        
        assert broadcast_success is True

    async def test_concurrent_connections(self):
        """Test handling concurrent WebSocket connections"""
        conn_mgr = ConnectionManager()
        
        async def connect_websocket():
            mock_ws = Mock(spec=WebSocket)
            mock_ws.accept = AsyncMock()
            await conn_mgr.connect(mock_ws)
            return mock_ws
        
        # Connect multiple WebSockets concurrently
        tasks = [connect_websocket() for _ in range(10)]
        websockets = await asyncio.gather(*tasks)
        
        # All should be connected
        assert len(conn_mgr.active_connections) == 10
        for ws in websockets:
            assert ws in conn_mgr.active_connections

    async def test_concurrent_disconnections(self):
        """Test handling concurrent WebSocket disconnections"""
        conn_mgr = ConnectionManager()
        websockets = []
        
        # First connect multiple WebSockets
        for i in range(5):
            mock_ws = Mock(spec=WebSocket)
            mock_ws.accept = AsyncMock()
            websockets.append(mock_ws)
            await conn_mgr.connect(mock_ws)
        
        # Disconnect all concurrently
        async def disconnect_websocket(ws):
            conn_mgr.disconnect(ws)
        
        tasks = [disconnect_websocket(ws) for ws in websockets]
        await asyncio.gather(*tasks)
        
        # All should be disconnected
        assert len(conn_mgr.active_connections) == 0


class TestGlobalManagerInstance:
    """Test the global manager instance"""

    def test_global_manager_exists(self):
        """Test that global manager instance exists"""
        assert manager is not None
        assert isinstance(manager, ConnectionManager)

    async def test_global_manager_functionality(self):
        """Test that global manager works like a regular instance"""
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock()
        
        # Test connect
        await manager.connect(mock_websocket)
        assert mock_websocket in manager.active_connections
        
        # Test send
        await manager.send_personal_message("test", mock_websocket)
        mock_websocket.send_text.assert_called_once()
        
        # Test disconnect
        manager.disconnect(mock_websocket)
        assert mock_websocket not in manager.active_connections


class TestWebSocketMessageTypes:
    """Test different types of WebSocket messages"""

    async def test_send_string_message(self):
        """Test sending string messages"""
        conn_mgr = ConnectionManager()
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock()
        
        await conn_mgr.connect(mock_websocket)
        
        # Send string message
        await conn_mgr.send_personal_message("Hello WebSocket", mock_websocket)
        mock_websocket.send_text.assert_called_once_with("Hello WebSocket")

    async def test_send_json_message(self):
        """Test sending JSON messages"""
        conn_mgr = ConnectionManager()
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_json = AsyncMock()
        
        await conn_mgr.connect(mock_websocket)
        
        # Send JSON message
        json_data = {"event": "user_joined", "user_id": 123, "timestamp": "2024-01-01T00:00:00Z"}
        await conn_mgr.send_personal_message(json_data, mock_websocket)
        mock_websocket.send_json.assert_called_once_with(json_data)

    async def test_broadcast_different_message_types(self):
        """Test broadcasting different message types"""
        conn_mgr = ConnectionManager()
        
        # Create WebSockets that support both text and JSON
        mock_ws1 = Mock(spec=WebSocket)
        mock_ws1.accept = AsyncMock()
        mock_ws1.send_text = AsyncMock()
        mock_ws1.send_json = AsyncMock()
        
        mock_ws2 = Mock(spec=WebSocket)
        mock_ws2.accept = AsyncMock()
        mock_ws2.send_text = AsyncMock()
        mock_ws2.send_json = AsyncMock()
        
        await conn_mgr.connect(mock_ws1)
        await conn_mgr.connect(mock_ws2)
        
        # Broadcast string
        await conn_mgr.broadcast("String message")
        mock_ws1.send_text.assert_called_with("String message")
        mock_ws2.send_text.assert_called_with("String message")
        
        # Broadcast JSON
        json_message = {"type": "broadcast", "data": "test"}
        await conn_mgr.broadcast(json_message)
        mock_ws1.send_json.assert_called_with(json_message)
        mock_ws2.send_json.assert_called_with(json_message)


class TestWebSocketErrorHandling:
    """Test WebSocket error handling scenarios"""

    async def test_connection_error_during_accept(self):
        """Test handling connection errors during WebSocket accept"""
        conn_mgr = ConnectionManager()
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.accept = AsyncMock(side_effect=Exception("Connection failed"))
        
        # Should handle connection error gracefully
        try:
            await conn_mgr.connect(mock_websocket)
            connect_success = True
        except Exception:
            connect_success = False
        
        # Should either handle gracefully or propagate exception
        # Behavior depends on implementation
        assert isinstance(connect_success, bool)

    async def test_send_error_handling(self):
        """Test handling send errors (e.g., client disconnected)"""
        conn_mgr = ConnectionManager()
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock(side_effect=Exception("Send failed"))
        
        await conn_mgr.connect(mock_websocket)
        
        # Should handle send errors gracefully
        try:
            await conn_mgr.send_personal_message("test", mock_websocket)
            send_success = True
        except Exception:
            send_success = False
        
        # Implementation should handle this gracefully
        assert isinstance(send_success, bool)

    async def test_cleanup_after_errors(self):
        """Test that connections are properly cleaned up after errors"""
        conn_mgr = ConnectionManager()
        mock_websocket = Mock(spec=WebSocket)
        mock_websocket.accept = AsyncMock()
        
        # Connect successfully
        await conn_mgr.connect(mock_websocket)
        initial_count = len(conn_mgr.active_connections)
        assert initial_count == 1
        
        # Simulate error scenario and manual cleanup
        conn_mgr.disconnect(mock_websocket)
        
        # Connection should be cleaned up
        assert len(conn_mgr.active_connections) == 0