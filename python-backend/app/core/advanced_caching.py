"""
Advanced Multi-Level Caching Strategy for Sprint 8 - Enhanced Microservices Architecture
Intelligent caching with L1 (Redis), L2 (Database), predictive warming, and performance analytics
"""

import asyncio
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import structlog
from app.core.event_publisher import EventPublisher, EventType

# Import our Redis cluster manager and event publisher
from app.core.redis_cluster_manager import DatabaseType, RedisClusterManager
from prometheus_client import Counter, Gauge, Histogram

logger = structlog.get_logger(__name__)

# Prometheus metrics
CACHE_REQUESTS = Counter(
    "cache_requests_total",
    "Total cache requests",
    ["cache_level", "operation", "status"],
)
CACHE_HIT_RATIO = Gauge("cache_hit_ratio", "Cache hit ratio by level", ["cache_level"])
CACHE_RESPONSE_TIME = Histogram(
    "cache_response_time_seconds", "Cache response time", ["cache_level"]
)
CACHE_WARMING_OPERATIONS = Counter(
    "cache_warming_operations_total",
    "Cache warming operations",
    ["strategy", "status"],
)
CACHE_MEMORY_USAGE = Gauge(
    "cache_memory_usage_bytes", "Cache memory usage", ["cache_level"]
)
CACHE_EVICTIONS = Counter(
    "cache_evictions_total", "Cache evictions", ["cache_level", "reason"]
)


class CacheLevel(Enum):
    """Cache level types"""

    L1_REDIS = "L1_redis"
    L2_DATABASE = "L2_database"
    L3_MEMORY = "L3_memory"


class CacheStrategy(Enum):
    """Caching strategies"""

    WRITE_THROUGH = "write_through"
    WRITE_BACK = "write_back"
    WRITE_AROUND = "write_around"
    READ_THROUGH = "read_through"
    CACHE_ASIDE = "cache_aside"


class WarmingStrategy(Enum):
    """Cache warming strategies"""

    PREDICTIVE = "predictive"
    SCHEDULED = "scheduled"
    ON_DEMAND = "on_demand"
    PATTERN_BASED = "pattern_based"


