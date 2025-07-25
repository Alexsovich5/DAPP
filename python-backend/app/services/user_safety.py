# User Safety Service for Dating Platform
# Comprehensive user protection and reporting system

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging
from dataclasses import dataclass
import json
from pydantic import BaseModel

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

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class UserReport:
    reporter_id: int
    reported_user_id: int
    category: ReportCategory
    description: str
    evidence: Dict  # Screenshots, message IDs, etc.
    timestamp: datetime
    ip_address: str

@dataclass
class SafetyIncident:
    incident_id: str
    user_id: int
    incident_type: str
    severity: RiskLevel
    description: str
    metadata: Dict
    timestamp: datetime
    status: str

class UserSafetyService:
    """
    Comprehensive user safety and protection system
    """
    
    def __init__(self, database, redis_client, content_moderation_service):
        self.db = database
        self.redis = redis_client
        self.moderation_service = content_moderation_service
        self.safety_rules = self._load_safety_rules()
        
    def _load_safety_rules(self) -> Dict:
        """Load safety rules and thresholds"""
        return {
            "report_thresholds": {
                ReportCategory.HARASSMENT: 2,  # 2 reports trigger review
                ReportCategory.FAKE_PROFILE: 3,
                ReportCategory.INAPPROPRIATE_PHOTOS: 1,  # Single report triggers review
                ReportCategory.SPAM: 3,
                ReportCategory.SCAM: 1,
                ReportCategory.VIOLENCE_THREATS: 1,
                ReportCategory.HATE_SPEECH: 1,
                ReportCategory.UNDERAGE: 1,
                ReportCategory.IMPERSONATION: 2
            },
            
            "auto_action_thresholds": {
                "harassment_reports": 5,  # Auto-suspend after 5 harassment reports
                "fake_profile_score": 0.8,  # Auto-flag if fake profile score > 80%
                "spam_messages": 10,  # Auto-restrict after 10 spam messages
                "rapid_reports": 3  # Auto-review if 3+ reports in 24h
            },
            
            "cooling_off_periods": {
                ActionType.WARNING: timedelta(hours=24),
                ActionType.TEMPORARY_SUSPENSION: timedelta(days=7),
                ActionType.MESSAGE_RESTRICTION: timedelta(days=3),
                ActionType.PROFILE_RESTRICTION: timedelta(days=1)
            }
        }
    
    async def submit_report(self, report: UserReport) -> Dict:
        """
        Submit a user safety report
        """
        # Validate report
        validation_result = await self._validate_report(report)
        if not validation_result["is_valid"]:
            return {"success": False, "error": validation_result["error"]}
        
        # Generate report ID
        report_id = self._generate_report_id()
        
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
            "status": ReportStatus.PENDING.value
        }
        
        await self._store_report(report_data)
        
        # Immediate safety checks
        immediate_action = await self._check_immediate_action_required(report)
        if immediate_action["action_required"]:
            await self._take_immediate_action(report.reported_user_id, immediate_action)
        
        # Check if user has multiple reports
        await self._check_multiple_reports(report.reported_user_id)
        
        # Notify safety team if high-priority
        if report.category in [ReportCategory.VIOLENCE_THREATS, ReportCategory.UNDERAGE]:
            await self._notify_safety_team(report_data, priority="high")
        
        # Send confirmation to reporter
        await self._send_report_confirmation(report.reporter_id, report_id)
        
        return {
            "success": True,
            "report_id": report_id,
            "status": "submitted",
            "estimated_review_time": self._get_estimated_review_time(report.category)
        }
    
    async def _validate_report(self, report: UserReport) -> Dict:
        """Validate report data and check for abuse"""
        
        # Check if reporter exists and is not banned
        reporter_status = await self._get_user_status(report.reporter_id)
        if reporter_status["is_banned"]:
            return {"is_valid": False, "error": "Reporter is banned"}
        
        # Check if reported user exists
        reported_user_exists = await self._user_exists(report.reported_user_id)
        if not reported_user_exists:
            return {"is_valid": False, "error": "Reported user does not exist"}
        
        # Check for report spam (same user reporting multiple times)
        recent_reports = await self._get_recent_reports_by_reporter(
            report.reporter_id, hours=24
        )
        if len(recent_reports) > 5:
            return {"is_valid": False, "error": "Too many reports in 24 hours"}
        
        # Check if reporter is repeatedly reporting the same user
        same_user_reports = [r for r in recent_reports 
                           if r["reported_user_id"] == report.reported_user_id]
        if len(same_user_reports) > 2:
            return {"is_valid": False, "error": "Already reported this user recently"}
        
        # Validate evidence
        if not report.evidence or len(report.description) < 10:
            return {"is_valid": False, "error": "Insufficient description or evidence"}
        
        return {"is_valid": True}
    
    async def _check_immediate_action_required(self, report: UserReport) -> Dict:
        """Check if immediate action is required based on report"""
        action_required = False
        action_type = None
        reason = ""
        
        # Critical categories require immediate action
        if report.category in [ReportCategory.VIOLENCE_THREATS, ReportCategory.UNDERAGE]:
            action_required = True
            action_type = ActionType.TEMPORARY_SUSPENSION
            reason = f"Immediate suspension due to {report.category.value} report"
        
        # Check if user has pending critical reports
        pending_critical = await self._get_pending_critical_reports(report.reported_user_id)
        if len(pending_critical) > 0:
            action_required = True
            action_type = ActionType.PROFILE_REVIEW
            reason = "Multiple critical reports pending"
        
        # Check recent activity patterns
        suspicious_activity = await self._detect_suspicious_activity(report.reported_user_id)
        if suspicious_activity["is_suspicious"]:
            action_required = True
            action_type = ActionType.MESSAGE_RESTRICTION
            reason = f"Suspicious activity: {suspicious_activity['reason']}"
        
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
        action_id = await self._record_safety_action(user_id, action_type, reason)
        
        # Implement the action
        if action_type == ActionType.TEMPORARY_SUSPENSION:
            await self._suspend_user_temporarily(user_id, hours=24)
            
        elif action_type == ActionType.MESSAGE_RESTRICTION:
            await self._restrict_user_messaging(user_id, hours=24)
            
        elif action_type == ActionType.PROFILE_RESTRICTION:
            await self._restrict_profile_visibility(user_id, hours=24)
            
        elif action_type == ActionType.PROFILE_REVIEW:
            await self._flag_profile_for_review(user_id)
        
        # Notify user of action
        await self._notify_user_of_action(user_id, action_type, reason)
        
        # Log safety event
        await self._log_safety_event(SafetyIncident(
            incident_id=action_id,
            user_id=user_id,
            incident_type="immediate_action",
            severity=RiskLevel.HIGH,
            description=reason,
            metadata={"action_type": action_type.value},
            timestamp=datetime.utcnow(),
            status="active"
        ))
    
    async def _check_multiple_reports(self, user_id: int):
        """Check if user has multiple reports and take action if necessary"""
        
        # Get all reports for this user in the last 30 days
        recent_reports = await self._get_reports_for_user(user_id, days=30)
        
        # Group by category
        reports_by_category = {}
        for report in recent_reports:
            category = report["category"]
            if category not in reports_by_category:
                reports_by_category[category] = []
            reports_by_category[category].append(report)
        
        # Check thresholds
        actions_to_take = []
        
        for category, reports in reports_by_category.items():
            threshold = self.safety_rules["report_thresholds"].get(
                ReportCategory(category), 999
            )
            
            if len(reports) >= threshold:
                actions_to_take.append({
                    "category": category,
                    "report_count": len(reports),
                    "action": self._determine_action_for_category(category, len(reports))
                })
        
        # Take actions
        for action_info in actions_to_take:
            await self._take_threshold_action(user_id, action_info)
    
    async def process_safety_queue(self):
        """Process pending safety reports and incidents"""
        
        # Get pending reports
        pending_reports = await self._get_pending_reports()
        
        for report in pending_reports:
            try:
                # Analyze report
                analysis = await self._analyze_report(report)
                
                # Make decision
                decision = await self._make_safety_decision(report, analysis)
                
                # Take action if needed
                if decision["action_required"]:
                    await self._execute_safety_action(report, decision)
                
                # Update report status
                await self._update_report_status(report["id"], ReportStatus.RESOLVED)
                
            except Exception as e:
                logger.error(f"Error processing report {report['id']}: {str(e)}")
                await self._escalate_report(report["id"])
    
    async def _analyze_report(self, report: Dict) -> Dict:
        """Analyze a safety report using various signals"""
        
        reported_user_id = report["reported_user_id"]
        category = ReportCategory(report["category"])
        
        analysis = {
            "user_history": await self._get_user_safety_history(reported_user_id),
            "recent_activity": await self._get_recent_user_activity(reported_user_id),
            "content_analysis": None,
            "pattern_analysis": await self._analyze_behavior_patterns(reported_user_id),
            "credibility_score": await self._calculate_reporter_credibility(report["reporter_id"])
        }
        
        # Content-specific analysis
        if "message_ids" in report["evidence"]:
            message_ids = report["evidence"]["message_ids"]
            analysis["content_analysis"] = await self._analyze_reported_messages(message_ids)
        
        if "photo_urls" in report["evidence"]:
            photo_urls = report["evidence"]["photo_urls"]
            analysis["photo_analysis"] = await self._analyze_reported_photos(photo_urls)
        
        return analysis
    
    async def _make_safety_decision(self, report: Dict, analysis: Dict) -> Dict:
        """Make decision on safety report based on analysis"""
        
        category = ReportCategory(report["category"])
        decision = {
            "action_required": False,
            "action_type": ActionType.NO_ACTION,
            "confidence": 0.0,
            "reasoning": []
        }
        
        # High-confidence automated decisions
        if analysis["credibility_score"] > 0.8:
            
            if category == ReportCategory.HARASSMENT:
                if analysis["content_analysis"] and analysis["content_analysis"]["harassment_score"] > 0.7:
                    decision.update({
                        "action_required": True,
                        "action_type": ActionType.WARNING,
                        "confidence": 0.8,
                        "reasoning": ["High harassment score in content analysis"]
                    })
            
            elif category == ReportCategory.SPAM:
                if analysis["pattern_analysis"]["spam_indicators"] > 3:
                    decision.update({
                        "action_required": True,
                        "action_type": ActionType.MESSAGE_RESTRICTION,
                        "confidence": 0.9,
                        "reasoning": ["Multiple spam indicators detected"]
                    })
            
            elif category == ReportCategory.FAKE_PROFILE:
                fake_score = analysis["pattern_analysis"].get("fake_profile_score", 0)
                if fake_score > 0.7:
                    decision.update({
                        "action_required": True,
                        "action_type": ActionType.PROFILE_REVIEW,
                        "confidence": fake_score,
                        "reasoning": ["High fake profile probability"]
                    })
        
        # Check user history
        if analysis["user_history"]["violation_count"] > 5:
            if decision["action_type"] == ActionType.WARNING:
                decision["action_type"] = ActionType.TEMPORARY_SUSPENSION
                decision["reasoning"].append("User has extensive violation history")
        
        return decision
    
    async def create_safety_alert(self, user_id: int, alert_type: str, 
                                description: str, metadata: Dict = None) -> str:
        """Create a safety alert for monitoring"""
        
        alert_id = self._generate_alert_id()
        alert_data = {
            "id": alert_id,
            "user_id": user_id,
            "alert_type": alert_type,
            "description": description,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
            "status": "active",
            "severity": self._determine_alert_severity(alert_type)
        }
        
        # Store alert
        await self._store_safety_alert(alert_data)
        
        # Check if immediate notification needed
        if alert_data["severity"] in ["high", "critical"]:
            await self._notify_safety_team(alert_data, priority=alert_data["severity"])
        
        return alert_id
    
    async def get_user_safety_status(self, user_id: int) -> Dict:
        """Get comprehensive safety status for a user"""
        
        # Get current restrictions
        restrictions = await self._get_active_restrictions(user_id)
        
        # Get safety score
        safety_score = await self._calculate_user_safety_score(user_id)
        
        # Get recent reports
        recent_reports = await self._get_reports_for_user(user_id, days=30)
        
        # Get trust level
        trust_level = await self._get_user_trust_level(user_id)
        
        return {
            "user_id": user_id,
            "safety_score": safety_score,
            "trust_level": trust_level,
            "active_restrictions": restrictions,
            "recent_reports_count": len(recent_reports),
            "last_violation": await self._get_last_violation_date(user_id),
            "risk_level": self._assess_user_risk_level(safety_score, len(recent_reports)),
            "recommendations": await self._generate_safety_recommendations(user_id)
        }
    
    # Helper methods
    async def _get_user_status(self, user_id: int) -> Dict:
        """Get user account status"""
        # Implementation would query database
        return {"is_banned": False, "is_suspended": False}
    
    async def _user_exists(self, user_id: int) -> bool:
        """Check if user exists"""
        # Implementation would query database
        return True
    
    def _generate_report_id(self) -> str:
        """Generate unique report ID"""
        import uuid
        return f"RPT_{uuid.uuid4().hex[:8].upper()}"
    
    def _generate_alert_id(self) -> str:
        """Generate unique alert ID"""
        import uuid
        return f"ALT_{uuid.uuid4().hex[:8].upper()}"
    
    async def _store_report(self, report_data: Dict):
        """Store report in database"""
        # Implementation would store in database
        await self.redis.lpush("safety_reports", json.dumps(report_data))
    
    async def _store_safety_alert(self, alert_data: Dict):
        """Store safety alert"""
        await self.redis.lpush("safety_alerts", json.dumps(alert_data))
    
    def _get_estimated_review_time(self, category: ReportCategory) -> str:
        """Get estimated review time for report category"""
        times = {
            ReportCategory.VIOLENCE_THREATS: "1-2 hours",
            ReportCategory.UNDERAGE: "1-2 hours",
            ReportCategory.HARASSMENT: "24-48 hours",
            ReportCategory.FAKE_PROFILE: "48-72 hours",
            ReportCategory.SPAM: "24-48 hours",
            ReportCategory.INAPPROPRIATE_PHOTOS: "12-24 hours"
        }
        return times.get(category, "48-72 hours")
    
    def _determine_alert_severity(self, alert_type: str) -> str:
        """Determine severity level for alert type"""
        high_severity = ["violence", "threats", "underage", "self_harm"]
        medium_severity = ["harassment", "fake_profile", "scam"]
        
        if alert_type in high_severity:
            return "critical"
        elif alert_type in medium_severity:
            return "high"
        else:
            return "medium"
    
    async def _notify_safety_team(self, data: Dict, priority: str):
        """Notify safety team of high-priority issues"""
        # Implementation would send notifications to safety team
        logger.critical(f"Safety alert ({priority}): {data}")
    
    async def _send_report_confirmation(self, reporter_id: int, report_id: str):
        """Send confirmation to user who submitted report"""
        # Implementation would send notification/email
        pass

# Configuration for automated safety actions
SAFETY_CONFIG = {
    "auto_suspend_thresholds": {
        "harassment_reports": 3,
        "violence_reports": 1,
        "fake_profile_score": 0.9
    },
    
    "escalation_triggers": {
        "multiple_categories": 3,  # Reports in 3+ categories
        "rapid_reports": 5,  # 5+ reports in 24 hours
        "high_severity_single": True  # Any violence/underage report
    },
    
    "cooling_off_periods": {
        "first_warning": timedelta(hours=24),
        "second_warning": timedelta(days=3),
        "temporary_suspension": timedelta(days=7),
        "extended_suspension": timedelta(days=30)
    }
}