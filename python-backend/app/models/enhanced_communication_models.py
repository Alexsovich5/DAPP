"""
Phase 7: Enhanced Communication Models
Database models for advanced real-time communication features
"""
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, DECIMAL, Float, ForeignKey, LargeBinary
from sqlalchemy.orm import relationship

from app.core.database import Base


class MessageType(str, enum.Enum):
    """Types of messages in the enhanced communication system"""
    TEXT = "text"
    VOICE = "voice"
    VIDEO = "video"
    IMAGE = "image"
    REVELATION = "revelation"
    SYSTEM = "system"
    SMART_REPLY = "smart_reply"


class EmotionalTone(str, enum.Enum):
    """Emotional tones detected in messages"""
    JOYFUL = "joyful"
    EXCITED = "excited"
    CONTEMPLATIVE = "contemplative"
    ROMANTIC = "romantic"
    NERVOUS = "nervous"
    CONFIDENT = "confident"
    VULNERABLE = "vulnerable"
    PLAYFUL = "playful"
    SUPPORTIVE = "supportive"
    CURIOUS = "curious"
    NEUTRAL = "neutral"


class CallStatus(str, enum.Enum):
    """Video call session statuses"""
    INITIATED = "initiated"
    RINGING = "ringing"
    ACTIVE = "active"
    ENDED = "ended"
    MISSED = "missed"
    DECLINED = "declined"
    TECHNICAL_ISSUE = "technical_issue"


class ReactionType(str, enum.Enum):
    """Message reaction types"""
    LOVE = "love"
    LIKE = "like"
    LAUGH = "laugh"
    SURPRISED = "surprised"
    THOUGHTFUL = "thoughtful"
    SUPPORTIVE = "supportive"


class EnhancedMessage(Base):
    """Enhanced messages with AI analysis and emotional intelligence"""
    __tablename__ = "enhanced_messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    connection_id = Column(Integer, ForeignKey("soul_connections.id"), nullable=False)
    
    # Message content
    message_type = Column(String, default=MessageType.TEXT.value)
    content_text = Column(Text, nullable=True)
    attachment_data = Column(JSON, nullable=True)
    
    # AI Analysis
    emotional_tone = Column(String, nullable=True)  # EmotionalTone enum
    sentiment_score = Column(Float, nullable=True)  # -1.0 to 1.0
    ai_insights = Column(JSON, nullable=True)
    personalization_applied = Column(JSON, nullable=True)
    
    # Conversation context
    conversation_context = Column(JSON, nullable=True)
    message_depth_score = Column(Float, nullable=True)
    vulnerability_level = Column(Float, nullable=True)
    connection_building_score = Column(Float, nullable=True)
    
    # Delivery and engagement
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    engagement_score = Column(Float, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id])
    connection = relationship("SoulConnection", foreign_keys=[connection_id])
    reactions = relationship("MessageReaction", back_populates="message")
    smart_replies = relationship("SmartReply", back_populates="original_message")


class VoiceMessage(Base):
    """Voice messages with emotion analysis"""
    __tablename__ = "voice_messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    connection_id = Column(Integer, ForeignKey("soul_connections.id"), nullable=False)
    
    # Audio file details
    audio_file_path = Column(String, nullable=False)
    duration_seconds = Column(Float, nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    audio_format = Column(String, default="wav")
    
    # Voice analysis
    transcription = Column(Text, nullable=True)
    emotional_tone = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=True)
    emotional_metadata = Column(JSON, nullable=True)
    
    # Voice characteristics
    voice_characteristics = Column(JSON, nullable=True)  # pace, tone, clarity
    authenticity_score = Column(Float, nullable=True)
    engagement_indicators = Column(JSON, nullable=True)
    
    # Processing status
    processed = Column(Boolean, default=False)
    processing_error = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id])
    connection = relationship("SoulConnection", foreign_keys=[connection_id])


