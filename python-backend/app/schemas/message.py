from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class MessageBase(BaseModel):
    message_text: str = Field(..., min_length=1, max_length=2000, description="Message content")
    message_type: str = Field(default="text", description="Type of message (text, revelation, photo, system)")


class MessageCreate(MessageBase):
    connection_id: int
    # sender_id will be set from current user


class MessageUpdate(BaseModel):
    is_read: Optional[bool] = None


class MessageResponse(MessageBase):
    id: int
    connection_id: int
    sender_id: int
    is_read: bool
    created_at: datetime
    
    # Include sender info for display
    sender_name: Optional[str] = None
    is_own_message: bool = False  # Will be set based on current user
    
    class Config:
        from_attributes = True


class ConversationResponse(BaseModel):
    connection_id: int
    messages: list[MessageResponse]
    total_messages: int
    unread_count: int
    last_message_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True