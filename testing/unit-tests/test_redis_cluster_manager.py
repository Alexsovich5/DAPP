"""
Unit Tests for Redis Cluster Manager - Sprint 8 Enhanced Caching
Tests the RedisClusterManager class functionality including:
- Connection pooling and failover
- Database separation (sessions, profiles, matches, analytics, sentiment)
- Performance monitoring and metrics
- Circuit breaker functionality
- Cache warming and invalidation
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
import redis.asyncio as redis

sys.path.append(os.path.join(os.path.dirname(__file__), "../../python-backend/app"))

from core.redis_cluster_manager import (
    CacheDatabase,
    CacheMetrics,
    CircuitBreakerState,
    RedisClusterManager,
)


class TestRedisClusterManager:
    """Comprehensive test suite for Redis Cluster Manager"""

    @pytest.fixture
    async def mock_redis_cluster(self):
        """Mock Redis cluster connection"""
        mock_cluster = AsyncMock(spec=redis.RedisCluster)
        mock_cluster.ping = AsyncMock(return_value=True)
        mock_cluster.get = AsyncMock(return_value='{"test": "data"}')
        mock_cluster.set = AsyncMock(return_value=True)
        mock_cluster.delete = AsyncMock(return_value=1)
        mock_cluster.exists = AsyncMock(return_value=1)
        mock_cluster.expire = AsyncMock(return_value=True)
        mock_cluster.pipeline = Mock()
        mock_cluster.close = AsyncMock()
        return mock_cluster

    @pytest.fixture
    async def cluster_manager(self, mock_redis_cluster):
        """Redis cluster manager instance with mocked cluster"""
        cluster_endpoints = ["localhost:6379", "localhost:6380", "localhost:6381"]
        manager = RedisClusterManager(cluster_endpoints)

        # Replace the actual cluster with mock
        with patch.object(
            manager, "_create_cluster_connection", return_value=mock_redis_cluster
        ):
            await manager.initialize()
            manager.cluster = mock_redis_cluster

        return manager

    @pytest.mark.asyncio
    async def test_initialization(self, cluster_manager):
        """Test cluster manager initialization"""
        assert cluster_manager.is_connected is True
        assert cluster_manager.cluster is not None
        assert len(cluster_manager.cluster_endpoints) == 3

        # Check metrics initialization
        assert isinstance(cluster_manager.metrics, CacheMetrics)
        assert cluster_manager.metrics.total_requests == 0
        assert cluster_manager.metrics.cache_hits == 0
        assert cluster_manager.metrics.cache_misses == 0

    @pytest.mark.asyncio
    async def test_connection_failover(self, mock_redis_cluster):
        """Test connection failover mechanism"""
        cluster_endpoints = ["failed:6379", "localhost:6380", "localhost:6381"]
        manager = RedisClusterManager(cluster_endpoints)

        # Mock first connection to fail, second to succeed
        connection_attempts = []

        async def mock_create_connection(endpoints):
            connection_attempts.append(endpoints[0])
            if "failed" in endpoints[0]:
                raise ConnectionError("Failed to connect")
            return mock_redis_cluster

        with patch.object(
            manager, "_create_cluster_connection", side_effect=mock_create_connection
        ):
            await manager.initialize()

        # Should have tried failed endpoint first, then succeeded with localhost
        assert len(connection_attempts) >= 1
        assert manager.is_connected is True

    @pytest.mark.asyncio
    async def test_database_selection(self, cluster_manager):
        """Test database selection for different data types"""
        # Test sessions database
        key = await cluster_manager.get_sessions("test_session_key")
        cluster_manager.cluster.get.assert_called()

        # Test profiles database
        await cluster_manager.get_profiles("test_profile_key")
        cluster_manager.cluster.get.assert_called()

        # Test matches database
        await cluster_manager.get_matches("test_match_key")
        cluster_manager.cluster.get.assert_called()

        # Test analytics database
        await cluster_manager.get_analytics("test_analytics_key")
        cluster_manager.cluster.get.assert_called()

        # Test sentiment database
        await cluster_manager.get_sentiment("test_sentiment_key")
        cluster_manager.cluster.get.assert_called()

    @pytest.mark.asyncio
    async def test_cache_operations(self, cluster_manager):
        """Test basic cache operations (get, set, delete)"""
        test_key = "test:cache:key"
        test_data = {"user_id": 123, "name": "Test User"}

        # Test set operation
        result = await cluster_manager.set_sessions(test_key, test_data, ttl=3600)
        assert result is True
        cluster_manager.cluster.set.assert_called()

        # Test get operation
        cluster_manager.cluster.get.return_value = json.dumps(test_data)
        result = await cluster_manager.get_sessions(test_key)
        assert result == test_data

        # Test delete operation
        result = await cluster_manager.delete_sessions(test_key)
        assert result is True
        cluster_manager.cluster.delete.assert_called()

        # Test exists operation
        exists = await cluster_manager.exists_sessions(test_key)
        assert exists is True
        cluster_manager.cluster.exists.assert_called()

    @pytest.mark.asyncio
    async def test_cache_serialization(self, cluster_manager):
        """Test JSON serialization/deserialization"""
        test_cases = [
            {"simple": "string"},
            {"number": 42},
            {"boolean": True},
            {"null": None},
            {"list": [1, 2, 3]},
            {"nested": {"deep": {"value": "test"}}},
            {"datetime": "2025-01-01T00:00:00"},
        ]

        for test_data in test_cases:
            # Mock the get to return serialized data
            cluster_manager.cluster.get.return_value = json.dumps(test_data)

            # Set and get the data
            await cluster_manager.set_profiles("test_key", test_data)
            result = await cluster_manager.get_profiles("test_key")

            assert result == test_data

    @pytest.mark.asyncio
    async def test_cache_ttl(self, cluster_manager):
        """Test TTL (time to live) functionality"""
        test_key = "test:ttl:key"
        test_data = {"expires": "soon"}
        ttl_seconds = 1800  # 30 minutes

        await cluster_manager.set_profiles(test_key, test_data, ttl=ttl_seconds)

        # Verify set was called with correct parameters
        cluster_manager.cluster.set.assert_called()

        # Test expire functionality
        await cluster_manager.expire_profiles(test_key, ttl_seconds)
        cluster_manager.cluster.expire.assert_called_with(test_key, ttl_seconds)

    @pytest.mark.asyncio
    async def test_batch_operations(self, cluster_manager):
        """Test batch get and set operations"""
        keys = ["key1", "key2", "key3"]
        values = [{"data": 1}, {"data": 2}, {"data": 3}]

        # Mock pipeline for batch operations
        mock_pipeline = Mock()
        mock_pipeline.get = Mock()
        mock_pipeline.set = Mock()
        mock_pipeline.execute = AsyncMock(return_value=[json.dumps(v) for v in values])
        cluster_manager.cluster.pipeline.return_value.__aenter__ = AsyncMock(
            return_value=mock_pipeline
        )
        cluster_manager.cluster.pipeline.return_value.__aexit__ = AsyncMock()

        # Test batch get
        results = await cluster_manager.get_multiple_profiles(keys)
        assert len(results) == len(keys)

        # Test batch set
        data_dict = dict(zip(keys, values))
        await cluster_manager.set_multiple_profiles(data_dict, ttl=3600)

        # Verify pipeline was used
        cluster_manager.cluster.pipeline.assert_called()

    @pytest.mark.asyncio
    async def test_cache_warming(self, cluster_manager):
        """Test cache warming functionality"""
        warm_data = {
            "popular_profiles": [1, 2, 3, 4, 5],
            "trending_matches": {"user1": "user2"},
            "common_interests": ["cooking", "travel", "music"],
        }

        # Mock the warming data source
        with patch.object(cluster_manager, "_get_warming_data", return_value=warm_data):
            await cluster_manager.warm_cache()

        # Verify cache warming calls were made
        assert cluster_manager.cluster.set.call_count > 0

    @pytest.mark.asyncio
    async def test_cache_invalidation(self, cluster_manager):
        """Test cache invalidation patterns"""
        # Test single key invalidation
        await cluster_manager.invalidate_profile_cache("user:123")
        cluster_manager.cluster.delete.assert_called()

        # Test pattern-based invalidation
        mock_keys = ["user:123:profile", "user:123:matches", "user:123:messages"]
        cluster_manager.cluster.keys = AsyncMock(return_value=mock_keys)

        await cluster_manager.invalidate_user_cache("user:123")

        # Should have called keys with pattern and delete for each key
        cluster_manager.cluster.keys.assert_called()
        assert cluster_manager.cluster.delete.call_count >= len(mock_keys)

    @pytest.mark.asyncio
    async def test_performance_monitoring(self, cluster_manager):
        """Test performance monitoring and metrics collection"""
        # Simulate cache operations to generate metrics
        await cluster_manager.get_sessions("test_key")
        await cluster_manager.get_profiles("test_key")
        await cluster_manager.set_sessions("test_key", {"data": "test"})

        metrics = cluster_manager.get_metrics()

        assert metrics.total_requests > 0
        assert metrics.average_response_time >= 0
        assert isinstance(metrics.hit_ratio, float)
        assert 0 <= metrics.hit_ratio <= 1

    @pytest.mark.asyncio
    async def test_circuit_breaker(self, cluster_manager):
        """Test circuit breaker functionality"""
        # Set circuit breaker to trip easily for testing
        cluster_manager.circuit_breaker.failure_threshold = 2
        cluster_manager.circuit_breaker.recovery_timeout = 1

        # Simulate failures
        cluster_manager.cluster.get.side_effect = ConnectionError("Connection failed")

        # First few calls should try and fail
        with pytest.raises(ConnectionError):
            await cluster_manager.get_sessions("test_key")

        with pytest.raises(ConnectionError):
            await cluster_manager.get_sessions("test_key")

        # Circuit breaker should be open now
        assert cluster_manager.circuit_breaker.state == CircuitBreakerState.OPEN

        # Next call should be rejected immediately
        with pytest.raises(Exception):  # CircuitBreakerOpenError
            await cluster_manager.get_sessions("test_key")

        # Wait for recovery timeout
        await asyncio.sleep(1.1)

        # Circuit breaker should allow half-open
        assert cluster_manager.circuit_breaker.state == CircuitBreakerState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_connection_health_check(self, cluster_manager):
        """Test connection health monitoring"""
        # Test healthy connection
        is_healthy = await cluster_manager.health_check()
        assert is_healthy is True
        cluster_manager.cluster.ping.assert_called()

        # Test unhealthy connection
        cluster_manager.cluster.ping.side_effect = ConnectionError("Ping failed")
        is_healthy = await cluster_manager.health_check()
        assert is_healthy is False

    @pytest.mark.asyncio
    async def test_memory_usage_monitoring(self, cluster_manager):
        """Test memory usage monitoring"""
        # Mock memory info response
        mock_memory_info = {
            "used_memory": 1000000,
            "used_memory_human": "976.56K",
            "used_memory_rss": 2000000,
            "maxmemory": 10000000,
        }
        cluster_manager.cluster.info = AsyncMock(return_value=mock_memory_info)

        memory_stats = await cluster_manager.get_memory_usage()

        assert "used_memory" in memory_stats
        assert "memory_usage_percent" in memory_stats
        assert memory_stats["memory_usage_percent"] == 10.0  # 1M / 10M * 100

    @pytest.mark.asyncio
    async def test_key_expiration_handling(self, cluster_manager):
        """Test handling of expired keys"""
        # Mock expired key scenario
        cluster_manager.cluster.get.return_value = None

        result = await cluster_manager.get_sessions("expired_key")
        assert result is None

        # Verify cache miss was recorded
        assert cluster_manager.metrics.cache_misses > 0

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, cluster_manager):
        """Test concurrent cache operations"""
        # Create multiple concurrent operations
        tasks = []
        for i in range(10):
            task = cluster_manager.set_profiles(f"concurrent_key_{i}", {"data": i})
            tasks.append(task)

        # Wait for all operations to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All operations should succeed
        for result in results:
            assert not isinstance(result, Exception)
            assert result is True

    @pytest.mark.asyncio
    async def test_cleanup_and_shutdown(self, cluster_manager):
        """Test proper cleanup and shutdown"""
        # Test cleanup operation
        await cluster_manager.cleanup()
        cluster_manager.cluster.close.assert_called()

        # Manager should be marked as disconnected
        assert cluster_manager.is_connected is False

    @pytest.mark.asyncio
    async def test_error_handling(self, cluster_manager):
        """Test error handling for various failure scenarios"""
        # Test JSON decode error
        cluster_manager.cluster.get.return_value = "invalid json{"
        result = await cluster_manager.get_profiles("invalid_json_key")
        assert result is None

        # Test connection timeout
        cluster_manager.cluster.set.side_effect = asyncio.TimeoutError(
            "Operation timed out"
        )
        result = await cluster_manager.set_sessions("timeout_key", {"data": "test"})
        assert result is False

        # Test Redis error
        cluster_manager.cluster.delete.side_effect = redis.RedisError(
            "Redis operation failed"
        )
        result = await cluster_manager.delete_profiles("error_key")
        assert result is False

    @pytest.mark.asyncio
    async def test_cache_compression(self, cluster_manager):
        """Test cache compression for large data"""
        # Large test data
        large_data = {
            "users": [{"id": i, "data": "x" * 1000} for i in range(100)],
            "metadata": {"size": "large", "compressed": True},
        }

        # Mock compression settings
        cluster_manager.compression_enabled = True
        cluster_manager.compression_threshold = 1024  # 1KB

        # Test setting large data (should trigger compression)
        await cluster_manager.set_analytics("large_data_key", large_data)

        # Verify set was called (compression logic would be in actual implementation)
        cluster_manager.cluster.set.assert_called()

    @pytest.mark.asyncio
    async def test_database_specific_operations(self, cluster_manager):
        """Test database-specific cache operations"""
        # Test session-specific operations
        session_data = {
            "session_id": "sess_123",
            "user_id": 456,
            "expires_at": "2025-01-01T00:00:00Z",
        }
        await cluster_manager.set_sessions("session:sess_123", session_data, ttl=3600)

        # Test profile-specific operations
        profile_data = {
            "user_id": 456,
            "interests": ["cooking", "travel"],
            "emotional_profile": {"openness": 0.8},
        }
        await cluster_manager.set_profiles("profile:456", profile_data, ttl=7200)

        # Test match-specific operations
        match_data = {
            "user1_id": 456,
            "user2_id": 789,
            "compatibility_score": 85.5,
            "match_date": "2025-01-01T10:00:00Z",
        }
        await cluster_manager.set_matches("match:456:789", match_data, ttl=86400)

        # Test analytics operations
        analytics_data = {
            "event_type": "profile_view",
            "user_id": 456,
            "timestamp": "2025-01-01T10:00:00Z",
            "metadata": {"viewed_profile": 789},
        }
        await cluster_manager.set_analytics(
            "analytics:456:profile_view", analytics_data, ttl=604800
        )

        # Test sentiment operations
        sentiment_data = {
            "message_id": "msg_123",
            "sentiment_score": 0.85,
            "emotions": {"joy": 0.8, "excitement": 0.7},
            "confidence": 0.92,
        }
        await cluster_manager.set_sentiment(
            "sentiment:msg_123", sentiment_data, ttl=2592000
        )

        # Verify all operations were called
        assert cluster_manager.cluster.set.call_count == 5


class TestCacheMetrics:
    """Test cache metrics collection and calculation"""

    def test_metrics_initialization(self):
        """Test metrics object initialization"""
        metrics = CacheMetrics()
        assert metrics.total_requests == 0
        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 0
        assert len(metrics.response_times) == 0
        assert metrics.hit_ratio == 0.0
        assert metrics.average_response_time == 0.0

    def test_metrics_recording(self):
        """Test recording cache operations"""
        metrics = CacheMetrics()

        # Record cache hit
        metrics.record_hit(25.5)  # 25.5ms response time
        assert metrics.cache_hits == 1
        assert metrics.total_requests == 1
        assert metrics.hit_ratio == 1.0
        assert metrics.average_response_time == 25.5

        # Record cache miss
        metrics.record_miss(45.0)  # 45.0ms response time
        assert metrics.cache_misses == 1
        assert metrics.total_requests == 2
        assert metrics.hit_ratio == 0.5
        assert metrics.average_response_time == 35.25  # (25.5 + 45.0) / 2

    def test_metrics_calculation(self):
        """Test metrics calculations with multiple data points"""
        metrics = CacheMetrics()

        # Record multiple operations
        response_times = [10, 15, 20, 25, 30, 35, 40, 45, 50]
        for i, rt in enumerate(response_times):
            if i % 2 == 0:  # Even indices are hits
                metrics.record_hit(rt)
            else:  # Odd indices are misses
                metrics.record_miss(rt)

        assert metrics.total_requests == 9
        assert metrics.cache_hits == 5
        assert metrics.cache_misses == 4
        assert metrics.hit_ratio == 5 / 9
        assert metrics.average_response_time == sum(response_times) / len(
            response_times
        )

    def test_metrics_edge_cases(self):
        """Test metrics edge cases"""
        metrics = CacheMetrics()

        # Test with no requests
        assert metrics.hit_ratio == 0.0
        assert metrics.average_response_time == 0.0

        # Test with only hits
        metrics.record_hit(10)
        metrics.record_hit(20)
        assert metrics.hit_ratio == 1.0

        # Reset and test with only misses
        metrics = CacheMetrics()
        metrics.record_miss(10)
        metrics.record_miss(20)
        assert metrics.hit_ratio == 0.0


if __name__ == "__main__":
    """
    Run unit tests directly
    Usage: python test_redis_cluster_manager.py
    """
    pytest.main([__file__, "-v", "--tb=short"])
