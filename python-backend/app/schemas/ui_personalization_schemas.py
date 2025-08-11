"""
Phase 6: UI Personalization Schemas
Pydantic models for UI personalization API request/response validation
"""
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

class InteractionTrackingRequest(BaseModel):
    """Schema for tracking user interactions"""
    type: str = Field(..., description="Type of interaction (click, scroll, swipe, etc.)")
    element_type: Optional[str] = Field(None, description="Type of UI element")
    element_id: Optional[str] = Field(None, description="Unique element identifier")
    page_route: Optional[str] = Field(None, description="Current page route")
    device_type: Optional[str] = Field(None, description="Device type (mobile, desktop, tablet)")
    screen_size: Optional[str] = Field(None, description="Screen dimensions (e.g., '375x667')")
    viewport_size: Optional[str] = Field(None, description="Viewport dimensions")
    scroll_position: Optional[int] = Field(None, description="Current scroll position")
    session_id: Optional[str] = Field(None, description="User session identifier")
    time_since_last: Optional[float] = Field(None, description="Time since last interaction (seconds)")
    duration: Optional[float] = Field(None, description="Interaction duration (seconds)")
    coordinates: Optional[Dict[str, int]] = Field(None, description="Click/touch coordinates")
    scroll_distance: Optional[int] = Field(None, description="Scroll distance in pixels")
    swipe_direction: Optional[str] = Field(None, description="Swipe direction (up, down, left, right)")
    gesture_data: Optional[Dict[str, Any]] = Field(None, description="Complex gesture data")
    emotional_state: Optional[str] = Field(None, description="Current emotional state")
    connection_context: Optional[Dict[str, Any]] = Field(None, description="Connection context data")
    feature_flags: Optional[Dict[str, Any]] = Field(None, description="Active feature flags")
    render_time: Optional[float] = Field(None, description="Render time in milliseconds")
    response_time: Optional[float] = Field(None, description="Response time in milliseconds")
    error: Optional[bool] = Field(False, description="Whether an error occurred")
    error_details: Optional[str] = Field(None, description="Error details if applicable")

    @validator('type')
    def validate_interaction_type(cls, v):
        valid_types = ['click', 'scroll', 'hover', 'swipe', 'keyboard', 'form_interaction', 
                      'navigation', 'gesture', 'voice_command']
        if v not in valid_types:
            raise ValueError(f'Interaction type must be one of: {valid_types}')
        return v

class UIAdaptationRequest(BaseModel):
    """Schema for requesting UI adaptations"""
    current_context: Dict[str, Any] = Field(..., description="Current application context")
    page_route: Optional[str] = Field(None, description="Current page route")
    device_context: Optional[Dict[str, Any]] = Field(None, description="Device information")
    user_state: Optional[Dict[str, Any]] = Field(None, description="Current user state")
    preferences_override: Optional[Dict[str, Any]] = Field(None, description="Temporary preference overrides")

class UIProfileResponse(BaseModel):
    """Schema for UI profile information"""
    id: int
    user_id: int
    primary_device_type: str
    preferred_theme: str
    font_size_preference: str
    animation_preference: str
    layout_density: str
    interaction_speed: str
    navigation_pattern: str
    personalization_score: float = Field(..., ge=0.0, le=1.0)
    accessibility_settings: Dict[str, bool]
    current_preferences: Dict[str, Any]
    last_updated: datetime
    
    class Config:
        from_attributes = True

class UIPersonalizationResponse(BaseModel):
    """Schema for UI personalization recommendations"""
    user_id: int
    personalizations: Dict[str, Any] = Field(..., description="Personalization recommendations by category")
    generated_at: datetime
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in personalizations")
    applied_strategies: List[str] = Field(..., description="Personalization strategies applied")

class PersonalizationInsightResponse(BaseModel):
    """Schema for personalization insights"""
    id: int
    insight_type: str = Field(..., description="Type of insight (pattern, preference, anomaly, opportunity)")
    category: str = Field(..., description="Insight category (usability, accessibility, performance)")
    title: str = Field(..., description="Insight title")
    description: str = Field(..., description="Detailed description")
    recommended_action: Optional[str] = Field(None, description="Recommended action to take")
    priority: str = Field(..., description="Implementation priority (low, medium, high, critical)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the insight")
    impact_estimate: Optional[float] = Field(None, ge=0.0, le=1.0, description="Expected impact")
    generated_at: datetime
    implemented: bool = Field(False, description="Whether the insight has been acted upon")

class UIAnalyticsResponse(BaseModel):
    """Schema for UI analytics data"""
    user_id: int
    analysis_period_days: int
    total_interactions: int
    unique_sessions: int
    error_rate: float = Field(..., ge=0.0, le=1.0)
    personalization_score: float = Field(..., ge=0.0, le=1.0)
    behavior_patterns: Dict[str, Any]
    device_usage_distribution: Dict[str, int]
    page_interaction_distribution: Dict[str, int]
    interaction_efficiency: Dict[str, Any]
    recommendations: List[str]

