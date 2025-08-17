"""
Phase 6: Advanced Personalization & Content Intelligence Schemas
Pydantic models for personalization API request/response validation
"""
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

from app.models.personalization_models import PersonalizationStrategy, ContentType

class PersonalizationProfileResponse(BaseModel):
    """Response schema for personalization profile"""
    id: int
    user_id: int
    preferred_communication_style: str
    conversation_pace_preference: str
    revelation_timing_preference: str
    content_depth_preference: str
    communication_patterns: Optional[Dict[str, Any]] = None
    engagement_patterns: Optional[Dict[str, Any]] = None
    emotional_expression_patterns: Optional[Dict[str, Any]] = None
    topic_preferences: Optional[Dict[str, Any]] = None
    content_engagement_scores: Optional[Dict[str, Any]] = None
    personalization_effectiveness: float
    adaptation_learning_rate: float
    preferred_ui_complexity: str
    animation_preferences: Optional[Dict[str, Any]] = None
    color_theme_preferences: Optional[Dict[str, Any]] = None
    accessibility_preferences: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ConversationStarterRequest(BaseModel):
    """Request schema for generating conversation starters"""
    target_user_id: int = Field(..., description="ID of the user to start conversation with")
    count: int = Field(default=5, ge=1, le=10, description="Number of starters to generate")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context for generation")

class ConversationStarterResponse(BaseModel):
    """Response schema for conversation starters"""
    id: Optional[int] = None
    text: str
    category: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = None

class RevelationPromptRequest(BaseModel):
    """Request schema for generating revelation prompts"""
    revelation_day: int = Field(..., ge=1, le=7, description="Day in the revelation cycle (1-7)")
    connection_context: Dict[str, Any] = Field(..., description="Connection context and progress")

class RevelationPromptResponse(BaseModel):
    """Response schema for revelation prompts"""
    id: Optional[int] = None
    text: str
    focus: str
    emotional_depth: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = None

class SmartReplyRequest(BaseModel):
    """Request schema for generating smart replies"""
    conversation_context: Dict[str, Any] = Field(..., description="Current conversation context")
    last_message: str = Field(..., description="The message to reply to")
    reply_count: int = Field(default=3, ge=1, le=5, description="Number of reply suggestions")

class SmartReplyResponse(BaseModel):
    """Response schema for smart replies"""
    id: Optional[int] = None
    text: str
    strategy: str = Field(..., description="Reply strategy used")
    tone: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = None

class UIPersonalizationRequest(BaseModel):
    """Request schema for UI personalization"""
    current_context: Dict[str, Any] = Field(..., description="Current app context and user state")
    screen: str = Field(..., description="Current screen/page identifier")
    device_type: Optional[str] = Field(default="web", description="Device type (web, mobile, tablet)")

class UIPersonalizationResponse(BaseModel):
    """Response schema for UI personalization"""
    theme_adjustments: Dict[str, Any]
    layout_preferences: Dict[str, Any]
    animation_settings: Dict[str, Any]
    content_density: str
    interaction_hints: List[Dict[str, Any]]

class ContentFeedbackRequest(BaseModel):
    """Request schema for content feedback"""
    content_id: int = Field(..., description="ID of the personalized content")
    feedback_data: Dict[str, Any] = Field(..., description="Feedback data including type, score, etc.")

    @validator('feedback_data')
    def validate_feedback_data(cls, v):
        """Validate feedback data structure"""
        required_fields = {'type'}  # 'explicit', 'implicit', 'behavioral'
        if not isinstance(v, dict) or not required_fields.issubset(v.keys()):
            raise ValueError('Feedback data must include feedback type')
        
        feedback_type = v.get('type')
        if feedback_type not in ['explicit', 'implicit', 'behavioral']:
            raise ValueError('Feedback type must be explicit, implicit, or behavioral')
        
        # Validate explicit feedback has score
        if feedback_type == 'explicit' and 'score' not in v:
            raise ValueError('Explicit feedback must include score')
        
        return v

class ContentFeedbackResponse(BaseModel):
    """Response schema for content feedback submission"""
    success: bool
    message: str

class AlgorithmOptimizationRequest(BaseModel):
    """Request schema for algorithm optimization"""
    optimization_type: str = Field(..., description="Type of optimization (matching, content_generation, ui_adaptation)")
    target_metrics: Dict[str, float] = Field(..., description="Target performance metrics")
    constraints: Optional[Dict[str, Any]] = Field(default=None, description="Optimization constraints")

    @validator('optimization_type')
    def validate_optimization_type(cls, v):
        valid_types = ['matching', 'content_generation', 'ui_adaptation', 'conversation_flow']
        if v not in valid_types:
            raise ValueError(f'Optimization type must be one of: {valid_types}')
        return v

