"""
Phase 8B: Advanced UI/UX & Mobile Experience Models
Database models for sophisticated UI personalization and mobile optimization
"""
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, DECIMAL, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class AnimationType(str, enum.Enum):
    """Types of UI animations"""
    FADE_IN_UP = "fade_in_up"
    PULSE_GLOW = "pulse_glow"
    SLIDE_FADE = "slide_fade"
    BOUNCE_SCALE = "bounce_scale"
    ROTATE_3D = "rotate_3d"
    MORPHING = "morphing"
    PARTICLE_EFFECT = "particle_effect"
    SOUL_REVEAL = "soul_reveal"


class GestureType(str, enum.Enum):
    """Types of mobile gestures"""
    HORIZONTAL_SWIPE = "horizontal_swipe"
    VERTICAL_SWIPE = "vertical_swipe"
    LONG_PRESS = "long_press"
    MULTI_TAP = "multi_tap"
    CIRCULAR_GESTURE = "circular_gesture"
    PINCH_ZOOM = "pinch_zoom"
    DRAG_DROP = "drag_drop"
    SHAKE = "shake"


class AccessibilityFeature(str, enum.Enum):
    """Types of accessibility features"""
    HIGH_CONTRAST = "high_contrast"
    LARGE_TEXT = "large_text"
    REDUCED_MOTION = "reduced_motion"
    SCREEN_READER = "screen_reader"
    KEYBOARD_NAVIGATION = "keyboard_navigation"
    VOICE_CONTROL = "voice_control"
    MOTOR_ASSISTANCE = "motor_assistance"
    COLOR_BLIND_SUPPORT = "color_blind_support"


class ComponentType(str, enum.Enum):
    """Types of UI components"""
    SOUL_CARD = "soul_card"
    REVELATION_INPUT = "revelation_input"
    CONNECTION_BUTTON = "connection_button"
    CHAT_INTERFACE = "chat_interface"
    NAVIGATION_BAR = "navigation_bar"
    PROFILE_HEADER = "profile_header"
    ANIMATION_CONTAINER = "animation_container"
    GESTURE_AREA = "gesture_area"


class UIExperienceProfile(Base):
    """User interface experience personalization profile"""
    __tablename__ = "ui_experience_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Device and display preferences
    primary_device_type = Column(String, nullable=False)  # mobile, tablet, desktop
    screen_size_category = Column(String, nullable=False)  # small, medium, large
    preferred_orientation = Column(String, default="portrait")
    pixel_density_optimization = Column(String, default="standard")  # standard, high, ultra
    
    # Personalization level and preferences
    personalization_level = Column(String, default="medium")  # low, medium, high, custom
    emotional_design_preference = Column(String, default="balanced")  # warm, cool, balanced, vibrant
    animation_preference = Column(String, default="standard")  # minimal, standard, enhanced, dynamic
    
    # Interaction preferences
    gesture_sensitivity = Column(Float, default=0.5)  # 0.0 to 1.0
    haptic_feedback_enabled = Column(Boolean, default=True)
    voice_interaction_enabled = Column(Boolean, default=False)
    motion_controls_enabled = Column(Boolean, default=False)
    
    # Accessibility requirements
    accessibility_needs = Column(JSON, nullable=True)
    color_blind_type = Column(String, nullable=True)
    motor_limitations = Column(JSON, nullable=True)
    cognitive_preferences = Column(JSON, nullable=True)
    
    # UI customizations
    ui_preferences = Column(JSON, nullable=True)
    custom_theme_config = Column(JSON, nullable=True)
    layout_preferences = Column(JSON, nullable=True)
    
    # Performance preferences
    performance_priority = Column(String, default="balanced")  # performance, visual_quality, balanced
    battery_optimization = Column(Boolean, default=True)
    data_usage_optimization = Column(Boolean, default=False)
    
    # Experience metrics
    satisfaction_score = Column(Float, nullable=True)
    usability_score = Column(Float, nullable=True)
    engagement_score = Column(Float, nullable=True)
    
    # Learning and adaptation
    interaction_patterns = Column(JSON, nullable=True)
    preference_evolution = Column(JSON, nullable=True)
    adaptation_confidence = Column(Float, default=0.5)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    animations = relationship("InteractionAnimation", back_populates="ui_profile")
    gestures = relationship("MobileGesture", back_populates="ui_profile")
    accessibility_profile = relationship("AccessibilityProfile", back_populates="ui_profile", uselist=False)


