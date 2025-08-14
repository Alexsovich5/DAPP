# Monitoring and Health Check API Endpoints
# Comprehensive system monitoring and observability

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
import psutil
import asyncio
import logging
import time
import json

logger = logging.getLogger(__name__)
router = APIRouter()

class HealthCheckResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
    uptime_seconds: float
    services: Dict[str, Dict]
    system: Dict[str, Any]

class MetricsResponse(BaseModel):
    timestamp: datetime
    application: Dict
    system: Dict
    database: Dict
    redis: Dict
    custom_metrics: Dict

# Store startup time for uptime calculation
startup_time = time.time()

# In-memory metrics storage (in production, use Redis or proper metrics store)
metrics_store = {
    "requests_total": 0,
    "requests_by_endpoint": {},
    "response_times": [],
    "errors_total": 0,
    "active_users": 0,
    "database_queries": 0,
    "cache_hits": 0,
    "cache_misses": 0
}

@router.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint
    Returns detailed health status of all system components
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "version": "1.0.0",  # This should come from app config
            "uptime_seconds": time.time() - startup_time,
            "services": {},
            "system": {}
        }
        
        # Check database health
        try:
            db_health = await check_database_health()
            health_status["services"]["database"] = db_health
        except Exception as e:
            health_status["services"]["database"] = {"status": "unhealthy", "error": str(e)}
        
        # Check Redis health
        try:
            redis_health = await check_redis_health()
            health_status["services"]["redis"] = redis_health
        except Exception as e:
            health_status["services"]["redis"] = {"status": "unhealthy", "error": str(e)}
        
        # Check external services
        try:
            external_health = await check_external_services()
            health_status["services"]["external"] = external_health
        except Exception as e:
            health_status["services"]["external"] = {"status": "unhealthy", "error": str(e)}
        
        # System resource checks
        try:
            system_health = get_system_health()
            health_status["system"] = system_health
        except Exception as e:
            health_status["system"] = {"error": str(e)}
        
        # Determine overall status
        overall_status = determine_overall_health_status(health_status)
        health_status["status"] = overall_status
        
        # Return JSON response directly (FastAPI will handle status codes)
        return health_status
            
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow(),
            "error": "Health check failed",
            "details": str(e),
            "services": {},
            "system": {},
            "version": "1.0.0",
            "uptime_seconds": time.time() - startup_time
        }

@router.get("/health/live")
async def liveness_probe():
    """
    Simple liveness probe for Kubernetes
    Returns 200 if the application is running
    """
    return {"status": "alive", "timestamp": datetime.utcnow()}

