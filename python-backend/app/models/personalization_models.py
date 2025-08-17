"""
Phase 6: Advanced Personalization & Content Intelligence Models
Dynamic content personalization and intelligent user experience adaptation
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, List, Any, Optional
import enum

from app.core.database import Base


class PersonalizationStrategy(str, enum.Enum):
    """Content personalization strategies"""
    BEHAVIORAL_ANALYSIS = "behavioral_analysis"
    COMPATIBILITY_BASED = "compatibility_based"
    CONVERSATION_FLOW = "conversation_flow"
    EMOTIONAL_STATE = "emotional_state"
    LEARNING_ADAPTATION = "learning_adaptation"


class ContentType(str, enum.Enum):
    """Types of personalized content"""
    CONVERSATION_STARTER = "conversation_starter"
    REVELATION_PROMPT = "revelation_prompt"
    UI_PERSONALIZATION = "ui_personalization"
    SMART_REPLY = "smart_reply"
    ICEBREAKER_QUESTION = "icebreaker_question"
    COMPATIBILITY_INSIGHT = "compatibility_insight"


class UserPersonalizationProfile(Base):
    """
    Advanced user personalization profile for content intelligence
    Tracks preferences, behaviors, and optimization metrics
    """
    __tablename__ = "user_personalization_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Personalization Preferences
    preferred_communication_style = Column(String, default="balanced")  # casual, formal, balanced, playful
    conversation_pace_preference = Column(String, default="moderate")   # slow, moderate, fast, adaptive
    revelation_timing_preference = Column(String, default="gradual")    # immediate, gradual, patient
    content_depth_preference = Column(String, default="medium")         # light, medium, deep, adaptive
    
    # Behavioral Patterns (AI-Generated)
    communication_patterns = Column(JSON, nullable=True)  # Response times, message lengths, etc.
    engagement_patterns = Column(JSON, nullable=True)     # Peak activity times, session lengths
    emotional_expression_patterns = Column(JSON, nullable=True)  # Emoji usage, sentiment patterns
    topic_preferences = Column(JSON, nullable=True)       # Interests, conversation topics
    
    # Learning & Adaptation Metrics
    content_engagement_scores = Column(JSON, nullable=True)  # Success rates for different content types
    personalization_effectiveness = Column(Float, default=0.0)  # Overall personalization success
    adaptation_learning_rate = Column(Float, default=0.1)       # How quickly to adapt to feedback
    
    # UI/UX Preferences
    preferred_ui_complexity = Column(String, default="balanced")  # minimal, balanced, detailed
    animation_preferences = Column(JSON, nullable=True)           # Speed, type preferences
    color_theme_preferences = Column(JSON, nullable=True)        # Theme adjustments
    accessibility_preferences = Column(JSON, nullable=True)      # Accessibility customizations
    
    # Content Optimization History
    successful_content_patterns = Column(JSON, nullable=True)    # What content works best
    failed_content_patterns = Column(JSON, nullable=True)       # What content doesn't work
    optimization_iterations = Column(Integer, default=0)        # Number of optimization cycles
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_optimization_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="personalization_profile")
    generated_content = relationship("PersonalizedContent", back_populates="user_profile")
    feedback_entries = relationship("ContentFeedback", back_populates="user_profile")

    def get_communication_style_vector(self) -> Dict[str, float]:
        """Get user's communication style as a vector for ML processing"""
        patterns = self.communication_patterns or {}
        return {
            "formality": patterns.get("formality_score", 0.5),
            "enthusiasm": patterns.get("enthusiasm_score", 0.5),
            "emotional_openness": patterns.get("emotional_openness", 0.5),
            "conversation_depth": patterns.get("preferred_depth", 0.5),
            "response_speed": patterns.get("typical_response_speed", 0.5)
        }
    
    def update_engagement_metrics(self, content_type: str, engagement_score: float):
        """Update engagement metrics for specific content types"""
        if not self.content_engagement_scores:
            self.content_engagement_scores = {}
        
        current_scores = self.content_engagement_scores.get(content_type, [])
        current_scores.append(engagement_score)
        
        # Keep only the last 50 scores for each content type
        if len(current_scores) > 50:
            current_scores = current_scores[-50:]
        
        self.content_engagement_scores[content_type] = current_scores
        self.updated_at = datetime.utcnow()


