# Push Notification Service for Dinner First Dating Platform
# Comprehensive push notification system with dating-specific features

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import logging
import json
import asyncio
from pywebpush import webpush, WebPushException
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import redis
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from app.core.database import Base

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    NEW_MESSAGE = "new_message"
    NEW_MATCH = "new_match"
    NEW_REVELATION = "new_revelation"
    PHOTO_REVEAL = "photo_reveal"
    CONNECTION_REQUEST = "connection_request"
    REVELATION_REMINDER = "revelation_reminder"
    DAILY_PROMPT = "daily_prompt"
    MATCH_EXPIRING = "match_expiring"
    PROFILE_VIEW = "profile_view"
    SYSTEM_ANNOUNCEMENT = "system_announcement"

class NotificationPriority(Enum):
    URGENT = "urgent"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

@dataclass
class NotificationPayload:
    title: str
    body: str
    icon: str = "/assets/icons/icon-192x192.png"
    badge: str = "/assets/icons/badge-72x72.png"
    image: Optional[str] = None
    tag: Optional[str] = None
    data: Dict[str, Any] = None
    actions: List[Dict[str, str]] = None
    require_interaction: bool = False
    silent: bool = False
    vibrate: List[int] = None
    timestamp: int = None

class PushSubscription(Base):
    __tablename__ = "push_subscriptions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    endpoint = Column(Text, nullable=False)
    p256dh_key = Column(Text, nullable=False)
    auth_key = Column(Text, nullable=False)
    user_agent = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, default=datetime.utcnow)

class NotificationLog(Base):
    __tablename__ = "notification_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    notification_type = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    payload = Column(JSON)
    sent_at = Column(DateTime, default=datetime.utcnow)
    delivered = Column(Boolean, default=False)
    clicked = Column(Boolean, default=False)
    error_message = Column(Text)