class InteractionAnimation(Base):
    """Advanced animations and transitions for UI interactions"""
    __tablename__ = "interaction_animations"

    id = Column(Integer, primary_key=True, index=True)
    ui_profile_id = Column(Integer, ForeignKey("ui_experience_profiles.id"), nullable=False)
    
    # Animation configuration
    animation_type = Column(String, nullable=False)  # AnimationType enum
    animation_name = Column(String, nullable=False)
    animation_config = Column(JSON, nullable=False)
    
    # Trigger and context
    trigger_event = Column(String, nullable=False)  # swipe, tap, reveal, etc.
    context_data = Column(JSON, nullable=True)
    emotional_context = Column(String, nullable=True)
    
    # Animation properties
    duration_ms = Column(Integer, nullable=False)
    delay_ms = Column(Integer, default=0)
    easing_function = Column(String, default="ease-out")
    loop_count = Column(Integer, default=1)
    
    # Sequence and choreography
    sequence_data = Column(JSON, nullable=True)
    choreography_rules = Column(JSON, nullable=True)
    parallel_animations = Column(JSON, nullable=True)
    
    # Performance and optimization
    estimated_duration_ms = Column(Integer, nullable=True)
    gpu_acceleration = Column(Boolean, default=True)
    performance_budget = Column(Float, nullable=True)
    fallback_animation = Column(JSON, nullable=True)
    
    # User feedback and effectiveness
    user_rating = Column(Float, nullable=True)
    completion_rate = Column(Float, nullable=True)
    emotional_resonance_score = Column(Float, nullable=True)
    
    # Accessibility compliance
    accessibility_compliant = Column(Boolean, default=True)
    reduced_motion_alternative = Column(JSON, nullable=True)
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ui_profile = relationship("UIExperienceProfile", back_populates="animations")


class MobileGesture(Base):
    """Mobile gesture recognition and customization"""
    __tablename__ = "mobile_gestures"

    id = Column(Integer, primary_key=True, index=True)
    ui_profile_id = Column(Integer, ForeignKey("ui_experience_profiles.id"), nullable=False)
    
    # Gesture identification
    gesture_type = Column(String, nullable=False)  # GestureType enum
    gesture_name = Column(String, nullable=False)
    gesture_description = Column(Text, nullable=True)
    
    # Gesture configuration
    gesture_config = Column(JSON, nullable=False)
    sensitivity_level = Column(Float, default=0.5)  # 0.0 to 1.0
    threshold_values = Column(JSON, nullable=True)
    
    # Gesture recognition
    recognition_algorithm = Column(String, default="basic")
    custom_recognition_data = Column(JSON, nullable=True)
    machine_learning_model = Column(String, nullable=True)
    
    # Feedback and response
    haptic_feedback_enabled = Column(Boolean, default=True)
    haptic_pattern = Column(JSON, nullable=True)
    audio_feedback_enabled = Column(Boolean, default=False)
    visual_feedback_config = Column(JSON, nullable=True)
    
    # Action mapping
    primary_action = Column(String, nullable=False)
    secondary_actions = Column(JSON, nullable=True)
    context_dependent_actions = Column(JSON, nullable=True)
    
    # Performance and accuracy
    success_rate = Column(Float, nullable=True)
    false_positive_rate = Column(Float, nullable=True)
    response_time_ms = Column(Float, nullable=True)
    
    # User adaptation
    learning_enabled = Column(Boolean, default=True)
    user_corrections = Column(JSON, nullable=True)
    adaptation_data = Column(JSON, nullable=True)
    
    # Accessibility alternatives
    accessibility_alternatives = Column(JSON, nullable=True)
    voice_command_alternative = Column(String, nullable=True)
    keyboard_shortcut_alternative = Column(String, nullable=True)
    
    # Usage metrics
    usage_frequency = Column(Float, nullable=True)
    last_used = Column(DateTime, nullable=True)
    user_satisfaction = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ui_profile = relationship("UIExperienceProfile", back_populates="gestures")