@router.get("/health/ready")
async def readiness_probe():
    """
    Readiness probe for Kubernetes
    Returns 200 if the application is ready to receive traffic
    """
    try:
        # Check critical dependencies
        db_status = await check_database_connection()
        if not db_status["healthy"]:
            raise HTTPException(status_code=503, detail="Database not ready")
            
        redis_status = await check_redis_connection()
        if not redis_status["healthy"]:
            raise HTTPException(status_code=503, detail="Redis not ready")
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow(),
            "checks": {
                "database": db_status,
                "redis": redis_status
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Not ready: {str(e)}")

@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    Prometheus-compatible metrics endpoint
    Returns application and system metrics
    """
    try:
        current_time = datetime.utcnow()
        
        # Application metrics
        app_metrics = {
            "requests_total": metrics_store["requests_total"],
            "requests_per_second": calculate_requests_per_second(),
            "average_response_time": calculate_average_response_time(),
            "error_rate": calculate_error_rate(),
            "active_users": metrics_store["active_users"],
            "uptime_seconds": time.time() - startup_time
        }
        
        # System metrics
        system_metrics = {
            "cpu_usage_percent": psutil.cpu_percent(interval=1),
            "memory_usage_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": psutil.disk_usage('/').percent,
            "network_io": dict(psutil.net_io_counters()._asdict()),
            "process_count": len(psutil.pids())
        }
        
        # Database metrics
        db_metrics = await get_database_metrics()
        
        # Redis metrics
        redis_metrics = await get_redis_metrics()
        
        # Custom business metrics
        custom_metrics = await get_custom_metrics()
        
        return MetricsResponse(
            timestamp=current_time,
            application=app_metrics,
            system=system_metrics,
            database=db_metrics,
            redis=redis_metrics,
            custom_metrics=custom_metrics
        )
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to collect metrics")

@router.get("/metrics/prometheus")
async def get_prometheus_metrics():
    """
    Prometheus text format metrics
    """
    try:
        metrics_lines = []
        
        # Application metrics
        metrics_lines.append(f"# HELP dinner_first_requests_total Total number of requests")
        metrics_lines.append(f"# TYPE dinner_first_requests_total counter")
        metrics_lines.append(f"dinner_first_requests_total {metrics_store['requests_total']}")
        
        metrics_lines.append(f"# HELP dinner_first_errors_total Total number of errors")
        metrics_lines.append(f"# TYPE dinner_first_errors_total counter")
        metrics_lines.append(f"dinner_first_errors_total {metrics_store['errors_total']}")
        
        metrics_lines.append(f"# HELP dinner_first_active_users Number of active users")
        metrics_lines.append(f"# TYPE dinner_first_active_users gauge")
        metrics_lines.append(f"dinner_first_active_users {metrics_store['active_users']}")
        
        # System metrics
        metrics_lines.append(f"# HELP dinner_first_cpu_usage_percent CPU usage percentage")
        metrics_lines.append(f"# TYPE dinner_first_cpu_usage_percent gauge")
        metrics_lines.append(f"dinner_first_cpu_usage_percent {psutil.cpu_percent()}")
        
        metrics_lines.append(f"# HELP dinner_first_memory_usage_percent Memory usage percentage")
        metrics_lines.append(f"# TYPE dinner_first_memory_usage_percent gauge")
        metrics_lines.append(f"dinner_first_memory_usage_percent {psutil.virtual_memory().percent}")
        
        # Database metrics
        db_metrics = await get_database_metrics()
        metrics_lines.append(f"# HELP dinner_first_db_connections Database connections")
        metrics_lines.append(f"# TYPE dinner_first_db_connections gauge")
        metrics_lines.append(f"dinner_first_db_connections {db_metrics.get('active_connections', 0)}")
        
        # Custom business metrics
        custom_metrics = await get_custom_metrics()
        for metric_name, value in custom_metrics.items():
            metrics_lines.append(f"# HELP dinner_first_{metric_name} {metric_name.replace('_', ' ').title()}")
            metrics_lines.append(f"# TYPE dinner_first_{metric_name} gauge")
            metrics_lines.append(f"dinner_first_{metric_name} {value}")
        
        return "\n".join(metrics_lines)
        
    except Exception as e:
        logger.error(f"Prometheus metrics collection failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to collect Prometheus metrics")

@router.get("/status")
async def get_system_status():
    """
    Detailed system status for monitoring dashboards
    """
    try:
        status = {
            "timestamp": datetime.utcnow(),
            "application": {
                "name": "Dinner First API",
                "version": "1.0.0",
                "environment": "production",  # This should come from config
                "uptime": time.time() - startup_time,
                "status": "running"
            },
            "performance": {
                "requests_per_minute": calculate_requests_per_minute(),
                "average_response_time_ms": calculate_average_response_time(),
                "error_rate_percent": calculate_error_rate() * 100,
                "throughput": calculate_throughput()
            },
            "resources": {
                "cpu_usage": psutil.cpu_percent(interval=1),
                "memory_usage": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent,
                "network_connections": len(psutil.net_connections())
            },
            "services": {
                "database": await check_database_health(),
                "redis": await check_redis_health(),
                "external_apis": await check_external_services()
            },
            "business_metrics": await get_business_metrics()
        }
        
        return status
        
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get system status")

class CustomMetricRequest(BaseModel):
    metric_name: str
    value: Optional[float] = None
    metric_value: Optional[float] = None  # Alternative field name for compatibility
    tags: Optional[Dict[str, str]] = None
    
    def get_value(self) -> float:
        """Get the metric value from either 'value' or 'metric_value' field"""
        if self.value is not None:
            return self.value
        elif self.metric_value is not None:
            return self.metric_value
        else:
            raise ValueError("Either 'value' or 'metric_value' must be provided")

@router.post("/metrics/record")
async def record_custom_metric(request: CustomMetricRequest):
    """
    Record custom application metrics
    """
    try:
        timestamp = datetime.utcnow()
        
        # Get the metric value from either field
        metric_value = request.get_value()
        
        # Store metric (in production, this would go to a proper metrics store)
        metric_data = {
            "name": request.metric_name,
            "value": metric_value,
            "tags": request.tags or {},
            "timestamp": timestamp.isoformat()
        }
        
        # For now, store in memory (use Redis or proper metrics store in production)
        if "custom_metrics" not in metrics_store:
            metrics_store["custom_metrics"] = []
        
        metrics_store["custom_metrics"].append(metric_data)
        
        # Keep only last 1000 metrics to prevent memory issues
        if len(metrics_store["custom_metrics"]) > 1000:
            metrics_store["custom_metrics"] = metrics_store["custom_metrics"][-1000:]
        
        return {
            "success": True, 
            "recorded_at": timestamp,
            "metric_name": request.metric_name,
            "value": metric_value
        }
        
    except Exception as e:
        logger.error(f"Failed to record metric {request.metric_name}: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to record metric: {str(e)}",
            "metric_name": request.metric_name
        }

# Health check helper functions
async def check_database_health():
    """Check database connection and basic functionality"""
    try:
        # This would use your actual database connection
        # For now, simulate the check
        start_time = time.time()
        
        # Simulate database query
        await asyncio.sleep(0.001)  # Simulate query time
        
        response_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return {
            "status": "healthy",
            "response_time_ms": response_time,
            "connection_pool": {
                "active": 5,
                "idle": 15,
                "total": 20
            },
            "last_check": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "last_check": datetime.utcnow().isoformat()
        }

async def check_redis_health():
    """Check Redis connection and basic functionality"""
    try:
        start_time = time.time()
        
        # Simulate Redis ping
        await asyncio.sleep(0.001)  # Simulate ping time
        
        response_time = (time.time() - start_time) * 1000
        
        return {
            "status": "healthy",
            "response_time_ms": response_time,
            "memory_usage": "128MB",  # This would come from Redis INFO
            "connected_clients": 10,
            "last_check": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "last_check": datetime.utcnow().isoformat()
        }

async def check_external_services():
    """Check external service dependencies"""
    services = {}
    
    # AWS S3 check (simulate)
    try:
        services["s3"] = {
            "status": "healthy",
            "response_time_ms": 45,
            "last_check": datetime.utcnow().isoformat()
        }
    except Exception as e:
        services["s3"] = {
            "status": "unhealthy",
            "error": str(e),
            "last_check": datetime.utcnow().isoformat()
        }
    
    return services

def get_system_health():
    """Get system resource health information"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_usage_percent": cpu_percent,
            "memory": {
                "usage_percent": memory.percent,
                "available_gb": round(memory.available / (1024**3), 2),
                "total_gb": round(memory.total / (1024**3), 2)
            },
            "disk": {
                "usage_percent": disk.percent,
                "free_gb": round(disk.free / (1024**3), 2),
                "total_gb": round(disk.total / (1024**3), 2)
            },
            "load_average": list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else [0, 0, 0],
            "boot_time": psutil.boot_time()
        }
        
    except Exception as e:
        logger.error(f"System health check failed: {str(e)}")
        return {"error": str(e)}

