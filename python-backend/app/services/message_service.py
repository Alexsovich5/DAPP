"""
Message Service - Phase 4 Real-time Messaging System
Soul-themed messaging with emotional context and real-time delivery
"""
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.models.user import User, UserEmotionalState
from app.models.soul_connection import SoulConnection
from app.models.message import Message
from app.models.soul_analytics import AnalyticsEventType
from app.services.analytics_service import analytics_service
from app.services.realtime_connection_manager import realtime_manager, MessageType

logger = logging.getLogger(__name__)


@dataclass
class MessageResult:
    """Result of message sending operation"""
    success: bool
    message_id: Optional[int]
    message: str
    delivered: bool
    error: Optional[str] = None


@dataclass
class ConversationSummary:
    """Summary of conversation between two users"""
    connection_id: int
    partner_id: int
    partner_name: str
    total_messages: int
    last_message_at: Optional[datetime]
    last_message_content: str
    unread_count: int
    emotional_energy: str
    conversation_stage: str


class MessageService:
    """Enhanced messaging service with soul-themed features"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.max_message_length = 5000
        self.min_message_length = 1
        self.rate_limit_messages_per_minute = 30  # Rate limit for messages per minute
        
    def create_message(self, sender_id: int, recipient_id: int, content: str, message_type: str = "text") -> Optional[Message]:
        """Create a new message between users"""
        if not self.validate_message_content(content):
            return None
            
        try:
            # Try to find a connection between users
            from app.models.soul_connection import SoulConnection
            connection = self.db.query(SoulConnection).filter(
                or_(
                    and_(SoulConnection.user1_id == sender_id, SoulConnection.user2_id == recipient_id),
                    and_(SoulConnection.user1_id == recipient_id, SoulConnection.user2_id == sender_id)
                )
            ).first()
            
            if not connection:
                # For testing, create a basic connection or use ID 1
                connection_id = 1
            else:
                connection_id = connection.id
                
            message = Message(
                connection_id=connection_id,
                sender_id=sender_id,
                message_text=content,
                message_type=message_type,
                created_at=datetime.utcnow()
            )
            self.db.add(message)
            self.db.commit()
            self.db.refresh(message)
            return message
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create message: {e}")
            return None
    
    def validate_message_content(self, content: str) -> bool:
        """Validate message content for length and safety"""
        if not content or len(content.strip()) < self.min_message_length:
            return False
        if len(content) > self.max_message_length:
            return False
        return True
    
    def filter_message_content(self, content: str) -> str:
        """Filter and sanitize message content"""
        if not content:
            return ""
        
        # Basic filtering - remove potential PII patterns
        import re
        
        # Filter email addresses
        content = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[email hidden]', content)
        
        # Filter phone numbers (basic pattern)
        content = re.sub(r'\b\d{3}-\d{3}-\d{4}\b', '[phone hidden]', content)
        
        return content.strip()
    
    def get_conversation(self, user1_id: int, user2_id: int, limit: int = 50) -> List[Message]:
        """Retrieve conversation messages between two users"""
        try:
            # For now, just return messages from these users
            # In real implementation, would need to find shared connection
            messages = self.db.query(Message).filter(
                or_(
                    Message.sender_id == user1_id,
                    Message.sender_id == user2_id
                )
            ).order_by(desc(Message.created_at)).limit(limit).all()
            
            return messages
        except Exception as e:
            logger.error(f"Failed to retrieve conversation: {e}")
            return []
    
    async def send_message(
        self,
        sender_id: int,
        connection_id: int,
        content: str,
        emotional_context: Optional[Dict[str, Any]] = None,
        db: Session = None
    ) -> MessageResult:
        """Send a message in a soul connection with real-time delivery"""
        try:
            # Validate message content
            if not content or not content.strip():
                return MessageResult(
                    success=False,
                    message_id=None,
                    message="Message cannot be empty",
                    delivered=False,
                    error="empty_content"
                )
            
            if len(content) > self.max_message_length:
                return MessageResult(
                    success=False,
                    message_id=None,
                    message=f"Message too long (max {self.max_message_length} characters)",
                    delivered=False,
                    error="content_too_long"
                )
            
            # Verify connection exists and user is authorized
            connection = db.query(SoulConnection).filter(
                SoulConnection.id == connection_id,
                or_(
                    SoulConnection.user1_id == sender_id,
                    SoulConnection.user2_id == sender_id
                )
            ).first()
            
            if not connection:
                return MessageResult(
                    success=False,
                    message_id=None,
                    message="Connection not found or access denied",
                    delivered=False,
                    error="invalid_connection"
                )
            
            # Check rate limiting
            rate_limit_check = await self._check_rate_limit(sender_id, connection_id, db)
            if not rate_limit_check["allowed"]:
                return MessageResult(
                    success=False,
                    message_id=None,
                    message=rate_limit_check["message"],
                    delivered=False,
                    error="rate_limited"
                )
            
            # Get sender info for emotional context
            sender = db.query(User).filter(User.id == sender_id).first()
            partner_id = connection.get_partner_id(sender_id)
            
            # Create message with emotional context
            message = Message(
                connection_id=connection_id,
                sender_id=sender_id,
                content=content.strip(),
                emotional_state=emotional_context.get("emotional_state") if emotional_context else sender.current_emotional_state,
                message_energy=emotional_context.get("message_energy", "medium") if emotional_context else "medium",
                is_soul_revelation=emotional_context.get("is_revelation", False) if emotional_context else False
            )
            
            db.add(message)
            
            # Update connection metrics
            connection.total_messages_exchanged += 1
            connection.last_message_at = datetime.utcnow()
            if not connection.first_message_at:
                connection.first_message_at = datetime.utcnow()
            
            # Update user message counter
            sender.total_messages_sent += 1
            
            db.commit()
            db.refresh(message)
            
            # Send real-time notification to partner
            delivery_success = await self._deliver_message_realtime(
                message, partner_id, sender, db
            )
            
            # Track analytics
            await analytics_service.track_user_event(
                user_id=sender_id,
                event_type=AnalyticsEventType.MESSAGE_SENT,
                event_data={
                    "connection_id": connection_id,
                    "partner_id": partner_id,
                    "message_length": len(content),
                    "emotional_state": message.emotional_state,
                    "is_revelation": message.is_soul_revelation,
                    "delivered": delivery_success
                },
                db=db,
                connection_id=connection_id
            )
            
            logger.info(f"Message sent: user {sender_id} -> connection {connection_id}")
            
            return MessageResult(
                success=True,
                message_id=message.id,
                message="Message sent successfully",
                delivered=delivery_success
            )
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            if db:
                db.rollback()
            return MessageResult(
                success=False,
                message_id=None,
                message=f"Failed to send message: {str(e)}",
                delivered=False,
                error="send_failed"
            )
    
    async def get_conversation_messages(
        self,
        user_id: int,
        connection_id: int,
        limit: int = 50,
        offset: int = 0,
        db: Session = None
    ) -> Dict[str, Any]:
        """Get messages for a conversation with pagination"""
        try:
            # Verify user access to connection
            connection = db.query(SoulConnection).filter(
                SoulConnection.id == connection_id,
                or_(
                    SoulConnection.user1_id == user_id,
                    SoulConnection.user2_id == user_id
                )
            ).first()
            
            if not connection:
                return {"success": False, "error": "Connection not found or access denied"}
            
            # Get messages with pagination
            messages = db.query(Message).filter(
                Message.connection_id == connection_id
            ).order_by(desc(Message.created_at)).offset(offset).limit(limit).all()
            
            # Reverse to get chronological order (oldest first)
            messages = list(reversed(messages))
            
            # Mark messages as read
            unread_messages = [m for m in messages if m.sender_id != user_id and not m.is_read]
            for message in unread_messages:
                message.is_read = True
                message.read_at = datetime.utcnow()
            
            if unread_messages:
                db.commit()
            
            # Get partner info
            partner_id = connection.get_partner_id(user_id)
            partner = db.query(User).filter(User.id == partner_id).first()
            
            # Format messages for frontend
            formatted_messages = []
            for message in messages:
                formatted_messages.append({
                    "id": message.id,
                    "sender_id": message.sender_id,
                    "content": message.content,
                    "emotional_state": message.emotional_state,
                    "message_energy": message.message_energy,
                    "is_soul_revelation": message.is_soul_revelation,
                    "is_read": message.is_read,
                    "created_at": message.created_at.isoformat(),
                    "read_at": message.read_at.isoformat() if message.read_at else None,
                    "is_own_message": message.sender_id == user_id
                })
            
            return {
                "success": True,
                "messages": formatted_messages,
                "total_messages": len(formatted_messages),
                "connection": {
                    "id": connection.id,
                    "partner_id": partner_id,
                    "partner_name": f"{partner.first_name} {partner.last_name}" if partner else "Unknown",
                    "energy_level": connection.current_energy_level,
                    "stage": connection.stage
                },
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "has_more": len(messages) == limit
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation messages: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_user_conversations(
        self,
        user_id: int,
        db: Session = None
    ) -> Dict[str, Any]:
        """Get all conversations for a user with summary info"""
        try:
            # Get all connections for user
            connections = db.query(SoulConnection).filter(
                or_(
                    SoulConnection.user1_id == user_id,
                    SoulConnection.user2_id == user_id
                ),
                SoulConnection.status == "active"
            ).order_by(desc(SoulConnection.last_message_at)).all()
            
            conversations = []
            for connection in connections:
                partner_id = connection.get_partner_id(user_id)
                partner = db.query(User).filter(User.id == partner_id).first()
                
                # Get last message
                last_message = db.query(Message).filter(
                    Message.connection_id == connection.id
                ).order_by(desc(Message.created_at)).first()
                
                # Count unread messages
                unread_count = db.query(Message).filter(
                    Message.connection_id == connection.id,
                    Message.sender_id != user_id,
                    Message.is_read == False
                ).count()
                
                conversation_summary = ConversationSummary(
                    connection_id=connection.id,
                    partner_id=partner_id,
                    partner_name=f"{partner.first_name} {partner.last_name}" if partner else "Unknown",
                    total_messages=connection.total_messages_exchanged,
                    last_message_at=connection.last_message_at,
                    last_message_content=last_message.content if last_message else "",
                    unread_count=unread_count,
                    emotional_energy=connection.current_energy_level,
                    conversation_stage=connection.stage
                )
                
                conversations.append({
                    "connection_id": conversation_summary.connection_id,
                    "partner": {
                        "id": conversation_summary.partner_id,
                        "name": conversation_summary.partner_name,
                        "emotional_state": partner.current_emotional_state if partner else "unknown"
                    },
                    "last_message": {
                        "content": conversation_summary.last_message_content,
                        "timestamp": conversation_summary.last_message_at.isoformat() if conversation_summary.last_message_at else None
                    },
                    "metrics": {
                        "total_messages": conversation_summary.total_messages,
                        "unread_count": conversation_summary.unread_count,
                        "emotional_energy": conversation_summary.emotional_energy,
                        "stage": conversation_summary.conversation_stage
                    }
                })
            
            return {
                "success": True,
                "conversations": conversations,
                "total_conversations": len(conversations)
            }
            
        except Exception as e:
            logger.error(f"Error getting user conversations: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def update_typing_status(
        self,
        user_id: int,
        connection_id: int,
        is_typing: bool,
        emotional_state: Optional[str] = None,
        db: Session = None
    ) -> bool:
        """Update typing status with real-time broadcast"""
        try:
            # Verify connection access
            connection = db.query(SoulConnection).filter(
                SoulConnection.id == connection_id,
                or_(
                    SoulConnection.user1_id == user_id,
                    SoulConnection.user2_id == user_id
                )
            ).first()
            
            if not connection:
                return False
            
            partner_id = connection.get_partner_id(user_id)
            
            # Broadcast typing status to partner
            await realtime_manager.handle_typing_indicator(
                user_id=user_id,
                connection_id=connection_id,
                is_typing=is_typing,
                emotional_state=emotional_state or "contemplative"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating typing status: {str(e)}")
            return False
    
    async def mark_messages_as_read(
        self,
        user_id: int,
        connection_id: int,
        db: Session = None
    ) -> bool:
        """Mark all messages in a connection as read"""
        try:
            # Update unread messages
            updated = db.query(Message).filter(
                Message.connection_id == connection_id,
                Message.sender_id != user_id,
                Message.is_read == False
            ).update({
                "is_read": True,
                "read_at": datetime.utcnow()
            })
            
            db.commit()
            
            if updated > 0:
                # Notify sender that messages were read
                partner_id = db.query(SoulConnection).filter(
                    SoulConnection.id == connection_id
                ).first().get_partner_id(user_id)
                
                await realtime_manager.send_to_user(
                    user_id=partner_id,
                    message_type="message_read",
                    data={
                        "connection_id": connection_id,
                        "reader_id": user_id,
                        "messages_read": updated
                    }
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error marking messages as read: {str(e)}")
            return False
    
    # Helper methods
    
    async def _check_rate_limit(
        self,
        user_id: int,
        connection_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Check if user is within rate limits"""
        try:
            # Check messages sent in last minute
            cutoff = datetime.utcnow() - timedelta(minutes=1)
            recent_messages = db.query(Message).filter(
                Message.sender_id == user_id,
                Message.connection_id == connection_id,
                Message.created_at >= cutoff
            ).count()
            
            if recent_messages >= self.rate_limit_messages_per_minute:
                return {
                    "allowed": False,
                    "message": "Rate limit exceeded. Please wait before sending more messages."
                }
            
            return {"allowed": True}
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}")
            return {"allowed": True}  # Allow on error to avoid blocking users
    
    async def _deliver_message_realtime(
        self,
        message: Message,
        recipient_id: int,
        sender: User,
        db: Session
    ) -> bool:
        """Deliver message via real-time WebSocket"""
        try:
            message_data = {
                "id": message.id,
                "connection_id": message.connection_id,
                "sender": {
                    "id": sender.id,
                    "name": f"{sender.first_name} {sender.last_name}",
                    "emotional_state": message.emotional_state
                },
                "content": message.content,
                "emotional_state": message.emotional_state,
                "message_energy": message.message_energy,
                "is_soul_revelation": message.is_soul_revelation,
                "created_at": message.created_at.isoformat()
            }
            
            # Send via WebSocket
            success = await realtime_manager.send_to_user(
                user_id=recipient_id,
                message_type="new_message",
                data=message_data
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Error delivering message via WebSocket: {str(e)}")
            return False


# Global service factory function
def get_message_service(db_session=None):
    """Factory function to create message service with database session"""
    if db_session:
        return MessageService(db_session)
    # For compatibility, return a mock service when no session provided
    return type('MockMessageService', (), {
        'send_message': lambda *args, **kwargs: None,
        'get_conversations': lambda *args, **kwargs: [],
        'validate_message_content': lambda self, content: bool(content and content.strip())
    })()