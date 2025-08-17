"""
Phase 6: Adaptive Revelation Prompts Schemas
Pydantic models for adaptive revelation API request/response validation
"""
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Any, Optional
from datetime import datetime

class AdaptiveRevelationRequest(BaseModel):
    """Request schema for generating adaptive revelation prompts"""
    connection_id: int = Field(..., description="ID of the soul connection")
    revelation_day: int = Field(..., ge=1, le=7, description="Day in the revelation cycle (1-7)")
    count: int = Field(default=3, ge=1, le=5, description="Number of prompts to generate")
    preferences: Optional[Dict[str, Any]] = Field(default=None, description="Additional preferences")

class AdaptiveRevelationResponse(BaseModel):
    """Response schema for adaptive revelation prompts"""
    id: Optional[int] = None
    text: str = Field(..., description="The personalized revelation prompt text")
    theme: str = Field(..., description="Theme category of the revelation")
    focus: str = Field(..., description="Primary focus area of the prompt")
    emotional_depth: str = Field(..., description="Depth level (light, medium, deep, profound)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="AI confidence in personalization quality")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional prompt metadata")
    timing_recommendation: Optional[Dict[str, Any]] = Field(default=None, description="Optimal timing info")
    follow_up_suggestions: Optional[List[str]] = Field(default=None, description="Suggested follow-up questions")

class RevelationThemeResponse(BaseModel):
    """Response schema for revelation themes"""
    name: str = Field(..., description="Theme name")
    description: str = Field(..., description="Theme description")
    communication_style: str = Field(..., description="Recommended communication style")
    requires_high_compatibility: bool = Field(..., description="Whether theme requires high compatibility")
    emotional_intensity: float = Field(..., ge=0.0, le=1.0, description="Emotional intensity level")
    sample_templates: List[str] = Field(..., description="Sample template texts")

class RevelationTimingResponse(BaseModel):
    """Response schema for timing recommendations"""
    connection_id: int = Field(..., description="Connection ID")
    recommended_hours: List[int] = Field(..., description="Optimal hours of day (0-23)")
    optimal_day_time: str = Field(..., description="Best time period (morning, afternoon, evening)")
    reasoning: str = Field(..., description="Explanation for timing recommendation")
    urgency: str = Field(..., description="Urgency level (low, moderate, high)")
    next_optimal_time: Optional[datetime] = Field(default=None, description="Next specific optimal time")

class RevelationFeedbackRequest(BaseModel):
    """Request schema for revelation feedback"""
    revelation_id: int = Field(..., description="ID of the revelation")
    content_id: int = Field(..., description="ID of the personalized content")
    helpful_score: float = Field(..., ge=1.0, le=5.0, description="How helpful was the prompt (1-5)")
    engagement_score: float = Field(..., ge=1.0, le=5.0, description="How engaging was the prompt (1-5)")
    emotional_resonance: float = Field(..., ge=1.0, le=5.0, description="Emotional impact (1-5)")
    timing_appropriateness: float = Field(..., ge=1.0, le=5.0, description="Timing quality (1-5)")
    comments: Optional[str] = Field(default=None, description="Optional feedback comments")

    @validator('helpful_score', 'engagement_score', 'emotional_resonance', 'timing_appropriateness')
    def validate_scores(cls, v):
        """Ensure scores are in valid range"""
        if not 1.0 <= v <= 5.0:
            raise ValueError('Score must be between 1.0 and 5.0')
        return v

class RevelationAnalyticsResponse(BaseModel):
    """Response schema for revelation analytics"""
    connection_id: int = Field(..., description="Connection ID")
    completed_revelation_days: int = Field(..., description="Number of revelation days completed")
    total_revelations_shared: int = Field(..., description="Total revelations shared by user")
    average_words_per_revelation: float = Field(..., description="Average word count per revelation")
    theme_distribution: Dict[str, int] = Field(..., description="Distribution of themes used")
    engagement_trend: str = Field(..., description="Overall engagement trend")
    most_successful_themes: List[str] = Field(..., description="Themes with highest engagement")
    overall_depth_score: float = Field(..., description="Average depth/intensity score")
    personalization_effectiveness: float = Field(..., ge=0.0, le=1.0, description="How well personalization works")
    next_recommended_theme: Optional[str] = Field(default=None, description="Next recommended theme")

class RevelationInsight(BaseModel):
    """Schema for revelation insights and recommendations"""
    insight_type: str = Field(..., description="Type of insight (performance, suggestion, warning)")
    title: str = Field(..., description="Insight title")
    description: str = Field(..., description="Detailed insight description")
    recommended_action: Optional[str] = Field(default=None, description="Suggested action")
    impact_score: float = Field(..., ge=0.0, le=1.0, description="Potential impact of following insight")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Supporting data")

class RevelationOptimizationRequest(BaseModel):
    """Request schema for revelation optimization"""
    connection_id: int = Field(..., description="Connection to optimize for")
    optimization_goals: List[str] = Field(..., description="What to optimize (engagement, depth, timing)")
    constraints: Optional[Dict[str, Any]] = Field(default=None, description="Optimization constraints")

class RevelationOptimizationResponse(BaseModel):
    """Response schema for revelation optimization results"""
    optimization_id: str = Field(..., description="Optimization session ID")
    improved_prompts: List[AdaptiveRevelationResponse] = Field(..., description="Optimized prompts")
    expected_improvements: Dict[str, float] = Field(..., description="Expected improvement percentages")
    insights: List[RevelationInsight] = Field(..., description="Optimization insights")

