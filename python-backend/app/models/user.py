from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, DECIMAL
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


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
