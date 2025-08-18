"""
Photo Reveal System Models - Phase 4 Secure Photo Management
Soul Before Skin progressive photo revelation with consent and timeline management
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timedelta
from enum import Enum
import uuid
from typing import Dict, List, Optional

from app.core.database import Base


class PhotoRevealStage(Enum):
    """Stages of photo reveal progression"""
    HIDDEN = "hidden"                    # Photos completely hidden
    CONSENT_REQUESTED = "consent_requested"  # One user requested reveal
    MUTUAL_CONSENT = "mutual_consent"    # Both users agreed to reveal
    REVEALED = "revealed"                # Photos are now visible
    DECLINED = "declined"                # One or both users declined


class PhotoConsentType(Enum):
    """Types of photo consent"""
    TIMELINE_BASED = "timeline_based"    # Automatic after 7-day revelation cycle
    MANUAL_REQUEST = "manual_request"    # User manually requests early reveal
    MUTUAL_AGREEMENT = "mutual_agreement"  # Both users mutually agree


class PhotoPrivacyLevel(Enum):
    """Photo privacy and blur levels"""
    COMPLETELY_HIDDEN = "completely_hidden"  # No photo shown
    SILHOUETTE = "silhouette"                # Basic outline only
    HEAVILY_BLURRED = "heavily_blurred"      # Very blurred preview
    LIGHTLY_BLURRED = "lightly_blurred"      # Slightly blurred preview
    FULLY_REVEALED = "fully_revealed"        # Complete clear photo


class UserPhoto(Base):
    """User photo storage with privacy controls"""
    __tablename__ = "user_photos"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    photo_uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    
    # Photo storage and metadata
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)  # Encrypted storage path
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String, nullable=False)
    upload_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Privacy and security
    is_profile_primary = Column(Boolean, default=False)
    privacy_level = Column(SQLEnum(PhotoPrivacyLevel), default=PhotoPrivacyLevel.COMPLETELY_HIDDEN)
    encryption_key_hash = Column(String, nullable=False)  # For secure storage
    
    # Photo processing status
    blur_versions_generated = Column(Boolean, default=False)
    silhouette_generated = Column(Boolean, default=False)
    processing_complete = Column(Boolean, default=False)
    
    # Moderation and safety
    moderation_status = Column(String, default="pending")  # pending, approved, rejected
    moderation_flags = Column(JSON)  # AI moderation results
    manual_review_required = Column(Boolean, default=False)
    
    # Photo reveal history
    total_reveals = Column(Integer, default=0)
    last_revealed_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="photos")
    reveal_requests = relationship("PhotoRevealRequest", back_populates="photo")
    reveal_permissions = relationship("PhotoRevealPermission", back_populates="photo")
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def get_reveal_url(self, privacy_level: PhotoPrivacyLevel, requester_id: int) -> Optional[str]:
        """Get appropriate photo URL based on privacy level and permissions"""
        # Implementation would generate appropriate URL based on privacy level
        base_url = f"/api/v1/photos/{self.photo_uuid}"
        
        if privacy_level == PhotoPrivacyLevel.COMPLETELY_HIDDEN:
            return None
        elif privacy_level == PhotoPrivacyLevel.SILHOUETTE:
            return f"{base_url}/silhouette"
        elif privacy_level == PhotoPrivacyLevel.HEAVILY_BLURRED:
            return f"{base_url}/blur/heavy"
        elif privacy_level == PhotoPrivacyLevel.LIGHTLY_BLURRED:
            return f"{base_url}/blur/light"
        elif privacy_level == PhotoPrivacyLevel.FULLY_REVEALED:
            return f"{base_url}/full?token={self._generate_access_token(requester_id)}"
        
        return None

    def _generate_access_token(self, requester_id: int) -> str:
        """Generate secure access token for photo viewing"""
        # Implementation would create JWT token with expiration
        return f"temp_token_{requester_id}_{self.id}"


class PhotoRevealTimeline(Base):
    """Timeline management for soul connection photo reveals"""
    __tablename__ = "photo_reveal_timelines"
    
    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("soul_connections.id"), nullable=False, unique=True)
    
    # Timeline configuration
    revelation_cycle_days = Column(Integer, default=7)  # Standard 7-day cycle
    auto_reveal_enabled = Column(Boolean, default=True)  # Auto-reveal after cycle
    early_reveal_allowed = Column(Boolean, default=True)  # Allow manual early reveal
    
    # Timeline progression
    connection_started_at = Column(DateTime, nullable=False)
    revelation_cycle_completed_at = Column(DateTime)
    photo_reveal_eligible_at = Column(DateTime)  # When reveal becomes available
    
    # Current status
    current_stage = Column(SQLEnum(PhotoRevealStage), default=PhotoRevealStage.HIDDEN)
    days_until_reveal = Column(Integer)  # Calculated daily
    revelations_completed = Column(Integer, default=0)  # Out of 7
    min_revelations_required = Column(Integer, default=5)  # Minimum for photo reveal
    
    # Consent tracking
    user1_consent_status = Column(String, default="pending")  # pending, granted, declined
    user2_consent_status = Column(String, default="pending")
    mutual_consent_achieved = Column(Boolean, default=False)
    consent_achieved_at = Column(DateTime)
    
    # Photo reveal execution
    photos_revealed = Column(Boolean, default=False)
    photo_reveal_completed_at = Column(DateTime)
    reveal_method = Column(SQLEnum(PhotoConsentType))  # How reveal was triggered
    
    # Privacy settings
    allow_partial_reveal = Column(Boolean, default=True)  # Allow blurred previews
    gradual_reveal_enabled = Column(Boolean, default=True)  # Progressive clarity
    
    # Relationships
    connection = relationship("SoulConnection", back_populates="photo_timeline")
    reveal_requests = relationship("PhotoRevealRequest", back_populates="timeline")
    reveal_events = relationship("PhotoRevealEvent", back_populates="timeline")
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def calculate_days_until_reveal(self) -> int:
        """Calculate days remaining until automatic photo reveal"""
        if self.photo_reveal_eligible_at:
            if datetime.utcnow() >= self.photo_reveal_eligible_at:
                return 0
            else:
                delta = self.photo_reveal_eligible_at - datetime.utcnow()
                return max(0, delta.days)
        
        # Calculate based on connection start + cycle days
        if self.connection_started_at:
            target_date = self.connection_started_at + timedelta(days=self.revelation_cycle_days)
            if datetime.utcnow() >= target_date:
                return 0
            else:
                delta = target_date - datetime.utcnow()
                return max(0, delta.days)
        
        return self.revelation_cycle_days

    def is_reveal_eligible(self) -> bool:
        """Check if photo reveal is currently eligible"""
        if not self.auto_reveal_enabled:
            return False
            
        # Check if minimum revelations completed
        if self.revelations_completed < self.min_revelations_required:
            return False
            
        # Check if timeline has passed
        return self.calculate_days_until_reveal() == 0

    def get_reveal_progress_percentage(self) -> float:
        """Get photo reveal progress as percentage"""
        if self.photos_revealed:
            return 100.0
            
        # Factor in both time and revelations
        time_progress = max(0, 1 - (self.calculate_days_until_reveal() / self.revelation_cycle_days))
        revelation_progress = self.revelations_completed / self.min_revelations_required
        
        # Weight time 40%, revelations 60%
        return min(100.0, (time_progress * 40 + revelation_progress * 60))


class PhotoRevealRequest(Base):
    """Individual photo reveal requests and consent management"""
    __tablename__ = "photo_reveal_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    timeline_id = Column(Integer, ForeignKey("photo_reveal_timelines.id"), nullable=False)
    photo_id = Column(Integer, ForeignKey("user_photos.id"), nullable=False)
    
    # Request details
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    photo_owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    request_type = Column(SQLEnum(PhotoConsentType), nullable=False)
    
    # Request message and context
    request_message = Column(Text)  # Optional personal message
    emotional_context = Column(JSON)  # Current emotional state, connection energy
    
    # Status tracking
    status = Column(String, default="pending")  # pending, approved, declined, expired
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    responded_at = Column(DateTime)
    expires_at = Column(DateTime)  # Auto-expire consent requests
    
    # Response details
    response_message = Column(Text)  # Optional response from photo owner
    decline_reason = Column(String)  # If declined, optional reason
    
    # Privacy preferences for reveal
    requested_privacy_level = Column(SQLEnum(PhotoPrivacyLevel), default=PhotoPrivacyLevel.FULLY_REVEALED)
    granted_privacy_level = Column(SQLEnum(PhotoPrivacyLevel))  # What was actually granted
    
    # Usage tracking
    photo_viewed = Column(Boolean, default=False)
    first_viewed_at = Column(DateTime)
    total_views = Column(Integer, default=0)
    view_duration_seconds = Column(Integer, default=0)
    
    # Relationships
    timeline = relationship("PhotoRevealTimeline", back_populates="reveal_requests")
    photo = relationship("UserPhoto", back_populates="reveal_requests")
    requester = relationship("User", foreign_keys=[requester_id])
    photo_owner = relationship("User", foreign_keys=[photo_owner_id])
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def is_expired(self) -> bool:
        """Check if the consent request has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    def can_be_approved(self) -> bool:
        """Check if request can still be approved"""
        return self.status == "pending" and not self.is_expired()


