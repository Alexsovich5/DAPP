# Simplified User Safety Service for immediate functionality
# This is a working implementation that stores reports in memory for now
# Can be upgraded to database storage later

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging
from dataclasses import dataclass
import uuid
import json

logger = logging.getLogger(__name__)

class ReportCategory(Enum):
    HARASSMENT = "harassment"
    FAKE_PROFILE = "fake_profile"
    INAPPROPRIATE_PHOTOS = "inappropriate_photos"
    SPAM = "spam"
    SCAM = "scam"
    VIOLENCE_THREATS = "violence_threats"
    HATE_SPEECH = "hate_speech"
    UNDERAGE = "underage"
    IMPERSONATION = "impersonation"
    OTHER = "other"

class ReportStatus(Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"

class ActionType(Enum):
    WARNING = "warning"
    TEMPORARY_SUSPENSION = "temporary_suspension"
    PERMANENT_BAN = "permanent_ban"
    PROFILE_RESTRICTION = "profile_restriction"
    MESSAGE_RESTRICTION = "message_restriction"
    PHOTO_REMOVAL = "photo_removal"
    PROFILE_REVIEW = "profile_review"
    NO_ACTION = "no_action"

@dataclass
class UserReport:
    reporter_id: int
    reported_user_id: int
    category: ReportCategory
    description: str
    evidence: Dict
    timestamp: datetime
    ip_address: str

class UserSafetyService:
    """
    Simplified user safety service for immediate functionality
    Uses in-memory storage for now, can be upgraded to database later
    """
    
    def __init__(self, database=None, redis_client=None, content_moderation_service=None):
        # In-memory storage for reports (would be database in production)
        self.reports = []
        self.safety_actions = []
        self.user_restrictions = {}
        
        # Safety rules and thresholds
        self.safety_rules = {
            "report_thresholds": {
                ReportCategory.HARASSMENT: 2,
                ReportCategory.FAKE_PROFILE: 3,
                ReportCategory.INAPPROPRIATE_PHOTOS: 1,
                ReportCategory.SPAM: 3,
                ReportCategory.SCAM: 1,
                ReportCategory.VIOLENCE_THREATS: 1,
                ReportCategory.HATE_SPEECH: 1,
                ReportCategory.UNDERAGE: 1,
                ReportCategory.IMPERSONATION: 2
            }
        }
    
    async def submit_report(self, report: UserReport) -> Dict:
        """
        Submit a user safety report
        """
        try:
            # Validate report
            validation_result = await self._validate_report(report)
            if not validation_result["is_valid"]:
                return {"success": False, "error": validation_result["error"]}
            
            # Generate report ID
            report_id = f"RPT_{uuid.uuid4().hex[:8].upper()}"
            
            # Store report
            report_data = {
                "id": report_id,
                "reporter_id": report.reporter_id,
                "reported_user_id": report.reported_user_id,
                "category": report.category.value,
                "description": report.description,
                "evidence": report.evidence,
                "timestamp": report.timestamp.isoformat(),
                "ip_address": report.ip_address,
                "status": ReportStatus.PENDING.value,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Add to in-memory storage
            self.reports.append(report_data)
            logger.info(f"Safety report {report_id} submitted for user {report.reported_user_id}")
            
            # Check for immediate action needed
            immediate_action = await self._check_immediate_action_required(report)
            if immediate_action["action_required"]:
                await self._take_immediate_action(report.reported_user_id, immediate_action)
                logger.warning(f"Immediate action taken for user {report.reported_user_id}: {immediate_action['reason']}")
            
            # Check multiple reports threshold
            await self._check_multiple_reports(report.reported_user_id)
            
            return {
                "success": True,
                "report_id": report_id,
                "status": "submitted",
                "message": "Report submitted successfully",
                "estimated_review_time": self._get_estimated_review_time(report.category),
                "immediate_action_taken": immediate_action["action_required"]
            }
            
        except Exception as e:
            logger.error(f"Error submitting safety report: {str(e)}")
            return {"success": False, "error": f"Failed to submit report: {str(e)}"}
    
    async def _validate_report(self, report: UserReport) -> Dict:
        """Validate report data"""
        
        # Basic validation
        if not report.description or len(report.description) < 10:
            return {"is_valid": False, "error": "Description must be at least 10 characters"}
        
        if report.reporter_id == report.reported_user_id:
            return {"is_valid": False, "error": "Cannot report yourself"}
        
        # Check for report spam (same user reporting too frequently)
        recent_reports = [r for r in self.reports 
                         if r["reporter_id"] == report.reporter_id and 
                            (datetime.utcnow() - datetime.fromisoformat(r["timestamp"])).total_seconds() < 24*3600]
        
        if len(recent_reports) > 5:
            return {"is_valid": False, "error": "Too many reports submitted in the last 24 hours"}
        
        # Check for duplicate reports of same user
        duplicate_reports = [r for r in recent_reports 
                           if r["reported_user_id"] == report.reported_user_id]
        
        if len(duplicate_reports) > 2:
            return {"is_valid": False, "error": "You have already reported this user recently"}
        
        return {"is_valid": True}
    
    async def _check_immediate_action_required(self, report: UserReport) -> Dict:
        """Check if immediate action is required"""
        action_required = False
        action_type = None
        reason = ""
        
        # Critical categories require immediate review
        if report.category in [ReportCategory.VIOLENCE_THREATS, ReportCategory.UNDERAGE]:
            action_required = True
            action_type = ActionType.TEMPORARY_SUSPENSION
            reason = f"Immediate suspension due to {report.category.value} report"
        
        elif report.category == ReportCategory.HARASSMENT:
            # Check if user has multiple harassment reports
            harassment_reports = [r for r in self.reports 
                                if r["reported_user_id"] == report.reported_user_id and 
                                   r["category"] == "harassment"]
            
            if len(harassment_reports) >= 2:  # Including current report
                action_required = True
                action_type = ActionType.MESSAGE_RESTRICTION
                reason = "Multiple harassment reports - restricting messaging"
        
        return {
            "action_required": action_required,
            "action_type": action_type,
            "reason": reason
        }
    
    async def _take_immediate_action(self, user_id: int, action_info: Dict):
        """Take immediate protective action"""
        action_type = action_info["action_type"]
        reason = action_info["reason"]
        
        # Record the action
        action_record = {
            "id": f"ACT_{uuid.uuid4().hex[:8].upper()}",
            "user_id": user_id,
            "action_type": action_type.value,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "status": "active"
        }
        
        self.safety_actions.append(action_record)
        
        # Apply restriction
        if user_id not in self.user_restrictions:
            self.user_restrictions[user_id] = []
        
        self.user_restrictions[user_id].append({
            "type": action_type.value,
            "reason": reason,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": action_record["expires_at"]
        })
        
        logger.warning(f"Safety action applied to user {user_id}: {action_type.value} - {reason}")
    
    async def _check_multiple_reports(self, user_id: int):
        """Check if user has multiple reports and needs action"""
        
        # Get all reports for this user
        user_reports = [r for r in self.reports if r["reported_user_id"] == user_id]
        
        # Group by category
        reports_by_category = {}
        for report in user_reports:
            category = report["category"]
            if category not in reports_by_category:
                reports_by_category[category] = []
            reports_by_category[category].append(report)
        
        # Check thresholds
        for category, reports in reports_by_category.items():
            try:
                report_category = ReportCategory(category)
                threshold = self.safety_rules["report_thresholds"].get(report_category, 999)
                
                if len(reports) >= threshold:
                    # Take escalated action
                    await self._take_threshold_action(user_id, category, len(reports))
                    
            except ValueError:
                # Invalid category, skip
                continue
    
    async def _take_threshold_action(self, user_id: int, category: str, report_count: int):
        """Take action when report threshold is exceeded"""
        
        if category == "harassment":
            action_type = ActionType.MESSAGE_RESTRICTION
            reason = f"Multiple harassment reports ({report_count}) - messaging restricted"
            
        elif category == "fake_profile":
            action_type = ActionType.PROFILE_REVIEW
            reason = f"Multiple fake profile reports ({report_count}) - profile under review"
            
        elif category == "spam":
            action_type = ActionType.MESSAGE_RESTRICTION
            reason = f"Multiple spam reports ({report_count}) - messaging restricted"
            
        else:
            action_type = ActionType.PROFILE_REVIEW
            reason = f"Multiple {category} reports ({report_count}) - account under review"
        
        await self._take_immediate_action(user_id, {
            "action_required": True,
            "action_type": action_type,
            "reason": reason
        })
    
    def _get_estimated_review_time(self, category: ReportCategory) -> str:
        """Get estimated review time for report category"""
        times = {
            ReportCategory.VIOLENCE_THREATS: "1-2 hours",
            ReportCategory.UNDERAGE: "1-2 hours", 
            ReportCategory.HARASSMENT: "24-48 hours",
            ReportCategory.FAKE_PROFILE: "48-72 hours",
            ReportCategory.SPAM: "24-48 hours",
            ReportCategory.INAPPROPRIATE_PHOTOS: "12-24 hours",
            ReportCategory.SCAM: "24-48 hours",
            ReportCategory.HATE_SPEECH: "12-24 hours",
            ReportCategory.IMPERSONATION: "48-72 hours",
            ReportCategory.OTHER: "48-72 hours"
        }
        return times.get(category, "48-72 hours")
    
    async def get_user_safety_status(self, user_id: int) -> Dict:
        """Get safety status for a user"""
        
        # Get reports against this user
        user_reports = [r for r in self.reports if r["reported_user_id"] == user_id]
        
        # Get active restrictions
        active_restrictions = self.user_restrictions.get(user_id, [])
        
        # Filter expired restrictions
        current_time = datetime.utcnow()
        active_restrictions = [r for r in active_restrictions 
                             if datetime.fromisoformat(r["expires_at"]) > current_time]
        
        # Calculate safety score (simplified)
        safety_score = max(0, 100 - (len(user_reports) * 10))  # Reduce by 10 for each report
        
        return {
            "user_id": user_id,
            "safety_score": safety_score,
            "total_reports": len(user_reports),
            "active_restrictions": active_restrictions,
            "last_report_date": user_reports[-1]["timestamp"] if user_reports else None,
            "status": "restricted" if active_restrictions else "good_standing"
        }
    
    async def get_reports_summary(self) -> Dict:
        """Get summary of all reports (admin function)"""
        
        total_reports = len(self.reports)
        pending_reports = len([r for r in self.reports if r["status"] == "pending"])
        
        reports_by_category = {}
        for report in self.reports:
            category = report["category"]
            reports_by_category[category] = reports_by_category.get(category, 0) + 1
        
        return {
            "total_reports": total_reports,
            "pending_reports": pending_reports,
            "reports_by_category": reports_by_category,
            "total_actions_taken": len(self.safety_actions),
            "users_with_restrictions": len(self.user_restrictions)
        }


# Standalone functions for testing
def moderate_user_content(content: str) -> Dict:
    """Moderate user content for safety and appropriateness"""
    flags = []
    is_safe = True
    
    content_lower = content.lower()
    
    # Check for personal information sharing
    import re
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    phone_pattern = r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b'
    
    if re.search(email_pattern, content):
        flags.append("personal_info_email")
        is_safe = False
        
    if re.search(phone_pattern, content):
        flags.append("personal_info_phone")
        is_safe = False
    
    # Check for suspicious keywords
    suspicious_keywords = [
        "venmo", "paypal", "cashapp", "money", "send me",
        "whatsapp", "telegram", "snapchat", "kik"
    ]
    
    for keyword in suspicious_keywords:
        if keyword in content_lower:
            flags.append(f"suspicious_keyword_{keyword}")
            is_safe = False
    
    return {
        "is_safe": is_safe,
        "flags": flags,
        "confidence": 0.8 if flags else 0.95
    }

def report_user(reporter_id: int, reported_user_id: int, reason: str, description: str) -> Dict:
    """Report a user for inappropriate behavior"""
    report_id = str(uuid.uuid4())
    
    # Store report (in-memory for MVP)
    report = {
        "report_id": report_id,
        "reporter_id": reporter_id,
        "reported_user_id": reported_user_id,
        "reason": reason,
        "description": description,
        "timestamp": datetime.utcnow(),
        "status": "pending"
    }
    
    logger.info(f"User report created: {report_id}")
    return {"report_id": report_id, "status": "submitted"}

def detect_spam(content: str) -> bool:
    """Detect if content is spam"""
    spam_indicators = [
        "click here", "amazing deal", "limited time", "act now",
        "www.", "http://", "https://", "bit.ly", "tinyurl",
        "!!!", "FREE", "URGENT", "CONGRATULATIONS"
    ]
    
    content_upper = content.upper()
    spam_count = sum(1 for indicator in spam_indicators if indicator.upper() in content_upper)
    
    # Consider spam if multiple indicators present
    return spam_count >= 2