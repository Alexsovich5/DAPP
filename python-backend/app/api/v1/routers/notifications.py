# Push Notification API Router for Dinner1
# RESTful endpoints for managing push notifications

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.services.push_notification import (
    get_push_service, 
    NotificationType, 
    PushNotificationService
)

router = APIRouter()

# Pydantic models for request/response
class PushSubscriptionRequest(BaseModel):
    endpoint: str = Field(..., description="Push service endpoint URL")
    keys: Dict[str, str] = Field(..., description="Encryption keys (p256dh and auth)")
    user_agent: Optional[str] = Field(None, description="User agent string")

class NotificationRequest(BaseModel):
    user_id: int = Field(..., description="Target user ID")
    type: str = Field(..., description="Notification type")
    context: Optional[Dict[str, Any]] = Field(None, description="Notification context data")

class BulkNotificationRequest(BaseModel):
    notifications: List[NotificationRequest] = Field(..., description="List of notifications to send")

class NotificationPreferencesRequest(BaseModel):
    new_message: bool = True
    new_match: bool = True
    new_revelation: bool = True
    photo_reveal: bool = True
    connection_request: bool = True
    revelation_reminder: bool = True
    daily_prompt: bool = False
    match_expiring: bool = True
    profile_view: bool = False
    system_announcement: bool = True

class NotificationPreferencesResponse(BaseModel):
    user_id: int
    preferences: Dict[str, bool]
    updated_at: datetime

class NotificationAnalyticsResponse(BaseModel):
    total_sent: int
    delivery_rate: float
    click_rate: float
    most_effective_type: Optional[str]
    period_days: int

