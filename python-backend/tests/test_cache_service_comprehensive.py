import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import time
import json
import pickle
import gzip
import base64
from datetime import datetime, timedelta

from app.services.cache_service import (
    CacheService,
    CacheLevel,
    CacheStrategy,
    CachePolicy,
    CacheMetrics
)


class TestCacheService:
    
    @pytest.fixture
    def mock_redis(self):
        mock_redis = Mock()
        mock_redis.get = Mock()
        mock_redis.set = Mock()
        mock_redis.delete = Mock()
        mock_redis.exists = Mock()
        mock_redis.keys = Mock()
        mock_redis.flushdb = Mock()
        mock_redis.expire = Mock()
        mock_redis.ttl = Mock()
        mock_redis.pipeline = Mock()
        return mock_redis
    
    @pytest.fixture
    def cache_service(self, mock_redis):
        with patch.object(CacheService, '_setup_cache_warming'):
            return CacheService(mock_redis)
    
    @pytest.fixture
    def sample_cache_policy(self):
        return CachePolicy(
            ttl=3600,
            max_size=1000,
            compression=True,
            serialization="json",
            invalidation_tags=["test_tag"]
        )

    def test_cache_service_initialization(self, cache_service, mock_redis):
        """Test cache service initialization"""
        assert cache_service.redis_client == mock_redis
        assert isinstance(cache_service.l1_cache, dict)
        assert isinstance(cache_service.cache_policies, dict)
        assert isinstance(cache_service.metrics, CacheMetrics)

    def test_cache_policies_setup(self, cache_service):
        """Test cache policies are properly configured"""
        policies = cache_service.cache_policies
        
        # Test user profile policy
        user_profile_policy = policies["user_profile"]
        assert user_profile_policy.ttl == 3600
        assert user_profile_policy.compression is True
        assert "user_data" in user_profile_policy.invalidation_tags
        
        # Test match recommendations policy
        match_policy = policies["match_recommendations"]
        assert match_policy.ttl == 900
        assert match_policy.max_size == 1000
        assert "matching_algorithm" in match_policy.invalidation_tags
        
        # Test conversation threads policy
        conv_policy = policies["conversation_threads"]
        assert conv_policy.ttl == 600
        assert "new_messages" in conv_policy.invalidation_tags

    def test_cache_level_enum_values(self):
        """Test CacheLevel enum values"""
        assert CacheLevel.L1_MEMORY.value == "l1_memory"
        assert CacheLevel.L2_REDIS.value == "l2_redis"
        assert CacheLevel.L3_DATABASE.value == "l3_database"

    def test_cache_strategy_enum_values(self):
        """Test CacheStrategy enum values"""
        assert CacheStrategy.WRITE_THROUGH.value == "write_through"
        assert CacheStrategy.WRITE_BEHIND.value == "write_behind"
        assert CacheStrategy.READ_THROUGH.value == "read_through"
        assert CacheStrategy.CACHE_ASIDE.value == "cache_aside"

    def test_cache_policy_dataclass(self, sample_cache_policy):
        """Test CachePolicy dataclass"""
        assert sample_cache_policy.ttl == 3600
        assert sample_cache_policy.max_size == 1000
        assert sample_cache_policy.compression is True
        assert sample_cache_policy.serialization == "json"
        assert "test_tag" in sample_cache_policy.invalidation_tags

    def test_cache_metrics_dataclass(self):
        """Test CacheMetrics dataclass"""
        metrics = CacheMetrics()
        assert metrics.hits == 0
        assert metrics.misses == 0
        assert metrics.evictions == 0
        assert metrics.memory_usage == 0
        assert metrics.total_requests == 0
        assert metrics.avg_response_time == 0.0

    def test_get_from_l1_cache_hit(self, cache_service):
        """Test getting value from L1 cache (hit)"""
        # Pre-populate L1 cache
        cache_service.l1_cache["test_key"] = "test_value"
        
        result = cache_service.get("test_key")
        
        assert result == "test_value"
        assert cache_service.metrics.hits == 1
        assert cache_service.metrics.total_requests == 1

    def test_get_from_redis_cache_hit(self, cache_service, mock_redis):
        """Test getting value from Redis cache (L1 miss, L2 hit)"""
        # L1 cache miss
        cache_service.l1_cache = {}
        
        # Mock Redis hit
        mock_redis.get.return_value = b'{"data": "test_value"}'
        
        with patch.object(cache_service, '_deserialize', return_value="test_value"):
            with patch.object(cache_service, '_store_l1_cache') as mock_store_l1:
                result = cache_service.get("test_key")
                
                assert result == "test_value"
                mock_redis.get.assert_called_once_with("test_key")
                mock_store_l1.assert_called_once_with("test_key", "test_value")
                assert cache_service.metrics.hits == 1

    def test_get_cache_miss(self, cache_service, mock_redis):
        """Test cache miss (both L1 and L2)"""
        # L1 cache miss
        cache_service.l1_cache = {}
        
        # Redis miss
        mock_redis.get.return_value = None
        
        result = cache_service.get("test_key", default="default_value")
        
        assert result == "default_value"
        assert cache_service.metrics.misses == 1
        assert cache_service.metrics.total_requests == 1

    def test_get_with_error_handling(self, cache_service, mock_redis):
        """Test get method error handling"""
        cache_service.l1_cache = {}
        mock_redis.get.side_effect = Exception("Redis error")
        
        result = cache_service.get("test_key", default="default_value")
        
        assert result == "default_value"

    def test_set_with_default_policy(self, cache_service, mock_redis):
        """Test setting value with default policy"""
        with patch.object(cache_service, '_get_cache_policy') as mock_get_policy:
            with patch.object(cache_service, '_serialize', return_value=b'serialized_data') as mock_serialize:
                with patch.object(cache_service, '_store_l1_cache') as mock_store_l1:
                    mock_policy = CachePolicy(ttl=3600)
                    mock_get_policy.return_value = mock_policy
                    
                    result = cache_service.set("test_key", "test_value")
                    
                    assert result is True
                    mock_redis.set.assert_called_once_with("test_key", b'serialized_data', ex=3600)
                    mock_store_l1.assert_called_once_with("test_key", "test_value")

    def test_set_with_custom_ttl(self, cache_service, mock_redis):
        """Test setting value with custom TTL"""
        with patch.object(cache_service, '_get_cache_policy') as mock_get_policy:
            with patch.object(cache_service, '_serialize', return_value=b'serialized_data'):
                with patch.object(cache_service, '_store_l1_cache'):
                    mock_policy = CachePolicy(ttl=3600)
                    mock_get_policy.return_value = mock_policy
                    
                    result = cache_service.set("test_key", "test_value", ttl=7200)
                    
                    assert result is True
                    mock_redis.set.assert_called_once_with("test_key", b'serialized_data', ex=7200)

    def test_set_with_policy_name(self, cache_service, mock_redis):
        """Test setting value with specific policy name"""
        with patch.object(cache_service, '_get_cache_policy') as mock_get_policy:
            with patch.object(cache_service, '_serialize', return_value=b'serialized_data'):
                with patch.object(cache_service, '_store_l1_cache'):
                    mock_policy = CachePolicy(ttl=1800)
                    mock_get_policy.return_value = mock_policy
                    
                    result = cache_service.set("test_key", "test_value", policy_name="user_profile")
                    
                    assert result is True
                    mock_get_policy.assert_called_once_with("test_key", "user_profile")

    def test_set_large_value_skips_l1(self, cache_service, mock_redis):
        """Test that large values skip L1 cache"""
        large_value = "x" * 20000  # 20KB value
        
        with patch.object(cache_service, '_get_cache_policy') as mock_get_policy:
            with patch.object(cache_service, '_serialize', return_value=b'serialized_data'):
                with patch.object(cache_service, '_store_l1_cache') as mock_store_l1:
                    mock_policy = CachePolicy(ttl=3600)
                    mock_get_policy.return_value = mock_policy
                    
                    result = cache_service.set("test_key", large_value)
                    
                    assert result is True
                    mock_redis.set.assert_called_once()
                    mock_store_l1.assert_not_called()  # Should skip L1 for large values

    def test_set_with_error_handling(self, cache_service, mock_redis):
        """Test set method error handling"""
        mock_redis.set.side_effect = Exception("Redis error")
        
        with patch.object(cache_service, '_get_cache_policy') as mock_get_policy:
            with patch.object(cache_service, '_serialize', return_value=b'serialized_data'):
                mock_policy = CachePolicy(ttl=3600)
                mock_get_policy.return_value = mock_policy
                
                result = cache_service.set("test_key", "test_value")
                
                assert result is False

    def test_delete_from_all_layers(self, cache_service, mock_redis):
        """Test deleting from all cache layers"""
        # Pre-populate L1 cache
        cache_service.l1_cache["test_key"] = "test_value"
        
        result = cache_service.delete("test_key")
        
        assert result is True
        assert "test_key" not in cache_service.l1_cache
        mock_redis.delete.assert_called_once_with("test_key")

    def test_delete_with_error_handling(self, cache_service, mock_redis):
        """Test delete method error handling"""
        mock_redis.delete.side_effect = Exception("Redis error")
        
        result = cache_service.delete("test_key")
        
        assert result is False

    def test_exists_in_l1_cache(self, cache_service, mock_redis):
        """Test exists check finds key in L1 cache"""
        cache_service.l1_cache["test_key"] = "test_value"
        
        result = cache_service.exists("test_key")
        
        assert result is True
        mock_redis.exists.assert_not_called()  # Should not check Redis if found in L1

    def test_exists_in_redis_cache(self, cache_service, mock_redis):
        """Test exists check finds key in Redis cache"""
        cache_service.l1_cache = {}
        mock_redis.exists.return_value = 1
        
        result = cache_service.exists("test_key")
        
        assert result is True
        mock_redis.exists.assert_called_once_with("test_key")

    def test_exists_not_found(self, cache_service, mock_redis):
        """Test exists check when key not found"""
        cache_service.l1_cache = {}
        mock_redis.exists.return_value = 0
        
        result = cache_service.exists("test_key")
        
        assert result is False

    def test_clear_l1_cache(self, cache_service):
        """Test clearing L1 cache"""
        cache_service.l1_cache = {"key1": "value1", "key2": "value2"}
        
        cache_service.clear_l1_cache()
        
        assert len(cache_service.l1_cache) == 0

    def test_clear_all_cache(self, cache_service, mock_redis):
        """Test clearing all cache layers"""
        cache_service.l1_cache = {"key1": "value1"}
        
        cache_service.clear_all()
        
        assert len(cache_service.l1_cache) == 0
        mock_redis.flushdb.assert_called_once()

    def test_get_cache_metrics(self, cache_service):
        """Test getting cache metrics"""
        # Simulate some cache operations
        cache_service.metrics.hits = 10
        cache_service.metrics.misses = 5
        cache_service.metrics.total_requests = 15
        
        metrics = cache_service.get_metrics()
        
        assert metrics.hits == 10
        assert metrics.misses == 5
        assert metrics.total_requests == 15
        
        # Test hit rate calculation
        hit_rate = cache_service.get_hit_rate()
        assert hit_rate == 10/15  # 66.67%

    def test_get_hit_rate_no_requests(self, cache_service):
        """Test hit rate calculation with no requests"""
        hit_rate = cache_service.get_hit_rate()
        
        assert hit_rate == 0.0

    def test_invalidate_by_tag(self, cache_service, mock_redis):
        """Test cache invalidation by tag"""
        mock_redis.keys.return_value = [b"user_profile:123", b"user_profile:456"]
        
        with patch.object(cache_service, '_get_keys_by_tag', return_value=["user_profile:123", "user_profile:456"]):
            result = cache_service.invalidate_by_tag("user_data")
            
            assert result == 2
            # Should delete from L1 cache
            assert "user_profile:123" not in cache_service.l1_cache
            assert "user_profile:456" not in cache_service.l1_cache

    def test_invalidate_by_pattern(self, cache_service, mock_redis):
        """Test cache invalidation by pattern"""
        mock_redis.keys.return_value = [b"user_profile:*"]
        
        result = cache_service.invalidate_by_pattern("user_profile:*")
        
        assert result >= 0
        mock_redis.keys.assert_called_once_with("user_profile:*")

    def test_get_cache_size(self, cache_service, mock_redis):
        """Test getting cache size information"""
        cache_service.l1_cache = {"key1": "value1", "key2": "value2"}
        mock_redis.dbsize.return_value = 100
        
        with patch.object(cache_service, '_calculate_l1_memory_usage', return_value=1024):
            size_info = cache_service.get_cache_size()
            
            assert size_info["l1_items"] == 2
            assert size_info["l1_memory_bytes"] == 1024
            assert size_info["l2_items"] == 100

    def test_set_expiration(self, cache_service, mock_redis):
        """Test setting expiration for existing key"""
        result = cache_service.set_expiration("test_key", 3600)
        
        assert result is True
        mock_redis.expire.assert_called_once_with("test_key", 3600)

    def test_get_ttl(self, cache_service, mock_redis):
        """Test getting TTL for key"""
        mock_redis.ttl.return_value = 1800
        
        result = cache_service.get_ttl("test_key")
        
        assert result == 1800
        mock_redis.ttl.assert_called_once_with("test_key")

    def test_batch_get(self, cache_service, mock_redis):
        """Test batch getting multiple keys"""
        keys = ["key1", "key2", "key3"]
        
        # Mock pipeline operations
        mock_pipeline = Mock()
        mock_pipeline.get = Mock()
        mock_pipeline.execute.return_value = [b'value1', None, b'value3']
        mock_redis.pipeline.return_value = mock_pipeline
        
        with patch.object(cache_service, '_deserialize', side_effect=lambda x, k: x.decode() if x else None):
            results = cache_service.batch_get(keys)
            
            assert results == {"key1": "value1", "key2": None, "key3": "value3"}

    def test_batch_set(self, cache_service, mock_redis):
        """Test batch setting multiple key-value pairs"""
        data = {"key1": "value1", "key2": "value2", "key3": "value3"}
        
        # Mock pipeline operations
        mock_pipeline = Mock()
        mock_pipeline.set = Mock()
        mock_pipeline.execute.return_value = [True, True, True]
        mock_redis.pipeline.return_value = mock_pipeline
        
        with patch.object(cache_service, '_serialize', side_effect=lambda v, p: v.encode()):
            with patch.object(cache_service, '_get_cache_policy') as mock_get_policy:
                mock_policy = CachePolicy(ttl=3600)
                mock_get_policy.return_value = mock_policy
                
                result = cache_service.batch_set(data)
                
                assert result is True
                assert mock_pipeline.set.call_count == 3

    def test_batch_delete(self, cache_service, mock_redis):
        """Test batch deleting multiple keys"""
        keys = ["key1", "key2", "key3"]
        
        # Pre-populate L1 cache
        for key in keys:
            cache_service.l1_cache[key] = f"value_{key}"
        
        mock_redis.delete.return_value = 3
        
        result = cache_service.batch_delete(keys)
        
        assert result == 3
        # Should remove from L1 cache
        for key in keys:
            assert key not in cache_service.l1_cache
        mock_redis.delete.assert_called_once_with(*keys)

    def test_cache_decorator(self, cache_service):
        """Test cache decorator functionality"""
        @cache_service.cached(key_func=lambda x: f"test_func:{x}", ttl=300)
        def expensive_function(param):
            return f"computed_result_{param}"
        
        with patch.object(cache_service, 'get', return_value=None) as mock_get:
            with patch.object(cache_service, 'set', return_value=True) as mock_set:
                result = expensive_function("test_param")
                
                assert result == "computed_result_test_param"
                mock_get.assert_called_once_with("test_func:test_param")
                mock_set.assert_called_once_with("test_func:test_param", "computed_result_test_param", ttl=300, policy_name=None)

    def test_cache_decorator_cache_hit(self, cache_service):
        """Test cache decorator with cache hit"""
        @cache_service.cached(key_func=lambda x: f"test_func:{x}", ttl=300)
        def expensive_function(param):
            return f"computed_result_{param}"
        
        with patch.object(cache_service, 'get', return_value="cached_result") as mock_get:
            with patch.object(cache_service, 'set') as mock_set:
                result = expensive_function("test_param")
                
                assert result == "cached_result"
                mock_get.assert_called_once()
                mock_set.assert_not_called()  # Should not set if cache hit

    def test_serialize_json(self, cache_service):
        """Test JSON serialization"""
        policy = CachePolicy(ttl=3600, serialization="json")
        data = {"key": "value", "number": 123}
        
        result = cache_service._serialize(data, policy)
        
        assert isinstance(result, bytes)
        # Should be able to deserialize back
        deserialized = json.loads(result.decode())
        assert deserialized == data

    def test_serialize_pickle(self, cache_service):
        """Test pickle serialization"""
        policy = CachePolicy(ttl=3600, serialization="pickle")
        data = {"key": "value", "complex_object": datetime.now()}
        
        result = cache_service._serialize(data, policy)
        
        assert isinstance(result, bytes)
        # Should be able to deserialize back
        deserialized = pickle.loads(result)
        assert deserialized["key"] == data["key"]

    def test_serialize_with_compression(self, cache_service):
        """Test serialization with compression"""
        policy = CachePolicy(ttl=3600, compression=True, serialization="json")
        large_data = {"key": "x" * 1000}  # Large data that benefits from compression
        
        result = cache_service._serialize(large_data, policy)
        
        assert isinstance(result, bytes)
        # Result should be compressed
        assert len(result) < len(json.dumps(large_data).encode())

    def test_deserialize_json(self, cache_service):
        """Test JSON deserialization"""
        data = {"key": "value", "number": 123}
        serialized = json.dumps(data).encode()
        
        result = cache_service._deserialize(serialized, "test_key")
        
        assert result == data

    def test_deserialize_compressed(self, cache_service):
        """Test deserialization of compressed data"""
        data = {"key": "value"}
        json_data = json.dumps(data).encode()
        compressed_data = base64.b64encode(gzip.compress(json_data))
        
        # Mock policy with compression
        with patch.object(cache_service, '_get_cache_policy') as mock_get_policy:
            mock_policy = CachePolicy(ttl=3600, compression=True, serialization="json")
            mock_get_policy.return_value = mock_policy
            
            result = cache_service._deserialize(compressed_data, "test_key")
            
            assert result == data

    def test_get_cache_policy_by_name(self, cache_service):
        """Test getting cache policy by name"""
        policy = cache_service._get_cache_policy("test_key", "user_profile")
        
        assert policy.ttl == 3600
        assert policy.compression is True

    def test_get_cache_policy_by_key_pattern(self, cache_service):
        """Test getting cache policy by key pattern"""
        policy = cache_service._get_cache_policy("user_profile:123", None)
        
        assert policy.ttl == 3600  # Should match user_profile policy

    def test_get_cache_policy_default(self, cache_service):
        """Test getting default cache policy"""
        policy = cache_service._get_cache_policy("unknown_key", None)
        
        assert policy.ttl == 3600  # Default TTL
        assert policy.compression is False

    def test_store_l1_cache_with_limit(self, cache_service):
        """Test L1 cache storage with size limit"""
        # Fill L1 cache to near capacity
        for i in range(950):  # Assuming 1000 is the limit
            cache_service.l1_cache[f"key_{i}"] = f"value_{i}"
        
        # Should store new item
        cache_service._store_l1_cache("new_key", "new_value")
        
        assert "new_key" in cache_service.l1_cache

    def test_update_metrics(self, cache_service):
        """Test metrics updating"""
        initial_hits = cache_service.metrics.hits
        initial_requests = cache_service.metrics.total_requests
        
        cache_service._update_metrics(hit=True, response_time=0.1)
        
        assert cache_service.metrics.hits == initial_hits + 1
        assert cache_service.metrics.total_requests == initial_requests + 1

    def test_calculate_l1_memory_usage(self, cache_service):
        """Test L1 cache memory usage calculation"""
        cache_service.l1_cache = {
            "key1": "value1",
            "key2": "value2" * 100  # Larger value
        }
        
        memory_usage = cache_service._calculate_l1_memory_usage()
        
        assert memory_usage > 0
        assert isinstance(memory_usage, int)

    def test_preload_user_profile(self, cache_service):
        """Test user profile preloading"""
        with patch.object(cache_service, '_fetch_user_profile_from_db', return_value={"name": "John"}):
            with patch.object(cache_service, 'set') as mock_set:
                cache_service._preload_user_profile(123)
                
                mock_set.assert_called_once_with("user_profile:123", {"name": "John"}, policy_name="user_profile")

    def test_preload_conversation_thread(self, cache_service):
        """Test conversation thread preloading"""
        with patch.object(cache_service, '_fetch_conversation_from_db', return_value={"messages": []}):
            with patch.object(cache_service, 'set') as mock_set:
                cache_service._preload_conversation_thread(456)
                
                mock_set.assert_called_once_with("conversation_threads:456", {"messages": []}, policy_name="conversation_threads")

    def test_get_popular_user_ids(self, cache_service):
        """Test getting popular user IDs"""
        with patch.object(cache_service, '_query_popular_users', return_value=[123, 456, 789]):
            result = cache_service._get_popular_user_ids()
            
            assert result == [123, 456, 789]

    def test_get_active_conversation_ids(self, cache_service):
        """Test getting active conversation IDs"""
        with patch.object(cache_service, '_query_active_conversations', return_value=["conv_1", "conv_2"]):
            result = cache_service._get_active_conversation_ids()
            
            assert result == ["conv_1", "conv_2"]

    def test_concurrent_cache_operations(self, cache_service, mock_redis):
        """Test concurrent cache operations"""
        import threading
        import time
        
        results = []
        errors = []
        
        def cache_operation(thread_id):
            try:
                # Simulate concurrent get/set operations
                cache_service.set(f"key_{thread_id}", f"value_{thread_id}")
                result = cache_service.get(f"key_{thread_id}")
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=cache_operation, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All operations should complete without errors
        assert len(errors) == 0
        assert len(results) == 10

    def test_cache_warming_disabled_during_test(self, mock_redis):
        """Test that cache warming is properly disabled during testing"""
        with patch.object(CacheService, '_setup_cache_warming') as mock_warming:
            cache_service = CacheService(mock_redis)
            
            # Cache warming should be called during initialization
            mock_warming.assert_called_once()

    def test_performance_with_large_dataset(self, cache_service, mock_redis):
        """Test cache performance with large dataset"""
        import time
        
        # Test setting many items
        start_time = time.time()
        
        for i in range(100):
            cache_service.set(f"perf_key_{i}", f"perf_value_{i}")
        
        set_time = time.time() - start_time
        
        # Test getting many items
        start_time = time.time()
        
        for i in range(100):
            cache_service.get(f"perf_key_{i}")
        
        get_time = time.time() - start_time
        
        # Operations should complete in reasonable time
        assert set_time < 1.0  # Should set 100 items in under 1 second
        assert get_time < 0.5  # Should get 100 items in under 0.5 seconds

    def test_cache_invalidation_cascade(self, cache_service, mock_redis):
        """Test cache invalidation cascades properly"""
        # Set up cache with tagged items
        cache_service.set("user_profile:123", {"name": "John"}, policy_name="user_profile")
        cache_service.set("emotional_profile:123", {"trait": "openness"}, policy_name="emotional_profile")
        
        with patch.object(cache_service, '_get_keys_by_tag') as mock_get_keys:
            mock_get_keys.return_value = ["user_profile:123", "emotional_profile:123"]
            
            # Invalidate by user_data tag
            invalidated_count = cache_service.invalidate_by_tag("user_data")
            
            assert invalidated_count == 2

    def test_memory_pressure_handling(self, cache_service):
        """Test handling of memory pressure in L1 cache"""
        # Fill L1 cache beyond reasonable limits
        large_data = "x" * 1000
        
        with patch.object(cache_service, '_check_memory_pressure', return_value=True):
            with patch.object(cache_service, '_evict_lru_items') as mock_evict:
                cache_service._store_l1_cache("memory_test", large_data)
                
                # Should trigger eviction when under memory pressure
                mock_evict.assert_called_once()

    def test_error_recovery_redis_unavailable(self, cache_service, mock_redis):
        """Test error recovery when Redis is unavailable"""
        # Simulate Redis being unavailable
        mock_redis.get.side_effect = Exception("Redis connection failed")
        mock_redis.set.side_effect = Exception("Redis connection failed")
        
        # Should fall back gracefully
        result_get = cache_service.get("test_key", default="fallback")
        result_set = cache_service.set("test_key", "test_value")
        
        assert result_get == "fallback"
        assert result_set is False  # Should fail gracefully

    def test_serialization_format_compatibility(self, cache_service):
        """Test compatibility between different serialization formats"""
        test_data = {"string": "test", "number": 123, "list": [1, 2, 3]}
        
        # Test JSON serialization
        json_policy = CachePolicy(ttl=3600, serialization="json")
        json_serialized = cache_service._serialize(test_data, json_policy)
        json_deserialized = cache_service._deserialize(json_serialized, "test_key")
        
        # Test pickle serialization
        pickle_policy = CachePolicy(ttl=3600, serialization="pickle")
        pickle_serialized = cache_service._serialize(test_data, pickle_policy)
        pickle_deserialized = cache_service._deserialize(pickle_serialized, "test_key")
        
        # Both should produce the same result
        assert json_deserialized == test_data
        assert pickle_deserialized == test_data