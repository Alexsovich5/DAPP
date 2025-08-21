# User Safety Models for Database Integration
# Safety and moderation features for the dating platform

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.core.database import Base


class ReportCategory(enum.Enum):
    """Categories for user reports"""
    HARASSMENT = "harassment"
    FAKE_PROFILE = "fake_profile"
    INAPPROPRIATE_PHOTOS = "inappropriate_photos"
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    SPAM = "spam"
    SCAM = "scam"
    VIOLENCE_THREATS = "violence_threats"
    HATE_SPEECH = "hate_speech"
    UNDERAGE = "underage"
    IMPERSONATION = "impersonation"
    SAFETY_CONCERN = "safety_concern"
    OTHER = "other"


class ReportStatus(enum.Enum):
    """Status of user reports"""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class SafetyStatus(enum.Enum):
    """User safety status for moderation"""
    CLEAR = "clear"
    ACTIVE = "active"
    FLAGGED = "flagged"
    RESTRICTED = "restricted"
    SUSPENDED = "suspended"
    BANNED = "banned"
    UNDER_REVIEW = "under_review"


class UserReport(Base):
    """User reports for safety and moderation"""
    __tablename__ = "user_reports"

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    reported_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    category = Column(SQLEnum(ReportCategory), nullable=False, index=True)
    description = Column(Text, nullable=False)
    evidence_urls = Column(Text)  # JSON string of evidence URLs
    status = Column(SQLEnum(ReportStatus), default=ReportStatus.PENDING, index=True)
    admin_notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True))
    resolved_by = Column(Integer, ForeignKey("users.id"))

    # Relationships
    reporter = relationship("User", foreign_keys=[reporter_id], back_populates="reports_made")
    reported_user = relationship("User", foreign_keys=[reported_user_id], back_populates="reports_received")
    resolver = relationship("User", foreign_keys=[resolved_by])

    def __repr__(self):
        return f"<UserReport(id={self.id}, category={self.category.value}, status={self.status.value})>"


class BlockedUser(Base):
    """Blocked user relationships"""
    __tablename__ = "blocked_users"

    id = Column(Integer, primary_key=True, index=True)
    blocker_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    blocked_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    reason = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    blocker = relationship("User", foreign_keys=[blocker_id], back_populates="users_blocked")
    blocked_user = relationship("User", foreign_keys=[blocked_user_id], back_populates="blocked_by_users")

    # Unique constraint to prevent duplicate blocks
    __table_args__ = (
        {"schema": None},  # Ensure no schema conflicts
    )

    def __repr__(self):
        return f"<BlockedUser(blocker_id={self.blocker_id}, blocked_user_id={self.blocked_user_id})>"


class UserSafetyProfile(Base):
    """User safety profile and moderation status"""
    __tablename__ = "user_safety_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    safety_status = Column(SQLEnum(SafetyStatus), default=SafetyStatus.ACTIVE, index=True)
    restriction_reason = Column(Text)
    restriction_start = Column(DateTime(timezone=True))
    restriction_end = Column(DateTime(timezone=True))
    total_reports = Column(Integer, default=0, index=True)
    last_report_date = Column(DateTime(timezone=True))
    safety_score = Column(Integer, default=100)  # 0-100 safety score
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    user = relationship("User", back_populates="safety_profile")

    def __repr__(self):
        return f"<UserSafetyProfile(user_id={self.user_id}, status={self.safety_status.value})>"


class ModerationAction(Base):
    """Track moderation actions taken"""
    __tablename__ = "moderation_actions"

    id = Column(Integer, primary_key=True, index=True)
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    moderator_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action_type = Column(String(50), nullable=False, index=True)  # warning, suspension, ban, etc.
    reason = Column(Text, nullable=False)
    related_report_id = Column(Integer, ForeignKey("user_reports.id"))
    duration_hours = Column(Integer)  # For temporary actions
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    expires_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True, index=True)

    # Relationships
    target_user = relationship("User", foreign_keys=[target_user_id])
    moderator = relationship("User", foreign_keys=[moderator_id])
    related_report = relationship("UserReport")

    def __repr__(self):
        return f"<ModerationAction(id={self.id}, action={self.action_type}, target={self.target_user_id})>"