# Content Moderation Service for Dating Platform
# Comprehensive system for user safety and content filtering

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import re
import asyncio
import logging
from dataclasses import dataclass
from textblob import TextBlob
import hashlib
import json

logger = logging.getLogger(__name__)

class ModerationDecision(Enum):
    APPROVED = "approved"
    FLAGGED = "flagged"
    BLOCKED = "blocked"
    MANUAL_REVIEW = "manual_review"

class ContentType(Enum):
    MESSAGE = "message"
    PROFILE_BIO = "profile_bio"
    PROFILE_PHOTO = "profile_photo"
    REVELATION = "revelation"
    COMMENT = "comment"

class ViolationType(Enum):
    SPAM = "spam"
    HARASSMENT = "harassment"
    HATE_SPEECH = "hate_speech"
    SEXUAL_CONTENT = "sexual_content"
    VIOLENCE = "violence"
    FAKE_PROFILE = "fake_profile"
    SCAM = "scam"
    PERSONAL_INFO = "personal_info"
    INAPPROPRIATE_PHOTO = "inappropriate_photo"

@dataclass
class ModerationResult:
    decision: ModerationDecision
    confidence: float
    violations: List[ViolationType]
    filtered_content: Optional[str]
    reason: str
    metadata: Dict

class ContentModerationService:
    """
    Advanced content moderation system designed for dating platforms
    """
    
    def __init__(self, redis_client, database):
        self.redis = redis_client
        self.db = database
        self.moderation_rules = self._load_moderation_rules()
        self.user_trust_scores = {}
        
    def _load_moderation_rules(self) -> Dict:
        """Load comprehensive moderation rules"""
        return {
            "spam_keywords": [
                # Financial scams
                "make money fast", "get rich quick", "investment opportunity",
                "cryptocurrency", "bitcoin mining", "forex trading",
                "work from home", "easy money", "guaranteed income",
                
                # Dating scams
                "send money", "western union", "gift cards", "emergency funds",
                "travel visa", "customs fee", "transfer fee",
                "prove you love me", "help me financially",
                
                # Escort/prostitution
                "escort", "massage", "companionship", "generous gentleman",
                "mutual benefit", "sugar daddy", "financial support",
                "donations", "rates", "incall", "outcall",
                
                # Adult content
                "cam show", "webcam", "private show", "adult entertainment",
                "xxx", "porn", "nude pics", "sexy photos"
            ],
            
            "harassment_patterns": [
                # Direct threats
                r"\b(kill|hurt|harm|beat)\s+(you|yourself)\b",
                r"\b(die|death)\s+(to\s+)?you\b",
                r"\bi\s+will\s+(find|get|hurt)\s+you\b",
                
                # Sexual harassment
                r"\b(send|show)\s+(nudes?|naked|pictures?)\b",
                r"\bwant\s+to\s+(fuck|screw|bang)\s+you\b",
                r"\b(sexy|hot)\s+(body|ass|tits|boobs)\b",
                
                # Identity-based harassment
                r"\b(ugly|fat|stupid|worthless|pathetic)\s+(bitch|whore|slut)\b",
                r"\bgo\s+back\s+to\s+your\s+country\b",
                r"\b(racist|sexist|homophobic)\s+slurs\b"
            ],
            
            "personal_info_patterns": [
                # Phone numbers
                r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
                r"\b\+?1?[-.]?\(?[2-9]\d{2}\)?[-.]?\d{3}[-.]?\d{4}\b",
                
                # Email addresses
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                
                # Social media handles
                r"\b@[A-Za-z0-9._]+\b",
                r"\binstagram:\s*[A-Za-z0-9._]+\b",
                r"\bsnapchat:\s*[A-Za-z0-9._]+\b",
                r"\btiktok:\s*[A-Za-z0-9._]+\b",
                
                # Addresses
                r"\b\d+\s+[A-Za-z0-9\s,]+\s+(street|st|avenue|ave|road|rd|drive|dr|boulevard|blvd)\b",
                
                # Credit card patterns
                r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"
            ],
            
            "scam_patterns": [
                # Romance scam indicators
                r"\bi\s+love\s+you\b.*\bmoney\b",
                r"\bemergency.*\bneed\s+(money|help)\b",
                r"\bstuck\s+in\s+\w+.*\bmoney\b",
                r"\bfamily\s+emergency.*\bcash\b",
                
                # Investment scams
                r"\bguaranteed\s+(profit|return|income)\b",
                r"\brisk-free\s+investment\b",
                r"\bdouble\s+your\s+money\b",
                
                # Advance fee fraud
                r"\binheritance.*\bmillion\s+(dollars?|usd)\b",
                r"\blottery.*\bwon.*\bclaim\b",
                r"\bprince.*\bmoney.*\btransfer\b"
            ],
            
            "fake_profile_indicators": [
                # Generic descriptions
                "love to laugh", "easy going", "work hard play hard",
                "live life to the fullest", "no drama", "ask me anything",
                "just moved here", "new to this", "looking for something real",
                
                # Professional claims
                "model", "photographer", "social media influencer",
                "entrepreneur", "travel blogger", "consultant",
                
                # Vague personal info
                "tell you later", "ask me", "will fill this out later",
                "more about me later", "getting to know me"
            ]
        }
    
    async def moderate_content(self, content: str, content_type: ContentType, 
                             user_id: int, metadata: Dict = None) -> ModerationResult:
        """
        Main content moderation function
        """
        metadata = metadata or {}
        violations = []
        confidence_scores = []
        filtered_content = content
        
        # Get user trust score
        user_trust = await self._get_user_trust_score(user_id)
        
        # Text-based moderation
        if content_type in [ContentType.MESSAGE, ContentType.PROFILE_BIO, ContentType.REVELATION]:
            
            # Spam detection
            spam_result = await self._detect_spam(content, user_id)
            if spam_result["is_spam"]:
                violations.append(ViolationType.SPAM)
                confidence_scores.append(spam_result["confidence"])
            
            # Harassment detection
            harassment_result = await self._detect_harassment(content)
            if harassment_result["is_harassment"]:
                violations.append(ViolationType.HARASSMENT)
                confidence_scores.append(harassment_result["confidence"])
            
            # Personal information detection
            personal_info_result = self._detect_personal_information(content)
            if personal_info_result["contains_personal_info"]:
                violations.append(ViolationType.PERSONAL_INFO)
                filtered_content = personal_info_result["filtered_content"]
                confidence_scores.append(personal_info_result["confidence"])
            
            # Scam detection
            scam_result = await self._detect_scam_content(content, user_id)
            if scam_result["is_scam"]:
                violations.append(ViolationType.SCAM)
                confidence_scores.append(scam_result["confidence"])
            
            # Hate speech detection
            hate_speech_result = self._detect_hate_speech(content)
            if hate_speech_result["is_hate_speech"]:
                violations.append(ViolationType.HATE_SPEECH)
                confidence_scores.append(hate_speech_result["confidence"])
            
            # Sexual content detection
            sexual_content_result = self._detect_sexual_content(content)
            if sexual_content_result["is_sexual"]:
                violations.append(ViolationType.SEXUAL_CONTENT)
                confidence_scores.append(sexual_content_result["confidence"])
        
        # Photo-specific moderation
        elif content_type == ContentType.PROFILE_PHOTO:
            photo_result = await self._moderate_photo(content, metadata)
            if not photo_result["is_appropriate"]:
                violations.extend(photo_result["violations"])
                confidence_scores.append(photo_result["confidence"])
        
        # Determine overall decision
        decision = await self._make_moderation_decision(
            violations, confidence_scores, user_trust, content_type
        )
        
        # Calculate overall confidence
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        # Generate reason
        reason = self._generate_moderation_reason(violations, decision)
        
        # Store moderation result
        await self._store_moderation_result(user_id, content_type, decision, violations)
        
        return ModerationResult(
            decision=decision,
            confidence=overall_confidence,
            violations=violations,
            filtered_content=filtered_content if filtered_content != content else None,
            reason=reason,
            metadata={
                "user_trust_score": user_trust,
                "content_type": content_type.value,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def _detect_spam(self, content: str, user_id: int) -> Dict:
        """Comprehensive spam detection"""
        spam_score = 0.0
        indicators = []
        
        content_lower = content.lower()
        
        # Keyword-based detection
        for keyword in self.moderation_rules["spam_keywords"]:
            if keyword.lower() in content_lower:
                spam_score += 0.3
                indicators.append(f"Contains spam keyword: {keyword}")
        
        # Repetition detection
        words = content_lower.split()
        if len(words) > 5:
            unique_words = len(set(words))
            repetition_ratio = 1 - (unique_words / len(words))
            if repetition_ratio > 0.7:
                spam_score += 0.4
                indicators.append("High word repetition")
        
        # URL detection
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        if re.search(url_pattern, content):
            spam_score += 0.5
            indicators.append("Contains URL")
        
        # Excessive punctuation
        punct_ratio = sum(1 for char in content if char in '!?.,;:') / len(content) if content else 0
        if punct_ratio > 0.3:
            spam_score += 0.2
            indicators.append("Excessive punctuation")
        
        # User history check
        user_spam_history = await self._get_user_spam_history(user_id)
        if user_spam_history > 3:
            spam_score += 0.3
            indicators.append("User has spam history")
        
        # Message frequency check
        recent_messages = await self._get_recent_message_count(user_id, minutes=60)
        if recent_messages > 20:
            spam_score += 0.4
            indicators.append("High message frequency")
        
        return {
            "is_spam": spam_score > 0.6,
            "confidence": min(spam_score, 1.0),
            "indicators": indicators
        }
    
    async def _detect_harassment(self, content: str) -> Dict:
        """Detect harassment and threatening language"""
        harassment_score = 0.0
        indicators = []
        
        # Pattern-based detection
        for pattern in self.moderation_rules["harassment_patterns"]:
            if re.search(pattern, content, re.IGNORECASE):
                harassment_score += 0.8
                indicators.append("Contains harassment pattern")
        
        # Sentiment analysis
        blob = TextBlob(content)
        if blob.sentiment.polarity < -0.7:
            harassment_score += 0.4
            indicators.append("Very negative sentiment")
        
        # Profanity detection (simplified)
        profanity_list = [
            "fuck", "shit", "bitch", "asshole", "damn", "hell",
            "cunt", "whore", "slut", "bastard", "cock", "pussy"
        ]
        
        profanity_count = sum(1 for word in profanity_list if word in content.lower())
        if profanity_count > 0:
            harassment_score += min(profanity_count * 0.2, 0.6)
            indicators.append(f"Contains {profanity_count} profane words")
        
        # All caps detection (aggressive tone)
        if len(content) > 10 and content.isupper():
            harassment_score += 0.3
            indicators.append("All caps text")
        
        return {
            "is_harassment": harassment_score > 0.5,
            "confidence": min(harassment_score, 1.0),
            "indicators": indicators
        }
    
    def _detect_personal_information(self, content: str) -> Dict:
        """Detect and filter personal information"""
        filtered_content = content
        confidence = 0.0
        found_info = []
        
        # Phone number detection and filtering
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        if re.search(phone_pattern, content):
            filtered_content = re.sub(phone_pattern, '[PHONE NUMBER REMOVED]', filtered_content)
            confidence += 0.9
            found_info.append("phone_number")
        
        # Email detection and filtering
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if re.search(email_pattern, content):
            filtered_content = re.sub(email_pattern, '[EMAIL REMOVED]', filtered_content)
            confidence += 0.9
            found_info.append("email")
        
        # Social media handle detection
        social_patterns = [
            r'\b@[A-Za-z0-9._]+\b',
            r'\binstagram:\s*[A-Za-z0-9._]+\b',
            r'\bsnapchat:\s*[A-Za-z0-9._]+\b'
        ]
        
        for pattern in social_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                filtered_content = re.sub(pattern, '[SOCIAL MEDIA HANDLE REMOVED]', filtered_content, flags=re.IGNORECASE)
                confidence += 0.7
                found_info.append("social_media")
        
        # Address detection (simplified)
        address_pattern = r'\b\d+\s+[A-Za-z\s]+(?:street|st|avenue|ave|road|rd|drive|dr)\b'
        if re.search(address_pattern, content, re.IGNORECASE):
            filtered_content = re.sub(address_pattern, '[ADDRESS REMOVED]', filtered_content, flags=re.IGNORECASE)
            confidence += 0.8
            found_info.append("address")
        
        return {
            "contains_personal_info": len(found_info) > 0,
            "filtered_content": filtered_content,
            "confidence": min(confidence, 1.0),
            "info_types": found_info
        }
    
    async def _detect_scam_content(self, content: str, user_id: int) -> Dict:
        """Detect potential scam content"""
        scam_score = 0.0
        indicators = []
        
        content_lower = content.lower()
        
        # Pattern-based scam detection
        for pattern in self.moderation_rules["scam_patterns"]:
            if re.search(pattern, content_lower):
                scam_score += 0.7
                indicators.append("Contains scam pattern")
        
        # Money-related keywords in emotional context
        money_keywords = ["money", "cash", "dollars", "payment", "transfer", "send"]
        emotional_keywords = ["love", "emergency", "help", "please", "urgent"]
        
        has_money = any(keyword in content_lower for keyword in money_keywords)
        has_emotional = any(keyword in content_lower for keyword in emotional_keywords)
        
        if has_money and has_emotional:
            scam_score += 0.6
            indicators.append("Combines money request with emotional appeal")
        
        # Check for sob story patterns
        sob_story_keywords = ["hospital", "accident", "sick", "died", "funeral", "stranded"]
        if any(keyword in content_lower for keyword in sob_story_keywords) and has_money:
            scam_score += 0.8
            indicators.append("Sob story combined with money request")
        
        # User profile age check
        user_profile_age = await self._get_user_profile_age(user_id)
        if user_profile_age < 7:  # Account less than 7 days old
            if has_money:
                scam_score += 0.4
                indicators.append("New account requesting money")
        
        return {
            "is_scam": scam_score > 0.6,
            "confidence": min(scam_score, 1.0),
            "indicators": indicators
        }
    
    def _detect_hate_speech(self, content: str) -> Dict:
        """Detect hate speech and discriminatory content"""
        hate_score = 0.0
        indicators = []
        
        # Slur detection (simplified - in production use comprehensive databases)
        racial_slurs = ["n-word", "chink", "spic", "kike", "towelhead"]  # Simplified list
        sexual_slurs = ["fag", "dyke", "tranny"]
        religious_slurs = ["kike", "raghead", "papist"]
        
        all_slurs = racial_slurs + sexual_slurs + religious_slurs
        
        for slur in all_slurs:
            if slur in content.lower():
                hate_score += 0.9
                indicators.append("Contains hate speech slur")
                break
        
        # Discriminatory language patterns
        discriminatory_patterns = [
            r'\b(all|most)\s+(black|white|asian|mexican|muslim|jewish|gay|lesbian)\s+people\s+are\b',
            r'\bi\s+hate\s+(black|white|asian|mexican|muslim|jewish|gay|lesbian)\s+people\b',
            r'\b(black|white|asian|mexican|muslim|jewish|gay|lesbian)\s+people\s+should\s+(die|leave)\b'
        ]
        
        for pattern in discriminatory_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                hate_score += 0.8
                indicators.append("Contains discriminatory language")
        
        return {
            "is_hate_speech": hate_score > 0.7,
            "confidence": min(hate_score, 1.0),
            "indicators": indicators
        }
    
    def _detect_sexual_content(self, content: str) -> Dict:
        """Detect inappropriate sexual content"""
        sexual_score = 0.0
        indicators = []
        
        # Explicit sexual terms
        explicit_terms = [
            "fuck", "pussy", "cock", "dick", "cum", "orgasm",
            "masturbate", "blow job", "anal", "oral sex"
        ]
        
        for term in explicit_terms:
            if term in content.lower():
                sexual_score += 0.6
                indicators.append("Contains explicit sexual language")
                break
        
        # Sexual invitation patterns
        sexual_patterns = [
            r'\bwant\s+to\s+have\s+sex\b',
            r'\bcome\s+over\s+and\s+fuck\b',
            r'\bsend\s+(nude|naked)\s+(pics?|photos?)\b',
            r'\bshow\s+me\s+your\s+(body|tits|ass)\b'
        ]
        
        for pattern in sexual_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                sexual_score += 0.8
                indicators.append("Contains sexual invitation")
        
        # Body part references in sexual context
        body_parts = ["tits", "boobs", "ass", "penis", "vagina"]
        sexual_verbs = ["touch", "lick", "suck", "grab", "squeeze"]
        
        has_body_part = any(part in content.lower() for part in body_parts)
        has_sexual_verb = any(verb in content.lower() for verb in sexual_verbs)
        
        if has_body_part and has_sexual_verb:
            sexual_score += 0.7
            indicators.append("Sexual reference to body parts")
        
        return {
            "is_sexual": sexual_score > 0.5,
            "confidence": min(sexual_score, 1.0),
            "indicators": indicators
        }
    
    async def _moderate_photo(self, photo_data: bytes, metadata: Dict) -> Dict:
        """Moderate photo content (placeholder for image analysis)"""
        # In production, this would integrate with image analysis services
        # like AWS Rekognition, Google Vision API, or custom ML models
        
        violations = []
        confidence = 0.0
        
        # For now, return appropriate result
        # In real implementation, check for:
        # - NSFW content
        # - Faces (ensure profile photos contain faces)
        # - Fake/stock photos
        # - Violence or weapons
        # - Text in images (for spam)
        
        return {
            "is_appropriate": True,
            "violations": violations,
            "confidence": confidence
        }
    
    async def _make_moderation_decision(self, violations: List[ViolationType], 
                                      confidence_scores: List[float], 
                                      user_trust: float, 
                                      content_type: ContentType) -> ModerationDecision:
        """Make final moderation decision based on all factors"""
        
        if not violations:
            return ModerationDecision.APPROVED
        
        # Calculate severity
        high_severity_violations = [
            ViolationType.HARASSMENT, ViolationType.HATE_SPEECH, 
            ViolationType.VIOLENCE, ViolationType.SCAM
        ]
        
        has_high_severity = any(v in high_severity_violations for v in violations)
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        # Decision matrix
        if has_high_severity and avg_confidence > 0.8:
            return ModerationDecision.BLOCKED
        elif has_high_severity and avg_confidence > 0.6:
            return ModerationDecision.MANUAL_REVIEW
        elif len(violations) > 2 or avg_confidence > 0.7:
            return ModerationDecision.FLAGGED
        elif user_trust < 0.3:  # Low trust users get stricter treatment
            return ModerationDecision.MANUAL_REVIEW
        else:
            return ModerationDecision.FLAGGED
    
    def _generate_moderation_reason(self, violations: List[ViolationType], 
                                  decision: ModerationDecision) -> str:
        """Generate human-readable moderation reason"""
        if not violations:
            return "Content approved"
        
        violation_descriptions = {
            ViolationType.SPAM: "spam or promotional content",
            ViolationType.HARASSMENT: "harassment or threatening language",
            ViolationType.HATE_SPEECH: "hate speech or discriminatory content",
            ViolationType.SEXUAL_CONTENT: "inappropriate sexual content",
            ViolationType.VIOLENCE: "violent or threatening content",
            ViolationType.SCAM: "potential scam or fraudulent content",
            ViolationType.PERSONAL_INFO: "personal information that has been filtered",
            ViolationType.FAKE_PROFILE: "indicators of fake profile"
        }
        
        reasons = [violation_descriptions.get(v, str(v)) for v in violations]
        
        if decision == ModerationDecision.BLOCKED:
            return f"Content blocked due to: {', '.join(reasons)}"
        elif decision == ModerationDecision.FLAGGED:
            return f"Content flagged for: {', '.join(reasons)}"
        elif decision == ModerationDecision.MANUAL_REVIEW:
            return f"Content requires manual review for: {', '.join(reasons)}"
        else:
            return f"Content approved with filtering applied for: {', '.join(reasons)}"
    
    # Helper methods for database queries
    async def _get_user_trust_score(self, user_id: int) -> float:
        """Get user trust score based on history"""
        # Implementation would query database for user's moderation history
        # For now, return default score
        return 0.5
    
    async def _get_user_spam_history(self, user_id: int) -> int:
        """Get count of user's spam violations"""
        # Implementation would query moderation history
        return 0
    
    async def _get_recent_message_count(self, user_id: int, minutes: int) -> int:
        """Get count of recent messages from user"""
        # Implementation would query message history
        return 0
    
    async def _get_user_profile_age(self, user_id: int) -> int:
        """Get age of user's profile in days"""
        # Implementation would calculate from user creation date
        return 30
    
    async def _store_moderation_result(self, user_id: int, content_type: ContentType, 
                                     decision: ModerationDecision, violations: List[ViolationType]):
        """Store moderation result for future reference"""
        result_data = {
            "user_id": user_id,
            "content_type": content_type.value,
            "decision": decision.value,
            "violations": [v.value for v in violations],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store in Redis for immediate access
        await self.redis.lpush("moderation_results", json.dumps(result_data))
        
        # Update user trust score based on violations
        if violations:
            await self._update_user_trust_score(user_id, len(violations))
    
    async def _update_user_trust_score(self, user_id: int, violation_count: int):
        """Update user trust score based on violations"""
        current_score = await self._get_user_trust_score(user_id)
        penalty = violation_count * 0.1
        new_score = max(0.0, current_score - penalty)
        
        # Store updated score
        await self.redis.set(f"trust_score:{user_id}", new_score)

# Automated moderation configuration
MODERATION_CONFIG = {
    "auto_block_threshold": 0.9,  # Auto-block if confidence > 90%
    "manual_review_threshold": 0.7,  # Manual review if confidence > 70%
    "flag_threshold": 0.5,  # Flag if confidence > 50%
    
    "content_type_sensitivity": {
        ContentType.MESSAGE: 0.8,  # Messages are more sensitive
        ContentType.PROFILE_BIO: 0.9,  # Profile bios are very sensitive
        ContentType.REVELATION: 0.7,  # Revelations allow more personal content
        ContentType.PROFILE_PHOTO: 0.95  # Photos are extremely sensitive
    },
    
    "trust_score_adjustments": {
        ViolationType.SPAM: -0.1,
        ViolationType.HARASSMENT: -0.3,
        ViolationType.HATE_SPEECH: -0.5,
        ViolationType.SCAM: -0.4,
        ViolationType.FAKE_PROFILE: -0.6
    }
}