class PushNotificationService:
    """
    Comprehensive push notification service for dating platform
    """
    
    def __init__(self, redis_client: redis.Redis, vapid_private_key: str, vapid_public_key: str, vapid_email: str):
        self.redis_client = redis_client
        self.vapid_private_key = vapid_private_key
        self.vapid_public_key = vapid_public_key
        self.vapid_email = vapid_email
        
        # Notification templates for dating app
        self.notification_templates = {
            NotificationType.NEW_MESSAGE: {
                "title": "New message from {sender_name}",
                "body": "{message_preview}",
                "actions": [
                    {"action": "reply", "title": "Reply"},
                    {"action": "view_profile", "title": "View Profile"}
                ],
                "vibrate": [100, 50, 100],
                "require_interaction": False
            },
            NotificationType.NEW_MATCH: {
                "title": "You have a new soul connection! 💫",
                "body": "You and {match_name} have a compatibility score of {compatibility}%",
                "actions": [
                    {"action": "view_profile", "title": "View Profile"},
                    {"action": "start_conversation", "title": "Say Hello"}
                ],
                "vibrate": [200, 100, 200, 100, 200],
                "require_interaction": True
            },
            NotificationType.NEW_REVELATION: {
                "title": "New revelation from {sender_name} ✨",
                "body": "Day {day}: {revelation_preview}",
                "actions": [
                    {"action": "view_revelation", "title": "View Revelation"},
                    {"action": "respond", "title": "Respond"}
                ],
                "vibrate": [300, 200, 100, 200, 300]
            },
            NotificationType.PHOTO_REVEAL: {
                "title": "Photo reveal time! 📸",
                "body": "{name} has chosen to reveal their photos to you",
                "actions": [
                    {"action": "view_photos", "title": "View Photos"}
                ],
                "vibrate": [500],
                "require_interaction": True
            },
            NotificationType.CONNECTION_REQUEST: {
                "title": "Someone wants to connect with your soul 💞",
                "body": "A compatible soul is interested in getting to know you",
                "actions": [
                    {"action": "view_request", "title": "View Request"},
                    {"action": "accept", "title": "Accept"}
                ],
                "vibrate": [200, 100, 200]
            },
            NotificationType.REVELATION_REMINDER: {
                "title": "Time to share your daily revelation ⏰",
                "body": "Your soul connection is waiting for today's revelation",
                "actions": [
                    {"action": "create_revelation", "title": "Share Now"}
                ],
                "vibrate": [150, 150, 150]
            },
            NotificationType.DAILY_PROMPT: {
                "title": "Daily soul prompt 🌟",
                "body": "Today's question: {prompt_text}",
                "actions": [
                    {"action": "answer_prompt", "title": "Answer"}
                ],
                "vibrate": [100, 100]
            },
            NotificationType.MATCH_EXPIRING: {
                "title": "Connection expiring soon ⏳",
                "body": "Your connection with {name} expires in {hours} hours",
                "actions": [
                    {"action": "continue_connection", "title": "Continue"}
                ],
                "vibrate": [200, 200, 200]
            }
        }
        
        # User preference defaults
        self.default_preferences = {
            NotificationType.NEW_MESSAGE: True,
            NotificationType.NEW_MATCH: True,
            NotificationType.NEW_REVELATION: True,
            NotificationType.PHOTO_REVEAL: True,
            NotificationType.CONNECTION_REQUEST: True,
            NotificationType.REVELATION_REMINDER: True,
            NotificationType.DAILY_PROMPT: False,
            NotificationType.MATCH_EXPIRING: True,
            NotificationType.PROFILE_VIEW: False,
            NotificationType.SYSTEM_ANNOUNCEMENT: True
        }
    
    async def subscribe_user(self, user_id: int, subscription_data: Dict[str, Any], 
                           user_agent: str = None, db: Session = None) -> bool:
        """Subscribe user for push notifications"""
        try:
            # Extract subscription details
            endpoint = subscription_data.get('endpoint')
            keys = subscription_data.get('keys', {})
            p256dh_key = keys.get('p256dh')
            auth_key = keys.get('auth')
            
            if not all([endpoint, p256dh_key, auth_key]):
                raise ValueError("Invalid subscription data")
            
            # Check if subscription already exists
            existing_subscription = db.query(PushSubscription).filter(
                PushSubscription.user_id == user_id,
                PushSubscription.endpoint == endpoint
            ).first()
            
            if existing_subscription:
                # Update existing subscription
                existing_subscription.p256dh_key = p256dh_key
                existing_subscription.auth_key = auth_key
                existing_subscription.user_agent = user_agent
                existing_subscription.is_active = True
                existing_subscription.last_used = datetime.utcnow()
            else:
                # Create new subscription
                new_subscription = PushSubscription(
                    user_id=user_id,
                    endpoint=endpoint,
                    p256dh_key=p256dh_key,
                    auth_key=auth_key,
                    user_agent=user_agent
                )
                db.add(new_subscription)
            
            db.commit()
            
            # Send welcome notification
            await self.send_welcome_notification(user_id, db)
            
            logger.info(f"Push subscription added for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to subscribe user {user_id}: {e}")
            db.rollback()
            return False
    
    async def send_notification(self, user_id: int, notification_type: NotificationType,
                              context: Dict[str, Any] = None, db: Session = None) -> bool:
        """Send notification to user"""
        try:
            # Check user notification preferences
            if not await self.should_send_notification(user_id, notification_type):
                return False
            
            # Get user subscriptions
            subscriptions = db.query(PushSubscription).filter(
                PushSubscription.user_id == user_id,
                PushSubscription.is_active == True
            ).all()
            
            if not subscriptions:
                logger.info(f"No active subscriptions for user {user_id}")
                return False
            
            # Generate notification payload
            payload = self.create_notification_payload(notification_type, context or {})
            
            # Send to all user subscriptions
            success_count = 0
            for subscription in subscriptions:
                if await self.send_to_subscription(subscription, payload, db):
                    success_count += 1
            
            # Log notification
            await self.log_notification(user_id, notification_type, payload, 
                                      success_count > 0, db)
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Failed to send notification to user {user_id}: {e}")
            return False
    
    async def send_to_subscription(self, subscription: PushSubscription, 
                                 payload: NotificationPayload, db: Session) -> bool:
        """Send notification to specific subscription"""
        try:
            # Prepare webpush data
            subscription_info = {
                "endpoint": subscription.endpoint,
                "keys": {
                    "p256dh": subscription.p256dh_key,
                    "auth": subscription.auth_key
                }
            }
            
            # Create notification data
            notification_data = {
                "title": payload.title,
                "body": payload.body,
                "icon": payload.icon,
                "badge": payload.badge,
                "tag": payload.tag,
                "data": payload.data or {},
                "timestamp": payload.timestamp or int(datetime.now().timestamp() * 1000)
            }
            
            if payload.image:
                notification_data["image"] = payload.image
            
            if payload.actions:
                notification_data["actions"] = payload.actions
            
            if payload.require_interaction:
                notification_data["requireInteraction"] = True
            
            if payload.silent:
                notification_data["silent"] = True
            
            if payload.vibrate:
                notification_data["vibrate"] = payload.vibrate
            
            # Send notification
            webpush(
                subscription_info=subscription_info,
                data=json.dumps(notification_data),
                vapid_private_key=self.vapid_private_key,
                vapid_claims={
                    "sub": f"mailto:{self.vapid_email}",
                    "aud": subscription.endpoint
                }
            )
            
            # Update subscription last used time
            subscription.last_used = datetime.utcnow()
            db.commit()
            
            return True
            
        except WebPushException as e:
            logger.error(f"WebPush error: {e}")
            
            # Handle subscription errors
            if e.response and e.response.status_code in [404, 410]:
                # Subscription is no longer valid
                subscription.is_active = False
                db.commit()
                logger.info(f"Deactivated invalid subscription for user {subscription.user_id}")
            
            return False
        except Exception as e:
            logger.error(f"Failed to send to subscription: {e}")
            return False
    
    def create_notification_payload(self, notification_type: NotificationType, 
                                  context: Dict[str, Any]) -> NotificationPayload:
        """Create notification payload from template and context"""
        template = self.notification_templates.get(notification_type, {})
        
        # Format title and body with context
        title = template.get("title", "Dinner First").format(**context)
        body = template.get("body", "You have a new notification").format(**context)
        
        # Create payload
        payload = NotificationPayload(
            title=title,
            body=body,
            tag=f"{notification_type.value}_{context.get('id', '')}",
            data={
                "type": notification_type.value,
                "timestamp": int(datetime.now().timestamp()),
                **context
            },
            actions=template.get("actions"),
            require_interaction=template.get("require_interaction", False),
            silent=template.get("silent", False),
            vibrate=template.get("vibrate"),
            timestamp=int(datetime.now().timestamp() * 1000)
        )
        
        return payload
    
    async def send_bulk_notifications(self, notifications: List[Dict[str, Any]], 
                                    db: Session) -> Dict[str, int]:
        """Send multiple notifications efficiently"""
        results = {"sent": 0, "failed": 0}
        
        # Group notifications by user for efficiency
        user_notifications = {}
        for notification in notifications:
            user_id = notification["user_id"]
            if user_id not in user_notifications:
                user_notifications[user_id] = []
            user_notifications[user_id].append(notification)
        
        # Send notifications in batches
        batch_size = 50
        for i in range(0, len(user_notifications), batch_size):
            batch_users = list(user_notifications.keys())[i:i + batch_size]
            
            tasks = []
            for user_id in batch_users:
                for notification in user_notifications[user_id]:
                    task = self.send_notification(
                        user_id=user_id,
                        notification_type=NotificationType(notification["type"]),
                        context=notification.get("context", {}),
                        db=db
                    )
                    tasks.append(task)
            
            # Execute batch
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, bool) and result:
                    results["sent"] += 1
                else:
                    results["failed"] += 1
            
            # Small delay between batches to avoid overwhelming the service
            await asyncio.sleep(0.1)
        
        return results
    
    # Dating app specific notification methods
    async def notify_new_message(self, user_id: int, sender_name: str, message_preview: str,
                                connection_id: int, db: Session) -> bool:
        """Send new message notification"""
        return await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.NEW_MESSAGE,
            context={
                "sender_name": sender_name,
                "message_preview": message_preview[:50] + "..." if len(message_preview) > 50 else message_preview,
                "connectionId": connection_id
            },
            db=db
        )
    
    async def notify_new_match(self, user_id: int, match_name: str, compatibility_score: float,
                             match_id: int, db: Session) -> bool:
        """Send new match notification"""
        return await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.NEW_MATCH,
            context={
                "match_name": match_name,
                "compatibility": int(compatibility_score),
                "matchId": match_id
            },
            db=db
        )
    
    async def notify_new_revelation(self, user_id: int, sender_name: str, day: int,
                                  revelation_preview: str, connection_id: int, db: Session) -> bool:
        """Send new revelation notification"""
        return await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.NEW_REVELATION,
            context={
                "sender_name": sender_name,
                "day": day,
                "revelation_preview": revelation_preview[:40] + "..." if len(revelation_preview) > 40 else revelation_preview,
                "connectionId": connection_id
            },
            db=db
        )
    
    async def notify_photo_reveal(self, user_id: int, revealer_name: str, 
                                connection_id: int, db: Session) -> bool:
        """Send photo reveal notification"""
        return await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.PHOTO_REVEAL,
            context={
                "name": revealer_name,
                "connectionId": connection_id
            },
            db=db
        )
    
    async def notify_connection_request(self, user_id: int, requester_name: str,
                                      compatibility_score: float, db: Session) -> bool:
        """Send connection request notification"""
        return await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.CONNECTION_REQUEST,
            context={
                "requester_name": requester_name,
                "compatibility": int(compatibility_score)
            },
            db=db
        )
    
    async def notify_revelation_reminder(self, user_id: int, connection_id: int, 
                                       day: int, db: Session) -> bool:
        """Send revelation reminder notification"""
        return await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.REVELATION_REMINDER,
            context={
                "connectionId": connection_id,
                "day": day
            },
            db=db
        )
    
    async def send_welcome_notification(self, user_id: int, db: Session) -> bool:
        """Send welcome notification to new subscriber"""
        return await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.SYSTEM_ANNOUNCEMENT,
            context={
                "title": "Welcome to Dinner First! 🌟",
                "body": "You'll now receive notifications for soul connections, revelations, and messages"
            },
            db=db
        )
    
    # Notification preferences and management
    async def should_send_notification(self, user_id: int, notification_type: NotificationType) -> bool:
        """Check if user wants to receive this type of notification"""
        try:
            # Get user preferences from cache or database
            cache_key = f"notification_prefs:{user_id}"
            cached_prefs = self.redis_client.get(cache_key)
            
            if cached_prefs:
                prefs = json.loads(cached_prefs)
            else:
                # Load from database (would need to implement user preferences table)
                prefs = self.default_preferences
                
                # Cache for 1 hour
                self.redis_client.setex(
                    cache_key, 
                    3600, 
                    json.dumps({k.value: v for k, v in prefs.items()})
                )
            
            return prefs.get(notification_type.value, True)
            
        except Exception as e:
            logger.error(f"Error checking notification preferences: {e}")
            return True  # Default to sending notifications
    
    async def update_notification_preferences(self, user_id: int, 
                                            preferences: Dict[str, bool]) -> bool:
        """Update user notification preferences"""
        try:
            # Update cache
            cache_key = f"notification_prefs:{user_id}"
            self.redis_client.setex(cache_key, 3600, json.dumps(preferences))
            
            # TODO: Update database table with user preferences
            
            return True
        except Exception as e:
            logger.error(f"Failed to update notification preferences: {e}")
            return False
    
    async def log_notification(self, user_id: int, notification_type: NotificationType,
                             payload: NotificationPayload, delivered: bool, db: Session) -> None:
        """Log notification for analytics"""
        try:
            log_entry = NotificationLog(
                user_id=user_id,
                notification_type=notification_type.value,
                title=payload.title,
                body=payload.body,
                payload=asdict(payload),
                delivered=delivered
            )
            
            db.add(log_entry)
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log notification: {e}")
    
    async def track_notification_click(self, user_id: int, notification_id: int, 
                                     db: Session) -> bool:
        """Track notification click for analytics"""
        try:
            notification_log = db.query(NotificationLog).filter(
                NotificationLog.id == notification_id,
                NotificationLog.user_id == user_id
            ).first()
            
            if notification_log:
                notification_log.clicked = True
                db.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to track notification click: {e}")
        
        return False
    
    async def get_notification_analytics(self, user_id: int = None, 
                                       days: int = 30) -> Dict[str, Any]:
        """Get notification analytics"""
        try:
            # This would query the notification logs table
            # Return analytics like delivery rates, click rates, etc.
            return {
                "total_sent": 0,
                "delivery_rate": 0.0,
                "click_rate": 0.0,
                "most_effective_type": None
            }
        except Exception as e:
            logger.error(f"Failed to get notification analytics: {e}")
            return {}
    
    async def cleanup_old_subscriptions(self, days: int = 30, db: Session = None) -> int:
        """Clean up old inactive subscriptions"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            old_subscriptions = db.query(PushSubscription).filter(
                PushSubscription.last_used < cutoff_date,
                PushSubscription.is_active == False
            ).all()
            
            count = len(old_subscriptions)
            
            for subscription in old_subscriptions:
                db.delete(subscription)
            
            db.commit()
            
            logger.info(f"Cleaned up {count} old subscriptions")
            return count
            
        except Exception as e:
            logger.error(f"Failed to cleanup subscriptions: {e}")
            return 0

# Global push notification service instance
_push_service: Optional[PushNotificationService] = None

def get_push_service() -> PushNotificationService:
    """Get global push notification service instance"""
    global _push_service
    if _push_service is None:
        raise RuntimeError("Push notification service not initialized")
    return _push_service

def init_push_service(redis_client: redis.Redis, vapid_private_key: str,
                     vapid_public_key: str, vapid_email: str) -> PushNotificationService:
    """Initialize global push notification service"""
    global _push_service
    _push_service = PushNotificationService(
        redis_client, vapid_private_key, vapid_public_key, vapid_email
    )
    return _push_service