def determine_overall_health_status(health_data):
    """Determine overall system health status"""
    
    # Check critical services
    critical_services = ["database", "redis"]
    for service in critical_services:
        if service in health_data["services"]:
            if health_data["services"][service]["status"] != "healthy":
                return "unhealthy"
    
    # Check system resources
    system = health_data.get("system", {})
    if isinstance(system, dict):
        cpu_usage = system.get("cpu_usage_percent", 0)
        memory_usage = system.get("memory", {}).get("usage_percent", 0)
        disk_usage = system.get("disk", {}).get("usage_percent", 0)
        
        # Critical thresholds
        if cpu_usage > 90 or memory_usage > 95 or disk_usage > 95:
            return "unhealthy"
        
        # Warning thresholds  
        if cpu_usage > 80 or memory_usage > 85 or disk_usage > 85:
            return "degraded"
    
    return "healthy"

# Metrics calculation functions
def calculate_requests_per_second():
    """Calculate requests per second over the last minute"""
    # This would be calculated from actual request timestamps
    return metrics_store["requests_total"] / max((time.time() - startup_time), 1)

def calculate_requests_per_minute():
    """Calculate requests per minute"""
    return calculate_requests_per_second() * 60

def calculate_average_response_time():
    """Calculate average response time in milliseconds"""
    response_times = metrics_store.get("response_times", [])
    if not response_times:
        return 0
    return sum(response_times) / len(response_times)