class CacheAnalytics:
    """Cache performance analytics and monitoring"""

    def __init__(self):
        self.request_history: Dict[str, List[Dict[str, Any]]] = {}
        self.usage_patterns: Dict[str, Dict[str, Any]] = {}
        self.performance_metrics: Dict[CacheLevel, Dict[str, float]] = {}

        # Initialize metrics for each cache level
        for level in CacheLevel:
            self.performance_metrics[level] = {
                "hit_count": 0,
                "miss_count": 0,
                "total_requests": 0,
                "average_response_time": 0.0,
                "error_count": 0,
                "eviction_count": 0,
            }

    async def record_hit(
        self, cache_level: CacheLevel, key: str, response_time: float = 0.0
    ):
        """Record cache hit"""
        metrics = self.performance_metrics[cache_level]
        metrics["hit_count"] += 1
        metrics["total_requests"] += 1

        # Update average response time
        if metrics["total_requests"] > 1:
            metrics["average_response_time"] = (
                metrics["average_response_time"] * (metrics["total_requests"] - 1)
                + response_time
            ) / metrics["total_requests"]
        else:
            metrics["average_response_time"] = response_time

        # Update Prometheus metrics
        CACHE_REQUESTS.labels(
            cache_level=cache_level.value, operation="get", status="hit"
        ).inc()
        CACHE_RESPONSE_TIME.labels(cache_level=cache_level.value).observe(response_time)

        hit_ratio = metrics["hit_count"] / metrics["total_requests"]
        CACHE_HIT_RATIO.labels(cache_level=cache_level.value).set(hit_ratio)

        # Record usage pattern
        await self._record_usage_pattern(key, "hit", response_time)

    async def record_miss(self, cache_level: CacheLevel, key: str):
        """Record cache miss"""
        metrics = self.performance_metrics[cache_level]
        metrics["miss_count"] += 1
        metrics["total_requests"] += 1

        # Update Prometheus metrics
        CACHE_REQUESTS.labels(
            cache_level=cache_level.value, operation="get", status="miss"
        ).inc()

        hit_ratio = (
            metrics["hit_count"] / metrics["total_requests"]
            if metrics["total_requests"] > 0
            else 0
        )
        CACHE_HIT_RATIO.labels(cache_level=cache_level.value).set(hit_ratio)

        # Record usage pattern
        await self._record_usage_pattern(key, "miss")

    async def record_error(self, cache_level: CacheLevel, key: str, error: str):
        """Record cache error"""
        metrics = self.performance_metrics[cache_level]
        metrics["error_count"] += 1

        CACHE_REQUESTS.labels(
            cache_level=cache_level.value, operation="get", status="error"
        ).inc()

        logger.error(f"Cache error on {cache_level.value} for key {key}: {error}")

    async def record_eviction(
        self, cache_level: CacheLevel, key: str, reason: str = "ttl"
    ):
        """Record cache eviction"""
        metrics = self.performance_metrics[cache_level]
        metrics["eviction_count"] += 1

        CACHE_EVICTIONS.labels(cache_level=cache_level.value, reason=reason).inc()

    async def _record_usage_pattern(
        self, key: str, result: str, response_time: float = 0.0
    ):
        """Record usage pattern for predictive analytics"""
        pattern_key = self._get_pattern_key(key)

        if pattern_key not in self.usage_patterns:
            self.usage_patterns[pattern_key] = {
                "access_count": 0,
                "hit_count": 0,
                "miss_count": 0,
                "average_response_time": 0.0,
                "last_access": None,
                "access_frequency": 0.0,
                "access_times": [],
            }

        pattern = self.usage_patterns[pattern_key]
        pattern["access_count"] += 1

        if result == "hit":
            pattern["hit_count"] += 1
        else:
            pattern["miss_count"] += 1

        # Update response time
        if response_time > 0:
            if pattern["access_count"] > 1:
                pattern["average_response_time"] = (
                    pattern["average_response_time"] * (pattern["access_count"] - 1)
                    + response_time
                ) / pattern["access_count"]
            else:
                pattern["average_response_time"] = response_time

        # Record access time for frequency analysis
        now = datetime.utcnow()
        pattern["last_access"] = now.isoformat()
        pattern["access_times"].append(now)

        # Keep only recent access times (last 24 hours)
        cutoff_time = now - timedelta(hours=24)
        pattern["access_times"] = [
            t for t in pattern["access_times"] if t > cutoff_time
        ]

        # Calculate access frequency (accesses per hour)
        if len(pattern["access_times"]) > 1:
            time_span = (
                pattern["access_times"][-1] - pattern["access_times"][0]
            ).total_seconds() / 3600
            pattern["access_frequency"] = len(pattern["access_times"]) / max(
                time_span, 0.1
            )

    def _get_pattern_key(self, key: str) -> str:
        """Extract pattern key from cache key"""
        # Remove user-specific parts and IDs to find patterns
        # Example: "profile:123" -> "profile:*", "matches:user:456" -> "matches:user:*"
        import re

        pattern_key = re.sub(r":\d+", ":*", key)
        pattern_key = re.sub(r":[a-f0-9-]{32,}", ":*", pattern_key)  # Remove UUIDs
        return pattern_key

    def get_usage_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Get usage patterns for predictive analysis"""
        return self.usage_patterns.copy()

    def get_performance_metrics(self) -> Dict[str, Dict[str, float]]:
        """Get performance metrics for all cache levels"""
        return {
            level.value: metrics.copy()
            for level, metrics in self.performance_metrics.items()
        }


class CacheWarmingService:
    """Intelligent cache warming service with predictive capabilities"""

    def __init__(
        self,
        redis_manager: RedisClusterManager,
        cache_analytics: CacheAnalytics,
    ):
        self.redis_manager = redis_manager
        self.cache_analytics = cache_analytics
        self.warming_tasks: Dict[str, asyncio.Task] = {}
        self.warming_config: Dict[str, Dict[str, Any]] = {}

    async def warm_cache(
        self,
        key: str,
        fallback_func: Callable,
        ttl: int = 3600,
        priority: int = 1,
    ):
        """Warm cache with specific key"""
        try:
            start_time = time.time()

            # Check if already warming
            if key in self.warming_tasks:
                return

            # Create warming task
            task = asyncio.create_task(self._warm_single_key(key, fallback_func, ttl))
            self.warming_tasks[key] = task

            # Execute warming
            await task

            # Clean up completed task
            if key in self.warming_tasks:
                del self.warming_tasks[key]

            warming_time = time.time() - start_time
            CACHE_WARMING_OPERATIONS.labels(
                strategy="on_demand", status="success"
            ).inc()

            logger.debug(f"Cache warmed for key {key} in {warming_time:.3f}s")

        except Exception as e:
            CACHE_WARMING_OPERATIONS.labels(strategy="on_demand", status="error").inc()
            logger.error(f"Cache warming failed for key {key}: {e}")

    async def _warm_single_key(self, key: str, fallback_func: Callable, ttl: int):
        """Warm a single cache key"""
        try:
            # Execute fallback function to get fresh data
            fresh_value = await fallback_func()

            # Store in Redis
            await self.redis_manager.set_with_ttl(
                DatabaseType.USER_PROFILES,  # Default to profiles cache
                key,
                fresh_value,
                ttl,
            )

        except Exception as e:
            logger.error(f"Failed to warm cache key {key}: {e}")
            raise

    async def predictive_warming(self):
        """Predictively warm cache based on usage patterns"""
        try:
            usage_patterns = self.cache_analytics.get_usage_patterns()

            # Find high-probability keys to warm
            candidates = self._identify_warming_candidates(usage_patterns)

            for candidate in candidates:
                if candidate["probability"] > 0.7:  # High probability threshold
                    await self._schedule_predictive_warming(candidate)

            CACHE_WARMING_OPERATIONS.labels(
                strategy="predictive", status="success"
            ).inc()

        except Exception as e:
            CACHE_WARMING_OPERATIONS.labels(strategy="predictive", status="error").inc()
            logger.error(f"Predictive warming failed: {e}")

    def _identify_warming_candidates(
        self, usage_patterns: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify keys that should be warmed based on patterns"""
        candidates = []

        for pattern_key, pattern_data in usage_patterns.items():
            # Calculate warming priority based on multiple factors
            access_frequency = pattern_data.get("access_frequency", 0.0)
            hit_ratio = pattern_data.get("hit_count", 0) / max(
                pattern_data.get("access_count", 1), 1
            )

            # Higher frequency and lower hit ratio = good warming candidate
            warming_score = access_frequency * (1 - hit_ratio)

            if warming_score > 0.5:  # Minimum threshold
                candidates.append(
                    {
                        "pattern": pattern_key,
                        "probability": min(warming_score, 1.0),
                        "frequency": access_frequency,
                        "hit_ratio": hit_ratio,
                        "last_access": pattern_data.get("last_access"),
                    }
                )

        # Sort by probability (highest first)
        candidates.sort(key=lambda x: x["probability"], reverse=True)

        return candidates[:50]  # Limit to top 50 candidates

    async def _schedule_predictive_warming(self, candidate: Dict[str, Any]):
        """Schedule predictive warming for a candidate"""
        try:
            pattern = candidate["pattern"]

            # This would normally expand the pattern to actual keys
            # For now, we'll simulate this
            logger.info(
                f"Would warm cache pattern: {pattern} (probability: {candidate['probability']:.3f})"
            )

        except Exception as e:
            logger.error(f"Failed to schedule warming for {candidate}: {e}")