class ThemeAdaptation(BaseModel):
    """Schema for theme adaptations"""
    suggest_dark_mode: Optional[Dict[str, Any]] = None
    minimal_theme: Optional[Dict[str, Any]] = None
    high_contrast: Optional[Dict[str, Any]] = None
    font_scaling: Optional[Dict[str, Any]] = None
    color_adjustments: Optional[Dict[str, Any]] = None

class LayoutOptimization(BaseModel):
    """Schema for layout optimizations"""
    simplified_navigation: Optional[Dict[str, Any]] = None
    enhanced_navigation: Optional[Dict[str, Any]] = None
    swipe_optimized: Optional[Dict[str, Any]] = None
    click_optimized: Optional[Dict[str, Any]] = None
    mobile_first: Optional[Dict[str, Any]] = None
    desktop_optimized: Optional[Dict[str, Any]] = None

class InteractionEnhancement(BaseModel):
    """Schema for interaction enhancements"""
    fast_user_optimizations: Optional[Dict[str, Any]] = None
    deliberate_user_optimizations: Optional[Dict[str, Any]] = None
    error_prevention: Optional[Dict[str, Any]] = None
    engagement_boosters: Optional[Dict[str, Any]] = None
    gesture_improvements: Optional[Dict[str, Any]] = None

class AccessibilityImprovement(BaseModel):
    """Schema for accessibility improvements"""
    screen_reader_support: Optional[Dict[str, Any]] = None
    keyboard_navigation: Optional[Dict[str, Any]] = None
    motor_accessibility: Optional[Dict[str, Any]] = None
    visual_accessibility: Optional[Dict[str, Any]] = None
    cognitive_accessibility: Optional[Dict[str, Any]] = None

class PerformanceOptimization(BaseModel):
    """Schema for performance optimizations"""
    loading_optimizations: Optional[Dict[str, Any]] = None
    data_saving: Optional[Dict[str, Any]] = None
    mobile_performance: Optional[Dict[str, Any]] = None
    memory_optimization: Optional[Dict[str, Any]] = None
    battery_efficiency: Optional[Dict[str, Any]] = None

class ComponentAdaptation(BaseModel):
    """Schema for component adaptations"""
    chat_component: Optional[Dict[str, Any]] = None
    discovery_component: Optional[Dict[str, Any]] = None
    profile_component: Optional[Dict[str, Any]] = None
    navigation_component: Optional[Dict[str, Any]] = None
    revelation_component: Optional[Dict[str, Any]] = None

class DetailedPersonalizationResponse(BaseModel):
    """Detailed schema for comprehensive UI personalizations"""
    user_id: int
    theme_adaptations: ThemeAdaptation
    layout_optimizations: LayoutOptimization
    interaction_enhancements: InteractionEnhancement
    accessibility_improvements: AccessibilityImprovement
    performance_optimizations: PerformanceOptimization
    component_adaptations: ComponentAdaptation
    overall_confidence: float = Field(..., ge=0.0, le=1.0)
    applied_strategies: List[str]
    generation_context: Dict[str, Any]
    expires_at: Optional[datetime] = None

class InteractionPattern(BaseModel):
    """Schema for interaction patterns"""
    pattern_type: str = Field(..., description="Type of pattern (navigation, timing, device)")
    pattern_name: str = Field(..., description="Name of the pattern")
    frequency: float = Field(..., ge=0.0, description="How often this pattern occurs")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in pattern detection")
    impact_on_ux: str = Field(..., description="Impact on user experience (positive, negative, neutral)")
    recommendations: List[str] = Field(default=[], description="Recommendations based on this pattern")

class BehaviorAnalysis(BaseModel):
    """Schema for comprehensive behavior analysis"""
    user_id: int
    analysis_period: str = Field(..., description="Period of analysis (e.g., 'last_30_days')")
    total_interactions: int
    identified_patterns: List[InteractionPattern]
    dominant_interaction_style: str
    navigation_efficiency: float = Field(..., ge=0.0, le=1.0)
    error_tendency: float = Field(..., ge=0.0, le=1.0)
    engagement_level: str = Field(..., description="Overall engagement level (low, medium, high)")
    accessibility_indicators: Dict[str, bool]
    performance_sensitivity: Dict[str, Any]
    device_preferences: Dict[str, Any]
    timing_patterns: Dict[str, Any]
    personalization_opportunities: List[str]

class UITestVariant(BaseModel):
    """Schema for UI A/B test variants"""
    variant_id: str = Field(..., description="Unique variant identifier")
    variant_name: str = Field(..., description="Human-readable variant name")
    test_category: str = Field(..., description="Category of UI element being tested")
    changes: Dict[str, Any] = Field(..., description="Specific changes in this variant")
    target_metric: str = Field(..., description="Primary metric being optimized")
    expected_impact: float = Field(..., ge=0.0, le=1.0, description="Expected improvement")
    confidence_threshold: float = Field(default=0.8, ge=0.5, le=1.0)

class UIABTestResponse(BaseModel):
    """Schema for UI A/B test information"""
    test_id: str
    test_name: str
    user_variant: str
    test_category: str
    enrollment_date: datetime
    is_active: bool
    primary_metric_value: Optional[float] = None
    secondary_metrics: Optional[Dict[str, float]] = None
    session_count: int
    conversion_achieved: bool

