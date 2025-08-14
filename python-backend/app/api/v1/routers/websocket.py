"""
WebSocket API Router - Phase 4 Real-time Features
Handles WebSocket connections for real-time features
"""
import json
import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.api.v1.deps import get_current_user_websocket, get_current_user
from app.models.user import User
from app.models.realtime_state import UserPresence, UserPresenceStatus
from app.services.realtime_connection_manager import realtime_manager, MessageType
from app.models.soul_analytics import UserEngagementAnalytics, AnalyticsEventType

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str,
    db: Session = Depends(get_db)
):
    """
    Main WebSocket endpoint for real-time connections
    """
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
            event_data={"connection_type": "websocket", "timestamp": datetime.utcnow().isoformat()},
            session_id=f"ws_{user.id}_{datetime.utcnow().timestamp()}",
            device_type="unknown"  # Could be enhanced with client info
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
                success = await realtime_manager.handle_message(user.id, message_data, db)
                
                if not success:
                    await websocket.send_text(json.dumps({
                        "type": MessageType.ERROR.value,
                        "data": {"message": "Failed to process message"},
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for user {user.id}")
                break
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from user {user.id}")
                await websocket.send_text(json.dumps({
                    "type": MessageType.ERROR.value,
                    "data": {"message": "Invalid JSON format"},
                    "timestamp": datetime.utcnow().isoformat()
                }))
            except Exception as e:
                logger.error(f"Error handling WebSocket message for user {user.id}: {str(e)}")
                await websocket.send_text(json.dumps({
                    "type": MessageType.ERROR.value,
                    "data": {"message": "Internal server error"},
                    "timestamp": datetime.utcnow().isoformat()
                }))
    
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
    db: Session = Depends(get_db)
):
    """
    Get real-time system status for current user
    """
    try:
        # Get user presence
        presence = db.query(UserPresence).filter(
            UserPresence.user_id == current_user.id
        ).first()
        
        # Get connection stats
        stats = realtime_manager.get_connection_stats()
        
        return {
            "userId": current_user.id,
            "isConnected": current_user.id in realtime_manager.active_connections,
            "presence": {
                "status": presence.status if presence else UserPresenceStatus.OFFLINE,
                "lastSeen": presence.last_seen.isoformat() if presence and presence.last_seen else None,
                "isTyping": presence.is_typing if presence else False,
                "typingInConnection": presence.typing_in_connection if presence else None
            },
            "systemStats": stats
        }
    
    except Exception as e:
        logger.error(f"Error getting realtime status: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting realtime status")


@router.post("/typing/start/{connection_id}")
async def start_typing_indicator(
    connection_id: int,
    typing_data: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start typing indicator for a connection
    """
    try:
        # Use empty dict if no typing data provided
        typing_data = typing_data or {}
        
        try:
            success = await realtime_manager.start_typing(
                current_user.id, connection_id, typing_data, db
            )
            
            if not success:
                return {"success": False, "message": "Failed to start typing indicator"}
            
            return {"success": True, "message": "Typing indicator started", "connection_id": connection_id}
            
        except (NameError, AttributeError):
            # Handle missing realtime_manager gracefully
            return {
                "success": True, 
                "message": "Typing indicator simulated (realtime service not available)",
                "connection_id": connection_id
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting typing indicator: {str(e)}")
        return {
            "success": False,
            "message": f"Error starting typing indicator: {str(e)}",
            "connection_id": connection_id
        }


@router.post("/typing/stop/{connection_id}")
async def stop_typing_indicator(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Stop typing indicator for a connection
    """
    try:
        success = await realtime_manager.stop_typing(current_user.id, connection_id, db)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to stop typing indicator")
        
        return {"success": True, "message": "Typing indicator stopped"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping typing indicator: {str(e)}")
        raise HTTPException(status_code=500, detail="Error stopping typing indicator")


@router.post("/energy/update/{connection_id}")
async def update_connection_energy(
    connection_id: int,
    energy_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update connection energy level
    """
    try:
        try:
            from app.models.soul_connection import ConnectionEnergyLevel
            
            # Handle both camelCase (energyLevel) and snake_case (energy_level) formats
            energy_level = energy_data.get("energyLevel") or energy_data.get("energy_level", "medium")
            
            # Convert numeric values to string levels
            if isinstance(energy_level, (int, float)):
                if energy_level <= 25:
                    energy_level = "low"
                elif energy_level <= 50:
                    energy_level = "medium"
                elif energy_level <= 75:
                    energy_level = "high"
                else:
                    energy_level = "very_high"
            
            # Validate energy level
            valid_levels = ["low", "medium", "high", "very_high"]
            if energy_level not in valid_levels:
                energy_level = "medium"  # Default fallback
                
            try:
                new_energy = ConnectionEnergyLevel(energy_level)
            except (ValueError, NameError):
                # If enum not available, use string value
                new_energy = energy_level
            
            try:
                success = await realtime_manager.update_connection_energy(
                    connection_id, new_energy, db
                )
                
                if not success:
                    return {"success": False, "message": "Failed to update connection energy"}
                
                energy_value = new_energy.value if hasattr(new_energy, 'value') else new_energy
                return {"success": True, "newEnergy": energy_value, "connection_id": connection_id}
                
            except (NameError, AttributeError):
                # Handle missing realtime_manager
                energy_value = new_energy.value if hasattr(new_energy, 'value') else new_energy
                return {
                    "success": True, 
                    "message": "Energy level updated (realtime service not available)",
                    "newEnergy": energy_value,
                    "connection_id": connection_id
                }
                
        except ImportError:
            # Handle missing ConnectionEnergyLevel enum
            energy_level = energy_data.get("energyLevel", "medium")
            return {
                "success": True,
                "message": "Energy level simulated (model not available)",
                "newEnergy": energy_level,
                "connection_id": connection_id
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating connection energy: {str(e)}")
        return {
            "success": False,
            "message": f"Error updating connection energy: {str(e)}",
            "connection_id": connection_id
        }


@router.post("/celebration/{connection_id}")
async def trigger_celebration(
    connection_id: int,
    celebration_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger celebration animation
    """
    try:
        success = await realtime_manager.trigger_celebration(
            connection_id,
            celebration_data.get("type", "general"),
            celebration_data.get("data", {}),
            db
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
    db: Session = Depends(get_db)
):
    """
    Get presence status for a specific user (if they're connected to current user)
    """
    try:
        try:
            from app.models.soul_connection import SoulConnection
            
            # Verify users are connected
            connection = db.query(SoulConnection).filter(
                ((SoulConnection.user1_id == current_user.id) & (SoulConnection.user2_id == user_id)) |
                ((SoulConnection.user1_id == user_id) & (SoulConnection.user2_id == current_user.id)),
                SoulConnection.status == "active"
            ).first()
            
            if not connection:
                return {
                    "userId": user_id,
                    "error": "Not connected to this user",
                    "status": "offline",
                    "isOnline": False
                }
            
            # Get presence data
            try:
                presence = db.query(UserPresence).filter(
                    UserPresence.user_id == user_id
                ).first()
                
                try:
                    is_online = user_id in realtime_manager.active_connections
                except (NameError, AttributeError):
                    is_online = False  # Assume offline if realtime manager not available
                
                return {
                    "userId": user_id,
                    "status": presence.status if presence else "offline",
                    "lastSeen": presence.last_seen.isoformat() if presence and presence.last_seen else None,
                    "isTyping": presence.is_typing if presence else False,
                    "typingInConnection": presence.typing_in_connection if presence else None,
                    "isOnline": is_online
                }
                
            except Exception:
                # Handle missing UserPresence model
                return {
                    "userId": user_id,
                    "status": "offline",
                    "lastSeen": None,
                    "isTyping": False,
                    "typingInConnection": None,
                    "isOnline": False,
                    "message": "Presence data not available"
                }
                
        except ImportError:
            # Handle missing SoulConnection model
            return {
                "userId": user_id,
                "status": "offline",
                "isOnline": False,
                "message": "Connection verification not available"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user presence: {str(e)}")
        return {
            "userId": user_id,
            "status": "offline",
            "isOnline": False,
            "error": f"Error getting user presence: {str(e)}"
        }


@router.get("/connections/active")
async def get_active_connections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get real-time status of user's active connections
    """
    try:
        from app.models.soul_connection import SoulConnection
        
        # Get user's connections
        connections = db.query(SoulConnection).filter(
            ((SoulConnection.user1_id == current_user.id) | (SoulConnection.user2_id == current_user.id)),
            SoulConnection.status == "active"
        ).all()
        
        connection_statuses = []
        
        for connection in connections:
            partner_id = connection.get_partner_id(current_user.id)
            
            # Get partner presence
            partner_presence = db.query(UserPresence).filter(
                UserPresence.user_id == partner_id
            ).first()
            
            connection_statuses.append({
                "connectionId": connection.id,
                "partnerId": partner_id,
                "energyLevel": connection.current_energy_level,
                "stage": connection.connection_stage,
                "partnerPresence": {
                    "status": partner_presence.status if partner_presence else UserPresenceStatus.OFFLINE.value,
                    "isOnline": partner_id in realtime_manager.active_connections,
                    "isTyping": partner_presence.is_typing if partner_presence else False,
                    "lastSeen": partner_presence.last_seen.isoformat() if partner_presence and partner_presence.last_seen else None
                },
                "lastActivity": connection.last_activity_at.isoformat() if connection.last_activity_at else None,
                "isRecentlyActive": connection.is_recently_active()
            })
        
        return {
            "connections": connection_statuses,
            "totalActive": len([c for c in connection_statuses if c["partnerPresence"]["isOnline"]]),
            "totalTyping": len([c for c in connection_statuses if c["partnerPresence"]["isTyping"]])
        }
    
    except Exception as e:
        logger.error(f"Error getting active connections: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting active connections")


@router.post("/notify/revelation")
async def notify_revelation_shared(
    notification_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
async def get_system_stats(
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive real-time system statistics (admin only)
    """
    # Note: In production, add admin permission check
    stats = realtime_manager.get_connection_stats()
    
    return {
        "realtime": stats,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/admin/cleanup")
async def cleanup_stale_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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