class PhotoRevealPermission(Base):
    """Active photo viewing permissions between users"""
    __tablename__ = "photo_reveal_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    photo_id = Column(Integer, ForeignKey("user_photos.id"), nullable=False)
    connection_id = Column(Integer, ForeignKey("soul_connections.id"), nullable=False)
    
    # Permission details
    viewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    photo_owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    privacy_level = Column(SQLEnum(PhotoPrivacyLevel), nullable=False)
    
    # Permission lifecycle
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime)  # Optional expiration
    revoked_at = Column(DateTime)  # If permission is revoked
    is_active = Column(Boolean, default=True)
    
    # Usage analytics
    total_views = Column(Integer, default=0)
    last_viewed_at = Column(DateTime)
    total_view_time_seconds = Column(Integer, default=0)
    
    # Permission source
    granted_through_request_id = Column(Integer, ForeignKey("photo_reveal_requests.id"))
    grant_method = Column(SQLEnum(PhotoConsentType), nullable=False)
    
    # Relationships
    photo = relationship("UserPhoto", back_populates="reveal_permissions")
    connection = relationship("SoulConnection")
    viewer = relationship("User", foreign_keys=[viewer_id])
    photo_owner = relationship("User", foreign_keys=[photo_owner_id])
    source_request = relationship("PhotoRevealRequest")
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def is_valid(self) -> bool:
        """Check if permission is currently valid"""
        if not self.is_active or self.revoked_at:
            return False
            
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
            
        return True

    def record_view(self, view_duration_seconds: int = 0):
        """Record a photo view"""
        self.total_views += 1
        self.last_viewed_at = datetime.utcnow()
        self.total_view_time_seconds += view_duration_seconds


