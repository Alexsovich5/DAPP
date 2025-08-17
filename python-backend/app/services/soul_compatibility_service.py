"""
Soul Compatibility Algorithm Service - Phase 4 Enhanced Matching
Advanced local algorithms for soul-based compatibility scoring
"""
import json
import math
import logging
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from datetime import datetime, date
from collections import Counter

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.soul_connection import SoulConnection, ConnectionEnergyLevel
from app.models.daily_revelation import DailyRevelation
from app.models.soul_analytics import CompatibilityAccuracyTracking

logger = logging.getLogger(__name__)


@dataclass
class CompatibilityScore:
    """Comprehensive compatibility score breakdown"""
    total_score: float  # 0-100
    confidence: float   # 0-100
    
    # Individual components (0-100 each)
    interests_score: float
    values_score: float
    personality_score: float
    communication_score: float
    demographic_score: float
    emotional_resonance: float
    
    # Qualitative assessment
    match_quality: str  # low, medium, high, soulmate
    energy_level: ConnectionEnergyLevel
    
    # Supporting data
    strengths: List[str]
    growth_areas: List[str]
    compatibility_summary: str


class SoulCompatibilityService:
    """Advanced compatibility calculation service"""
    
    def __init__(self):
        # Algorithm weights - tunable based on success data
        self.weights = {
            "interests": 0.20,      # Shared hobbies and activities
            "values": 0.30,         # Core life values alignment
            "personality": 0.15,    # Personality trait compatibility  
            "communication": 0.20,  # Communication style match
            "demographic": 0.10,    # Age, location, etc.
            "emotional": 0.05       # Emotional intelligence/resonance
        }
        
        # Threshold levels
        self.thresholds = {
            "soulmate": 90.0,
            "high": 75.0,
            "medium": 60.0,
            "low": 40.0
        }
        
        # Value keywords for semantic matching
        self.value_keywords = self._initialize_value_keywords()
        
        # Personality trait mappings
        self.personality_traits = self._initialize_personality_traits()
        
        logger.info("Soul Compatibility Service initialized")
    
    def calculate_compatibility(self, user1: User, user2: User, db: Session) -> CompatibilityScore:
        """
        Calculate comprehensive compatibility between two users
        """
        try:
            # Individual component scores
            interests_score = self._calculate_interests_compatibility(user1, user2)
            values_score = self._calculate_values_compatibility(user1, user2)
            personality_score = self._calculate_personality_compatibility(user1, user2)
            communication_score = self._calculate_communication_compatibility(user1, user2)
            demographic_score = self._calculate_demographic_compatibility(user1, user2)
            emotional_score = self._calculate_emotional_resonance(user1, user2)
            
            # Weighted total score
            total_score = (
                interests_score * self.weights["interests"] +
                values_score * self.weights["values"] +
                personality_score * self.weights["personality"] +
                communication_score * self.weights["communication"] +
                demographic_score * self.weights["demographic"] +
                emotional_score * self.weights["emotional"]
            )
            
            # Calculate confidence based on data completeness
            confidence = self._calculate_confidence(user1, user2)
            
            # Determine match quality and energy level
            match_quality, energy_level = self._determine_match_quality(total_score)
            
            # Generate insights
            strengths = self._identify_strengths(user1, user2, {
                "interests": interests_score,
                "values": values_score,
                "personality": personality_score,
                "communication": communication_score,
                "demographic": demographic_score,
                "emotional": emotional_score
            })
            
            growth_areas = self._identify_growth_areas(user1, user2, {
                "interests": interests_score,
                "values": values_score,
                "personality": personality_score,
                "communication": communication_score,
                "demographic": demographic_score,
                "emotional": emotional_score
            })
            
            compatibility_summary = self._generate_summary(total_score, strengths, growth_areas)
            
            return CompatibilityScore(
                total_score=round(total_score, 1),
                confidence=round(confidence, 1),
                interests_score=round(interests_score, 1),
                values_score=round(values_score, 1),
                personality_score=round(personality_score, 1),
                communication_score=round(communication_score, 1),
                demographic_score=round(demographic_score, 1),
                emotional_resonance=round(emotional_score, 1),
                match_quality=match_quality,
                energy_level=energy_level,
                strengths=strengths,
                growth_areas=growth_areas,
                compatibility_summary=compatibility_summary
            )
            
        except Exception as e:
            logger.error(f"Error calculating compatibility: {str(e)}")
            # Return default score on error
            return self._default_compatibility_score()
    
    def _calculate_interests_compatibility(self, user1: User, user2: User) -> float:
        """Calculate compatibility based on shared interests using Jaccard similarity"""
        try:
            interests1 = set(user1.interests or [])
            interests2 = set(user2.interests or [])
            
            if not interests1 and not interests2:
                return 70.0  # Neutral score when no data
            
            if not interests1 or not interests2:
                return 50.0  # Lower score when one user has no interests
            
            # Jaccard similarity coefficient
            intersection = len(interests1.intersection(interests2))
            union = len(interests1.union(interests2))
            
            if union == 0:
                return 70.0
            
            jaccard_score = intersection / union
            
            # Apply bonus for high overlap
            bonus = 0.0
            if intersection >= 3:
                bonus = 10.0
            elif intersection >= 5:
                bonus = 20.0
            
            return min(100.0, (jaccard_score * 80) + 20 + bonus)
            
        except Exception as e:
            logger.error(f"Error calculating interests compatibility: {str(e)}")
            return 50.0
    
    def _calculate_values_compatibility(self, user1: User, user2: User) -> float:
        """Calculate values alignment using semantic keyword matching"""
        try:
            values1 = user1.core_values or {}
            values2 = user2.core_values or {}
            
            if not values1 and not values2:
                return 70.0
            
            if not values1 or not values2:
                return 45.0
            
            # Compare each value category
            category_scores = []
            
            for category in self.value_keywords.keys():
                score1 = self._extract_value_signals(values1.get(category, ""), category)
                score2 = self._extract_value_signals(values2.get(category, ""), category)
                
                if score1 and score2:
                    # Calculate similarity between value vectors
                    similarity = self._calculate_vector_similarity(score1, score2)
                    category_scores.append(similarity)
            
            if not category_scores:
                return 60.0
            
            # Weight by importance and calculate average
            avg_score = sum(category_scores) / len(category_scores)
            
            # Values are critical - amplify the difference
            if avg_score > 0.8:
                return min(100.0, avg_score * 95 + 10)
            elif avg_score > 0.6:
                return avg_score * 85 + 5
            else:
                return avg_score * 70
                
        except Exception as e:
            logger.error(f"Error calculating values compatibility: {str(e)}")
            return 50.0
    
    def _calculate_personality_compatibility(self, user1: User, user2: User) -> float:
        """Calculate personality trait compatibility"""
        try:
            traits1 = user1.personality_traits or {}
            traits2 = user2.personality_traits or {}
            
            if not traits1 and not traits2:
                return 70.0
            
            if not traits1 or not traits2:
                return 55.0
            
            compatibility_scores = []
            
            # Analyze complementary vs similar traits
            for trait_category, trait_data in self.personality_traits.items():
                score1 = traits1.get(trait_category, 50)  # Default middle score
                score2 = traits2.get(trait_category, 50)
                
                if trait_data["type"] == "complementary":
                    # Opposites can attract (but not too extreme)
                    diff = abs(score1 - score2)
                    if 20 <= diff <= 40:  # Sweet spot for complementary traits
                        compatibility_scores.append(85.0)
                    elif diff < 20:
                        compatibility_scores.append(70.0)  # Too similar
                    else:
                        compatibility_scores.append(50.0)  # Too different
                else:  # Similar traits preferred
                    diff = abs(score1 - score2)
                    if diff <= 15:
                        compatibility_scores.append(90.0)
                    elif diff <= 30:
                        compatibility_scores.append(75.0)
                    elif diff <= 45:
                        compatibility_scores.append(60.0)
                    else:
                        compatibility_scores.append(40.0)
            
            return sum(compatibility_scores) / len(compatibility_scores) if compatibility_scores else 60.0
            
        except Exception as e:
            logger.error(f"Error calculating personality compatibility: {str(e)}")
            return 50.0
    
    def _calculate_communication_compatibility(self, user1: User, user2: User) -> float:
        """Calculate communication style compatibility"""
        try:
            comm1 = user1.communication_style or {}
            comm2 = user2.communication_style or {}
            
            if not comm1 and not comm2:
                return 70.0
            
            if not comm1 or not comm2:
                return 55.0
            
            compatibility_factors = []
            
            # Preferred communication frequency
            freq1 = comm1.get("frequency", "moderate")
            freq2 = comm2.get("frequency", "moderate")
            freq_score = self._compare_communication_frequency(freq1, freq2)
            compatibility_factors.append(freq_score)
            
            # Communication depth preference
            depth1 = comm1.get("depth", "mixed")
            depth2 = comm2.get("depth", "mixed")
            depth_score = self._compare_communication_depth(depth1, depth2)
            compatibility_factors.append(depth_score)
            
            # Response time expectations
            response1 = comm1.get("response_time", "flexible")
            response2 = comm2.get("response_time", "flexible")
            response_score = self._compare_response_expectations(response1, response2)
            compatibility_factors.append(response_score)
            
            # Conflict resolution style
            conflict1 = comm1.get("conflict_style", "collaborative")
            conflict2 = comm2.get("conflict_style", "collaborative")
            conflict_score = self._compare_conflict_styles(conflict1, conflict2)
            compatibility_factors.append(conflict_score)
            
            return sum(compatibility_factors) / len(compatibility_factors)
            
        except Exception as e:
            logger.error(f"Error calculating communication compatibility: {str(e)}")
            return 50.0
    
    def _calculate_demographic_compatibility(self, user1: User, user2: User) -> float:
        """Calculate demographic compatibility (age, location, etc.)"""
        try:
            scores = []
            
            # Age compatibility
            age_score = self._calculate_age_compatibility(user1, user2)
            scores.append(age_score)
            
            # Location compatibility
            location_score = self._calculate_location_compatibility(user1, user2)
            scores.append(location_score * 0.7)  # Lower weight for location
            
            # Lifestyle compatibility (if available)
            lifestyle_score = self._calculate_lifestyle_compatibility(user1, user2)
            scores.append(lifestyle_score * 0.5)
            
            return sum(scores) / len(scores) if scores else 60.0
            
        except Exception as e:
            logger.error(f"Error calculating demographic compatibility: {str(e)}")
            return 50.0
    
    def _calculate_emotional_resonance(self, user1: User, user2: User) -> float:
        """Calculate emotional intelligence and resonance compatibility"""
        try:
            responses1 = user1.emotional_responses or {}
            responses2 = user2.emotional_responses or {}
            
            if not responses1 and not responses2:
                return 70.0
            
            if not responses1 or not responses2:
                return 60.0
            
            # Analyze emotional depth and maturity indicators
            emotional_factors = []
            
            # Emotional self-awareness
            awareness_score = self._compare_emotional_awareness(responses1, responses2)
            emotional_factors.append(awareness_score)
            
            # Empathy indicators
            empathy_score = self._compare_empathy_levels(responses1, responses2)
            emotional_factors.append(empathy_score)
            
            # Emotional expression style
            expression_score = self._compare_emotional_expression(responses1, responses2)
            emotional_factors.append(expression_score)
            
            return sum(emotional_factors) / len(emotional_factors) if emotional_factors else 65.0
            
        except Exception as e:
            logger.error(f"Error calculating emotional resonance: {str(e)}")
            return 50.0
    
    def _calculate_age_compatibility(self, user1: User, user2: User) -> float:
        """Calculate age compatibility with bell curve optimization"""
        try:
            if not user1.date_of_birth or not user2.date_of_birth:
                return 60.0
            
            # Parse birth dates
            birth1 = datetime.strptime(user1.date_of_birth, "%Y-%m-%d").date()
            birth2 = datetime.strptime(user2.date_of_birth, "%Y-%m-%d").date()
            
            # Calculate ages
            today = date.today()
            age1 = today.year - birth1.year - ((today.month, today.day) < (birth1.month, birth1.day))
            age2 = today.year - birth2.year - ((today.month, today.day) < (birth2.month, birth2.day))
            
            age_diff = abs(age1 - age2)
            
            # Bell curve scoring - optimal within reasonable range
            if age_diff == 0:
                return 95.0
            elif age_diff <= 2:
                return 90.0
            elif age_diff <= 5:
                return 85.0
            elif age_diff <= 8:
                return 75.0
            elif age_diff <= 12:
                return 65.0
            elif age_diff <= 15:
                return 50.0
            else:
                return 30.0
                
        except Exception as e:
            logger.error(f"Error calculating age compatibility: {str(e)}")
            return 60.0
    
    def _calculate_location_compatibility(self, user1: User, user2: User) -> float:
        """Calculate location compatibility"""
        try:
            if not user1.location or not user2.location:
                return 60.0
            
            loc1 = user1.location.lower().strip()
            loc2 = user2.location.lower().strip()
            
            if loc1 == loc2:
                return 90.0
            
            # Simple city/state matching (could be enhanced with geo-distance)
            loc1_parts = set(loc1.replace(",", " ").split())
            loc2_parts = set(loc2.replace(",", " ").split())
            
            common_parts = loc1_parts.intersection(loc2_parts)
            
            if common_parts:
                return 75.0  # Same city/state/region
            else:
                return 50.0  # Different locations
                
        except Exception as e:
            logger.error(f"Error calculating location compatibility: {str(e)}")
            return 60.0
    
    def _calculate_lifestyle_compatibility(self, user1: User, user2: User) -> float:
        """Calculate lifestyle compatibility based on dietary preferences, etc."""
        try:
            diet1 = set(user1.dietary_preferences or [])
            diet2 = set(user2.dietary_preferences or [])
            
            if not diet1 and not diet2:
                return 70.0
            
            if diet1 == diet2:
                return 85.0
            
            # Check for major incompatibilities
            incompatible_pairs = [
                ("vegan", "carnivore"),
                ("halal", "non-halal"),
                ("kosher", "non-kosher")
            ]
            
            for pref1, pref2 in incompatible_pairs:
                if (pref1 in diet1 and pref2 in diet2) or (pref2 in diet1 and pref1 in diet2):
                    return 30.0
            
            # Calculate overlap
            if diet1 and diet2:
                overlap = len(diet1.intersection(diet2)) / len(diet1.union(diet2))
                return 50 + (overlap * 35)
            
            return 60.0
            
        except Exception as e:
            logger.error(f"Error calculating lifestyle compatibility: {str(e)}")
            return 60.0
    
    def _calculate_confidence(self, user1: User, user2: User) -> float:
        """Calculate confidence score based on data completeness"""
        try:
            factors = []
            
            # Profile completeness
            user1_completeness = self._calculate_profile_completeness(user1)
            user2_completeness = self._calculate_profile_completeness(user2)
            factors.extend([user1_completeness, user2_completeness])
            
            # Data quality
            data_quality = self._assess_data_quality(user1, user2)
            factors.append(data_quality)
            
            return sum(factors) / len(factors) if factors else 50.0
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {str(e)}")
            return 50.0
    
    def _calculate_profile_completeness(self, user: User) -> float:
        """Calculate how complete a user's profile is"""
        completeness_factors = []
        
        # Basic info
        if user.first_name and user.last_name:
            completeness_factors.append(1.0)
        else:
            completeness_factors.append(0.0)
        
        # Demographics
        if user.date_of_birth and user.gender and user.location:
            completeness_factors.append(1.0)
        else:
            completeness_factors.append(0.5)
        
        # Interests
        if user.interests and len(user.interests) >= 3:
            completeness_factors.append(1.0)
        elif user.interests:
            completeness_factors.append(0.7)
        else:
            completeness_factors.append(0.0)
        
        # Values and emotional data
        if user.core_values and user.emotional_responses:
            completeness_factors.append(1.0)
        elif user.core_values or user.emotional_responses:
            completeness_factors.append(0.6)
        else:
            completeness_factors.append(0.0)
        
        # Personality traits
        if user.personality_traits:
            completeness_factors.append(1.0)
        else:
            completeness_factors.append(0.0)
        
        return (sum(completeness_factors) / len(completeness_factors)) * 100
    
    def _assess_data_quality(self, user1: User, user2: User) -> float:
        """Assess the quality of available data for matching"""
        quality_score = 80.0  # Base quality
        
        # Check for rich text responses
        for user in [user1, user2]:
            if user.emotional_responses:
                for response in user.emotional_responses.values():
                    if isinstance(response, str) and len(response) > 50:
                        quality_score += 5.0
        
        # Check for detailed interests
        for user in [user1, user2]:
            if user.interests and len(user.interests) >= 5:
                quality_score += 5.0
        
        return min(100.0, quality_score)
    
    def _determine_match_quality(self, total_score: float) -> Tuple[str, ConnectionEnergyLevel]:
        """Determine match quality label and energy level"""
        if total_score >= self.thresholds["soulmate"]:
            return "soulmate", ConnectionEnergyLevel.SOULMATE
        elif total_score >= self.thresholds["high"]:
            return "high", ConnectionEnergyLevel.HIGH
        elif total_score >= self.thresholds["medium"]:
            return "medium", ConnectionEnergyLevel.MEDIUM
        else:
            return "low", ConnectionEnergyLevel.LOW
    
    # Helper methods for detailed calculations
    
    def _extract_value_signals(self, text: str, category: str) -> Dict[str, float]:
        """Extract value signals from text using keyword matching"""
        if not text or not isinstance(text, str):
            return {}
        
        text_lower = text.lower()
        signals = {}
        
        category_keywords = self.value_keywords.get(category, {})
        
        for value_type, keywords in category_keywords.items():
            score = 0.0
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    score += 1.0
            
            if score > 0:
                signals[value_type] = min(1.0, score / len(keywords))
        
        return signals
    
    def _calculate_vector_similarity(self, vector1: Dict[str, float], vector2: Dict[str, float]) -> float:
        """Calculate cosine similarity between two value vectors"""
        if not vector1 or not vector2:
            return 0.0
        
        # Get all keys
        all_keys = set(vector1.keys()) | set(vector2.keys())
        
        if not all_keys:
            return 0.0
        
        # Create vectors
        v1 = [vector1.get(key, 0.0) for key in all_keys]
        v2 = [vector2.get(key, 0.0) for key in all_keys]
        
        # Calculate cosine similarity
        dot_product = sum(a * b for a, b in zip(v1, v2))
        magnitude1 = math.sqrt(sum(a * a for a in v1))
        magnitude2 = math.sqrt(sum(b * b for b in v2))
        
        if magnitude1 == 0.0 or magnitude2 == 0.0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def _initialize_value_keywords(self) -> Dict[str, Dict[str, List[str]]]:
        """Initialize value keyword mappings for semantic matching"""
        return {
            "relationship_values": {
                "commitment": ["loyal", "faithful", "dedicated", "devoted", "commitment", "exclusive", "monogamous"],
                "growth": ["learn", "improve", "develop", "evolve", "grow", "progress", "better"],
                "adventure": ["explore", "travel", "new", "experience", "adventure", "discover", "journey"],
                "stability": ["secure", "steady", "reliable", "consistent", "stable", "grounded", "dependable"],
                "intimacy": ["close", "intimate", "deep", "connection", "bond", "vulnerable", "trust"],
                "independence": ["space", "freedom", "individual", "autonomous", "independent", "separate"],
                "family": ["family", "children", "kids", "legacy", "tradition", "home", "nest"],
                "career": ["ambition", "success", "achievement", "professional", "career", "work", "goals"]
            },
            "connection_style": {
                "deep_talks": ["meaningful", "deep", "philosophy", "soul", "profound", "intellectual", "thoughtful"],
                "shared_activities": ["together", "activities", "hobbies", "fun", "adventures", "experiences", "doing"],
                "quality_time": ["present", "attention", "focus", "listen", "time", "moments", "availability"],
                "physical_affection": ["touch", "affection", "close", "intimate", "physical", "cuddle", "embrace"],
                "emotional_support": ["support", "understanding", "empathy", "comfort", "encouragement", "there"],
                "humor": ["laugh", "funny", "humor", "playful", "joy", "lighthearted", "wit"]
            },
            "life_philosophy": {
                "optimism": ["positive", "optimistic", "hopeful", "bright", "upbeat", "cheerful", "happy"],
                "mindfulness": ["mindful", "present", "awareness", "meditation", "conscious", "zen", "peace"],
                "authenticity": ["authentic", "genuine", "real", "honest", "true", "sincere", "original"],
                "compassion": ["kind", "compassionate", "caring", "empathy", "help", "service", "giving"],
                "achievement": ["success", "accomplish", "achieve", "excel", "strive", "ambition", "goals"],
                "balance": ["balance", "harmony", "equilibrium", "moderation", "peaceful", "centered"]
            }
        }
    
    def _initialize_personality_traits(self) -> Dict[str, Dict[str, any]]:
        """Initialize personality trait compatibility rules"""
        return {
            "extroversion": {"type": "complementary", "weight": 1.0},
            "openness": {"type": "similar", "weight": 1.2},
            "conscientiousness": {"type": "similar", "weight": 1.0},
            "agreeableness": {"type": "similar", "weight": 1.1},
            "emotional_stability": {"type": "similar", "weight": 0.9},
            "adventurousness": {"type": "complementary", "weight": 0.8},
            "analytical": {"type": "complementary", "weight": 0.7}
        }
    
    def _compare_communication_frequency(self, freq1: str, freq2: str) -> float:
        """Compare communication frequency preferences"""
        freq_scores = {"low": 1, "moderate": 2, "high": 3, "very_high": 4}
        
        score1 = freq_scores.get(freq1, 2)
        score2 = freq_scores.get(freq2, 2)
        
        diff = abs(score1 - score2)
        
        if diff == 0:
            return 90.0
        elif diff == 1:
            return 75.0
        elif diff == 2:
            return 60.0
        else:
            return 45.0
    
    def _compare_communication_depth(self, depth1: str, depth2: str) -> float:
        """Compare communication depth preferences"""
        compatibility_matrix = {
            ("surface", "surface"): 70.0,
            ("surface", "mixed"): 60.0,
            ("surface", "deep"): 40.0,
            ("mixed", "mixed"): 85.0,
            ("mixed", "deep"): 75.0,
            ("deep", "deep"): 90.0
        }
        
        key = tuple(sorted([depth1, depth2]))
        return compatibility_matrix.get(key, 60.0)
    
    def _compare_response_expectations(self, response1: str, response2: str) -> float:
        """Compare response time expectations"""
        response_scores = {"immediate": 4, "quick": 3, "moderate": 2, "flexible": 1}
        
        score1 = response_scores.get(response1, 2)
        score2 = response_scores.get(response2, 2)
        
        diff = abs(score1 - score2)
        
        if diff == 0:
            return 85.0
        elif diff == 1:
            return 70.0
        elif diff == 2:
            return 55.0
        else:
            return 40.0
    
    def _compare_conflict_styles(self, style1: str, style2: str) -> float:
        """Compare conflict resolution styles"""
        compatible_styles = {
            "collaborative": ["collaborative", "compromise"],
            "compromise": ["collaborative", "compromise", "accommodating"],
            "accommodating": ["collaborative", "compromise", "accommodating"],
            "direct": ["direct", "collaborative"],
            "avoidant": ["accommodating", "avoidant"]
        }
        
        if style2 in compatible_styles.get(style1, []):
            return 80.0
        elif style1 == style2:
            return 85.0
        else:
            return 50.0
    
    def _compare_emotional_awareness(self, responses1: Dict, responses2: Dict) -> float:
        """Compare emotional self-awareness levels"""
        # Look for indicators of emotional intelligence in responses
        awareness_indicators = [
            "feel", "emotion", "aware", "understand", "recognize",
            "process", "handle", "cope", "manage", "express"
        ]
        
        score1 = self._count_indicators(responses1, awareness_indicators)
        score2 = self._count_indicators(responses2, awareness_indicators)
        
        # Both high awareness
        if score1 >= 3 and score2 >= 3:
            return 85.0
        # One high, one moderate
        elif (score1 >= 3 and score2 >= 2) or (score2 >= 3 and score1 >= 2):
            return 70.0
        # Both moderate
        elif score1 >= 2 and score2 >= 2:
            return 75.0
        else:
            return 60.0
    
    def _compare_empathy_levels(self, responses1: Dict, responses2: Dict) -> float:
        """Compare empathy and consideration levels"""
        empathy_indicators = [
            "understand", "others", "perspective", "feelings", "empathy",
            "care", "support", "help", "listen", "compassion"
        ]
        
        score1 = self._count_indicators(responses1, empathy_indicators)
        score2 = self._count_indicators(responses2, empathy_indicators)
        
        if score1 >= 2 and score2 >= 2:
            return 80.0
        elif score1 >= 1 and score2 >= 1:
            return 70.0
        else:
            return 55.0
    
    def _compare_emotional_expression(self, responses1: Dict, responses2: Dict) -> float:
        """Compare emotional expression styles"""
        # This would be more sophisticated in practice
        # For now, return a neutral score
        return 65.0
    
    def _count_indicators(self, responses: Dict, indicators: List[str]) -> int:
        """Count occurrence of indicator words in responses"""
        count = 0
        for response in responses.values():
            if isinstance(response, str):
                response_lower = response.lower()
                for indicator in indicators:
                    if indicator in response_lower:
                        count += 1
        return count
    
    def _identify_strengths(self, user1: User, user2: User, scores: Dict[str, float]) -> List[str]:
        """Identify relationship strengths based on high scores"""
        strengths = []
        
        if scores["values"] >= 80:
            strengths.append("Strong shared values and life philosophy")
        if scores["interests"] >= 75:
            strengths.append("Many common interests and hobbies")
        if scores["communication"] >= 80:
            strengths.append("Compatible communication styles")
        if scores["personality"] >= 75:
            strengths.append("Complementary personality traits")
        if scores["emotional"] >= 70:
            strengths.append("Good emotional compatibility")
        if scores["demographic"] >= 70:
            strengths.append("Well-matched life circumstances")
        
        return strengths[:3]  # Top 3 strengths
    
    def _identify_growth_areas(self, user1: User, user2: User, scores: Dict[str, float]) -> List[str]:
        """Identify areas that may need attention in the relationship"""
        growth_areas = []
        
        if scores["communication"] < 60:
            growth_areas.append("May benefit from discussing communication preferences")
        if scores["interests"] < 50:
            growth_areas.append("Could explore new shared activities together")
        if scores["values"] < 60:
            growth_areas.append("Important to understand each other's core values")
        if scores["personality"] < 50:
            growth_areas.append("Personality differences may require understanding")
        
        return growth_areas[:2]  # Top 2 growth areas
    
    def _generate_summary(self, total_score: float, strengths: List[str], growth_areas: List[str]) -> str:
        """Generate a human-readable compatibility summary"""
        if total_score >= 90:
            base = "Exceptional compatibility with strong potential for a deep, lasting connection."
        elif total_score >= 75:
            base = "High compatibility with many shared values and complementary traits."
        elif total_score >= 60:
            base = "Good compatibility foundation with room for mutual growth."
        else:
            base = "Some compatibility challenges that could be navigated with understanding."
        
        if strengths:
            base += f" Key strengths include: {', '.join(strengths[:2]).lower()}."
        
        if growth_areas:
            base += f" Areas for attention: {', '.join(growth_areas[:1]).lower()}."
        
        return base
    
    def _default_compatibility_score(self) -> CompatibilityScore:
        """Return default compatibility score when calculation fails"""
        return CompatibilityScore(
            total_score=60.0,
            confidence=30.0,
            interests_score=50.0,
            values_score=50.0,
            personality_score=50.0,
            communication_score=50.0,
            demographic_score=50.0,
            emotional_resonance=50.0,
            match_quality="medium",
            energy_level=ConnectionEnergyLevel.MEDIUM,
            strengths=["Potential for connection"],
            growth_areas=["Getting to know each other better"],
            compatibility_summary="Compatibility assessment needs more profile data for accuracy."
        )
    
    async def track_compatibility_accuracy(self, connection_id: int, predicted_score: CompatibilityScore, 
                                         db: Session, algorithm_version: str = "1.0"):
        """Track compatibility prediction for later accuracy analysis"""
        try:
            tracking = CompatibilityAccuracyTracking(
                connection_id=connection_id,
                predicted_compatibility_score=predicted_score.total_score,
                prediction_confidence=predicted_score.confidence,
                algorithm_version=algorithm_version,
                prediction_made_at=datetime.utcnow()
            )
            
            db.add(tracking)
            db.commit()
            
        except Exception as e:
            logger.error(f"Error tracking compatibility accuracy: {str(e)}")
            db.rollback()


# Global service instance
compatibility_service = SoulCompatibilityService()