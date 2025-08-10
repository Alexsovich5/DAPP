"""
Soul Analytics Models - Phase 4 Enhanced Analytics
Track user engagement, connection quality, and system performance
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, DECIMAL, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class AnalyticsEventType(str, enum.Enum):
    """Types of analytics events we track"""
    # User engagement
    LOGIN = "login"
    PROFILE_VIEW = "profile_view"
    SWIPE_ACTION = "swipe_action"
    MESSAGE_SENT = "message_sent"
    MESSAGE_READ = "message_read"
    
    # Revelation system
    REVELATION_SHARED = "revelation_shared"
    REVELATION_VIEWED = "revelation_viewed"
    DAY_UNLOCKED = "day_unlocked"
    PHOTO_CONSENT_GIVEN = "photo_consent_given"
    
    # Connection events
    CONNECTION_INITIATED = "connection_initiated"
    CONNECTION_ACCEPTED = "connection_accepted"
    CONNECTION_STAGE_ADVANCED = "connection_stage_advanced"
    
    # App interaction
    HAPTIC_FEEDBACK_TRIGGERED = "haptic_feedback_triggered"
    ANIMATION_VIEWED = "animation_viewed"
    TYPING_INDICATOR_SHOWN = "typing_indicator_shown"


class UserEngagementAnalytics(Base):
    """Track detailed user engagement metrics"""
    __tablename__ = "user_engagement_analytics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Event details
    event_type = Column(String, nullable=False)
    event_data = Column(JSON, nullable=True)  # Additional event context
    
    # Session context
    session_id = Column(String, nullable=True)
    device_type = Column(String, nullable=True)  # mobile, tablet, desktop
    browser_info = Column(JSON, nullable=True)
    
    # Location context (anonymized)
    timezone = Column(String, nullable=True)
    country_code = Column(String, nullable=True)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])


class SoulConnectionAnalytics(Base):
    """Analytics specific to soul connections and their quality"""
    __tablename__ = "soul_connection_analytics"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("soul_connections.id"), nullable=False)
    
    # Quality metrics
    message_frequency_score = Column(DECIMAL(5,2), nullable=True)
    revelation_completion_rate = Column(DECIMAL(5,2), nullable=True)
    mutual_engagement_score = Column(DECIMAL(5,2), nullable=True)
    conversation_depth_score = Column(DECIMAL(5,2), nullable=True)
    
    # Timeline metrics
    time_to_first_message = Column(Integer, nullable=True)  # seconds
    time_to_revelation_sharing = Column(Integer, nullable=True)  # seconds
    time_to_photo_reveal = Column(Integer, nullable=True)  # seconds
    
    # Prediction scores
    success_prediction_score = Column(DECIMAL(5,2), nullable=True)
    compatibility_validation_score = Column(DECIMAL(5,2), nullable=True)
    
    # Metadata
    calculation_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    connection = relationship("SoulConnection", foreign_keys=[connection_id])


class EmotionalJourneyTracking(Base):
    """Track the emotional journey through the revelation process"""
    __tablename__ = "emotional_journey_tracking"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    connection_id = Column(Integer, ForeignKey("soul_connections.id"), nullable=False)
    
    # Journey stage
    journey_stage = Column(String, nullable=False)  # discovery, revelation, connection
    emotional_state = Column(String, nullable=True)  # curious, excited, nervous, etc.
    
    # Engagement metrics
    time_spent = Column(Integer, nullable=True)  # seconds spent in this stage
    interaction_count = Column(Integer, default=0)
    haptic_triggers = Column(Integer, default=0)
    
    # Sentiment analysis (if implemented)
    message_sentiment_score = Column(DECIMAL(5,2), nullable=True)
    revelation_sentiment_score = Column(DECIMAL(5,2), nullable=True)
    
    # Timing
    stage_entered_at = Column(DateTime, default=datetime.utcnow)
    stage_completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    connection = relationship("SoulConnection", foreign_keys=[connection_id])


class SystemPerformanceMetrics(Base):
    """Track system performance and technical metrics"""
    __tablename__ = "system_performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    
    # Performance metrics
    metric_name = Column(String, nullable=False)
    metric_value = Column(DECIMAL(10,4), nullable=False)
    metric_unit = Column(String, nullable=True)  # ms, count, percentage, etc.
    
    # Context
    component = Column(String, nullable=True)  # frontend, backend, database
    endpoint = Column(String, nullable=True)  # which API endpoint
    user_agent = Column(Text, nullable=True)
    
    # Aggregation level
    aggregation_period = Column(String, nullable=True)  # hour, day, week
    sample_size = Column(Integer, nullable=True)
    
    # Timing
    measured_at = Column(DateTime, default=datetime.utcnow, index=True)


class UserRetentionMetrics(Base):
    """Track user retention and lifecycle metrics"""
    __tablename__ = "user_retention_metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Retention tracking
    cohort_month = Column(String, nullable=False)  # YYYY-MM of registration
    days_since_registration = Column(Integer, nullable=False)
    
    # Activity flags
    is_active_day_1 = Column(Boolean, default=False)
    is_active_day_7 = Column(Boolean, default=False)
    is_active_day_30 = Column(Boolean, default=False)
    
    # Milestone achievements
    completed_onboarding = Column(Boolean, default=False)
    made_first_connection = Column(Boolean, default=False)
    shared_first_revelation = Column(Boolean, default=False)
    reached_photo_reveal = Column(Boolean, default=False)
    
    # Last activity
    last_active_date = Column(DateTime, nullable=True)
    total_sessions = Column(Integer, default=0)
    total_session_duration = Column(Integer, default=0)  # seconds
    
    # Updated tracking
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])


class CompatibilityAccuracyTracking(Base):
    """Track how accurate our compatibility predictions are"""
    __tablename__ = "compatibility_accuracy_tracking"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("soul_connections.id"), nullable=False)
    
    # Original prediction
    predicted_compatibility_score = Column(DECIMAL(5,2), nullable=False)
    prediction_confidence = Column(DECIMAL(5,2), nullable=True)
    algorithm_version = Column(String, nullable=False)
    
    # Actual outcomes
    actual_message_count = Column(Integer, nullable=True)
    actual_revelation_completion_rate = Column(DECIMAL(5,2), nullable=True)
    connection_lasted_days = Column(Integer, nullable=True)
    reached_photo_reveal = Column(Boolean, default=False)
    mutual_satisfaction_score = Column(DECIMAL(5,2), nullable=True)
    
    # Accuracy calculation
    prediction_accuracy = Column(DECIMAL(5,2), nullable=True)
    prediction_error = Column(DECIMAL(5,2), nullable=True)
    
    # Timing
    prediction_made_at = Column(DateTime, default=datetime.utcnow)
    outcome_evaluated_at = Column(DateTime, nullable=True)
    
    # Relationships
    connection = relationship("SoulConnection", foreign_keys=[connection_id])