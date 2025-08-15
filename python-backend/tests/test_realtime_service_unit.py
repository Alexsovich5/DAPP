"""
Unit tests for realtime connection manager functionality
Tests WebSocket connection management without external dependencies
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio
import json

from app.services.realtime import ConnectionManager


@pytest.mark.unit
class TestConnectionManager:
    """Test suite for ConnectionManager class"""
    
    @pytest.fixture
    def connection_manager(self):
        """Create ConnectionManager instance"""
        return ConnectionManager()
    
    def test_manager_initialization(self, connection_manager):
        """Test ConnectionManager initialization"""
        assert connection_manager.active_connections == []
        assert connection_manager.connection_user == {}
        assert hasattr(connection_manager, '_lock')
    
    @pytest.mark.asyncio
    async def test_connect_websocket(self, connection_manager):
        """Test connecting a websocket"""
        mock_websocket = Mock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.query_params = {}
        
        await connection_manager.connect(mock_websocket)
        
        assert mock_websocket in connection_manager.active_connections
        mock_websocket.accept.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_websocket_with_user_id(self, connection_manager):
        """Test connecting websocket with user ID in query params"""
        mock_websocket = Mock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.query_params = Mock()
        mock_websocket.query_params.get.return_value = "123"
        
        await connection_manager.connect(mock_websocket)
        
        assert mock_websocket in connection_manager.active_connections
        assert connection_manager.connection_user[id(mock_websocket)] == "123"
    
    @pytest.mark.asyncio
    async def test_connect_websocket_query_params_error(self, connection_manager):
        """Test connecting websocket when query params raise error"""
        mock_websocket = Mock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.query_params = Mock()
        mock_websocket.query_params.get.side_effect = Exception("Query param error")
        
        # Should not raise error
        await connection_manager.connect(mock_websocket)
        
        assert mock_websocket in connection_manager.active_connections
        assert id(mock_websocket) not in connection_manager.connection_user
    
    def test_disconnect_websocket(self, connection_manager):
        """Test disconnecting a websocket"""
        mock_websocket = Mock()
        connection_manager.active_connections.append(mock_websocket)
        connection_manager.connection_user[id(mock_websocket)] = "123"
        
        connection_manager.disconnect(mock_websocket)
        
        assert mock_websocket not in connection_manager.active_connections
        assert id(mock_websocket) not in connection_manager.connection_user
    
    def test_disconnect_websocket_not_connected(self, connection_manager):
        """Test disconnecting a websocket that wasn't connected"""
        mock_websocket = Mock()
        
        # Should not raise error
        connection_manager.disconnect(mock_websocket)
        
        assert mock_websocket not in connection_manager.active_connections
    
    @pytest.mark.asyncio
    async def test_broadcast_message(self, connection_manager):
        """Test broadcasting message to all connections"""
        mock_ws1, mock_ws2 = Mock(), Mock()
        connection_manager.active_connections = [mock_ws1, mock_ws2]
        
        message = {"type": "test", "content": "Hello everyone"}
        
        with patch.object(connection_manager, '_safe_send_text', new_callable=AsyncMock) as mock_send:
            await connection_manager.broadcast(message)
        
        assert mock_send.call_count == 2
        expected_data = json.dumps(message)
        mock_send.assert_any_call(mock_ws1, expected_data)
        mock_send.assert_any_call(mock_ws2, expected_data)
    
    @pytest.mark.asyncio
    async def test_broadcast_message_empty_connections(self, connection_manager):
        """Test broadcasting when no connections exist"""
        message = {"type": "test", "content": "Nobody to send to"}
        
        # Should not raise error
        await connection_manager.broadcast(message)
        
        assert len(connection_manager.active_connections) == 0
    
    @pytest.mark.asyncio
    async def test_send_to_all_except(self, connection_manager):
        """Test sending to all connections except one"""
        mock_ws1, mock_ws2, mock_ws3 = Mock(), Mock(), Mock()
        connection_manager.active_connections = [mock_ws1, mock_ws2, mock_ws3]
        
        message = {"type": "test", "content": "Not for ws2"}
        
        with patch.object(connection_manager, '_safe_send_text', new_callable=AsyncMock) as mock_send:
            await connection_manager.send_to_all_except(message, mock_ws2)
        
        assert mock_send.call_count == 2
        expected_data = json.dumps(message)
        mock_send.assert_any_call(mock_ws1, expected_data)
        mock_send.assert_any_call(mock_ws3, expected_data)
        # Should not call for mock_ws2
    
    @pytest.mark.asyncio
    async def test_send_to_all_except_none(self, connection_manager):
        """Test sending to all when except_ws is None"""
        mock_ws1, mock_ws2 = Mock(), Mock()
        connection_manager.active_connections = [mock_ws1, mock_ws2]
        
        message = {"type": "test", "content": "To everyone"}
        
        with patch.object(connection_manager, '_safe_send_text', new_callable=AsyncMock) as mock_send:
            await connection_manager.send_to_all_except(message, None)
        
        assert mock_send.call_count == 2
    
    @pytest.mark.asyncio
    async def test_safe_send_text_success(self, connection_manager):
        """Test successful safe text sending"""
        mock_websocket = Mock()
        mock_websocket.send_text = AsyncMock()
        
        await connection_manager._safe_send_text(mock_websocket, "test message")
        
        mock_websocket.send_text.assert_called_once_with("test message")
    
    @pytest.mark.asyncio
    async def test_safe_send_text_websocket_disconnect(self, connection_manager):
        """Test safe text sending when websocket disconnects"""
        from fastapi import WebSocketDisconnect
        
        mock_websocket = Mock()
        mock_websocket.send_text = AsyncMock(side_effect=WebSocketDisconnect())
        connection_manager.active_connections.append(mock_websocket)
        
        await connection_manager._safe_send_text(mock_websocket, "test message")
        
        # Should remove disconnected websocket
        assert mock_websocket not in connection_manager.active_connections
    
    @pytest.mark.asyncio
    async def test_safe_send_text_general_exception(self, connection_manager):
        """Test safe text sending when general exception occurs"""
        mock_websocket = Mock()
        mock_websocket.send_text = AsyncMock(side_effect=Exception("Connection error"))
        connection_manager.active_connections.append(mock_websocket)
        
        await connection_manager._safe_send_text(mock_websocket, "test message")
        
        # Should remove problematic websocket
        assert mock_websocket not in connection_manager.active_connections


