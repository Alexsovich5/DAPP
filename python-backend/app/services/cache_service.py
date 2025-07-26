# Advanced Caching Service for Dinner First
# Multi-layer caching with Redis, application-level caching, and CDN integration

from typing import Dict, List, Optional, Any, Union, Callable, TypeVar
from datetime import datetime, timedelta
from enum import Enum
import json
import pickle
import hashlib
import logging
import asyncio
from dataclasses import dataclass, asdict
from functools import wraps
import redis
from redis.connection import ConnectionPool
import time
import gzip
import base64

logger = logging.getLogger(__name__)

T = TypeVar('T')

class CacheLevel(Enum):
    L1_MEMORY = "l1_memory"        # In-memory cache (fastest)
    L2_REDIS = "l2_redis"          # Redis cache (fast)
    L3_DATABASE = "l3_database"    # Database cache (slower)

class CacheStrategy(Enum):
    WRITE_THROUGH = "write_through"    # Write to cache and DB simultaneously
    WRITE_BEHIND = "write_behind"      # Write to cache first, DB later
    READ_THROUGH = "read_through"      # Read from cache, fallback to DB
    CACHE_ASIDE = "cache_aside"        # Manual cache management

@dataclass
class CachePolicy:
    ttl: int                          # Time to live in seconds
    max_size: Optional[int] = None    # Maximum cache size
    compression: bool = False         # Enable compression for large objects
    serialization: str = "json"      # json, pickle, or msgpack
    invalidation_tags: List[str] = None  # Tags for cache invalidation
    
@dataclass
class CacheMetrics:
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    memory_usage: int = 0
    total_requests: int = 0
    avg_response_time: float = 0.0