class PersonalizedContent(Base):
    """
    AI-generated personalized content for users
    Tracks generation, performance, and optimization
    """
    __tablename__ = "personalized_content"

    id = Column(Integer, primary_key=True, index=True)
    user_profile_id = Column(Integer, ForeignKey("user_personalization_profiles.id"), nullable=False)
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # For user-specific content
    
    # Content Details
    content_type = Column(String, nullable=False)  # ContentType enum
    content_text = Column(Text, nullable=False)
    content_metadata = Column(JSON, nullable=True)  # Additional content data
    
    # Generation Details
    generation_strategy = Column(String, nullable=False)  # PersonalizationStrategy enum
    generation_context = Column(JSON, nullable=True)      # Context used for generation
    ai_confidence_score = Column(Float, default=0.0)      # AI's confidence in this content
    
    # Performance Metrics
    presentation_count = Column(Integer, default=0)       # How many times shown
    engagement_count = Column(Integer, default=0)         # How many times used/clicked
    success_count = Column(Integer, default=0)            # How many times led to positive outcome
    feedback_score = Column(Float, nullable=True)         # User feedback (1-5 scale)
    
    # Optimization Data
    a_b_test_variant = Column(String, nullable=True)      # A/B test variant identifier
    optimization_version = Column(Integer, default=1)     # Version for optimization tracking
    is_baseline = Column(Boolean, default=False)          # Whether this is a baseline version
    
    # Metadata
    generated_at = Column(DateTime, default=datetime.utcnow)
    first_used_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user_profile = relationship("UserPersonalizationProfile", back_populates="generated_content")
    target_user = relationship("User", foreign_keys=[target_user_id])
    feedback_entries = relationship("ContentFeedback", back_populates="content")

    def calculate_effectiveness_score(self) -> float:
        """Calculate content effectiveness based on engagement metrics"""
        if self.presentation_count == 0:
            return 0.0
        
        engagement_rate = self.engagement_count / self.presentation_count
        success_rate = self.success_count / max(self.engagement_count, 1)
        feedback_score = self.feedback_score or 0.0
        
        # Weighted effectiveness score
        effectiveness = (
            engagement_rate * 0.4 +
            success_rate * 0.4 +
            (feedback_score / 5.0) * 0.2
        )
        
        return min(effectiveness, 1.0)

    def should_retire_content(self) -> bool:
        """Determine if content should be retired based on performance"""
        if self.presentation_count < 10:  # Need minimum data
            return False
        
        effectiveness = self.calculate_effectiveness_score()
        return effectiveness < 0.2  # Retire if less than 20% effective


class ContentFeedback(Base):
    """
    User feedback on personalized content for optimization
    """
    __tablename__ = "content_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_profile_id = Column(Integer, ForeignKey("user_personalization_profiles.id"), nullable=False)
    content_id = Column(Integer, ForeignKey("personalized_content.id"), nullable=False)
    
    # Feedback Details
    feedback_type = Column(String, nullable=False)  # explicit, implicit, behavioral
    feedback_score = Column(Float, nullable=True)   # 1-5 rating if explicit
    feedback_text = Column(Text, nullable=True)     # Optional text feedback
    
    # Behavioral Feedback
    interaction_duration = Column(Float, nullable=True)  # Time spent with content
    follow_up_actions = Column(JSON, nullable=True)      # Actions taken after seeing content
    context_data = Column(JSON, nullable=True)           # Context when feedback was given
    
    # Metadata
    feedback_given_at = Column(DateTime, default=datetime.utcnow)
    session_id = Column(String, nullable=True)           # Session identifier
    device_type = Column(String, nullable=True)          # Mobile, desktop, etc.
    
    # Relationships
    user_profile = relationship("UserPersonalizationProfile", back_populates="feedback_entries")
    content = relationship("PersonalizedContent", back_populates="feedback_entries")