@router.post("/subscribe")
async def subscribe_to_notifications(
    subscription_request: PushSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Subscribe user to push notifications
    """
    try:
        push_service = get_push_service()
        
        subscription_data = {
            "endpoint": subscription_request.endpoint,
            "keys": subscription_request.keys
        }
        
        success = await push_service.subscribe_user(
            user_id=current_user.id,
            subscription_data=subscription_data,
            user_agent=subscription_request.user_agent,
            db=db
        )
        
        if success:
            return {
                "success": True,
                "message": "Successfully subscribed to push notifications",
                "user_id": current_user.id
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Failed to subscribe to push notifications"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Subscription failed: {str(e)}"
        )

@router.post("/unsubscribe")
async def unsubscribe_from_notifications(
    endpoint: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Unsubscribe user from push notifications
    """
    try:
        from app.services.push_notification import PushSubscription
        
        # Find and deactivate subscription
        subscription = db.query(PushSubscription).filter(
            PushSubscription.user_id == current_user.id,
            PushSubscription.endpoint == endpoint
        ).first()
        
        if subscription:
            subscription.is_active = False
            db.commit()
            
            return {
                "success": True,
                "message": "Successfully unsubscribed from push notifications"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Subscription not found"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unsubscription failed: {str(e)}"
        )

@router.post("/send")
async def send_notification(
    notification_request: NotificationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a push notification (admin/system use)
    """
    # This endpoint would typically be restricted to admin users
    # For demo purposes, allowing authenticated users
    
    try:
        # Validate notification type
        try:
            notification_type = NotificationType(notification_request.type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid notification type: {notification_request.type}"
            )
        
        push_service = get_push_service()
        
        # Send notification in background
        background_tasks.add_task(
            push_service.send_notification,
            user_id=notification_request.user_id,
            notification_type=notification_type,
            context=notification_request.context or {},
            db=db
        )
        
        return {
            "success": True,
            "message": "Notification queued for sending",
            "type": notification_request.type,
            "target_user": notification_request.user_id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send notification: {str(e)}"
        )

@router.post("/send-bulk")
async def send_bulk_notifications(
    bulk_request: BulkNotificationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send multiple notifications efficiently
    """
    try:
        # Validate all notification types
        validated_notifications = []
        for notification in bulk_request.notifications:
            try:
                notification_type = NotificationType(notification.type)
                validated_notifications.append({
                    "user_id": notification.user_id,
                    "type": notification.type,
                    "context": notification.context or {}
                })
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid notification type: {notification.type}"
                )
        
        push_service = get_push_service()
        
        # Send notifications in background
        background_tasks.add_task(
            push_service.send_bulk_notifications,
            notifications=validated_notifications,
            db=db
        )
        
        return {
            "success": True,
            "message": f"Queued {len(validated_notifications)} notifications for sending",
            "count": len(validated_notifications)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send bulk notifications: {str(e)}"
        )

# Dating app specific notification endpoints

@router.post("/new-message")
async def notify_new_message(
    connection_id: int,
    sender_name: str,
    message_preview: str,
    recipient_user_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send new message notification
    """
    push_service = get_push_service()
    
    background_tasks.add_task(
        push_service.notify_new_message,
        user_id=recipient_user_id,
        sender_name=sender_name,
        message_preview=message_preview,
        connection_id=connection_id,
        db=db
    )
    
    return {"success": True, "message": "Message notification queued"}

@router.post("/new-match")
async def notify_new_match(
    match_name: str,
    compatibility_score: float,
    match_id: int,
    user_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send new match notification
    """
    push_service = get_push_service()
    
    background_tasks.add_task(
        push_service.notify_new_match,
        user_id=user_id,
        match_name=match_name,
        compatibility_score=compatibility_score,
        match_id=match_id,
        db=db
    )
    
    return {"success": True, "message": "Match notification queued"}

@router.post("/new-revelation")
async def notify_new_revelation(
    sender_name: str,
    day: int,
    revelation_preview: str,
    connection_id: int,
    recipient_user_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send new revelation notification
    """
    push_service = get_push_service()
    
    background_tasks.add_task(
        push_service.notify_new_revelation,
        user_id=recipient_user_id,
        sender_name=sender_name,
        day=day,
        revelation_preview=revelation_preview,
        connection_id=connection_id,
        db=db
    )
    
    return {"success": True, "message": "Revelation notification queued"}

@router.post("/photo-reveal")
async def notify_photo_reveal(
    revealer_name: str,
    connection_id: int,
    recipient_user_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send photo reveal notification
    """
    push_service = get_push_service()
    
    background_tasks.add_task(
        push_service.notify_photo_reveal,
        user_id=recipient_user_id,
        revealer_name=revealer_name,
        connection_id=connection_id,
        db=db
    )
    
    return {"success": True, "message": "Photo reveal notification queued"}

@router.post("/revelation-reminder")
async def send_revelation_reminder(
    connection_id: int,
    day: int,
    user_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send revelation reminder notification
    """
    push_service = get_push_service()
    
    background_tasks.add_task(
        push_service.notify_revelation_reminder,
        user_id=user_id,
        connection_id=connection_id,
        day=day,
        db=db
    )
    
    return {"success": True, "message": "Revelation reminder queued"}

# Notification preferences management

@router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(
    current_user: User = Depends(get_current_user)
):
    """
    Get user's notification preferences
    """
    try:
        push_service = get_push_service()
        
        # This would get preferences from cache/database
        # For now, returning default preferences
        default_prefs = {
            "new_message": True,
            "new_match": True,
            "new_revelation": True,
            "photo_reveal": True,
            "connection_request": True,
            "revelation_reminder": True,
            "daily_prompt": False,
            "match_expiring": True,
            "profile_view": False,
            "system_announcement": True
        }
        
        return NotificationPreferencesResponse(
            user_id=current_user.id,
            preferences=default_prefs,
            updated_at=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get preferences: {str(e)}"
        )

@router.put("/preferences")
async def update_notification_preferences(
    preferences: NotificationPreferencesRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Update user's notification preferences
    """
    try:
        push_service = get_push_service()
        
        # Convert to dictionary
        prefs_dict = {
            "new_message": preferences.new_message,
            "new_match": preferences.new_match,
            "new_revelation": preferences.new_revelation,
            "photo_reveal": preferences.photo_reveal,
            "connection_request": preferences.connection_request,
            "revelation_reminder": preferences.revelation_reminder,
            "daily_prompt": preferences.daily_prompt,
            "match_expiring": preferences.match_expiring,
            "profile_view": preferences.profile_view,
            "system_announcement": preferences.system_announcement
        }
        
        success = await push_service.update_notification_preferences(
            user_id=current_user.id,
            preferences=prefs_dict
        )
        
        if success:
            return {
                "success": True,
                "message": "Notification preferences updated successfully",
                "user_id": current_user.id,
                "preferences": prefs_dict
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Failed to update notification preferences"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update preferences: {str(e)}"
        )

# Analytics and monitoring

@router.get("/analytics", response_model=NotificationAnalyticsResponse)
async def get_notification_analytics(
    days: int = 30,
    current_user: User = Depends(get_current_user)
):
    """
    Get notification analytics for user
    """
    try:
        push_service = get_push_service()
        
        analytics = await push_service.get_notification_analytics(
            user_id=current_user.id,
            days=days
        )
        
        return NotificationAnalyticsResponse(
            total_sent=analytics.get("total_sent", 0),
            delivery_rate=analytics.get("delivery_rate", 0.0),
            click_rate=analytics.get("click_rate", 0.0),
            most_effective_type=analytics.get("most_effective_type"),
            period_days=days
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get analytics: {str(e)}"
        )

@router.post("/track-click/{notification_id}")
async def track_notification_click(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Track notification click for analytics
    """
    try:
        push_service = get_push_service()
        
        success = await push_service.track_notification_click(
            user_id=current_user.id,
            notification_id=notification_id,
            db=db
        )
        
        if success:
            return {
                "success": True,
                "message": "Click tracked successfully"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Notification not found"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to track click: {str(e)}"
        )

@router.get("/subscriptions")
async def get_user_subscriptions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's active push subscriptions
    """
    try:
        from app.services.push_notification import PushSubscription
        
        subscriptions = db.query(PushSubscription).filter(
            PushSubscription.user_id == current_user.id,
            PushSubscription.is_active == True
        ).all()
        
        subscription_data = []
        for sub in subscriptions:
            subscription_data.append({
                "id": sub.id,
                "endpoint": sub.endpoint[:50] + "..." if len(sub.endpoint) > 50 else sub.endpoint,
                "user_agent": sub.user_agent,
                "created_at": sub.created_at.isoformat(),
                "last_used": sub.last_used.isoformat() if sub.last_used else None
            })
        
        return {
            "user_id": current_user.id,
            "subscriptions": subscription_data,
            "total_active": len(subscription_data)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get subscriptions: {str(e)}"
        )

@router.post("/test")
async def test_notification(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a test notification to verify push setup
    """
    try:
        push_service = get_push_service()
        
        success = await push_service.send_notification(
            user_id=current_user.id,
            notification_type=NotificationType.SYSTEM_ANNOUNCEMENT,
            context={
                "title": "Test Notification 🔔",
                "body": "Your push notifications are working perfectly!"
            },
            db=db
        )
        
        if success:
            return {
                "success": True,
                "message": "Test notification sent successfully"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Failed to send test notification. Check your subscription."
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Test notification failed: {str(e)}"
        )