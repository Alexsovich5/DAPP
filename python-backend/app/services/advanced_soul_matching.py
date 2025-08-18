"""
Advanced Soul Matching Service - Enhanced Compatibility Algorithm
Building upon the existing soul compatibility service with advanced features:
- Enhanced emotional intelligence detection
- Dynamic weight adjustment based on user preferences  
- Temporal compatibility analysis
- Advanced sentiment analysis
- Machine learning feedback integration
"""

import json
import math
import logging
import re
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime, date, time
from collections import Counter, defaultdict
from enum import Enum

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.soul_connection import SoulConnection, ConnectionEnergyLevel
from app.models.daily_revelation import DailyRevelation
from app.services.soul_compatibility_service import CompatibilityScore, compatibility_service

logger = logging.getLogger(__name__)


class MatchingPreference(Enum):
    """User preferences for matching priority"""
    VALUES_FIRST = "values_first"
    PERSONALITY_FIRST = "personality_first"
    INTERESTS_FIRST = "interests_first"
    EMOTIONAL_FIRST = "emotional_first"
    BALANCED = "balanced"


class TimeCompatibilityFactor(Enum):
    """Time-based compatibility factors"""
    CHRONOTYPE = "chronotype"  # Morning vs evening person
    AVAILABILITY = "availability"  # When free for dates/calls
    COMMUNICATION_TIMES = "communication_times"  # Preferred messaging times


@dataclass
class EmotionalIntelligenceMetrics:
    """Advanced emotional intelligence assessment"""
    self_awareness: float  # 0-100
    empathy_level: float   # 0-100
    emotional_regulation: float  # 0-100
    social_awareness: float  # 0-100
    relationship_skills: float  # 0-100
    emotional_vocabulary: int  # Number of emotion words used
    depth_indicators: List[str]  # Specific depth indicators found


@dataclass
class AdvancedCompatibilityScore(CompatibilityScore):
    """Extended compatibility score with advanced metrics"""
    # Additional advanced metrics
    emotional_intelligence_compatibility: float
    temporal_compatibility: float
    communication_rhythm_match: float
    growth_potential: float
    conflict_resolution_compatibility: float
    
    # Enhanced insights
    relationship_prediction: str  # Predicted relationship dynamic
    growth_timeline: str  # Expected relationship development
    recommended_first_date: str  # AI-suggested first date type
    conversation_starters: List[str]  # Personalized conversation topics