class AlgorithmOptimization(Base):
    """
    Track real-time algorithm optimization and A/B testing
    """
    __tablename__ = "algorithm_optimizations"

    id = Column(Integer, primary_key=True, index=True)
    
    # Optimization Details
    optimization_type = Column(String, nullable=False)   # matching, content_generation, ui_adaptation
    algorithm_version = Column(String, nullable=False)   # Version identifier
    optimization_strategy = Column(String, nullable=False)  # PersonalizationStrategy enum
    
    # Configuration
    parameters = Column(JSON, nullable=False)            # Algorithm parameters
    target_metrics = Column(JSON, nullable=False)        # Metrics to optimize for
    constraints = Column(JSON, nullable=True)            # Optimization constraints
    
    # Performance Data
    baseline_metrics = Column(JSON, nullable=True)       # Baseline performance
    current_metrics = Column(JSON, nullable=True)        # Current performance
    improvement_percentage = Column(Float, default=0.0)  # Performance improvement
    
    # A/B Testing
    test_population_size = Column(Integer, nullable=True)  # Number of users in test
    control_group_size = Column(Integer, nullable=True)    # Control group size
    statistical_significance = Column(Float, nullable=True)  # P-value
    
    # Status
    is_active = Column(Boolean, default=True)
    is_deployed = Column(Boolean, default=False)
    deployment_percentage = Column(Float, default=0.0)   # Gradual rollout percentage
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deployed_at = Column(DateTime, nullable=True)
    retired_at = Column(DateTime, nullable=True)

    def calculate_statistical_significance(self) -> float:
        """Calculate statistical significance of optimization results"""
        # Placeholder for statistical analysis
        # In production, would implement proper statistical testing
        if not self.current_metrics or not self.baseline_metrics:
            return 0.0
        
        # Simplified significance calculation
        improvement = self.improvement_percentage
        sample_size = self.test_population_size or 0
        
        if sample_size < 100 or abs(improvement) < 0.05:
            return 0.0
        
        # Simplified p-value estimation
        significance = min(abs(improvement) * (sample_size / 1000), 0.05)
        return significance


class ConversationFlowAnalytics(Base):
    """
    Track conversation flow patterns for optimization
    """
    __tablename__ = "conversation_flow_analytics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    connection_id = Column(Integer, ForeignKey("soul_connections.id"), nullable=True)
    
    # Flow Analysis
    conversation_stage = Column(String, nullable=False)  # initial, developing, deep, declining
    message_count = Column(Integer, default=0)
    average_response_time = Column(Float, nullable=True)  # In seconds
    sentiment_trend = Column(JSON, nullable=True)        # Sentiment over time
    
    # Content Performance
    successful_starters = Column(JSON, nullable=True)    # What worked well
    failed_starters = Column(JSON, nullable=True)        # What didn't work
    optimal_timing_patterns = Column(JSON, nullable=True)  # Best times for different content
    
    # Engagement Metrics
    engagement_score = Column(Float, default=0.0)        # Overall conversation engagement
    depth_progression = Column(JSON, nullable=True)      # How conversation deepened over time
    emotional_connection_score = Column(Float, default=0.0)  # Emotional bonding metric
    
    # Metadata
    analysis_date = Column(DateTime, default=datetime.utcnow)
    conversation_start_date = Column(DateTime, nullable=True)
    conversation_end_date = Column(DateTime, nullable=True)
    
    # Relationships  
    user = relationship("User")
    connection = relationship("SoulConnection", foreign_keys=[connection_id])