# Advanced schemas for real-time features

class RealTimeRevelationUpdate(BaseModel):
    """Schema for real-time revelation updates"""
    connection_id: int = Field(..., description="Connection ID")
    user_id: int = Field(..., description="User making the update")
    update_type: str = Field(..., description="Type of update (started, completed, feedback)")
    revelation_day: int = Field(..., ge=1, le=7, description="Revelation day")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Update data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Update timestamp")

class RevelationProgressSync(BaseModel):
    """Schema for syncing revelation progress between users"""
    connection_id: int = Field(..., description="Connection ID")
    user_progress: Dict[str, Any] = Field(..., description="User's revelation progress")
    partner_progress: Dict[str, Any] = Field(..., description="Partner's revelation progress")
    synchronized_at: datetime = Field(default_factory=datetime.utcnow, description="Sync timestamp")

class PersonalizedRevelationTheme(BaseModel):
    """Schema for personalized theme recommendations"""
    theme_name: str = Field(..., description="Theme name")
    personalization_score: float = Field(..., ge=0.0, le=1.0, description="How well theme fits user")
    compatibility_requirement: float = Field(..., ge=0.0, le=1.0, description="Required compatibility level")
    optimal_day: int = Field(..., ge=1, le=7, description="Best day for this theme")
    reasoning: str = Field(..., description="Why this theme is recommended")
    sample_prompt: str = Field(..., description="Sample personalized prompt")

class RevelationMatchingInsight(BaseModel):
    """Schema for insights about revelation compatibility between users"""
    connection_id: int = Field(..., description="Connection ID")
    compatibility_score: float = Field(..., ge=0.0, le=1.0, description="Revelation compatibility score")
    shared_themes: List[str] = Field(..., description="Themes both users respond well to")
    complementary_themes: List[str] = Field(..., description="Themes that complement each other")
    communication_sync: float = Field(..., ge=0.0, le=1.0, description="How well communication styles align")
    timing_compatibility: float = Field(..., ge=0.0, le=1.0, description="How well timing preferences align")
    recommendations: List[str] = Field(..., description="Recommendations for improving revelation experience")

class AdaptiveRevelationConfig(BaseModel):
    """Configuration schema for adaptive revelation system"""
    user_id: int = Field(..., description="User ID")
    personalization_level: str = Field(default="medium", description="Level of personalization (low, medium, high)")
    preferred_themes: List[str] = Field(default=[], description="User's preferred themes")
    avoided_themes: List[str] = Field(default=[], description="Themes to avoid")
    communication_style_override: Optional[str] = Field(default=None, description="Override communication style")
    timing_preferences: Optional[Dict[str, Any]] = Field(default=None, description="Timing preferences")
    depth_progression_rate: str = Field(default="normal", description="How quickly to increase depth (slow, normal, fast)")
    enable_follow_ups: bool = Field(default=True, description="Whether to generate follow-up suggestions")
    enable_timing_optimization: bool = Field(default=True, description="Whether to optimize timing")

    @validator('personalization_level')
    def validate_personalization_level(cls, v):
        if v not in ['low', 'medium', 'high']:
            raise ValueError('Personalization level must be low, medium, or high')
        return v

    @validator('depth_progression_rate')
    def validate_depth_progression(cls, v):
        if v not in ['slow', 'normal', 'fast']:
            raise ValueError('Depth progression rate must be slow, normal, or fast')
        return v

class RevelationEngagementMetrics(BaseModel):
    """Schema for tracking revelation engagement metrics"""
    revelation_id: int = Field(..., description="Revelation ID")
    content_id: int = Field(..., description="Personalized content ID")
    time_to_start: Optional[float] = Field(default=None, description="Time to start writing (seconds)")
    completion_time: Optional[float] = Field(default=None, description="Time to complete (seconds)")
    word_count: int = Field(default=0, description="Word count of revelation")
    engagement_indicators: Dict[str, Any] = Field(default={}, description="Various engagement metrics")
    follow_up_engagement: Optional[Dict[str, Any]] = Field(default=None, description="Follow-up interaction metrics")
    partner_response_time: Optional[float] = Field(default=None, description="Partner's response time")
    mutual_engagement_score: Optional[float] = Field(default=None, description="Combined engagement score")

class RevelationA11ySupport(BaseModel):
    """Schema for accessibility support in revelations"""
    audio_description: Optional[str] = Field(default=None, description="Audio description of prompt")
    simplified_language: Optional[str] = Field(default=None, description="Simplified version for cognitive accessibility")
    visual_aids: Optional[List[str]] = Field(default=None, description="Visual aid suggestions")
    interaction_alternatives: Optional[Dict[str, str]] = Field(default=None, description="Alternative interaction methods")
    reading_level: Optional[str] = Field(default=None, description="Reading level assessment")

class RevelationLocalization(BaseModel):
    """Schema for localized revelation content"""
    language_code: str = Field(..., description="Language code (e.g., 'en', 'es', 'fr')")
    cultural_context: Optional[str] = Field(default=None, description="Cultural context considerations")
    localized_text: str = Field(..., description="Localized prompt text")
    cultural_sensitivity_notes: Optional[List[str]] = Field(default=None, description="Cultural sensitivity considerations")
    regional_preferences: Optional[Dict[str, Any]] = Field(default=None, description="Regional customizations")