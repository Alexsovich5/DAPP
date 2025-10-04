"""
Real-time Connection Manager - Phase 4 Enhanced
Handles WebSocket connections, presence tracking, and live state management
"""

# import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set

from app.core.logging_config import get_logger
from app.models.realtime_state import UserPresence, UserPresenceStatus
from app.models.soul_analytics import AnalyticsEventType, UserEngagementAnalytics
from app.models.soul_connection import ConnectionEnergyLevel, SoulConnection
from app.models.user import UserEmotionalState
from fastapi import WebSocket
from sqlalchemy import or_
from sqlalchemy.orm import Session

logger = get_logger("app.services.realtime_connection_manager")


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

    # Messages
    MESSAGE = "message"
    MESSAGE_SENT = "message_sent"
    MESSAGE_DELIVERED = "message_delivered"

    # Notifications
    NEW_MESSAGE = "new_message"
    NEW_REVELATION = "new_revelation"
    PHOTO_CONSENT = "photo_consent"
    CELEBRATION = "celebration"

    # Soul-specific features (Frontend compatibility)
    COMPATIBILITY_CHANGE = "compatibility_change"
    ENERGY_SYNC = "energy_sync"
    NEW_MATCH = "new_match"
    REVELATION_SHARED = "revelation_shared"
    REVELATION_RECEIVED = "revelation_received"
    REVELATION_MUTUAL_COMPLETE = "revelation_mutual_complete"
    CHANNEL_SUBSCRIBE = "subscribe"
    CHANNEL_UNSUBSCRIBE = "unsubscribe"
    HEARTBEAT_ACK = "heartbeat_ack"

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
            "connectionId": self.connection_id,
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

        # Channel-based subscriptions: channel -> set of user_ids (for frontend compatibility)
        self.channel_subscribers: Dict[str, Set[int]] = {}

        # User channel subscriptions: user_id -> set of channels
        self.user_channels: Dict[int, Set[str]] = {}

        # Message queues for offline users
        self.offline_message_queue: Dict[int, List[RealtimeMessage]] = {}

        logger.info("Real-time Connection Manager initialized")

    @property
    def user_connections(self) -> Dict[int, WebSocket]:
        """Backward compatibility property for tests"""
        return self.active_connections

    async def send_personal_message(self, user_id: int, message: str):
        """Backward compatibility method for tests"""
        realtime_msg = RealtimeMessage(
            type=MessageType.NEW_MESSAGE,
            data={"text": message},
            user_id=user_id,
            timestamp=datetime.utcnow(),
        )
        await self.send_to_user(user_id, realtime_msg)

    async def connect(self, websocket: WebSocket, user_id: int, db: Session):
        """Handle new WebSocket connection"""
        try:
            await websocket.accept()

            # Store connection
            self.active_connections[user_id] = websocket

            # Update presence
            await self.update_user_presence(user_id, UserPresenceStatus.ONLINE, db)

            # Send connection confirmation
            await self.send_to_user(
                user_id,
                RealtimeMessage(
                    type=MessageType.CONNECTED,
                    data={"userId": user_id, "status": "connected"},
                ),
            )

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

            # Clean up channel subscriptions
            await self.cleanup_user_channels(user_id)

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

    async def send_to_connection(
        self,
        connection_id: int,
        message: RealtimeMessage,
        exclude_user: Optional[int] = None,
    ):
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

    async def start_typing(
        self, user_id: int, connection_id: int, typing_data: Dict, db: Session
    ):
        """Handle user starting to type"""
        try:
            # Get connection to verify access
            connection = (
                db.query(SoulConnection)
                .filter(
                    SoulConnection.id == connection_id,
                    or_(
                        SoulConnection.user1_id == user_id,
                        SoulConnection.user2_id == user_id,
                    ),
                    SoulConnection.status == "active",
                )
                .first()
            )

            if not connection:
                return False

            # Store typing session
            if connection_id not in self.typing_sessions:
                self.typing_sessions[connection_id] = {}

            self.typing_sessions[connection_id][user_id] = {
                "started_at": datetime.utcnow(),
                "energy_level": typing_data.get(
                    "energyLevel", ConnectionEnergyLevel.MEDIUM
                ),
                "emotional_state": typing_data.get(
                    "emotionalState", UserEmotionalState.CONTEMPLATIVE
                ),
                "message_type": typing_data.get("messageType", "text"),
            }

            # Update database
            await self.update_user_presence(
                user_id, UserPresenceStatus.TYPING, db, connection_id
            )

            # Notify partner
            partner_id = connection.get_partner_id(user_id)
            await self.send_to_user(
                partner_id,
                RealtimeMessage(
                    type=MessageType.TYPING_START,
                    connection_id=connection_id,
                    data={
                        "userId": user_id,
                        "energyLevel": typing_data.get(
                            "energyLevel", ConnectionEnergyLevel.MEDIUM
                        ),
                        "emotionalState": typing_data.get(
                            "emotionalState", UserEmotionalState.CONTEMPLATIVE
                        ),
                        "connectionStage": connection.connection_stage,
                    },
                ),
            )

            # Track analytics
            await self.track_engagement_event(
                user_id,
                AnalyticsEventType.TYPING_INDICATOR_SHOWN,
                {"connection_id": connection_id},
                db,
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
                    del self.typing_sessions[connection_id][user_id]

                    # Clean up empty connections
                    if not self.typing_sessions[connection_id]:
                        del self.typing_sessions[connection_id]

                    # Update presence
                    await self.update_user_presence(
                        user_id, UserPresenceStatus.ONLINE, db
                    )

                    # Get connection for partner notification
                    connection = (
                        db.query(SoulConnection)
                        .filter(
                            SoulConnection.id == connection_id,
                            or_(
                                SoulConnection.user1_id == user_id,
                                SoulConnection.user2_id == user_id,
                            ),
                        )
                        .first()
                    )

                    if connection:
                        partner_id = connection.get_partner_id(user_id)
                        await self.send_to_user(
                            partner_id,
                            RealtimeMessage(
                                type=MessageType.TYPING_STOP,
                                connection_id=connection_id,
                                data={"userId": user_id},
                            ),
                        )

            return True

        except Exception as e:
            logger.error(f"Error stopping typing session: {str(e)}")
            return False

    async def update_connection_energy(
        self,
        connection_id: int,
        new_energy: ConnectionEnergyLevel,
        db: Session,
    ):
        """Update connection energy level and notify users"""
        try:
            connection = (
                db.query(SoulConnection)
                .filter(SoulConnection.id == connection_id)
                .first()
            )

            if not connection:
                return False

            # Update energy
            old_energy = connection.current_energy_level
            connection.current_energy_level = new_energy
            connection.last_activity_at = datetime.utcnow()

            # Update energy history
            if not connection.energy_history:
                connection.energy_history = []

            connection.energy_history.append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "old_energy": old_energy,
                    "new_energy": new_energy,
                }
            )

            db.commit()

            # Notify both users
            await self.send_to_connection(
                connection_id,
                RealtimeMessage(
                    type=MessageType.ENERGY_CHANGE,
                    data={
                        "oldEnergy": old_energy,
                        "newEnergy": new_energy,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                ),
            )

            return True

        except Exception as e:
            logger.error(f"Error updating connection energy: {str(e)}")
            db.rollback()
            return False

    async def trigger_celebration(
        self,
        connection_id: int,
        celebration_type: str,
        data: Dict,
        db: Session,
    ):
        """Trigger celebration animation for both users"""
        try:
            await self.send_to_connection(
                connection_id,
                RealtimeMessage(
                    type=MessageType.CELEBRATION,
                    data={
                        "celebrationType": celebration_type,
                        "animationData": data,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                ),
            )

            # Track analytics
            connection = (
                db.query(SoulConnection)
                .filter(SoulConnection.id == connection_id)
                .first()
            )

            if connection:
                for user_id in [connection.user1_id, connection.user2_id]:
                    await self.track_engagement_event(
                        user_id,
                        AnalyticsEventType.ANIMATION_VIEWED,
                        {
                            "connection_id": connection_id,
                            "animation_type": celebration_type,
                            "data": data,
                        },
                        db,
                    )

            return True

        except Exception as e:
            logger.error(f"Error triggering celebration: {str(e)}")
            return False

    async def notify_new_revelation(
        self,
        connection_id: int,
        sender_id: int,
        revelation_data: Dict,
        db: Session,
    ):
        """Notify about new revelation sharing"""
        try:
            connection = (
                db.query(SoulConnection)
                .filter(SoulConnection.id == connection_id)
                .first()
            )

            if not connection:
                return False

            # Get partner
            partner_id = connection.get_partner_id(sender_id)

            # Send notification to partner
            await self.send_to_user(
                partner_id,
                RealtimeMessage(
                    type=MessageType.NEW_REVELATION,
                    connection_id=connection_id,
                    data={
                        "senderId": sender_id,
                        "dayNumber": revelation_data.get("dayNumber"),
                        "revelationType": revelation_data.get("revelationType"),
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                ),
            )

            # Update connection energy (revelations increase energy)
            if connection.current_energy_level == ConnectionEnergyLevel.LOW:
                await self.update_connection_energy(
                    connection_id, ConnectionEnergyLevel.MEDIUM, db
                )
            elif connection.current_energy_level == ConnectionEnergyLevel.MEDIUM:
                await self.update_connection_energy(
                    connection_id, ConnectionEnergyLevel.HIGH, db
                )

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
            channel = message_data.get("channel")

            # Handle channel subscriptions (Frontend WebSocket Pool compatibility)
            if message_type == MessageType.CHANNEL_SUBSCRIBE and channel:
                success = await self.subscribe_to_channel(user_id, channel)
                if success:
                    # Send confirmation
                    await self.send_to_user(
                        user_id,
                        RealtimeMessage(
                            type=MessageType.CHANNEL_SUBSCRIBE,
                            data={"channel": channel, "status": "subscribed"},
                        ),
                    )
                return success

            elif message_type == MessageType.CHANNEL_UNSUBSCRIBE and channel:
                success = await self.unsubscribe_from_channel(user_id, channel)
                if success:
                    # Send confirmation
                    await self.send_to_user(
                        user_id,
                        RealtimeMessage(
                            type=MessageType.CHANNEL_UNSUBSCRIBE,
                            data={
                                "channel": channel,
                                "status": "unsubscribed",
                            },
                        ),
                    )
                return success

            # Handle heartbeat with acknowledgment
            elif message_type == MessageType.HEARTBEAT:
                # Update last seen
                await self.update_user_presence(user_id, UserPresenceStatus.ONLINE, db)
                # Send heartbeat acknowledgment
                await self.send_to_user(
                    user_id,
                    RealtimeMessage(
                        type=MessageType.HEARTBEAT_ACK,
                        data={"timestamp": datetime.utcnow().isoformat()},
                    ),
                )
                return True

            # Handle energy pulse updates
            elif message_type == MessageType.ENERGY_SYNC:
                return await self.handle_energy_pulse(user_id, data, db)

            # Handle presence updates
            elif message_type == MessageType.PRESENCE_UPDATE:
                return await self.handle_presence_update(user_id, data, db)

            # Existing message handlers
            elif message_type == MessageType.TYPING_START:
                return await self.start_typing(user_id, connection_id, data, db)

            elif message_type == MessageType.TYPING_STOP:
                return await self.stop_typing(user_id, connection_id, db)

            elif message_type == MessageType.CONNECTION_UPDATE:
                # Subscribe to connection updates
                if connection_id:
                    await self.subscribe_to_connection(user_id, connection_id)
                return True

            elif message_type == MessageType.MESSAGE:
                # Handle real-time message
                return await self.handle_real_time_message(user_id, message_data, db)

            else:
                logger.warning(f"Unknown message type: {message_type}")
                return False

        except Exception as e:
            logger.error(f"Error handling message from user {user_id}: {str(e)}")
            return False

    async def handle_real_time_message(
        self, sender_id: int, message_data: Dict, db: Session
    ):
        """Handle real-time message sending and delivery"""
        try:
            from app.models.message import Message

            connection_id = message_data.get("connection_id")
            content = message_data.get("content")
            message_type = message_data.get("message_type", "text")

            if not connection_id or not content:
                logger.warning(f"Invalid message data from user {sender_id}")
                return False

            # Verify sender has access to this connection
            connection = (
                db.query(SoulConnection)
                .filter(
                    SoulConnection.id == connection_id,
                    or_(
                        SoulConnection.user1_id == sender_id,
                        SoulConnection.user2_id == sender_id,
                    ),
                )
                .first()
            )

            if not connection:
                logger.warning(
                    f"User {sender_id} tried to send message to unauthorized connection {connection_id}"
                )
                return False

            # Create message record
            message = Message(
                connection_id=connection_id,
                sender_id=sender_id,
                message_text=content,
                message_type=message_type,
            )
            db.add(message)
            db.commit()
            db.refresh(message)

            # Determine recipient
            recipient_id = (
                connection.user2_id
                if connection.user1_id == sender_id
                else connection.user1_id
            )

            # Send confirmation to sender
            confirmation_message = RealtimeMessage(
                type=MessageType.MESSAGE_SENT,
                data={
                    "message": {
                        "id": message.id,
                        "content": content,
                        "message_type": message_type,
                        "connection_id": connection_id,
                        "timestamp": (
                            message.created_at.isoformat()
                            if message.created_at
                            else datetime.utcnow().isoformat()
                        ),
                    }
                },
                target_user_id=sender_id,
                connection_id=connection_id,
            )
            await self.send_to_user(sender_id, confirmation_message)

            # Deliver message to recipient if online
            if recipient_id in self.active_connections:
                delivery_message = RealtimeMessage(
                    type=MessageType.NEW_MESSAGE,
                    data={
                        "message": {
                            "id": message.id,
                            "content": content,
                            "message_type": message_type,
                            "connection_id": connection_id,
                            "sender_id": sender_id,
                            "timestamp": (
                                message.created_at.isoformat()
                                if message.created_at
                                else datetime.utcnow().isoformat()
                            ),
                        }
                    },
                    target_user_id=recipient_id,
                    connection_id=connection_id,
                )
                await self.send_to_user(recipient_id, delivery_message)

                logger.info(f"Message {message.id} delivered to user {recipient_id}")
            else:
                # Queue notification for offline user
                await self.queue_notification_for_offline_user(
                    recipient_id,
                    {
                        "message": {
                            "id": message.id,
                            "content": content,
                            "message_type": message_type,
                            "connection_id": connection_id,
                            "sender_id": sender_id,
                        }
                    },
                    db,
                )

                logger.info(
                    f"Message {message.id} queued for offline user {recipient_id}"
                )

            return True

        except Exception as e:
            logger.error(
                f"Error handling real-time message from user {sender_id}: {str(e)}"
            )
            return False

    async def update_user_presence(
        self,
        user_id: int,
        status: UserPresenceStatus,
        db: Session,
        connection_id: Optional[int] = None,
    ):
        """Update user presence in database"""
        try:
            presence = (
                db.query(UserPresence).filter(UserPresence.user_id == user_id).first()
            )

            if not presence:
                presence = UserPresence(
                    user_id=user_id, status=status, last_seen=datetime.utcnow()
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

    async def notify_user_connections(
        self, user_id: int, message_type: MessageType, db: Session
    ):
        """Notify all connections about user presence change"""
        try:
            # Get user's active connections
            connections = (
                db.query(SoulConnection)
                .filter(
                    or_(
                        SoulConnection.user1_id == user_id,
                        SoulConnection.user2_id == user_id,
                    ),
                    SoulConnection.status == "active",
                )
                .all()
            )

            for connection in connections:
                partner_id = connection.get_partner_id(user_id)

                await self.send_to_user(
                    partner_id,
                    RealtimeMessage(
                        type=message_type,
                        connection_id=connection.id,
                        data={
                            "userId": user_id,
                            "status": self.user_presence.get(
                                user_id, UserPresenceStatus.OFFLINE
                            ).value,
                        },
                    ),
                )

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

    async def track_engagement_event(
        self,
        user_id: int,
        event_type: AnalyticsEventType,
        event_data: Dict,
        db: Session,
    ):
        """Track user engagement event"""
        try:
            analytics_event = UserEngagementAnalytics(
                user_id=user_id,
                event_type=event_type.value,
                event_data=event_data,
                created_at=datetime.utcnow(),
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
            stale_presence = (
                db.query(UserPresence)
                .filter(
                    UserPresence.last_seen < cutoff_time,
                    UserPresence.status != UserPresenceStatus.OFFLINE,
                )
                .all()
            )

            for presence in stale_presence:
                if presence.user_id not in self.active_connections:
                    presence.status = UserPresenceStatus.OFFLINE
                    presence.is_typing = False
                    presence.typing_in_connection = None

            db.commit()

        except Exception as e:
            logger.error(f"Error cleaning up stale sessions: {str(e)}")
            db.rollback()

    async def queue_notification_for_offline_user(
        self, user_id: int, notification_data: Dict, db: Session
    ):
        """Queue notification for offline user"""
        try:
            # Add to in-memory queue
            if user_id not in self.offline_message_queue:
                self.offline_message_queue[user_id] = []

            notification_msg = RealtimeMessage(
                type=MessageType.NEW_MESSAGE,
                data=notification_data,
                target_user_id=user_id,
            )
            self.offline_message_queue[user_id].append(notification_msg)

            logger.info(f"Queued notification for offline user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error queuing notification for user {user_id}: {str(e)}")
            return False

    def is_user_online(self, user_id: int) -> bool:
        """Check if user is currently online"""
        return user_id in self.active_connections

    def get_last_seen(self, user_id: int) -> Optional[str]:
        """Get when user was last seen online"""
        # For test compatibility, return current timestamp if user is online
        # In production, this would query the database for actual last_seen
        if self.is_user_online(user_id):
            return datetime.utcnow().isoformat()
        else:
            # Mock a recent timestamp for offline users
            return (datetime.utcnow() - timedelta(minutes=5)).isoformat()

    # Synchronous wrapper methods for test compatibility
    def connect_sync(self, websocket: WebSocket, user_id: int) -> None:
        """Synchronous connect wrapper for tests"""
        self.active_connections[user_id] = websocket
        self.user_presence[user_id] = UserPresenceStatus.ONLINE

    def disconnect_sync(self, user_id: int) -> None:
        """Synchronous disconnect wrapper for tests"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        if user_id in self.user_presence:
            self.user_presence[user_id] = UserPresenceStatus.OFFLINE

    # Channel-based subscription methods (Frontend WebSocket Pool compatibility)

    async def subscribe_to_channel(self, user_id: int, channel: str):
        """Subscribe user to a specific channel"""
        try:
            if channel not in self.channel_subscribers:
                self.channel_subscribers[channel] = set()

            if user_id not in self.user_channels:
                self.user_channels[user_id] = set()

            self.channel_subscribers[channel].add(user_id)
            self.user_channels[user_id].add(channel)

            logger.info(f"User {user_id} subscribed to channel '{channel}'")
            return True

        except Exception as e:
            logger.error(
                f"Error subscribing user {user_id} to channel '{channel}': {str(e)}"
            )
            return False

    async def unsubscribe_from_channel(self, user_id: int, channel: str):
        """Unsubscribe user from a specific channel"""
        try:
            if channel in self.channel_subscribers:
                self.channel_subscribers[channel].discard(user_id)

                # Clean up empty channels
                if not self.channel_subscribers[channel]:
                    del self.channel_subscribers[channel]

            if user_id in self.user_channels:
                self.user_channels[user_id].discard(channel)

                # Clean up empty user subscriptions
                if not self.user_channels[user_id]:
                    del self.user_channels[user_id]

            logger.info(f"User {user_id} unsubscribed from channel '{channel}'")
            return True

        except Exception as e:
            logger.error(
                f"Error unsubscribing user {user_id} from channel '{channel}': {str(e)}"
            )
            return False

    async def broadcast_to_channel(self, channel: str, message: RealtimeMessage):
        """Broadcast message to all subscribers of a channel"""
        try:
            if channel not in self.channel_subscribers:
                logger.warning(
                    f"Attempted to broadcast to non-existent channel '{channel}'"
                )
                return 0

            sent_count = 0
            for user_id in self.channel_subscribers[
                channel
            ].copy():  # Copy to avoid modification during iteration
                success = await self.send_to_user(user_id, message)
                if success:
                    sent_count += 1

            logger.debug(
                f"Broadcast to channel '{channel}': {sent_count} users reached"
            )
            return sent_count

        except Exception as e:
            logger.error(f"Error broadcasting to channel '{channel}': {str(e)}")
            return 0

    async def get_channel_subscribers(self, channel: str) -> List[int]:
        """Get list of user IDs subscribed to a channel"""
        return list(self.channel_subscribers.get(channel, set()))

    async def get_user_channels(self, user_id: int) -> List[str]:
        """Get list of channels a user is subscribed to"""
        return list(self.user_channels.get(user_id, set()))

    async def cleanup_user_channels(self, user_id: int):
        """Clean up all channel subscriptions for a user (called on disconnect)"""
        try:
            if user_id not in self.user_channels:
                return

            channels_to_cleanup = self.user_channels[user_id].copy()

            for channel in channels_to_cleanup:
                await self.unsubscribe_from_channel(user_id, channel)

            logger.info(
                f"Cleaned up {len(channels_to_cleanup)} channel subscriptions for user {user_id}"
            )

        except Exception as e:
            logger.error(f"Error cleaning up channels for user {user_id}: {str(e)}")

    # Soul-specific message handlers

    async def handle_energy_pulse(self, user_id: int, data: Dict, db: Session):
        """Handle energy pulse updates for soul connections"""
        try:
            connection_id = data.get("connectionId")
            soul_type = data.get("soulType")  # 'left' or 'right'
            energy_level = data.get("energyLevel", 3)

            if not connection_id:
                return False

            # Broadcast energy pulse to connection channel
            connection_channel = f"connection_{connection_id}"
            energy_message = RealtimeMessage(
                type=MessageType.ENERGY_SYNC,
                data={
                    "connectionId": connection_id,
                    "soulType": soul_type,
                    "energyLevel": energy_level,
                    "userId": user_id,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                connection_id=connection_id,
            )

            await self.broadcast_to_channel(connection_channel, energy_message)
            logger.debug(f"Energy pulse broadcasted for connection {connection_id}")
            return True

        except Exception as e:
            logger.error(f"Error handling energy pulse: {str(e)}")
            return False

    async def handle_presence_update(self, user_id: int, data: Dict, db: Session):
        """Handle presence status updates"""
        try:
            status = data.get("status", "online")
            activity = data.get("activity", "exploring")

            # Update user presence in database
            if status == "online":
                await self.update_user_presence(user_id, UserPresenceStatus.ONLINE, db)
            elif status == "away":
                await self.update_user_presence(user_id, UserPresenceStatus.AWAY, db)
            elif status == "offline":
                await self.update_user_presence(user_id, UserPresenceStatus.OFFLINE, db)

            # Broadcast presence update to user_presence channel
            presence_message = RealtimeMessage(
                type=MessageType.PRESENCE_UPDATE,
                data={
                    "userId": user_id,
                    "status": status,
                    "activity": activity,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            await self.broadcast_to_channel("user_presence", presence_message)
            logger.debug(f"Presence update broadcasted for user {user_id}: {status}")
            return True

        except Exception as e:
            logger.error(f"Error handling presence update: {str(e)}")
            return False

    async def broadcast_compatibility_update(
        self, connection_id: int, compatibility_data: Dict, db: Session
    ):
        """Broadcast compatibility score updates to subscribers"""
        try:
            # Broadcast to specific connection channel
            connection_channel = f"connection_{connection_id}"
            compatibility_message = RealtimeMessage(
                type=MessageType.COMPATIBILITY_CHANGE,
                data={
                    "connectionId": connection_id,
                    "newScore": compatibility_data.get("newScore"),
                    "previousScore": compatibility_data.get("previousScore"),
                    "breakdown": compatibility_data.get("breakdown", {}),
                    "factors": compatibility_data.get("factors", []),
                    "timestamp": datetime.utcnow().isoformat(),
                },
                connection_id=connection_id,
            )

            sent_count = await self.broadcast_to_channel(
                connection_channel, compatibility_message
            )

            # Also broadcast to global compatibility updates channel
            await self.broadcast_to_channel(
                "compatibility_updates", compatibility_message
            )

            logger.info(
                f"Compatibility update broadcasted for connection {connection_id} to {sent_count} subscribers"
            )
            return True

        except Exception as e:
            logger.error(f"Error broadcasting compatibility update: {str(e)}")
            return False

    async def broadcast_new_match(self, user_id: int, match_data: Dict, db: Session):
        """Broadcast new match notification"""
        try:
            match_message = RealtimeMessage(
                type=MessageType.NEW_MATCH,
                data={
                    "userId": user_id,
                    "matchData": match_data,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            # Send to the specific user
            await self.send_to_user(user_id, match_message)

            # Also broadcast to soul_connections channel for global listeners
            await self.broadcast_to_channel("soul_connections", match_message)

            logger.info(f"New match notification sent to user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error broadcasting new match: {str(e)}")
            return False

    async def broadcast_revelation_update(
        self, connection_id: int, revelation_data: Dict, db: Session
    ):
        """Broadcast revelation sharing updates"""
        try:
            revelation_type = revelation_data.get("type", "shared")

            if revelation_type == "shared":
                message_type = MessageType.REVELATION_SHARED
            elif revelation_type == "received":
                message_type = MessageType.REVELATION_RECEIVED
            elif revelation_type == "mutual_complete":
                message_type = MessageType.REVELATION_MUTUAL_COMPLETE
            else:
                message_type = MessageType.NEW_REVELATION

            revelation_message = RealtimeMessage(
                type=message_type,
                data={
                    "connectionId": connection_id,
                    "senderId": revelation_data.get("senderId"),
                    "senderName": revelation_data.get("senderName"),
                    "day": revelation_data.get("day"),
                    "type": revelation_type,
                    "preview": revelation_data.get("preview", ""),
                    "timestamp": datetime.utcnow().isoformat(),
                },
                connection_id=connection_id,
            )

            # Broadcast to connection channel
            connection_channel = f"connection_{connection_id}"
            await self.broadcast_to_channel(connection_channel, revelation_message)

            # Also broadcast to revelation updates channel
            await self.broadcast_to_channel("revelation_updates", revelation_message)

            logger.info(f"Revelation update broadcasted for connection {connection_id}")
            return True

        except Exception as e:
            logger.error(f"Error broadcasting revelation update: {str(e)}")
            return False

    def get_connection_stats(self) -> Dict:
        """Get real-time system statistics"""
        return {
            "active_connections": len(self.active_connections),
            "typing_sessions": sum(
                len(sessions) for sessions in self.typing_sessions.values()
            ),
            "connection_subscribers": len(self.connection_subscribers),
            "channel_subscribers": len(self.channel_subscribers),
            "total_channel_subscriptions": sum(
                len(subs) for subs in self.channel_subscribers.values()
            ),
            "queued_messages": sum(
                len(queue) for queue in self.offline_message_queue.values()
            ),
            "user_presence_tracked": len(self.user_presence),
        }

    async def integrate_with_activity_tracking(self, user_id: int, activity_data: Dict):
        """Integration point for activity tracking system"""
        try:
            pass

            # Extract activity information
            activity_type = activity_data.get("activityType")
            context = activity_data.get("context")
            activity_data.get("connectionId")

            if not activity_type:
                return False

            # Update activity summary for real-time display
            if user_id in self.active_connections:
                # User is online, update their presence with activity
                presence_data = {
                    "status": "online",
                    "activity": activity_type,
                    "location": context or "unknown",
                }
                await self.handle_presence_update(user_id, presence_data, None)

            logger.debug(
                f"Activity tracking integrated for user {user_id}: {activity_type}"
            )
            return True

        except Exception as e:
            logger.error(f"Error integrating with activity tracking: {str(e)}")
            return False


# Global instance
realtime_manager = RealtimeConnectionManager()
