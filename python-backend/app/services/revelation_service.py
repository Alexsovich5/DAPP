"""
Revelation Service - Handles the 7-day soul revelation cycle
Implements the progressive revelation system from CLAUDE.md
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum

from sqlalchemy.orm import Session
from app.models.user import User
from app.models.soul_connection import SoulConnection
from app.models.daily_revelation import DailyRevelation
from app.models.message import Message, MessageType


class RevelationType(str, Enum):
    PERSONAL_VALUE = "personal_value"
    MEANINGFUL_EXPERIENCE = "meaningful_experience" 
    HOPE_OR_DREAM = "hope_or_dream"
    WHAT_MAKES_LAUGH = "what_makes_laugh"
    CHALLENGE_OVERCOME = "challenge_overcome"
    IDEAL_CONNECTION = "ideal_connection"
    PHOTO_REVEAL = "photo_reveal"


class RevelationService:
    """Service for managing the 7-day revelation cycle"""
    
    def __init__(self, db_session: Session = None):
        self.db_session = db_session
        self.revelation_cycle = {
            1: {
                "type": RevelationType.PERSONAL_VALUE,
                "prompt": "What do you value most in a relationship?",
                "description": "Share a personal value that guides your connections"
            },
            2: {
                "type": RevelationType.MEANINGFUL_EXPERIENCE,
                "prompt": "Describe a meaningful experience that shaped who you are today",
                "description": "Tell about a moment that changed or defined you"
            },
            3: {
                "type": RevelationType.HOPE_OR_DREAM,
                "prompt": "What's a hope or dream you hold close to your heart?",
                "description": "Share something you aspire to or dream about"
            },
            4: {
                "type": RevelationType.WHAT_MAKES_LAUGH,
                "prompt": "What makes you genuinely laugh or brings you joy?",
                "description": "Tell about what brings lightness to your life"
            },
            5: {
                "type": RevelationType.CHALLENGE_OVERCOME,
                "prompt": "Share a challenge you've overcome that made you stronger",
                "description": "Describe how you grew through a difficult time"
            },
            6: {
                "type": RevelationType.IDEAL_CONNECTION,
                "prompt": "Describe your ideal way to connect with someone special",
                "description": "Share what deep connection means to you"
            },
            7: {
                "type": RevelationType.PHOTO_REVEAL,
                "prompt": "Ready to reveal your photo?",
                "description": "The moment of visual revelation - if both consent"
            }
        }

    def get_current_revelation_day(self, connection: SoulConnection) -> int:
        """Calculate current revelation day based on connection creation date"""
        if not connection.created_at:
            return 1
            
        days_since_creation = (datetime.utcnow() - connection.created_at).days
        # Cap at day 7
        return min(days_since_creation + 1, 7)

    def get_revelation_for_day(self, day: int) -> Optional[Dict[str, Any]]:
        """Get revelation prompt and details for a specific day"""
        return self.revelation_cycle.get(day)

    def can_user_share_revelation(self, db: Session, connection_id: int, user_id: int, day: int) -> Dict[str, Any]:
        """Check if user can share a revelation for the given day"""
        connection = db.query(SoulConnection).filter(SoulConnection.id == connection_id).first()
        if not connection:
            return {"can_share": False, "reason": "Connection not found"}
            
        if user_id not in {connection.user1_id, connection.user2_id}:
            return {"can_share": False, "reason": "User not part of connection"}

        current_day = self.get_current_revelation_day(connection)
        
        if day > current_day:
            return {"can_share": False, "reason": f"Day {day} not yet unlocked. Current day: {current_day}"}
            
        # Check if user already shared for this day
        existing = db.query(DailyRevelation).filter(
            DailyRevelation.connection_id == connection_id,
            DailyRevelation.sender_id == user_id,
            DailyRevelation.day_number == day
        ).first()
        
        if existing:
            return {"can_share": False, "reason": f"Already shared revelation for day {day}"}
            
        return {"can_share": True, "revelation": self.get_revelation_for_day(day)}

    def create_revelation(self, db: Session, connection_id: int, user_id: int, day: int, content: str) -> Dict[str, Any]:
        """Create a new revelation entry"""
        # Validate user can share
        validation = self.can_user_share_revelation(db, connection_id, user_id, day)
        if not validation["can_share"]:
            return {"success": False, "error": validation["reason"]}

        revelation_info = self.get_revelation_for_day(day)
        if not revelation_info:
            return {"success": False, "error": "Invalid revelation day"}

        # Create revelation record
        revelation = DailyRevelation(
            connection_id=connection_id,
            sender_id=user_id,
            day_number=day,
            revelation_type=revelation_info["type"].value,
            content=content,
            created_at=datetime.utcnow()
        )
        
        db.add(revelation)
        
        # Create corresponding message
        message = Message(
            connection_id=connection_id,
            sender_id=user_id,
            message_text=f"✨ Day {day} Revelation: {content}",
            message_type=MessageType.REVELATION,
            created_at=datetime.utcnow()
        )
        
        db.add(message)
        db.commit()
        db.refresh(revelation)
        db.refresh(message)

        return {
            "success": True,
            "revelation": {
                "id": revelation.id,
                "day": day,
                "type": revelation_info["type"].value,
                "content": content,
                "created_at": revelation.created_at.isoformat()
            },
            "message": {
                "id": message.id,
                "content": message.message_text,
                "timestamp": message.created_at.isoformat()
            }
        }

    def get_connection_revelations(self, db: Session, connection_id: int, user_id: int) -> Dict[str, Any]:
        """Get all revelations for a connection that user can view"""
        connection = db.query(SoulConnection).filter(SoulConnection.id == connection_id).first()
        if not connection:
            return {"error": "Connection not found"}
            
        if user_id not in {connection.user1_id, connection.user2_id}:
            return {"error": "Access denied"}

        revelations = db.query(DailyRevelation).filter(
            DailyRevelation.connection_id == connection_id
        ).order_by(DailyRevelation.day_number.asc()).all()

        current_day = self.get_current_revelation_day(connection)
        
        revelation_timeline = []
        for day in range(1, 8):  # Days 1-7
            day_info = self.get_revelation_for_day(day)
            day_revelations = [r for r in revelations if r.day_number == day]
            
            user_revelation = next((r for r in day_revelations if r.sender_id == user_id), None)
            partner_revelation = next((r for r in day_revelations if r.sender_id != user_id), None)
            
            timeline_entry = {
                "day": day,
                "prompt": day_info["prompt"],
                "description": day_info["description"],
                "is_unlocked": day <= current_day,
                "user_shared": bool(user_revelation),
                "partner_shared": bool(partner_revelation),
                "user_content": user_revelation.content if user_revelation else None,
                "partner_content": partner_revelation.content if partner_revelation else None,
                "user_shared_at": user_revelation.created_at.isoformat() if user_revelation else None,
                "partner_shared_at": partner_revelation.created_at.isoformat() if partner_revelation else None
            }
            
            revelation_timeline.append(timeline_entry)

        return {
            "connection_id": connection_id,
            "current_day": current_day,
            "timeline": revelation_timeline,
            "completion_percentage": self.calculate_completion_percentage(revelation_timeline)
        }

    def calculate_completion_percentage(self, timeline: List[Dict]) -> float:
        """Calculate how much of the revelation cycle is complete"""
        total_possible = 0
        completed = 0
        
        for day_entry in timeline:
            if day_entry["is_unlocked"]:
                total_possible += 2  # Both users can share
                if day_entry["user_shared"]:
                    completed += 1
                if day_entry["partner_shared"]:
                    completed += 1
                    
        return round((completed / total_possible * 100), 1) if total_possible > 0 else 0.0

    def check_photo_reveal_eligibility(self, db: Session, connection_id: int) -> Dict[str, Any]:
        """Check if connection is eligible for photo reveal (Day 7)"""
        connection = db.query(SoulConnection).filter(SoulConnection.id == connection_id).first()
        if not connection:
            return {"eligible": False, "reason": "Connection not found"}

        current_day = self.get_current_revelation_day(connection)
        if current_day < 7:
            return {"eligible": False, "reason": f"Photo reveal unlocks on day 7. Current day: {current_day}"}

        # Check if both users have shared at least 4 revelations (Days 1-6)
        revelations = db.query(DailyRevelation).filter(
            DailyRevelation.connection_id == connection_id,
            DailyRevelation.day_number < 7
        ).all()

        user1_revelations = len([r for r in revelations if r.sender_id == connection.user1_id])
        user2_revelations = len([r for r in revelations if r.sender_id == connection.user2_id])

        min_revelations_required = 4  # At least 4 out of 6 days
        
        if user1_revelations < min_revelations_required or user2_revelations < min_revelations_required:
            return {
                "eligible": False,
                "reason": f"Both users must share at least {min_revelations_required} revelations before photo reveal",
                "user1_count": user1_revelations,
                "user2_count": user2_revelations
            }

        return {
            "eligible": True,
            "message": "Ready for photo reveal! Both users have shared enough of their souls.",
            "user1_revelations": user1_revelations,
            "user2_revelations": user2_revelations
        }

    def handle_photo_reveal_consent(self, db: Session, connection_id: int, user_id: int, consent: bool) -> Dict[str, Any]:
        """Handle user consent for photo reveal"""
        connection = db.query(SoulConnection).filter(SoulConnection.id == connection_id).first()
        if not connection:
            return {"success": False, "error": "Connection not found"}
            
        if user_id not in {connection.user1_id, connection.user2_id}:
            return {"success": False, "error": "Access denied"}

        # Check eligibility first
        eligibility = self.check_photo_reveal_eligibility(db, connection_id)
        if not eligibility["eligible"]:
            return {"success": False, "error": eligibility["reason"]}

        # Update connection with consent
        # In a real implementation, you'd track individual consent
        # For MVP, we'll use the mutual_reveal_consent field
        if consent:
            # Check if partner has also consented (simplified logic)
            # In production, you'd track individual consent
            connection.mutual_reveal_consent = True
            connection.connection_stage = "photo_reveal"
            
            # Create revelation entry for photo reveal
            revelation_result = self.create_revelation(
                db, connection_id, user_id, 7, 
                "I'm ready to reveal my photo and see yours! 📸✨"
            )
            
            db.commit()
            
            return {
                "success": True,
                "message": "Photo reveal consent recorded. You can now see each other's photos!",
                "connection_stage": connection.connection_stage,
                "revelation": revelation_result.get("revelation")
            }
        else:
            return {
                "success": True,
                "message": "Photo reveal consent declined. You can continue with text revelations.",
                "connection_stage": connection.connection_stage
            }

    def get_revelation_statistics(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Get revelation statistics for a user"""
        # Get all connections for user
        connections = db.query(SoulConnection).filter(
            (SoulConnection.user1_id == user_id) | (SoulConnection.user2_id == user_id)
        ).all()

        total_connections = len(connections)
        active_revelations = 0
        completed_cycles = 0
        total_revelations_shared = 0

        for connection in connections:
            current_day = self.get_current_revelation_day(connection)
            if current_day > 1:  # Has started revelations
                active_revelations += 1
                
            if current_day >= 7 and connection.mutual_reveal_consent:
                completed_cycles += 1

            # Count user's revelations for this connection
            user_revelations = db.query(DailyRevelation).filter(
                DailyRevelation.connection_id == connection.id,
                DailyRevelation.sender_id == user_id
            ).count()
            total_revelations_shared += user_revelations

        return {
            "total_connections": total_connections,
            "active_revelation_cycles": active_revelations,
            "completed_cycles": completed_cycles,
            "total_revelations_shared": total_revelations_shared,
            "average_revelations_per_connection": round(total_revelations_shared / max(total_connections, 1), 1)
        }

    def calculate_revelation_streak(self, db: Session, user_id: int, connection_id: int) -> Dict[str, Any]:
        """Calculate revelation sharing streak for a user in a specific connection"""
        connection = db.query(SoulConnection).filter(SoulConnection.id == connection_id).first()
        if not connection:
            return {"current_streak": 0, "longest_streak": 0, "total_days": 0}

        # Get all user's revelations for this connection ordered by day
        revelations = db.query(DailyRevelation).filter(
            DailyRevelation.connection_id == connection_id,
            DailyRevelation.sender_id == user_id
        ).order_by(DailyRevelation.day_number.asc()).all()

        if not revelations:
            return {"current_streak": 0, "longest_streak": 0, "total_days": 0}

        # Calculate current streak (consecutive days from most recent)
        current_day = self.get_current_revelation_day(connection)
        current_streak = 0
        
        # Check if user shared yesterday and today
        revelation_days = set(r.day_number for r in revelations)
        
        # Current streak: count backwards from current day
        for day in range(min(current_day, 7), 0, -1):
            if day in revelation_days:
                current_streak += 1
            else:
                break

        # Calculate longest streak
        longest_streak = 0
        temp_streak = 0
        
        for day in range(1, 8):
            if day in revelation_days:
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 0

        return {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "total_days": len(revelations),
            "streak_percentage": round((current_streak / current_day * 100), 1) if current_day > 0 else 0
        }

    def get_global_revelation_streak(self, db: Session, user_id: int) -> Dict[str, Any]:
        """Calculate user's overall revelation streak across all connections"""
        connections = db.query(SoulConnection).filter(
            (SoulConnection.user1_id == user_id) | (SoulConnection.user2_id == user_id)
        ).all()

        total_streaks = []
        active_streaks = []
        
        for connection in connections:
            streak_data = self.calculate_revelation_streak(db, user_id, connection.id)
            total_streaks.append(streak_data["longest_streak"])
            
            current_day = self.get_current_revelation_day(connection)
            if current_day <= 7:  # Active connection
                active_streaks.append(streak_data["current_streak"])

        return {
            "longest_overall_streak": max(total_streaks) if total_streaks else 0,
            "average_streak": round(sum(total_streaks) / len(total_streaks), 1) if total_streaks else 0,
            "active_connections_streak": sum(active_streaks),
            "total_connections_with_streaks": len([s for s in total_streaks if s > 0])
        }

    def check_revelation_reminder_eligibility(self, db: Session, connection_id: int) -> Dict[str, Any]:
        """Check if a connection needs revelation reminders"""
        connection = db.query(SoulConnection).filter(SoulConnection.id == connection_id).first()
        if not connection:
            return {"needs_reminder": False, "reason": "Connection not found"}

        current_day = self.get_current_revelation_day(connection)
        if current_day > 7:
            return {"needs_reminder": False, "reason": "Revelation cycle complete"}

        # Check if both users haven't shared for current day
        today_revelations = db.query(DailyRevelation).filter(
            DailyRevelation.connection_id == connection_id,
            DailyRevelation.day_number == current_day
        ).all()

        user1_shared = any(r.sender_id == connection.user1_id for r in today_revelations)
        user2_shared = any(r.sender_id == connection.user2_id for r in today_revelations)

        needs_reminder_user1 = not user1_shared
        needs_reminder_user2 = not user2_shared

        if not needs_reminder_user1 and not needs_reminder_user2:
            return {"needs_reminder": False, "reason": "Both users have shared today"}

        # Check last activity to avoid spam
        hours_since_creation = (datetime.utcnow() - connection.created_at).total_seconds() / 3600
        day_hours = (current_day - 1) * 24

        # Only send reminders if it's been at least 20 hours since the day unlocked
        if hours_since_creation < (day_hours + 20):
            return {"needs_reminder": False, "reason": "Too early for reminder"}

        return {
            "needs_reminder": True,
            "user1_needs_reminder": needs_reminder_user1,
            "user2_needs_reminder": needs_reminder_user2,
            "current_day": current_day,
            "hours_since_unlock": hours_since_creation - day_hours
        }

    def update_connection_timeline(self, db: Session, connection_id: int, stage_update: str) -> Dict[str, Any]:
        """Update connection timeline with stage progression"""
        connection = db.query(SoulConnection).filter(SoulConnection.id == connection_id).first()
        if not connection:
            return {"success": False, "error": "Connection not found"}

        # Initialize stage progression dates if not exists
        if not connection.stage_progression_dates:
            connection.stage_progression_dates = {}

        # Update stage progression tracking
        stage_progression = connection.stage_progression_dates.copy() if connection.stage_progression_dates else {}
        stage_progression[stage_update] = datetime.utcnow().isoformat()
        
        connection.stage_progression_dates = stage_progression
        connection.updated_at = datetime.utcnow()

        # Update specific timeline fields based on stage
        if stage_update == "revelation_started" and not connection.revelation_started_at:
            connection.revelation_started_at = datetime.utcnow()
        elif stage_update == "photo_reveal" and not connection.photo_revealed_at:
            connection.photo_revealed_at = datetime.utcnow()

        db.commit()
        
        return {
            "success": True,
            "connection_id": connection_id,
            "stage_updated": stage_update,
            "timeline": stage_progression
        }

    def calculate_revelation_progress(self, db: Session, connection_id: int) -> Dict[str, Any]:
        """Calculate detailed revelation progress for timeline visualization"""
        connection = db.query(SoulConnection).filter(SoulConnection.id == connection_id).first()
        if not connection:
            return {"error": "Connection not found"}

        # Get all revelations for this connection
        revelations = db.query(DailyRevelation).filter(
            DailyRevelation.connection_id == connection_id
        ).order_by(DailyRevelation.day_number.asc()).all()

        current_day = self.get_current_revelation_day(connection)
        
        # Build comprehensive timeline data
        timeline_data = {
            "connection_id": connection_id,
            "current_day": current_day,
            "total_days": 7,
            "days_completed": min(current_day - 1, 7),
            "progression_data": []
        }

        # Calculate progress for each day
        for day in range(1, 8):
            day_revelations = [r for r in revelations if r.day_number == day]
            user1_revelation = next((r for r in day_revelations if r.sender_id == connection.user1_id), None)
            user2_revelation = next((r for r in day_revelations if r.sender_id == connection.user2_id), None)
            
            day_info = self.get_revelation_for_day(day)
            
            # Calculate day completion status
            is_unlocked = day <= current_day
            user1_shared = bool(user1_revelation)
            user2_shared = bool(user2_revelation)
            both_shared = user1_shared and user2_shared
            
            day_progress = {
                "day": day,
                "is_unlocked": is_unlocked,
                "is_current": day == current_day,
                "prompt": day_info["prompt"] if day_info else "",
                "type": day_info["type"].value if day_info else "",
                "completion_status": {
                    "user1_shared": user1_shared,
                    "user2_shared": user2_shared,
                    "both_shared": both_shared,
                    "completion_percentage": (int(user1_shared) + int(user2_shared)) * 50
                },
                "timing": {
                    "user1_shared_at": user1_revelation.created_at.isoformat() if user1_revelation else None,
                    "user2_shared_at": user2_revelation.created_at.isoformat() if user2_revelation else None,
                    "time_to_mutual_share": self._calculate_mutual_share_time(user1_revelation, user2_revelation)
                },
                "content_preview": {
                    "user1_content": user1_revelation.content[:50] + "..." if user1_revelation and len(user1_revelation.content) > 50 else user1_revelation.content if user1_revelation else None,
                    "user2_content": user2_revelation.content[:50] + "..." if user2_revelation and len(user2_revelation.content) > 50 else user2_revelation.content if user2_revelation else None
                }
            }
            
            timeline_data["progression_data"].append(day_progress)

        # Calculate overall statistics
        total_revelations = len(revelations)
        user1_revelations = len([r for r in revelations if r.sender_id == connection.user1_id])
        user2_revelations = len([r for r in revelations if r.sender_id == connection.user2_id])
        
        mutual_days = len(set(r.day_number for r in revelations if r.sender_id == connection.user1_id) & 
                         set(r.day_number for r in revelations if r.sender_id == connection.user2_id))

        timeline_data["statistics"] = {
            "total_revelations_shared": total_revelations,
            "user1_revelations": user1_revelations,
            "user2_revelations": user2_revelations,
            "mutual_sharing_days": mutual_days,
            "overall_completion_percentage": round((total_revelations / 14) * 100, 1),
            "user1_completion_percentage": round((user1_revelations / 7) * 100, 1),
            "user2_completion_percentage": round((user2_revelations / 7) * 100, 1),
            "mutual_completion_percentage": round((mutual_days / 7) * 100, 1)
        }

        # Calculate quality metrics
        timeline_data["quality_metrics"] = self._calculate_revelation_quality_metrics(revelations, connection)

        # Generate insights and recommendations
        timeline_data["insights"] = self._generate_timeline_insights(timeline_data, connection)

        return timeline_data

    def _calculate_mutual_share_time(self, revelation1, revelation2) -> Optional[str]:
        """Calculate time difference between two revelations"""
        if not revelation1 or not revelation2:
            return None
        
        time_diff = abs((revelation1.created_at - revelation2.created_at).total_seconds())
        
        if time_diff < 3600:  # Less than 1 hour
            return f"{int(time_diff // 60)} minutes"
        elif time_diff < 86400:  # Less than 1 day
            return f"{int(time_diff // 3600)} hours"
        else:
            return f"{int(time_diff // 86400)} days"

    def _calculate_revelation_quality_metrics(self, revelations: List, connection) -> Dict[str, Any]:
        """Calculate quality metrics for revelations"""
        if not revelations:
            return {"average_length": 0, "emotional_depth": 0, "consistency": 0}

        # Calculate average content length
        total_length = sum(len(r.content) for r in revelations)
        average_length = total_length / len(revelations)

        # Simple emotional depth scoring based on content length and keywords
        emotional_keywords = ["feel", "love", "hope", "dream", "fear", "joy", "pain", "heart", "soul", "connection"]
        emotional_score = 0
        
        for revelation in revelations:
            content_lower = revelation.content.lower()
            keyword_count = sum(1 for keyword in emotional_keywords if keyword in content_lower)
            length_score = min(len(revelation.content) / 100, 1.0)  # Normalize to 0-1
            emotional_score += (keyword_count * 0.1) + (length_score * 0.5)

        emotional_depth = min(emotional_score / len(revelations), 1.0)

        # Calculate consistency (how regularly revelations are shared)
        days_with_revelations = len(set(r.day_number for r in revelations))
        consistency = days_with_revelations / 7.0

        return {
            "average_length": round(average_length, 1),
            "emotional_depth": round(emotional_depth, 2),
            "consistency": round(consistency, 2),
            "total_emotional_keywords": sum(1 for r in revelations for keyword in emotional_keywords if keyword in r.content.lower())
        }

    def _generate_timeline_insights(self, timeline_data: Dict, connection) -> List[str]:
        """Generate insights and recommendations based on timeline data"""
        insights = []
        stats = timeline_data["statistics"]
        quality = timeline_data["quality_metrics"]
        
        # Completion insights
        if stats["mutual_completion_percentage"] >= 80:
            insights.append("🌟 Excellent mutual engagement! You're both deeply invested in this connection.")
        elif stats["mutual_completion_percentage"] >= 60:
            insights.append("💫 Strong connection building! Keep sharing your authentic selves.")
        elif stats["mutual_completion_percentage"] >= 40:
            insights.append("🌱 Growing connection! Consider encouraging more mutual sharing.")
        else:
            insights.append("💭 Early stages! Take time to share more deeply with each other.")

        # Quality insights
        if quality["emotional_depth"] >= 0.7:
            insights.append("❤️ Your revelations show deep emotional openness and vulnerability.")
        elif quality["average_length"] >= 150:
            insights.append("📝 You're sharing detailed, thoughtful revelations - great depth!")

        # Consistency insights
        if quality["consistency"] >= 0.8:
            insights.append("⭐ Consistent sharing pattern shows strong commitment to connection.")
        elif quality["consistency"] < 0.5:
            insights.append("📅 Try to share more regularly to maintain connection momentum.")

        # Timing insights
        current_day = timeline_data["current_day"]
        if current_day == 7:
            insights.append("🎉 You've reached the photo reveal day! A beautiful milestone.")
        elif current_day >= 5:
            insights.append("✨ Almost at the finish line! The deepest revelations are happening.")
        elif current_day >= 3:
            insights.append("🚀 Halfway through the journey! Your connection is deepening.")

        return insights[:4]  # Return top 4 insights

    def advance_revelation_day(self, db: Session, connection_id: int) -> Dict[str, Any]:
        """Manually advance revelation day (for testing or admin use)"""
        connection = db.query(SoulConnection).filter(SoulConnection.id == connection_id).first()
        if not connection:
            return {"success": False, "error": "Connection not found"}

        if connection.reveal_day >= 7:
            return {"success": False, "error": "Revelation cycle already complete"}

        old_day = connection.reveal_day
        connection.reveal_day = min(connection.reveal_day + 1, 7)
        connection.updated_at = datetime.utcnow()

        # Update timeline
        self.update_connection_timeline(db, connection_id, f"day_{connection.reveal_day}_unlocked")

        db.commit()

        return {
            "success": True,
            "connection_id": connection_id,
            "previous_day": old_day,
            "current_day": connection.reveal_day,
            "message": f"Advanced from Day {old_day} to Day {connection.reveal_day}"
        }