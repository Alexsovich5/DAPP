"""
Database Health Monitoring API
Provides endpoints for monitoring database performance and connection pool status
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from app.core.database import (
    get_db, get_connection_pool_status, check_database_health, 
    optimize_query_performance, engine
)
from app.api.v1.deps import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(tags=["database-health"])


@router.get("/health")
def get_database_health():
    """
    Get comprehensive database health status.
    Public endpoint for basic health monitoring.
    """
    try:
        health_status = check_database_health()
        return {
            "status": "healthy" if health_status["database_accessible"] else "unhealthy",
            "health_score": health_status["health_score"],
            "database_accessible": health_status["database_accessible"],
            "timestamp": health_status.get("timestamp", "unknown"),
            "pool_healthy": health_status.get("pool_status", {}).get("is_healthy", False)
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Database health check failed")


@router.get("/pool-status")
def get_pool_status(current_user: User = Depends(get_current_user)):
    """
    Get detailed connection pool status.
    Requires authentication for security.
    """
    try:
        pool_status = get_connection_pool_status()
        return {
            "pool_metrics": pool_status,
            "recommendations": _generate_pool_recommendations(pool_status),
            "status": "healthy" if pool_status["is_healthy"] else "warning"
        }
    except Exception as e:
        logger.error(f"Pool status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get pool status")


@router.get("/detailed-health")
def get_detailed_health(current_user: User = Depends(get_current_user)):
    """
    Get comprehensive database health and performance metrics.
    Admin-level endpoint with full diagnostics.
    """
    try:
        health_status = check_database_health()
        pool_status = get_connection_pool_status()
        
        # Get additional database metrics
        db_metrics = _get_database_metrics()
        
        return {
            "overall_health": health_status,
            "connection_pool": pool_status,
            "database_metrics": db_metrics,
            "performance_recommendations": _generate_performance_recommendations(
                health_status, pool_status, db_metrics
            ),
            "alert_level": _calculate_alert_level(health_status, pool_status)
        }
    except Exception as e:
        logger.error(f"Detailed health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get detailed health status")


@router.post("/optimize")
def optimize_database_performance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Apply database performance optimizations.
    Requires authentication and should be used carefully.
    """
    try:
        # Check if user has admin privileges (simplified check)
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        optimization_result = optimize_query_performance()
        
        # Log the optimization attempt
        logger.info(f"Database optimization triggered by user {current_user.id}")
        
        return {
            "optimization_applied": optimization_result["optimizations_applied"],
            "message": "Database optimizations applied successfully" if optimization_result["optimizations_applied"] else "Optimization failed",
            "details": optimization_result,
            "user_id": current_user.id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database optimization failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to optimize database")


@router.get("/query-performance")
def get_query_performance_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get query performance statistics from PostgreSQL.
    """
    try:
        # Get PostgreSQL query statistics
        query_stats = _get_postgresql_stats(db)
        
        return {
            "query_statistics": query_stats,
            "slow_queries": _identify_slow_queries(query_stats),
            "recommendations": _generate_query_recommendations(query_stats)
        }
    except Exception as e:
        logger.error(f"Query performance stats failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get query performance stats")


# Helper functions

def _generate_pool_recommendations(pool_status: Dict[str, Any]) -> list:
    """Generate recommendations based on pool status"""
    recommendations = []
    
    utilization = pool_status["checked_out_connections"] / pool_status["total_connections"]
    
    if utilization > 0.8:
        recommendations.append("High pool utilization detected. Consider increasing pool_size.")
    
    if pool_status["overflow_connections"] > 0:
        recommendations.append("Overflow connections in use. Monitor for sustained high load.")
    
    if pool_status["invalid_connections"] > 0:
        recommendations.append("Invalid connections detected. Check database connectivity.")
    
    if utilization < 0.2:
        recommendations.append("Low pool utilization. Consider reducing pool_size for efficiency.")
    
    return recommendations


def _get_database_metrics() -> Dict[str, Any]:
    """Get additional database metrics"""
    try:
        from sqlalchemy import text
        db = engine.connect()
        
        # Basic database size and connection info
        result = db.execute(text("""
            SELECT 
                pg_database_size(current_database()) as db_size,
                count(*) as total_connections
            FROM pg_stat_activity 
            WHERE datname = current_database()
        """)).fetchone()
        
        db.close()
        
        return {
            "database_size_bytes": result[0] if result else 0,
            "active_connections": result[1] if result else 0,
            "engine_url": str(engine.url).replace(engine.url.password, "***") if engine.url.password else str(engine.url)
        }
    except Exception as e:
        logger.warning(f"Could not get database metrics: {str(e)}")
        return {"error": "Metrics unavailable"}


def _get_postgresql_stats(db: Session) -> Dict[str, Any]:
    """Get PostgreSQL-specific performance statistics"""
    try:
        from sqlalchemy import text
        
        # Get table statistics
        table_stats = db.execute(text("""
            SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del, n_live_tup
            FROM pg_stat_user_tables 
            WHERE schemaname = 'public'
            ORDER BY n_live_tup DESC
            LIMIT 10
        """)).fetchall()
        
        # Get index usage
        index_stats = db.execute(text("""
            SELECT schemaname, tablename, indexname, idx_tup_read, idx_tup_fetch
            FROM pg_stat_user_indexes 
            WHERE schemaname = 'public'
            ORDER BY idx_tup_read DESC
            LIMIT 10
        """)).fetchall()
        
        return {
            "table_statistics": [dict(row) for row in table_stats],
            "index_usage": [dict(row) for row in index_stats]
        }
    except Exception as e:
        logger.warning(f"Could not get PostgreSQL stats: {str(e)}")
        return {"error": "PostgreSQL stats unavailable"}


def _identify_slow_queries(query_stats: Dict[str, Any]) -> list:
    """Identify potentially slow queries"""
    # This is a simplified implementation
    # In production, you'd integrate with pg_stat_statements
    return []


def _generate_query_recommendations(query_stats: Dict[str, Any]) -> list:
    """Generate query optimization recommendations"""
    recommendations = []
    
    if "table_statistics" in query_stats:
        for table in query_stats["table_statistics"]:
            if table.get("n_live_tup", 0) > 100000:
                recommendations.append(f"Table {table['tablename']} has many rows. Consider partitioning.")
    
    return recommendations


def _generate_performance_recommendations(
    health_status: Dict, pool_status: Dict, db_metrics: Dict
) -> list:
    """Generate comprehensive performance recommendations"""
    recommendations = []
    
    # Pool recommendations
    recommendations.extend(_generate_pool_recommendations(pool_status))
    
    # Health-based recommendations
    if health_status["health_score"] < 80:
        recommendations.append("Overall health score is low. Check database and pool status.")
    
    # Database size recommendations
    if "database_size_bytes" in db_metrics:
        size_mb = db_metrics["database_size_bytes"] / (1024 * 1024)
        if size_mb > 1000:  # 1GB
            recommendations.append("Database size is large. Consider archiving old data.")
    
    return recommendations


def _calculate_alert_level(health_status: Dict, pool_status: Dict) -> str:
    """Calculate overall alert level"""
    if not health_status["database_accessible"]:
        return "critical"
    
    if health_status["health_score"] < 50:
        return "warning"
    
    if not pool_status["is_healthy"]:
        return "warning"
    
    return "normal"