class VideoCallSession(Base):
    """Video call sessions for face-to-face interactions"""
    __tablename__ = "video_call_sessions"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("soul_connections.id"), nullable=False)
    initiator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Call details
    call_type = Column(String, default="revelation_reveal")  # revelation_reveal, casual_chat
    status = Column(String, default=CallStatus.INITIATED.value)
    call_token = Column(String, nullable=True)  # Secure token for call access
    
    # Scheduling
    scheduled_time = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    actual_duration_seconds = Column(Integer, nullable=True)
    
    # Call metadata
    call_metadata = Column(JSON, nullable=True)
    preparation_insights = Column(JSON, nullable=True)
    call_quality_score = Column(Float, nullable=True)
    
    # Technical details
    webrtc_session_id = Column(String, nullable=True)
    connection_quality = Column(JSON, nullable=True)
    technical_issues = Column(JSON, nullable=True)
    
    # Post-call analysis
    call_satisfaction = Column(JSON, nullable=True)  # Both users' satisfaction
    follow_up_generated = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    connection = relationship("SoulConnection", foreign_keys=[connection_id])
    initiator = relationship("User", foreign_keys=[initiator_id])


class SmartReply(Base):
    """AI-generated smart reply suggestions"""
    __tablename__ = "smart_replies"

    id = Column(Integer, primary_key=True, index=True)
    original_message_id = Column(Integer, ForeignKey("enhanced_messages.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Reply content
    suggested_text = Column(Text, nullable=False)
    reply_type = Column(String, nullable=False)  # emotional_support, curiosity, validation, etc.
    confidence_score = Column(Float, nullable=False)
    
    # Context and personalization
    generation_context = Column(JSON, nullable=True)
    personalization_factors = Column(JSON, nullable=True)
    
    # Usage tracking
    was_used = Column(Boolean, default=False)
    was_modified = Column(Boolean, default=False)
    final_message_text = Column(Text, nullable=True)
    
    # Performance metrics
    user_rating = Column(Integer, nullable=True)  # 1-5 rating
    effectiveness_score = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    used_at = Column(DateTime, nullable=True)
    
    # Relationships
    original_message = relationship("EnhancedMessage", back_populates="smart_replies")
    recipient = relationship("User", foreign_keys=[recipient_id])


class MessageReaction(Base):
    """Reactions to messages (likes, loves, etc.)"""
    __tablename__ = "message_reactions"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("enhanced_messages.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    reaction_type = Column(String, nullable=False)  # ReactionType enum
    emotional_context = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    message = relationship("EnhancedMessage", back_populates="reactions")
    user = relationship("User", foreign_keys=[user_id])


class ConversationInsight(Base):
    """AI-generated insights about conversations"""
    __tablename__ = "conversation_insights"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("soul_connections.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    insight_type = Column(String, nullable=False)  # comprehensive_analysis, trend_analysis, etc.
    insights_data = Column(JSON, nullable=False)
    suggestions = Column(JSON, nullable=True)
    
    confidence_score = Column(Float, nullable=False)
    relevance_score = Column(Float, nullable=True)
    
    # User interaction with insights
    viewed_at = Column(DateTime, nullable=True)
    user_feedback = Column(JSON, nullable=True)
    acted_upon = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    # Relationships
    connection = relationship("SoulConnection", foreign_keys=[connection_id])
    user = relationship("User", foreign_keys=[user_id])


class CommunicationPattern(Base):
    """User communication patterns learned from interactions"""
    __tablename__ = "communication_patterns"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Communication style analysis
    preferred_style = Column(String, nullable=True)  # casual, formal, playful, balanced
    response_time_pattern = Column(String, nullable=True)  # fast, medium, slow, varied
    message_length_preference = Column(String, nullable=True)  # short, medium, long, varied
    
    # Emotional patterns
    emotional_expression_style = Column(JSON, nullable=True)
    vulnerability_comfort_level = Column(Float, nullable=True)
    emotional_reciprocity_score = Column(Float, nullable=True)
    
    # Conversation patterns
    topic_preferences = Column(JSON, nullable=True)
    question_asking_frequency = Column(Float, nullable=True)
    deep_conversation_comfort = Column(Float, nullable=True)
    
    # Engagement patterns
    peak_activity_hours = Column(JSON, nullable=True)
    conversation_initiation_rate = Column(Float, nullable=True)
    sustaining_conversation_ability = Column(Float, nullable=True)
    
    # Learning metadata
    pattern_confidence = Column(Float, nullable=False, default=0.5)
    data_points_analyzed = Column(Integer, default=0)
    last_pattern_update = Column(DateTime, default=datetime.utcnow)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])