"""
Phase 7: Advanced AI Matching Evolution Models
Database models for machine learning optimization and predictive analytics
"""
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, DECIMAL, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class AlgorithmType(str, enum.Enum):
    """Types of matching algorithms"""
    RULE_BASED = "rule_based"
    MACHINE_LEARNING = "machine_learning"
    HYBRID = "hybrid"
    DEEP_LEARNING = "deep_learning"
    ENSEMBLE = "ensemble"


class OutcomeType(str, enum.Enum):
    """Types of matching outcomes"""
    SUCCESS = "success"
    MODERATE_SUCCESS = "moderate_success"
    NEUTRAL = "neutral"
    DISAPPOINTING = "disappointing"
    FAILURE = "failure"


class ExperimentStatus(str, enum.Enum):
    """Status of A/B test experiments"""
    PLANNING = "planning"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ANALYZING = "analyzing"


class PredictionConfidence(str, enum.Enum):
    """Confidence levels for predictions"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class MatchingAlgorithmVersion(Base):
    """Different versions of matching algorithms with their configurations"""
    __tablename__ = "matching_algorithm_versions"

    id = Column(Integer, primary_key=True, index=True)
    version_name = Column(String, nullable=False, unique=True)
    algorithm_type = Column(String, nullable=False)  # AlgorithmType enum
    
    # Algorithm configuration
    algorithm_config = Column(JSON, nullable=False)
    feature_weights = Column(JSON, nullable=False)
    model_parameters = Column(JSON, nullable=True)
    
    # Performance tracking
    is_active = Column(Boolean, default=False)
    performance_score = Column(Float, nullable=True)
    success_rate = Column(Float, nullable=True)
    
    # Metadata
    created_by = Column(String, default="system")
    description = Column(Text, nullable=True)
    changelog = Column(JSON, nullable=True)
    
    # Deployment information
    deployed_at = Column(DateTime, nullable=True)
    deprecated_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserBehaviorAnalytics(Base):
    """Analytics on user behavior for matching optimization"""
    __tablename__ = "user_behavior_analytics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Interaction patterns
    interaction_patterns = Column(JSON, nullable=True)
    communication_style_analysis = Column(JSON, nullable=True)
    response_time_patterns = Column(JSON, nullable=True)
    engagement_metrics = Column(JSON, nullable=True)
    
    # Preference evolution
    preference_evolution = Column(JSON, nullable=True)
    preference_stability_score = Column(Float, nullable=True)
    learning_rate = Column(Float, default=0.1)
    
    # Success indicators
    success_indicators = Column(JSON, nullable=True)
    failure_patterns = Column(JSON, nullable=True)
    behavioral_score = Column(Float, default=0.5)
    
    # Predictive features
    predicted_preferences = Column(JSON, nullable=True)
    compatibility_patterns = Column(JSON, nullable=True)
    optimal_match_timing = Column(JSON, nullable=True)
    
    # Learning metadata
    data_points_count = Column(Integer, default=0)
    confidence_level = Column(Float, default=0.5)
    last_pattern_update = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])


class MatchingOutcome(Base):
    """Outcomes of matches for algorithm learning"""
    __tablename__ = "matching_outcomes"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("soul_connections.id"), nullable=False)
    algorithm_version = Column(String, nullable=False)
    
    # Outcome classification
    outcome_type = Column(String, nullable=False)  # OutcomeType enum
    outcome_score = Column(Float, nullable=False)  # 0.0 to 1.0
    outcome_details = Column(JSON, nullable=True)
    
    # Success metrics
    messages_exchanged = Column(Integer, default=0)
    revelations_completed = Column(Integer, default=0)
    video_calls_completed = Column(Integer, default=0)
    relationship_duration_days = Column(Integer, nullable=True)
    
    # Feedback scores
    user1_satisfaction = Column(Float, nullable=True)
    user2_satisfaction = Column(Float, nullable=True)
    mutual_interest_score = Column(Float, nullable=True)
    
    # Learning data
    original_prediction = Column(JSON, nullable=True)
    prediction_accuracy = Column(Float, nullable=True)
    contributing_factors = Column(JSON, nullable=True)
    
    # Timing information
    outcome_determined_at = Column(DateTime, nullable=True)
    follow_up_period_days = Column(Integer, default=30)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    connection = relationship("SoulConnection", foreign_keys=[connection_id])


class SuccessPrediction(Base):
    """ML-based predictions for relationship success"""
    __tablename__ = "success_predictions"

    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user2_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Prediction details
    prediction_model_version = Column(String, nullable=False)
    success_probability = Column(Float, nullable=False)
    relationship_duration_prediction = Column(Integer, nullable=True)  # days
    compatibility_breakdown = Column(JSON, nullable=True)
    
    # Key factors
    key_compatibility_factors = Column(JSON, nullable=True)
    risk_factors = Column(JSON, nullable=True)
    improvement_suggestions = Column(JSON, nullable=True)
    
    # Prediction confidence
    prediction_confidence = Column(Float, nullable=False)
    confidence_level = Column(String, default="medium")  # PredictionConfidence enum
    model_accuracy_estimate = Column(Float, nullable=True)
    
    # Validation tracking
    actual_outcome = Column(String, nullable=True)
    prediction_accuracy = Column(Float, nullable=True)
    validation_date = Column(DateTime, nullable=True)
    
    # Metadata
    prediction_metadata = Column(JSON, nullable=True)
    feature_importance = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user1 = relationship("User", foreign_keys=[user1_id])
    user2 = relationship("User", foreign_keys=[user2_id])


class AlgorithmPerformanceMetric(Base):
    """Performance metrics for different algorithm versions"""
    __tablename__ = "algorithm_performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    algorithm_version = Column(String, nullable=False)
    metric_date = Column(DateTime, nullable=False)
    
    # Core performance metrics
    total_matches_made = Column(Integer, default=0)
    successful_matches = Column(Integer, default=0)
    success_rate = Column(Float, nullable=True)
    average_satisfaction_score = Column(Float, nullable=True)
    
    # Quality metrics
    prediction_accuracy = Column(Float, nullable=True)
    false_positive_rate = Column(Float, nullable=True)
    false_negative_rate = Column(Float, nullable=True)
    precision_score = Column(Float, nullable=True)
    recall_score = Column(Float, nullable=True)
    
    # Efficiency metrics
    average_time_to_match = Column(Float, nullable=True)
    computational_cost = Column(Float, nullable=True)
    matches_per_user_average = Column(Float, nullable=True)
    
    # User experience metrics
    user_engagement_score = Column(Float, nullable=True)
    average_response_rate = Column(Float, nullable=True)
    conversation_initiation_rate = Column(Float, nullable=True)
    
    # Long-term metrics
    relationship_retention_rate = Column(Float, nullable=True)
    user_return_rate = Column(Float, nullable=True)
    
    # Metadata
    sample_size = Column(Integer, nullable=False)
    confidence_interval = Column(JSON, nullable=True)
    statistical_significance = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class MatchingExperiment(Base):
    """A/B test experiments for matching algorithms"""
    __tablename__ = "matching_experiments"

    id = Column(Integer, primary_key=True, index=True)
    experiment_name = Column(String, nullable=False)
    experiment_type = Column(String, nullable=False)  # a_b_test, multivariate, etc.
    
    # Experiment configuration
    algorithm_a_config = Column(JSON, nullable=False)
    algorithm_b_config = Column(JSON, nullable=False)
    control_group_percentage = Column(Float, default=0.5)
    
    # Target metrics and goals
    target_metrics = Column(JSON, nullable=False)
    success_criteria = Column(JSON, nullable=False)
    expected_improvement = Column(Float, nullable=True)
    
    # Experiment status
    status = Column(String, default=ExperimentStatus.PLANNING.value)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    expected_duration_days = Column(Integer, nullable=False)
    
    # Sample and participation
    sample_size_target = Column(Integer, nullable=False)
    participants_enrolled = Column(Integer, default=0)
    group_a_size = Column(Integer, default=0)
    group_b_size = Column(Integer, default=0)
    
    # Results tracking
    preliminary_results = Column(JSON, nullable=True)
    final_results = Column(JSON, nullable=True)
    statistical_significance = Column(Float, nullable=True)
    winner_algorithm = Column(String, nullable=True)
    
    # Metadata
    created_by = Column(String, default="system")
    experiment_description = Column(Text, nullable=True)
    hypothesis = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserPreferenceEvolution(Base):
    """Tracking how user preferences evolve over time"""
    __tablename__ = "user_preference_evolution"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Preference snapshots
    preference_snapshot = Column(JSON, nullable=False)
    snapshot_date = Column(DateTime, nullable=False)
    
    # Evolution metrics
    change_magnitude = Column(Float, nullable=True)
    change_direction = Column(JSON, nullable=True)
    stability_score = Column(Float, nullable=True)
    
    # Influencing factors
    influencing_experiences = Column(JSON, nullable=True)
    recent_matches_impact = Column(JSON, nullable=True)
    external_factors = Column(JSON, nullable=True)
    
    # Prediction updates
    updated_predictions = Column(JSON, nullable=True)
    prediction_confidence_change = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])


class RealTimeMatchingAdjustment(Base):
    """Real-time adjustments to matching algorithms per user"""
    __tablename__ = "real_time_matching_adjustments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Adjustment details
    adjustment_type = Column(String, nullable=False)  # outcome_based, preference_based, etc.
    original_weights = Column(JSON, nullable=False)
    adjusted_weights = Column(JSON, nullable=False)
    adjustment_magnitude = Column(Float, nullable=False)
    
    # Reasoning and confidence
    adjustment_reason = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=False)
    expected_improvement = Column(Float, nullable=True)
    
    # Application tracking
    is_applied = Column(Boolean, default=False)
    applied_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Validation and results
    validation_period_days = Column(Integer, default=7)
    actual_improvement = Column(Float, nullable=True)
    was_successful = Column(Boolean, nullable=True)
    
    # Metadata
    triggering_events = Column(JSON, nullable=True)
    rollback_weights = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])


class PredictiveCompatibility(Base):
    """Predictive compatibility scores between users"""
    __tablename__ = "predictive_compatibility"

    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user2_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Compatibility scoring
    algorithm_version = Column(String, nullable=False)
    base_compatibility_score = Column(Float, nullable=False)
    behavioral_adjustment_score = Column(Float, nullable=False)
    predicted_success_probability = Column(Float, nullable=False)
    overall_enhanced_score = Column(Float, nullable=False)
    
    # Detailed breakdown
    compatibility_breakdown = Column(JSON, nullable=True)
    success_factors = Column(JSON, nullable=True)
    risk_factors = Column(JSON, nullable=True)
    
    # Reasoning and explanation
    compatibility_reasoning = Column(JSON, nullable=True)
    human_readable_explanation = Column(Text, nullable=True)
    
    # Validation and updates
    prediction_metadata = Column(JSON, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)
    next_update_due = Column(DateTime, nullable=True)
    
    # Outcome validation
    actual_connection_created = Column(Boolean, nullable=True)
    actual_connection_outcome = Column(String, nullable=True)
    prediction_accuracy_score = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user1 = relationship("User", foreign_keys=[user1_id])
    user2 = relationship("User", foreign_keys=[user2_id])


class MachineLearningModel(Base):
    """ML models used for various matching predictions"""
    __tablename__ = "machine_learning_models"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, nullable=False, unique=True)
    model_type = Column(String, nullable=False)  # neural_network, random_forest, etc.
    model_version = Column(String, nullable=False)
    
    # Model configuration
    model_config = Column(JSON, nullable=False)
    hyperparameters = Column(JSON, nullable=False)
    feature_set = Column(JSON, nullable=False)
    
    # Training information
    training_data_size = Column(Integer, nullable=True)
    training_accuracy = Column(Float, nullable=True)
    validation_accuracy = Column(Float, nullable=True)
    test_accuracy = Column(Float, nullable=True)
    
    # Deployment status
    is_active = Column(Boolean, default=False)
    deployed_at = Column(DateTime, nullable=True)
    last_retrained_at = Column(DateTime, nullable=True)
    next_retraining_due = Column(DateTime, nullable=True)
    
    # Performance tracking
    production_accuracy = Column(Float, nullable=True)
    drift_detection_score = Column(Float, nullable=True)
    performance_degradation = Column(Boolean, default=False)
    
    # Model artifacts
    model_file_path = Column(String, nullable=True)
    model_metadata = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)