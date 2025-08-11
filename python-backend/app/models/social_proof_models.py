"""
Phase 7: Social Proof & Community Features Models
Database models for trust, verification, and community validation
"""
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, DECIMAL, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class VerificationType(str, enum.Enum):
    """Types of user verification"""
    PHOTO_VERIFICATION = "photo_verification"
    PHONE_VERIFICATION = "phone_verification"
    SOCIAL_MEDIA_VERIFICATION = "social_media_verification"
    IDENTITY_VERIFICATION = "identity_verification"
    EMAIL_VERIFICATION = "email_verification"


class FeedbackType(str, enum.Enum):
    """Types of community feedback"""
    EXCELLENT = "excellent"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    CONCERNING = "concerning"
    NEGATIVE = "negative"


class ReputationCategory(str, enum.Enum):
    """Categories for user reputation scoring"""
    AUTHENTICITY = "authenticity"
    COMMUNICATION = "communication"
    RESPECT = "respect"
    RELIABILITY = "reliability"


class SafetyLevel(str, enum.Enum):
    """Safety concern severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class UserVerification(Base):
    """User verification records for different verification types"""
    __tablename__ = "user_verifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Verification details
    verification_type = Column(String, nullable=False)  # VerificationType enum
    verification_token = Column(String, nullable=True)
    verification_data = Column(JSON, nullable=True)
    
    # Verification status
    is_verified = Column(Boolean, default=False)
    verification_completed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Verification results
    confidence_score = Column(Float, nullable=True)
    verification_notes = Column(Text, nullable=True)
    verification_metadata = Column(JSON, nullable=True)
    
    # Processing information
    verified_by = Column(String, nullable=True)  # system, moderator, api_service
    processing_attempts = Column(Integer, default=0)
    last_attempt_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])


class CommunityFeedback(Base):
    """Community feedback and ratings for users"""
    __tablename__ = "community_feedback"

    id = Column(Integer, primary_key=True, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    connection_id = Column(Integer, ForeignKey("soul_connections.id"), nullable=False)
    
    # Feedback content
    feedback_type = Column(String, nullable=False)  # FeedbackType enum
    rating_scores = Column(JSON, nullable=True)  # {authenticity: 4.5, communication: 5.0, etc}
    feedback_text = Column(Text, nullable=True)
    
    # Context and validation
    interaction_context = Column(JSON, nullable=True)
    is_verified_interaction = Column(Boolean, default=True)
    feedback_weight = Column(Float, default=1.0)
    
    # Moderation
    is_approved = Column(Boolean, default=True)
    moderation_notes = Column(Text, nullable=True)
    moderated_by = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    subject_user = relationship("User", foreign_keys=[subject_user_id])
    connection = relationship("SoulConnection", foreign_keys=[connection_id])


class SuccessStory(Base):
    """Success stories from completed connections"""
    __tablename__ = "success_stories"

    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user2_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    connection_id = Column(Integer, ForeignKey("soul_connections.id"), nullable=False)
    
    # Story content
    story_title = Column(String, nullable=False)
    story_content = Column(Text, nullable=False)
    story_type = Column(String, default="relationship_success")
    
    # Privacy and consent
    both_users_consented = Column(Boolean, default=False)
    public_visibility = Column(Boolean, default=False)
    anonymous_sharing = Column(Boolean, default=True)
    
    # Story metadata
    story_metadata = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)
    
    # Community impact
    inspiration_score = Column(Float, nullable=True)
    community_reactions = Column(JSON, nullable=True)
    view_count = Column(Integer, default=0)
    
    # Moderation
    is_approved = Column(Boolean, default=False)
    moderated_at = Column(DateTime, nullable=True)
    moderated_by = Column(String, nullable=True)
    moderation_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user1 = relationship("User", foreign_keys=[user1_id])
    user2 = relationship("User", foreign_keys=[user2_id])
    connection = relationship("SoulConnection", foreign_keys=[connection_id])


class UserReputation(Base):
    """User reputation scores based on community feedback"""
    __tablename__ = "user_reputations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Reputation scores by category
    authenticity_score = Column(Float, default=0.5)
    communication_score = Column(Float, default=0.5)
    respect_score = Column(Float, default=0.5)
    reliability_score = Column(Float, default=0.5)
    overall_reputation_score = Column(Float, default=0.5)
    
    # Reputation metadata
    total_feedback_count = Column(Integer, default=0)
    positive_feedback_count = Column(Integer, default=0)
    reputation_trend = Column(String, default="stable")  # improving, stable, declining
    
    # Community status
    community_standing = Column(String, default="new_member")
    special_recognitions = Column(JSON, nullable=True)
    
    # Calculation metadata
    last_calculated_at = Column(DateTime, default=datetime.utcnow)
    calculation_confidence = Column(Float, default=0.5)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])


class ReferralSystem(Base):
    """Friend referral system for trusted users"""
    __tablename__ = "referral_system"

    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    referee_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Set when they join
    
    # Referral details
    referee_email = Column(String, nullable=False)
    referral_token = Column(String, nullable=False, unique=True)
    referral_message = Column(Text, nullable=True)
    referral_context = Column(JSON, nullable=True)
    
    # Referral status
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    
    # Rewards and benefits
    referrer_rewards = Column(JSON, nullable=True)
    referee_benefits = Column(JSON, nullable=True)
    rewards_claimed = Column(Boolean, default=False)
    
    # Success tracking
    referee_completed_onboarding = Column(Boolean, default=False)
    referee_first_connection = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    referrer = relationship("User", foreign_keys=[referrer_id])
    referee = relationship("User", foreign_keys=[referee_id])


class SocialProofIndicator(Base):
    """Social proof indicators displayed on user profiles"""
    __tablename__ = "social_proof_indicators"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Indicator details
    indicator_type = Column(String, nullable=False)  # verification, reputation, feedback, etc.
    indicator_badge = Column(String, nullable=False)
    indicator_description = Column(String, nullable=False)
    
    # Display settings
    is_active = Column(Boolean, default=True)
    display_priority = Column(Integer, default=0)
    visibility_settings = Column(JSON, nullable=True)
    
    # Indicator metadata
    confidence_score = Column(Float, nullable=True)
    indicator_data = Column(JSON, nullable=True)
    
    # Validity
    expires_at = Column(DateTime, nullable=True)
    auto_refresh = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])


class TrustScore(Base):
    """Overall trust scores for users"""
    __tablename__ = "trust_scores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Trust score components
    trust_score = Column(Float, nullable=False, default=0.5)  # 0.0 to 1.0
    verification_score = Column(Float, nullable=False, default=0.0)
    community_feedback_score = Column(Float, nullable=False, default=0.5)
    behavioral_score = Column(Float, nullable=True)
    
    # Trust level classification
    trust_level = Column(String, default="unverified")  # unverified, verified_user, trusted_member, community_champion
    trust_badges = Column(JSON, nullable=True)
    
    # Score metadata
    calculation_method = Column(String, default="weighted_average")
    score_confidence = Column(Float, default=0.5)
    contributing_factors = Column(JSON, nullable=True)
    
    # History tracking
    score_history = Column(JSON, nullable=True)
    last_significant_change = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])


class SafetyReport(Base):
    """Safety reports for concerning user behavior"""
    __tablename__ = "safety_reports"

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reported_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Report details
    report_type = Column(String, nullable=False)  # harassment, inappropriate_content, fake_profile, etc.
    report_description = Column(Text, nullable=False)
    severity_level = Column(String, nullable=False)  # SafetyLevel enum
    
    # Evidence and context
    evidence_data = Column(JSON, nullable=True)
    connection_context = Column(JSON, nullable=True)
    message_references = Column(JSON, nullable=True)
    
    # Report status
    status = Column(String, default="open")  # open, investigating, resolved, dismissed
    priority_level = Column(String, default="normal")  # low, normal, high, urgent
    
    # Investigation
    assigned_to = Column(String, nullable=True)
    investigation_notes = Column(Text, nullable=True)
    resolution = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Actions taken
    immediate_actions = Column(JSON, nullable=True)
    final_actions = Column(JSON, nullable=True)
    
    # Anonymity and protection
    reporter_anonymous = Column(Boolean, default=False)
    reporter_protection_needed = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    reporter = relationship("User", foreign_keys=[reporter_id])
    reported_user = relationship("User", foreign_keys=[reported_user_id])


class CommunityInsight(Base):
    """Community insights and trends for platform improvement"""
    __tablename__ = "community_insights"

    id = Column(Integer, primary_key=True, index=True)
    
    # Insight details
    insight_type = Column(String, nullable=False)  # trust_trends, feedback_patterns, safety_analysis
    insight_title = Column(String, nullable=False)
    insight_description = Column(Text, nullable=False)
    
    # Insight data
    insight_data = Column(JSON, nullable=False)
    supporting_metrics = Column(JSON, nullable=True)
    confidence_level = Column(Float, nullable=False)
    
    # Actionability
    recommended_actions = Column(JSON, nullable=True)
    implementation_priority = Column(String, default="medium")
    
    # Visibility
    is_public = Column(Boolean, default=False)
    target_audience = Column(String, default="internal")  # internal, community, public
    
    # Metadata
    generated_by = Column(String, default="system")
    generation_method = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    
class UserSafetyScore(Base):
    """User safety scores based on reports and behavior"""
    __tablename__ = "user_safety_scores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Safety scores
    safety_score = Column(Float, default=1.0)  # 0.0 (unsafe) to 1.0 (very safe)
    risk_level = Column(String, default="low")  # low, medium, high, critical
    
    # Contributing factors
    report_count = Column(Integer, default=0)
    verified_report_count = Column(Integer, default=0)
    false_report_count = Column(Integer, default=0)
    
    # Behavioral indicators
    behavioral_flags = Column(JSON, nullable=True)
    positive_indicators = Column(JSON, nullable=True)
    
    # Actions and restrictions
    active_restrictions = Column(JSON, nullable=True)
    restriction_history = Column(JSON, nullable=True)
    
    # Review status
    under_review = Column(Boolean, default=False)
    last_reviewed_at = Column(DateTime, nullable=True)
    next_review_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])