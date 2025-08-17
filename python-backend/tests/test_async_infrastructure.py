"""
Test Async Infrastructure - Story 3.2 Validation
Validates all new async fixtures and testing capabilities
"""

import pytest
import asyncio
import time
from datetime import datetime


@pytest.mark.asyncio
class TestAsyncFixtures:
    """Test that all async fixtures work correctly"""
    
    async def test_async_db_session_fixture(self, async_db_session):
        """Test async database session fixture"""
        assert async_db_session is not None
        
        # Test basic session operations
        result = await async_db_session.execute("SELECT 1 as test")
        row = result.scalar()
        assert row == 1
    
    async def test_async_client_with_db_fixture(self, async_client_with_db):
        """Test async HTTP client fixture"""
        assert async_client_with_db is not None
        
        # Test basic HTTP request
        response = await async_client_with_db.get("/health")
        # Note: This may fail if /health endpoint doesn't exist, but fixture should work
        assert response is not None
    
    async def test_websocket_test_client_fixture(self, websocket_test_client):
        """Test WebSocket test client fixture"""
        client = websocket_test_client
        
        # Test connection
        assert not client.connected
        await client.connect("/ws/test", headers={"user_id": "123"})
        assert client.connected
        assert client.user_id == "123"
        assert client.connection_id == "test_connection_123"
        
        # Test sending messages
        await client.send_text("Hello WebSocket")
        await client.send_json({"type": "test", "data": "test_data"})
        
        assert len(client.messages_sent) == 2
        assert client.messages_sent[0]["type"] == "text"
        assert client.messages_sent[1]["type"] == "json"
        
        # Test receiving messages
        client.simulate_incoming_message("Incoming test message")
        received = await client.receive_text()
        assert received == "Incoming test message"
        
        # Test disconnection
        await client.disconnect()
        assert not client.connected
    
    async def test_mock_redis_async_fixture(self, mock_redis_async):
        """Test async Redis mock fixture"""
        redis = mock_redis_async
        
        # Test basic Redis operations
        await redis.set("test_key", "test_value")
        value = await redis.get("test_key")
        assert value == b"test_value"
        
        # Test Redis lists
        await redis.lpush("test_list", "item1", "item2")
        length = await redis.llen("test_list")
        assert length == 2
    
    async def test_async_realtime_service_fixture(self, async_realtime_service):
        """Test async realtime service fixture"""
        service = async_realtime_service
        
        # Test message sending
        result = await service.send_message_to_connection(123, {"content": "test"})
        assert result["status"] == "sent"
        assert result["connection_id"] == 123
        
        # Test message saving
        message_data = {"connection_id": 123, "sender_id": 456, "content": "test message"}
        message = await service.send_and_save_message(message_data)
        assert message.connection_id == 123
        assert message.sender_id == 456
        assert message.message_text == "test message"
        
        # Test typing indicators
        await service.start_typing_indicator(123, 456)
        assert 456 in service.typing_sessions[123]
        
        await service.stop_typing_indicator(123, 456)
        assert 456 not in service.typing_sessions[123]
        
        # Test presence notifications
        result = await service.notify_presence_change(456, "online")
        assert result["user_id"] == 456
        assert result["status"] == "online"
        assert result["notified"] is True
        
        # Test WebSocket authentication
        valid_result = await service.validate_websocket_auth("valid_token")
        assert valid_result["user_id"] == 1
        
        invalid_result = await service.validate_websocket_auth("invalid_token")
        assert invalid_result is None
    
    async def test_async_ai_service_fixture(self, async_ai_service):
        """Test async AI service fixture"""
        ai_service = async_ai_service
        
        # Test compatibility insights
        user1_data = {"interests": ["cooking", "reading"], "values": {"growth": True}}
        user2_data = {"interests": ["cooking", "hiking"], "values": {"growth": True}}
        
        insights = await ai_service.generate_compatibility_insights(user1_data, user2_data)
        assert "insights" in insights
        assert "confidence" in insights
        assert len(insights["insights"]) > 0
        assert insights["confidence"] > 0.5
        
        # Test revelation sentiment analysis
        revelation = "I believe in personal growth and authentic connections"
        sentiment = await ai_service.analyze_revelation_sentiment(revelation)
        assert sentiment["sentiment"] == "positive"
        assert sentiment["emotional_depth"] > 0.5
        
        # Test conversation starters
        starters = await ai_service.suggest_conversation_starters(user1_data, user2_data)
        assert "suggestions" in starters
        assert len(starters["suggestions"]) > 0
        
        # Test content moderation
        safe_content = await ai_service.detect_inappropriate_content("This is a nice message")
        assert not safe_content["flagged"]
        
        unsafe_content = await ai_service.detect_inappropriate_content("This is inappropriate content")
        assert unsafe_content["flagged"]
        
        # Test batch processing
        user_pairs = [(1, 2), (3, 4), (5, 6)]
        batch_results = await ai_service.process_batch_compatibility(user_pairs)
        assert len(batch_results) == 3
        assert all("compatibility_score" in result for result in batch_results)
        
        # Verify API calls were tracked
        assert "generate_compatibility_insights" in ai_service.api_calls
        assert "analyze_revelation_sentiment" in ai_service.api_calls
    
    async def test_async_performance_monitor_fixture(self, async_performance_monitor):
        """Test async performance monitoring fixture"""
        monitor = async_performance_monitor
        
        # Test timer functionality
        await monitor.start_timer("test_operation")
        await asyncio.sleep(0.01)  # Small delay
        duration = await monitor.end_timer("test_operation")
        assert duration >= 0.01
        
        # Test operation measurement
        async def mock_async_operation():
            await asyncio.sleep(0.005)
            return "operation_result"
        
        result, duration = await monitor.measure_async_operation(
            mock_async_operation(), "measured_operation"
        )
        assert result == "operation_result"
        assert duration >= 0.005
        
        # Test metrics summary
        summary = await monitor.get_metrics_summary()
        assert "test_operation" in summary
        assert "measured_operation" in summary
        assert summary["test_operation"]["count"] == 1
        
        # Test concurrent load simulation
        async def simple_async_task():
            await asyncio.sleep(0.001)
            return "success"
        
        load_results = await monitor.simulate_concurrent_load(
            simple_async_task, concurrent_users=5, iterations=2
        )
        assert load_results["total_operations"] == 10
        assert load_results["successful"] == 10
        assert load_results["failed"] == 0
        assert load_results["operations_per_second"] > 0
    
    async def test_async_test_data_generator_fixture(self, async_test_data_generator):
        """Test async test data generator fixture"""
        generator = async_test_data_generator
        
        # Test user batch creation
        users = await generator.create_users_batch(count=5)
        assert len(users) == 5
        assert all(user.email.startswith("batch_user_") for user in users)
        
        # Test connection batch creation
        connections = await generator.create_connections_batch(users, count=2)
        assert len(connections) == 2
        assert all(hasattr(conn, 'user1_id') and hasattr(conn, 'user2_id') for conn in connections)
        
        # Test cleanup
        user_ids = [user.id for user in users]
        cleanup_result = await generator.cleanup_test_data(user_ids)
        assert cleanup_result is True


