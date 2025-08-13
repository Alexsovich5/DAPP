"""
AI Models - Phase 5 Machine Learning Data Architecture
Advanced AI/ML models for soul-based matching and personalization
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, Float, JSON, DECIMAL
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, List, Optional, Any
import enum

from app.core.database import Base


class ModelType(str, enum.Enum):
    """Types of ML models in the system"""
    USER_EMBEDDING = "user_embedding"
    COMPATIBILITY_NEURAL = "compatibility_neural"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    BEHAVIORAL_PATTERN = "behavioral_pattern"
    RECOMMENDATION_ENGINE = "recommendation_engine"
    PERSONALITY_PREDICTION = "personality_prediction"
    CONVERSATION_QUALITY = "conversation_quality"


class TrainingStatus(str, enum.Enum):
    """ML model training status"""
    PENDING = "pending"
    TRAINING = "training"
    VALIDATING = "validating"
    DEPLOYED = "deployed"
    DEPRECATED = "deprecated"
    FAILED = "failed"


class UserProfile(Base):
    """Enhanced user profile with AI-generated insights"""
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # AI-Generated Profile Vectors
    personality_vector = Column(JSON, nullable=True)  # 128-dim embedding
    interests_vector = Column(JSON, nullable=True)    # Interest embeddings
    values_vector = Column(JSON, nullable=True)       # Core values representation
    communication_vector = Column(JSON, nullable=True)  # Communication style
    
    # Personality Analysis (Big 5 + Extended)
    openness_score = Column(Float, nullable=True)          # 0-1 scale
    conscientiousness_score = Column(Float, nullable=True)
    extraversion_score = Column(Float, nullable=True)
    agreeableness_score = Column(Float, nullable=True)
    neuroticism_score = Column(Float, nullable=True)
    
    # Extended Personality Traits
    emotional_intelligence = Column(Float, nullable=True)
    attachment_style = Column(String, nullable=True)      # secure, anxious, avoidant, disorganized
    love_language_primary = Column(String, nullable=True)
    love_language_secondary = Column(String, nullable=True)
    
    # Communication Analysis
    communication_style = Column(String, nullable=True)   # direct, diplomatic, expressive, analytical
    conversation_depth_preference = Column(Float, nullable=True)  # 0-1 scale
    response_time_pattern = Column(JSON, nullable=True)   # Timing preferences
    emoji_usage_pattern = Column(JSON, nullable=True)     # Emotional expression patterns
    
    # Behavioral Patterns
    activity_patterns = Column(JSON, nullable=True)       # Usage patterns, peak hours
    engagement_patterns = Column(JSON, nullable=True)     # How user engages with features
    decision_patterns = Column(JSON, nullable=True)       # Swiping, messaging patterns
    
    # AI Confidence Scores
    profile_completeness_score = Column(Float, default=0.0)
    ai_confidence_level = Column(Float, default=0.0)      # How confident AI is in analysis
    data_quality_score = Column(Float, default=0.0)       # Quality of source data
    
    # Learning and Adaptation
    learning_rate = Column(Float, default=0.1)            # How fast to update profile
    last_updated_by_ai = Column(DateTime)
    ai_update_frequency = Column(Integer, default=7)      # Days between AI updates
    manual_overrides = Column(JSON, nullable=True)        # User corrections to AI insights
    
    # Privacy and Consent
    ai_profiling_consent = Column(Boolean, default=True)
    data_sharing_level = Column(String, default="aggregated")  # none, aggregated, full
    
    # Relationships
    user = relationship("User", back_populates="ai_profile")
    compatibility_scores = relationship("CompatibilityPrediction", foreign_keys="CompatibilityPrediction.user1_profile_id", back_populates="user_profile")
    recommendations = relationship("PersonalizedRecommendation", back_populates="user_profile")
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def get_personality_summary(self) -> Dict[str, Any]:
        """Get human-readable personality summary"""
        return {
            "big_five": {
                "openness": self.openness_score,
                "conscientiousness": self.conscientiousness_score,
                "extraversion": self.extraversion_score,
                "agreeableness": self.agreeableness_score,
                "neuroticism": self.neuroticism_score
            },
            "extended_traits": {
                "emotional_intelligence": self.emotional_intelligence,
                "attachment_style": self.attachment_style,
                "primary_love_language": self.love_language_primary
            },
            "communication": {
                "style": self.communication_style,
                "depth_preference": self.conversation_depth_preference
            }
        }


class MLModel(Base):
    """Machine Learning model metadata and versioning"""
    __tablename__ = "ml_models"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Model Identity
    model_name = Column(String, nullable=False)
    model_type = Column(String, nullable=False)  # ModelType enum value
    version = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    
    # Model Specifications
    architecture = Column(String, nullable=True)          # neural_network, gradient_boosting, etc.
    input_features = Column(JSON, nullable=True)          # Feature specifications
    output_schema = Column(JSON, nullable=True)           # Expected output format
    hyperparameters = Column(JSON, nullable=True)         # Model configuration
    
    # Training Information
    training_status = Column(String, default=TrainingStatus.PENDING)
    training_data_size = Column(Integer, nullable=True)
    validation_accuracy = Column(Float, nullable=True)
    test_accuracy = Column(Float, nullable=True)
    training_duration_minutes = Column(Integer, nullable=True)
    
    # Performance Metrics
    inference_time_ms = Column(Float, nullable=True)      # Average prediction time
    memory_usage_mb = Column(Float, nullable=True)
    cpu_usage_percent = Column(Float, nullable=True)
    
    # Deployment Information
    is_active = Column(Boolean, default=False)
    deployment_date = Column(DateTime, nullable=True)
    model_file_path = Column(String, nullable=True)       # Path to serialized model
    model_checksum = Column(String, nullable=True)        # Integrity verification
    
    # Model Lineage
    parent_model_id = Column(Integer, ForeignKey("ml_models.id"), nullable=True)
    training_config = Column(JSON, nullable=True)         # Complete training configuration
    feature_importance = Column(JSON, nullable=True)       # Feature contribution scores
    
    # Monitoring and Alerting
    prediction_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    last_prediction_at = Column(DateTime, nullable=True)
    drift_detection_score = Column(Float, nullable=True)   # Model drift indicator
    
    # Relationships
    parent_model = relationship("MLModel", remote_side=[id])
    child_models = relationship("MLModel", back_populates="parent_model")
    predictions = relationship("ModelPrediction", back_populates="model")
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @property
    def is_healthy(self) -> bool:
        """Check if model is performing within acceptable parameters"""
        if not self.is_active:
            return False
        
        # Check error rate
        total_predictions = self.prediction_count
        if total_predictions > 100:  # Only check if we have enough data
            error_rate = self.error_count / total_predictions
            if error_rate > 0.05:  # More than 5% error rate
                return False
        
        # Check drift
        if self.drift_detection_score and self.drift_detection_score > 0.8:
            return False
            
        return True


class CompatibilityPrediction(Base):
    """AI-powered compatibility predictions between users"""
    __tablename__ = "compatibility_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    user1_profile_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    user2_profile_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    
    # Prediction Results
    overall_compatibility = Column(Float, nullable=False)  # 0-1 score
    confidence_level = Column(Float, nullable=False)       # Model confidence
    
    # Detailed Compatibility Breakdown
    personality_compatibility = Column(Float, nullable=True)
    values_compatibility = Column(Float, nullable=True)
    interests_compatibility = Column(Float, nullable=True)
    communication_compatibility = Column(Float, nullable=True)
    lifestyle_compatibility = Column(Float, nullable=True)
    
    # Relationship Predictions
    conversation_quality_prediction = Column(Float, nullable=True)
    long_term_potential = Column(Float, nullable=True)
    conflict_likelihood = Column(Float, nullable=True)
    growth_potential = Column(Float, nullable=True)
    
    # Explanation and Insights
    compatibility_reasons = Column(JSON, nullable=True)    # Why they're compatible
    potential_challenges = Column(JSON, nullable=True)     # Potential issues
    conversation_starters = Column(JSON, nullable=True)    # AI-suggested topics
    
    # Model Information
    model_id = Column(Integer, ForeignKey("ml_models.id"), nullable=False)
    prediction_version = Column(String, nullable=False)
    
    # Validation and Feedback
    actual_outcome = Column(String, nullable=True)         # matched, messaged, met, etc.
    user_feedback_score = Column(Float, nullable=True)     # User rating of prediction quality
    prediction_accuracy = Column(Float, nullable=True)     # Calculated accuracy
    
    # Temporal Information
    prediction_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)           # When prediction becomes stale
    last_validated_at = Column(DateTime, nullable=True)
    
    # Relationships
    user_profile = relationship("UserProfile", foreign_keys=[user1_profile_id])
    partner_profile = relationship("UserProfile", foreign_keys=[user2_profile_id])
    model = relationship("MLModel")
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def get_compatibility_insights(self) -> Dict[str, Any]:
        """Get human-readable compatibility insights"""
        return {
            "overall_score": round(self.overall_compatibility * 100, 1),
            "confidence": round(self.confidence_level * 100, 1),
            "strengths": self.compatibility_reasons or [],
            "potential_challenges": self.potential_challenges or [],
            "conversation_starters": self.conversation_starters or [],
            "breakdown": {
                "personality": round((self.personality_compatibility or 0) * 100, 1),
                "values": round((self.values_compatibility or 0) * 100, 1),
                "interests": round((self.interests_compatibility or 0) * 100, 1),
                "communication": round((self.communication_compatibility or 0) * 100, 1),
                "lifestyle": round((self.lifestyle_compatibility or 0) * 100, 1)
            },
            "predictions": {
                "conversation_quality": round((self.conversation_quality_prediction or 0) * 100, 1),
                "long_term_potential": round((self.long_term_potential or 0) * 100, 1),
                "conflict_likelihood": round((self.conflict_likelihood or 0) * 100, 1),
                "growth_potential": round((self.growth_potential or 0) * 100, 1)
            }
        }


class PersonalizedRecommendation(Base):
    """AI-generated personalized recommendations for users"""
    __tablename__ = "personalized_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_profile_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    
    # Recommendation Details
    recommendation_type = Column(String, nullable=False)   # profile_suggestion, conversation_starter, etc.
    recommendation_content = Column(JSON, nullable=False)  # The actual recommendation
    priority_score = Column(Float, default=0.5)           # 0-1 importance
    
    # Personalization Context
    context_data = Column(JSON, nullable=True)            # What triggered this recommendation
    user_segment = Column(String, nullable=True)          # User persona/segment
    timing_relevance = Column(Float, nullable=True)       # Time-sensitive relevance
    
    # AI Model Information
    model_id = Column(Integer, ForeignKey("ml_models.id"), nullable=False)
    generation_algorithm = Column(String, nullable=True)  # Algorithm used
    confidence_score = Column(Float, nullable=False)
    
    # User Interaction Tracking
    shown_to_user = Column(Boolean, default=False)
    shown_at = Column(DateTime, nullable=True)
    user_action = Column(String, nullable=True)           # clicked, dismissed, completed
    user_feedback = Column(String, nullable=True)         # positive, negative, neutral
    effectiveness_score = Column(Float, nullable=True)    # Measured impact
    
    # Lifecycle Management
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    invalidation_reason = Column(String, nullable=True)   # Why recommendation became invalid
    
    # A/B Testing
    experiment_id = Column(String, nullable=True)
    variant = Column(String, nullable=True)               # control, treatment_a, etc.
    
    # Relationships
    user_profile = relationship("UserProfile", back_populates="recommendations")
    model = relationship("MLModel")
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class ModelPrediction(Base):
    """Individual ML model predictions for monitoring and analysis"""
    __tablename__ = "model_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("ml_models.id"), nullable=False)
    
    # Prediction Context
    prediction_type = Column(String, nullable=False)      # compatibility, recommendation, etc.
    input_data_hash = Column(String, nullable=False)      # Hash of input for deduplication
    input_features = Column(JSON, nullable=False)         # Actual input data
    
    # Prediction Results
    prediction_output = Column(JSON, nullable=False)      # Model output
    confidence_score = Column(Float, nullable=True)
    processing_time_ms = Column(Float, nullable=False)
    
    # Quality Metrics
    prediction_quality = Column(String, nullable=True)    # high, medium, low
    uncertainty_estimate = Column(Float, nullable=True)   # Model uncertainty
    feature_importance = Column(JSON, nullable=True)      # Feature contributions
    
    # Validation and Feedback
    ground_truth_value = Column(JSON, nullable=True)      # Actual outcome when available
    prediction_error = Column(Float, nullable=True)       # Calculated error
    user_feedback_score = Column(Float, nullable=True)    # User satisfaction with result
    
    # System Context
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_id = Column(String, nullable=True)
    request_source = Column(String, nullable=True)        # api, batch_job, etc.
    
    # Relationships
    model = relationship("MLModel", back_populates="predictions")
    user = relationship("User")
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class BehavioralPattern(Base):
    """Detected behavioral patterns for users"""
    __tablename__ = "behavioral_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Pattern Information
    pattern_type = Column(String, nullable=False)         # usage, communication, preference
    pattern_name = Column(String, nullable=False)
    pattern_description = Column(Text, nullable=True)
    
    # Pattern Characteristics
    pattern_strength = Column(Float, nullable=False)      # 0-1 how strong the pattern is
    pattern_consistency = Column(Float, nullable=False)   # 0-1 how consistent over time
    pattern_data = Column(JSON, nullable=False)           # Pattern-specific data
    
    # Temporal Information
    first_observed = Column(DateTime, nullable=False)
    last_confirmed = Column(DateTime, nullable=False)
    observation_count = Column(Integer, default=1)
    
    # Pattern Evolution
    trend_direction = Column(String, nullable=True)       # increasing, decreasing, stable
    seasonal_component = Column(JSON, nullable=True)      # Time-based patterns
    
    # AI Detection
    detection_model_id = Column(Integer, ForeignKey("ml_models.id"), nullable=True)
    detection_confidence = Column(Float, nullable=False)
    detection_method = Column(String, nullable=False)     # statistical, ml, rule_based
    
    # Impact and Usage
    business_impact = Column(String, nullable=True)       # high, medium, low
    actionable_insights = Column(JSON, nullable=True)     # What to do with this pattern
    
    # Relationships
    user = relationship("User")
    detection_model = relationship("MLModel")
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)