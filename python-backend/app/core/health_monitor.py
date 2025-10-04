"""
Health Monitoring System - Sprint 4
Comprehensive health checks for real-time features and system monitoring
"""

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import psutil
from app.core.database import get_db
from app.core.logging_config import get_logger
from app.services.realtime_connection_manager import realtime_manager
from sqlalchemy import text
from sqlalchemy.orm import Session


class HealthStatus(str, Enum):
    """Health status levels"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


class ComponentType(str, Enum):
    """Types of system components to monitor"""

    DATABASE = "database"
    WEBSOCKET = "websocket"
    ACTIVITY_TRACKING = "activity_tracking"
    REALTIME_INTEGRATION = "realtime_integration"
    SYSTEM_RESOURCES = "system_resources"
    LOGGING = "logging"


@dataclass
class HealthCheck:
    """Individual health check result"""

    component: ComponentType
    status: HealthStatus
    message: str
    details: Dict[str, Any]
    check_duration_ms: float
    timestamp: datetime
    error: Optional[str] = None


@dataclass
class SystemHealth:
    """Overall system health summary"""

    overall_status: HealthStatus
    checks: List[HealthCheck]
    summary: Dict[str, Any]
    timestamp: datetime
    uptime_seconds: float


class HealthMonitor:
    """Comprehensive health monitoring system"""

    def __init__(self):
        self.logger = get_logger("app.core.health_monitor")
        self.start_time = datetime.utcnow()
        self._last_health_check = None
        self._health_check_interval = 60  # seconds

    async def check_database_health(self, db: Session) -> HealthCheck:
        """Check database connectivity and performance"""
        start_time = time.time()

        try:
            # Simple connectivity test
            db.execute(text("SELECT 1")).fetchone()

            # Performance test - count users
            users_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar()

            # Check for long-running queries (if supported)
            try:
                active_connections = db.execute(
                    text("SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active'")
                ).scalar()
            except Exception:
                active_connections = "unknown"

            duration_ms = (time.time() - start_time) * 1000

            # Determine status based on response time
            if duration_ms > 5000:  # > 5s
                status = HealthStatus.CRITICAL
                message = f"Database response very slow: {duration_ms:.2f}ms"
            elif duration_ms > 1000:  # > 1s
                status = HealthStatus.DEGRADED
                message = f"Database response slow: {duration_ms:.2f}ms"
            else:
                status = HealthStatus.HEALTHY
                message = f"Database responsive: {duration_ms:.2f}ms"

            return HealthCheck(
                component=ComponentType.DATABASE,
                status=status,
                message=message,
                details={
                    "users_count": users_count,
                    "active_connections": active_connections,
                    "response_time_ms": duration_ms,
                },
                check_duration_ms=duration_ms,
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(f"Database health check failed: {str(e)}")

            return HealthCheck(
                component=ComponentType.DATABASE,
                status=HealthStatus.CRITICAL,
                message="Database connection failed",
                details={"response_time_ms": duration_ms},
                check_duration_ms=duration_ms,
                timestamp=datetime.utcnow(),
                error=str(e),
            )

    async def check_websocket_health(self) -> HealthCheck:
        """Check WebSocket manager health"""
        start_time = time.time()

        try:
            stats = realtime_manager.get_connection_stats()

            # Evaluate WebSocket health
            active_connections = stats.get("active_connections", 0)
            stats.get("total_channel_subscriptions", 0)
            queued_messages = stats.get("queued_messages", 0)

            # Determine status based on metrics
            if queued_messages > 1000:
                status = HealthStatus.DEGRADED
                message = f"High message queue: {queued_messages} pending messages"
            elif active_connections > 100:
                status = HealthStatus.HEALTHY
                message = f"WebSocket system active: {active_connections} connections"
            else:
                status = HealthStatus.HEALTHY
                message = f"WebSocket system ready: {active_connections} connections"

            duration_ms = (time.time() - start_time) * 1000

            return HealthCheck(
                component=ComponentType.WEBSOCKET,
                status=status,
                message=message,
                details=stats,
                check_duration_ms=duration_ms,
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(f"WebSocket health check failed: {str(e)}")

            return HealthCheck(
                component=ComponentType.WEBSOCKET,
                status=HealthStatus.UNHEALTHY,
                message="WebSocket system check failed",
                details={"response_time_ms": duration_ms},
                check_duration_ms=duration_ms,
                timestamp=datetime.utcnow(),
                error=str(e),
            )

    async def check_activity_tracking_health(self, db: Session) -> HealthCheck:
        """Check activity tracking system health"""
        start_time = time.time()

        try:
            from app.services.activity_tracking_service import activity_tracker

            # Check if service is responsive
            activity_types = list(activity_tracker.activity_display_map.keys())

            # Check recent activity logs
            recent_activities = db.execute(
                text(
                    """
                    SELECT COUNT(*) FROM user_activity_log
                    WHERE started_at > NOW() - INTERVAL '1 hour'
                """
                )
            ).scalar()

            # Check active sessions
            active_sessions = db.execute(
                text(
                    """
                    SELECT COUNT(*) FROM user_activity_sessions
                    WHERE ended_at IS NULL
                """
                )
            ).scalar()

            duration_ms = (time.time() - start_time) * 1000

            status = HealthStatus.HEALTHY
            message = (
                f"Activity tracking operational: {len(activity_types)} activity types"
            )

            return HealthCheck(
                component=ComponentType.ACTIVITY_TRACKING,
                status=status,
                message=message,
                details={
                    "activity_types_count": len(activity_types),
                    "recent_activities_1h": recent_activities,
                    "active_sessions": active_sessions,
                    "response_time_ms": duration_ms,
                },
                check_duration_ms=duration_ms,
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(f"Activity tracking health check failed: {str(e)}")

            return HealthCheck(
                component=ComponentType.ACTIVITY_TRACKING,
                status=HealthStatus.UNHEALTHY,
                message="Activity tracking system check failed",
                details={"response_time_ms": duration_ms},
                check_duration_ms=duration_ms,
                timestamp=datetime.utcnow(),
                error=str(e),
            )

    async def check_system_resources(self) -> HealthCheck:
        """Check system resource utilization"""
        start_time = time.time()

        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # Memory usage
            memory = psutil.virtual_memory()

            # Disk usage
            disk = psutil.disk_usage("/")

            duration_ms = (time.time() - start_time) * 1000

            # Determine status based on resource usage
            if cpu_percent > 90 or memory.percent > 90 or disk.percent > 95:
                status = HealthStatus.CRITICAL
                message = "Critical resource usage detected"
            elif cpu_percent > 75 or memory.percent > 75 or disk.percent > 85:
                status = HealthStatus.DEGRADED
                message = "High resource usage detected"
            else:
                status = HealthStatus.HEALTHY
                message = "System resources normal"

            return HealthCheck(
                component=ComponentType.SYSTEM_RESOURCES,
                status=status,
                message=message,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": round(memory.available / (1024**3), 2),
                    "disk_percent": disk.percent,
                    "disk_free_gb": round(disk.free / (1024**3), 2),
                },
                check_duration_ms=duration_ms,
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(f"System resources health check failed: {str(e)}")

            return HealthCheck(
                component=ComponentType.SYSTEM_RESOURCES,
                status=HealthStatus.UNHEALTHY,
                message="System resources check failed",
                details={"response_time_ms": duration_ms},
                check_duration_ms=duration_ms,
                timestamp=datetime.utcnow(),
                error=str(e),
            )

    async def check_realtime_integration_health(self) -> HealthCheck:
        """Check real-time integration services health"""
        start_time = time.time()

        try:
            from app.services.realtime_integration_service import realtime_integration

            # Get integration statistics
            stats = realtime_integration.get_realtime_statistics()

            duration_ms = (time.time() - start_time) * 1000

            status = HealthStatus.HEALTHY
            message = "Real-time integration operational"

            return HealthCheck(
                component=ComponentType.REALTIME_INTEGRATION,
                status=status,
                message=message,
                details=stats,
                check_duration_ms=duration_ms,
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.logger.error(f"Real-time integration health check failed: {str(e)}")

            return HealthCheck(
                component=ComponentType.REALTIME_INTEGRATION,
                status=HealthStatus.UNHEALTHY,
                message="Real-time integration check failed",
                details={"response_time_ms": duration_ms},
                check_duration_ms=duration_ms,
                timestamp=datetime.utcnow(),
                error=str(e),
            )

    async def perform_comprehensive_health_check(
        self, db: Optional[Session] = None
    ) -> SystemHealth:
        """Perform comprehensive health check of all system components"""
        check_start_time = time.time()

        if db is None:
            db = next(get_db())

        try:
            # Run all health checks concurrently
            tasks = [
                self.check_database_health(db),
                self.check_websocket_health(),
                self.check_activity_tracking_health(db),
                self.check_system_resources(),
                self.check_realtime_integration_health(),
            ]

            checks = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter out exceptions and convert to HealthCheck objects
            valid_checks = []
            for check in checks:
                if isinstance(check, Exception):
                    self.logger.error(
                        f"Health check failed with exception: {str(check)}"
                    )
                    # Create error health check
                    valid_checks.append(
                        HealthCheck(
                            component=ComponentType.SYSTEM_RESOURCES,  # Generic
                            status=HealthStatus.CRITICAL,
                            message="Health check failed with exception",
                            details={},
                            check_duration_ms=0,
                            timestamp=datetime.utcnow(),
                            error=str(check),
                        )
                    )
                else:
                    valid_checks.append(check)

            # Determine overall status
            statuses = [check.status for check in valid_checks]
            if HealthStatus.CRITICAL in statuses:
                overall_status = HealthStatus.CRITICAL
            elif HealthStatus.UNHEALTHY in statuses:
                overall_status = HealthStatus.UNHEALTHY
            elif HealthStatus.DEGRADED in statuses:
                overall_status = HealthStatus.DEGRADED
            else:
                overall_status = HealthStatus.HEALTHY

            # Create summary
            uptime = (datetime.utcnow() - self.start_time).total_seconds()
            total_check_duration = (time.time() - check_start_time) * 1000

            summary = {
                "total_components": len(valid_checks),
                "healthy_components": len(
                    [c for c in valid_checks if c.status == HealthStatus.HEALTHY]
                ),
                "degraded_components": len(
                    [c for c in valid_checks if c.status == HealthStatus.DEGRADED]
                ),
                "unhealthy_components": len(
                    [c for c in valid_checks if c.status == HealthStatus.UNHEALTHY]
                ),
                "critical_components": len(
                    [c for c in valid_checks if c.status == HealthStatus.CRITICAL]
                ),
                "total_check_duration_ms": total_check_duration,
                "uptime_seconds": uptime,
            }

            system_health = SystemHealth(
                overall_status=overall_status,
                checks=valid_checks,
                summary=summary,
                timestamp=datetime.utcnow(),
                uptime_seconds=uptime,
            )

            # Cache the result
            self._last_health_check = system_health

            # Log health status
            self.logger.info(
                f"System health check completed: {overall_status}",
                extra={
                    "overall_status": overall_status.value,
                    "total_components": len(valid_checks),
                    "healthy_components": summary["healthy_components"],
                    "check_duration_ms": total_check_duration,
                },
            )

            return system_health

        except Exception as e:
            self.logger.error(
                f"Comprehensive health check failed: {str(e)}", exc_info=True
            )

            # Return critical status health check
            return SystemHealth(
                overall_status=HealthStatus.CRITICAL,
                checks=[
                    HealthCheck(
                        component=ComponentType.SYSTEM_RESOURCES,
                        status=HealthStatus.CRITICAL,
                        message="System health check completely failed",
                        details={},
                        check_duration_ms=0,
                        timestamp=datetime.utcnow(),
                        error=str(e),
                    )
                ],
                summary={"error": "Health check system failure"},
                timestamp=datetime.utcnow(),
                uptime_seconds=(datetime.utcnow() - self.start_time).total_seconds(),
            )
        finally:
            if db:
                db.close()

    def get_last_health_check(self) -> Optional[SystemHealth]:
        """Get the last cached health check result"""
        return self._last_health_check

    def to_dict(self, health: SystemHealth) -> Dict[str, Any]:
        """Convert SystemHealth to dictionary for API responses"""
        return {
            "overall_status": health.overall_status.value,
            "timestamp": health.timestamp.isoformat(),
            "uptime_seconds": health.uptime_seconds,
            "summary": health.summary,
            "components": [
                {
                    "component": check.component.value,
                    "status": check.status.value,
                    "message": check.message,
                    "details": check.details,
                    "check_duration_ms": check.check_duration_ms,
                    "timestamp": check.timestamp.isoformat(),
                    "error": check.error,
                }
                for check in health.checks
            ],
        }


# Global instance
health_monitor = HealthMonitor()
