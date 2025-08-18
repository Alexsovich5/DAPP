# Pydantic schemas for AI-Enhanced Matching System
# Dinner First Dating Platform

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from datetime import datetime

class CompatibilityBreakdown(BaseModel):
    """Detailed breakdown of compatibility scores"""
    semantic_similarity: float = Field(..., ge=0, le=100, description="Semantic text similarity score")
    communication_style: float = Field(..., ge=0, le=100, description="Communication compatibility score")
    emotional_depth: float = Field(..., ge=0, le=100, description="Emotional compatibility score")
    life_goals: float = Field(..., ge=0, le=100, description="Life goals alignment score")
    personality_match: float = Field(..., ge=0, le=100, description="Personality compatibility score")
    interest_overlap: float = Field(..., ge=0, le=100, description="Interest overlap score")

class AICompatibilityAnalysis(BaseModel):
    """Complete AI compatibility analysis result"""
    ai_compatibility_score: float = Field(..., ge=0, le=100, description="Overall AI compatibility score")
    confidence_level: float = Field(..., ge=0, le=100, description="Confidence in the analysis")
    compatibility_breakdown: CompatibilityBreakdown
    unique_connection_potential: List[str] = Field(default=[], description="Unique factors for connection")
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: Optional[float] = Field(None, description="Analysis processing time in milliseconds")
    error: Optional[str] = Field(None, description="Error message if analysis failed")

class ConversationStarter(BaseModel):
    """AI-generated conversation starter"""
    message: str = Field(..., min_length=10, max_length=500, description="Conversation starter text")
    category: str = Field(..., description="Category of the starter (interests, values, personality, etc.)")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence in starter effectiveness")
    personalization_factors: List[str] = Field(default=[], description="Factors used for personalization")

class ConversationStartersResponse(BaseModel):
    """Response containing multiple conversation starters"""
    starters: List[ConversationStarter]
    user_compatibility_score: float = Field(..., ge=0, le=100)
    generation_timestamp: datetime = Field(default_factory=datetime.utcnow)

class MatchingRequest(BaseModel):
    """Request for AI matching analysis"""
    user1_id: int = Field(..., description="First user ID")
    user2_id: int = Field(..., description="Second user ID")
    include_conversation_starters: bool = Field(default=False, description="Include conversation starters")
    detailed_analysis: bool = Field(default=True, description="Include detailed breakdown")

class BatchMatchingRequest(BaseModel):
    """Request for batch matching analysis"""
    target_user_id: int = Field(..., description="Target user for matching")
    candidate_user_ids: List[int] = Field(..., min_items=1, max_items=100, description="Candidate user IDs")
    min_compatibility_score: float = Field(default=50.0, ge=0, le=100, description="Minimum compatibility threshold")
    include_conversation_starters: bool = Field(default=False, description="Include conversation starters")
    
    @validator('candidate_user_ids')
    def validate_unique_candidates(cls, v, values):
        if 'target_user_id' in values and values['target_user_id'] in v:
            raise ValueError("Target user cannot be in candidate list")
        if len(v) != len(set(v)):
            raise ValueError("Candidate user IDs must be unique")
        return v

class MatchResult(BaseModel):
    """Single match result in batch analysis"""
    user_id: int
    compatibility_analysis: AICompatibilityAnalysis
    conversation_starters: Optional[List[ConversationStarter]] = None
    match_rank: Optional[int] = Field(None, description="Rank in batch results")

class BatchMatchingResponse(BaseModel):
    """Response for batch matching analysis"""
    target_user_id: int
    matches: List[MatchResult]
    total_candidates_analyzed: int
    matches_above_threshold: int
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: Optional[float] = None

class PersonalityInsight(BaseModel):
    """Insight about personality compatibility"""
    aspect: str = Field(..., description="Personality aspect (e.g., 'communication style')")
    description: str = Field(..., description="Description of the insight")
    compatibility_impact: str = Field(..., description="How this impacts compatibility")
    score: float = Field(..., ge=0, le=100, description="Score for this aspect")

class DeepCompatibilityAnalysis(BaseModel):
    """Deep analysis with personality insights"""
    basic_analysis: AICompatibilityAnalysis
    personality_insights: List[PersonalityInsight]
    relationship_potential: str = Field(..., description="Assessment of relationship potential")
    growth_opportunities: List[str] = Field(default=[], description="Areas for mutual growth")
    potential_challenges: List[str] = Field(default=[], description="Potential relationship challenges")
    recommended_activities: List[str] = Field(default=[], description="Recommended activities for connection")

class AIModelStatus(BaseModel):
    """Status of AI models"""
    is_initialized: bool
    model_version: str = "1.0.0"
    training_data_size: int = Field(default=0, description="Number of profiles used for training")
    last_updated: Optional[datetime] = None
    capabilities: List[str] = Field(default=[
        "semantic_similarity",
        "compatibility_analysis", 
        "conversation_generation",
        "personality_insights"
    ])

class AIMatchingConfig(BaseModel):
    """Configuration for AI matching system"""
    compatibility_weights: Dict[str, float] = Field(default={
        "semantic_similarity": 0.25,
        "communication_style": 0.20,
        "emotional_depth": 0.20,
        "life_goals": 0.15,
        "personality_match": 0.10,
        "interest_overlap": 0.10
    })
    min_profile_completeness: float = Field(default=0.5, ge=0, le=1)
    conversation_starter_count: int = Field(default=3, ge=1, le=10)
    enable_deep_analysis: bool = Field(default=True)
    privacy_mode: bool = Field(default=True, description="Ensure all processing is local")
    
    @validator('compatibility_weights')
    def validate_weights_sum(cls, v):
        total = sum(v.values())
        if not (0.99 <= total <= 1.01):  # Allow for minor floating point differences
            raise ValueError("Compatibility weights must sum to 1.0")
        return v

class UserProfileEmbedding(BaseModel):
    """User profile embedding for semantic analysis"""
    user_id: int
    embedding_vector: List[float] = Field(..., description="High-dimensional profile embedding")
    text_features: List[str] = Field(default=[], description="Extracted text features")
    personality_vector: List[float] = Field(default=[], description="Personality trait vector")
    interests_vector: List[float] = Field(default=[], description="Interests embedding")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(default="1.0.0", description="Embedding model version")

class SimilarityMatrix(BaseModel):
    """Similarity matrix for batch processing"""
    user_ids: List[int]
    similarity_scores: List[List[float]] = Field(..., description="NxN similarity matrix")
    calculation_method: str = Field(default="cosine_similarity")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MatchingMetrics(BaseModel):
    """Metrics for matching system performance"""
    total_comparisons: int = Field(default=0)
    successful_analyses: int = Field(default=0)
    failed_analyses: int = Field(default=0)
    average_processing_time_ms: float = Field(default=0.0)
    average_compatibility_score: float = Field(default=0.0)
    high_compatibility_matches: int = Field(default=0, description="Matches with >80% compatibility")
    model_confidence_average: float = Field(default=0.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AIMatchingError(BaseModel):
    """Error information for AI matching failures"""
    error_type: str = Field(..., description="Type of error (validation, processing, model, etc.)")
    error_message: str = Field(..., description="Detailed error message")
    user_ids: Optional[List[int]] = Field(None, description="User IDs involved in failed analysis")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    stack_trace: Optional[str] = Field(None, description="Error stack trace for debugging")
    recovery_suggestion: Optional[str] = Field(None, description="Suggested recovery action")