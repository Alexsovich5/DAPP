"""
Revelation Scheduler Service - Background task system for revelation reminders
Implements daily revelation prompts and streak maintenance notifications
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.soul_connection import SoulConnection
from app.models.user import User
from app.services.revelation_service import RevelationService
from app.services.push_notification import send_notification


logger = logging.getLogger(__name__)


class RevelationScheduler:
    """Service for managing revelation reminders and background tasks"""
    
    def __init__(self):
        self.is_running = False
        self.scheduler_tasks = []
        self.notification_queue = []
        
    async def start_scheduler(self):
        """Start the background revelation reminder scheduler"""
        if self.is_running:
            logger.warning("Revelation scheduler already running")
            return
            
        self.is_running = True
        logger.info("Starting revelation reminder scheduler")
        
        # Start background tasks
        tasks = [
            asyncio.create_task(self._daily_reminder_task()),
            asyncio.create_task(self._streak_maintenance_task()),
            asyncio.create_task(self._notification_processor())
        ]
        
        self.scheduler_tasks = tasks
        
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("Revelation scheduler stopped")
        except Exception as e:
            logger.error(f"Revelation scheduler error: {str(e)}")
        finally:
            self.is_running = False

    async def stop_scheduler(self):
        """Stop the background scheduler"""
        if not self.is_running:
            return
            
        logger.info("Stopping revelation reminder scheduler")
        self.is_running = False
        
        for task in self.scheduler_tasks:
            task.cancel()
            
        await asyncio.gather(*self.scheduler_tasks, return_exceptions=True)
        self.scheduler_tasks = []

    async def _daily_reminder_task(self):
        """Main task for sending daily revelation reminders"""
        while self.is_running:
            try:
                # Get database session
                db = next(get_db())
                
                # Check active connections for reminders
                await self._process_daily_reminders(db)
                
                # Wait 2 hours before next check
                await asyncio.sleep(2 * 60 * 60)  # 2 hours
                
            except Exception as e:
                logger.error(f"Error in daily reminder task: {str(e)}")
                await asyncio.sleep(30 * 60)  # Wait 30 minutes on error
            finally:
                if 'db' in locals():
                    db.close()

    async def _process_daily_reminders(self, db: Session):
        """Process daily revelation reminders for all active connections"""
        revelation_service = RevelationService(db)
        
        # Get all active connections
        active_connections = db.query(SoulConnection).filter(
            SoulConnection.status == "active"
        ).all()
        
        reminder_count = 0
        
        for connection in active_connections:
            try:
                # Check if reminders are needed
                reminder_data = revelation_service.check_revelation_reminder_eligibility(
                    db, connection.id
                )
                
                if reminder_data.get("needs_reminder"):
                    await self._send_revelation_reminders(db, connection, reminder_data)
                    reminder_count += 1
                    
            except Exception as e:
                logger.error(f"Error processing reminder for connection {connection.id}: {str(e)}")
        
        if reminder_count > 0:
            logger.info(f"Sent revelation reminders for {reminder_count} connections")

    async def _send_revelation_reminders(self, db: Session, connection: SoulConnection, reminder_data: Dict):
        """Send revelation reminder notifications to users"""
        current_day = reminder_data["current_day"]
        
        # Get revelation prompt for today
        revelation_service = RevelationService(db)
        day_info = revelation_service.get_revelation_for_day(current_day)
        
        if not day_info:
            return
        
        # Send reminder to user1 if needed
        if reminder_data.get("user1_needs_reminder"):
            user1 = db.query(User).filter(User.id == connection.user1_id).first()
            if user1:
                await self._queue_reminder_notification(
                    user1, connection, current_day, day_info
                )
        
        # Send reminder to user2 if needed
        if reminder_data.get("user2_needs_reminder"):
            user2 = db.query(User).filter(User.id == connection.user2_id).first()
            if user2:
                await self._queue_reminder_notification(
                    user2, connection, current_day, day_info
                )

    async def _queue_reminder_notification(self, user: User, connection: SoulConnection, day: int, day_info: Dict):
        """Queue a reminder notification for a user"""
        # Get partner name
        partner_id = connection.get_partner_id(user.id)
        partner = user # Default fallback
        try:
            db = next(get_db())
            partner = db.query(User).filter(User.id == partner_id).first()
        except:
            pass
        finally:
            if 'db' in locals():
                db.close()
        
        partner_name = partner.first_name if partner else "your soul connection"
        
        notification = {
            "user_id": user.id,
            "title": f"✨ Day {day} Soul Revelation",
            "message": f"Share your soul with {partner_name}: {day_info['prompt']}",
            "type": "revelation_reminder",
            "data": {
                "connection_id": connection.id,
                "day": day,
                "prompt": day_info["prompt"]
            },
            "scheduled_time": datetime.utcnow()
        }
        
        self.notification_queue.append(notification)

    async def _streak_maintenance_task(self):
        """Task for maintaining revelation streaks and sending streak notifications"""
        while self.is_running:
            try:
                db = next(get_db())
                await self._process_streak_maintenance(db)
                
                # Check streaks once per day
                await asyncio.sleep(24 * 60 * 60)  # 24 hours
                
            except Exception as e:
                logger.error(f"Error in streak maintenance task: {str(e)}")
                await asyncio.sleep(60 * 60)  # Wait 1 hour on error
            finally:
                if 'db' in locals():
                    db.close()

    async def _process_streak_maintenance(self, db: Session):
        """Process streak maintenance for all users"""
        revelation_service = RevelationService(db)
        
        # Get all users with active connections
        users_with_connections = db.query(User).join(
            SoulConnection,
            (SoulConnection.user1_id == User.id) | (SoulConnection.user2_id == User.id)
        ).filter(
            SoulConnection.status == "active"
        ).distinct().all()
        
        streak_notifications = 0
        
        for user in users_with_connections:
            try:
                # Get global streak data
                global_streak = revelation_service.get_global_revelation_streak(db, user.id)
                
                # Check for streak achievements
                if global_streak["longest_overall_streak"] in [3, 5, 7]:
                    await self._send_streak_achievement_notification(user, global_streak)
                    streak_notifications += 1
                    
                # Check for streak at risk (hasn't shared in 18+ hours)
                await self._check_streak_at_risk(db, user, revelation_service)
                
            except Exception as e:
                logger.error(f"Error processing streak for user {user.id}: {str(e)}")
        
        if streak_notifications > 0:
            logger.info(f"Sent streak notifications for {streak_notifications} users")

    async def _send_streak_achievement_notification(self, user: User, streak_data: Dict):
        """Send streak achievement notification"""
        longest_streak = streak_data["longest_overall_streak"]
        
        achievement_messages = {
            3: "🔥 3-Day Streak! You're building beautiful soul connections!",
            5: "⭐ 5-Day Streak! Your consistency is creating deeper bonds!",
            7: "✨ Perfect Week! You've mastered the art of soul revelation!"
        }
        
        message = achievement_messages.get(longest_streak, f"🎉 {longest_streak}-Day Streak!")
        
        notification = {
            "user_id": user.id,
            "title": "Revelation Streak Achievement!",
            "message": message,
            "type": "streak_achievement",
            "data": {
                "streak_length": longest_streak,
                "total_connections": streak_data["total_connections_with_streaks"]
            },
            "scheduled_time": datetime.utcnow()
        }
        
        self.notification_queue.append(notification)

    async def _check_streak_at_risk(self, db: Session, user: User, revelation_service: RevelationService):
        """Check if user's streak is at risk and send warning"""
        # Get user's active connections
        connections = db.query(SoulConnection).filter(
            (SoulConnection.user1_id == user.id) | (SoulConnection.user2_id == user.id),
            SoulConnection.status == "active"
        ).all()
        
        for connection in connections:
            current_day = revelation_service.get_current_revelation_day(connection)
            if current_day > 7:  # Completed cycle
                continue
                
            # Check if user shared today
            from app.models.daily_revelation import DailyRevelation
            today_revelation = db.query(DailyRevelation).filter(
                DailyRevelation.connection_id == connection.id,
                DailyRevelation.sender_id == user.id,
                DailyRevelation.day_number == current_day
            ).first()
            
            if not today_revelation:
                # Check if it's been more than 18 hours since day unlocked
                hours_since_creation = (datetime.utcnow() - connection.created_at).total_seconds() / 3600
                day_hours = (current_day - 1) * 24
                hours_since_unlock = hours_since_creation - day_hours
                
                if hours_since_unlock > 18:
                    await self._send_streak_risk_notification(user, connection, current_day)

    async def _send_streak_risk_notification(self, user: User, connection: SoulConnection, day: int):
        """Send streak at risk notification"""
        notification = {
            "user_id": user.id,
            "title": "⚠️ Streak at Risk!",
            "message": f"Don't break your revelation streak! Share your Day {day} soul story.",
            "type": "streak_risk",
            "data": {
                "connection_id": connection.id,
                "day": day
            },
            "scheduled_time": datetime.utcnow()
        }
        
        self.notification_queue.append(notification)

    async def _notification_processor(self):
        """Process the notification queue"""
        while self.is_running:
            try:
                if self.notification_queue:
                    # Process up to 10 notifications at a time
                    batch = self.notification_queue[:10]
                    self.notification_queue = self.notification_queue[10:]
                    
                    for notification in batch:
                        try:
                            await self._send_notification(notification)
                        except Exception as e:
                            logger.error(f"Error sending notification: {str(e)}")
                
                # Wait 30 seconds before next batch
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in notification processor: {str(e)}")
                await asyncio.sleep(60)

    async def _send_notification(self, notification: Dict):
        """Send a single notification"""
        try:
            # Use existing push notification service
            await send_notification(
                user_id=notification["user_id"],
                title=notification["title"],
                message=notification["message"],
                notification_type=notification["type"],
                data=notification.get("data", {})
            )
            
            logger.debug(f"Sent notification to user {notification['user_id']}: {notification['title']}")
            
        except Exception as e:
            logger.error(f"Failed to send notification to user {notification['user_id']}: {str(e)}")

    # Manual trigger methods for testing and admin use

    async def trigger_daily_reminders(self, db: Session) -> Dict[str, Any]:
        """Manually trigger daily reminder processing"""
        try:
            await self._process_daily_reminders(db)
            return {"success": True, "message": "Daily reminders processed"}
        except Exception as e:
            logger.error(f"Error triggering daily reminders: {str(e)}")
            return {"success": False, "error": str(e)}

    async def trigger_streak_maintenance(self, db: Session) -> Dict[str, Any]:
        """Manually trigger streak maintenance"""
        try:
            await self._process_streak_maintenance(db)
            return {"success": True, "message": "Streak maintenance processed"}
        except Exception as e:
            logger.error(f"Error triggering streak maintenance: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        return {
            "is_running": self.is_running,
            "active_tasks": len(self.scheduler_tasks),
            "notification_queue_size": len(self.notification_queue),
            "last_check": datetime.utcnow().isoformat()
        }


# Global scheduler instance
revelation_scheduler = RevelationScheduler()


def get_revelation_scheduler() -> RevelationScheduler:
    """Factory function to get revelation scheduler instance"""
    return revelation_scheduler