class AlgorithmOptimizationResponse(BaseModel):
    """Response schema for algorithm optimization"""
    optimization_id: int
    parameters: Dict[str, Any]
    expected_improvement: Dict[str, float]

class ContentPerformanceMetrics(BaseModel):
    """Schema for content performance metrics"""
    content_id: int
    content_type: str
    presentation_count: int
    engagement_count: int
    success_count: int
    feedback_score: Optional[float] = None
    effectiveness_score: float
    should_retire: bool
    ai_confidence_score: float
    optimization_version: int

class ConversationFlowAnalytics(BaseModel):
    """Schema for conversation flow analytics"""
    id: int
    connection_id: Optional[int] = None
    conversation_stage: str
    message_count: int
    average_response_time: Optional[float] = None
    engagement_score: float
    emotional_connection_score: float
    analysis_date: str
    successful_starters: Optional[Dict[str, Any]] = None
    optimal_timing_patterns: Optional[Dict[str, Any]] = None

class PersonalizationPreferences(BaseModel):
    """Schema for user personalization preferences"""
    communication_style: str = Field(default="balanced")
    conversation_pace: str = Field(default="moderate")
    revelation_timing: str = Field(default="gradual")
    content_depth: str = Field(default="medium")
    ui_complexity: str = Field(default="balanced")
    animation_preferences: Optional[Dict[str, Any]] = None
    color_theme_preferences: Optional[Dict[str, Any]] = None
    accessibility_preferences: Optional[Dict[str, Any]] = None
    learning_rate: float = Field(default=0.1, ge=0.01, le=1.0)
    personalization_effectiveness: float = Field(default=0.0, ge=0.0, le=1.0)

    @validator('communication_style')
    def validate_communication_style(cls, v):
        valid_styles = ['casual', 'formal', 'balanced', 'playful']
        if v not in valid_styles:
            raise ValueError(f'Communication style must be one of: {valid_styles}')
        return v

    @validator('conversation_pace')
    def validate_conversation_pace(cls, v):
        valid_paces = ['slow', 'moderate', 'fast', 'adaptive']
        if v not in valid_paces:
            raise ValueError(f'Conversation pace must be one of: {valid_paces}')
        return v

    @validator('revelation_timing')
    def validate_revelation_timing(cls, v):
        valid_timings = ['immediate', 'gradual', 'patient']
        if v not in valid_timings:
            raise ValueError(f'Revelation timing must be one of: {valid_timings}')
        return v

    @validator('content_depth')
    def validate_content_depth(cls, v):
        valid_depths = ['light', 'medium', 'deep', 'adaptive']
        if v not in valid_depths:
            raise ValueError(f'Content depth must be one of: {valid_depths}')
        return v

    @validator('ui_complexity')
    def validate_ui_complexity(cls, v):
        valid_complexities = ['minimal', 'balanced', 'detailed']
        if v not in valid_complexities:
            raise ValueError(f'UI complexity must be one of: {valid_complexities}')
        return v

class OptimizationHistory(BaseModel):
    """Schema for optimization history"""
    id: int
    optimization_type: str
    algorithm_version: str
    improvement_percentage: float
    statistical_significance: Optional[float] = None
    is_deployed: bool
    deployment_percentage: float
    created_at: str
    target_metrics: Dict[str, float]
    current_metrics: Optional[Dict[str, float]] = None

class PersonalizedContentResponse(BaseModel):
    """Schema for personalized content responses"""
    id: int
    content_type: str
    content_text: str
    generation_strategy: str
    ai_confidence_score: float
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# Advanced schemas for real-time features

class RealTimePersonalizationUpdate(BaseModel):
    """Schema for real-time personalization updates"""
    user_id: int
    update_type: str  # 'preference_change', 'behavior_pattern', 'feedback_received'
    data: Dict[str, Any]
    timestamp: datetime

class PersonalizationInsight(BaseModel):
    """Schema for personalization insights and recommendations"""
    insight_type: str  # 'performance', 'opportunity', 'warning'
    title: str
    description: str
    recommended_action: Optional[str] = None
    impact_score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    data: Optional[Dict[str, Any]] = None

class ABTestVariant(BaseModel):
    """Schema for A/B testing variants"""
    variant_id: str
    name: str
    description: str
    parameters: Dict[str, Any]
    traffic_percentage: float = Field(..., ge=0.0, le=100.0)
    is_active: bool

class ABTestResults(BaseModel):
    """Schema for A/B test results"""
    test_id: str
    test_name: str
    variants: List[ABTestVariant]
    winner: Optional[str] = None
    statistical_significance: Optional[float] = None
    improvement_percentage: Optional[float] = None
    sample_size: int
    test_duration_days: int
    metrics: Dict[str, Dict[str, float]]  # variant_id -> metric_name -> value