class CacheService:
    """
    Advanced multi-layer caching service optimized for dating platform
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.l1_cache: Dict[str, Any] = {}  # In-memory cache
        self.cache_policies: Dict[str, CachePolicy] = {}
        self.metrics = CacheMetrics()
        
        # Dating platform specific cache configurations
        self._setup_cache_policies()
        
        # Cache warming for frequently accessed data
        self._setup_cache_warming()
    
    def _setup_cache_policies(self):
        """Setup cache policies for different data types"""
        
        self.cache_policies = {
            # User profiles - high read frequency
            "user_profile": CachePolicy(
                ttl=3600,  # 1 hour
                compression=True,
                invalidation_tags=["user_data", "profile_updates"]
            ),
            
            # Emotional profiles - moderate read frequency
            "emotional_profile": CachePolicy(
                ttl=7200,  # 2 hours
                compression=True,
                invalidation_tags=["profile_updates", "onboarding"]
            ),
            
            # Match recommendations - dynamic, short TTL
            "match_recommendations": CachePolicy(
                ttl=900,  # 15 minutes
                max_size=1000,
                invalidation_tags=["matching_algorithm", "user_preferences"]
            ),
            
            # Compatibility scores - computationally expensive
            "compatibility_scores": CachePolicy(
                ttl=1800,  # 30 minutes
                compression=True,
                invalidation_tags=["algorithm_updates", "profile_updates"]
            ),
            
            # Conversation threads - frequently accessed
            "conversation_threads": CachePolicy(
                ttl=600,  # 10 minutes
                invalidation_tags=["new_messages", "user_blocks"]
            ),
            
            # Revelation content - static until user changes
            "user_revelations": CachePolicy(
                ttl=86400,  # 24 hours
                compression=True,
                invalidation_tags=["revelation_updates", "profile_updates"]
            ),
            
            # Session data - short-lived but frequently accessed
            "user_sessions": CachePolicy(
                ttl=1800,  # 30 minutes
                invalidation_tags=["logout", "security_events"]
            ),
            
            # Search results - dynamic but cacheable
            "search_results": CachePolicy(
                ttl=300,  # 5 minutes
                max_size=500,
                invalidation_tags=["new_users", "profile_updates"]
            ),
            
            # API rate limiting data
            "rate_limits": CachePolicy(
                ttl=3600,  # 1 hour
                invalidation_tags=["security_events"]
            ),
            
            # Business analytics - can be slightly stale
            "business_metrics": CachePolicy(
                ttl=1800,  # 30 minutes
                compression=True,
                invalidation_tags=["data_refresh"]
            )
        }
    
    def _setup_cache_warming(self):
        """Setup cache warming for frequently accessed data"""
        
        # Start background task for cache warming
        import threading
        
        def cache_warmer():
            while True:
                try:
                    self._warm_popular_profiles()
                    self._warm_active_conversations()
                    time.sleep(300)  # Warm cache every 5 minutes
                except Exception as e:
                    logger.error(f"Cache warming error: {e}")
                    time.sleep(60)
        
        thread = threading.Thread(target=cache_warmer, daemon=True)
        thread.start()
    
    def _warm_popular_profiles(self):
        """Warm cache with popular user profiles"""
        try:
            # Get list of active users (this would come from database)
            popular_user_ids = self._get_popular_user_ids()
            
            for user_id in popular_user_ids[:100]:  # Top 100 users
                cache_key = f"user_profile:{user_id}"
                if not self.exists(cache_key):
                    # Pre-load profile data
                    self._preload_user_profile(user_id)
            
        except Exception as e:
            logger.error(f"Failed to warm popular profiles: {e}")
    
    def _warm_active_conversations(self):
        """Warm cache with active conversation data"""
        try:
            # Get active conversation IDs
            active_conversation_ids = self._get_active_conversation_ids()
            
            for conv_id in active_conversation_ids[:50]:  # Top 50 conversations
                cache_key = f"conversation_threads:{conv_id}"
                if not self.exists(cache_key):
                    self._preload_conversation_thread(conv_id)
            
        except Exception as e:
            logger.error(f"Failed to warm active conversations: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from multi-layer cache"""
        start_time = time.time()
        
        try:
            # Try L1 cache first (in-memory)
            if key in self.l1_cache:
                self._update_metrics(hit=True, response_time=time.time() - start_time)
                return self.l1_cache[key]
            
            # Try L2 cache (Redis)
            redis_value = self.redis_client.get(key)
            if redis_value:
                # Deserialize and potentially decompress
                value = self._deserialize(redis_value, key)
                
                # Store in L1 cache for faster future access
                self._store_l1_cache(key, value)
                
                self._update_metrics(hit=True, response_time=time.time() - start_time)
                return value
            
            # Cache miss
            self._update_metrics(hit=False, response_time=time.time() - start_time)
            return default
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, 
            policy_name: Optional[str] = None) -> bool:
        """Set value in multi-layer cache"""
        
        try:
            # Get cache policy
            policy = self._get_cache_policy(key, policy_name)
            cache_ttl = ttl or policy.ttl
            
            # Serialize and potentially compress
            serialized_value = self._serialize(value, policy)
            
            # Store in Redis (L2)
            self.redis_client.set(key, serialized_value, ex=cache_ttl)
            
            # Store in L1 cache if not too large
            if len(str(value)) < 10000:  # 10KB limit for L1 cache
                self._store_l1_cache(key, value)
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete from all cache layers"""
        try:
            # Remove from L1 cache
            self.l1_cache.pop(key, None)
            
            # Remove from Redis
            self.redis_client.delete(key)
            
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in any cache layer"""
        try:
            if key in self.l1_cache:
                return True
            
            return self.redis_client.exists(key) > 0
            
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    def invalidate_by_tags(self, tags: List[str]) -> int:
        """Invalidate cache entries by tags"""
        invalidated_count = 0
        
        try:
            # Get all keys that match the tags
            for tag in tags:
                pattern = f"*{tag}*"
                keys = self.redis_client.keys(pattern)
                
                for key in keys:
                    if isinstance(key, bytes):
                        key = key.decode()
                    
                    self.delete(key)
                    invalidated_count += 1
            
            logger.info(f"Invalidated {invalidated_count} cache entries for tags: {tags}")
            return invalidated_count
            
        except Exception as e:
            logger.error(f"Cache invalidation error for tags {tags}: {e}")
            return 0
    
    def get_or_set(self, key: str, factory_func: Callable[[], T], 
                   ttl: Optional[int] = None, policy_name: Optional[str] = None) -> T:
        """Get from cache or set using factory function"""
        
        # Try to get from cache first
        value = self.get(key)
        
        if value is not None:
            return value
        
        # Generate value using factory function
        try:
            new_value = factory_func()
            self.set(key, new_value, ttl, policy_name)
            return new_value
            
        except Exception as e:
            logger.error(f"Factory function error for key {key}: {e}")
            raise
    
    def mget(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple keys efficiently"""
        results = {}
        redis_keys = []
        
        # Check L1 cache first
        for key in keys:
            if key in self.l1_cache:
                results[key] = self.l1_cache[key]
            else:
                redis_keys.append(key)
        
        # Get remaining keys from Redis
        if redis_keys:
            try:
                redis_values = self.redis_client.mget(redis_keys)
                
                for i, key in enumerate(redis_keys):
                    if redis_values[i] is not None:
                        value = self._deserialize(redis_values[i], key)
                        results[key] = value
                        
                        # Store in L1 cache
                        self._store_l1_cache(key, value)
                
            except Exception as e:
                logger.error(f"Cache mget error: {e}")
        
        return results
    
    def mset(self, key_value_pairs: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple key-value pairs efficiently"""
        try:
            redis_pairs = {}
            
            for key, value in key_value_pairs.items():
                policy = self._get_cache_policy(key)
                serialized_value = self._serialize(value, policy)
                redis_pairs[key] = serialized_value
                
                # Store in L1 cache if small enough
                if len(str(value)) < 10000:
                    self._store_l1_cache(key, value)
            
            # Set all in Redis
            self.redis_client.mset(redis_pairs)
            
            # Set TTL for all keys
            if ttl:
                pipe = self.redis_client.pipeline()
                for key in redis_pairs.keys():
                    pipe.expire(key, ttl)
                pipe.execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Cache mset error: {e}")
            return False
    
    def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        """Atomic increment operation"""
        try:
            # Remove from L1 cache to avoid inconsistency
            self.l1_cache.pop(key, None)
            
            # Increment in Redis
            new_value = self.redis_client.incr(key, amount)
            
            # Set TTL if specified
            if ttl:
                self.redis_client.expire(key, ttl)
            
            return new_value
            
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return 0
    
    def get_cache_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics"""
        try:
            # Get Redis info
            redis_info = self.redis_client.info('memory')
            
            hit_ratio = (
                self.metrics.hits / self.metrics.total_requests
                if self.metrics.total_requests > 0 else 0
            )
            
            return {
                'cache_metrics': {
                    'hits': self.metrics.hits,
                    'misses': self.metrics.misses,
                    'hit_ratio': round(hit_ratio, 3),
                    'evictions': self.metrics.evictions,
                    'total_requests': self.metrics.total_requests,
                    'avg_response_time_ms': round(self.metrics.avg_response_time * 1000, 2),
                    'l1_cache_size': len(self.l1_cache),
                    'l1_memory_usage': sum(len(str(v)) for v in self.l1_cache.values())
                },
                'redis_metrics': {
                    'used_memory': redis_info.get('used_memory', 0),
                    'used_memory_human': redis_info.get('used_memory_human', '0B'),
                    'used_memory_peak': redis_info.get('used_memory_peak', 0),
                    'connected_clients': self.redis_client.info('clients').get('connected_clients', 0),
                    'total_commands_processed': self.redis_client.info('stats').get('total_commands_processed', 0)
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache metrics: {e}")
            return {}
    
    def cleanup_expired_l1_cache(self):
        """Clean up expired entries from L1 cache"""
        # Simple LRU cleanup - remove 25% of entries when cache is too large
        if len(self.l1_cache) > 1000:
            keys_to_remove = list(self.l1_cache.keys())[:250]
            for key in keys_to_remove:
                self.l1_cache.pop(key, None)
                self.metrics.evictions += 1
    
    # Private helper methods
    
    def _get_cache_policy(self, key: str, policy_name: Optional[str] = None) -> CachePolicy:
        """Get cache policy for a key"""
        if policy_name and policy_name in self.cache_policies:
            return self.cache_policies[policy_name]
        
        # Infer policy from key prefix
        for policy_prefix, policy in self.cache_policies.items():
            if key.startswith(policy_prefix):
                return policy
        
        # Default policy
        return CachePolicy(ttl=300)
    
    def _serialize(self, value: Any, policy: CachePolicy) -> bytes:
        """Serialize value based on cache policy"""
        try:
            if policy.serialization == "json":
                serialized = json.dumps(value, default=str)
            elif policy.serialization == "pickle":
                serialized = pickle.dumps(value)
            else:
                serialized = json.dumps(value, default=str)
            
            # Apply compression if enabled
            if policy.compression and len(serialized) > 1000:  # Only compress large objects
                if isinstance(serialized, str):
                    serialized = serialized.encode('utf-8')
                
                compressed = gzip.compress(serialized)
                return base64.b64encode(b'COMPRESSED:' + compressed)
            
            if isinstance(serialized, str):
                return serialized.encode('utf-8')
            
            return serialized
            
        except Exception as e:
            logger.error(f"Serialization error: {e}")
            raise
    
    def _deserialize(self, data: bytes, key: str) -> Any:
        """Deserialize value based on cache policy"""
        try:
            # Check if data is compressed
            if data.startswith(base64.b64encode(b'COMPRESSED:')):
                compressed_data = base64.b64decode(data)
                decompressed = gzip.decompress(compressed_data[11:])  # Remove 'COMPRESSED:' prefix
                data = decompressed
            
            # Determine serialization method
            policy = self._get_cache_policy(key)
            
            if policy.serialization == "pickle":
                return pickle.loads(data)
            else:
                return json.loads(data.decode('utf-8'))
                
        except Exception as e:
            logger.error(f"Deserialization error for key {key}: {e}")
            return None
    
    def _store_l1_cache(self, key: str, value: Any):
        """Store value in L1 cache with size limits"""
        try:
            # Check size limits
            if len(self.l1_cache) >= 1000:
                self.cleanup_expired_l1_cache()
            
            self.l1_cache[key] = value
            
        except Exception as e:
            logger.error(f"L1 cache store error: {e}")
    
    def _update_metrics(self, hit: bool, response_time: float):
        """Update cache metrics"""
        self.metrics.total_requests += 1
        
        if hit:
            self.metrics.hits += 1
        else:
            self.metrics.misses += 1
        
        # Update average response time
        self.metrics.avg_response_time = (
            (self.metrics.avg_response_time * (self.metrics.total_requests - 1) + response_time) /
            self.metrics.total_requests
        )
    
    # Mock methods for cache warming (would be implemented with actual database queries)
    
    def _get_popular_user_ids(self) -> List[int]:
        """Get list of popular user IDs for cache warming"""
        # Mock implementation - would query database for active users
        return list(range(1, 101))
    
    def _get_active_conversation_ids(self) -> List[int]:
        """Get list of active conversation IDs"""
        # Mock implementation - would query database for active conversations
        return list(range(1, 51))
    
    def _preload_user_profile(self, user_id: int):
        """Preload user profile data into cache"""
        # Mock implementation - would load from database
        profile_data = {"user_id": user_id, "name": f"User {user_id}"}
        self.set(f"user_profile:{user_id}", profile_data, policy_name="user_profile")
    
    def _preload_conversation_thread(self, conversation_id: int):
        """Preload conversation thread into cache"""
        # Mock implementation - would load from database
        thread_data = {"conversation_id": conversation_id, "messages": []}
        self.set(f"conversation_threads:{conversation_id}", thread_data, policy_name="conversation_threads")

# Decorators for easy caching

def cached(key_prefix: str, ttl: int = 300, policy_name: Optional[str] = None):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function arguments
            key_suffix = hashlib.md5(str(args + tuple(kwargs.items())).encode()).hexdigest()[:16]
            cache_key = f"{key_prefix}:{key_suffix}"
            
            # Use cache service (would be injected in real implementation)
            cache_service = get_cache_service()
            
            return cache_service.get_or_set(
                cache_key,
                lambda: func(*args, **kwargs),
                ttl,
                policy_name
            )
        
        return wrapper
    return decorator

def cache_invalidate(tags: List[str]):
    """Decorator for cache invalidation after function execution"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Invalidate cache after successful execution
            cache_service = get_cache_service()
            cache_service.invalidate_by_tags(tags)
            
            return result
        
        return wrapper
    return decorator

# Global cache service instance
_cache_service: Optional[CacheService] = None

def get_cache_service() -> CacheService:
    """Get global cache service instance"""
    global _cache_service
    if _cache_service is None:
        raise RuntimeError("Cache service not initialized")
    return _cache_service

def init_cache_service(redis_client: redis.Redis) -> CacheService:
    """Initialize global cache service"""
    global _cache_service
    _cache_service = CacheService(redis_client)
    return _cache_service