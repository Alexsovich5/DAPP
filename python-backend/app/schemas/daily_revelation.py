from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DailyRevelationBase(BaseModel):
    day_number: int = Field(..., ge=1, le=7, description="Day in the revelation cycle (1-7)")
    revelation_type: str = Field(..., description="Type of revelation being shared")
    content: str = Field(..., min_length=10, max_length=1000, description="Revelation content")


class DailyRevelationCreate(DailyRevelationBase):
    connection_id: int
    # sender_id will be set from current user


class DailyRevelationUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=10, max_length=1000)
    is_read: Optional[bool] = None


class DailyRevelationResponse(DailyRevelationBase):
    id: int
    connection_id: int
    sender_id: int
    is_read: bool
    created_at: datetime
    
    # Include sender info for display
    sender_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class RevelationTimelineResponse(BaseModel):
    connection_id: int
    current_day: int
    revelations: list[DailyRevelationResponse]
    next_revelation_type: Optional[str] = None
    is_cycle_complete: bool = False
    
    class Config:
        from_attributes = True


class RevelationPrompt(BaseModel):
    day_number: int
    revelation_type: str
    prompt_text: str
    example_response: str
    
    class Config:
        from_attributes = True