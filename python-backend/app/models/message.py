from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class MessageType(str, enum.Enum):
    TEXT = "text"
    REVELATION = "revelation"
    PHOTO = "photo"
    SYSTEM = "system"


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("soul_connections.id"), nullable=False, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Message content
    message_text = Column(Text, nullable=False)
    message_type = Column(String, default=MessageType.TEXT, index=True)
    
    # Message metadata
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    connection = relationship("SoulConnection", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])

    # Performance indexes for common queries
    __table_args__ = (
        Index('ix_messages_connection_created', 'connection_id', 'created_at'),
        Index('ix_messages_sender_unread', 'sender_id', 'is_read'),
        Index('ix_messages_connection_unread', 'connection_id', 'is_read'),
        Index('ix_messages_connection_type_created', 'connection_id', 'message_type', 'created_at'),
    )