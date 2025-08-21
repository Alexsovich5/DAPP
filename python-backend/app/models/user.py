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
    
    # Activity tracking for matching algorithms  
    last_active_at = Column(DateTime, nullable=True, index=True)
    is_verified = Column(Boolean, default=False, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        index=True
    )
    
    # Core relationships with proper cascading
    profile = relationship("Profile", uselist=False, back_populates="user", cascade="all, delete-orphan")
    sent_matches = relationship(
        "Match", back_populates="sender", foreign_keys="[Match.sender_id]", cascade="all, delete-orphan"
    )
    received_matches = relationship(
        "Match", back_populates="receiver", foreign_keys="[Match.receiver_id]", cascade="all, delete-orphan"
    )
    
    # Soul connection relationships
    soul_connections_as_user1 = relationship(
        "SoulConnection", foreign_keys="[SoulConnection.user1_id]", cascade="all, delete-orphan"
    )
    soul_connections_as_user2 = relationship(
        "SoulConnection", foreign_keys="[SoulConnection.user2_id]", cascade="all, delete-orphan"
    )
    initiated_connections = relationship(
        "SoulConnection", foreign_keys="[SoulConnection.initiated_by]", cascade="all, delete-orphan"
    )
    
    # Message and revelation relationships
    sent_messages = relationship("Message", foreign_keys="[Message.sender_id]", cascade="all, delete-orphan")
    sent_revelations = relationship("DailyRevelation", foreign_keys="[DailyRevelation.sender_id]", cascade="all, delete-orphan")
    
    # Photo reveal relationships with proper cascading
    photos = relationship("UserPhoto", back_populates="user", cascade="all, delete-orphan")
    photo_reveal_requests_made = relationship(
        "PhotoRevealRequest", foreign_keys="[PhotoRevealRequest.requester_id]", cascade="all, delete-orphan"
    )
    photo_reveal_requests_received = relationship(
        "PhotoRevealRequest", foreign_keys="[PhotoRevealRequest.photo_owner_id]", cascade="all, delete-orphan"
    )
    photo_permissions_granted = relationship(
        "PhotoRevealPermission", foreign_keys="[PhotoRevealPermission.photo_owner_id]", cascade="all, delete-orphan"
    )
    photo_permissions_received = relationship(
        "PhotoRevealPermission", foreign_keys="[PhotoRevealPermission.viewer_id]", cascade="all, delete-orphan"
    )
    
    # Safety and moderation relationships with proper cascading
    safety_profile = relationship("UserSafetyProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    reports_made = relationship(
        "UserReport", foreign_keys="[UserReport.reporter_id]", back_populates="reporter", cascade="all, delete-orphan"
    )
    reports_received = relationship(
        "UserReport", foreign_keys="[UserReport.reported_user_id]", back_populates="reported_user", cascade="all, delete-orphan"
    )
    users_blocked = relationship(
        "BlockedUser", foreign_keys="[BlockedUser.blocker_id]", back_populates="blocker", cascade="all, delete-orphan"
    )
    blocked_by_users = relationship(
        "BlockedUser", foreign_keys="[BlockedUser.blocked_user_id]", back_populates="blocked_user", cascade="all, delete-orphan"
    )
    moderation_actions_received = relationship(
        "ModerationAction", foreign_keys="[ModerationAction.target_user_id]", cascade="all, delete-orphan"
    )
    moderation_actions_performed = relationship(
        "ModerationAction", foreign_keys="[ModerationAction.moderator_id]"
    )
    
    def __str__(self):
        """String representation of the User"""
        return f"User(id={self.id}, username={self.username}, email={self.email})"
