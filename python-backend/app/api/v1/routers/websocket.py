"""
WebSocket API Router - Phase 4 Real-time Features
Handles WebSocket connections for real-time features
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict

from app.api.v1.deps import get_current_user, get_current_user_websocket
from app.core.database import get_db
from app.models.realtime_state import UserPresence, UserPresenceStatus
from app.models.soul_analytics import AnalyticsEventType, UserEngagementAnalytics
from app.models.user import User
from app.services.realtime_connection_manager import MessageType, realtime_manager
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket, token: str, db: Session = Depends(get_db)
):
    """Main WebSocket endpoint for real-time connections"""
    await _handle_websocket_connection(websocket, token, db)


@router.websocket("/{user_id}")
async def websocket_user_endpoint(
    websocket: WebSocket,
    user_id: int,
    token: str,
    db: Session = Depends(get_db),
):
    """WebSocket endpoint with user ID in path (for test compatibility)"""
    # Restore full WebSocket functionality with authentication
    await _handle_websocket_connection(websocket, token, db)


async def _handle_websocket_connection(websocket: WebSocket, token: str, db: Session):
    """Handle WebSocket connection logic"""
    user = None
    try:
        # Authenticate user from token
        user = await get_current_user_websocket(token, db)
        if not user:
            await websocket.close(code=4001, reason="Authentication failed")
            return

        # Connect user to real-time system
        await realtime_manager.connect(websocket, user.id, db)

        # Track connection event
        engagement_event = UserEngagementAnalytics(
            user_id=user.id,
            event_type=AnalyticsEventType.LOGIN.value,
            event_data={
                "connection_type": "websocket",
                "timestamp": datetime.utcnow().isoformat(),
            },
            session_id=f"ws_{user.id}_{datetime.utcnow().timestamp()}",
            device_type="unknown",  # Could be enhanced with client info
        )
        db.add(engagement_event)
        db.commit()

        # Message handling loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)

                # Handle message through realtime manager
                success = await realtime_manager.handle_message(
                    user.id, message_data, db
                )

                if not success:
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": MessageType.ERROR.value,
                                "data": {"message": "Failed to process message"},
                                "timestamp": datetime.utcnow().isoformat(),
                            }
                        )
                    )

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for user {user.id}")
                break
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from user {user.id}")
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": MessageType.ERROR.value,
                            "data": {"message": "Invalid JSON format"},
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )
                )
            except Exception as e:
                logger.error(
                    f"Error handling WebSocket message for user {user.id}: {str(e)}"
                )
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": MessageType.ERROR.value,
                            "data": {"message": "Internal server error"},
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )
                )

    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
        if websocket.client_state.name != "DISCONNECTED":
            await websocket.close(code=4000, reason="Server error")

    finally:
        # Clean up connection
        if user:
            await realtime_manager.disconnect(user.id, db)


# HTTP endpoints for real-time system management


@router.get("/status")
async def get_realtime_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get real-time system status for current user
    """
    try:
        # Get user presence
        presence = (
            db.query(UserPresence)
            .filter(UserPresence.user_id == current_user.id)
            .first()
        )

        # Get connection stats
        stats = realtime_manager.get_connection_stats()

        # Get user channel subscriptions
        user_channels = await realtime_manager.get_user_channels(current_user.id)

        return {
            "userId": current_user.id,
            "isConnected": current_user.id in realtime_manager.active_connections,
            "presence": {
                "status": (presence.status if presence else UserPresenceStatus.OFFLINE),
                "lastSeen": (
                    presence.last_seen.isoformat()
                    if presence and presence.last_seen
                    else None
                ),
                "isTyping": presence.is_typing if presence else False,
                "typingInConnection": (
                    presence.typing_in_connection if presence else None
                ),
            },
            "channels": user_channels,
            "systemStats": stats,
        }

    except Exception as e:
        logger.error(f"Error getting realtime status: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting realtime status")