class PhotoRevealEvent(Base):
    """Event log for photo reveal timeline activities"""
    __tablename__ = "photo_reveal_events"
    
    id = Column(Integer, primary_key=True, index=True)
    timeline_id = Column(Integer, ForeignKey("photo_reveal_timelines.id"), nullable=False)
    connection_id = Column(Integer, ForeignKey("soul_connections.id"), nullable=False)
    
    # Event details
    event_type = Column(String, nullable=False)  # consent_requested, consent_granted, photo_revealed, etc.
    user_id = Column(Integer, ForeignKey("users.id"))  # User who triggered the event
    event_data = Column(JSON)  # Additional event metadata
    
    # Event context
    revelation_day = Column(Integer)  # Which day in the revelation cycle
    emotional_state = Column(String)  # User's emotional state during event
    connection_energy_level = Column(String)  # Connection energy at time of event
    
    # Timeline snapshot
    days_since_connection = Column(Integer)
    revelations_completed_at_time = Column(Integer)
    
    # Event description
    event_description = Column(Text)  # Human-readable event description
    system_generated = Column(Boolean, default=False)  # vs user-initiated
    
    # Relationships
    timeline = relationship("PhotoRevealTimeline", back_populates="reveal_events")
    connection = relationship("SoulConnection")
    user = relationship("User")
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    @classmethod
    def create_event(cls, timeline_id: int, connection_id: int, event_type: str, 
                    user_id: Optional[int] = None, event_data: Optional[Dict] = None,
                    description: Optional[str] = None) -> 'PhotoRevealEvent':
        """Factory method to create photo reveal events"""
        return cls(
            timeline_id=timeline_id,
            connection_id=connection_id,
            event_type=event_type,
            user_id=user_id,
            event_data=event_data or {},
            event_description=description,
            system_generated=user_id is None
        )


class PhotoModerationLog(Base):
    """Photo content moderation and safety tracking"""
    __tablename__ = "photo_moderation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    photo_id = Column(Integer, ForeignKey("user_photos.id"), nullable=False)
    
    # Moderation details
    moderation_type = Column(String, nullable=False)  # ai_scan, manual_review, user_report
    moderator_type = Column(String)  # system, admin_user, ai_model
    moderator_id = Column(Integer, ForeignKey("users.id"))  # If human moderator
    
    # Moderation results
    status = Column(String, nullable=False)  # approved, rejected, flagged, pending
    confidence_score = Column(Integer)  # AI confidence (0-100)
    flags_detected = Column(JSON)  # Array of detected issues
    
    # Violation details
    violation_type = Column(String)  # inappropriate, nudity, violence, etc.
    severity_level = Column(String)  # low, medium, high, critical
    action_taken = Column(String)  # approved, rejected, requires_review, etc.
    
    # Moderation context
    moderation_notes = Column(Text)  # Human moderator notes
    appeal_status = Column(String)  # none, pending, approved, denied
    appeal_notes = Column(Text)
    
    # AI model details
    ai_model_version = Column(String)
    processing_time_ms = Column(Integer)
    
    # Relationships
    photo = relationship("UserPhoto")
    moderator = relationship("User", foreign_keys=[moderator_id])
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)