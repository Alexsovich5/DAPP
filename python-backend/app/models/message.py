import enum
from datetime import datetime

from app.core.database import Base
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship


class MessageType(str, enum.Enum):
    TEXT = "text"
    REVELATION = "revelation"
    PHOTO = "photo"
    SYSTEM = "system"


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    connection_id = Column(Integer, ForeignKey("soul_connections.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Message content
    message_text = Column(Text, nullable=False)
    message_type = Column(String, default=MessageType.TEXT)

    # Message metadata
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    connection = relationship("SoulConnection", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
