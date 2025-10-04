"""
Redis Cluster Manager for Sprint 8 - Advanced Microservices Architecture
High-performance, multi-database Redis cluster management with connection pooling and failover
"""

import json
import logging
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

try:
    import aioredis
    from aioredis.exceptions import RedisError
except ImportError:
    aioredis = None
    RedisError = Exception

try:
    from rediscluster import RedisCluster
except ImportError:
    RedisCluster = None

logger = logging.getLogger(__name__)


class DatabaseType(Enum):
    """Redis database types for different data categories"""

    USER_SESSIONS = 0  # User Sessions & Auth (512MB, LRU, 15min TTL)
    USER_PROFILES = 1  # User Profile Cache (1GB, LFU, 1hr TTL)
    MATCHING_RESULTS = 2  # Matching Results Cache (1.5GB, Volatile TTL, 30min TTL)
    ANALYTICS_STREAM = 3  # Real-time Analytics Stream (512MB, Volatile LRU, 5min TTL)
    SENTIMENT_CACHE = 4  # Sentiment Analysis Cache (1GB, LRU, 2hr TTL)


class RedisClusterManager:
    """
    Advanced Redis Cluster Manager with intelligent connection pooling,
    database separation, and automatic failover capabilities
    """

    def __init__(self, cluster_nodes: List[Dict[str, Union[str, int]]] = None):
        """
        Initialize Redis Cluster Manager

        Args:
            cluster_nodes: List of cluster node configurations
        """
        self.cluster_nodes = cluster_nodes or [
            {"host": "172.20.0.10", "port": 6379},
            {"host": "172.20.0.11", "port": 6380},
            {"host": "172.20.0.12", "port": 6381},
        ]

        # Connection pools for different databases
        self._connection_pools: Dict[DatabaseType, aioredis.ConnectionPool] = {}
        self._cluster_clients: Dict[DatabaseType, RedisCluster] = {}

        # Performance monitoring
        self._performance_stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "average_response_time": 0.0,
            "error_count": 0,
        }

        # Database-specific configurations
        self._db_configs = {
            DatabaseType.USER_SESSIONS: {
                "max_memory": "512mb",
                "eviction_policy": "allkeys-lru",
                "default_ttl": 900,  # 15 minutes
                "max_connections": 50,
            },
            DatabaseType.USER_PROFILES: {
                "max_memory": "1gb",
                "eviction_policy": "allkeys-lfu",
                "default_ttl": 3600,  # 1 hour
                "max_connections": 100,
            },
            DatabaseType.MATCHING_RESULTS: {
                "max_memory": "1.5gb",
                "eviction_policy": "volatile-ttl",
                "default_ttl": 1800,  # 30 minutes
                "max_connections": 75,
            },
            DatabaseType.ANALYTICS_STREAM: {
                "max_memory": "512mb",
                "eviction_policy": "volatile-lru",
                "default_ttl": 300,  # 5 minutes
                "max_connections": 30,
            },
            DatabaseType.SENTIMENT_CACHE: {
                "max_memory": "1gb",
                "eviction_policy": "allkeys-lru",
                "default_ttl": 7200,  # 2 hours
                "max_connections": 60,
            },
        }

        # Initialize connection pools
        self._initialize_connection_pools()

    def _initialize_connection_pools(self):
        """Initialize connection pools for each database type"""
        for db_type in DatabaseType:
            config = self._db_configs[db_type]

            # Create async connection pool
            pool = aioredis.ConnectionPool.from_url(
                f"redis://:{self._get_redis_password()}@{self.cluster_nodes[0]['host']}:"
                f"{self.cluster_nodes[0]['port']}/{db_type.value}",
                max_connections=config["max_connections"],
                retry_on_timeout=True,
                socket_keepalive=True,
                socket_keepalive_options={
                    1: 1,  # TCP_KEEPIDLE
                    2: 3,  # TCP_KEEPINTVL
                    3: 5,  # TCP_KEEPCNT
                },
                health_check_interval=30,
            )
            self._connection_pools[db_type] = pool

            # Create cluster client for synchronous operations
            cluster_client = RedisCluster(
                startup_nodes=self.cluster_nodes,
                decode_responses=True,
                skip_full_coverage_check=True,
                health_check_interval=30,
                password=self._get_redis_password(),
            )
            self._cluster_clients[db_type] = cluster_client

    def _get_redis_password(self) -> str:
        """Get Redis password from environment"""
        import os

        return os.getenv("REDIS_PASSWORD", "dinner_first_redis_2025")

    async def get_client(self, db_type: DatabaseType) -> aioredis.Redis:
        """Get async Redis client for specific database type"""
        if db_type not in self._connection_pools:
            raise ValueError(f"Unknown database type: {db_type}")

        return aioredis.Redis(connection_pool=self._connection_pools[db_type])

    def get_cluster_client(self, db_type: DatabaseType) -> RedisCluster:
        """Get synchronous Redis cluster client for specific database type"""
        if db_type not in self._cluster_clients:
            raise ValueError(f"Unknown database type: {db_type}")

        return self._cluster_clients[db_type]

    async def set_with_ttl(
        self,
        db_type: DatabaseType,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Set key-value pair with TTL based on database type

        Args:
            db_type: Database type to use
            key: Redis key
            value: Value to store (will be JSON encoded if not string)
            ttl: Time to live in seconds (uses default if None)

        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        try:
            client = await self.get_client(db_type)

            # Convert value to JSON if needed
            if not isinstance(value, (str, bytes)):
                value = json.dumps(value)

            # Use default TTL if not specified
            if ttl is None:
                ttl = self._db_configs[db_type]["default_ttl"]

            result = await client.setex(key, ttl, value)

            # Update performance stats
            self._update_performance_stats(start_time, success=True)

            logger.debug(f"Set key '{key}' in {db_type.name} with TTL {ttl}s")
            return bool(result)

        except RedisError as e:
            self._update_performance_stats(start_time, success=False)
            logger.error(f"Failed to set key '{key}' in {db_type.name}: {e}")
            return False

    async def get(
        self, db_type: DatabaseType, key: str, decode_json: bool = True
    ) -> Optional[Any]:
        """
        Get value by key from specific database

        Args:
            db_type: Database type to query
            key: Redis key
            decode_json: Whether to decode JSON values

        Returns:
            Value if found, None otherwise
        """
        start_time = time.time()
        try:
            client = await self.get_client(db_type)
            value = await client.get(key)

            if value is None:
                self._performance_stats["cache_misses"] += 1
                self._update_performance_stats(start_time, success=True)
                return None

            # Decode JSON if requested
            if decode_json and isinstance(value, (str, bytes)):
                try:
                    value = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    # Return raw value if JSON decode fails
                    pass

            self._performance_stats["cache_hits"] += 1
            self._update_performance_stats(start_time, success=True)

            logger.debug(f"Retrieved key '{key}' from {db_type.name}")
            return value

        except RedisError as e:
            self._update_performance_stats(start_time, success=False)
            logger.error(f"Failed to get key '{key}' from {db_type.name}: {e}")
            return None

    async def delete(self, db_type: DatabaseType, key: str) -> bool:
        """Delete key from specific database"""
        start_time = time.time()
        try:
            client = await self.get_client(db_type)
            result = await client.delete(key)

            self._update_performance_stats(start_time, success=True)
            logger.debug(f"Deleted key '{key}' from {db_type.name}")
            return bool(result)

        except RedisError as e:
            self._update_performance_stats(start_time, success=False)
            logger.error(f"Failed to delete key '{key}' from {db_type.name}: {e}")
            return False

    async def exists(self, db_type: DatabaseType, key: str) -> bool:
        """Check if key exists in specific database"""
        start_time = time.time()
        try:
            client = await self.get_client(db_type)
            result = await client.exists(key)

            self._update_performance_stats(start_time, success=True)
            return bool(result)

        except RedisError as e:
            self._update_performance_stats(start_time, success=False)
            logger.error(f"Failed to check key '{key}' in {db_type.name}: {e}")
            return False

    async def batch_operations(
        self, db_type: DatabaseType, operations: List[Dict[str, Any]]
    ) -> List[Any]:
        """
        Execute batch operations for better performance

        Args:
            db_type: Database type to use
            operations: List of operations with format:
                       [{"command": "set", "key": "key1", "value": "val1", "ttl": 300}, ...]

        Returns:
            List of operation results
        """
        start_time = time.time()
        try:
            client = await self.get_client(db_type)
            pipeline = client.pipeline()

            for operation in operations:
                command = operation.get("command")
                key = operation.get("key")

                if command == "set":
                    value = operation.get("value")
                    ttl = operation.get("ttl", self._db_configs[db_type]["default_ttl"])

                    if not isinstance(value, (str, bytes)):
                        value = json.dumps(value)

                    pipeline.setex(key, ttl, value)

                elif command == "get":
                    pipeline.get(key)

                elif command == "delete":
                    pipeline.delete(key)

                elif command == "exists":
                    pipeline.exists(key)

                else:
                    logger.warning(f"Unknown batch operation: {command}")

            results = await pipeline.execute()

            self._update_performance_stats(start_time, success=True)
            logger.debug(
                f"Executed {len(operations)} batch operations in {db_type.name}"
            )

            return results

        except RedisError as e:
            self._update_performance_stats(start_time, success=False)
            logger.error(f"Failed to execute batch operations in {db_type.name}: {e}")
            return []

    async def cache_user_session(
        self, user_id: int, session_data: Dict[str, Any]
    ) -> bool:
        """Cache user session data with optimized TTL"""
        key = f"session:{user_id}"
        return await self.set_with_ttl(
            DatabaseType.USER_SESSIONS, key, session_data, ttl=900
        )

    async def get_user_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get cached user session data"""
        key = f"session:{user_id}"
        return await self.get(DatabaseType.USER_SESSIONS, key)

    async def cache_user_profile(
        self, user_id: int, profile_data: Dict[str, Any]
    ) -> bool:
        """Cache user profile data with optimized TTL"""
        key = f"profile:{user_id}"
        return await self.set_with_ttl(
            DatabaseType.USER_PROFILES, key, profile_data, ttl=3600
        )

    async def get_cached_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get cached user profile data"""
        key = f"profile:{user_id}"
        return await self.get(DatabaseType.USER_PROFILES, key)

    async def cache_match_results(
        self, user_id: int, matches: List[Dict[str, Any]]
    ) -> bool:
        """Cache matching results with optimized TTL"""
        key = f"matches:{user_id}"
        return await self.set_with_ttl(
            DatabaseType.MATCHING_RESULTS, key, matches, ttl=1800
        )

    async def get_cached_matches(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """Get cached matching results"""
        key = f"matches:{user_id}"
        return await self.get(DatabaseType.MATCHING_RESULTS, key)

    async def cache_sentiment_analysis(
        self, user_id: int, message_id: int, sentiment_data: Dict[str, Any]
    ) -> bool:
        """Cache sentiment analysis results"""
        key = f"sentiment:{user_id}:{message_id}"
        return await self.set_with_ttl(
            DatabaseType.SENTIMENT_CACHE, key, sentiment_data, ttl=7200
        )

    async def get_cached_sentiment(
        self, user_id: int, message_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get cached sentiment analysis"""
        key = f"sentiment:{user_id}:{message_id}"
        return await self.get(DatabaseType.SENTIMENT_CACHE, key)

    async def stream_analytics_event(
        self, event_type: str, event_data: Dict[str, Any]
    ) -> bool:
        """Stream analytics events with short TTL"""
        timestamp = int(time.time() * 1000)
        key = f"analytics:{event_type}:{timestamp}"
        return await self.set_with_ttl(
            DatabaseType.ANALYTICS_STREAM, key, event_data, ttl=300
        )

    def _update_performance_stats(self, start_time: float, success: bool):
        """Update internal performance statistics"""
        response_time = time.time() - start_time

        self._performance_stats["total_requests"] += 1
        if not success:
            self._performance_stats["error_count"] += 1

        # Update rolling average response time
        current_avg = self._performance_stats["average_response_time"]
        total_requests = self._performance_stats["total_requests"]

        self._performance_stats["average_response_time"] = (
            current_avg * (total_requests - 1) + response_time
        ) / total_requests

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        stats = self._performance_stats.copy()

        # Calculate cache hit ratio
        total_cache_ops = stats["cache_hits"] + stats["cache_misses"]
        if total_cache_ops > 0:
            stats["cache_hit_ratio"] = stats["cache_hits"] / total_cache_ops
        else:
            stats["cache_hit_ratio"] = 0.0

        # Calculate error rate
        if stats["total_requests"] > 0:
            stats["error_rate"] = stats["error_count"] / stats["total_requests"]
        else:
            stats["error_rate"] = 0.0

        return stats

    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check of Redis cluster"""
        health_status = {
            "overall_status": "healthy",
            "database_status": {},
            "performance_stats": self.get_performance_stats(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        for db_type in DatabaseType:
            try:
                client = await self.get_client(db_type)

                # Test basic operations
                test_key = f"health_check:{int(time.time())}"
                test_value = "health_check_value"

                # Test set
                await client.setex(test_key, 60, test_value)

                # Test get
                retrieved_value = await client.get(test_key)

                # Test delete
                await client.delete(test_key)

                # Verify operation success
                if retrieved_value == test_value:
                    health_status["database_status"][db_type.name] = {
                        "status": "healthy",
                        "response_time_ms": round(
                            self._performance_stats["average_response_time"] * 1000,
                            2,
                        ),
                    }
                else:
                    health_status["database_status"][db_type.name] = {
                        "status": "unhealthy",
                        "error": "Data integrity check failed",
                    }
                    health_status["overall_status"] = "degraded"

            except Exception as e:
                health_status["database_status"][db_type.name] = {
                    "status": "unhealthy",
                    "error": str(e),
                }
                health_status["overall_status"] = "degraded"

        return health_status

    async def close_connections(self):
        """Close all Redis connections"""
        for pool in self._connection_pools.values():
            await pool.disconnect()

        for client in self._cluster_clients.values():
            client.connection_pool.disconnect()

        logger.info("All Redis connections closed")


# Global Redis cluster manager instance
redis_cluster_manager = None


def get_redis_cluster_manager() -> RedisClusterManager:
    """Get global Redis cluster manager instance"""
    global redis_cluster_manager
    if redis_cluster_manager is None:
        redis_cluster_manager = RedisClusterManager()
    return redis_cluster_manager


async def init_redis_cluster():
    """Initialize Redis cluster manager"""
    global redis_cluster_manager
    redis_cluster_manager = RedisClusterManager()

    # Perform health check
    health_status = await redis_cluster_manager.health_check()
    logger.info(f"Redis cluster initialized: {health_status['overall_status']}")

    return redis_cluster_manager


async def close_redis_cluster():
    """Close Redis cluster connections"""
    global redis_cluster_manager
    if redis_cluster_manager:
        await redis_cluster_manager.close_connections()
        redis_cluster_manager = None
