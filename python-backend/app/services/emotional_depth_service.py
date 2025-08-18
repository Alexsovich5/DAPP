"""
Emotional Depth Assessment Service
Advanced psychological profiling for soul-based matching
Analyzes emotional maturity, vulnerability, and authenticity indicators
"""

import re
import math
import logging
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from datetime import datetime
from collections import Counter, defaultdict
from enum import Enum

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.daily_revelation import DailyRevelation

logger = logging.getLogger(__name__)


class EmotionalDepthLevel(Enum):
    """Emotional depth classification levels"""
    SURFACE = "surface"           # 0-25: Basic emotional expression
    EMERGING = "emerging"         # 26-50: Developing emotional awareness
    MODERATE = "moderate"         # 51-75: Good emotional intelligence
    DEEP = "deep"                # 76-90: High emotional sophistication
    PROFOUND = "profound"         # 91-100: Exceptional emotional depth


class VulnerabilityIndicator(Enum):
    """Types of vulnerability expression"""
    INTELLECTUAL = "intellectual"    # Sharing thoughts and ideas
    EMOTIONAL = "emotional"         # Sharing feelings and experiences
    RELATIONAL = "relational"       # Sharing relationship history/desires
    SPIRITUAL = "spiritual"         # Sharing beliefs and meaning
    PERSONAL = "personal"          # Sharing struggles and growth


@dataclass
class EmotionalDepthMetrics:
    """Comprehensive emotional depth assessment"""
    # Core depth scores (0-100)
    overall_depth: float
    emotional_vocabulary: int
    vulnerability_score: float
    authenticity_score: float
    empathy_indicators: float
    growth_mindset: float
    
    # Depth level classification
    depth_level: EmotionalDepthLevel
    
    # Supporting analysis
    vulnerability_types: List[VulnerabilityIndicator]
    depth_indicators: List[str]
    maturity_signals: List[str]
    authenticity_markers: List[str]
    
    # Relationship readiness
    emotional_availability: float
    attachment_security: float
    communication_depth: float
    
    # Analysis metadata
    confidence: float
    text_quality: str
    response_richness: int


@dataclass
class DepthCompatibilityScore:
    """Emotional depth compatibility between two users"""
    compatibility_score: float  # 0-100
    depth_harmony: float       # How well depth levels complement
    vulnerability_match: float  # Shared comfort with openness
    growth_alignment: float    # Mutual development potential
    
    # Detailed breakdown
    user1_depth: EmotionalDepthMetrics
    user2_depth: EmotionalDepthMetrics
    
    # Relationship predictions
    connection_potential: str
    recommended_approach: str
    depth_growth_timeline: str