class IntelligentCacheManager:
    """
    Advanced multi-level cache manager with intelligent routing,
    predictive warming, and comprehensive analytics
    """

    def __init__(
        self,
        redis_manager: RedisClusterManager,
        db_session_factory: Optional[Callable] = None,
        event_publisher: Optional[EventPublisher] = None,
    ):

        self.redis_manager = redis_manager
        self.db_session_factory = db_session_factory
        self.event_publisher = event_publisher

        # Initialize components
        self.cache_analytics = CacheAnalytics()
        self.cache_warming = CacheWarmingService(redis_manager, self.cache_analytics)

        # Cache configuration
        self.default_strategy = CacheStrategy.CACHE_ASIDE
        self.cache_levels = [
            CacheLevel.L1_REDIS,
            CacheLevel.L2_DATABASE,
            CacheLevel.L3_MEMORY,
        ]

        # In-memory cache (L3)
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.memory_cache_ttl: Dict[str, datetime] = {}
        self.max_memory_cache_size = 1000  # Maximum number of items

        # Performance thresholds
        self.slow_query_threshold = 1.0  # 1 second
        self.cache_warming_threshold = 0.3  # 30% hit ratio

        logger.info("Intelligent Cache Manager initialized")

    async def smart_cache_get(
        self,
        key: str,
        fallback_func: Optional[Callable] = None,
        ttl: int = 3600,
        cache_levels: Optional[List[CacheLevel]] = None,
        database_type: DatabaseType = DatabaseType.USER_PROFILES,
    ) -> Optional[Any]:
        """
        Intelligent multi-level cache get with automatic fallback

        Args:
            key: Cache key
            fallback_func: Function to call on cache miss
            ttl: Time to live in seconds
            cache_levels: Cache levels to use (all if None)
            database_type: Redis database type to use

        Returns:
            Cached or fresh value
        """
        start_time = time.time()

        if cache_levels is None:
            cache_levels = self.cache_levels

        try:
            # Try L3 (Memory) cache first
            if CacheLevel.L3_MEMORY in cache_levels:
                value = await self._get_from_memory_cache(key)
                if value is not None:
                    response_time = time.time() - start_time
                    await self.cache_analytics.record_hit(
                        CacheLevel.L3_MEMORY, key, response_time
                    )
                    return value
                else:
                    await self.cache_analytics.record_miss(CacheLevel.L3_MEMORY, key)

            # Try L1 (Redis) cache
            if CacheLevel.L1_REDIS in cache_levels:
                value = await self._get_from_redis_cache(key, database_type)
                if value is not None:
                    response_time = time.time() - start_time
                    await self.cache_analytics.record_hit(
                        CacheLevel.L1_REDIS, key, response_time
                    )

                    # Promote to L3 if enabled
                    if CacheLevel.L3_MEMORY in cache_levels:
                        await self._set_memory_cache(key, value, ttl)

                    return value
                else:
                    await self.cache_analytics.record_miss(CacheLevel.L1_REDIS, key)

            # Try L2 (Database materialized views) cache
            if CacheLevel.L2_DATABASE in cache_levels and self.db_session_factory:
                value = await self._get_from_database_cache(key)
                if value is not None:
                    response_time = time.time() - start_time
                    await self.cache_analytics.record_hit(
                        CacheLevel.L2_DATABASE, key, response_time
                    )

                    # Promote to higher cache levels
                    if CacheLevel.L1_REDIS in cache_levels:
                        await self._set_redis_cache(key, value, ttl, database_type)
                    if CacheLevel.L3_MEMORY in cache_levels:
                        await self._set_memory_cache(key, value, ttl)

                    return value
                else:
                    await self.cache_analytics.record_miss(CacheLevel.L2_DATABASE, key)

            # All cache levels missed - use fallback function
            if fallback_func:
                fresh_value = await fallback_func()

                response_time = time.time() - start_time

                # Store in all requested cache levels
                await self._store_in_all_levels(
                    key, fresh_value, ttl, cache_levels, database_type
                )

                # Check if we should trigger cache warming
                await self._check_warming_triggers(key, response_time)

                return fresh_value

            return None

        except Exception as e:
            logger.error(f"Smart cache get failed for key {key}: {e}")
            return None

    async def smart_cache_set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600,
        cache_levels: Optional[List[CacheLevel]] = None,
        database_type: DatabaseType = DatabaseType.USER_PROFILES,
        strategy: CacheStrategy = CacheStrategy.CACHE_ASIDE,
    ) -> bool:
        """
        Intelligent cache set with strategy-based storage

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            cache_levels: Cache levels to use
            database_type: Redis database type
            strategy: Caching strategy to use

        Returns:
            True if successful
        """
        try:
            if cache_levels is None:
                cache_levels = self.cache_levels

            success = await self._store_in_all_levels(
                key, value, ttl, cache_levels, database_type
            )

            # Publish cache update event if event publisher is available
            if self.event_publisher:
                await self.event_publisher.publish_analytics_event(
                    EventType.PERFORMANCE_METRIC,
                    {
                        "event_type": "cache_set",
                        "cache_key": key,
                        "cache_levels": [level.value for level in cache_levels],
                        "strategy": strategy.value,
                        "ttl": ttl,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )

            return success

        except Exception as e:
            logger.error(f"Smart cache set failed for key {key}: {e}")
            return False

    async def smart_cache_delete(
        self,
        key: str,
        cache_levels: Optional[List[CacheLevel]] = None,
        database_type: DatabaseType = DatabaseType.USER_PROFILES,
    ) -> bool:
        """Delete key from specified cache levels"""
        try:
            if cache_levels is None:
                cache_levels = self.cache_levels

            success = True

            # Delete from memory cache
            if CacheLevel.L3_MEMORY in cache_levels:
                if key in self.memory_cache:
                    del self.memory_cache[key]
                if key in self.memory_cache_ttl:
                    del self.memory_cache_ttl[key]

            # Delete from Redis
            if CacheLevel.L1_REDIS in cache_levels:
                redis_success = await self.redis_manager.delete(database_type, key)
                success = success and redis_success

            # Delete from database cache (if applicable)
            if CacheLevel.L2_DATABASE in cache_levels and self.db_session_factory:
                db_success = await self._delete_from_database_cache(key)
                success = success and db_success

            return success

        except Exception as e:
            logger.error(f"Smart cache delete failed for key {key}: {e}")
            return False

    async def batch_cache_operations(
        self, operations: List[Dict[str, Any]]
    ) -> List[Any]:
        """Execute batch cache operations for better performance"""
        try:
            results = []

            # Group operations by type for optimization
            get_operations = [op for op in operations if op.get("operation") == "get"]
            set_operations = [op for op in operations if op.get("operation") == "set"]
            delete_operations = [
                op for op in operations if op.get("operation") == "delete"
            ]

            # Execute gets first (may inform sets)
            for op in get_operations:
                result = await self.smart_cache_get(
                    key=op["key"],
                    fallback_func=op.get("fallback_func"),
                    ttl=op.get("ttl", 3600),
                    cache_levels=op.get("cache_levels"),
                    database_type=op.get("database_type", DatabaseType.USER_PROFILES),
                )
                results.append(result)

            # Execute sets
            for op in set_operations:
                result = await self.smart_cache_set(
                    key=op["key"],
                    value=op["value"],
                    ttl=op.get("ttl", 3600),
                    cache_levels=op.get("cache_levels"),
                    database_type=op.get("database_type", DatabaseType.USER_PROFILES),
                )
                results.append(result)

            # Execute deletes
            for op in delete_operations:
                result = await self.smart_cache_delete(
                    key=op["key"],
                    cache_levels=op.get("cache_levels"),
                    database_type=op.get("database_type", DatabaseType.USER_PROFILES),
                )
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Batch cache operations failed: {e}")
            return []

    async def _get_from_memory_cache(self, key: str) -> Optional[Any]:
        """Get value from in-memory cache"""
        try:
            # Check if key exists and is not expired
            if key in self.memory_cache and key in self.memory_cache_ttl:
                if datetime.utcnow() < self.memory_cache_ttl[key]:
                    return self.memory_cache[key]["value"]
                else:
                    # Expired, remove from cache
                    del self.memory_cache[key]
                    del self.memory_cache_ttl[key]
                    await self.cache_analytics.record_eviction(
                        CacheLevel.L3_MEMORY, key, "ttl"
                    )

            return None

        except Exception as e:
            await self.cache_analytics.record_error(CacheLevel.L3_MEMORY, key, str(e))
            return None

    async def _set_memory_cache(self, key: str, value: Any, ttl: int):
        """Set value in in-memory cache"""
        try:
            # Check cache size limit
            if len(self.memory_cache) >= self.max_memory_cache_size:
                await self._evict_memory_cache_lru()

            # Store value with metadata
            self.memory_cache[key] = {
                "value": value,
                "created_at": datetime.utcnow(),
                "access_count": 0,
            }
            self.memory_cache_ttl[key] = datetime.utcnow() + timedelta(seconds=ttl)

        except Exception as e:
            await self.cache_analytics.record_error(CacheLevel.L3_MEMORY, key, str(e))

    async def _evict_memory_cache_lru(self):
        """Evict least recently used items from memory cache"""
        try:
            if not self.memory_cache:
                return

            # Find oldest item by creation time
            oldest_key = min(
                self.memory_cache.keys(),
                key=lambda k: self.memory_cache[k]["created_at"],
            )

            # Remove oldest item
            del self.memory_cache[oldest_key]
            if oldest_key in self.memory_cache_ttl:
                del self.memory_cache_ttl[oldest_key]

            await self.cache_analytics.record_eviction(
                CacheLevel.L3_MEMORY, oldest_key, "lru"
            )

        except Exception as e:
            logger.error(f"Memory cache LRU eviction failed: {e}")

    async def _get_from_redis_cache(
        self, key: str, database_type: DatabaseType
    ) -> Optional[Any]:
        """Get value from Redis cache"""
        try:
            return await self.redis_manager.get(database_type, key)
        except Exception as e:
            await self.cache_analytics.record_error(CacheLevel.L1_REDIS, key, str(e))
            return None

    async def _set_redis_cache(
        self, key: str, value: Any, ttl: int, database_type: DatabaseType
    ):
        """Set value in Redis cache"""
        try:
            await self.redis_manager.set_with_ttl(database_type, key, value, ttl)
        except Exception as e:
            await self.cache_analytics.record_error(CacheLevel.L1_REDIS, key, str(e))

    async def _get_from_database_cache(self, key: str) -> Optional[Any]:
        """Get value from database materialized view cache"""
        if not self.db_session_factory:
            return None

        try:
            async with self.db_session_factory() as _:
                # This would query materialized views or cached tables
                # For now, return None to indicate miss
                return None

        except Exception as e:
            await self.cache_analytics.record_error(CacheLevel.L2_DATABASE, key, str(e))
            return None

    async def _delete_from_database_cache(self, key: str) -> bool:
        """Delete from database cache"""
        if not self.db_session_factory:
            return True

        try:
            # Implementation would depend on database cache structure
            return True
        except Exception as e:
            logger.error(f"Database cache delete failed for {key}: {e}")
            return False

    async def _store_in_all_levels(
        self,
        key: str,
        value: Any,
        ttl: int,
        cache_levels: List[CacheLevel],
        database_type: DatabaseType,
    ) -> bool:
        """Store value in all requested cache levels"""
        success = True

        try:
            # Store in memory cache
            if CacheLevel.L3_MEMORY in cache_levels:
                await self._set_memory_cache(key, value, ttl)

            # Store in Redis cache
            if CacheLevel.L1_REDIS in cache_levels:
                redis_success = await self.redis_manager.set_with_ttl(
                    database_type, key, value, ttl
                )
                success = success and redis_success

            # Store in database cache (if applicable)
            if CacheLevel.L2_DATABASE in cache_levels and self.db_session_factory:
                # Database cache storage would be implemented here
                pass

            return success

        except Exception as e:
            logger.error(f"Failed to store in all cache levels for key {key}: {e}")
            return False

    async def _check_warming_triggers(self, key: str, response_time: float):
        """Check if cache warming should be triggered"""
        try:
            # Trigger warming for slow queries
            if response_time > self.slow_query_threshold:
                self.cache_analytics._get_pattern_key(key)

                # Schedule warming for similar keys
                await self.cache_warming.warm_cache(
                    key,
                    lambda: None,
                    ttl=3600,
                    priority=1,  # Would be actual fallback
                )

        except Exception as e:
            logger.error(f"Cache warming trigger check failed: {e}")

    async def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        try:
            performance_metrics = self.cache_analytics.get_performance_metrics()
            usage_patterns = self.cache_analytics.get_usage_patterns()

            # Memory cache statistics
            memory_stats = {
                "total_items": len(self.memory_cache),
                "max_capacity": self.max_memory_cache_size,
                "utilization": len(self.memory_cache) / self.max_memory_cache_size,
                "expired_items": sum(
                    1
                    for key in self.memory_cache_ttl
                    if datetime.utcnow() > self.memory_cache_ttl[key]
                ),
            }

            return {
                "performance_metrics": performance_metrics,
                "memory_cache": memory_stats,
                "usage_patterns_count": len(usage_patterns),
                "warming_tasks_active": len(self.cache_warming.warming_tasks),
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get cache statistics: {e}")
            return {}

    async def optimize_cache_configuration(self) -> Dict[str, Any]:
        """Automatically optimize cache configuration based on usage patterns"""
        try:
            stats = await self.get_cache_statistics()
            performance_metrics = stats.get("performance_metrics", {})

            recommendations = {
                "ttl_adjustments": {},
                "cache_level_changes": {},
                "warming_recommendations": [],
                "eviction_policy_changes": {},
            }

            # Analyze hit ratios and suggest optimizations
            for level, metrics in performance_metrics.items():
                hit_ratio = metrics.get("hit_count", 0) / max(
                    metrics.get("total_requests", 1), 1
                )

                if hit_ratio < 0.5:  # Poor hit ratio
                    recommendations["warming_recommendations"].append(
                        {
                            "cache_level": level,
                            "current_hit_ratio": hit_ratio,
                            "recommended_action": "increase_warming_frequency",
                        }
                    )

                if metrics.get("average_response_time", 0) > 0.1:  # Slow responses
                    recommendations["cache_level_changes"][level] = {
                        "current_response_time": metrics["average_response_time"],
                        "recommendation": "consider_promoting_to_faster_level",
                    }

            return recommendations

        except Exception as e:
            logger.error(f"Cache optimization failed: {e}")
            return {}

    async def cleanup_expired_cache(self):
        """Clean up expired cache entries"""
        try:
            # Clean memory cache
            expired_keys = [
                key
                for key, ttl in self.memory_cache_ttl.items()
                if datetime.utcnow() > ttl
            ]

            for key in expired_keys:
                if key in self.memory_cache:
                    del self.memory_cache[key]
                del self.memory_cache_ttl[key]
                await self.cache_analytics.record_eviction(
                    CacheLevel.L3_MEMORY, key, "ttl"
                )

            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")


# Global intelligent cache manager instance
intelligent_cache_manager: Optional[IntelligentCacheManager] = None


def get_intelligent_cache_manager() -> IntelligentCacheManager:
    """Get global intelligent cache manager instance"""
    if (
        "intelligent_cache_manager" not in globals()
        or intelligent_cache_manager is None
    ):
        raise Exception(
            "Intelligent cache manager not initialized. Call init_intelligent_cache_manager first."
        )
    return intelligent_cache_manager


async def init_intelligent_cache_manager(
    redis_manager: RedisClusterManager,
    db_session_factory: Optional[Callable] = None,
    event_publisher: Optional[EventPublisher] = None,
) -> IntelligentCacheManager:
    """Initialize global intelligent cache manager"""
    global intelligent_cache_manager
    intelligent_cache_manager = IntelligentCacheManager(
        redis_manager, db_session_factory, event_publisher
    )

    # Start background tasks
    asyncio.create_task(periodic_cache_cleanup())
    asyncio.create_task(periodic_predictive_warming())

    logger.info("Intelligent cache manager initialized globally")
    return intelligent_cache_manager


async def periodic_cache_cleanup():
    """Periodic cache cleanup task"""
    while True:
        try:
            if intelligent_cache_manager:
                await intelligent_cache_manager.cleanup_expired_cache()
            await asyncio.sleep(300)  # Run every 5 minutes
        except Exception as e:
            logger.error(f"Periodic cache cleanup error: {e}")
            await asyncio.sleep(60)  # Retry after 1 minute on error


async def periodic_predictive_warming():
    """Periodic predictive cache warming task"""
    while True:
        try:
            if intelligent_cache_manager:
                await intelligent_cache_manager.cache_warming.predictive_warming()
            await asyncio.sleep(1800)  # Run every 30 minutes
        except Exception as e:
            logger.error(f"Periodic predictive warming error: {e}")
            await asyncio.sleep(300)  # Retry after 5 minutes on error
