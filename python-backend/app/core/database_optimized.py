# Optimized Database Configuration for Dinner1
# High-performance database setup with connection pooling, query optimization, and monitoring

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, StaticPool
from typing import Dict, List, Optional, Any, Generator
import logging
import time
import asyncio
from contextlib import contextmanager
import redis
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import hashlib
from functools import wraps

logger = logging.getLogger(__name__)

@dataclass
class DatabaseMetrics:
    total_queries: int = 0
    slow_queries: int = 0
    failed_queries: int = 0
    avg_query_time: float = 0.0
    connection_pool_size: int = 0
    active_connections: int = 0
    cache_hits: int = 0
    cache_misses: int = 0

class DatabaseOptimizer:
    """
    High-performance database optimization for dating platform
    """
    
    def __init__(self, database_url: str, redis_client: redis.Redis):
        self.database_url = database_url
        self.redis_client = redis_client
        self.metrics = DatabaseMetrics()
        
        # Performance configuration
        self.config = {
            'pool_size': 20,
            'max_overflow': 30,
            'pool_timeout': 30,
            'pool_recycle': 3600,
            'pool_pre_ping': True,
            'echo_slow_queries': True,
            'slow_query_threshold': 1.0,  # seconds
            'query_cache_ttl': 300,  # 5 minutes
            'connection_cache_ttl': 3600,  # 1 hour
        }
        
        # Initialize optimized engine
        self.engine = self._create_optimized_engine()
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Query cache for frequently accessed data
        self.query_cache = {}
        
        # Setup monitoring
        self._setup_query_monitoring()
    
    def _create_optimized_engine(self) -> Engine:
        """Create optimized SQLAlchemy engine with connection pooling"""
        
        # Connection pool configuration
        engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=self.config['pool_size'],
            max_overflow=self.config['max_overflow'],
            pool_timeout=self.config['pool_timeout'],
            pool_recycle=self.config['pool_recycle'],
            pool_pre_ping=self.config['pool_pre_ping'],
            echo=False,  # Disable SQL echo for performance
            
            # Connection arguments for PostgreSQL optimization
            connect_args={
                "options": "-c timezone=utc",
                "application_name": "dinner1_backend",
                "connect_timeout": 10,
                "command_timeout": 30,
            }
        )
        
        # Register event listeners for monitoring
        self._register_engine_events(engine)
        
        return engine
    
    def _register_engine_events(self, engine: Engine):
        """Register SQLAlchemy event listeners for performance monitoring"""
        
        @event.listens_for(engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
        
        @event.listens_for(engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total_time = time.time() - context._query_start_time
            
            # Update metrics
            self.metrics.total_queries += 1
            self.metrics.avg_query_time = (
                (self.metrics.avg_query_time * (self.metrics.total_queries - 1) + total_time) /
                self.metrics.total_queries
            )
            
            # Log slow queries
            if total_time > self.config['slow_query_threshold']:
                self.metrics.slow_queries += 1
                logger.warning(
                    f"Slow query detected: {total_time:.3f}s - {statement[:200]}..."
                )
                
                # Store slow query for analysis
                self._record_slow_query(statement, parameters, total_time)
        
        @event.listens_for(engine, "handle_error")
        def handle_error(exception_context):
            self.metrics.failed_queries += 1
            logger.error(f"Database error: {exception_context.original_exception}")
    
    def _setup_query_monitoring(self):
        """Setup query performance monitoring"""
        
        # Monitor connection pool status
        def update_pool_metrics():
            pool = self.engine.pool
            self.metrics.connection_pool_size = pool.size()
            self.metrics.active_connections = pool.checkedin() + pool.checkedout()
        
        # Update metrics every 30 seconds
        import threading
        def metrics_updater():
            while True:
                try:
                    update_pool_metrics()
                    self._store_metrics()
                    time.sleep(30)
                except Exception as e:
                    logger.error(f"Error updating database metrics: {e}")
                    time.sleep(30)
        
        thread = threading.Thread(target=metrics_updater, daemon=True)
        thread.start()
    
    def _record_slow_query(self, statement: str, parameters: Any, execution_time: float):
        """Record slow query for analysis"""
        try:
            slow_query = {
                'statement': statement[:1000],  # Truncate long queries
                'execution_time': execution_time,
                'timestamp': datetime.utcnow().isoformat(),
                'parameters_hash': hashlib.md5(str(parameters).encode()).hexdigest()[:10]
            }
            
            # Store in Redis for analysis
            self.redis_client.lpush('slow_queries', json.dumps(slow_query))
            self.redis_client.ltrim('slow_queries', 0, 999)  # Keep last 1000
            
        except Exception as e:
            logger.error(f"Failed to record slow query: {e}")
    
    def _store_metrics(self):
        """Store database metrics in Redis"""
        try:
            metrics_data = {
                'total_queries': self.metrics.total_queries,
                'slow_queries': self.metrics.slow_queries,
                'failed_queries': self.metrics.failed_queries,
                'avg_query_time': round(self.metrics.avg_query_time, 4),
                'connection_pool_size': self.metrics.connection_pool_size,
                'active_connections': self.metrics.active_connections,
                'cache_hits': self.metrics.cache_hits,
                'cache_misses': self.metrics.cache_misses,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.redis_client.set('db_metrics', json.dumps(metrics_data), ex=3600)
            
        except Exception as e:
            logger.error(f"Failed to store database metrics: {e}")
    
    @contextmanager
    def get_db_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def query_with_cache(self, cache_key: str, query_func, ttl: int = None) -> Any:
        """Execute query with Redis caching"""
        ttl = ttl or self.config['query_cache_ttl']
        
        try:
            # Try to get from cache first
            cached_result = self.redis_client.get(cache_key)
            if cached_result:
                self.metrics.cache_hits += 1
                return json.loads(cached_result)
            
            # Cache miss - execute query
            self.metrics.cache_misses += 1
            
            with self.get_db_session() as session:
                result = query_func(session)
                
                # Cache the result
                if result is not None:
                    self.redis_client.set(
                        cache_key, 
                        json.dumps(result, default=str), 
                        ex=ttl
                    )
                
                return result
                
        except Exception as e:
            logger.error(f"Error in cached query {cache_key}: {e}")
            raise
    
    def invalidate_cache_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache entries matching {pattern}")
        except Exception as e:
            logger.error(f"Failed to invalidate cache pattern {pattern}: {e}")
    
    def get_database_metrics(self) -> Dict[str, Any]:
        """Get current database performance metrics"""
        try:
            metrics_json = self.redis_client.get('db_metrics')
            if metrics_json:
                return json.loads(metrics_json)
            
            # Return current metrics if Redis data not available
            return {
                'total_queries': self.metrics.total_queries,
                'slow_queries': self.metrics.slow_queries,
                'failed_queries': self.metrics.failed_queries,
                'avg_query_time': round(self.metrics.avg_query_time, 4),
                'connection_pool_size': self.metrics.connection_pool_size,
                'active_connections': self.metrics.active_connections,
                'cache_hits': self.metrics.cache_hits,
                'cache_misses': self.metrics.cache_misses,
                'cache_hit_ratio': (
                    self.metrics.cache_hits / 
                    (self.metrics.cache_hits + self.metrics.cache_misses)
                    if (self.metrics.cache_hits + self.metrics.cache_misses) > 0 else 0
                ),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get database metrics: {e}")
            return {}
    
    def optimize_query_plan(self, query: str) -> Dict[str, Any]:
        """Analyze and optimize query execution plan"""
        try:
            with self.get_db_session() as session:
                # Get query execution plan
                explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
                result = session.execute(text(explain_query))
                plan = result.fetchone()[0]
                
                # Analyze plan for optimization opportunities
                analysis = self._analyze_query_plan(plan)
                
                return {
                    'original_query': query,
                    'execution_plan': plan,
                    'analysis': analysis,
                    'optimization_suggestions': self._generate_optimization_suggestions(analysis)
                }
                
        except Exception as e:
            logger.error(f"Failed to optimize query plan: {e}")
            return {}
    
    def _analyze_query_plan(self, plan: List[Dict]) -> Dict[str, Any]:
        """Analyze query execution plan for performance issues"""
        analysis = {
            'total_cost': 0,
            'execution_time': 0,
            'seq_scans': 0,
            'index_scans': 0,
            'sorts': 0,
            'hash_joins': 0,
            'nested_loops': 0,
            'issues': []
        }
        
        def analyze_node(node):
            node_type = node.get('Node Type', '')
            
            # Update statistics
            analysis['total_cost'] += node.get('Total Cost', 0)
            analysis['execution_time'] += node.get('Actual Total Time', 0)
            
            # Identify performance issues
            if node_type == 'Seq Scan':
                analysis['seq_scans'] += 1
                if node.get('Total Cost', 0) > 1000:
                    analysis['issues'].append(f"High-cost sequential scan on {node.get('Relation Name', 'unknown')}")
            
            elif node_type == 'Index Scan':
                analysis['index_scans'] += 1
            
            elif node_type == 'Sort':
                analysis['sorts'] += 1
                if node.get('Sort Method') == 'external sort':
                    analysis['issues'].append("External sort detected - consider increasing work_mem")
            
            elif node_type == 'Hash Join':
                analysis['hash_joins'] += 1
            
            elif node_type == 'Nested Loop':
                analysis['nested_loops'] += 1
                if node.get('Actual Loops', 1) > 1000:
                    analysis['issues'].append("High-cardinality nested loop - consider hash join")
            
            # Recursively analyze child nodes
            for child in node.get('Plans', []):
                analyze_node(child)
        
        # Start analysis from root node
        if plan and len(plan) > 0:
            analyze_node(plan[0]['Plan'])
        
        return analysis
    
    def _generate_optimization_suggestions(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate optimization suggestions based on query analysis"""
        suggestions = []
        
        if analysis['seq_scans'] > analysis['index_scans']:
            suggestions.append("Consider adding indexes to reduce sequential scans")
        
        if analysis['sorts'] > 2:
            suggestions.append("Multiple sorts detected - consider optimizing ORDER BY clauses")
        
        if analysis['nested_loops'] > 3:
            suggestions.append("Many nested loops - review JOIN conditions and consider hash joins")
        
        if analysis['total_cost'] > 10000:
            suggestions.append("High query cost - consider query rewriting or partitioning")
        
        if analysis['execution_time'] > 1000:  # > 1 second
            suggestions.append("Long execution time - review query complexity and data volume")
        
        return suggestions
    
    def create_optimized_indexes(self):
        """Create optimized indexes for dating platform queries"""
        
        indexes = [
            # User profile optimization
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_active_location ON users (last_activity, location) WHERE is_active = true",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_age_gender ON users (age, gender) WHERE is_active = true",
            
            # Emotional profiles optimization
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_emotional_profiles_interests ON emotional_profiles USING gin(interests)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_emotional_profiles_values ON emotional_profiles USING gin(core_values)",
            
            # Matching optimization
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_soul_connections_stage_created ON soul_connections (connection_stage, created_at)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_soul_connections_users ON soul_connections (user1_id, user2_id)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_soul_connections_compatibility ON soul_connections (compatibility_score DESC) WHERE connection_stage = 'active'",
            
            # Messages optimization
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_connection_time ON messages (connection_id, created_at DESC)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_messages_sender_time ON messages (sender_id, created_at DESC)",
            
            # Revelations optimization
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_daily_revelations_connection_day ON daily_revelations (connection_id, day_number)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_daily_revelations_sender_time ON daily_revelations (sender_id, created_at DESC)",
            
            # Performance monitoring indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_last_activity ON users (last_activity DESC) WHERE is_active = true",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_soul_connections_mutual_consent ON soul_connections (mutual_reveal_consent, reveal_day) WHERE connection_stage = 'soul_discovery'",
        ]
        
        try:
            with self.get_db_session() as session:
                for index_sql in indexes:
                    try:
                        session.execute(text(index_sql))
                        logger.info(f"Created index: {index_sql.split('idx_')[1].split(' ')[0]}")
                    except Exception as e:
                        logger.warning(f"Index creation skipped (may already exist): {e}")
                
                session.commit()
                logger.info("Database index optimization completed")
                
        except Exception as e:
            logger.error(f"Failed to create optimized indexes: {e}")
            raise
    
    def vacuum_analyze_tables(self):
        """Run VACUUM ANALYZE on key tables for performance"""
        
        tables = [
            'users', 'emotional_profiles', 'soul_connections', 
            'messages', 'daily_revelations'
        ]
        
        try:
            # VACUUM ANALYZE requires autocommit
            with self.engine.connect() as connection:
                connection.execute(text("COMMIT"))  # End any existing transaction
                
                for table in tables:
                    connection.execute(text(f"VACUUM ANALYZE {table}"))
                    logger.info(f"VACUUM ANALYZE completed for {table}")
                
                logger.info("Database maintenance completed")
                
        except Exception as e:
            logger.error(f"Failed to run VACUUM ANALYZE: {e}")
    
    def get_table_statistics(self) -> Dict[str, Any]:
        """Get table statistics for monitoring"""
        
        stats_query = """
        SELECT 
            schemaname,
            tablename,
            n_tup_ins as inserts,
            n_tup_upd as updates,
            n_tup_del as deletes,
            n_live_tup as live_tuples,
            n_dead_tup as dead_tuples,
            last_vacuum,
            last_autovacuum,
            last_analyze,
            last_autoanalyze
        FROM pg_stat_user_tables 
        WHERE schemaname = 'public'
        ORDER BY n_live_tup DESC
        """
        
        try:
            with self.get_db_session() as session:
                result = session.execute(text(stats_query))
                
                tables_stats = []
                for row in result:
                    tables_stats.append({
                        'schema': row.schemaname,
                        'table': row.tablename,
                        'inserts': row.inserts,
                        'updates': row.updates,
                        'deletes': row.deletes,
                        'live_tuples': row.live_tuples,
                        'dead_tuples': row.dead_tuples,
                        'last_vacuum': row.last_vacuum,
                        'last_autovacuum': row.last_autovacuum,
                        'last_analyze': row.last_analyze,
                        'last_autoanalyze': row.last_autoanalyze,
                        'dead_tuple_ratio': (
                            row.dead_tuples / row.live_tuples 
                            if row.live_tuples > 0 else 0
                        )
                    })
                
                return {
                    'timestamp': datetime.utcnow().isoformat(),
                    'tables': tables_stats
                }
                
        except Exception as e:
            logger.error(f"Failed to get table statistics: {e}")
            return {}

# Global database optimizer instance
db_optimizer: Optional[DatabaseOptimizer] = None

def get_database_optimizer() -> DatabaseOptimizer:
    """Get global database optimizer instance"""
    global db_optimizer
    if db_optimizer is None:
        raise RuntimeError("Database optimizer not initialized")
    return db_optimizer

def init_database_optimizer(database_url: str, redis_client: redis.Redis) -> DatabaseOptimizer:
    """Initialize global database optimizer"""
    global db_optimizer
    db_optimizer = DatabaseOptimizer(database_url, redis_client)
    return db_optimizer

# Decorator for cached database queries
def cached_query(cache_key_prefix: str, ttl: int = 300):
    """Decorator for caching database query results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{cache_key_prefix}:{hashlib.md5(str(args + tuple(kwargs.items())).encode()).hexdigest()[:16]}"
            
            optimizer = get_database_optimizer()
            return optimizer.query_with_cache(cache_key, lambda session: func(session, *args[1:], **kwargs), ttl)
        
        return wrapper
    return decorator

# Context manager for database transactions
@contextmanager
def database_transaction():
    """Context manager for database transactions with automatic rollback"""
    optimizer = get_database_optimizer()
    with optimizer.get_db_session() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise