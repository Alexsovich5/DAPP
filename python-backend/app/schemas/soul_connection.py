from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class SoulConnectionBase(BaseModel):
    connection_stage: str = "soul_discovery"
    compatibility_score: Optional[float] = None
    compatibility_breakdown: Optional[Dict[str, Any]] = None
    reveal_day: int = 1
    mutual_reveal_consent: bool = False
    first_dinner_completed: bool = False
    status: str = "active"


class SoulConnectionCreate(SoulConnectionBase):
    user2_id: int
    # user1_id and initiated_by will be set from current user


class SoulConnectionUpdate(BaseModel):
    connection_stage: Optional[str] = None
    reveal_day: Optional[int] = None
    mutual_reveal_consent: Optional[bool] = None
    first_dinner_completed: Optional[bool] = None
    status: Optional[str] = None


class SoulConnectionResponse(SoulConnectionBase):
    id: int
    user1_id: int
    user2_id: int
    initiated_by: int
    created_at: datetime
    updated_at: datetime
    
    # Include user details for frontend display
    user1_profile: Optional[Dict[str, Any]] = None
    user2_profile: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class CompatibilityResponse(BaseModel):
    total_compatibility: float = Field(..., description="Overall compatibility score (0-100)")
    breakdown: Dict[str, float] = Field(..., description="Detailed compatibility breakdown")
    match_quality: str = Field(..., description="Descriptive match quality label")
    explanation: str = Field(..., description="Human-readable compatibility explanation")


class DiscoveryRequest(BaseModel):
    max_results: int = Field(default=10, ge=1, le=50)
    min_compatibility: float = Field(default=50.0, ge=0, le=100)
    hide_photos: bool = Field(default=True)
    age_range_min: Optional[int] = Field(default=None, ge=18, le=100)
    age_range_max: Optional[int] = Field(default=None, ge=18, le=100)


class DiscoveryResponse(BaseModel):
    user_id: int
    compatibility: CompatibilityResponse
    profile_preview: Dict[str, Any]  # Limited profile info for soul discovery
    is_photo_hidden: bool = True
    
    class Config:
        from_attributes = True