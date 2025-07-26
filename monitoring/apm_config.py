# Application Performance Monitoring (APM) Configuration for Dinner First
# Comprehensive monitoring with New Relic, DataDog, and custom metrics

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
import logging
import time
import psutil
import asyncio
from dataclasses import dataclass, asdict
from functools import wraps
import redis
import json

logger = logging.getLogger(__name__)

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

class AlertSeverity(Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

@dataclass
class PerformanceMetric:
    name: str
    value: float
    metric_type: MetricType
    tags: Dict[str, str]
    timestamp: datetime
    
@dataclass
class AlertRule:
    name: str
    metric: str
    threshold: float
    comparison: str  # gt, lt, eq
    severity: AlertSeverity
    duration_minutes: int
    enabled: bool = True

class APMService:
    """
    Comprehensive Application Performance Monitoring for dating platform
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.metrics_buffer: List[PerformanceMetric] = []
        self.alert_rules: List[AlertRule] = []
        
        # Performance tracking
        self.performance_config = {
            'buffer_size': 1000,
            'flush_interval': 30,  # seconds
            'retention_days': 30,
            'sampling_rate': 0.1,  # 10% sampling for high-volume metrics
        }
        
        # Dating platform specific metrics
        self._setup_dating_metrics()
        self._setup_alert_rules()
        
        # Start background tasks
        asyncio.create_task(self._metrics_flusher())
        asyncio.create_task(self._system_monitor())
        asyncio.create_task(self._alert_processor())
    
    def _setup_dating_metrics(self):
        """Setup dating platform specific metrics"""
        self.dating_metrics = {
            # User engagement metrics
            'user_sessions_active': MetricType.GAUGE,
            'user_registration_rate': MetricType.COUNTER,
            'user_churn_rate': MetricType.GAUGE,
            'user_retention_7d': MetricType.GAUGE,
            'user_retention_30d': MetricType.GAUGE,
            
            # Matching metrics
            'matches_created_rate': MetricType.COUNTER,
            'match_success_rate': MetricType.GAUGE,
            'compatibility_score_avg': MetricType.GAUGE,
            'swipe_rate': MetricType.COUNTER,
            'like_rate': MetricType.GAUGE,
            
            # Communication metrics
            'messages_sent_rate': MetricType.COUNTER,
            'conversation_start_rate': MetricType.COUNTER,
            'response_rate': MetricType.GAUGE,
            'average_response_time': MetricType.HISTOGRAM,
            
            # Soul Before Skin specific
            'revelations_shared_rate': MetricType.COUNTER,
            'revelation_completion_rate': MetricType.GAUGE,
            'photo_reveal_rate': MetricType.COUNTER,
            'photo_reveal_success_rate': MetricType.GAUGE,
            
            # Business metrics
            'subscription_conversion_rate': MetricType.GAUGE,
            'revenue_per_user': MetricType.GAUGE,
            'customer_lifetime_value': MetricType.GAUGE,
            'churn_prevention_success_rate': MetricType.GAUGE,
            
            # Technical performance
            'api_response_time': MetricType.HISTOGRAM,
            'database_query_time': MetricType.HISTOGRAM,
            'cache_hit_ratio': MetricType.GAUGE,
            'error_rate': MetricType.GAUGE,
            'throughput_rps': MetricType.GAUGE,
        }
    
    def _setup_alert_rules(self):
        """Setup alert rules for critical metrics"""
        self.alert_rules = [
            # Critical system alerts
            AlertRule(
                name="High Error Rate",
                metric="error_rate",
                threshold=0.05,  # 5%
                comparison="gt",
                severity=AlertSeverity.CRITICAL,
                duration_minutes=5
            ),
            AlertRule(
                name="Slow API Response",
                metric="api_response_time_p95",
                threshold=2000,  # 2 seconds
                comparison="gt",
                severity=AlertSeverity.WARNING,
                duration_minutes=10
            ),
            AlertRule(
                name="Low Cache Hit Ratio",
                metric="cache_hit_ratio",
                threshold=0.7,  # 70%
                comparison="lt",
                severity=AlertSeverity.WARNING,
                duration_minutes=15
            ),
            AlertRule(
                name="High CPU Usage",
                metric="cpu_usage_percent",
                threshold=80,
                comparison="gt",
                severity=AlertSeverity.WARNING,
                duration_minutes=10
            ),
            AlertRule(
                name="High Memory Usage",
                metric="memory_usage_percent",
                threshold=85,
                comparison="gt",
                severity=AlertSeverity.WARNING,
                duration_minutes=10
            ),
            
            # Business critical alerts
            AlertRule(
                name="Low Match Success Rate",
                metric="match_success_rate",
                threshold=0.3,  # 30%
                comparison="lt",
                severity=AlertSeverity.WARNING,
                duration_minutes=30
            ),
            AlertRule(
                name="High User Churn",
                metric="user_churn_rate",
                threshold=0.1,  # 10%
                comparison="gt",
                severity=AlertSeverity.CRITICAL,
                duration_minutes=60
            ),
            AlertRule(
                name="Low Revelation Completion",
                metric="revelation_completion_rate",
                threshold=0.4,  # 40%
                comparison="lt",
                severity=AlertSeverity.WARNING,
                duration_minutes=45
            ),
        ]
    
    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a performance metric"""
        try:
            if name in self.dating_metrics:
                metric_type = self.dating_metrics[name]
            else:
                metric_type = MetricType.GAUGE  # Default
            
            metric = PerformanceMetric(
                name=name,
                value=value,
                metric_type=metric_type,
                tags=tags or {},
                timestamp=datetime.utcnow()
            )
            
            self.metrics_buffer.append(metric)
            
            # Flush if buffer is full
            if len(self.metrics_buffer) >= self.performance_config['buffer_size']:
                asyncio.create_task(self._flush_metrics())
            
        except Exception as e:
            logger.error(f"Failed to record metric {name}: {e}")
    
    def record_timer(self, name: str, duration_ms: float, tags: Dict[str, str] = None):
        """Record timing metric"""
        self.record_metric(f"{name}_duration_ms", duration_ms, tags)
        self.record_metric(f"{name}_count", 1, tags)
    
    def increment_counter(self, name: str, value: float = 1, tags: Dict[str, str] = None):
        """Increment a counter metric"""
        self.record_metric(name, value, tags)
    
    def set_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Set a gauge value"""
        self.record_metric(name, value, tags)
    
    async def _flush_metrics(self):
        """Flush metrics buffer to storage"""
        if not self.metrics_buffer:
            return
        
        try:
            # Prepare metrics for storage
            metrics_data = []
            for metric in self.metrics_buffer:
                metric_data = asdict(metric)
                metric_data['timestamp'] = metric.timestamp.isoformat()
                metric_data['metric_type'] = metric.metric_type.value
                metrics_data.append(metric_data)
            
            # Store in Redis time series
            pipe = self.redis_client.pipeline()
            
            for metric_data in metrics_data:
                key = f"metrics:{metric_data['name']}"
                value = json.dumps(metric_data)
                
                # Store with timestamp as score for time-based queries
                timestamp_score = metric_data['timestamp']
                pipe.zadd(key, {value: time.time()})
                
                # Set expiry
                pipe.expire(key, 86400 * self.performance_config['retention_days'])
            
            pipe.execute()
            
            # Send to external APM systems
            await self._send_to_external_apm(metrics_data)
            
            # Clear buffer
            self.metrics_buffer.clear()
            
            logger.debug(f"Flushed {len(metrics_data)} metrics")
            
        except Exception as e:
            logger.error(f"Failed to flush metrics: {e}")
    
    async def _send_to_external_apm(self, metrics_data: List[Dict]):
        """Send metrics to external APM systems"""
        try:
            # Send to New Relic
            await self._send_to_newrelic(metrics_data)
            
            # Send to DataDog
            await self._send_to_datadog(metrics_data)
            
            # Send to custom APM endpoint
            await self._send_to_custom_apm(metrics_data)
            
        except Exception as e:
            logger.error(f"Failed to send to external APM: {e}")
    
    async def _send_to_newrelic(self, metrics_data: List[Dict]):
        """Send metrics to New Relic"""
        try:
            # New Relic Metric API integration
            import aiohttp
            
            newrelic_api_key = "your_newrelic_api_key"  # From environment
            newrelic_url = "https://metric-api.newrelic.com/metric/v1"
            
            # Format metrics for New Relic
            nr_metrics = []
            for metric in metrics_data:
                nr_metric = {
                    "name": f"dinner_first.{metric['name']}",
                    "type": metric['metric_type'],
                    "value": metric['value'],
                    "timestamp": int(datetime.fromisoformat(metric['timestamp']).timestamp() * 1000),
                    "attributes": metric['tags']
                }
                nr_metrics.append(nr_metric)
            
            payload = {
                "metrics": nr_metrics
            }
            
            headers = {
                "Content-Type": "application/json",
                "Api-Key": newrelic_api_key
            }
            
            # Send to New Relic (mock implementation)
            logger.debug(f"Would send {len(nr_metrics)} metrics to New Relic")
            
        except Exception as e:
            logger.error(f"New Relic integration error: {e}")
    
    async def _send_to_datadog(self, metrics_data: List[Dict]):
        """Send metrics to DataDog"""
        try:
            # DataDog API integration
            datadog_api_key = "your_datadog_api_key"  # From environment
            
            # Format metrics for DataDog
            dd_metrics = []
            for metric in metrics_data:
                dd_metric = {
                    "metric": f"dinner_first.{metric['name']}",
                    "type": metric['metric_type'],
                    "points": [[
                        int(datetime.fromisoformat(metric['timestamp']).timestamp()),
                        metric['value']
                    ]],
                    "tags": [f"{k}:{v}" for k, v in metric['tags'].items()]
                }
                dd_metrics.append(dd_metric)
            
            # Send to DataDog (mock implementation)
            logger.debug(f"Would send {len(dd_metrics)} metrics to DataDog")
            
        except Exception as e:
            logger.error(f"DataDog integration error: {e}")
    
    async def _send_to_custom_apm(self, metrics_data: List[Dict]):
        """Send metrics to custom APM endpoint"""
        try:
            # Custom internal APM system
            apm_endpoint = "https://apm.dinner_first.internal/api/metrics"
            
            payload = {
                "service": "dinner_first-backend",
                "environment": "production",
                "metrics": metrics_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Send to internal APM (mock implementation)
            logger.debug(f"Would send {len(metrics_data)} metrics to custom APM")
            
        except Exception as e:
            logger.error(f"Custom APM integration error: {e}")
    
    async def _metrics_flusher(self):
        """Background task to flush metrics periodically"""
        while True:
            try:
                await asyncio.sleep(self.performance_config['flush_interval'])
                await self._flush_metrics()
            except Exception as e:
                logger.error(f"Metrics flusher error: {e}")
    
    async def _system_monitor(self):
        """Monitor system resources"""
        while True:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.record_metric("cpu_usage_percent", cpu_percent)
                
                # Memory usage
                memory = psutil.virtual_memory()
                self.record_metric("memory_usage_percent", memory.percent)
                self.record_metric("memory_used_bytes", memory.used)
                self.record_metric("memory_available_bytes", memory.available)
                
                # Disk usage
                disk = psutil.disk_usage('/')
                disk_percent = (disk.used / disk.total) * 100
                self.record_metric("disk_usage_percent", disk_percent)
                
                # Network I/O
                network = psutil.net_io_counters()
                self.record_metric("network_bytes_sent", network.bytes_sent)
                self.record_metric("network_bytes_recv", network.bytes_recv)
                
                # Process count
                process_count = len(psutil.pids())
                self.record_metric("process_count", process_count)
                
                # Load average (Unix only)
                try:
                    load_avg = psutil.getloadavg()
                    self.record_metric("load_average_1m", load_avg[0])
                    self.record_metric("load_average_5m", load_avg[1])
                    self.record_metric("load_average_15m", load_avg[2])
                except AttributeError:
                    pass  # Windows doesn't have load average
                
                await asyncio.sleep(60)  # Monitor every minute
                
            except Exception as e:
                logger.error(f"System monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _alert_processor(self):
        """Process alerts based on metric thresholds"""
        while True:
            try:
                await self._check_alert_rules()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Alert processor error: {e}")
                await asyncio.sleep(60)
    
    async def _check_alert_rules(self):
        """Check all alert rules against current metrics"""
        for rule in self.alert_rules:
            if not rule.enabled:
                continue
            
            try:
                # Get recent metric values
                metric_values = await self._get_recent_metric_values(
                    rule.metric, rule.duration_minutes
                )
                
                if not metric_values:
                    continue
                
                # Calculate average value over duration
                avg_value = sum(metric_values) / len(metric_values)
                
                # Check threshold
                threshold_breached = False
                if rule.comparison == "gt" and avg_value > rule.threshold:
                    threshold_breached = True
                elif rule.comparison == "lt" and avg_value < rule.threshold:
                    threshold_breached = True
                elif rule.comparison == "eq" and abs(avg_value - rule.threshold) < 0.01:
                    threshold_breached = True
                
                if threshold_breached:
                    await self._trigger_alert(rule, avg_value)
                
            except Exception as e:
                logger.error(f"Alert rule check error for {rule.name}: {e}")
    
    async def _get_recent_metric_values(self, metric_name: str, duration_minutes: int) -> List[float]:
        """Get recent metric values for alert checking"""
        try:
            key = f"metrics:{metric_name}"
            
            # Get values from the last duration_minutes
            end_time = time.time()
            start_time = end_time - (duration_minutes * 60)
            
            # Get data from Redis
            data = self.redis_client.zrangebyscore(key, start_time, end_time)
            
            values = []
            for item in data:
                try:
                    metric_data = json.loads(item)
                    values.append(metric_data['value'])
                except (json.JSONDecodeError, KeyError):
                    continue
            
            return values
            
        except Exception as e:
            logger.error(f"Failed to get recent metric values for {metric_name}: {e}")
            return []
    
    async def _trigger_alert(self, rule: AlertRule, current_value: float):
        """Trigger an alert"""
        try:
            alert_data = {
                "rule_name": rule.name,
                "metric": rule.metric,
                "current_value": current_value,
                "threshold": rule.threshold,
                "severity": rule.severity.value,
                "timestamp": datetime.utcnow().isoformat(),
                "comparison": rule.comparison
            }
            
            # Store alert
            alert_key = f"alerts:{rule.name}:{int(time.time())}"
            self.redis_client.set(alert_key, json.dumps(alert_data), ex=86400 * 7)  # Keep for 7 days
            
            # Send notifications
            await self._send_alert_notifications(alert_data)
            
            logger.warning(f"Alert triggered: {rule.name} - {current_value} {rule.comparison} {rule.threshold}")
            
        except Exception as e:
            logger.error(f"Failed to trigger alert for {rule.name}: {e}")
    
    async def _send_alert_notifications(self, alert_data: Dict):
        """Send alert notifications"""
        try:
            # Send to Slack
            await self._send_slack_alert(alert_data)
            
            # Send to email
            await self._send_email_alert(alert_data)
            
            # Send to PagerDuty (for critical alerts)
            if alert_data['severity'] == AlertSeverity.CRITICAL.value:
                await self._send_pagerduty_alert(alert_data)
            
        except Exception as e:
            logger.error(f"Failed to send alert notifications: {e}")
    
    async def _send_slack_alert(self, alert_data: Dict):
        """Send alert to Slack"""
        # Mock Slack integration
        logger.info(f"Would send Slack alert: {alert_data['rule_name']}")
    
    async def _send_email_alert(self, alert_data: Dict):
        """Send alert via email"""
        # Mock email integration
        logger.info(f"Would send email alert: {alert_data['rule_name']}")
    
    async def _send_pagerduty_alert(self, alert_data: Dict):
        """Send critical alert to PagerDuty"""
        # Mock PagerDuty integration
        logger.info(f"Would send PagerDuty alert: {alert_data['rule_name']}")
    
    # Public methods for getting metrics and status
    
    async def get_metrics_summary(self, duration_hours: int = 1) -> Dict[str, Any]:
        """Get metrics summary for dashboard"""
        try:
            end_time = time.time()
            start_time = end_time - (duration_hours * 3600)
            
            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "duration_hours": duration_hours,
                "metrics": {}
            }
            
            # Get key metrics
            key_metrics = [
                "api_response_time", "error_rate", "cache_hit_ratio",
                "cpu_usage_percent", "memory_usage_percent",
                "matches_created_rate", "user_sessions_active"
            ]
            
            for metric in key_metrics:
                values = await self._get_recent_metric_values(metric, duration_hours * 60)
                
                if values:
                    summary["metrics"][metric] = {
                        "current": values[-1] if values else 0,
                        "average": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                        "count": len(values)
                    }
                else:
                    summary["metrics"][metric] = {
                        "current": 0,
                        "average": 0,
                        "min": 0,
                        "max": 0,
                        "count": 0
                    }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get metrics summary: {e}")
            return {}
    
    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get currently active alerts"""
        try:
            # Get all alert keys
            alert_keys = self.redis_client.keys("alerts:*")
            
            alerts = []
            for key in alert_keys:
                try:
                    alert_data = json.loads(self.redis_client.get(key))
                    alerts.append(alert_data)
                except (json.JSONDecodeError, TypeError):
                    continue
            
            # Sort by timestamp (newest first)
            alerts.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return alerts[:50]  # Return last 50 alerts
            
        except Exception as e:
            logger.error(f"Failed to get active alerts: {e}")
            return []
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status"""
        try:
            # Basic health checks
            health_status = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "checks": {}
            }
            
            # Redis connectivity
            try:
                self.redis_client.ping()
                health_status["checks"]["redis"] = "healthy"
            except Exception:
                health_status["checks"]["redis"] = "unhealthy"
                health_status["status"] = "degraded"
            
            # Metrics buffer size
            buffer_size = len(self.metrics_buffer)
            if buffer_size < self.performance_config['buffer_size'] * 0.8:
                health_status["checks"]["metrics_buffer"] = "healthy"
            else:
                health_status["checks"]["metrics_buffer"] = "warning"
                health_status["status"] = "degraded"
            
            # System resources (basic check)
            try:
                cpu_percent = psutil.cpu_percent()
                memory_percent = psutil.virtual_memory().percent
                
                if cpu_percent < 80 and memory_percent < 85:
                    health_status["checks"]["system_resources"] = "healthy"
                else:
                    health_status["checks"]["system_resources"] = "warning"
                    health_status["status"] = "degraded"
                    
            except Exception:
                health_status["checks"]["system_resources"] = "unknown"
            
            return health_status
            
        except Exception as e:
            logger.error(f"Health status check failed: {e}")
            return {
                "status": "error",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }

# Decorators for automatic performance tracking

def track_performance(metric_name: str, tags: Dict[str, str] = None):
    """Decorator to track function performance"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                success = True
            except Exception as e:
                success = False
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                
                final_tags = tags.copy() if tags else {}
                final_tags['success'] = str(success)
                
                # Get global APM service
                apm_service = get_apm_service()
                apm_service.record_timer(metric_name, duration_ms, final_tags)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                success = True
            except Exception as e:
                success = False
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                
                final_tags = tags.copy() if tags else {}
                final_tags['success'] = str(success)
                
                # Get global APM service
                apm_service = get_apm_service()
                apm_service.record_timer(metric_name, duration_ms, final_tags)
            
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def track_counter(metric_name: str, tags: Dict[str, str] = None):
    """Decorator to track function call counts"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Get global APM service
            apm_service = get_apm_service()
            apm_service.increment_counter(metric_name, 1, tags)
            
            return result
        
        return wrapper
    return decorator

# Global APM service instance
_apm_service: Optional[APMService] = None

def get_apm_service() -> APMService:
    """Get global APM service instance"""
    global _apm_service
    if _apm_service is None:
        raise RuntimeError("APM service not initialized")
    return _apm_service

def init_apm_service(redis_client: redis.Redis) -> APMService:
    """Initialize global APM service"""
    global _apm_service
    _apm_service = APMService(redis_client)
    return _apm_service