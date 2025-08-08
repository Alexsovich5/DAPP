from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, DECIMAL, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import enum
from app.core.database import Base


class ConnectionStage(str, enum.Enum):
    SOUL_DISCOVERY = "soul_discovery"
    REVELATION_PHASE = "revelation_phase" 
    DEEPER_CONNECTION = "deeper_connection"
    PHOTO_REVEAL = "photo_reveal"
    DINNER_PLANNING = "dinner_planning"
    COMPLETED = "completed"


class ConnectionEnergyLevel(str, enum.Enum):
    """Energy levels for connection visualization"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high" 
    SOULMATE = "soulmate"


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
    user1_photo_consent = Column(Boolean, default=False)
    user2_photo_consent = Column(Boolean, default=False)
    photo_revealed_at = Column(DateTime, nullable=True)
    first_dinner_completed = Column(Boolean, default=False)
    
    # Phase 4 Enhanced Features
    # Energy and mood tracking
    current_energy_level = Column(String, default=ConnectionEnergyLevel.MEDIUM)
    energy_history = Column(JSON, nullable=True)  # Track energy changes over time
    
    # Advanced compatibility
    personality_match_score = Column(DECIMAL(5,2), nullable=True)
    values_alignment_score = Column(DECIMAL(5,2), nullable=True) 
    communication_compatibility = Column(DECIMAL(5,2), nullable=True)
    emotional_resonance_score = Column(DECIMAL(5,2), nullable=True)
    
    # Engagement metrics
    total_messages_exchanged = Column(Integer, default=0)
    revelation_completion_percentage = Column(DECIMAL(5,2), default=0.0)
    average_response_time_minutes = Column(Integer, nullable=True)
    mutual_engagement_score = Column(DECIMAL(5,2), nullable=True)
    
    # Timeline tracking
    first_message_at = Column(DateTime, nullable=True)
    last_message_at = Column(DateTime, nullable=True)
    revelation_started_at = Column(DateTime, nullable=True)
    stage_progression_dates = Column(JSON, nullable=True)  # Track when each stage was reached
    
    # Quality indicators
    conversation_depth_score = Column(DECIMAL(5,2), nullable=True) 
    emotional_openness_level = Column(Integer, default=1)  # 1-10 scale
    mutual_satisfaction_rating = Column(DECIMAL(5,2), nullable=True)
    
    # Real-time state
    last_activity_at = Column(DateTime, default=datetime.utcnow)
    active_users_count = Column(Integer, default=0)
    is_typing_active = Column(Boolean, default=False)
    
    # Connection metadata
    initiated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="active")  # active, paused, ended, archived
    end_reason = Column(String, nullable=True)  # If ended: mutual, timeout, reported, etc.
    ended_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    ended_at = Column(DateTime, nullable=True)
    
    # Success prediction
    success_prediction_score = Column(DECIMAL(5,2), nullable=True)
    ml_model_version = Column(String, nullable=True)
    prediction_confidence = Column(DECIMAL(5,2), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user1 = relationship("User", foreign_keys=[user1_id])
    user2 = relationship("User", foreign_keys=[user2_id])
    initiator = relationship("User", foreign_keys=[initiated_by])
    ender = relationship("User", foreign_keys=[ended_by])
    
    # Relationship to revelations and messages
    revelations = relationship("DailyRevelation", back_populates="connection", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="connection", cascade="all, delete-orphan")
    
    # Photo reveal relationship
    photo_timeline = relationship("PhotoRevealTimeline", back_populates="connection", uselist=False)
    
    # Helper methods for frontend
    def get_partner_id(self, current_user_id: int) -> int:
        """Get the partner's user ID"""
        return self.user2_id if self.user1_id == current_user_id else self.user1_id
        
    def has_mutual_photo_consent(self) -> bool:
        """Check if both users have given photo consent"""
        return self.user1_photo_consent and self.user2_photo_consent
        
    def get_days_active(self) -> int:
        """Get number of days the connection has been active"""
        if self.ended_at:
            return (self.ended_at - self.created_at).days
        return (datetime.utcnow() - self.created_at).days
        
    def is_recently_active(self, hours: int = 24) -> bool:
        """Check if connection had recent activity"""
        if not self.last_activity_at:
            return False
        return (datetime.utcnow() - self.last_activity_at) <= timedelta(hours=hours)