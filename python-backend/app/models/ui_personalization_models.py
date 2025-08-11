"""
Phase 6: User Behavior-Based UI Personalization Models
Dynamic UI adaptation based on user interaction patterns and preferences
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, List, Any, Optional
import enum

from app.core.database import Base


class UIInteractionType(str, enum.Enum):
    """Types of UI interactions to track"""
    CLICK = "click"
    SCROLL = "scroll"
    HOVER = "hover"
    SWIPE = "swipe"
    KEYBOARD = "keyboard"
    FORM_INTERACTION = "form_interaction"
    NAVIGATION = "navigation"
    GESTURE = "gesture"
    VOICE_COMMAND = "voice_command"


class UIPersonalizationStrategy(str, enum.Enum):
    """UI personalization strategies"""
    BEHAVIORAL_ADAPTATION = "behavioral_adaptation"
    ACCESSIBILITY_OPTIMIZATION = "accessibility_optimization"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    AESTHETIC_PREFERENCE = "aesthetic_preference"
    COGNITIVE_LOAD_REDUCTION = "cognitive_load_reduction"


class DeviceType(str, enum.Enum):
    """Device types for responsive personalization"""
    MOBILE = "mobile"
    TABLET = "tablet"
    DESKTOP = "desktop"
    SMART_TV = "smart_tv"
    WEARABLE = "wearable"


class UserUIProfile(Base):
    """
    Comprehensive user UI behavior and personalization profile
    """
    __tablename__ = "user_ui_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Device and Platform Preferences
    primary_device_type = Column(String, default=DeviceType.MOBILE.value)
    screen_resolution = Column(String, nullable=True)  # e.g., "1920x1080"
    preferred_orientation = Column(String, default="portrait")  # portrait, landscape, auto
    
    # Visual Preferences
    preferred_theme = Column(String, default="auto")  # light, dark, auto
    color_contrast_preference = Column(String, default="standard")  # low, standard, high
    font_size_preference = Column(String, default="medium")  # small, medium, large, extra-large
    animation_preference = Column(String, default="standard")  # none, reduced, standard, enhanced
    
    # Layout Preferences
    layout_density = Column(String, default="comfortable")  # compact, comfortable, spacious
    sidebar_preference = Column(String, default="auto")  # always, auto, never
    bottom_navigation_enabled = Column(Boolean, default=True)
    floating_action_button_position = Column(String, default="bottom-right")
    
    # Interaction Patterns
    primary_interaction_method = Column(String, default="touch")  # touch, mouse, keyboard, voice
    swipe_sensitivity = Column(Float, default=1.0)  # 0.5 = low, 1.0 = normal, 1.5 = high
    tap_sensitivity = Column(Float, default=1.0)
    double_tap_enabled = Column(Boolean, default=True)
    haptic_feedback_intensity = Column(Float, default=0.7)
    
    # Accessibility Settings
    screen_reader_enabled = Column(Boolean, default=False)
    keyboard_navigation_primary = Column(Boolean, default=False)
    high_contrast_enabled = Column(Boolean, default=False)
    reduce_motion_enabled = Column(Boolean, default=False)
    voice_control_enabled = Column(Boolean, default=False)
    
    # Behavioral Analytics
    average_session_duration = Column(Float, nullable=True)  # minutes
    typical_usage_hours = Column(JSON, nullable=True)  # [19, 20, 21, 22]
    interaction_speed = Column(String, default="medium")  # slow, medium, fast
    navigation_pattern = Column(String, default="explorer")  # linear, explorer, focused, random
    
    # Performance Preferences
    data_saver_enabled = Column(Boolean, default=False)
    preload_content = Column(Boolean, default=True)
    offline_mode_preference = Column(Boolean, default=False)
    background_sync_enabled = Column(Boolean, default=True)
    
    # Personalization Metrics
    personalization_score = Column(Float, default=0.0)  # How well UI is personalized
    adaptation_learning_rate = Column(Float, default=0.1)  # How quickly to adapt
    last_personalization_update = Column(DateTime, nullable=True)
    total_interactions_tracked = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="ui_profile")
    interaction_logs = relationship("UIInteractionLog", back_populates="ui_profile")
    personalization_events = relationship("UIPersonalizationEvent", back_populates="ui_profile")
    a_b_test_participations = relationship("UIABTestParticipation", back_populates="ui_profile")

    def get_current_preferences(self) -> Dict[str, Any]:
        """Get current UI preferences as a dictionary"""
        return {
            "theme": self.preferred_theme,
            "font_size": self.font_size_preference,
            "layout_density": self.layout_density,
            "animation_level": self.animation_preference,
            "contrast": self.color_contrast_preference,
            "haptic_intensity": self.haptic_feedback_intensity,
            "navigation_style": self.navigation_pattern
        }

    def update_personalization_score(self, new_interactions: int, satisfaction_score: float):
        """Update personalization effectiveness score"""
        if self.total_interactions_tracked == 0:
            self.personalization_score = satisfaction_score
        else:
            # Weighted average with more weight on recent interactions
            weight = min(new_interactions / 100.0, 0.3)  # Max 30% weight for new data
            self.personalization_score = (
                self.personalization_score * (1 - weight) + 
                satisfaction_score * weight
            )
        
        self.total_interactions_tracked += new_interactions
        self.last_personalization_update = datetime.utcnow()


class UIInteractionLog(Base):
    """
    Log of user interactions for behavioral analysis
    """
    __tablename__ = "ui_interaction_logs"

    id = Column(Integer, primary_key=True, index=True)
    ui_profile_id = Column(Integer, ForeignKey("user_ui_profiles.id"), nullable=False)
    
    # Interaction Details
    interaction_type = Column(String, nullable=False)  # UIInteractionType
    element_type = Column(String, nullable=True)  # button, input, link, card, etc.
    element_id = Column(String, nullable=True)  # Specific element identifier
    page_route = Column(String, nullable=True)  # /chat, /discover, /profile, etc.
    
    # Interaction Context
    device_type = Column(String, nullable=True)
    screen_size = Column(String, nullable=True)  # e.g., "375x667"
    viewport_size = Column(String, nullable=True)
    scroll_position = Column(Integer, nullable=True)
    
    # Timing Information
    interaction_timestamp = Column(DateTime, default=datetime.utcnow)
    session_id = Column(String, nullable=True)
    time_since_last_interaction = Column(Float, nullable=True)  # seconds
    interaction_duration = Column(Float, nullable=True)  # seconds (for hover, scroll, etc.)
    
    # Interaction Metrics
    click_coordinates = Column(JSON, nullable=True)  # {x: 100, y: 200}
    scroll_distance = Column(Integer, nullable=True)  # pixels
    swipe_direction = Column(String, nullable=True)  # up, down, left, right
    gesture_data = Column(JSON, nullable=True)  # Complex gesture information
    
    # Context Data
    user_emotional_state = Column(String, nullable=True)  # From emotional state service
    connection_context = Column(JSON, nullable=True)  # Current connection info
    feature_flags = Column(JSON, nullable=True)  # Active feature flags during interaction
    
    # Performance Metrics
    render_time = Column(Float, nullable=True)  # milliseconds
    response_time = Column(Float, nullable=True)  # milliseconds
    error_occurred = Column(Boolean, default=False)
    error_details = Column(Text, nullable=True)
    
    # Relationships
    ui_profile = relationship("UserUIProfile", back_populates="interaction_logs")

    def calculate_interaction_efficiency(self) -> float:
        """Calculate efficiency score for this interaction"""
        base_score = 1.0
        
        # Penalize for errors
        if self.error_occurred:
            base_score -= 0.3
        
        # Penalize for slow response times
        if self.response_time and self.response_time > 1000:  # > 1 second
            base_score -= min(0.2, (self.response_time - 1000) / 5000)
        
        # Reward for quick, decisive interactions
        if self.interaction_duration and self.interaction_duration < 0.5:
            base_score += 0.1
        
        return max(0.0, min(1.0, base_score))


class UIPersonalizationEvent(Base):
    """
    Track UI personalization changes and their effectiveness
    """
    __tablename__ = "ui_personalization_events"

    id = Column(Integer, primary_key=True, index=True)
    ui_profile_id = Column(Integer, ForeignKey("user_ui_profiles.id"), nullable=False)
    
    # Personalization Details
    personalization_type = Column(String, nullable=False)  # theme_change, layout_adjustment, etc.
    strategy_used = Column(String, nullable=False)  # UIPersonalizationStrategy
    
    # Changes Made
    previous_settings = Column(JSON, nullable=True)  # Settings before change
    new_settings = Column(JSON, nullable=False)  # Settings after change
    change_reason = Column(String, nullable=True)  # behavioral_pattern, user_request, etc.
    
    # Effectiveness Tracking
    applied_at = Column(DateTime, default=datetime.utcnow)
    effectiveness_measured = Column(Boolean, default=False)
    user_satisfaction_score = Column(Float, nullable=True)  # 0.0 to 1.0
    interaction_improvement = Column(Float, nullable=True)  # % improvement in interaction metrics
    
    # Context
    trigger_event = Column(String, nullable=True)  # What triggered this personalization
    device_context = Column(JSON, nullable=True)  # Device info when change was made
    session_context = Column(JSON, nullable=True)  # Session info
    
    # A/B Testing
    is_ab_test = Column(Boolean, default=False)
    ab_test_variant = Column(String, nullable=True)
    control_group = Column(Boolean, default=False)
    
    # Rollback Information
    was_rolled_back = Column(Boolean, default=False)
    rollback_reason = Column(String, nullable=True)
    rollback_timestamp = Column(DateTime, nullable=True)
    
    # Relationships
    ui_profile = relationship("UserUIProfile", back_populates="personalization_events")

    def measure_effectiveness(self, satisfaction: float, interaction_improvement: float):
        """Record effectiveness metrics for this personalization"""
        self.user_satisfaction_score = satisfaction
        self.interaction_improvement = interaction_improvement
        self.effectiveness_measured = True


class UIABTestParticipation(Base):
    """
    Track user participation in UI A/B tests
    """
    __tablename__ = "ui_ab_test_participations"

    id = Column(Integer, primary_key=True, index=True)
    ui_profile_id = Column(Integer, ForeignKey("user_ui_profiles.id"), nullable=False)
    
    # Test Information
    test_name = Column(String, nullable=False)
    test_variant = Column(String, nullable=False)  # A, B, C, etc.
    test_category = Column(String, nullable=True)  # layout, theme, interaction, etc.
    
    # Participation Details
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Test Results
    primary_metric_value = Column(Float, nullable=True)  # Main metric being tested
    secondary_metrics = Column(JSON, nullable=True)  # Additional metrics
    user_feedback = Column(Text, nullable=True)  # Qualitative feedback
    
    # Conversion Tracking
    conversion_achieved = Column(Boolean, default=False)
    conversion_type = Column(String, nullable=True)  # registration, match, message, etc.
    time_to_conversion = Column(Float, nullable=True)  # minutes
    
    # Statistical Data
    session_count = Column(Integer, default=0)
    total_interaction_time = Column(Float, default=0.0)  # minutes
    bounce_rate = Column(Float, nullable=True)
    
    # Relationships
    ui_profile = relationship("UserUIProfile", back_populates="a_b_test_participations")


class UIAdaptiveComponent(Base):
    """
    Track adaptive UI components and their performance
    """
    __tablename__ = "ui_adaptive_components"

    id = Column(Integer, primary_key=True, index=True)
    
    # Component Information
    component_name = Column(String, nullable=False)  # revelation-card, chat-input, etc.
    component_type = Column(String, nullable=False)  # card, form, navigation, etc.
    page_route = Column(String, nullable=False)  # Where the component appears
    
    # Adaptation Rules
    adaptation_triggers = Column(JSON, nullable=False)  # Conditions that trigger adaptation
    adaptation_options = Column(JSON, nullable=False)  # Available adaptations
    default_configuration = Column(JSON, nullable=False)  # Default component settings
    
    # Performance Metrics
    total_adaptations = Column(Integer, default=0)
    successful_adaptations = Column(Integer, default=0)
    average_effectiveness = Column(Float, default=0.0)
    
    # Configuration
    is_active = Column(Boolean, default=True)
    adaptation_frequency = Column(String, default="real_time")  # real_time, session, daily
    learning_enabled = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def calculate_success_rate(self) -> float:
        """Calculate adaptation success rate"""
        if self.total_adaptations == 0:
            return 0.0
        return self.successful_adaptations / self.total_adaptations


class UIPersonalizationInsight(Base):
    """
    AI-generated insights about user UI preferences and behaviors
    """
    __tablename__ = "ui_personalization_insights"

    id = Column(Integer, primary_key=True, index=True)
    ui_profile_id = Column(Integer, ForeignKey("user_ui_profiles.id"), nullable=False)
    
    # Insight Details
    insight_type = Column(String, nullable=False)  # pattern, preference, anomaly, opportunity
    insight_category = Column(String, nullable=False)  # usability, accessibility, performance
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    
    # Recommendations
    recommended_action = Column(String, nullable=True)
    implementation_priority = Column(String, default="medium")  # low, medium, high, critical
    expected_impact = Column(Float, nullable=True)  # Expected improvement (0.0 to 1.0)
    
    # Supporting Data
    supporting_data = Column(JSON, nullable=True)  # Data that led to this insight
    confidence_score = Column(Float, nullable=False)  # AI confidence in insight
    
    # Lifecycle
    generated_at = Column(DateTime, default=datetime.utcnow)
    acted_upon = Column(Boolean, default=False)
    action_taken = Column(String, nullable=True)
    result_measured = Column(Boolean, default=False)
    actual_impact = Column(Float, nullable=True)
    
    # Relationships
    ui_profile = relationship("UserUIProfile")

    def mark_as_implemented(self, action_description: str):
        """Mark insight as implemented"""
        self.acted_upon = True
        self.action_taken = action_description

    def record_impact(self, measured_impact: float):
        """Record the actual impact after implementation"""
        self.actual_impact = measured_impact
        self.result_measured = True