class RealTimeAdaptationResponse(BaseModel):
    """Schema for real-time adaptation responses"""
    adaptation_id: str = Field(..., description="Unique adaptation identifier")
    adaptations_applied: Dict[str, Any] = Field(..., description="Specific adaptations applied")
    trigger_reason: str = Field(..., description="What triggered this adaptation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in adaptation quality")
    expected_improvement: float = Field(..., ge=0.0, le=1.0, description="Expected UX improvement")
    rollback_available: bool = Field(True, description="Whether adaptation can be rolled back")
    expires_at: Optional[datetime] = Field(None, description="When adaptation expires")

class PersonalizationFeedback(BaseModel):
    """Schema for personalization feedback"""
    satisfaction_score: float = Field(..., ge=0.0, le=1.0, description="Overall satisfaction (0-1)")
    feature: str = Field(default="general", description="Specific feature being rated")
    comments: Optional[str] = Field(None, description="Optional feedback comments")
    improvement_suggestions: Optional[List[str]] = Field(None, description="Suggested improvements")
    would_recommend: Optional[bool] = Field(None, description="Would recommend to others")

class UIPreferencesUpdate(BaseModel):
    """Schema for updating UI preferences"""
    preferred_theme: Optional[str] = Field(None, description="Theme preference")
    font_size_preference: Optional[str] = Field(None, description="Font size preference")
    animation_preference: Optional[str] = Field(None, description="Animation preference")
    layout_density: Optional[str] = Field(None, description="Layout density preference")
    color_contrast_preference: Optional[str] = Field(None, description="Color contrast preference")
    haptic_feedback_intensity: Optional[float] = Field(None, ge=0.0, le=1.0)
    screen_reader_enabled: Optional[bool] = Field(None, description="Screen reader usage")
    keyboard_navigation_primary: Optional[bool] = Field(None, description="Primary keyboard navigation")
    high_contrast_enabled: Optional[bool] = Field(None, description="High contrast mode")
    reduce_motion_enabled: Optional[bool] = Field(None, description="Reduced motion preference")
    
    @validator('preferred_theme')
    def validate_theme(cls, v):
        if v and v not in ['light', 'dark', 'auto']:
            raise ValueError('Theme must be light, dark, or auto')
        return v
    
    @validator('font_size_preference')
    def validate_font_size(cls, v):
        if v and v not in ['small', 'medium', 'large', 'extra-large']:
            raise ValueError('Font size must be small, medium, large, or extra-large')
        return v
    
    @validator('animation_preference')
    def validate_animation(cls, v):
        if v and v not in ['none', 'reduced', 'standard', 'enhanced']:
            raise ValueError('Animation preference must be none, reduced, standard, or enhanced')
        return v
    
    @validator('layout_density')
    def validate_density(cls, v):
        if v and v not in ['compact', 'comfortable', 'spacious']:
            raise ValueError('Layout density must be compact, comfortable, or spacious')
        return v

class UIPersonalizationConfig(BaseModel):
    """Schema for UI personalization configuration"""
    enable_real_time_adaptation: bool = Field(default=True)
    adaptation_sensitivity: float = Field(default=0.7, ge=0.0, le=1.0)
    learning_rate: float = Field(default=0.1, ge=0.01, le=1.0)
    feedback_frequency: str = Field(default="adaptive", description="How often to ask for feedback")
    auto_apply_high_confidence: bool = Field(default=True)
    enable_a_b_testing: bool = Field(default=True)
    privacy_level: str = Field(default="standard", description="Data collection privacy level")
    
    @validator('feedback_frequency')
    def validate_feedback_frequency(cls, v):
        valid_frequencies = ['never', 'rare', 'adaptive', 'frequent', 'always']
        if v not in valid_frequencies:
            raise ValueError(f'Feedback frequency must be one of: {valid_frequencies}')
        return v
    
    @validator('privacy_level')
    def validate_privacy_level(cls, v):
        valid_levels = ['minimal', 'standard', 'detailed']
        if v not in valid_levels:
            raise ValueError(f'Privacy level must be one of: {valid_levels}')
        return v

class UIMetrics(BaseModel):
    """Schema for UI performance metrics"""
    page_load_time: Optional[float] = Field(None, description="Average page load time (ms)")
    interaction_response_time: Optional[float] = Field(None, description="Average interaction response time (ms)")
    error_rate: float = Field(..., ge=0.0, le=1.0, description="Error rate percentage")
    user_satisfaction: float = Field(..., ge=0.0, le=1.0, description="User satisfaction score")
    task_completion_rate: float = Field(..., ge=0.0, le=1.0, description="Task completion rate")
    bounce_rate: float = Field(..., ge=0.0, le=1.0, description="Bounce rate")
    session_duration: Optional[float] = Field(None, description="Average session duration (minutes)")
    interactions_per_session: Optional[float] = Field(None, description="Average interactions per session")
    accessibility_score: float = Field(..., ge=0.0, le=1.0, description="Accessibility compliance score")
    mobile_usability_score: float = Field(..., ge=0.0, le=1.0, description="Mobile usability score")