@pytest.mark.asyncio
class TestAsyncFixtureIntegration:
    """Test that async fixtures work well together"""
    
    async def test_multiple_async_fixtures_together(self, websocket_test_client, async_realtime_service, async_ai_service):
        """Test using multiple async fixtures in same test"""
        # Setup WebSocket connection
        await websocket_test_client.connect("/ws/test")
        assert websocket_test_client.connected
        
        # Use realtime service
        message_result = await async_realtime_service.send_message_to_connection(
            123, {"content": "Integration test message"}
        )
        assert message_result["status"] == "sent"
        
        # Use AI service
        insights = await async_ai_service.generate_compatibility_insights(
            {"interests": ["test"]}, {"interests": ["test"]}
        )
        assert "insights" in insights
        
        # All fixtures should work independently
        assert websocket_test_client.connection_id is not None
        assert len(async_ai_service.api_calls) > 0
    
    async def test_async_service_with_performance_monitoring(self, async_ai_service, async_performance_monitor):
        """Test async service with performance monitoring"""
        monitor = async_performance_monitor
        ai_service = async_ai_service
        
        # Measure AI service operations
        user_data1 = {"interests": ["cooking", "reading"]}
        user_data2 = {"interests": ["cooking", "hiking"]}
        
        insights, duration = await monitor.measure_async_operation(
            ai_service.generate_compatibility_insights(user_data1, user_data2),
            "ai_compatibility_insights"
        )
        
        assert insights["confidence"] > 0.5
        assert duration > 0
        
        # Test concurrent AI operations
        async def ai_task():
            return await ai_service.analyze_revelation_sentiment("Test revelation")
        
        load_results = await monitor.simulate_concurrent_load(
            ai_task, concurrent_users=3, iterations=2
        )
        
        assert load_results["successful"] == 6
        assert load_results["operations_per_second"] > 0
    
    async def test_websocket_with_realtime_service(self, websocket_test_client, async_realtime_service):
        """Test WebSocket client with realtime service"""
        ws_client = websocket_test_client
        realtime_service = async_realtime_service
        
        # Connect WebSocket
        await ws_client.connect("/ws/connection/123", headers={"user_id": "456"})
        
        # Send message through realtime service
        message_data = {
            "connection_id": 123,
            "sender_id": 456,
            "content": "Hello from realtime service"
        }
        message = await realtime_service.send_and_save_message(message_data)
        
        # Simulate message received via WebSocket
        ws_client.simulate_incoming_message(message.message_text)
        received = await ws_client.receive_text()
        
        assert received == "Hello from realtime service"
        assert message.sender_id == 456
    
    async def test_async_data_generator_with_services(self, async_test_data_generator, async_ai_service):
        """Test async data generator with AI services"""
        generator = async_test_data_generator
        ai_service = async_ai_service
        
        # Generate test users
        users = await generator.create_users_batch(count=4)
        
        # Create connections
        connections = await generator.create_connections_batch(users, count=2)
        
        # Use AI service to analyze the generated data
        user1_data = {"id": users[0].id, "interests": ["test"]}
        user2_data = {"id": users[1].id, "interests": ["test"]}
        
        compatibility = await ai_service.generate_compatibility_insights(user1_data, user2_data)
        
        assert len(users) == 4
        assert len(connections) == 2
        assert compatibility["confidence"] > 0.5


