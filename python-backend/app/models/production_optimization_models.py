"""
Phase 8A: Production Optimization Models
Database models for performance monitoring, optimization, and production readiness
"""
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, DECIMAL, Float, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class MetricType(str, enum.Enum):
    """Types of performance metrics"""
    API_PERFORMANCE = "api_performance"
    DATABASE_PERFORMANCE = "database_performance"
    SYSTEM_PERFORMANCE = "system_performance"
    USER_EXPERIENCE = "user_experience"
    SECURITY_METRIC = "security_metric"
    CACHE_PERFORMANCE = "cache_performance"
    ERROR_TRACKING = "error_tracking"


class OptimizationType(str, enum.Enum):
    """Types of optimizations applied"""
    QUERY_OPTIMIZATION = "query_optimization"
    INDEX_OPTIMIZATION = "index_optimization"
    CACHE_OPTIMIZATION = "cache_optimization"
    API_OPTIMIZATION = "api_optimization"
    SECURITY_OPTIMIZATION = "security_optimization"
    RESOURCE_OPTIMIZATION = "resource_optimization"


class SecurityLevel(str, enum.Enum):
    """Security audit levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MonitoringStatus(str, enum.Enum):
    """Monitoring system status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class BackupStatus(str, enum.Enum):
    """Backup operation status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SCHEDULED = "scheduled"


class PerformanceMetric(Base):
    """Performance metrics tracking for production optimization"""
    __tablename__ = "performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    
    # Metric identification
    metric_type = Column(String, nullable=False)  # MetricType enum
    metric_name = Column(String, nullable=False)
    metric_category = Column(String, nullable=True)
    
    # Metric values
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String, nullable=True)
    target_value = Column(Float, nullable=True)
    
    # Context and metadata
    metric_data = Column(JSON, nullable=True)
    environment = Column(String, default="production")
    server_instance = Column(String, nullable=True)
    
    # Performance context
    request_id = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    endpoint = Column(String, nullable=True)
    
    # Timestamps
    measured_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_performance_metrics_type_time', 'metric_type', 'measured_at'),
        Index('ix_performance_metrics_name_time', 'metric_name', 'measured_at'),
        Index('ix_performance_metrics_environment', 'environment', 'measured_at'),
    )


class CacheEntry(Base):
    """Cache entries and performance tracking"""
    __tablename__ = "cache_entries"

    id = Column(Integer, primary_key=True, index=True)
    
    # Cache identification
    cache_key = Column(String, nullable=False, unique=True)
    cache_type = Column(String, nullable=False)  # redis, application, query, etc.
    cache_layer = Column(String, nullable=False)
    
    # Cache data
    cached_data = Column(Text, nullable=True)  # Serialized data
    data_size_bytes = Column(Integer, nullable=True)
    
    # Cache performance
    hit_count = Column(Integer, default=0)
    miss_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, nullable=True)
    access_frequency = Column(Float, default=0.0)
    
    # Cache configuration
    ttl_seconds = Column(Integer, nullable=True)
    max_age = Column(DateTime, nullable=True)
    auto_refresh = Column(Boolean, default=False)
    
    # Cache status
    is_active = Column(Boolean, default=True)
    invalidated_at = Column(DateTime, nullable=True)
    invalidation_reason = Column(String, nullable=True)
    
    # Metadata
    cache_metadata = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index('ix_cache_entries_key_type', 'cache_key', 'cache_type'),
        Index('ix_cache_entries_active', 'is_active', 'last_accessed'),
    )


class DatabaseOptimization(Base):
    """Database optimization tracking and results"""
    __tablename__ = "database_optimizations"

    id = Column(Integer, primary_key=True, index=True)
    
    # Optimization details
    optimization_type = Column(String, nullable=False)  # OptimizationType enum
    optimization_target = Column(String, nullable=False)  # table, query, index, etc.
    optimization_description = Column(Text, nullable=False)
    
    # Performance impact
    before_metrics = Column(JSON, nullable=True)
    after_metrics = Column(JSON, nullable=True)
    performance_improvement_percent = Column(Float, nullable=True)
    
    # Optimization configuration
    optimization_config = Column(JSON, nullable=False)
    sql_statements = Column(JSON, nullable=True)  # SQL commands executed
    
    # Status and results
    is_applied = Column(Boolean, default=False)
    applied_at = Column(DateTime, nullable=True)
    rollback_available = Column(Boolean, default=False)
    rollback_sql = Column(JSON, nullable=True)
    
    # Validation and monitoring
    validation_results = Column(JSON, nullable=True)
    monitoring_period_hours = Column(Integer, default=24)
    success_confirmed = Column(Boolean, nullable=True)
    
    # Metadata
    created_by = Column(String, default="system")
    optimization_metadata = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SecurityAudit(Base):
    """Security audit results and tracking"""
    __tablename__ = "security_audits"

    id = Column(Integer, primary_key=True, index=True)
    
    # Audit details
    audit_type = Column(String, nullable=False)
    audit_scope = Column(String, nullable=False)  # full_system, api, database, etc.
    security_level = Column(String, nullable=False)  # SecurityLevel enum
    
    # Audit results
    vulnerabilities_found = Column(Integer, default=0)
    critical_issues = Column(Integer, default=0)
    high_priority_issues = Column(Integer, default=0)
    medium_priority_issues = Column(Integer, default=0)
    low_priority_issues = Column(Integer, default=0)
    
    # Detailed findings
    audit_findings = Column(JSON, nullable=True)
    security_recommendations = Column(JSON, nullable=True)
    compliance_status = Column(JSON, nullable=True)
    
    # Audit execution
    audit_started_at = Column(DateTime, nullable=False)
    audit_completed_at = Column(DateTime, nullable=True)
    audit_duration_minutes = Column(Integer, nullable=True)
    
    # Remediation tracking
    issues_resolved = Column(Integer, default=0)
    resolution_deadline = Column(DateTime, nullable=True)
    next_audit_scheduled = Column(DateTime, nullable=True)
    
    # Audit metadata
    auditor = Column(String, default="automated_system")
    audit_tools_used = Column(JSON, nullable=True)
    environment = Column(String, default="production")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SystemMonitoring(Base):
    """System monitoring configuration and status"""
    __tablename__ = "system_monitoring"

    id = Column(Integer, primary_key=True, index=True)
    
    # Monitoring configuration
    monitoring_type = Column(String, nullable=False)
    environment = Column(String, nullable=False)
    status = Column(String, default=MonitoringStatus.ACTIVE.value)
    
    # Monitoring targets
    target_services = Column(JSON, nullable=True)
    monitored_metrics = Column(JSON, nullable=True)
    alert_thresholds = Column(JSON, nullable=True)
    
    # Monitoring schedule
    check_interval_seconds = Column(Integer, default=300)
    last_check_time = Column(DateTime, nullable=True)
    next_check_time = Column(DateTime, nullable=True)
    
    # Alert configuration
    alert_enabled = Column(Boolean, default=True)
    alert_contacts = Column(JSON, nullable=True)
    alert_channels = Column(JSON, nullable=True)
    
    # Status tracking
    consecutive_failures = Column(Integer, default=0)
    last_alert_sent = Column(DateTime, nullable=True)
    alert_suppression_until = Column(DateTime, nullable=True)
    
    # Configuration and metadata
    configuration = Column(JSON, nullable=False)
    monitoring_metadata = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BackupOperation(Base):
    """Backup operations tracking and management"""
    __tablename__ = "backup_operations"

    id = Column(Integer, primary_key=True, index=True)
    
    # Backup details
    backup_type = Column(String, nullable=False)  # database, files, configuration
    backup_scope = Column(String, nullable=False)  # full, incremental, differential
    environment = Column(String, nullable=False)
    
    # Backup execution
    status = Column(String, default=BackupStatus.PENDING.value)
    scheduled_at = Column(DateTime, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    
    # Backup results
    backup_size_bytes = Column(Integer, nullable=True)
    backup_location = Column(String, nullable=True)
    backup_checksum = Column(String, nullable=True)
    
    # Success and verification
    verification_status = Column(String, nullable=True)
    verification_completed_at = Column(DateTime, nullable=True)
    restore_tested = Column(Boolean, default=False)
    
    # Retention and cleanup
    retention_days = Column(Integer, default=30)
    expires_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Metadata
    backup_metadata = Column(JSON, nullable=True)
    configuration_snapshot = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CDNConfiguration(Base):
    """CDN configuration and performance tracking"""
    __tablename__ = "cdn_configurations"

    id = Column(Integer, primary_key=True, index=True)
    
    # CDN details
    cdn_provider = Column(String, nullable=False)
    cdn_endpoint = Column(String, nullable=False)
    environment = Column(String, nullable=False)
    
    # Configuration
    cache_rules = Column(JSON, nullable=True)
    compression_settings = Column(JSON, nullable=True)
    security_settings = Column(JSON, nullable=True)
    
    # Performance metrics
    cache_hit_ratio = Column(Float, nullable=True)
    average_response_time_ms = Column(Float, nullable=True)
    bandwidth_saved_percent = Column(Float, nullable=True)
    
    # Geographic distribution
    edge_locations = Column(JSON, nullable=True)
    geographic_performance = Column(JSON, nullable=True)
    
    # Status and monitoring
    is_active = Column(Boolean, default=True)
    last_performance_check = Column(DateTime, nullable=True)
    health_status = Column(String, default="healthy")
    
    # Cost and usage
    monthly_bandwidth_gb = Column(Float, nullable=True)
    monthly_requests = Column(Integer, nullable=True)
    estimated_monthly_cost = Column(DECIMAL(10, 2), nullable=True)
    
    # Configuration metadata
    configuration_version = Column(String, nullable=True)
    last_configuration_update = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LoadBalancingConfig(Base):
    """Load balancing configuration and health tracking"""
    __tablename__ = "load_balancing_configs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Load balancer details
    load_balancer_name = Column(String, nullable=False)
    load_balancer_type = Column(String, nullable=False)  # application, network
    environment = Column(String, nullable=False)
    
    # Configuration
    balancing_algorithm = Column(String, default="round_robin")
    health_check_config = Column(JSON, nullable=True)
    ssl_termination = Column(Boolean, default=True)
    
    # Backend servers
    backend_servers = Column(JSON, nullable=True)
    active_servers = Column(Integer, default=0)
    unhealthy_servers = Column(Integer, default=0)
    
    # Performance metrics
    requests_per_second = Column(Float, nullable=True)
    average_response_time_ms = Column(Float, nullable=True)
    error_rate_percent = Column(Float, nullable=True)
    
    # Health monitoring
    last_health_check = Column(DateTime, nullable=True)
    consecutive_health_failures = Column(Integer, default=0)
    failover_triggered = Column(Boolean, default=False)
    
    # Traffic distribution
    traffic_distribution = Column(JSON, nullable=True)
    session_affinity = Column(Boolean, default=False)
    
    # Status and alerts
    is_active = Column(Boolean, default=True)
    alert_threshold_breached = Column(Boolean, default=False)
    maintenance_mode = Column(Boolean, default=False)
    
    # Configuration versioning
    configuration_version = Column(String, nullable=True)
    configuration_history = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PerformanceAlert(Base):
    """Performance alerts and notifications"""
    __tablename__ = "performance_alerts"

    id = Column(Integer, primary_key=True, index=True)
    
    # Alert details
    alert_type = Column(String, nullable=False)
    alert_severity = Column(String, nullable=False)  # low, medium, high, critical
    alert_source = Column(String, nullable=False)
    
    # Alert trigger
    metric_name = Column(String, nullable=False)
    threshold_value = Column(Float, nullable=False)
    actual_value = Column(Float, nullable=False)
    threshold_direction = Column(String, nullable=False)  # above, below
    
    # Alert context
    environment = Column(String, nullable=False)
    service_component = Column(String, nullable=True)
    affected_users = Column(Integer, nullable=True)
    
    # Alert lifecycle
    triggered_at = Column(DateTime, default=datetime.utcnow)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    auto_resolved = Column(Boolean, default=False)
    
    # Resolution tracking
    resolution_time_minutes = Column(Integer, nullable=True)
    resolution_action = Column(Text, nullable=True)
    root_cause = Column(Text, nullable=True)
    
    # Notification tracking
    notifications_sent = Column(JSON, nullable=True)
    escalation_level = Column(Integer, default=1)
    suppressed = Column(Boolean, default=False)
    
    # Alert metadata
    alert_data = Column(JSON, nullable=True)
    related_metrics = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_performance_alerts_severity_time', 'alert_severity', 'triggered_at'),
        Index('ix_performance_alerts_resolved', 'resolved_at'),
        Index('ix_performance_alerts_environment', 'environment', 'triggered_at'),
    )


class OptimizationRecommendation(Base):
    """AI-generated optimization recommendations"""
    __tablename__ = "optimization_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    
    # Recommendation details
    recommendation_type = Column(String, nullable=False)  # OptimizationType enum
    priority = Column(String, nullable=False)  # low, medium, high, critical
    category = Column(String, nullable=False)
    
    # Recommendation content
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    implementation_steps = Column(JSON, nullable=True)
    
    # Impact analysis
    expected_improvement_percent = Column(Float, nullable=True)
    estimated_implementation_hours = Column(Float, nullable=True)
    risk_level = Column(String, default="low")
    
    # Implementation tracking
    status = Column(String, default="pending")  # pending, in_progress, completed, dismissed
    implemented_at = Column(DateTime, nullable=True)
    implementation_results = Column(JSON, nullable=True)
    
    # Context and metadata
    triggering_metrics = Column(JSON, nullable=True)
    environment = Column(String, nullable=False)
    generated_by = Column(String, default="ai_system")
    
    # Validation
    effectiveness_validated = Column(Boolean, nullable=True)
    validation_results = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)