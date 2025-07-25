# Enhanced Security Framework for Dating Platform
# Implements comprehensive security measures for user safety and data protection

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
import hmac
import secrets
import re
from enum import Enum
from dataclasses import dataclass
from cryptography.fernet import Fernet
from fastapi import HTTPException, Request
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ThreatType(Enum):
    SPAM = "spam"
    HARASSMENT = "harassment"
    FAKE_PROFILE = "fake_profile"
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    SUSPICIOUS_BEHAVIOR = "suspicious_behavior"
    DATA_SCRAPING = "data_scraping"

@dataclass
class SecurityEvent:
    user_id: Optional[int]
    event_type: ThreatType
    severity: SecurityLevel
    description: str
    ip_address: str
    timestamp: datetime
    metadata: Dict

class DatingPlatformSecurity:
    """
    Comprehensive security system designed specifically for dating platforms
    """
    
    def __init__(self, redis_client: redis.Redis, encryption_key: str):
        self.redis = redis_client
        self.cipher_suite = Fernet(encryption_key.encode())
        self.threat_patterns = self._load_threat_patterns()
        self.blocked_ips = set()
        self.suspicious_users = set()
        
    def _load_threat_patterns(self) -> Dict:
        """Load patterns for threat detection"""
        return {
            "spam_keywords": [
                "click here", "free money", "make money fast", "viagra",
                "webcam", "adult content", "sex chat", "escort"
            ],
            "harassment_patterns": [
                r"you\s+are\s+(ugly|fat|stupid)",
                r"kill\s+yourself",
                r"(fuck|shit|damn)\s+you",
                r"(bitch|slut|whore)"
            ],
            "suspicious_domains": [
                "tempmail.org", "10minutemail.com", "guerrillamail.com"
            ],
            "fake_profile_indicators": [
                "instagram model", "social media influencer",
                "just ask", "travel the world", "entrepreneur"
            ]
        }
    
    # === AUTHENTICATION SECURITY ===
    
    async def enhance_password_security(self, password: str) -> Dict:
        """Enhanced password validation for dating platforms"""
        security_score = 0
        issues = []
        
        # Length check
        if len(password) < 8:
            issues.append("Password must be at least 8 characters")
        else:
            security_score += 1
            
        # Complexity checks
        if not re.search(r"[a-z]", password):
            issues.append("Password must contain lowercase letters")
        else:
            security_score += 1
            
        if not re.search(r"[A-Z]", password):
            issues.append("Password must contain uppercase letters")
        else:
            security_score += 1
            
        if not re.search(r"\d", password):
            issues.append("Password must contain numbers")
        else:
            security_score += 1
            
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            issues.append("Password must contain special characters")
        else:
            security_score += 1
        
        # Common password check
        if password.lower() in self._get_common_passwords():
            issues.append("Password is too common")
            security_score -= 2
        
        # Dating-specific checks
        dating_words = ["love", "sexy", "date", "romance", "heart"]
        if any(word in password.lower() for word in dating_words):
            issues.append("Avoid dating-related words in passwords")
            security_score -= 1
        
        strength = "weak"
        if security_score >= 4:
            strength = "strong"
        elif security_score >= 2:
            strength = "medium"
            
        return {
            "strength": strength,
            "score": max(0, security_score),
            "issues": issues,
            "is_secure": len(issues) == 0 and security_score >= 4
        }
    
    async def detect_account_takeover(self, user_id: int, request: Request) -> bool:
        """Detect potential account takeover attempts"""
        cache_key = f"login_pattern:{user_id}"
        
        # Get recent login data
        recent_logins = await self._get_recent_logins(user_id)
        
        # Check for suspicious patterns
        suspicions = []
        
        # Geographic location changes
        if self._detect_location_jump(recent_logins):
            suspicions.append("rapid_location_change")
        
        # Device fingerprint changes
        if self._detect_device_change(recent_logins, request):
            suspicions.append("device_change")
        
        # Login frequency anomalies
        if self._detect_login_frequency_anomaly(recent_logins):
            suspicions.append("unusual_frequency")
        
        # Behavioral changes
        if await self._detect_behavioral_changes(user_id):
            suspicions.append("behavioral_change")
        
        if suspicions:
            await self._log_security_event(SecurityEvent(
                user_id=user_id,
                event_type=ThreatType.SUSPICIOUS_BEHAVIOR,
                severity=SecurityLevel.HIGH,
                description=f"Account takeover indicators: {', '.join(suspicions)}",
                ip_address=request.client.host,
                timestamp=datetime.utcnow(),
                metadata={"suspicions": suspicions}
            ))
            return True
            
        return False
    
    # === CONTENT SECURITY ===
    
    async def validate_profile_content(self, content: Dict) -> Dict:
        """Comprehensive profile content validation"""
        validation_result = {
            "is_valid": True,
            "issues": [],
            "risk_score": 0,
            "suggested_actions": []
        }
        
        # Check bio for inappropriate content
        if "bio" in content:
            bio_check = await self._check_text_content(content["bio"])
            if not bio_check["is_clean"]:
                validation_result["issues"].extend(bio_check["issues"])
                validation_result["risk_score"] += bio_check["risk_score"]
        
        # Check for fake profile indicators
        fake_indicators = self._detect_fake_profile_indicators(content)
        if fake_indicators:
            validation_result["issues"].append("Potential fake profile indicators detected")
            validation_result["risk_score"] += len(fake_indicators) * 10
            validation_result["suggested_actions"].append("manual_review")
        
        # Age verification
        if "age" in content:
            age_check = self._verify_age_consistency(content)
            if not age_check["is_consistent"]:
                validation_result["issues"].append("Age information inconsistent")
                validation_result["risk_score"] += 15
        
        # Photo analysis (if enabled)
        if "photos" in content:
            for photo in content["photos"]:
                photo_check = await self._analyze_photo_safety(photo)
                if not photo_check["is_safe"]:
                    validation_result["issues"].extend(photo_check["issues"])
                    validation_result["risk_score"] += photo_check["risk_score"]
        
        # Overall assessment
        if validation_result["risk_score"] > 50:
            validation_result["is_valid"] = False
            validation_result["suggested_actions"].append("block_profile")
        elif validation_result["risk_score"] > 25:
            validation_result["suggested_actions"].append("manual_review")
        
        return validation_result
    
    async def moderate_message_content(self, message: str, sender_id: int, recipient_id: int) -> Dict:
        """Real-time message content moderation"""
        moderation_result = {
            "approved": True,
            "filtered_message": message,
            "flags": [],
            "risk_score": 0,
            "action_required": None
        }
        
        # Spam detection
        spam_score = self._calculate_spam_score(message)
        if spam_score > 0.7:
            moderation_result["flags"].append("spam")
            moderation_result["risk_score"] += 30
        
        # Harassment detection
        harassment_score = self._detect_harassment(message)
        if harassment_score > 0.6:
            moderation_result["flags"].append("harassment")
            moderation_result["risk_score"] += 40
        
        # Sexual content detection
        sexual_content_score = self._detect_sexual_content(message)
        if sexual_content_score > 0.8:
            moderation_result["flags"].append("sexual_content")
            moderation_result["risk_score"] += 25
        
        # Personal information exposure
        if self._contains_personal_info(message):
            moderation_result["flags"].append("personal_info")
            moderation_result["filtered_message"] = self._filter_personal_info(message)
            moderation_result["risk_score"] += 15
        
        # Scam detection
        if self._detect_scam_patterns(message):
            moderation_result["flags"].append("potential_scam")
            moderation_result["risk_score"] += 35
        
        # Check sender's history
        sender_history = await self._get_user_moderation_history(sender_id)
        if sender_history["violations"] > 3:
            moderation_result["risk_score"] += 20
        
        # Final decision
        if moderation_result["risk_score"] > 40:
            moderation_result["approved"] = False
            moderation_result["action_required"] = "block_message"
        elif moderation_result["risk_score"] > 25:
            moderation_result["action_required"] = "manual_review"
        
        # Log moderation event
        if moderation_result["flags"]:
            await self._log_moderation_event(sender_id, recipient_id, message, moderation_result)
        
        return moderation_result
    
    # === BEHAVIORAL ANALYSIS ===
    
    async def analyze_user_behavior(self, user_id: int, action: str, metadata: Dict) -> Dict:
        """Comprehensive behavioral analysis for threat detection"""
        behavior_key = f"behavior:{user_id}"
        
        # Store action in behavior history
        await self._store_user_action(user_id, action, metadata)
        
        # Get recent behavior pattern
        recent_actions = await self._get_recent_actions(user_id, hours=24)
        
        analysis = {
            "risk_level": SecurityLevel.LOW,
            "alerts": [],
            "recommended_actions": [],
            "behavioral_score": 0
        }
        
        # Rapid-fire messaging detection
        if action == "send_message":
            message_frequency = self._calculate_message_frequency(recent_actions)
            if message_frequency > 10:  # More than 10 messages per hour
                analysis["alerts"].append("high_message_frequency")
                analysis["behavioral_score"] += 20
        
        # Profile view farming
        if action == "view_profile":
            profile_views = len([a for a in recent_actions if a["action"] == "view_profile"])
            if profile_views > 50:  # More than 50 profile views in 24h
                analysis["alerts"].append("excessive_profile_viewing")
                analysis["behavioral_score"] += 25
        
        # Connection request spam
        if action == "send_connection_request":
            requests = len([a for a in recent_actions if a["action"] == "send_connection_request"])
            if requests > 20:  # More than 20 requests in 24h
                analysis["alerts"].append("connection_spam")
                analysis["behavioral_score"] += 30
        
        # Location inconsistencies
        if "location" in metadata:
            if self._detect_location_spoofing(user_id, metadata["location"]):
                analysis["alerts"].append("location_spoofing")
                analysis["behavioral_score"] += 35
        
        # Bot-like behavior patterns
        if self._detect_bot_behavior(recent_actions):
            analysis["alerts"].append("bot_like_behavior")
            analysis["behavioral_score"] += 40
        
        # Determine risk level and actions
        if analysis["behavioral_score"] > 60:
            analysis["risk_level"] = SecurityLevel.CRITICAL
            analysis["recommended_actions"] = ["suspend_account", "manual_review"]
        elif analysis["behavioral_score"] > 40:
            analysis["risk_level"] = SecurityLevel.HIGH
            analysis["recommended_actions"] = ["limit_actions", "increase_monitoring"]
        elif analysis["behavioral_score"] > 20:
            analysis["risk_level"] = SecurityLevel.MEDIUM
            analysis["recommended_actions"] = ["monitor_closely"]
        
        return analysis
    
    # === DATA PROTECTION ===
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive personal data"""
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive personal data"""
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
    
    def anonymize_location(self, latitude: float, longitude: float) -> Tuple[float, float]:
        """Anonymize location data while maintaining matching capability"""
        # Reduce precision for privacy while keeping city-level accuracy
        anonymized_lat = round(latitude, 2)  # ~1km precision
        anonymized_lon = round(longitude, 2)
        return (anonymized_lat, anonymized_lon)
    
    def generate_profile_hash(self, profile_data: Dict) -> str:
        """Generate hash for profile integrity verification"""
        profile_string = f"{profile_data.get('name', '')}{profile_data.get('bio', '')}{profile_data.get('age', '')}"
        return hashlib.sha256(profile_string.encode()).hexdigest()
    
    # === RATE LIMITING ===
    
    def get_rate_limiter(self, action_type: str, user_id: int = None):
        """Get appropriate rate limiter for different actions"""
        rate_limits = {
            "login": RateLimiter(times=5, seconds=300),  # 5 attempts per 5 minutes
            "register": RateLimiter(times=3, seconds=3600),  # 3 attempts per hour
            "send_message": RateLimiter(times=30, seconds=3600),  # 30 messages per hour
            "connection_request": RateLimiter(times=10, seconds=3600),  # 10 requests per hour
            "profile_view": RateLimiter(times=100, seconds=3600),  # 100 views per hour
            "photo_upload": RateLimiter(times=5, seconds=1800),  # 5 uploads per 30 minutes
            "report_user": RateLimiter(times=5, seconds=86400),  # 5 reports per day
        }
        
        return rate_limits.get(action_type, RateLimiter(times=60, seconds=3600))
    
    # === HELPER METHODS ===
    
    def _get_common_passwords(self) -> List[str]:
        """Get list of common passwords to avoid"""
        return [
            "password", "123456", "123456789", "qwerty", "abc123",
            "password123", "admin", "letmein", "welcome", "monkey",
            "iloveyou", "princess", "sunshine", "password1"
        ]
    
    async def _check_text_content(self, text: str) -> Dict:
        """Check text content for inappropriate material"""
        issues = []
        risk_score = 0
        
        # Check for spam keywords
        for keyword in self.threat_patterns["spam_keywords"]:
            if keyword.lower() in text.lower():
                issues.append(f"Contains spam keyword: {keyword}")
                risk_score += 10
        
        # Check for harassment patterns
        for pattern in self.threat_patterns["harassment_patterns"]:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append("Contains harassment language")
                risk_score += 25
                break
        
        return {
            "is_clean": len(issues) == 0,
            "issues": issues,
            "risk_score": risk_score
        }
    
    def _detect_fake_profile_indicators(self, content: Dict) -> List[str]:
        """Detect indicators of fake profiles"""
        indicators = []
        
        if "bio" in content:
            bio = content["bio"].lower()
            for indicator in self.threat_patterns["fake_profile_indicators"]:
                if indicator in bio:
                    indicators.append(f"Fake profile phrase: {indicator}")
        
        # Check for stock photo indicators (would require image analysis)
        # Check for inconsistent information
        # Check for suspicious email domains
        
        return indicators
    
    async def _analyze_photo_safety(self, photo_data: bytes) -> Dict:
        """Analyze photo for safety and appropriateness"""
        # This would integrate with image analysis services
        # For now, return a safe result
        return {
            "is_safe": True,
            "issues": [],
            "risk_score": 0
        }
    
    def _calculate_spam_score(self, message: str) -> float:
        """Calculate spam probability for a message"""
        spam_indicators = 0
        total_indicators = len(self.threat_patterns["spam_keywords"])
        
        for keyword in self.threat_patterns["spam_keywords"]:
            if keyword.lower() in message.lower():
                spam_indicators += 1
        
        # Additional spam indicators
        if len(message.split()) < 3:  # Very short messages
            spam_indicators += 1
            total_indicators += 1
        
        if message.count('!') > 3:  # Excessive exclamation marks
            spam_indicators += 1
            total_indicators += 1
        
        if re.search(r'http[s]?://', message):  # Contains URLs
            spam_indicators += 2
            total_indicators += 2
        
        return spam_indicators / total_indicators if total_indicators > 0 else 0
    
    def _detect_harassment(self, message: str) -> float:
        """Detect harassment in messages"""
        harassment_score = 0
        
        for pattern in self.threat_patterns["harassment_patterns"]:
            if re.search(pattern, message, re.IGNORECASE):
                harassment_score += 0.3
        
        # Additional harassment indicators
        if message.isupper() and len(message) > 10:  # ALL CAPS
            harassment_score += 0.2
        
        if message.count('!') > 5:  # Excessive exclamation
            harassment_score += 0.1
        
        return min(harassment_score, 1.0)
    
    async def _log_security_event(self, event: SecurityEvent):
        """Log security events for monitoring and analysis"""
        event_data = {
            "user_id": event.user_id,
            "event_type": event.event_type.value,
            "severity": event.severity.value,
            "description": event.description,
            "ip_address": event.ip_address,
            "timestamp": event.timestamp.isoformat(),
            "metadata": event.metadata
        }
        
        # Store in Redis for immediate access
        await self.redis.lpush("security_events", str(event_data))
        
        # Also log to file/database for permanent storage
        logger.warning(f"Security Event: {event.description}", extra=event_data)
    
    async def _store_user_action(self, user_id: int, action: str, metadata: Dict):
        """Store user action for behavioral analysis"""
        action_data = {
            "user_id": user_id,
            "action": action,
            "metadata": metadata,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store in Redis with expiration
        key = f"user_actions:{user_id}"
        await self.redis.lpush(key, str(action_data))
        await self.redis.expire(key, 86400 * 7)  # Keep for 7 days

# Rate limiting configurations for different endpoints
RATE_LIMIT_CONFIGS = {
    "auth": {
        "login": RateLimiter(times=5, seconds=300),
        "register": RateLimiter(times=3, seconds=3600),
        "forgot_password": RateLimiter(times=3, seconds=1800)
    },
    "social": {
        "send_message": RateLimiter(times=30, seconds=3600),
        "connection_request": RateLimiter(times=10, seconds=3600),
        "profile_view": RateLimiter(times=100, seconds=3600)
    },
    "content": {
        "photo_upload": RateLimiter(times=5, seconds=1800),
        "profile_update": RateLimiter(times=10, seconds=3600),
        "revelation_create": RateLimiter(times=3, seconds=1800)
    },
    "safety": {
        "report_user": RateLimiter(times=5, seconds=86400),
        "block_user": RateLimiter(times=10, seconds=3600)
    }
}