@pytest.mark.asyncio
class TestAsyncPerformance:
    """Test async performance and load testing capabilities"""
    
    async def test_concurrent_websocket_connections(self, websocket_test_client, async_performance_monitor):
        """Test multiple concurrent WebSocket connections"""
        monitor = async_performance_monitor
        
        async def create_websocket_connection():
            # Create a new instance for each connection
            from unittest.mock import AsyncMock
            
            class TempWebSocketClient:
                def __init__(self):
                    self.connected = False
                
                async def connect(self, url):
                    await asyncio.sleep(0.001)  # Simulate connection time
                    self.connected = True
                    return True
                
                async def disconnect(self):
                    self.connected = False
            
            client = TempWebSocketClient()
            await client.connect("/ws/test")
            await client.disconnect()
            return "connected"
        
        # Test concurrent connections
        results = await monitor.simulate_concurrent_load(
            create_websocket_connection, concurrent_users=10, iterations=2
        )
        
        assert results["total_operations"] == 20
        assert results["successful"] == 20
        assert results["operations_per_second"] > 0
    
    async def test_async_ai_batch_processing_performance(self, async_ai_service, async_performance_monitor):
        """Test AI service batch processing performance"""
        ai_service = async_ai_service
        monitor = async_performance_monitor
        
        # Create test data for batch processing
        user_pairs = [(i, i+1) for i in range(1, 20, 2)]  # 10 pairs
        
        # Measure batch processing performance
        results, duration = await monitor.measure_async_operation(
            ai_service.process_batch_compatibility(user_pairs),
            "ai_batch_processing"
        )
        
        assert len(results) == 10
        assert duration > 0
        assert all(result["compatibility_score"] > 0 for result in results)
        
        # Test concurrent batch operations
        async def batch_task():
            pairs = [(1, 2), (3, 4)]
            return await ai_service.process_batch_compatibility(pairs)
        
        load_results = await monitor.simulate_concurrent_load(
            batch_task, concurrent_users=5, iterations=2
        )
        
        assert load_results["successful"] == 10
        assert load_results["operations_per_second"] > 0
    
    async def test_async_database_performance(self, async_test_data_generator, async_performance_monitor):
        """Test async database operations performance"""
        generator = async_test_data_generator
        monitor = async_performance_monitor
        
        # Measure user creation performance
        users, duration = await monitor.measure_async_operation(
            generator.create_users_batch(count=10),
            "batch_user_creation"
        )
        
        assert len(users) == 10
        assert duration > 0
        
        # Measure connection creation performance
        connections, duration = await monitor.measure_async_operation(
            generator.create_connections_batch(users, count=5),
            "batch_connection_creation"
        )
        
        assert len(connections) == 5
        assert duration > 0
        
        # Get performance summary
        summary = await monitor.get_metrics_summary()
        assert "batch_user_creation" in summary
        assert "batch_connection_creation" in summary


