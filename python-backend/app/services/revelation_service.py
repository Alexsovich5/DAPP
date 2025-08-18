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
    
    def __init__(self):
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