@pytest.mark.integration
class TestConnectionManagerIntegration:
    """Integration test scenarios for ConnectionManager"""
    
    @pytest.fixture
    def connection_manager(self):
        """Create ConnectionManager instance"""
        return ConnectionManager()
    
    @pytest.mark.asyncio
    async def test_connection_lifecycle(self, connection_manager):
        """Test complete connection lifecycle"""
        mock_websocket = Mock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.query_params = Mock()
        mock_websocket.query_params.get.return_value = "123"
        
        # Connect
        await connection_manager.connect(mock_websocket)
        assert len(connection_manager.active_connections) == 1
        assert connection_manager.connection_user[id(mock_websocket)] == "123"
        
        # Disconnect
        connection_manager.disconnect(mock_websocket)
        assert len(connection_manager.active_connections) == 0
        assert id(mock_websocket) not in connection_manager.connection_user
    
    @pytest.mark.asyncio
    async def test_multiple_connections_broadcast(self, connection_manager):
        """Test broadcasting to multiple connections"""
        # Create multiple mock websockets
        mock_websockets = []
        for i in range(3):
            mock_ws = Mock()
            mock_ws.accept = AsyncMock()
            mock_ws.query_params = Mock()
            mock_ws.query_params.get.return_value = str(100 + i)
            mock_websockets.append(mock_ws)
            
            await connection_manager.connect(mock_ws)
        
        assert len(connection_manager.active_connections) == 3
        
        # Broadcast message
        message = {"type": "announcement", "content": "Server maintenance"}
        
        with patch.object(connection_manager, '_safe_send_text', new_callable=AsyncMock) as mock_send:
            await connection_manager.broadcast(message)
        
        assert mock_send.call_count == 3
        expected_data = json.dumps(message)
        for mock_ws in mock_websockets:
            mock_send.assert_any_call(mock_ws, expected_data)
    
    @pytest.mark.asyncio
    async def test_connection_failure_handling(self, connection_manager):
        """Test handling connections that fail during broadcast"""
        # Create working and failing websockets
        working_ws = Mock()
        working_ws.accept = AsyncMock()
        working_ws.query_params = {}
        
        failing_ws = Mock()
        failing_ws.accept = AsyncMock()
        failing_ws.query_params = {}
        
        await connection_manager.connect(working_ws)
        await connection_manager.connect(failing_ws)
        
        assert len(connection_manager.active_connections) == 2
        
        # Mock safe_send_text to fail for one connection
        async def mock_safe_send(ws, data):
            if ws == failing_ws:
                connection_manager.disconnect(ws)
        
        with patch.object(connection_manager, '_safe_send_text', side_effect=mock_safe_send):
            await connection_manager.broadcast({"type": "test", "content": "message"})
        
        # Failing connection should be removed
        assert len(connection_manager.active_connections) == 1
        assert working_ws in connection_manager.active_connections
        assert failing_ws not in connection_manager.active_connections
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_operations(self, connection_manager):
        """Test that concurrent operations work correctly"""
        import asyncio
        
        async def connect_websocket(user_id):
            mock_ws = Mock()
            mock_ws.accept = AsyncMock()
            mock_ws.query_params = Mock()
            mock_ws.query_params.get.return_value = str(user_id)
            await connection_manager.connect(mock_ws)
            return mock_ws
        
        async def disconnect_websocket(mock_ws):
            await asyncio.sleep(0.001)  # Small delay to test concurrency
            connection_manager.disconnect(mock_ws)
        
        # Connect multiple websockets concurrently
        user_ids = [1, 2, 3, 4, 5]
        websockets = await asyncio.gather(*[connect_websocket(uid) for uid in user_ids])
        
        assert len(connection_manager.active_connections) == 5
        
        # Disconnect half of them concurrently
        disconnect_tasks = [disconnect_websocket(ws) for ws in websockets[:3]]
        await asyncio.gather(*disconnect_tasks)
        
        assert len(connection_manager.active_connections) == 2