@router.get("/health")
async def get_websocket_health():
    """
    Get WebSocket connection pool health status (Frontend WebSocket Pool compatibility)
    """
    try:
        stats = realtime_manager.get_connection_stats()

        # Determine health based on connections and system state
        if stats["active_connections"] == 0:
            health = "disconnected"
        elif (
            stats.get("channel_subscribers", 0) > 0 and stats["active_connections"] > 0
        ):
            # Good health if we have both connections and active subscribers
            connection_ratio = min(
                stats["active_connections"] / 10, 1.0
            )  # Scale by expected connections
            if connection_ratio >= 0.9:
                health = "excellent"
            elif connection_ratio >= 0.7:
                health = "good"
            else:
                health = "poor"
        else:
            health = "poor"

        return {
            "health": health,
            "connectionCount": stats["active_connections"],
            "activeChannels": stats.get("channel_subscribers", 0),
            "totalChannelSubscriptions": stats.get("total_channel_subscriptions", 0),
            "queuedMessages": stats["queued_messages"],
            "typingSessions": stats["typing_sessions"],
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting WebSocket health: {str(e)}")
        return {
            "health": "error",
            "connectionCount": 0,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


@router.post("/channels/subscribe")
async def subscribe_to_channel(
    channel_data: Dict[str, str],
    current_user: User = Depends(get_current_user),
):
    """
    Subscribe user to a WebSocket channel (Frontend WebSocket Pool compatibility)
    """
    try:
        channel = channel_data.get("channel")
        if not channel:
            raise HTTPException(status_code=400, detail="Channel name is required")

        success = await realtime_manager.subscribe_to_channel(current_user.id, channel)

        if not success:
            raise HTTPException(
                status_code=400, detail="Failed to subscribe to channel"
            )

        return {
            "success": True,
            "channel": channel,
            "userId": current_user.id,
            "message": f"Successfully subscribed to channel '{channel}'",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error subscribing to channel: {str(e)}")
        raise HTTPException(status_code=500, detail="Error subscribing to channel")


@router.post("/channels/unsubscribe")
async def unsubscribe_from_channel(
    channel_data: Dict[str, str],
    current_user: User = Depends(get_current_user),
):
    """
    Unsubscribe user from a WebSocket channel
    """
    try:
        channel = channel_data.get("channel")
        if not channel:
            raise HTTPException(status_code=400, detail="Channel name is required")

        success = await realtime_manager.unsubscribe_from_channel(
            current_user.id, channel
        )

        if not success:
            raise HTTPException(
                status_code=400, detail="Failed to unsubscribe from channel"
            )

        return {
            "success": True,
            "channel": channel,
            "userId": current_user.id,
            "message": f"Successfully unsubscribed from channel '{channel}'",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unsubscribing from channel: {str(e)}")
        raise HTTPException(status_code=500, detail="Error unsubscribing from channel")


@router.get("/channels/list")
async def list_user_channels(current_user: User = Depends(get_current_user)):
    """
    Get list of channels user is subscribed to
    """
    try:
        channels = await realtime_manager.get_user_channels(current_user.id)

        return {
            "userId": current_user.id,
            "channels": channels,
            "totalChannels": len(channels),
        }

    except Exception as e:
        logger.error(f"Error listing user channels: {str(e)}")
        raise HTTPException(status_code=500, detail="Error listing user channels")


@router.post("/typing/start/{connection_id}")
async def start_typing_indicator(
    connection_id: int,
    typing_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Start typing indicator for a connection
    """
    try:
        success = await realtime_manager.start_typing(
            current_user.id, connection_id, typing_data, db
        )

        if not success:
            raise HTTPException(
                status_code=400, detail="Failed to start typing indicator"
            )

        return {"success": True, "message": "Typing indicator started"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting typing indicator: {str(e)}")
        raise HTTPException(status_code=500, detail="Error starting typing indicator")


@router.post("/typing/stop/{connection_id}")
async def stop_typing_indicator(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Stop typing indicator for a connection
    """
    try:
        success = await realtime_manager.stop_typing(current_user.id, connection_id, db)

        if not success:
            raise HTTPException(
                status_code=400, detail="Failed to stop typing indicator"
            )

        return {"success": True, "message": "Typing indicator stopped"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping typing indicator: {str(e)}")
        raise HTTPException(status_code=500, detail="Error stopping typing indicator")


@router.post("/energy/update/{connection_id}")
async def update_connection_energy(
    connection_id: int,
    energy_data: Dict[str, str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update connection energy level
    """
    try:
        from app.models.soul_connection import ConnectionEnergyLevel

        new_energy = ConnectionEnergyLevel(energy_data.get("energyLevel", "medium"))

        success = await realtime_manager.update_connection_energy(
            connection_id, new_energy, db
        )

        if not success:
            raise HTTPException(
                status_code=400, detail="Failed to update connection energy"
            )

        return {"success": True, "newEnergy": new_energy.value}

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid energy level")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating connection energy: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating connection energy")


@router.post("/celebration/{connection_id}")
async def trigger_celebration(
    connection_id: int,
    celebration_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Trigger celebration animation
    """
    try:
        success = await realtime_manager.trigger_celebration(
            connection_id,
            celebration_data.get("type", "general"),
            celebration_data.get("data", {}),
            db,
        )

        if not success:
            raise HTTPException(status_code=400, detail="Failed to trigger celebration")

        return {"success": True, "message": "Celebration triggered"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering celebration: {str(e)}")
        raise HTTPException(status_code=500, detail="Error triggering celebration")


@router.get("/presence/{user_id}")
async def get_user_presence(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get presence status for a specific user (if they're connected to current user)
    """
    try:
        from app.models.soul_connection import SoulConnection

        # Verify users are connected
        connection = (
            db.query(SoulConnection)
            .filter(
                (
                    (SoulConnection.user1_id == current_user.id)
                    & (SoulConnection.user2_id == user_id)
                )
                | (
                    (SoulConnection.user1_id == user_id)
                    & (SoulConnection.user2_id == current_user.id)
                ),
                SoulConnection.status == "active",
            )
            .first()
        )

        if not connection:
            raise HTTPException(status_code=403, detail="Not connected to this user")

        # Get presence data
        presence = (
            db.query(UserPresence).filter(UserPresence.user_id == user_id).first()
        )

        return {
            "userId": user_id,
            "status": (
                presence.status if presence else UserPresenceStatus.OFFLINE.value
            ),
            "lastSeen": (
                presence.last_seen.isoformat()
                if presence and presence.last_seen
                else None
            ),
            "isTyping": presence.is_typing if presence else False,
            "typingInConnection": (presence.typing_in_connection if presence else None),
            "isOnline": user_id in realtime_manager.active_connections,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user presence: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting user presence")


@router.get("/connections/active")
async def get_active_connections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get real-time status of user's active connections
    """
    try:
        from app.models.soul_connection import SoulConnection

        # Get user's connections
        connections = (
            db.query(SoulConnection)
            .filter(
                (
                    (SoulConnection.user1_id == current_user.id)
                    | (SoulConnection.user2_id == current_user.id)
                ),
                SoulConnection.status == "active",
            )
            .all()
        )

        connection_statuses = []

        for connection in connections:
            partner_id = connection.get_partner_id(current_user.id)

            # Get partner presence
            partner_presence = (
                db.query(UserPresence)
                .filter(UserPresence.user_id == partner_id)
                .first()
            )

            connection_statuses.append(
                {
                    "connectionId": connection.id,
                    "partnerId": partner_id,
                    "energyLevel": connection.current_energy_level,
                    "stage": connection.connection_stage,
                    "partnerPresence": {
                        "status": (
                            partner_presence.status
                            if partner_presence
                            else UserPresenceStatus.OFFLINE.value
                        ),
                        "isOnline": partner_id in realtime_manager.active_connections,
                        "isTyping": (
                            partner_presence.is_typing if partner_presence else False
                        ),
                        "lastSeen": (
                            partner_presence.last_seen.isoformat()
                            if partner_presence and partner_presence.last_seen
                            else None
                        ),
                    },
                    "lastActivity": (
                        connection.last_activity_at.isoformat()
                        if connection.last_activity_at
                        else None
                    ),
                    "isRecentlyActive": connection.is_recently_active(),
                }
            )

        return {
            "connections": connection_statuses,
            "totalActive": len(
                [c for c in connection_statuses if c["partnerPresence"]["isOnline"]]
            ),
            "totalTyping": len(
                [c for c in connection_statuses if c["partnerPresence"]["isTyping"]]
            ),
        }

    except Exception as e:
        logger.error(f"Error getting active connections: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting active connections")


@router.post("/notify/revelation")
async def notify_revelation_shared(
    notification_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Notify about a new revelation being shared (called by revelation endpoints)
    """
    try:
        connection_id = notification_data.get("connectionId")
        revelation_data = notification_data.get("revelationData", {})

        success = await realtime_manager.notify_new_revelation(
            connection_id, current_user.id, revelation_data, db
        )

        if not success:
            raise HTTPException(status_code=400, detail="Failed to send notification")

        return {"success": True, "message": "Revelation notification sent"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error notifying revelation: {str(e)}")
        raise HTTPException(status_code=500, detail="Error sending notification")


# Admin endpoints for monitoring


@router.get("/admin/stats")
async def get_system_stats(current_user: User = Depends(get_current_user)):
    """
    Get comprehensive real-time system statistics (admin only)
    """
    # Note: In production, add admin permission check
    stats = realtime_manager.get_connection_stats()

    return {"realtime": stats, "timestamp": datetime.utcnow().isoformat()}


@router.post("/admin/cleanup")
async def cleanup_stale_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Manually trigger cleanup of stale sessions (admin only)
    """
    try:
        # Note: In production, add admin permission check
        await realtime_manager.cleanup_stale_sessions(db)

        return {"success": True, "message": "Cleanup completed"}

    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail="Error during cleanup")