class UIPersonalizationSettings(Base):
    """Detailed UI personalization settings and configurations"""
    __tablename__ = "ui_personalization_settings"

    id = Column(Integer, primary_key=True, index=True)
    ui_profile_id = Column(Integer, ForeignKey("ui_experience_profiles.id"), nullable=False)
    
    # Theme and visual preferences
    theme_mode = Column(String, default="auto")  # light, dark, auto, custom
    primary_color = Column(String, nullable=True)
    accent_color = Column(String, nullable=True)
    background_preference = Column(String, default="solid")  # solid, gradient, image
    
    # Typography preferences
    font_family = Column(String, default="system")
    font_size_scale = Column(Float, default=1.0)
    line_height_preference = Column(Float, default=1.5)
    text_weight_preference = Column(String, default="normal")
    
    # Layout and spacing
    content_density = Column(String, default="comfortable")  # compact, comfortable, spacious
    navigation_style = Column(String, default="bottom")  # top, bottom, side, floating
    card_layout_preference = Column(String, default="standard")
    
    # Interaction preferences
    button_style = Column(String, default="rounded")  # rounded, square, circular
    transition_speed = Column(String, default="normal")  # slow, normal, fast
    feedback_intensity = Column(String, default="medium")  # subtle, medium, strong
    
    # Content preferences
    image_loading_strategy = Column(String, default="progressive")
    auto_play_media = Column(Boolean, default=False)
    content_preview_enabled = Column(Boolean, default=True)
    
    # Privacy and data preferences
    analytics_sharing = Column(Boolean, default=True)
    personalization_data_sharing = Column(Boolean, default=True)
    cross_device_sync = Column(Boolean, default=True)
    
    # Advanced configurations
    custom_css = Column(Text, nullable=True)
    advanced_config = Column(JSON, nullable=True)
    experimental_features = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AccessibilityProfile(Base):
    """Comprehensive accessibility profile and accommodations"""
    __tablename__ = "accessibility_profiles"

    id = Column(Integer, primary_key=True, index=True)
    ui_profile_id = Column(Integer, ForeignKey("ui_experience_profiles.id"), nullable=False, unique=True)
    
    # Visual accessibility
    visual_impairment_type = Column(String, nullable=True)  # none, low_vision, blind, color_blind
    contrast_requirement = Column(String, default="normal")  # normal, high, ultra_high
    text_size_multiplier = Column(Float, default=1.0)
    color_blind_type = Column(String, nullable=True)  # protanopia, deuteranopia, tritanopia
    
    # Motor accessibility
    motor_limitation_type = Column(String, nullable=True)  # none, fine_motor, gross_motor, tremor
    touch_target_size_multiplier = Column(Float, default=1.0)
    gesture_alternatives_needed = Column(Boolean, default=False)
    dwell_time_preference = Column(Float, nullable=True)
    
    # Cognitive accessibility
    cognitive_load_preference = Column(String, default="standard")  # minimal, standard, enhanced
    information_density_preference = Column(String, default="medium")  # low, medium, high
    navigation_complexity_preference = Column(String, default="simple")
    
    # Auditory accessibility
    hearing_impairment_type = Column(String, nullable=True)  # none, partial, deaf
    audio_description_needed = Column(Boolean, default=False)
    visual_audio_indicators = Column(Boolean, default=False)
    
    # Assistive technology
    screen_reader_used = Column(Boolean, default=False)
    screen_reader_type = Column(String, nullable=True)
    voice_control_used = Column(Boolean, default=False)
    switch_control_used = Column(Boolean, default=False)
    
    # Accessibility features enabled
    enabled_features = Column(JSON, nullable=True)
    custom_accommodations = Column(JSON, nullable=True)
    
    # WCAG compliance level
    required_compliance_level = Column(String, default="AA")  # A, AA, AAA
    compliance_verified = Column(Boolean, default=False)
    last_compliance_check = Column(DateTime, nullable=True)
    
    # User feedback and effectiveness
    accommodation_effectiveness = Column(JSON, nullable=True)
    user_reported_barriers = Column(JSON, nullable=True)
    suggested_improvements = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ui_profile = relationship("UIExperienceProfile", back_populates="accessibility_profile")


