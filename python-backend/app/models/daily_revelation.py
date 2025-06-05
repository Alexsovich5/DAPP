from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
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


class DailyRevelation(Base):
    __tablename__ = "daily_revelations"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("soul_connections.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Revelation details
    day_number = Column(Integer, nullable=False)  # 1-7 for the revelation cycle
    revelation_type = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    
    # Metadata
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    connection = relationship("SoulConnection", back_populates="revelations")
    sender = relationship("User", foreign_keys=[sender_id])