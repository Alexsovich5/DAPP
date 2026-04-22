"""
Health Check API Endpoints - Sprint 4
Comprehensive health monitoring and system status endpoints
"""

from datetime import datetime

from app.core.database import get_db
from app.core.health_monitor import HealthStatus, health_monitor
from app.core.logging_config import get_logger
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

logger = get_logger("app.api.v1.routers.health")

router = APIRouter()


@router.get(
    "/",
    summary="Basic Health Check",
    description="Basic health check endpoint for load balancers and monitoring systems",
    response_description="Simple health status response",
    tags=["Health Monitoring"],
)
async def basic_health_check():
    """
    Basic health check for load balancers and monitoring systems.

    Returns a simple status response indicating the service is running.
    This endpoint is designed to be fast and lightweight for frequent polling.

    **Use Cases:**
    - Load balancer health checks
    - Basic monitoring systems
    - Service discovery health verification
    - Uptime monitoring

    **Response Format:**
    - `status`: Always "healthy" if service is responding
    - `timestamp`: ISO formatted timestamp of the response
    - `service`: Service identifier
    - `version`: Current service version
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "dinner-app-backend",
        "version": "1.0.0",
    }


@router.get(
    "/detailed",
    summary="Comprehensive Health Check",
    description="Detailed system health check with comprehensive component analysis",
    response_description="Detailed health status with component breakdown",
    tags=["Health Monitoring"],
)
async def detailed_health_check(
    include_details: bool = Query(
        True,
        description="Include detailed component information (error messages, response times, etc.)",
    ),
    db: Session = Depends(get_db),
):
    """
    Comprehensive system health check with detailed component status.

    Performs in-depth health checks on all system components including:
    - Database connectivity and performance
    - WebSocket connection manager status
    - Activity tracking system health
    - System resource utilization
    - Application metrics and performance

    **Parameters:**
    - `include_details`: If true, includes detailed error messages and performance metrics

    **Response Status Codes:**
    - `200 OK`: System is healthy or degraded but functional
    - `503 Service Unavailable`: System is unhealthy or critical

    **Response Format:**
    - `overall_status`: Overall system health (healthy, degraded, unhealthy, critical)
    - `timestamp`: When the health check was performed
    - `components`: Array of component health statuses
    - `summary`: High-level health summary
    - `check_duration_ms`: Total time taken for health check

    **Component Status Types:**
    - `healthy`: Component is fully operational
    - `degraded`: Component is functional but with reduced performance
    - `unhealthy`: Component has significant issues but may still work
    - `critical`: Component is failing or completely non-functional

    **Use Cases:**
    - Detailed monitoring dashboard
    - System diagnostic tools
    - Health status investigation
    - Performance monitoring
    - Alerting system integration
    """

    try:
        # Perform comprehensive health check
        system_health = await health_monitor.perform_comprehensive_health_check(db)

        # Convert to dictionary
        health_dict = health_monitor.to_dict(system_health)

        # Remove detailed information if not requested
        if not include_details:
            for component in health_dict.get("components", []):
                component.pop("details", None)
                component.pop("error", None)

        # Determine HTTP status code based on overall health
        status_code_map = {
            HealthStatus.HEALTHY: 200,
            HealthStatus.DEGRADED: 200,  # Still functional
            HealthStatus.UNHEALTHY: 503,  # Service unavailable
            HealthStatus.CRITICAL: 503,  # Service unavailable
        }

        status_code = status_code_map.get(system_health.overall_status, 503)

        return JSONResponse(
            content=health_dict,
            status_code=status_code,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

    except Exception as e:
        logger.error(f"Health check endpoint failed: {str(e)}", exc_info=True)

        return JSONResponse(
            content={
                "overall_status": "critical",
                "timestamp": datetime.utcnow().isoformat(),
                "error": "Health check system failure",
                "message": "Unable to determine system health",
            },
            status_code=503,
        )


@router.get(
    "/component/{component_name}",
    summary="Component-Specific Health Check",
    description="Get health status for a specific system component",
    response_description="Individual component health status",
    tags=["Health Monitoring"],
)
async def component_health_check(component_name: str, db: Session = Depends(get_db)):
    """
    Get health status for a specific system component.

    Performs a targeted health check for a single system component.
    This endpoint is useful for monitoring specific subsystems or
    diagnosing issues with particular components.

    **Path Parameters:**
    - `component_name`: Name of the component to check

    **Available Components:**
    - `database`: Database connectivity and performance
    - `websocket`: WebSocket connection manager status
    - `activity_tracking`: Activity tracking system health
    - `system_resources`: System resource utilization
    - `application_metrics`: Application performance metrics

    **Response Status Codes:**
    - `200 OK`: Component is healthy or degraded but functional
    - `404 Not Found`: Component name not recognized
    - `503 Service Unavailable`: Component is unhealthy or critical

    **Response Format:**
    - `component`: Component name
    - `status`: Health status (healthy, degraded, unhealthy, critical)
    - `message`: Human-readable status message
    - `details`: Component-specific metrics and information
    - `check_duration_ms`: Time taken to perform the check
    - `timestamp`: When the check was performed
    - `error`: Error message (if applicable)

    **Use Cases:**
    - Targeted component monitoring
    - Debugging specific subsystem issues
    - Component-specific alerting
    - Granular health dashboard displays
    - Service dependency checks
    """

    try:
        # Perform comprehensive health check
        system_health = await health_monitor.perform_comprehensive_health_check(db)

        # Find the specific component
        component_check = None
        for check in system_health.checks:
            if check.component.value == component_name.lower():
                component_check = check
                break

        if not component_check:
            return JSONResponse(
                content={
                    "error": f"Component '{component_name}' not found",
                    "available_components": [
                        check.component.value for check in system_health.checks
                    ],
                },
                status_code=404,
            )

        # Return component-specific health
        component_data = {
            "component": component_check.component.value,
            "status": component_check.status.value,
            "message": component_check.message,
            "details": component_check.details,
            "check_duration_ms": component_check.check_duration_ms,
            "timestamp": component_check.timestamp.isoformat(),
        }

        if component_check.error:
            component_data["error"] = component_check.error

        # Determine status code
        status_code = (
            200
            if component_check.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
            else 503
        )

        return JSONResponse(content=component_data, status_code=status_code)

    except Exception as e:
        logger.error(f"Component health check failed: {str(e)}", exc_info=True)

        return JSONResponse(
            content={
                "component": component_name,
                "status": "critical",
                "error": "Component health check failed",
                "timestamp": datetime.utcnow().isoformat(),
            },
            status_code=503,
        )


@router.get(
    "/status",
    summary="Cached System Status",
    description="Get cached system status for fast, frequent polling",
    response_description="Cached health status with performance metadata",
    tags=["Health Monitoring"],
)
async def get_system_status():
    """
    Get cached system status for fast, frequent polling.

    Returns the most recent health check results from cache, providing
    a fast response for frequent monitoring without the overhead of
    performing fresh health checks each time.

    **Performance Benefits:**
    - Sub-millisecond response time
    - No database queries or system checks
    - Suitable for high-frequency polling
    - Reduced system load from monitoring

    **Response Format:**
    - `overall_status`: Overall system health from last check
    - `timestamp`: When the cached health check was performed
    - `uptime_seconds`: System uptime in seconds
    - `cache_age_seconds`: Age of the cached data in seconds
    - `is_stale`: Whether the cached data is older than 5 minutes
    - `summary`: High-level summary of system health
    - `components_summary`: Quick overview of each component's status

    **Cache Freshness:**
    - Data is considered fresh for 5 minutes
    - `is_stale` flag indicates if a fresh check is recommended
    - Cache is automatically updated by background health checks

    **Use Cases:**
    - High-frequency monitoring dashboards
    - Load balancer health checks requiring fast response
    - System status widgets in UI
    - Automated monitoring scripts
    - Quick health overview before detailed checks
    """

    try:
        # Get last cached health check
        cached_health = health_monitor.get_last_health_check()

        if cached_health is None:
            # No cached data, return basic status
            return {
                "status": "unknown",
                "message": "No health data available yet",
                "timestamp": datetime.utcnow().isoformat(),
            }

        # Check if cached data is recent (within 5 minutes)
        cache_age = (datetime.utcnow() - cached_health.timestamp).total_seconds()
        is_stale = cache_age > 300  # 5 minutes

        return {
            "overall_status": cached_health.overall_status.value,
            "timestamp": cached_health.timestamp.isoformat(),
            "uptime_seconds": cached_health.uptime_seconds,
            "cache_age_seconds": cache_age,
            "is_stale": is_stale,
            "summary": cached_health.summary,
            "components_summary": {
                check.component.value: check.status.value
                for check in cached_health.checks
            },
        }

    except Exception as e:
        logger.error(f"System status endpoint failed: {str(e)}", exc_info=True)

        return JSONResponse(
            content={
                "status": "error",
                "message": "Unable to retrieve system status",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            },
            status_code=500,
        )


@router.get(
    "/metrics-json",
    summary="Health Metrics for Monitoring (JSON format)",
    description="Get system performance and health metrics as JSON. "
                "Renamed from /metrics so the canonical /metrics path can serve "
                "the Prometheus exposition format (mounted at root).",
    response_description="Structured metrics data for monitoring systems",
    tags=["Health Monitoring", "Metrics"],
)
async def get_health_metrics():
    """
    Get system performance and health metrics for monitoring systems.

    Returns structured metrics data optimized for integration with
    monitoring systems like Prometheus, Grafana, or custom dashboards.
    Provides numeric representations of health states for alerting.

    **Metrics Provided:**
    - `system_uptime_seconds`: Total system uptime
    - `health_check_duration_ms`: Time taken for complete health check
    - `components_*`: Count of components in each health state
    - `overall_status_numeric`: Overall health as numeric value (0-1)
    - `{component}_status_numeric`: Per-component health as numeric value
    - `{component}_response_time_ms`: Response time for each component check

    **Numeric Health Scale:**
    - `1.0`: Healthy (fully operational)
    - `0.7`: Degraded (functional with reduced performance)
    - `0.3`: Unhealthy (significant issues)
    - `0.0`: Critical (failing or non-functional)

    **Monitoring Integration:**
    - Compatible with Prometheus metrics collection
    - Suitable for Grafana dashboard visualization
    - Provides alerting thresholds (< 0.7 = warning, < 0.3 = critical)
    - Includes response time metrics for SLA monitoring

    **Use Cases:**
    - Prometheus metrics scraping
    - Custom monitoring dashboard data
    - Automated alerting systems
    - Performance trend analysis
    - SLA compliance monitoring
    - System health scoring
    """

    try:
        # Get fresh health check
        system_health = await health_monitor.perform_comprehensive_health_check()

        # Extract metrics for monitoring systems (Prometheus format style)
        metrics = {
            "system_uptime_seconds": system_health.uptime_seconds,
            "health_check_duration_ms": system_health.summary.get(
                "total_check_duration_ms", 0
            ),
            "components_total": system_health.summary.get("total_components", 0),
            "components_healthy": system_health.summary.get("healthy_components", 0),
            "components_degraded": system_health.summary.get("degraded_components", 0),
            "components_unhealthy": system_health.summary.get(
                "unhealthy_components", 0
            ),
            "components_critical": system_health.summary.get("critical_components", 0),
            "overall_status_numeric": {
                "healthy": 1,
                "degraded": 0.7,
                "unhealthy": 0.3,
                "critical": 0,
            }.get(system_health.overall_status.value, 0),
        }

        # Add component-specific metrics
        for check in system_health.checks:
            component_name = check.component.value
            metrics[f"{component_name}_status_numeric"] = {
                "healthy": 1,
                "degraded": 0.7,
                "unhealthy": 0.3,
                "critical": 0,
            }.get(check.status.value, 0)

            metrics[f"{component_name}_check_duration_ms"] = check.check_duration_ms

            # Add component-specific details as metrics
            for key, value in check.details.items():
                if isinstance(value, (int, float)):
                    metrics[f"{component_name}_{key}"] = value

        return {
            "timestamp": system_health.timestamp.isoformat(),
            "metrics": metrics,
        }

    except Exception as e:
        logger.error(f"Health metrics endpoint failed: {str(e)}", exc_info=True)

        return JSONResponse(
            content={
                "error": "Unable to retrieve health metrics",
                "timestamp": datetime.utcnow().isoformat(),
            },
            status_code=500,
        )