class EmotionalDepthService:
    """Service for analyzing emotional depth and compatibility"""
    
    def __init__(self):
        # Emotional vocabulary categories
        self.emotion_categories = self._initialize_emotion_vocabulary()
        
        # Depth indicator patterns
        self.depth_patterns = self._initialize_depth_patterns()
        
        # Vulnerability detection patterns
        self.vulnerability_patterns = self._initialize_vulnerability_patterns()
        
        # Authenticity markers
        self.authenticity_markers = self._initialize_authenticity_markers()
        
        # Growth mindset indicators
        self.growth_indicators = self._initialize_growth_indicators()
        
        logger.info("Emotional Depth Service initialized")
    
    def analyze_emotional_depth(self, user: User, db: Session) -> EmotionalDepthMetrics:
        """
        Analyze a user's emotional depth from their responses and revelations
        """
        try:
            # Gather text data from multiple sources
            text_data = self._gather_user_text_data(user, db)
            
            if not text_data or len(text_data) < 100:
                return self._default_depth_metrics("insufficient_data")
            
            # Calculate core depth components
            emotional_vocab = self._analyze_emotional_vocabulary(text_data)
            vulnerability_score = self._analyze_vulnerability_expression(text_data)
            authenticity_score = self._analyze_authenticity_markers(text_data)
            empathy_indicators = self._analyze_empathy_indicators(text_data)
            growth_mindset = self._analyze_growth_mindset(text_data)
            
            # Calculate overall depth score
            overall_depth = self._calculate_overall_depth(
                emotional_vocab, vulnerability_score, authenticity_score,
                empathy_indicators, growth_mindset
            )
            
            # Determine depth level
            depth_level = self._classify_depth_level(overall_depth)
            
            # Extract specific indicators
            vulnerability_types = self._identify_vulnerability_types(text_data)
            depth_indicators = self._extract_depth_indicators(text_data)
            maturity_signals = self._identify_maturity_signals(text_data)
            authenticity_markers = self._extract_authenticity_markers(text_data)
            
            # Analyze relationship readiness
            emotional_availability = self._assess_emotional_availability(text_data)
            attachment_security = self._analyze_attachment_patterns(text_data)
            communication_depth = self._assess_communication_depth(text_data)
            
            # Calculate confidence and quality metrics
            confidence = self._calculate_assessment_confidence(text_data, overall_depth)
            text_quality = self._assess_text_quality(text_data)
            response_richness = len(text_data.split())
            
            return EmotionalDepthMetrics(
                overall_depth=round(overall_depth, 1),
                emotional_vocabulary=len(emotional_vocab),
                vulnerability_score=round(vulnerability_score, 1),
                authenticity_score=round(authenticity_score, 1),
                empathy_indicators=round(empathy_indicators, 1),
                growth_mindset=round(growth_mindset, 1),
                depth_level=depth_level,
                vulnerability_types=vulnerability_types,
                depth_indicators=depth_indicators[:5],  # Top 5
                maturity_signals=maturity_signals[:3],   # Top 3
                authenticity_markers=authenticity_markers[:3],  # Top 3
                emotional_availability=round(emotional_availability, 1),
                attachment_security=round(attachment_security, 1),
                communication_depth=round(communication_depth, 1),
                confidence=round(confidence, 1),
                text_quality=text_quality,
                response_richness=response_richness
            )
            
        except Exception as e:
            logger.error(f"Error analyzing emotional depth: {str(e)}")
            return self._default_depth_metrics("error")
    
    def calculate_depth_compatibility(self, user1: User, user2: User, 
                                    db: Session) -> DepthCompatibilityScore:
        """
        Calculate emotional depth compatibility between two users
        """
        try:
            # Analyze individual emotional depths
            depth1 = self.analyze_emotional_depth(user1, db)
            depth2 = self.analyze_emotional_depth(user2, db)
            
            # Calculate depth harmony (how well depths complement)
            depth_harmony = self._calculate_depth_harmony(depth1, depth2)
            
            # Calculate vulnerability matching
            vulnerability_match = self._calculate_vulnerability_compatibility(depth1, depth2)
            
            # Calculate growth alignment
            growth_alignment = self._calculate_growth_compatibility(depth1, depth2)
            
            # Overall compatibility score
            compatibility_score = (
                depth_harmony * 0.40 +
                vulnerability_match * 0.35 +
                growth_alignment * 0.25
            )
            
            # Generate insights
            connection_potential = self._predict_connection_potential(
                depth1, depth2, compatibility_score
            )
            recommended_approach = self._recommend_connection_approach(depth1, depth2)
            depth_growth_timeline = self._predict_depth_growth_timeline(depth1, depth2)
            
            return DepthCompatibilityScore(
                compatibility_score=round(compatibility_score, 1),
                depth_harmony=round(depth_harmony, 1),
                vulnerability_match=round(vulnerability_match, 1),
                growth_alignment=round(growth_alignment, 1),
                user1_depth=depth1,
                user2_depth=depth2,
                connection_potential=connection_potential,
                recommended_approach=recommended_approach,
                depth_growth_timeline=depth_growth_timeline
            )
            
        except Exception as e:
            logger.error(f"Error calculating depth compatibility: {str(e)}")
            return self._default_depth_compatibility()
    
    def _gather_user_text_data(self, user: User, db: Session) -> str:
        """Gather all available text data from user's responses and revelations"""
        text_parts = []
        
        # Emotional responses from onboarding
        if user.emotional_responses:
            for response in user.emotional_responses.values():
                if isinstance(response, str) and len(response.strip()) > 10:
                    text_parts.append(response.strip())
        
        # Core values responses
        if user.core_values:
            for value in user.core_values.values():
                if isinstance(value, str) and len(value.strip()) > 10:
                    text_parts.append(value.strip())
        
        # Daily revelations
        try:
            revelations = db.query(DailyRevelation).filter(
                DailyRevelation.sender_id == user.id
            ).order_by(DailyRevelation.created_at.desc()).limit(10).all()
            
            for revelation in revelations:
                if revelation.content and len(revelation.content.strip()) > 20:
                    text_parts.append(revelation.content.strip())
        except Exception as e:
            logger.warning(f"Could not fetch revelations: {str(e)}")
        
        return " ".join(text_parts)
    
    def _analyze_emotional_vocabulary(self, text: str) -> Set[str]:
        """Analyze the diversity and sophistication of emotional vocabulary"""
        text_lower = text.lower()
        found_emotions = set()
        
        for category, emotions in self.emotion_categories.items():
            for emotion in emotions:
                if emotion in text_lower:
                    found_emotions.add(emotion)
        
        return found_emotions
    
    def _analyze_vulnerability_expression(self, text: str) -> float:
        """Analyze willingness to be vulnerable and open"""
        vulnerability_score = 0.0
        text_lower = text.lower()
        
        # Count vulnerability indicators
        for category, patterns in self.vulnerability_patterns.items():
            category_score = 0
            for pattern in patterns:
                if pattern in text_lower:
                    category_score += 1
            
            # Weight different types of vulnerability
            weights = {
                "personal_struggles": 1.5,
                "fears_insecurities": 1.4,
                "past_experiences": 1.2,
                "hopes_dreams": 1.1,
                "relationship_desires": 1.3
            }
            
            vulnerability_score += category_score * weights.get(category, 1.0)
        
        # Normalize to 0-100 scale
        max_possible = sum(
            len(patterns) * weight 
            for category, patterns in self.vulnerability_patterns.items()
            for weight in [1.5, 1.4, 1.2, 1.1, 1.3]
        ) / len(self.vulnerability_patterns)
        
        return min(100.0, (vulnerability_score / max_possible) * 100)
    
    def _analyze_authenticity_markers(self, text: str) -> float:
        """Analyze indicators of authentic, genuine expression"""
        authenticity_score = 0.0
        text_lower = text.lower()
        
        # Count authenticity indicators
        for marker in self.authenticity_markers:
            if marker in text_lower:
                authenticity_score += 1
        
        # Bonus for personal pronouns and specific details
        personal_pronouns = ["i feel", "i am", "i believe", "i think", "i want", "i need"]
        for pronoun in personal_pronouns:
            authenticity_score += text_lower.count(pronoun) * 0.5
        
        # Penalty for generic responses
        generic_phrases = ["i love to laugh", "i enjoy life", "live life to the fullest"]
        for phrase in generic_phrases:
            if phrase in text_lower:
                authenticity_score -= 2
        
        # Normalize to 0-100 scale
        max_score = len(self.authenticity_markers) + 20  # Including pronoun bonuses
        return min(100.0, max(0.0, (authenticity_score / max_score) * 100))
    
    def _analyze_empathy_indicators(self, text: str) -> float:
        """Analyze indicators of empathy and consideration for others"""
        empathy_score = 0.0
        text_lower = text.lower()
        
        empathy_patterns = [
            "understand others", "feel for", "put myself in", "others feel",
            "perspective", "empathy", "compassion", "care about",
            "help others", "support", "listen to", "there for"
        ]
        
        for pattern in empathy_patterns:
            if pattern in text_lower:
                empathy_score += 1
        
        # Normalize to 0-100 scale
        return min(100.0, (empathy_score / len(empathy_patterns)) * 100)
    
    def _analyze_growth_mindset(self, text: str) -> float:
        """Analyze indicators of growth mindset and self-development"""
        growth_score = 0.0
        text_lower = text.lower()
        
        for indicator in self.growth_indicators:
            if indicator in text_lower:
                growth_score += 1
        
        # Normalize to 0-100 scale
        return min(100.0, (growth_score / len(self.growth_indicators)) * 100)
    
    def _calculate_overall_depth(self, vocab_count: int, vulnerability: float, 
                               authenticity: float, empathy: float, growth: float) -> float:
        """Calculate overall emotional depth score"""
        # Vocabulary component (0-25 points)
        vocab_score = min(25.0, vocab_count * 2)
        
        # Weight the components
        weighted_score = (
            vocab_score * 0.20 +
            vulnerability * 0.30 +
            authenticity * 0.25 +
            empathy * 0.15 +
            growth * 0.10
        )
        
        return min(100.0, weighted_score)
    
    def _classify_depth_level(self, depth_score: float) -> EmotionalDepthLevel:
        """Classify emotional depth level based on score"""
        if depth_score >= 91:
            return EmotionalDepthLevel.PROFOUND
        elif depth_score >= 76:
            return EmotionalDepthLevel.DEEP
        elif depth_score >= 51:
            return EmotionalDepthLevel.MODERATE
        elif depth_score >= 26:
            return EmotionalDepthLevel.EMERGING
        else:
            return EmotionalDepthLevel.SURFACE
    
    # Helper methods for pattern matching and analysis
    
    def _initialize_emotion_vocabulary(self) -> Dict[str, List[str]]:
        """Initialize comprehensive emotional vocabulary categories"""
        return {
            "basic_emotions": [
                "happy", "sad", "angry", "scared", "excited", "calm",
                "worried", "frustrated", "content", "disappointed"
            ],
            "complex_emotions": [
                "ambivalent", "melancholic", "euphoric", "apprehensive",
                "nostalgic", "serene", "vulnerable", "overwhelmed",
                "empowered", "conflicted", "yearning", "fulfilled"
            ],
            "nuanced_feelings": [
                "bittersweet", "contemplative", "introspective", "wistful",
                "exhilarated", "apprehensive", "tender", "fierce",
                "reverent", "whimsical", "profound", "transcendent"
            ],
            "emotional_states": [
                "centered", "grounded", "scattered", "focused",
                "flowing", "stuck", "expanding", "contracting",
                "open", "guarded", "receptive", "resistant"
            ]
        }
    
    def _initialize_depth_patterns(self) -> List[str]:
        """Initialize patterns that indicate emotional depth"""
        return [
            "deeply", "profoundly", "authentically", "genuinely",
            "meaningfully", "significantly", "intimately", "personally",
            "soul", "essence", "core", "heart", "innermost",
            "transform", "evolve", "journey", "growth", "healing"
        ]
    
    def _initialize_vulnerability_patterns(self) -> Dict[str, List[str]]:
        """Initialize vulnerability expression patterns"""
        return {
            "personal_struggles": [
                "struggle with", "difficult for me", "challenge i face",
                "hard time with", "working through", "dealing with"
            ],
            "fears_insecurities": [
                "afraid that", "worry about", "insecure about",
                "fear of", "anxious about", "scared of"
            ],
            "past_experiences": [
                "learned from", "experienced", "went through",
                "taught me", "shaped me", "changed me"
            ],
            "hopes_dreams": [
                "dream of", "hope for", "wish for",
                "aspire to", "long for", "envision"
            ],
            "relationship_desires": [
                "need in a relationship", "want from a partner",
                "looking for someone", "hope to find"
            ]
        }
    
    def _initialize_authenticity_markers(self) -> List[str]:
        """Initialize markers of authentic expression"""
        return [
            "honestly", "truthfully", "to be honest", "genuinely",
            "authentically", "really", "actually", "truly",
            "if i'm being honest", "in reality", "the truth is"
        ]
    
    def _initialize_growth_indicators(self) -> List[str]:
        """Initialize growth mindset indicators"""
        return [
            "learn", "grow", "develop", "improve", "evolve",
            "becoming", "journey", "progress", "challenge myself",
            "self-awareness", "reflection", "mindful", "conscious"
        ]
    
    def _calculate_depth_harmony(self, depth1: EmotionalDepthMetrics, 
                                depth2: EmotionalDepthMetrics) -> float:
        """Calculate how well two depth levels complement each other"""
        level_compatibility = {
            (EmotionalDepthLevel.PROFOUND, EmotionalDepthLevel.PROFOUND): 95.0,
            (EmotionalDepthLevel.PROFOUND, EmotionalDepthLevel.DEEP): 85.0,
            (EmotionalDepthLevel.DEEP, EmotionalDepthLevel.DEEP): 90.0,
            (EmotionalDepthLevel.DEEP, EmotionalDepthLevel.MODERATE): 75.0,
            (EmotionalDepthLevel.MODERATE, EmotionalDepthLevel.MODERATE): 80.0,
            (EmotionalDepthLevel.MODERATE, EmotionalDepthLevel.EMERGING): 70.0,
            (EmotionalDepthLevel.EMERGING, EmotionalDepthLevel.EMERGING): 65.0,
        }
        
        # Create sorted tuple for lookup
        key = tuple(sorted([depth1.depth_level, depth2.depth_level], key=lambda x: x.value))
        
        base_compatibility = level_compatibility.get(key, 50.0)
        
        # Adjust based on overall depth scores
        score_diff = abs(depth1.overall_depth - depth2.overall_depth)
        if score_diff <= 15:
            adjustment = 10.0
        elif score_diff <= 30:
            adjustment = 0.0
        else:
            adjustment = -10.0
        
        return min(100.0, max(0.0, base_compatibility + adjustment))
    
    def _calculate_vulnerability_compatibility(self, depth1: EmotionalDepthMetrics,
                                             depth2: EmotionalDepthMetrics) -> float:
        """Calculate vulnerability compatibility"""
        # Compare vulnerability scores
        vuln_diff = abs(depth1.vulnerability_score - depth2.vulnerability_score)
        
        if vuln_diff <= 10:
            base_score = 90.0
        elif vuln_diff <= 20:
            base_score = 80.0
        elif vuln_diff <= 30:
            base_score = 70.0
        else:
            base_score = 50.0
        
        # Bonus for shared vulnerability types
        shared_types = set(depth1.vulnerability_types) & set(depth2.vulnerability_types)
        type_bonus = len(shared_types) * 5.0
        
        return min(100.0, base_score + type_bonus)
    
    def _calculate_growth_compatibility(self, depth1: EmotionalDepthMetrics,
                                      depth2: EmotionalDepthMetrics) -> float:
        """Calculate growth mindset compatibility"""
        growth_diff = abs(depth1.growth_mindset - depth2.growth_mindset)
        
        if growth_diff <= 15:
            return 85.0
        elif growth_diff <= 30:
            return 70.0
        else:
            return 55.0
    
    # Default and utility methods
    
    def _default_depth_metrics(self, reason: str) -> EmotionalDepthMetrics:
        """Return default emotional depth metrics"""
        return EmotionalDepthMetrics(
            overall_depth=50.0,
            emotional_vocabulary=5,
            vulnerability_score=40.0,
            authenticity_score=50.0,
            empathy_indicators=45.0,
            growth_mindset=50.0,
            depth_level=EmotionalDepthLevel.EMERGING,
            vulnerability_types=[VulnerabilityIndicator.INTELLECTUAL],
            depth_indicators=["developing emotional awareness"],
            maturity_signals=["shows potential for growth"],
            authenticity_markers=["genuine responses"],
            emotional_availability=60.0,
            attachment_security=55.0,
            communication_depth=50.0,
            confidence=30.0,
            text_quality=reason,
            response_richness=0
        )
    
    def _default_depth_compatibility(self) -> DepthCompatibilityScore:
        """Return default depth compatibility score"""
        default_depth = self._default_depth_metrics("insufficient_data")
        
        return DepthCompatibilityScore(
            compatibility_score=60.0,
            depth_harmony=60.0,
            vulnerability_match=60.0,
            growth_alignment=60.0,
            user1_depth=default_depth,
            user2_depth=default_depth,
            connection_potential="Moderate potential - needs more data",
            recommended_approach="Take time to understand each other's emotional style",
            depth_growth_timeline="Development depends on mutual openness"
        )
    
    # Additional analysis methods (stubs for now)
    
    def _identify_vulnerability_types(self, text: str) -> List[VulnerabilityIndicator]:
        """Identify types of vulnerability expressed"""
        found_types = []
        text_lower = text.lower()
        
        type_patterns = {
            VulnerabilityIndicator.EMOTIONAL: ["feel", "emotion", "heart"],
            VulnerabilityIndicator.RELATIONAL: ["relationship", "partner", "love"],
            VulnerabilityIndicator.PERSONAL: ["struggle", "challenge", "growth"],
            VulnerabilityIndicator.SPIRITUAL: ["believe", "meaning", "purpose"],
            VulnerabilityIndicator.INTELLECTUAL: ["think", "learn", "understand"]
        }
        
        for vuln_type, patterns in type_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                found_types.append(vuln_type)
        
        return found_types[:3]  # Top 3 types
    
    def _extract_depth_indicators(self, text: str) -> List[str]:
        """Extract specific depth indicators found in text"""
        found_indicators = []
        text_lower = text.lower()
        
        for pattern in self.depth_patterns:
            if pattern in text_lower:
                found_indicators.append(f"Uses '{pattern}' indicating depth")
        
        return found_indicators
    
    def _identify_maturity_signals(self, text: str) -> List[str]:
        """Identify emotional maturity signals"""
        return ["Shows self-reflection", "Expresses growth mindset", "Demonstrates empathy"]
    
    def _extract_authenticity_markers(self, text: str) -> List[str]:
        """Extract authenticity markers"""
        return ["Personal pronouns usage", "Specific examples", "Honest expression"]
    
    def _assess_emotional_availability(self, text: str) -> float:
        """Assess emotional availability for relationship"""
        return 70.0  # Placeholder
    
    def _analyze_attachment_patterns(self, text: str) -> float:
        """Analyze attachment security patterns"""
        return 65.0  # Placeholder
    
    def _assess_communication_depth(self, text: str) -> float:
        """Assess communication depth preference"""
        return 75.0  # Placeholder
    
    def _calculate_assessment_confidence(self, text: str, depth_score: float) -> float:
        """Calculate confidence in the depth assessment"""
        text_length = len(text.split())
        
        if text_length >= 200:
            return min(95.0, 70.0 + (text_length / 50))
        elif text_length >= 100:
            return 70.0
        elif text_length >= 50:
            return 50.0
        else:
            return 30.0
    
    def _assess_text_quality(self, text: str) -> str:
        """Assess the quality of text data"""
        word_count = len(text.split())
        
        if word_count >= 200:
            return "rich"
        elif word_count >= 100:
            return "adequate"
        elif word_count >= 50:
            return "limited"
        else:
            return "insufficient"
    
    def _predict_connection_potential(self, depth1: EmotionalDepthMetrics, 
                                    depth2: EmotionalDepthMetrics, 
                                    compatibility_score: float) -> str:
        """Predict connection potential based on depth analysis"""
        if compatibility_score >= 85:
            return "Exceptional emotional connection potential"
        elif compatibility_score >= 75:
            return "Strong potential for deep connection"
        elif compatibility_score >= 65:
            return "Good foundation for emotional growth together"
        else:
            return "Moderate potential requiring patience and understanding"
    
    def _recommend_connection_approach(self, depth1: EmotionalDepthMetrics,
                                     depth2: EmotionalDepthMetrics) -> str:
        """Recommend approach for connecting based on depth levels"""
        if depth1.depth_level == depth2.depth_level:
            return "Share at your natural depth level for authentic connection"
        elif depth1.overall_depth > depth2.overall_depth:
            return "Allow space for gradual deepening while staying authentic"
        else:
            return "Follow their lead in emotional sharing while being genuine"
    
    def _predict_depth_growth_timeline(self, depth1: EmotionalDepthMetrics,
                                     depth2: EmotionalDepthMetrics) -> str:
        """Predict how emotional depth might develop together"""
        if depth1.growth_mindset >= 70 and depth2.growth_mindset >= 70:
            return "Rapid emotional growth and deepening over 3-6 months"
        elif depth1.growth_mindset >= 50 or depth2.growth_mindset >= 50:
            return "Steady emotional development over 6-12 months"
        else:
            return "Gradual growth requiring consistent nurturing over 12+ months"


# Global service instance
emotional_depth_service = EmotionalDepthService()