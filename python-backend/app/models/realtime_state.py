"""
Real-time State Models - Phase 4 Enhanced Real-time Features  
Support typing indicators, presence, and live connection states
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import enum
from app.core.database import Base


class UserPresenceStatus(str, enum.Enum):
    """User presence states for real-time features"""
    ONLINE = "online"
    AWAY = "away"
    TYPING = "typing"
    OFFLINE = "offline"


class ConnectionEnergyLevel(str, enum.Enum):
    """Energy levels for soul connections"""
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    SOULMATE = "soulmate"


class UserPresence(Base):
    """Track real-time user presence and activity"""
    __tablename__ = "user_presence"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Presence state
    status = Column(String, default=UserPresenceStatus.OFFLINE)
    last_seen = Column(DateTime, default=datetime.utcnow)
    
    # Session info
    session_id = Column(String, nullable=True)
    device_type = Column(String, nullable=True)  # mobile, tablet, desktop
    socket_id = Column(String, nullable=True)  # WebSocket connection ID
    
    # Activity context
    current_screen = Column(String, nullable=True)  # discover, messages, profile
    active_connection_id = Column(Integer, ForeignKey("soul_connections.id"), nullable=True)
    
    # Typing indicators
    is_typing = Column(Boolean, default=False)
    typing_in_connection = Column(Integer, ForeignKey("soul_connections.id"), nullable=True)
    typing_started_at = Column(DateTime, nullable=True)
    
    # Updated automatically
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    active_connection = relationship("SoulConnection", foreign_keys=[active_connection_id])
    typing_connection = relationship("SoulConnection", foreign_keys=[typing_in_connection])


class ConnectionRealTimeState(Base):
    """Track real-time state of soul connections"""
    __tablename__ = "connection_realtime_state"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("soul_connections.id"), nullable=False, unique=True)
    
    # Energy and mood
    current_energy_level = Column(String, default=ConnectionEnergyLevel.MEDIUM)
    mood_indicators = Column(JSON, nullable=True)  # Store mood/emotional indicators
    
    # Activity tracking
    last_message_at = Column(DateTime, nullable=True)
    last_revelation_at = Column(DateTime, nullable=True) 
    message_frequency_24h = Column(Integer, default=0)
    
    # Real-time interaction
    active_users_count = Column(Integer, default=0)  # How many users currently viewing
    typing_users = Column(JSON, nullable=True)  # Array of user IDs currently typing
    
    # Connection health
    health_score = Column(Integer, default=100)  # 0-100 connection health
    warning_flags = Column(JSON, nullable=True)  # Array of potential issues
    
    # Celebration tracking
    celebration_animations_shown = Column(JSON, nullable=True)
    milestone_achievements = Column(JSON, nullable=True)
    
    # Updated tracking
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    connection = relationship("SoulConnection", foreign_keys=[connection_id])


class LiveTypingSession(Base):
    """Track live typing sessions for advanced indicators"""
    __tablename__ = "live_typing_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    connection_id = Column(Integer, ForeignKey("soul_connections.id"), nullable=False)
    
    # Session details
    session_start = Column(DateTime, default=datetime.utcnow)
    session_end = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Typing patterns (for soul-themed indicators)
    typing_speed_wpm = Column(Integer, nullable=True)
    pause_count = Column(Integer, default=0)
    backspace_count = Column(Integer, default=0)
    emotional_intensity = Column(String, nullable=True)  # calm, excited, thoughtful
    
    # Message context
    estimated_message_length = Column(Integer, nullable=True)
    message_type = Column(String, nullable=True)  # text, revelation, question
    
    # Soul energy indicators
    energy_level = Column(String, default=ConnectionEnergyLevel.MEDIUM)
    breathing_animation_speed = Column(Integer, default=1)  # multiplier
    particle_count = Column(Integer, default=5)
    
    # Final outcome
    message_sent = Column(Boolean, default=False)
    final_message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    was_cancelled = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    connection = relationship("SoulConnection", foreign_keys=[connection_id])
    final_message = relationship("Message", foreign_keys=[final_message_id])


class RealtimeNotification(Base):
    """Store real-time notifications for users"""
    __tablename__ = "realtime_notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Notification details
    notification_type = Column(String, nullable=False)  # message, revelation, match, etc.
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    
    # Visual styling
    icon = Column(String, nullable=True)  # emoji or icon name
    color_theme = Column(String, nullable=True)  # energy level color
    animation_type = Column(String, nullable=True)  # breathe, pulse, sparkle
    
    # Interaction data
    action_data = Column(JSON, nullable=True)  # Data for notification actions
    deep_link = Column(String, nullable=True)  # Where to navigate when clicked
    
    # Delivery tracking
    is_delivered = Column(Boolean, default=False)
    is_read = Column(Boolean, default=False)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    
    # Expiration
    expires_at = Column(DateTime, nullable=True)
    
    # Priority and grouping
    priority = Column(String, default="normal")  # low, normal, high, urgent
    group_key = Column(String, nullable=True)  # For grouping similar notifications
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])


class WebSocketConnection(Base):
    """Track active WebSocket connections for real-time features"""
    __tablename__ = "websocket_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Connection details
    socket_id = Column(String, nullable=False, unique=True)
    session_id = Column(String, nullable=True)
    
    # Client info
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)  # Hashed for privacy
    device_info = Column(JSON, nullable=True)
    
    # Connection state
    is_active = Column(Boolean, default=True)
    last_ping = Column(DateTime, default=datetime.utcnow)
    
    # Subscriptions (what real-time events user wants)
    subscribed_connections = Column(JSON, nullable=True)  # Connection IDs
    subscribed_channels = Column(JSON, nullable=True)  # General channels
    
    # Performance tracking
    messages_sent = Column(Integer, default=0)
    messages_received = Column(Integer, default=0)
    connection_quality = Column(String, default="good")  # good, fair, poor
    
    # Timing
    connected_at = Column(DateTime, default=datetime.utcnow)
    disconnected_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])


class AnimationEvent(Base):
    """Track animation events for analytics and performance"""
    __tablename__ = "animation_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    connection_id = Column(Integer, ForeignKey("soul_connections.id"), nullable=True)
    
    # Animation details
    animation_type = Column(String, nullable=False)  # breathe, pulse, sparkle, etc.
    energy_level = Column(String, nullable=False)
    trigger_event = Column(String, nullable=False)  # typing, match, revelation, etc.
    
    # Performance data
    duration_ms = Column(Integer, nullable=True)
    frame_rate = Column(Integer, nullable=True)
    was_completed = Column(Boolean, default=True)
    
    # Device context
    device_type = Column(String, nullable=True)
    screen_size = Column(String, nullable=True)
    reduced_motion = Column(Boolean, default=False)
    
    # User engagement
    user_interacted = Column(Boolean, default=False)  # Did user tap/interact during animation
    emotional_response = Column(String, nullable=True)  # Inferred from subsequent actions
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    connection = relationship("SoulConnection", foreign_keys=[connection_id])