@pytest.mark.unit
class TestConnectionManagerEdgeCases:
    """Edge cases and error conditions for ConnectionManager"""
    
    @pytest.fixture
    def connection_manager(self):
        """Create ConnectionManager instance"""
        return ConnectionManager()
    
    @pytest.mark.asyncio
    async def test_broadcast_with_json_serializable_data(self, connection_manager):
        """Test broadcasting with complex JSON data"""
        mock_ws = Mock()
        mock_ws.accept = AsyncMock()
        mock_ws.query_params = {}
        await connection_manager.connect(mock_ws)
        
        complex_message = {
            "type": "complex",
            "data": {
                "numbers": [1, 2, 3],
                "nested": {"key": "value"},
                "timestamp": "2023-01-01T00:00:00Z"
            }
        }
        
        with patch.object(connection_manager, '_safe_send_text', new_callable=AsyncMock) as mock_send:
            await connection_manager.broadcast(complex_message)
        
        mock_send.assert_called_once()
        expected_data = json.dumps(complex_message)
        mock_send.assert_called_with(mock_ws, expected_data)
    
    @pytest.mark.asyncio
    async def test_send_to_all_except_with_duplicate_connections(self, connection_manager):
        """Test send_to_all_except when there are duplicate connection references"""
        mock_ws1 = Mock()
        mock_ws2 = Mock()
        
        # Add duplicate reference
        connection_manager.active_connections = [mock_ws1, mock_ws2, mock_ws1]
        
        message = {"type": "test", "content": "message"}
        
        with patch.object(connection_manager, '_safe_send_text', new_callable=AsyncMock) as mock_send:
            await connection_manager.send_to_all_except(message, mock_ws1)
        
        # Should only send to mock_ws2 once (not to duplicated mock_ws1)
        assert mock_send.call_count == 1
        expected_data = json.dumps(message)
        mock_send.assert_called_with(mock_ws2, expected_data)
    
    def test_connection_user_mapping_persistence(self, connection_manager):
        """Test that connection-user mapping persists correctly"""
        mock_ws1 = Mock()
        mock_ws2 = Mock()
        
        # Manually add connections and mappings
        connection_manager.active_connections.extend([mock_ws1, mock_ws2])
        connection_manager.connection_user[id(mock_ws1)] = "user1"
        connection_manager.connection_user[id(mock_ws2)] = "user2"
        
        # Disconnect one
        connection_manager.disconnect(mock_ws1)
        
        # Check that only the disconnected mapping is removed
        assert id(mock_ws1) not in connection_manager.connection_user
        assert connection_manager.connection_user[id(mock_ws2)] == "user2"
        assert mock_ws2 in connection_manager.active_connections
    
    @pytest.mark.asyncio
    async def test_broadcast_with_empty_message(self, connection_manager):
        """Test broadcasting empty or minimal messages"""
        mock_ws = Mock()
        connection_manager.active_connections = [mock_ws]
        
        # Empty dict
        await connection_manager.broadcast({})
        
        # None values
        await connection_manager.broadcast({"type": None, "content": None})
        
        # Should not raise errors
        assert True  # Test passes if no exceptions raised