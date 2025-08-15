# Matching schemas for AI-enhanced compatibility analysis

from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime

class CompatibilityAnalysis(BaseModel):
    """Schema for compatibility analysis results"""
    user1_id: int
    user2_id: int
    overall_score: float
    compatibility_breakdown: Dict[str, float]
    semantic_similarity: float
    personality_match: float
    value_alignment: float
    communication_compatibility: float
    lifestyle_match: float
    conversation_starters: List[str]
    analysis_timestamp: datetime
    ai_confidence: float
    recommended_ice_breakers: List[str]

class ConversationStarter(BaseModel):
    """Schema for AI-generated conversation starters"""
    text: str
    category: str  # 'common_interest', 'value_based', 'personality'
    confidence_score: float
    context: Dict[str, Any]
    
class SemanticProfile(BaseModel):
    """Schema for semantic profile representation"""
    user_id: int
    topic_weights: Dict[str, float]
    personality_vector: List[float]
    interest_embeddings: Dict[str, List[float]]
    communication_style: str
    updated_at: datetime

class MatchingPreferences(BaseModel):
    """Schema for user matching preferences"""
    user_id: int
    age_range: tuple[int, int]
    distance_km: int
    compatibility_threshold: float
    preferred_personality_traits: List[str]
    dealbreakers: List[str]
    must_haves: List[str]