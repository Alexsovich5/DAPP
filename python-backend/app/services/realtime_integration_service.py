"""
Real-time Integration Service - Sprint 4
Provides integration points for other backend services to trigger real-time updates
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from app.services.realtime_connection_manager import realtime_manager
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class RealtimeIntegrationService:
    """Service for integrating real-time features with other backend services"""

    @staticmethod
    async def notify_compatibility_update(
        connection_id: int,
        new_score: float,
        previous_score: float,
        breakdown: Dict,
        factors: List[str],
        db: Session,
    ) -> bool:
        """
        Called by compatibility calculation services to broadcast score updates
        """
        try:
            compatibility_data = {
                "newScore": new_score,
                "previousScore": previous_score,
                "breakdown": breakdown,
                "factors": factors,
            }

            success = await realtime_manager.broadcast_compatibility_update(
                connection_id, compatibility_data, db
            )

            if success:
                logger.info(
                    f"Compatibility update broadcasted for connection {connection_id}: {new_score}%"
                )

            return success

        except Exception as e:
            logger.error(f"Error notifying compatibility update: {str(e)}")
            return False

    @staticmethod
    async def notify_new_match(
        user_id: int,
        partner_id: int,
        compatibility_score: float,
        match_type: str = "soul_connection",
        db: Session = None,
    ) -> bool:
        """
        Called by matching services when a new soul connection is found
        """
        try:
            match_data = {
                "partnerId": partner_id,
                "compatibilityScore": compatibility_score,
                "matchType": match_type,
                "timestamp": datetime.utcnow().isoformat(),
            }

            success = await realtime_manager.broadcast_new_match(
                user_id, match_data, db
            )

            if success:
                logger.info(
                    f"New match notification sent: user {user_id} matched with {partner_id}"
                )

            return success

        except Exception as e:
            logger.error(f"Error notifying new match: {str(e)}")
            return False

    @staticmethod
    async def notify_revelation_shared(
        connection_id: int,
        sender_id: int,
        sender_name: str,
        day: int,
        revelation_type: str = "shared",
        preview: str = "",
        db: Session = None,
    ) -> bool:
        """
        Called by revelation services when a revelation is shared
        """
        try:
            revelation_data = {
                "senderId": sender_id,
                "senderName": sender_name,
                "day": day,
                "type": revelation_type,
                "preview": preview,
            }

            success = await realtime_manager.broadcast_revelation_update(
                connection_id, revelation_data, db
            )

            if success:
                logger.info(
                    f"Revelation notification sent: connection {connection_id}, day {day}"
                )

            return success

        except Exception as e:
            logger.error(f"Error notifying revelation shared: {str(e)}")
            return False

    @staticmethod
    async def notify_message_sent(
        connection_id: int, sender_id: int, message_data: Dict, db: Session
    ) -> bool:
        """
        Called by messaging services when a new message is sent
        """
        try:
            from app.services.realtime_connection_manager import (
                MessageType,
                RealtimeMessage,
            )

            message = RealtimeMessage(
                type=MessageType.NEW_MESSAGE,
                data={
                    "connectionId": connection_id,
                    "senderId": sender_id,
                    "messageData": message_data,
                    "timestamp": datetime.utcnow().isoformat(),
                },
                connection_id=connection_id,
            )

            # Send to connection subscribers
            await realtime_manager.send_to_connection(connection_id, message)

            # Also broadcast to connection-specific channel
            connection_channel = f"connection_{connection_id}"
            await realtime_manager.broadcast_to_channel(connection_channel, message)

            logger.info(f"Message notification sent for connection {connection_id}")
            return True

        except Exception as e:
            logger.error(f"Error notifying message sent: {str(e)}")
            return False

    @staticmethod
    async def notify_user_activity(
        user_id: int, activity: str, location: str = "", db: Session = None
    ) -> bool:
        """
        Called by various services to update user activity/presence
        """
        try:
            presence_data = {
                "status": "online",
                "activity": activity,
                "location": location,
            }

            success = await realtime_manager.handle_presence_update(
                user_id, presence_data, db
            )

            if success:
                logger.debug(f"User activity updated: {user_id} - {activity}")

            return success

        except Exception as e:
            logger.error(f"Error notifying user activity: {str(e)}")
            return False

    @staticmethod
    async def trigger_soul_celebration(
        connection_id: int,
        celebration_type: str,
        trigger_data: Dict = None,
        db: Session = None,
    ) -> bool:
        """
        Called by various services to trigger celebration animations
        """
        try:
            success = await realtime_manager.trigger_celebration(
                connection_id, celebration_type, trigger_data or {}, db
            )

            if success:
                logger.info(
                    f"Celebration triggered: {celebration_type} for connection {connection_id}"
                )

            return success

        except Exception as e:
            logger.error(f"Error triggering celebration: {str(e)}")
            return False

    @staticmethod
    async def broadcast_system_announcement(
        message: str,
        channel: str = "system_announcements",
        user_ids: Optional[List[int]] = None,
    ) -> int:
        """
        Broadcast system-wide announcements to all users or specific users
        """
        try:
            from app.services.realtime_connection_manager import (
                MessageType,
                RealtimeMessage,
            )

            announcement = RealtimeMessage(
                type=MessageType.CONNECTED,  # Using CONNECTED as a system message
                data={
                    "type": "system_announcement",
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

            if user_ids:
                # Send to specific users
                sent_count = 0
                for user_id in user_ids:
                    success = await realtime_manager.send_to_user(user_id, announcement)
                    if success:
                        sent_count += 1
            else:
                # Broadcast to channel
                sent_count = await realtime_manager.broadcast_to_channel(
                    channel, announcement
                )

            logger.info(f"System announcement broadcasted to {sent_count} users")
            return sent_count

        except Exception as e:
            logger.error(f"Error broadcasting system announcement: {str(e)}")
            return 0

    @staticmethod
    def get_realtime_statistics() -> Dict:
        """
        Get real-time system statistics for monitoring
        """
        try:
            stats = realtime_manager.get_connection_stats()

            # Add additional computed metrics
            stats["health_score"] = min(
                100, (stats["active_connections"] * 10)
            )  # Simple health scoring
            stats["average_channels_per_user"] = stats.get(
                "total_channel_subscriptions", 0
            ) / max(stats["active_connections"], 1)
            stats["load_level"] = (
                "low"
                if stats["active_connections"] < 10
                else "medium" if stats["active_connections"] < 50 else "high"
            )

            return stats

        except Exception as e:
            logger.error(f"Error getting realtime statistics: {str(e)}")
            return {"error": str(e)}

    @staticmethod
    async def cleanup_user_data(user_id: int, db: Session) -> bool:
        """
        Clean up all real-time data for a user (called on account deletion)
        """
        try:
            # Disconnect user if connected
            if user_id in realtime_manager.active_connections:
                await realtime_manager.disconnect(user_id, db)

            # Clean up any remaining subscriptions
            await realtime_manager.cleanup_user_channels(user_id)

            # Clear message queue
            if user_id in realtime_manager.offline_message_queue:
                del realtime_manager.offline_message_queue[user_id]

            logger.info(f"Real-time data cleaned up for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error cleaning up user data: {str(e)}")
            return False


# Convenience instance for easy importing
realtime_integration = RealtimeIntegrationService()
