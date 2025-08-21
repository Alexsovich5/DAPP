"""
Production UserSafetyService implementation with database integration.
Replaces the simplified mock version with real database operations.
"""

from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc

from app.models.user_safety import (
    UserReport, BlockedUser, UserSafetyProfile, ModerationAction,
    ReportCategory, ReportStatus, SafetyStatus
)
from app.models.user import User
from app.core.database import get_db


class UserSafetyService:
    """Production safety service with full database integration."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def report_user(self, reporter_id: int, reported_user_id: int, 
                   category: str, description: str, evidence_urls: Optional[str] = None) -> Dict[str, Any]:
        """Create a new user report with database persistence."""
        try:
            # Validate category
            report_category = ReportCategory(category)
        except ValueError:
            raise ValueError(f"Invalid report category: {category}")
        
        # Create report record
        report = UserReport(
            reporter_id=reporter_id,
            reported_user_id=reported_user_id,
            category=report_category,
            description=description,
            evidence_urls=evidence_urls,
            status=ReportStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        
        # Update safety profile
        self._update_user_safety_metrics(reported_user_id)
        
        # Auto-moderate if threshold reached
        self._check_auto_moderation(reported_user_id)
        
        return {
            "report_id": report.id,
            "status": report.status.value,
            "created_at": report.created_at.isoformat(),
            "message": "Report submitted successfully"
        }
    
    def block_user(self, blocker_id: int, blocked_user_id: int, reason: Optional[str] = None) -> Dict[str, Any]:
        """Block a user with database persistence."""
        # Check if already blocked
        existing_block = self.db.query(BlockedUser).filter(
            and_(
                BlockedUser.blocker_id == blocker_id,
                BlockedUser.blocked_user_id == blocked_user_id
            )
        ).first()
        
        if existing_block:
            return {
                "success": False,
                "message": "User is already blocked"
            }
        
        # Create block record
        block = BlockedUser(
            blocker_id=blocker_id,
            blocked_user_id=blocked_user_id,
            reason=reason,
            created_at=datetime.utcnow()
        )
        
        self.db.add(block)
        self.db.commit()
        
        return {
            "success": True,
            "message": "User blocked successfully",
            "blocked_at": block.created_at.isoformat()
        }
    
    def unblock_user(self, blocker_id: int, blocked_user_id: int) -> Dict[str, Any]:
        """Unblock a user by removing block record."""
        block = self.db.query(BlockedUser).filter(
            and_(
                BlockedUser.blocker_id == blocker_id,
                BlockedUser.blocked_user_id == blocked_user_id
            )
        ).first()
        
        if not block:
            return {
                "success": False,
                "message": "User is not blocked"
            }
        
        self.db.delete(block)
        self.db.commit()
        
        return {
            "success": True,
            "message": "User unblocked successfully"
        }
    
    def get_blocked_users(self, user_id: int) -> List[Dict[str, Any]]:
        """Get list of users blocked by the current user."""
        blocks = self.db.query(BlockedUser).filter(
            BlockedUser.blocker_id == user_id
        ).all()
        
        blocked_users = []
        for block in blocks:
            blocked_user = self.db.query(User).filter(User.id == block.blocked_user_id).first()
            if blocked_user:
                blocked_users.append({
                    "user_id": blocked_user.id,
                    "username": blocked_user.username,
                    "blocked_at": block.created_at.isoformat(),
                    "reason": block.reason
                })
        
        return blocked_users
    
    def is_user_blocked(self, blocker_id: int, blocked_user_id: int) -> bool:
        """Check if one user has blocked another."""
        block = self.db.query(BlockedUser).filter(
            and_(
                BlockedUser.blocker_id == blocker_id,
                BlockedUser.blocked_user_id == blocked_user_id
            )
        ).first()
        
        return block is not None
    
    def get_user_reports(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get reports made by a user."""
        reports = self.db.query(UserReport).filter(
            UserReport.reporter_id == user_id
        ).order_by(desc(UserReport.created_at)).limit(limit).all()
        
        report_list = []
        for report in reports:
            reported_user = self.db.query(User).filter(User.id == report.reported_user_id).first()
            report_list.append({
                "report_id": report.id,
                "reported_user": {
                    "id": reported_user.id if reported_user else None,
                    "username": reported_user.username if reported_user else "Unknown"
                },
                "category": report.category.value,
                "description": report.description,
                "status": report.status.value,
                "created_at": report.created_at.isoformat(),
                "resolved_at": report.resolved_at.isoformat() if report.resolved_at else None
            })
        
        return report_list
    
    def get_safety_metrics(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive safety metrics for a user."""
        safety_profile = self._get_or_create_safety_profile(user_id)
        
        # Get report counts
        reports_received = self.db.query(func.count(UserReport.id)).filter(
            UserReport.reported_user_id == user_id
        ).scalar()
        
        reports_made = self.db.query(func.count(UserReport.id)).filter(
            UserReport.reporter_id == user_id
        ).scalar()
        
        # Get recent moderation actions
        recent_actions = self.db.query(ModerationAction).filter(
            and_(
                ModerationAction.target_user_id == user_id,
                ModerationAction.created_at >= datetime.utcnow() - timedelta(days=30)
            )
        ).count()
        
        return {
            "user_id": user_id,
            "safety_status": safety_profile.safety_status.value,
            "safety_score": safety_profile.safety_score,
            "total_reports_received": reports_received,
            "total_reports_made": reports_made,
            "recent_moderation_actions": recent_actions,
            "restriction_active": bool(
                safety_profile.restriction_end and 
                safety_profile.restriction_end > datetime.utcnow()
            ),
            "last_updated": safety_profile.updated_at.isoformat() if safety_profile.updated_at else None
        }
    
    def moderate_user(self, moderator_id: int, target_user_id: int, 
                     action_type: str, reason: str, duration_hours: Optional[int] = None) -> Dict[str, Any]:
        """Apply moderation action to a user."""
        # Create moderation action record
        expires_at = None
        if duration_hours:
            expires_at = datetime.utcnow() + timedelta(hours=duration_hours)
        
        moderation_action = ModerationAction(
            target_user_id=target_user_id,
            moderator_id=moderator_id,
            action_type=action_type,
            reason=reason,
            duration_hours=duration_hours,
            expires_at=expires_at,
            created_at=datetime.utcnow(),
            is_active=True
        )
        
        self.db.add(moderation_action)
        
        # Update user safety profile
        safety_profile = self._get_or_create_safety_profile(target_user_id)
        
        if action_type in ["suspend", "restrict"]:
            safety_profile.safety_status = SafetyStatus.RESTRICTED
            safety_profile.restriction_reason = reason
            safety_profile.restriction_start = datetime.utcnow()
            safety_profile.restriction_end = expires_at
        elif action_type == "ban":
            safety_profile.safety_status = SafetyStatus.BANNED
            safety_profile.restriction_reason = reason
            safety_profile.restriction_start = datetime.utcnow()
        
        safety_profile.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return {
            "success": True,
            "action_id": moderation_action.id,
            "action_type": action_type,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "message": f"Moderation action '{action_type}' applied successfully"
        }
    
    def check_user_safety_status(self, user_id: int) -> Dict[str, Any]:
        """Check if user has any active restrictions."""
        safety_profile = self._get_or_create_safety_profile(user_id)
        
        # Check for active restrictions
        active_restriction = None
        if (safety_profile.restriction_end and 
            safety_profile.restriction_end > datetime.utcnow()):
            active_restriction = {
                "type": safety_profile.safety_status.value,
                "reason": safety_profile.restriction_reason,
                "expires_at": safety_profile.restriction_end.isoformat()
            }
        
        return {
            "user_id": user_id,
            "safety_status": safety_profile.safety_status.value,
            "is_restricted": safety_profile.safety_status in [SafetyStatus.RESTRICTED, SafetyStatus.BANNED],
            "active_restriction": active_restriction,
            "safety_score": safety_profile.safety_score
        }
    
    def _get_or_create_safety_profile(self, user_id: int) -> UserSafetyProfile:
        """Get or create safety profile for user."""
        safety_profile = self.db.query(UserSafetyProfile).filter(
            UserSafetyProfile.user_id == user_id
        ).first()
        
        if not safety_profile:
            safety_profile = UserSafetyProfile(
                user_id=user_id,
                safety_status=SafetyStatus.ACTIVE,
                safety_score=100,
                total_reports=0,
                created_at=datetime.utcnow()
            )
            self.db.add(safety_profile)
            self.db.commit()
            self.db.refresh(safety_profile)
        
        return safety_profile
    
    def _update_user_safety_metrics(self, user_id: int) -> None:
        """Update safety metrics after new report."""
        safety_profile = self._get_or_create_safety_profile(user_id)
        
        # Count total reports
        total_reports = self.db.query(func.count(UserReport.id)).filter(
            UserReport.reported_user_id == user_id
        ).scalar()
        
        safety_profile.total_reports = total_reports
        safety_profile.last_report_date = datetime.utcnow()
        
        # Decrease safety score based on reports
        if total_reports > 0:
            # Decrease by 10 points per report, minimum 0
            safety_profile.safety_score = max(0, 100 - (total_reports * 10))
        
        safety_profile.updated_at = datetime.utcnow()
        self.db.commit()
    
    def _check_auto_moderation(self, user_id: int) -> None:
        """Check if user should be auto-moderated based on reports."""
        safety_profile = self._get_or_create_safety_profile(user_id)
        
        # Auto-restrict if 3+ reports in 24 hours
        recent_reports = self.db.query(func.count(UserReport.id)).filter(
            and_(
                UserReport.reported_user_id == user_id,
                UserReport.created_at >= datetime.utcnow() - timedelta(hours=24)
            )
        ).scalar()
        
        if recent_reports >= 3 and safety_profile.safety_status == SafetyStatus.ACTIVE:
            # Auto-restrict for 24 hours
            safety_profile.safety_status = SafetyStatus.RESTRICTED
            safety_profile.restriction_reason = "Auto-moderation: Multiple reports received"
            safety_profile.restriction_start = datetime.utcnow()
            safety_profile.restriction_end = datetime.utcnow() + timedelta(hours=24)
            safety_profile.updated_at = datetime.utcnow()
            
            # Create moderation action record
            auto_action = ModerationAction(
                target_user_id=user_id,
                moderator_id=1,  # System moderator
                action_type="auto_restrict",
                reason="Auto-moderation: Multiple reports received within 24 hours",
                duration_hours=24,
                expires_at=safety_profile.restriction_end,
                created_at=datetime.utcnow(),
                is_active=True
            )
            
            self.db.add(auto_action)
            self.db.commit()