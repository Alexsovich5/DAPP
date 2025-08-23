from datetime import datetime
from typing import Optional

from app.models.match import MatchStatus
from pydantic import BaseModel


class MatchBase(BaseModel):
    recipient_id: int
    restaurant_preference: Optional[str] = None
    proposed_date: Optional[datetime] = None


class MatchCreate(MatchBase):
    pass


class MatchUpdate(BaseModel):
    status: MatchStatus
    restaurant_preference: Optional[str] = None
    proposed_date: Optional[datetime] = None


class Match(MatchBase):
    id: int
    initiator_id: int
    status: MatchStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