class AdvancedSoulMatchingService:
    """Enhanced compatibility calculation service with advanced algorithms"""
    
    def __init__(self):
        # Advanced algorithm weights (dynamically adjustable)
        self.advanced_weights = {
            "emotional_intelligence": 0.25,
            "temporal_compatibility": 0.10,
            "communication_rhythm": 0.15,
            "growth_potential": 0.15,
            "conflict_resolution": 0.10,
            "base_compatibility": 0.25  # Weight for existing base score
        }
        
        # Emotional intelligence detection patterns
        self.emotional_patterns = self._initialize_emotional_patterns()
        
        # Temporal compatibility mappings
        self.temporal_mappings = self._initialize_temporal_mappings()
        
        # Advanced sentiment analysis keywords
        self.sentiment_keywords = self._initialize_sentiment_keywords()
        
        logger.info("Advanced Soul Matching Service initialized")
    
    def calculate_advanced_compatibility(self, user1: User, user2: User, db: Session, 
                                       user1_preferences: Optional[MatchingPreference] = None) -> AdvancedCompatibilityScore:
        """
        Calculate advanced compatibility with enhanced algorithms
        """
        try:
            # Get base compatibility score
            base_score = compatibility_service.calculate_compatibility(user1, user2, db)
            
            # Calculate advanced metrics
            ei_compatibility = self._calculate_emotional_intelligence_compatibility(user1, user2)
            temporal_compatibility = self._calculate_temporal_compatibility(user1, user2)
            communication_rhythm = self._calculate_communication_rhythm_match(user1, user2)
            growth_potential = self._calculate_growth_potential(user1, user2)
            conflict_resolution = self._calculate_conflict_resolution_compatibility(user1, user2)
            
            # Adjust weights based on user preferences
            adjusted_weights = self._adjust_weights_for_preferences(user1_preferences)
            
            # Calculate enhanced total score
            enhanced_total = (
                base_score.total_score * adjusted_weights["base_compatibility"] +
                ei_compatibility * adjusted_weights["emotional_intelligence"] +
                temporal_compatibility * adjusted_weights["temporal_compatibility"] +
                communication_rhythm * adjusted_weights["communication_rhythm"] +
                growth_potential * adjusted_weights["growth_potential"] +
                conflict_resolution * adjusted_weights["conflict_resolution"]
            )
            
            # Generate advanced insights
            relationship_prediction = self._predict_relationship_dynamic(
                user1, user2, enhanced_total, ei_compatibility, growth_potential
            )
            
            growth_timeline = self._predict_growth_timeline(growth_potential, base_score.total_score)
            
            recommended_first_date = self._suggest_first_date_type(
                user1, user2, base_score.interests_score, base_score.personality_score
            )
            
            conversation_starters = self._generate_conversation_starters(
                user1, user2, base_score.strengths
            )
            
            # Create advanced compatibility score
            return AdvancedCompatibilityScore(
                # Base compatibility metrics
                total_score=round(enhanced_total, 1),
                confidence=base_score.confidence,
                interests_score=base_score.interests_score,
                values_score=base_score.values_score,
                personality_score=base_score.personality_score,
                communication_score=base_score.communication_score,
                demographic_score=base_score.demographic_score,
                emotional_resonance=base_score.emotional_resonance,
                match_quality=self._determine_enhanced_match_quality(enhanced_total),
                energy_level=self._determine_enhanced_energy_level(enhanced_total),
                strengths=base_score.strengths,
                growth_areas=base_score.growth_areas,
                compatibility_summary=self._generate_enhanced_summary(
                    enhanced_total, base_score.strengths, growth_potential
                ),
                
                # Advanced metrics
                emotional_intelligence_compatibility=round(ei_compatibility, 1),
                temporal_compatibility=round(temporal_compatibility, 1),
                communication_rhythm_match=round(communication_rhythm, 1),
                growth_potential=round(growth_potential, 1),
                conflict_resolution_compatibility=round(conflict_resolution, 1),
                
                # Enhanced insights
                relationship_prediction=relationship_prediction,
                growth_timeline=growth_timeline,
                recommended_first_date=recommended_first_date,
                conversation_starters=conversation_starters
            )
            
        except Exception as e:
            logger.error(f"Error calculating advanced compatibility: {str(e)}")
            # Return enhanced default score
            return self._default_advanced_compatibility_score()
    
    def _calculate_emotional_intelligence_compatibility(self, user1: User, user2: User) -> float:
        """Calculate emotional intelligence compatibility using advanced NLP analysis"""
        try:
            # Analyze emotional intelligence for both users
            ei1 = self._analyze_emotional_intelligence(user1)
            ei2 = self._analyze_emotional_intelligence(user2)
            
            if not ei1 or not ei2:
                return 65.0  # Default when insufficient data
            
            # Calculate compatibility in each EI dimension
            self_awareness_compat = self._calculate_ei_dimension_compatibility(
                ei1.self_awareness, ei2.self_awareness, "similar"
            )
            
            empathy_compat = self._calculate_ei_dimension_compatibility(
                ei1.empathy_level, ei2.empathy_level, "similar"
            )
            
            regulation_compat = self._calculate_ei_dimension_compatibility(
                ei1.emotional_regulation, ei2.emotional_regulation, "complementary"
            )
            
            social_compat = self._calculate_ei_dimension_compatibility(
                ei1.social_awareness, ei2.social_awareness, "similar"
            )
            
            relationship_compat = self._calculate_ei_dimension_compatibility(
                ei1.relationship_skills, ei2.relationship_skills, "similar"
            )
            
            # Vocabulary diversity bonus
            vocab_bonus = 0.0
            if ei1.emotional_vocabulary >= 10 and ei2.emotional_vocabulary >= 10:
                vocab_bonus = 10.0
            elif ei1.emotional_vocabulary >= 5 and ei2.emotional_vocabulary >= 5:
                vocab_bonus = 5.0
            
            # Calculate weighted average
            ei_compatibility = (
                self_awareness_compat * 0.25 +
                empathy_compat * 0.30 +
                regulation_compat * 0.20 +
                social_compat * 0.15 +
                relationship_compat * 0.10
            ) + vocab_bonus
            
            return min(100.0, ei_compatibility)
            
        except Exception as e:
            logger.error(f"Error calculating EI compatibility: {str(e)}")
            return 65.0
    
    def _analyze_emotional_intelligence(self, user: User) -> Optional[EmotionalIntelligenceMetrics]:
        """Analyze user's emotional intelligence from their responses"""
        try:
            responses = user.emotional_responses or {}
            if not responses:
                return None
            
            # Combine all text responses
            combined_text = " ".join([
                str(response) for response in responses.values() 
                if isinstance(response, str)
            ])
            
            if not combined_text or len(combined_text) < 50:
                return None
            
            text_lower = combined_text.lower()
            
            # Analyze self-awareness indicators
            self_awareness = self._calculate_self_awareness_score(text_lower)
            
            # Analyze empathy indicators
            empathy_level = self._calculate_empathy_score(text_lower)
            
            # Analyze emotional regulation
            emotional_regulation = self._calculate_regulation_score(text_lower)
            
            # Analyze social awareness
            social_awareness = self._calculate_social_awareness_score(text_lower)
            
            # Analyze relationship skills
            relationship_skills = self._calculate_relationship_skills_score(text_lower)
            
            # Count emotional vocabulary
            emotional_vocabulary = self._count_emotional_vocabulary(text_lower)
            
            # Identify depth indicators
            depth_indicators = self._identify_depth_indicators(text_lower)
            
            return EmotionalIntelligenceMetrics(
                self_awareness=self_awareness,
                empathy_level=empathy_level,
                emotional_regulation=emotional_regulation,
                social_awareness=social_awareness,
                relationship_skills=relationship_skills,
                emotional_vocabulary=emotional_vocabulary,
                depth_indicators=depth_indicators
            )
            
        except Exception as e:
            logger.error(f"Error analyzing emotional intelligence: {str(e)}")
            return None
    
    def _calculate_temporal_compatibility(self, user1: User, user2: User) -> float:
        """Calculate temporal compatibility (chronotype, availability, etc.)"""
        try:
            temporal_factors = []
            
            # Analyze chronotype compatibility
            chronotype_compat = self._analyze_chronotype_compatibility(user1, user2)
            temporal_factors.append(chronotype_compat)
            
            # Analyze availability overlap
            availability_compat = self._analyze_availability_compatibility(user1, user2)
            temporal_factors.append(availability_compat)
            
            # Analyze communication timing preferences
            comm_timing_compat = self._analyze_communication_timing(user1, user2)
            temporal_factors.append(comm_timing_compat)
            
            return sum(temporal_factors) / len(temporal_factors) if temporal_factors else 70.0
            
        except Exception as e:
            logger.error(f"Error calculating temporal compatibility: {str(e)}")
            return 70.0
    
    def _calculate_growth_potential(self, user1: User, user2: User) -> float:
        """Calculate potential for mutual growth and development"""
        try:
            growth_indicators = []
            
            # Analyze openness to new experiences
            openness_score = self._analyze_openness_indicators(user1, user2)
            growth_indicators.append(openness_score)
            
            # Analyze learning orientation
            learning_score = self._analyze_learning_orientation(user1, user2)
            growth_indicators.append(learning_score)
            
            # Analyze complementary skills/knowledge
            complementary_score = self._analyze_complementary_growth_areas(user1, user2)
            growth_indicators.append(complementary_score)
            
            # Analyze shared goals and aspirations
            goals_score = self._analyze_shared_aspirations(user1, user2)
            growth_indicators.append(goals_score)
            
            return sum(growth_indicators) / len(growth_indicators) if growth_indicators else 65.0
            
        except Exception as e:
            logger.error(f"Error calculating growth potential: {str(e)}")
            return 65.0
    
    def _predict_relationship_dynamic(self, user1: User, user2: User, total_score: float, 
                                    ei_compatibility: float, growth_potential: float) -> str:
        """Predict the likely relationship dynamic based on compatibility factors"""
        try:
            if total_score >= 90 and ei_compatibility >= 80:
                if growth_potential >= 80:
                    return "Transformational Partnership - Deep growth and evolution together"
                else:
                    return "Harmonious Union - Natural ease and understanding"
            elif total_score >= 80:
                if growth_potential >= 75:
                    return "Dynamic Growth Partnership - Exciting mutual development"
                else:
                    return "Stable Companionship - Reliable and supportive connection"
            elif total_score >= 70:
                if ei_compatibility >= 70:
                    return "Emotionally Rich Connection - Deep feeling with some differences"
                else:
                    return "Complementary Partnership - Different strengths that balance"
            elif total_score >= 60:
                return "Exploratory Connection - Potential that requires nurturing"
            else:
                return "Friendship Foundation - Better suited as friends initially"
                
        except Exception as e:
            logger.error(f"Error predicting relationship dynamic: {str(e)}")
            return "Connection with Potential - Requires getting to know each other"
    
    def _suggest_first_date_type(self, user1: User, user2: User, 
                               interests_score: float, personality_score: float) -> str:
        """Suggest optimal first date type based on compatibility analysis"""
        try:
            interests1 = set(user1.interests or [])
            interests2 = set(user2.interests or [])
            shared_interests = interests1.intersection(interests2)
            
            personality1 = user1.personality_traits or {}
            personality2 = user2.personality_traits or {}
            
            extroversion1 = personality1.get("extroversion", 50)
            extroversion2 = personality2.get("extroversion", 50)
            avg_extroversion = (extroversion1 + extroversion2) / 2
            
            # Activity-based suggestions
            if "cooking" in shared_interests or "food" in shared_interests:
                return "Cooking class or food market exploration - Share your culinary interests"
            elif "art" in shared_interests or "music" in shared_interests:
                return "Art gallery or live music venue - Explore creativity together"
            elif "nature" in shared_interests or "hiking" in shared_interests:
                return "Nature walk or botanical garden - Connect in a peaceful setting"
            elif "books" in shared_interests or "reading" in shared_interests:
                return "Bookstore café or literary event - Discuss ideas over coffee"
            
            # Personality-based suggestions
            if avg_extroversion >= 70:
                return "Interactive experience - Escape room or mini golf for fun interaction"
            elif avg_extroversion <= 40:
                return "Quiet café or museum - Intimate setting for deep conversation"
            else:
                return "Coffee walk in a park - Perfect balance of activity and conversation"
                
        except Exception as e:
            logger.error(f"Error suggesting first date: {str(e)}")
            return "Coffee or tea date - Classic and comfortable for getting to know each other"
    
    def _generate_conversation_starters(self, user1: User, user2: User, strengths: List[str]) -> List[str]:
        """Generate personalized conversation starters based on compatibility analysis"""
        try:
            starters = []
            
            interests1 = set(user1.interests or [])
            interests2 = set(user2.interests or [])
            shared_interests = interests1.intersection(interests2)
            
            # Interest-based starters
            if "travel" in shared_interests:
                starters.append("What's the most meaningful place you've ever visited?")
            if "music" in shared_interests:
                starters.append("What song always puts you in a good mood?")
            if "cooking" in shared_interests:
                starters.append("What's your favorite dish to cook when you want to feel comforted?")
            if "books" in shared_interests:
                starters.append("What book has influenced how you see the world?")
            
            # Values-based starters from strengths
            if any("values" in strength.lower() for strength in strengths):
                starters.append("What values are you most proud of living by?")
                starters.append("How do you like to make a positive impact in the world?")
            
            # Personality-based starters
            if any("personality" in strength.lower() for strength in strengths):
                starters.append("What's something that always makes you laugh?")
                starters.append("How do you recharge when you need to feel like yourself again?")
            
            # Communication-based starters
            if any("communication" in strength.lower() for strength in strengths):
                starters.append("What's the best advice someone has ever given you?")
                starters.append("How do you prefer to celebrate good news?")
            
            # Default starters if none matched
            if not starters:
                starters = [
                    "What's something you're really passionate about right now?",
                    "What's the most interesting thing that's happened to you this week?",
                    "If you could learn any new skill instantly, what would it be?"
                ]
            
            # Limit to top 5 most relevant
            return starters[:5]
            
        except Exception as e:
            logger.error(f"Error generating conversation starters: {str(e)}")
            return [
                "What brings you the most joy in life?",
                "What's something you're looking forward to?",
                "How do you like to spend your ideal weekend?"
            ]
    
    # Helper methods for advanced calculations
    
    def _initialize_emotional_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for emotional intelligence detection"""
        return {
            "self_awareness": [
                "i feel", "i realize", "i recognize", "i understand about myself",
                "my emotions", "when i", "i tend to", "i notice that i"
            ],
            "empathy": [
                "others feel", "understand others", "put myself in", "perspective",
                "how others", "empathy", "compassion", "others' emotions"
            ],
            "regulation": [
                "manage my", "cope with", "handle stress", "calm down",
                "process emotions", "work through", "deal with feelings"
            ],
            "social_awareness": [
                "social situations", "group dynamics", "read the room",
                "social cues", "atmosphere", "others around me"
            ],
            "relationship_skills": [
                "communicate", "resolve conflicts", "build relationships",
                "trust", "intimacy", "connection", "support others"
            ]
        }
    
    def _initialize_temporal_mappings(self) -> Dict[str, Dict[str, float]]:
        """Initialize temporal compatibility mappings"""
        return {
            "chronotype": {
                ("morning", "morning"): 85.0,
                ("evening", "evening"): 85.0,
                ("morning", "evening"): 40.0,
                ("flexible", "morning"): 70.0,
                ("flexible", "evening"): 70.0,
                ("flexible", "flexible"): 75.0
            }
        }
    
    def _initialize_sentiment_keywords(self) -> Dict[str, List[str]]:
        """Initialize advanced sentiment analysis keywords"""
        return {
            "positive_depth": [
                "deeply", "profoundly", "meaningfully", "authentically",
                "genuinely", "wholeheartedly", "passionately"
            ],
            "emotional_maturity": [
                "growth", "learning", "understanding", "wisdom",
                "perspective", "balance", "mindfulness"
            ],
            "relationship_readiness": [
                "partnership", "together", "support", "share",
                "commitment", "future", "building"
            ]
        }
    
    # Placeholder methods for complex calculations (to be implemented)
    
    def _calculate_self_awareness_score(self, text: str) -> float:
        """Calculate self-awareness score from text analysis"""
        patterns = self.emotional_patterns["self_awareness"]
        score = sum(1 for pattern in patterns if pattern in text)
        return min(100.0, (score * 15) + 40)
    
    def _calculate_empathy_score(self, text: str) -> float:
        """Calculate empathy score from text analysis"""
        patterns = self.emotional_patterns["empathy"]
        score = sum(1 for pattern in patterns if pattern in text)
        return min(100.0, (score * 20) + 35)
    
    def _calculate_regulation_score(self, text: str) -> float:
        """Calculate emotional regulation score"""
        patterns = self.emotional_patterns["regulation"]
        score = sum(1 for pattern in patterns if pattern in text)
        return min(100.0, (score * 18) + 40)
    
    def _calculate_social_awareness_score(self, text: str) -> float:
        """Calculate social awareness score"""
        patterns = self.emotional_patterns["social_awareness"]
        score = sum(1 for pattern in patterns if pattern in text)
        return min(100.0, (score * 16) + 45)
    
    def _calculate_relationship_skills_score(self, text: str) -> float:
        """Calculate relationship skills score"""
        patterns = self.emotional_patterns["relationship_skills"]
        score = sum(1 for pattern in patterns if pattern in text)
        return min(100.0, (score * 14) + 50)
    
    def _count_emotional_vocabulary(self, text: str) -> int:
        """Count diverse emotional vocabulary usage"""
        emotion_words = [
            "happy", "sad", "angry", "excited", "nervous", "calm", "frustrated",
            "grateful", "disappointed", "hopeful", "anxious", "peaceful", "inspired",
            "overwhelmed", "content", "curious", "confident", "vulnerable", "empowered"
        ]
        return len(set(word for word in emotion_words if word in text))
    
    def _identify_depth_indicators(self, text: str) -> List[str]:
        """Identify specific depth indicators in text"""
        depth_patterns = [
            "meaningful", "deep", "profound", "authentic", "genuine",
            "soul", "heart", "essence", "core", "innermost"
        ]
        return [pattern for pattern in depth_patterns if pattern in text]
    
    def _calculate_ei_dimension_compatibility(self, score1: float, score2: float, 
                                           compatibility_type: str) -> float:
        """Calculate compatibility for a specific EI dimension"""
        diff = abs(score1 - score2)
        
        if compatibility_type == "similar":
            if diff <= 10:
                return 90.0
            elif diff <= 20:
                return 75.0
            elif diff <= 30:
                return 60.0
            else:
                return 45.0
        else:  # complementary
            if 15 <= diff <= 35:
                return 85.0
            elif diff < 15:
                return 70.0
            else:
                return 50.0
    
    def _adjust_weights_for_preferences(self, preference: Optional[MatchingPreference]) -> Dict[str, float]:
        """Adjust algorithm weights based on user preferences"""
        if not preference or preference == MatchingPreference.BALANCED:
            return self.advanced_weights
        
        adjusted = self.advanced_weights.copy()
        
        if preference == MatchingPreference.EMOTIONAL_FIRST:
            adjusted["emotional_intelligence"] = 0.35
            adjusted["base_compatibility"] = 0.20
        elif preference == MatchingPreference.VALUES_FIRST:
            adjusted["base_compatibility"] = 0.35  # Values are in base compatibility
            adjusted["emotional_intelligence"] = 0.20
        # Add more preference adjustments as needed
        
        return adjusted
    
    # Placeholder methods for temporal analysis
    def _analyze_chronotype_compatibility(self, user1: User, user2: User) -> float:
        return 70.0  # Default implementation
    
    def _analyze_availability_compatibility(self, user1: User, user2: User) -> float:
        return 70.0  # Default implementation
    
    def _analyze_communication_timing(self, user1: User, user2: User) -> float:
        return 70.0  # Default implementation
    
    def _calculate_communication_rhythm_match(self, user1: User, user2: User) -> float:
        return 70.0  # Default implementation
    
    def _calculate_conflict_resolution_compatibility(self, user1: User, user2: User) -> float:
        return 70.0  # Default implementation
    
    # Placeholder methods for growth analysis
    def _analyze_openness_indicators(self, user1: User, user2: User) -> float:
        return 65.0
    
    def _analyze_learning_orientation(self, user1: User, user2: User) -> float:
        return 65.0
    
    def _analyze_complementary_growth_areas(self, user1: User, user2: User) -> float:
        return 65.0
    
    def _analyze_shared_aspirations(self, user1: User, user2: User) -> float:
        return 65.0
    
    def _determine_enhanced_match_quality(self, score: float) -> str:
        """Determine enhanced match quality with more nuanced labels"""
        if score >= 95:
            return "Transcendent Soul Connection"
        elif score >= 90:
            return "Exceptional Soul Bond"
        elif score >= 80:
            return "Deep Compatibility"
        elif score >= 70:
            return "Strong Potential"
        elif score >= 60:
            return "Good Foundation"
        else:
            return "Exploratory Match"
    
    def _determine_enhanced_energy_level(self, score: float) -> ConnectionEnergyLevel:
        """Determine energy level with enhanced thresholds"""
        if score >= 92:
            return ConnectionEnergyLevel.SOULMATE
        elif score >= 78:
            return ConnectionEnergyLevel.HIGH
        elif score >= 62:
            return ConnectionEnergyLevel.MEDIUM
        else:
            return ConnectionEnergyLevel.LOW
    
    def _generate_enhanced_summary(self, total_score: float, strengths: List[str], 
                                 growth_potential: float) -> str:
        """Generate enhanced compatibility summary"""
        if total_score >= 90:
            base = "Exceptional compatibility with profound potential for soulmate connection."
        elif total_score >= 80:
            base = "Strong compatibility with excellent relationship potential."
        elif total_score >= 70:
            base = "Good compatibility foundation with promising growth opportunities."
        else:
            base = "Moderate compatibility that could develop with mutual understanding."
        
        if growth_potential >= 80:
            base += " High potential for transformational growth together."
        elif growth_potential >= 65:
            base += " Good potential for mutual development and learning."
        
        return base
    
    def _predict_growth_timeline(self, growth_potential: float, base_score: float) -> str:
        """Predict relationship growth timeline"""
        if growth_potential >= 80 and base_score >= 80:
            return "Rapid initial connection with deep bonding over 3-6 months"
        elif growth_potential >= 70:
            return "Steady development with meaningful milestones over 6-12 months"
        elif growth_potential >= 60:
            return "Gradual growth requiring patience over 12+ months"
        else:
            return "Slow development requiring significant mutual effort"
    
    def _default_advanced_compatibility_score(self) -> AdvancedCompatibilityScore:
        """Return default advanced compatibility score when calculation fails"""
        return AdvancedCompatibilityScore(
            # Base metrics
            total_score=60.0,
            confidence=30.0,
            interests_score=50.0,
            values_score=50.0,
            personality_score=50.0,
            communication_score=50.0,
            demographic_score=50.0,
            emotional_resonance=50.0,
            match_quality="Good Foundation",
            energy_level=ConnectionEnergyLevel.MEDIUM,
            strengths=["Potential for connection"],
            growth_areas=["Getting to know each other better"],
            compatibility_summary="Advanced compatibility assessment needs more profile data.",
            
            # Advanced metrics
            emotional_intelligence_compatibility=60.0,
            temporal_compatibility=60.0,
            communication_rhythm_match=60.0,
            growth_potential=60.0,
            conflict_resolution_compatibility=60.0,
            
            # Enhanced insights
            relationship_prediction="Connection with Potential",
            growth_timeline="Development timeline depends on mutual engagement",
            recommended_first_date="Coffee or tea date - comfortable setting for connection",
            conversation_starters=[
                "What brings you the most joy in life?",
                "What's something you're passionate about?",
                "How do you like to spend your ideal day?"
            ]
        )


# Global service instance
advanced_matching_service = AdvancedSoulMatchingService()