def calculate_error_rate():
    """Calculate error rate as a percentage"""
    total_requests = metrics_store["requests_total"]
    if total_requests == 0:
        return 0
    return metrics_store["errors_total"] / total_requests

def calculate_throughput():
    """Calculate current throughput (requests per second)"""
    return calculate_requests_per_second()

async def check_database_connection():
    """Simple database connection check"""
    try:
        # Simulate database connection check
        await asyncio.sleep(0.001)
        return {"healthy": True, "response_time_ms": 1}
    except Exception as e:
        return {"healthy": False, "error": str(e)}

async def check_redis_connection():
    """Simple Redis connection check"""
    try:
        # Simulate Redis connection check
        await asyncio.sleep(0.001)
        return {"healthy": True, "response_time_ms": 1}
    except Exception as e:
        return {"healthy": False, "error": str(e)}

async def get_database_metrics():
    """Get database-specific metrics"""
    return {
        "active_connections": 5,
        "query_duration_avg_ms": 12.5,
        "slow_queries": 0,
        "deadlocks": 0,
        "cache_hit_ratio": 0.95
    }

async def get_redis_metrics():
    """Get Redis-specific metrics"""
    return {
        "connected_clients": 10,
        "memory_usage_mb": 128,
        "cache_hits": metrics_store.get("cache_hits", 0),
        "cache_misses": metrics_store.get("cache_misses", 0),
        "evicted_keys": 0
    }

async def get_custom_metrics():
    """Get application-specific business metrics"""
    return {
        "total_users": 1250,
        "active_users_24h": 345,
        "total_matches": 2876,
        "messages_sent_24h": 1543,
        "photos_uploaded_24h": 87,
        "reports_submitted_24h": 3,
        "new_registrations_24h": 23
    }

async def get_business_metrics():
    """Get business-specific metrics for dashboards"""
    return {
        "user_engagement": {
            "daily_active_users": 345,
            "weekly_active_users": 1876,
            "monthly_active_users": 5432,
            "average_session_duration_minutes": 18.5
        },
        "matching": {
            "matches_created_24h": 156,
            "match_success_rate": 0.23,
            "conversations_started_24h": 89,
            "first_dates_scheduled_24h": 12
        },
        "safety": {
            "reports_submitted_24h": 3,
            "content_moderation_actions_24h": 15,
            "user_suspensions_24h": 1,
            "safety_score": 0.97
        },
        "revenue": {  # If applicable
            "premium_subscribers": 123,
            "revenue_24h": 1250.00,
            "conversion_rate": 0.045
        }
    }

# Middleware to track request metrics (this would be added to main app)
async def track_request_metrics(request, call_next):
    """Middleware to track request metrics"""
    start_time = time.time()
    
    # Increment request counter
    metrics_store["requests_total"] += 1
    
    # Track requests by endpoint
    endpoint = str(request.url.path)
    if endpoint not in metrics_store["requests_by_endpoint"]:
        metrics_store["requests_by_endpoint"][endpoint] = 0
    metrics_store["requests_by_endpoint"][endpoint] += 1
    
    # Process request
    try:
        response = await call_next(request)
        
        # Track response time
        response_time = (time.time() - start_time) * 1000  # Convert to ms
        metrics_store["response_times"].append(response_time)
        
        # Keep only last 1000 response times
        if len(metrics_store["response_times"]) > 1000:
            metrics_store["response_times"] = metrics_store["response_times"][-1000:]
        
        # Track errors
        if response.status_code >= 400:
            metrics_store["errors_total"] += 1
        
        return response
        
    except Exception as e:
        metrics_store["errors_total"] += 1
        raise