class DesignSystem(Base):
    """Personalized design system configuration"""
    __tablename__ = "design_systems"

    id = Column(Integer, primary_key=True, index=True)
    ui_profile_id = Column(Integer, ForeignKey("ui_experience_profiles.id"), nullable=False)
    
    # Design system metadata
    design_version = Column(String, nullable=False)
    design_name = Column(String, nullable=True)
    design_description = Column(Text, nullable=True)
    
    # Color system
    color_palette = Column(JSON, nullable=False)
    color_accessibility_ratings = Column(JSON, nullable=True)
    semantic_colors = Column(JSON, nullable=True)
    
    # Typography system
    typography_config = Column(JSON, nullable=False)
    font_loading_strategy = Column(String, default="swap")
    font_display_optimization = Column(Boolean, default=True)
    
    # Spacing and layout system
    spacing_config = Column(JSON, nullable=False)
    grid_system = Column(JSON, nullable=True)
    breakpoint_config = Column(JSON, nullable=True)
    
    # Component configurations
    component_config = Column(JSON, nullable=False)
    component_variants = Column(JSON, nullable=True)
    component_states = Column(JSON, nullable=True)
    
    # Interaction design
    interaction_config = Column(JSON, nullable=False)
    micro_interaction_library = Column(JSON, nullable=True)
    gesture_mappings = Column(JSON, nullable=True)
    
    # Accessibility design tokens
    accessibility_tokens = Column(JSON, nullable=True)
    high_contrast_alternatives = Column(JSON, nullable=True)
    reduced_motion_alternatives = Column(JSON, nullable=True)
    
    # Performance considerations
    performance_budget = Column(JSON, nullable=True)
    asset_optimization = Column(JSON, nullable=True)
    loading_strategies = Column(JSON, nullable=True)
    
    # Version control and evolution
    previous_version = Column(String, nullable=True)
    change_log = Column(JSON, nullable=True)
    a_b_test_variants = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UIComponentOptimization(Base):
    """Individual UI component optimization tracking"""
    __tablename__ = "ui_component_optimizations"

    id = Column(Integer, primary_key=True, index=True)
    
    # Component identification
    component_type = Column(String, nullable=False)  # ComponentType enum
    component_name = Column(String, nullable=False)
    component_version = Column(String, default="1.0")
    
    # Optimization configuration
    optimization_type = Column(String, nullable=False)  # performance, accessibility, ux
    optimization_config = Column(JSON, nullable=False)
    implementation_complexity = Column(String, default="medium")  # low, medium, high, critical
    
    # Performance metrics
    performance_metrics = Column(JSON, nullable=True)
    load_time_ms = Column(Float, nullable=True)
    render_time_ms = Column(Float, nullable=True)
    memory_usage_kb = Column(Float, nullable=True)
    
    # User experience metrics
    user_experience_score = Column(Float, nullable=True)
    interaction_success_rate = Column(Float, nullable=True)
    user_satisfaction_score = Column(Float, nullable=True)
    accessibility_score = Column(Float, nullable=True)
    
    # Optimization results
    before_metrics = Column(JSON, nullable=True)
    after_metrics = Column(JSON, nullable=True)
    expected_improvement_percent = Column(Float, nullable=True)
    actual_improvement_percent = Column(Float, nullable=True)
    
    # Implementation tracking
    implementation_status = Column(String, default="planned")  # planned, in_progress, completed, rolled_back
    implemented_at = Column(DateTime, nullable=True)
    rollback_reason = Column(Text, nullable=True)
    
    # A/B testing results
    a_b_test_results = Column(JSON, nullable=True)
    statistical_significance = Column(Float, nullable=True)
    winner_variant = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserJourney(Base):
    """User journey optimization and flow analysis"""
    __tablename__ = "user_journeys"

    id = Column(Integer, primary_key=True, index=True)
    ui_profile_id = Column(Integer, ForeignKey("ui_experience_profiles.id"), nullable=False)
    
    # Journey identification
    journey_name = Column(String, nullable=False)
    journey_type = Column(String, nullable=False)  # onboarding, matching, messaging, etc.
    journey_description = Column(Text, nullable=True)
    
    # Journey flow
    journey_steps = Column(JSON, nullable=False)
    step_completion_rates = Column(JSON, nullable=True)
    drop_off_points = Column(JSON, nullable=True)
    
    # Performance metrics
    total_completion_rate = Column(Float, nullable=True)
    average_completion_time_minutes = Column(Float, nullable=True)
    user_satisfaction_by_step = Column(JSON, nullable=True)
    
    # Optimization opportunities
    identified_friction_points = Column(JSON, nullable=True)
    optimization_recommendations = Column(JSON, nullable=True)
    a_b_test_variations = Column(JSON, nullable=True)
    
    # Personalization factors
    user_segment_performance = Column(JSON, nullable=True)
    device_specific_performance = Column(JSON, nullable=True)
    accessibility_considerations = Column(JSON, nullable=True)
    
    # Journey evolution
    version = Column(String, default="1.0")
    previous_versions = Column(JSON, nullable=True)
    improvement_history = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MobileOptimization(Base):
    """Mobile-specific optimizations and configurations"""
    __tablename__ = "mobile_optimizations"

    id = Column(Integer, primary_key=True, index=True)
    ui_profile_id = Column(Integer, ForeignKey("ui_experience_profiles.id"), nullable=False)
    
    # Device characteristics
    device_category = Column(String, nullable=False)  # phone, tablet, foldable
    screen_size_inches = Column(Float, nullable=True)
    pixel_density = Column(Float, nullable=True)
    operating_system = Column(String, nullable=True)
    
    # Mobile-specific features
    touch_optimizations = Column(JSON, nullable=True)
    gesture_configurations = Column(JSON, nullable=True)
    haptic_feedback_patterns = Column(JSON, nullable=True)
    
    # Performance optimizations
    network_optimization = Column(JSON, nullable=True)
    battery_optimization = Column(JSON, nullable=True)
    memory_optimization = Column(JSON, nullable=True)
    
    # Adaptive features
    orientation_adaptations = Column(JSON, nullable=True)
    one_handed_mode_config = Column(JSON, nullable=True)
    reachability_optimizations = Column(JSON, nullable=True)
    
    # Context-aware adaptations
    location_based_adaptations = Column(JSON, nullable=True)
    time_based_adaptations = Column(JSON, nullable=True)
    connectivity_adaptations = Column(JSON, nullable=True)
    
    # Accessibility on mobile
    mobile_accessibility_features = Column(JSON, nullable=True)
    voice_over_optimizations = Column(JSON, nullable=True)
    switch_control_config = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)