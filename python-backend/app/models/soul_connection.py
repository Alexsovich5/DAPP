from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, DECIMAL, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class ConnectionStage(str, enum.Enum):
    SOUL_DISCOVERY = "soul_discovery"
    REVELATION_PHASE = "revelation_phase"
    PHOTO_REVEAL = "photo_reveal"
    DINNER_PLANNING = "dinner_planning"
    COMPLETED = "completed"


class SoulConnection(Base):
    __tablename__ = "soul_connections"

    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user2_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Connection progression
    connection_stage = Column(String, default=ConnectionStage.SOUL_DISCOVERY)
    compatibility_score = Column(DECIMAL(5,2), nullable=True)
    compatibility_breakdown = Column(JSON, nullable=True)  # Store detailed scoring
    
    # Revelation system
    reveal_day = Column(Integer, default=1)
    mutual_reveal_consent = Column(Boolean, default=False)
    first_dinner_completed = Column(Boolean, default=False)
    
    # Connection metadata
    initiated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="active")  # active, paused, ended
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user1 = relationship("User", foreign_keys=[user1_id])
    user2 = relationship("User", foreign_keys=[user2_id])
    initiator = relationship("User", foreign_keys=[initiated_by])
    
    # Relationship to revelations
    revelations = relationship("DailyRevelation", back_populates="connection", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="connection", cascade="all, delete-orphan")