"""
Real-time Connection Manager - Phase 4 Enhanced
Handles WebSocket connections, presence tracking, and live state management
"""
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from enum import Enum

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.database import get_db
from app.models.user import User, UserEmotionalState
from app.models.soul_connection import SoulConnection, ConnectionEnergyLevel
from app.models.realtime_state import (
    UserPresence, ConnectionRealTimeState, LiveTypingSession,
    RealtimeNotification, WebSocketConnection, UserPresenceStatus
)
from app.models.soul_analytics import UserEngagementAnalytics, AnalyticsEventType

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Types of real-time messages"""
    # Presence
    PRESENCE_UPDATE = "presence_update"
    USER_ONLINE = "user_online"
    USER_OFFLINE = "user_offline"
    
    # Typing indicators
    TYPING_START = "typing_start"
    TYPING_STOP = "typing_stop"
    TYPING_UPDATE = "typing_update"
    
    # Connection updates
    CONNECTION_UPDATE = "connection_update"
    ENERGY_CHANGE = "energy_change"
    STAGE_PROGRESSION = "stage_progression"
    
    # Notifications
    NEW_MESSAGE = "new_message"
    NEW_REVELATION = "new_revelation"
    PHOTO_CONSENT = "photo_consent"
    CELEBRATION = "celebration"
    
    # System
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    CONNECTED = "connected"


@dataclass
class RealtimeMessage:
    """Structure for real-time messages"""
    type: MessageType
    data: Dict
    target_user_id: Optional[int] = None
    connection_id: Optional[int] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict:
        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "connectionId": self.connection_id
        }


class RealtimeConnectionManager:
    """Manages WebSocket connections and real-time features"""
    
    def __init__(self):
        # Active WebSocket connections: user_id -> WebSocket
        self.active_connections: Dict[int, WebSocket] = {}
        
        # User presence tracking
        self.user_presence: Dict[int, UserPresenceStatus] = {}
        
        # Typing sessions: connection_id -> {user_id: session_data}
        self.typing_sessions: Dict[int, Dict[int, Dict]] = {}
        
        # Connection subscribers: connection_id -> set of user_ids
        self.connection_subscribers: Dict[int, Set[int]] = {}
        
        # Message queues for offline users
        self.offline_message_queue: Dict[int, List[RealtimeMessage]] = {}
        
        logger.info("Real-time Connection Manager initialized")
    
    async def connect(self, websocket: WebSocket, user_id: int, db: Session):
        """Handle new WebSocket connection"""
        try:
            await websocket.accept()
            
            # Store connection
            self.active_connections[user_id] = websocket
            
            # Update presence
            await self.update_user_presence(user_id, UserPresenceStatus.ONLINE, db)
            
            # Send connection confirmation
            await self.send_to_user(user_id, RealtimeMessage(
                type=MessageType.CONNECTED,
                data={"userId": user_id, "status": "connected"}
            ))
            
            # Send any queued messages
            await self.send_queued_messages(user_id)
            
            # Notify connections about user coming online
            await self.notify_user_connections(user_id, MessageType.USER_ONLINE, db)
            
            logger.info(f"User {user_id} connected to real-time system")
            
        except Exception as e:
            logger.error(f"Error connecting user {user_id}: {str(e)}")
            raise
    
    async def disconnect(self, user_id: int, db: Session):
        """Handle WebSocket disconnection"""
        try:
            # Remove connection
            if user_id in self.active_connections:
                del self.active_connections[user_id]
            
            # Update presence
            await self.update_user_presence(user_id, UserPresenceStatus.OFFLINE, db)
            
            # Stop any typing sessions
            await self.stop_all_typing_sessions(user_id, db)
            
            # Notify connections about user going offline
            await self.notify_user_connections(user_id, MessageType.USER_OFFLINE, db)
            
            logger.info(f"User {user_id} disconnected from real-time system")
            
        except Exception as e:
            logger.error(f"Error disconnecting user {user_id}: {str(e)}")
    
    async def send_to_user(self, user_id: int, message: RealtimeMessage):
        """Send message to a specific user"""
        websocket = self.active_connections.get(user_id)
        
        if websocket:
            try:
                await websocket.send_text(json.dumps(message.to_dict()))
                return True
            except Exception as e:
                logger.error(f"Error sending message to user {user_id}: {str(e)}")
                # Remove stale connection
                if user_id in self.active_connections:
                    del self.active_connections[user_id]
                return False
        else:
            # Queue message for offline user
            if user_id not in self.offline_message_queue:
                self.offline_message_queue[user_id] = []
            self.offline_message_queue[user_id].append(message)
            return False
    
    async def send_to_connection(self, connection_id: int, message: RealtimeMessage, exclude_user: Optional[int] = None):
        """Send message to all users in a connection"""
        subscribers = self.connection_subscribers.get(connection_id, set())
        
        for user_id in subscribers:
            if exclude_user and user_id == exclude_user:
                continue
            
            message.connection_id = connection_id
            await self.send_to_user(user_id, message)
    
    async def subscribe_to_connection(self, user_id: int, connection_id: int):
        """Subscribe user to connection updates"""
        if connection_id not in self.connection_subscribers:
            self.connection_subscribers[connection_id] = set()
        
        self.connection_subscribers[connection_id].add(user_id)
        logger.debug(f"User {user_id} subscribed to connection {connection_id}")
    
    async def unsubscribe_from_connection(self, user_id: int, connection_id: int):
        """Unsubscribe user from connection updates"""
        if connection_id in self.connection_subscribers:
            self.connection_subscribers[connection_id].discard(user_id)
            
            # Clean up empty subscriptions
            if not self.connection_subscribers[connection_id]:
                del self.connection_subscribers[connection_id]
        
        logger.debug(f"User {user_id} unsubscribed from connection {connection_id}")
    
    async def start_typing(self, user_id: int, connection_id: int, typing_data: Dict, db: Session):
        """Handle user starting to type"""
        try:
            # Get connection to verify access
            connection = db.query(SoulConnection).filter(
                SoulConnection.id == connection_id,
                or_(SoulConnection.user1_id == user_id, SoulConnection.user2_id == user_id),
                SoulConnection.status == "active"
            ).first()
            
            if not connection:
                return False
            
            # Store typing session
            if connection_id not in self.typing_sessions:
                self.typing_sessions[connection_id] = {}
            
            self.typing_sessions[connection_id][user_id] = {
                "started_at": datetime.utcnow(),
                "energy_level": typing_data.get("energyLevel", ConnectionEnergyLevel.MEDIUM),
                "emotional_state": typing_data.get("emotionalState", UserEmotionalState.CONTEMPLATIVE),
                "message_type": typing_data.get("messageType", "text")
            }
            
            # Update database
            await self.update_user_presence(user_id, UserPresenceStatus.TYPING, db, connection_id)
            
            # Notify partner
            partner_id = connection.get_partner_id(user_id)
            await self.send_to_user(partner_id, RealtimeMessage(
                type=MessageType.TYPING_START,
                connection_id=connection_id,
                data={
                    "userId": user_id,
                    "energyLevel": typing_data.get("energyLevel", ConnectionEnergyLevel.MEDIUM),
                    "emotionalState": typing_data.get("emotionalState", UserEmotionalState.CONTEMPLATIVE),
                    "connectionStage": connection.connection_stage
                }
            ))
            
            # Track analytics
            await self.track_engagement_event(
                user_id, AnalyticsEventType.TYPING_INDICATOR_SHOWN, 
                {"connection_id": connection_id}, db
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting typing session: {str(e)}")
            return False
    
    async def stop_typing(self, user_id: int, connection_id: int, db: Session):
        """Handle user stopping typing"""
        try:
            # Remove typing session
            if connection_id in self.typing_sessions:
                if user_id in self.typing_sessions[connection_id]:
                    session_data = self.typing_sessions[connection_id][user_id]
                    del self.typing_sessions[connection_id][user_id]
                    
                    # Clean up empty connections
                    if not self.typing_sessions[connection_id]:
                        del self.typing_sessions[connection_id]
                    
                    # Update presence
                    await self.update_user_presence(user_id, UserPresenceStatus.ONLINE, db)
                    
                    # Get connection for partner notification
                    connection = db.query(SoulConnection).filter(
                        SoulConnection.id == connection_id,
                        or_(SoulConnection.user1_id == user_id, SoulConnection.user2_id == user_id)
                    ).first()
                    
                    if connection:
                        partner_id = connection.get_partner_id(user_id)
                        await self.send_to_user(partner_id, RealtimeMessage(
                            type=MessageType.TYPING_STOP,
                            connection_id=connection_id,
                            data={"userId": user_id}
                        ))
            
            return True
            
        except Exception as e:
            logger.error(f"Error stopping typing session: {str(e)}")
            return False
    
    async def update_connection_energy(self, connection_id: int, new_energy: ConnectionEnergyLevel, db: Session):
        """Update connection energy level and notify users"""
        try:
            connection = db.query(SoulConnection).filter(
                SoulConnection.id == connection_id
            ).first()
            
            if not connection:
                return False
            
            # Update energy
            old_energy = connection.current_energy_level
            connection.current_energy_level = new_energy
            connection.last_activity_at = datetime.utcnow()
            
            # Update energy history
            if not connection.energy_history:
                connection.energy_history = []
            
            connection.energy_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "old_energy": old_energy,
                "new_energy": new_energy
            })
            
            db.commit()
            
            # Notify both users
            await self.send_to_connection(connection_id, RealtimeMessage(
                type=MessageType.ENERGY_CHANGE,
                data={
                    "oldEnergy": old_energy,
                    "newEnergy": new_energy,
                    "timestamp": datetime.utcnow().isoformat()
                }
            ))
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating connection energy: {str(e)}")
            db.rollback()
            return False
    
    async def trigger_celebration(self, connection_id: int, celebration_type: str, data: Dict, db: Session):
        """Trigger celebration animation for both users"""
        try:
            await self.send_to_connection(connection_id, RealtimeMessage(
                type=MessageType.CELEBRATION,
                data={
                    "celebrationType": celebration_type,
                    "animationData": data,
                    "timestamp": datetime.utcnow().isoformat()
                }
            ))
            
            # Track analytics
            connection = db.query(SoulConnection).filter(
                SoulConnection.id == connection_id
            ).first()
            
            if connection:
                for user_id in [connection.user1_id, connection.user2_id]:
                    await self.track_engagement_event(
                        user_id, AnalyticsEventType.ANIMATION_VIEWED,
                        {
                            "connection_id": connection_id,
                            "animation_type": celebration_type,
                            "data": data
                        }, db
                    )
            
            return True
            
        except Exception as e:
            logger.error(f"Error triggering celebration: {str(e)}")
            return False
    
    async def notify_new_revelation(self, connection_id: int, sender_id: int, revelation_data: Dict, db: Session):
        """Notify about new revelation sharing"""
        try:
            connection = db.query(SoulConnection).filter(
                SoulConnection.id == connection_id
            ).first()
            
            if not connection:
                return False
            
            # Get partner
            partner_id = connection.get_partner_id(sender_id)
            
            # Send notification to partner
            await self.send_to_user(partner_id, RealtimeMessage(
                type=MessageType.NEW_REVELATION,
                connection_id=connection_id,
                data={
                    "senderId": sender_id,
                    "dayNumber": revelation_data.get("dayNumber"),
                    "revelationType": revelation_data.get("revelationType"),
                    "timestamp": datetime.utcnow().isoformat()
                }
            ))
            
            # Update connection energy (revelations increase energy)
            if connection.current_energy_level == ConnectionEnergyLevel.LOW:
                await self.update_connection_energy(connection_id, ConnectionEnergyLevel.MEDIUM, db)
            elif connection.current_energy_level == ConnectionEnergyLevel.MEDIUM:
                await self.update_connection_energy(connection_id, ConnectionEnergyLevel.HIGH, db)
            
            return True
            
        except Exception as e:
            logger.error(f"Error notifying new revelation: {str(e)}")
            return False
    
    async def handle_message(self, user_id: int, message_data: Dict, db: Session):
        """Handle incoming WebSocket message"""
        try:
            message_type = MessageType(message_data.get("type"))
            data = message_data.get("data", {})
            connection_id = message_data.get("connectionId")
            
            if message_type == MessageType.TYPING_START:
                return await self.start_typing(user_id, connection_id, data, db)
            
            elif message_type == MessageType.TYPING_STOP:
                return await self.stop_typing(user_id, connection_id, db)
            
            elif message_type == MessageType.HEARTBEAT:
                # Update last seen
                await self.update_user_presence(user_id, UserPresenceStatus.ONLINE, db)
                return True
            
            elif message_type == MessageType.CONNECTION_UPDATE:
                # Subscribe to connection updates
                if connection_id:
                    await self.subscribe_to_connection(user_id, connection_id)
                return True
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error handling message from user {user_id}: {str(e)}")
            return False
    
    async def update_user_presence(self, user_id: int, status: UserPresenceStatus, 
                                 db: Session, connection_id: Optional[int] = None):
        """Update user presence in database"""
        try:
            presence = db.query(UserPresence).filter(
                UserPresence.user_id == user_id
            ).first()
            
            if not presence:
                presence = UserPresence(
                    user_id=user_id,
                    status=status,
                    last_seen=datetime.utcnow()
                )
                db.add(presence)
            else:
                presence.status = status
                presence.last_seen = datetime.utcnow()
                
                if status == UserPresenceStatus.TYPING and connection_id:
                    presence.is_typing = True
                    presence.typing_in_connection = connection_id
                    presence.typing_started_at = datetime.utcnow()
                else:
                    presence.is_typing = False
                    presence.typing_in_connection = None
                    presence.typing_started_at = None
            
            db.commit()
            self.user_presence[user_id] = status
            
        except Exception as e:
            logger.error(f"Error updating user presence: {str(e)}")
            db.rollback()
    
    async def stop_all_typing_sessions(self, user_id: int, db: Session):
        """Stop all typing sessions for a user"""
        connections_to_update = []
        
        for connection_id, sessions in self.typing_sessions.items():
            if user_id in sessions:
                connections_to_update.append(connection_id)
        
        for connection_id in connections_to_update:
            await self.stop_typing(user_id, connection_id, db)
    
    async def notify_user_connections(self, user_id: int, message_type: MessageType, db: Session):
        """Notify all connections about user presence change"""
        try:
            # Get user's active connections
            connections = db.query(SoulConnection).filter(
                or_(SoulConnection.user1_id == user_id, SoulConnection.user2_id == user_id),
                SoulConnection.status == "active"
            ).all()
            
            for connection in connections:
                partner_id = connection.get_partner_id(user_id)
                
                await self.send_to_user(partner_id, RealtimeMessage(
                    type=message_type,
                    connection_id=connection.id,
                    data={
                        "userId": user_id,
                        "status": self.user_presence.get(user_id, UserPresenceStatus.OFFLINE).value
                    }
                ))
                
        except Exception as e:
            logger.error(f"Error notifying user connections: {str(e)}")
    
    async def send_queued_messages(self, user_id: int):
        """Send queued messages to newly connected user"""
        if user_id in self.offline_message_queue:
            messages = self.offline_message_queue[user_id]
            
            for message in messages:
                await self.send_to_user(user_id, message)
            
            # Clear queue
            del self.offline_message_queue[user_id]
    
    async def track_engagement_event(self, user_id: int, event_type: AnalyticsEventType, 
                                   event_data: Dict, db: Session):
        """Track user engagement event"""
        try:
            analytics_event = UserEngagementAnalytics(
                user_id=user_id,
                event_type=event_type.value,
                event_data=event_data,
                created_at=datetime.utcnow()
            )
            
            db.add(analytics_event)
            db.commit()
            
        except Exception as e:
            logger.error(f"Error tracking engagement event: {str(e)}")
            db.rollback()
    
    async def cleanup_stale_sessions(self, db: Session):
        """Clean up stale typing sessions and presence data"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=5)
            
            # Clean up typing sessions older than 5 minutes
            for connection_id, sessions in list(self.typing_sessions.items()):
                for user_id, session_data in list(sessions.items()):
                    if session_data["started_at"] < cutoff_time:
                        await self.stop_typing(user_id, connection_id, db)
            
            # Update stale presence records
            stale_presence = db.query(UserPresence).filter(
                UserPresence.last_seen < cutoff_time,
                UserPresence.status != UserPresenceStatus.OFFLINE
            ).all()
            
            for presence in stale_presence:
                if presence.user_id not in self.active_connections:
                    presence.status = UserPresenceStatus.OFFLINE
                    presence.is_typing = False
                    presence.typing_in_connection = None
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error cleaning up stale sessions: {str(e)}")
            db.rollback()
    
    def get_connection_stats(self) -> Dict:
        """Get real-time system statistics"""
        return {
            "active_connections": len(self.active_connections),
            "typing_sessions": sum(len(sessions) for sessions in self.typing_sessions.values()),
            "connection_subscribers": len(self.connection_subscribers),
            "queued_messages": sum(len(queue) for queue in self.offline_message_queue.values()),
            "user_presence_tracked": len(self.user_presence)
        }


# Global instance
realtime_manager = RealtimeConnectionManager()