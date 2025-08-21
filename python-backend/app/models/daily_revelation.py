from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class RevelationType(str, enum.Enum):
    PERSONAL_VALUE = "personal_value"
    MEANINGFUL_EXPERIENCE = "meaningful_experience"
    HOPE_OR_DREAM = "hope_or_dream"
    WHAT_MAKES_LAUGH = "what_makes_laugh"
    CHALLENGE_OVERCOME = "challenge_overcome"
    IDEAL_CONNECTION = "ideal_connection"
    PHOTO_REVEAL = "photo_reveal"


class RevelationStatus(str, enum.Enum):
    DRAFT = "draft"
    SHARED = "shared"
    PRIVATE = "private"
    ARCHIVED = "archived"


class DailyRevelation(Base):
    __tablename__ = "daily_revelations"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("soul_connections.id"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Revelation details
    day_number = Column(Integer, nullable=False, index=True)  # 1-7 for the revelation cycle
    revelation_type = Column(String, nullable=False, index=True)
    content = Column(Text, nullable=False)
    
    # Metadata
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    connection = relationship("SoulConnection", back_populates="revelations")
    sender = relationship("User", foreign_keys=[sender_id])

    # Performance indexes for revelation queries
    __table_args__ = (
        Index('ix_revelations_connection_day', 'connection_id', 'day_number'),
        Index('ix_revelations_sender_day', 'sender_id', 'day_number'),
        Index('ix_revelations_connection_sender', 'connection_id', 'sender_id'),
        Index('ix_revelations_connection_type_day', 'connection_id', 'revelation_type', 'day_number'),
        Index('ix_revelations_type_created', 'revelation_type', 'created_at'),
        Index('ix_revelations_sender_unread', 'sender_id', 'is_read'),
    )