@pytest.mark.asyncio
class TestAsyncErrorHandling:
    """Test error handling in async fixtures"""
    
    async def test_websocket_error_handling(self, websocket_test_client):
        """Test WebSocket error handling"""
        client = websocket_test_client
        
        # Test sending message without connection
        with pytest.raises(Exception, match="WebSocket not connected"):
            await client.send_text("This should fail")
        
        # Connect and then test normal operation
        await client.connect("/ws/test")
        await client.send_text("This should work")
        assert len(client.messages_sent) == 1
    
    async def test_async_service_error_handling(self, async_realtime_service):
        """Test async service error handling"""
        service = async_realtime_service
        
        # Test error handling method
        test_error = Exception("Test error")
        result = await service.handle_websocket_error(123, test_error)
        
        assert result["error_handled"] is True
        assert result["connection_id"] == 123
        assert "Test error" in result["error"]
    
    async def test_async_ai_service_content_moderation(self, async_ai_service):
        """Test AI service content moderation and error handling"""
        ai_service = async_ai_service
        
        # Test content flagging
        flagged_result = await ai_service.detect_inappropriate_content(
            "This content contains inappropriate material"
        )
        assert flagged_result["flagged"] is True
        assert flagged_result["confidence"] > 0.9
        
        # Test safe content
        safe_result = await ai_service.detect_inappropriate_content(
            "This is perfectly safe content about cooking and relationships"
        )
        assert safe_result["flagged"] is False
        assert safe_result["confidence"] > 0.9


@pytest.mark.asyncio
class TestAsyncFixtureReliability:
    """Test that async fixtures are reliable and deterministic"""
    
    async def test_async_fixture_consistency(self, async_ai_service):
        """Test that async fixture provides consistent results"""
        ai_service = async_ai_service
        
        # Run same operation multiple times
        user_data1 = {"interests": ["cooking", "reading"]}
        user_data2 = {"interests": ["cooking", "hiking"]}
        
        results = []
        for _ in range(3):
            result = await ai_service.generate_compatibility_insights(user_data1, user_data2)
            results.append(result)
        
        # All results should have the same structure
        for result in results:
            assert "insights" in result
            assert "confidence" in result
            assert result["confidence"] == 0.85  # Mock should be deterministic
    
    async def test_async_fixture_isolation(self, websocket_test_client, async_realtime_service):
        """Test that async fixtures provide proper isolation"""
        # Use both fixtures independently
        await websocket_test_client.connect("/ws/test")
        
        result = await async_realtime_service.send_message_to_connection(
            999, {"content": "isolation test"}
        )
        
        # They should not interfere with each other
        assert websocket_test_client.connected is True
        assert result["connection_id"] == 999
        assert websocket_test_client.connection_id != 999
    
    async def test_async_performance_monitor_accuracy(self, async_performance_monitor):
        """Test that performance monitoring provides accurate metrics"""
        monitor = async_performance_monitor
        
        # Measure a known delay
        await monitor.start_timer("known_delay")
        await asyncio.sleep(0.05)  # 50ms delay
        duration = await monitor.end_timer("known_delay")
        
        # Should be approximately 50ms (with some tolerance for system variance)
        assert 0.04 <= duration <= 0.1  # 40ms to 100ms tolerance
        
        # Test metrics summary accuracy
        summary = await monitor.get_metrics_summary()
        assert summary["known_delay"]["count"] == 1
        assert 0.04 <= summary["known_delay"]["avg"] <= 0.1