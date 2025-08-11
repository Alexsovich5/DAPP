from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, DECIMAL, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class UserEmotionalState(str, enum.Enum):
    """Current emotional state for typing indicators and animations"""
    CURIOUS = "curious"
    EXCITED = "excited"
    CONTEMPLATIVE = "contemplative"
    ROMANTIC = "romantic"
    NERVOUS = "nervous"
    CONFIDENT = "confident"
    PEACEFUL = "peaceful"
    PLAYFUL = "playful"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    
    # Additional profile fields for frontend compatibility
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    date_of_birth = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    profile_picture = Column(String, nullable=True)
    
    # JSON fields for complex data
    interests = Column(JSON, nullable=True)
    dietary_preferences = Column(JSON, nullable=True)
    
    # Profile completion tracking
    is_profile_complete = Column(Boolean, default=False)
    
    # Soul Before Skin fields
    emotional_onboarding_completed = Column(Boolean, default=False)
    soul_profile_visibility = Column(String, default='hidden')  # hidden, visible, selective
    emotional_depth_score = Column(DECIMAL(5,2), nullable=True)
    core_values = Column(JSON, nullable=True)  # Store values responses
    personality_traits = Column(JSON, nullable=True)  # Store personality assessment
    communication_style = Column(JSON, nullable=True)  # Store communication preferences
    emotional_responses = Column(JSON, nullable=True)  # Store onboarding question responses
    
    # Phase 4 Enhanced Features
    # Real-time state
    current_emotional_state = Column(String, default=UserEmotionalState.CONTEMPLATIVE)
    preferred_animation_speed = Column(Float, default=1.0)  # Animation speed multiplier
    
    # Mobile UX preferences
    haptic_feedback_enabled = Column(Boolean, default=True)
    reduced_motion_preference = Column(Boolean, default=False)
    dark_mode_preference = Column(Boolean, default=False)
    
    # Engagement metrics
    total_swipes = Column(Integer, default=0)
    total_matches = Column(Integer, default=0)
    total_revelations_shared = Column(Integer, default=0)
    total_messages_sent = Column(Integer, default=0)
    
    # Privacy and consent
    photo_sharing_consent = Column(Boolean, default=False)
    analytics_consent = Column(Boolean, default=True)
    marketing_consent = Column(Boolean, default=False)
    
    # Notification preferences
    push_notifications_enabled = Column(Boolean, default=True)
    email_notifications_enabled = Column(Boolean, default=True)
    revelation_reminders = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    profile = relationship("Profile", uselist=False, back_populates="user")
    sent_matches = relationship(
        "Match", back_populates="sender", foreign_keys="[Match.sender_id]"
    )
    received_matches = relationship(
        "Match", back_populates="receiver", foreign_keys="[Match.receiver_id]"
    )
    
    # Photo reveal relationships
    photos = relationship("UserPhoto", back_populates="user")
    
    # AI/ML relationships
    ai_profile = relationship("UserProfile", back_populates="user", uselist=False)
    
    # Phase 6: Personalization relationships
    personalization_profile = relationship("UserPersonalizationProfile", back_populates="user", uselist=False)
    ui_profile = relationship("UserUIProfile", back_populates="user", uselist=False)
