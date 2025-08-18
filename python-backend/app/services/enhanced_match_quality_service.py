"""
Enhanced Match Quality Service
Comprehensive match quality assessment combining soul compatibility and emotional depth
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.soul_connection import SoulConnection, ConnectionEnergyLevel
from app.services.soul_compatibility_service import compatibility_service, CompatibilityScore
from app.services.advanced_soul_matching import advanced_matching_service, AdvancedCompatibilityScore
from app.services.emotional_depth_service import emotional_depth_service, DepthCompatibilityScore

logger = logging.getLogger(__name__)


class MatchQualityTier(Enum):
    """Enhanced match quality tiers"""
    TRANSCENDENT = "transcendent"       # 95-100: Exceptional soulmate potential
    EXCEPTIONAL = "exceptional"        # 90-94: Outstanding compatibility
    HIGH = "high"                     # 80-89: Strong relationship potential
    GOOD = "good"                     # 70-79: Good foundation for connection
    MODERATE = "moderate"             # 60-69: Moderate compatibility
    EXPLORATORY = "exploratory"       # 50-59: Worth exploring with patience
    LIMITED = "limited"               # 40-49: Limited compatibility
    INCOMPATIBLE = "incompatible"     # 0-39: Significant challenges


class ConnectionPrediction(Enum):
    """Relationship development predictions"""
    SOULMATE_POTENTIAL = "soulmate_potential"
    TRANSFORMATIONAL = "transformational"  
    DYNAMIC_GROWTH = "dynamic_growth"
    STABLE_COMPANIONSHIP = "stable_companionship"
    EMOTIONAL_JOURNEY = "emotional_journey"
    COMPLEMENTARY_BALANCE = "complementary_balance"
    EXPLORATORY_CONNECTION = "exploratory_connection"
    FRIENDSHIP_FOUNDATION = "friendship_foundation"


@dataclass
class EnhancedMatchQuality:
    """Comprehensive match quality assessment"""
    # Overall Assessment
    total_compatibility: float  # 0-100 composite score
    match_quality_tier: MatchQualityTier
    connection_prediction: ConnectionPrediction
    
    # Component Scores
    soul_compatibility: CompatibilityScore
    advanced_compatibility: AdvancedCompatibilityScore
    emotional_depth_compatibility: DepthCompatibilityScore
    
    # Enhanced Insights
    relationship_timeline: str
    connection_strengths: List[str]
    growth_opportunities: List[str]
    potential_challenges: List[str]
    recommended_approach: str
    first_date_suggestion: str
    conversation_starters: List[str]
    
    # Confidence and Metadata
    assessment_confidence: float
    algorithm_version: str
    analysis_timestamp: datetime


class EnhancedMatchQualityService:
    """Service for comprehensive match quality assessment"""
    
    def __init__(self):
        # Algorithm weights for composite scoring
        self.component_weights = {
            "soul_compatibility": 0.35,      # Core soul connection metrics
            "advanced_compatibility": 0.35,  # Advanced algorithmic analysis
            "emotional_depth": 0.30         # Emotional depth compatibility
        }
        
        # Quality tier thresholds
        self.quality_thresholds = {
            MatchQualityTier.TRANSCENDENT: 95.0,
            MatchQualityTier.EXCEPTIONAL: 90.0,
            MatchQualityTier.HIGH: 80.0,
            MatchQualityTier.GOOD: 70.0,
            MatchQualityTier.MODERATE: 60.0,
            MatchQualityTier.EXPLORATORY: 50.0,
            MatchQualityTier.LIMITED: 40.0,
        }
        
        logger.info("Enhanced Match Quality Service initialized")
    
    def assess_comprehensive_match_quality(self, user1: User, user2: User, 
                                         db: Session) -> EnhancedMatchQuality:
        """
        Perform comprehensive match quality assessment combining all algorithms
        """
        try:
            # Run all compatibility analyses
            soul_compatibility = compatibility_service.calculate_compatibility(user1, user2, db)
            advanced_compatibility = advanced_matching_service.calculate_advanced_compatibility(
                user1, user2, db
            )
            depth_compatibility = emotional_depth_service.calculate_depth_compatibility(
                user1, user2, db
            )
            
            # Calculate composite compatibility score
            total_compatibility = self._calculate_composite_score(
                soul_compatibility, advanced_compatibility, depth_compatibility
            )
            
            # Determine match quality tier
            match_quality_tier = self._determine_match_quality_tier(total_compatibility)
            
            # Predict connection type
            connection_prediction = self._predict_connection_type(
                total_compatibility, soul_compatibility, advanced_compatibility, depth_compatibility
            )
            
            # Generate enhanced insights
            relationship_timeline = self._generate_relationship_timeline(
                total_compatibility, advanced_compatibility, depth_compatibility
            )
            
            connection_strengths = self._identify_connection_strengths(
                soul_compatibility, advanced_compatibility, depth_compatibility
            )
            
            growth_opportunities = self._identify_growth_opportunities(
                soul_compatibility, advanced_compatibility, depth_compatibility
            )
            
            potential_challenges = self._identify_potential_challenges(
                soul_compatibility, advanced_compatibility, depth_compatibility
            )
            
            recommended_approach = self._recommend_connection_approach(
                match_quality_tier, connection_prediction, depth_compatibility
            )
            
            first_date_suggestion = self._suggest_optimal_first_date(
                soul_compatibility, advanced_compatibility, depth_compatibility
            )
            
            conversation_starters = self._generate_enhanced_conversation_starters(
                user1, user2, connection_strengths
            )
            
            # Calculate assessment confidence
            assessment_confidence = self._calculate_assessment_confidence(
                soul_compatibility, advanced_compatibility, depth_compatibility
            )
            
            return EnhancedMatchQuality(
                total_compatibility=round(total_compatibility, 1),
                match_quality_tier=match_quality_tier,
                connection_prediction=connection_prediction,
                soul_compatibility=soul_compatibility,
                advanced_compatibility=advanced_compatibility,
                emotional_depth_compatibility=depth_compatibility,
                relationship_timeline=relationship_timeline,
                connection_strengths=connection_strengths,
                growth_opportunities=growth_opportunities,
                potential_challenges=potential_challenges,
                recommended_approach=recommended_approach,
                first_date_suggestion=first_date_suggestion,
                conversation_starters=conversation_starters,
                assessment_confidence=round(assessment_confidence, 1),
                algorithm_version="enhanced_v1.0",
                analysis_timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error in comprehensive match quality assessment: {str(e)}")
            return self._default_enhanced_match_quality()
    
    def _calculate_composite_score(self, soul_compat: CompatibilityScore,
                                 advanced_compat: AdvancedCompatibilityScore,
                                 depth_compat: DepthCompatibilityScore) -> float:
        """Calculate weighted composite compatibility score"""
        try:
            soul_score = soul_compat.total_score
            advanced_score = advanced_compat.total_score
            depth_score = depth_compat.compatibility_score
            
            composite = (
                soul_score * self.component_weights["soul_compatibility"] +
                advanced_score * self.component_weights["advanced_compatibility"] +
                depth_score * self.component_weights["emotional_depth"]
            )
            
            return min(100.0, max(0.0, composite))
            
        except Exception as e:
            logger.error(f"Error calculating composite score: {str(e)}")
            return 60.0
    
    def _determine_match_quality_tier(self, total_score: float) -> MatchQualityTier:
        """Determine match quality tier based on composite score"""
        for tier, threshold in self.quality_thresholds.items():
            if total_score >= threshold:
                return tier
        return MatchQualityTier.INCOMPATIBLE
    
    def _predict_connection_type(self, total_score: float, soul_compat: CompatibilityScore,
                               advanced_compat: AdvancedCompatibilityScore,
                               depth_compat: DepthCompatibilityScore) -> ConnectionPrediction:
        """Predict the type of connection based on compatibility analysis"""
        try:
            # Transcendent connections
            if (total_score >= 95 and 
                depth_compat.depth_harmony >= 90 and 
                advanced_compat.growth_potential >= 85):
                return ConnectionPrediction.SOULMATE_POTENTIAL
            
            # Transformational partnerships
            elif (total_score >= 88 and 
                  advanced_compat.growth_potential >= 80 and
                  depth_compat.vulnerability_match >= 75):
                return ConnectionPrediction.TRANSFORMATIONAL
            
            # Dynamic growth connections
            elif (total_score >= 80 and 
                  advanced_compat.growth_potential >= 70):
                return ConnectionPrediction.DYNAMIC_GROWTH
            
            # Stable companionships
            elif (total_score >= 75 and 
                  soul_compat.values_score >= 80 and
                  soul_compat.communication_score >= 75):
                return ConnectionPrediction.STABLE_COMPANIONSHIP
            
            # Emotional journeys
            elif (total_score >= 70 and 
                  depth_compat.compatibility_score >= 75):
                return ConnectionPrediction.EMOTIONAL_JOURNEY
            
            # Complementary balance
            elif (total_score >= 65 and 
                  soul_compat.personality_score >= 70):
                return ConnectionPrediction.COMPLEMENTARY_BALANCE
            
            # Exploratory connections
            elif total_score >= 55:
                return ConnectionPrediction.EXPLORATORY_CONNECTION
            
            else:
                return ConnectionPrediction.FRIENDSHIP_FOUNDATION
                
        except Exception as e:
            logger.error(f"Error predicting connection type: {str(e)}")
            return ConnectionPrediction.EXPLORATORY_CONNECTION
    
    def _generate_relationship_timeline(self, total_score: float, 
                                      advanced_compat: AdvancedCompatibilityScore,
                                      depth_compat: DepthCompatibilityScore) -> str:
        """Generate predicted relationship development timeline"""
        try:
            growth_potential = advanced_compat.growth_potential
            depth_harmony = depth_compat.depth_harmony
            
            if total_score >= 90 and growth_potential >= 85 and depth_harmony >= 80:
                return "Rapid deep connection within 2-4 weeks, profound bond by 3 months"
            elif total_score >= 80 and growth_potential >= 70:
                return "Strong connection within 4-6 weeks, deep understanding by 6 months"
            elif total_score >= 70:
                return "Steady connection building over 2-3 months, meaningful bond by 9 months"
            elif total_score >= 60:
                return "Gradual connection over 3-6 months, stable relationship potential by 12 months"
            else:
                return "Slow development requiring patience, meaningful connection possible over 12+ months"
                
        except Exception as e:
            logger.error(f"Error generating relationship timeline: {str(e)}")
            return "Connection timeline depends on mutual engagement and openness"
    
    def _identify_connection_strengths(self, soul_compat: CompatibilityScore,
                                     advanced_compat: AdvancedCompatibilityScore,
                                     depth_compat: DepthCompatibilityScore) -> List[str]:
        """Identify key connection strengths"""
        strengths = []
        
        try:
            # Soul compatibility strengths
            if soul_compat.values_score >= 80:
                strengths.append("Strong alignment in core values and life philosophy")
            if soul_compat.interests_score >= 75:
                strengths.append("Rich shared interests and natural conversation topics")
            if soul_compat.communication_score >= 80:
                strengths.append("Excellent communication compatibility and understanding")
            
            # Advanced compatibility strengths
            if advanced_compat.emotional_intelligence_compatibility >= 80:
                strengths.append("High emotional intelligence alignment")
            if advanced_compat.growth_potential >= 80:
                strengths.append("Exceptional potential for mutual growth and development")
            if advanced_compat.temporal_compatibility >= 75:
                strengths.append("Compatible lifestyle rhythms and availability")
            
            # Emotional depth strengths
            if depth_compat.vulnerability_match >= 80:
                strengths.append("Comfortable mutual vulnerability and emotional openness")
            if depth_compat.depth_harmony >= 85:
                strengths.append("Harmonious emotional depth levels")
            if depth_compat.growth_alignment >= 80:
                strengths.append("Aligned personal development goals")
            
            # Ensure we have at least some strengths
            if not strengths:
                strengths.append("Potential for meaningful connection with mutual effort")
            
            return strengths[:5]  # Return top 5 strengths
            
        except Exception as e:
            logger.error(f"Error identifying connection strengths: {str(e)}")
            return ["Potential for connection with mutual understanding"]
    
    def _identify_growth_opportunities(self, soul_compat: CompatibilityScore,
                                     advanced_compat: AdvancedCompatibilityScore,
                                     depth_compat: DepthCompatibilityScore) -> List[str]:
        """Identify growth opportunities in the relationship"""
        opportunities = []
        
        try:
            if advanced_compat.growth_potential >= 70:
                opportunities.append("Strong potential for transformational personal growth together")
            
            if depth_compat.growth_alignment >= 65:
                opportunities.append("Mutual support for individual development and self-discovery")
            
            if soul_compat.communication_score >= 70:
                opportunities.append("Deep meaningful conversations that enhance understanding")
            
            if advanced_compat.emotional_intelligence_compatibility >= 65:
                opportunities.append("Development of enhanced emotional intelligence through connection")
            
            if depth_compat.vulnerability_match >= 60:
                opportunities.append("Safe space for authentic self-expression and vulnerability")
            
            # Default opportunities if none specific identified
            if not opportunities:
                opportunities.append("Learning and growing through each other's perspectives")
                opportunities.append("Building trust and deeper emotional connection over time")
            
            return opportunities[:4]  # Return top 4 opportunities
            
        except Exception as e:
            logger.error(f"Error identifying growth opportunities: {str(e)}")
            return ["Opportunity for mutual growth and understanding"]
    
    def _identify_potential_challenges(self, soul_compat: CompatibilityScore,
                                     advanced_compat: AdvancedCompatibilityScore,
                                     depth_compat: DepthCompatibilityScore) -> List[str]:
        """Identify potential relationship challenges"""
        challenges = []
        
        try:
            # Communication challenges
            if soul_compat.communication_score < 60:
                challenges.append("May need to work on communication styles and expectations")
            
            # Values differences
            if soul_compat.values_score < 60:
                challenges.append("Different core values may require understanding and compromise")
            
            # Emotional depth misalignment
            if depth_compat.depth_harmony < 60:
                challenges.append("Different emotional expression styles may need patience")
            
            # Vulnerability comfort differences
            if depth_compat.vulnerability_match < 50:
                challenges.append("Different comfort levels with emotional openness")
            
            # Interest alignment
            if soul_compat.interests_score < 40:
                challenges.append("Limited shared interests may require finding new common ground")
            
            # Personality differences
            if soul_compat.personality_score < 50:
                challenges.append("Personality differences may require mutual understanding")
            
            # If no specific challenges, provide general guidance
            if not challenges:
                challenges.append("Building trust and understanding through open communication")
            
            return challenges[:3]  # Return top 3 challenges
            
        except Exception as e:
            logger.error(f"Error identifying potential challenges: {str(e)}")
            return ["Normal relationship development requires patience and understanding"]
    
    def _recommend_connection_approach(self, quality_tier: MatchQualityTier,
                                     prediction: ConnectionPrediction,
                                     depth_compat: DepthCompatibilityScore) -> str:
        """Recommend optimal approach for connection"""
        try:
            if quality_tier in [MatchQualityTier.TRANSCENDENT, MatchQualityTier.EXCEPTIONAL]:
                return "Be authentic and open - this connection has exceptional potential"
            
            elif quality_tier == MatchQualityTier.HIGH:
                if prediction == ConnectionPrediction.DYNAMIC_GROWTH:
                    return "Embrace growth opportunities while building trust gradually"
                else:
                    return "Build connection through shared experiences and open communication"
            
            elif quality_tier == MatchQualityTier.GOOD:
                return "Take time to understand each other's perspectives and build trust"
            
            elif quality_tier == MatchQualityTier.MODERATE:
                if depth_compat.vulnerability_match >= 65:
                    return "Focus on emotional connection while respecting differences"
                else:
                    return "Build friendship foundation first, then explore deeper connection"
            
            else:
                return "Approach with patience and open-mindedness to discover compatibility"
                
        except Exception as e:
            logger.error(f"Error recommending connection approach: {str(e)}")
            return "Take time to get to know each other authentically"
    
    def _suggest_optimal_first_date(self, soul_compat: CompatibilityScore,
                                  advanced_compat: AdvancedCompatibilityScore,
                                  depth_compat: DepthCompatibilityScore) -> str:
        """Suggest optimal first date based on compatibility analysis"""
        try:
            # Use advanced compatibility first date suggestion as base
            base_suggestion = advanced_compat.recommended_first_date
            
            # Enhance based on emotional depth compatibility
            if depth_compat.depth_harmony >= 80:
                return f"{base_suggestion} - Your emotional depth compatibility suggests deep conversation will flow naturally"
            elif depth_compat.vulnerability_match >= 75:
                return f"{base_suggestion} - Create space for meaningful sharing and authentic connection"
            else:
                return f"{base_suggestion} - Focus on getting comfortable with each other first"
                
        except Exception as e:
            logger.error(f"Error suggesting optimal first date: {str(e)}")
            return "Coffee or walk in a comfortable setting to get to know each other"
    
    def _generate_enhanced_conversation_starters(self, user1: User, user2: User,
                                               strengths: List[str]) -> List[str]:
        """Generate enhanced conversation starters based on compatibility strengths"""
        starters = []
        
        try:
            # Add strength-based starters
            for strength in strengths[:2]:  # Use top 2 strengths
                if "values" in strength.lower():
                    starters.append("What values are most important to you in how you live your life?")
                elif "interests" in strength.lower():
                    starters.append("What's something you're passionate about that always lights you up?")
                elif "emotional" in strength.lower():
                    starters.append("How do you like to connect with people on a deeper level?")
                elif "growth" in strength.lower():
                    starters.append("What's something you're working on growing or improving in yourself?")
            
            # Add general high-quality starters
            starters.extend([
                "What's brought you the most joy recently?",
                "If you could learn anything new instantly, what would it be and why?",
                "What's something you believe that might surprise people?",
                "How do you like to recharge when you need to feel like yourself again?",
                "What's a moment recently when you felt most alive?"
            ])
            
            # Return top 5 unique starters
            return list(set(starters))[:5]
            
        except Exception as e:
            logger.error(f"Error generating conversation starters: {str(e)}")
            return [
                "What brings you the most joy in life?",
                "What's something you're passionate about?",
                "How do you like to spend your ideal weekend?"
            ]
    
    def _calculate_assessment_confidence(self, soul_compat: CompatibilityScore,
                                       advanced_compat: AdvancedCompatibilityScore,
                                       depth_compat: DepthCompatibilityScore) -> float:
        """Calculate confidence in the overall assessment"""
        try:
            confidences = [
                soul_compat.confidence,
                advanced_compat.confidence,
                depth_compat.user1_depth.confidence,
                depth_compat.user2_depth.confidence
            ]
            
            # Weight the confidences
            weights = [0.3, 0.3, 0.2, 0.2]
            weighted_confidence = sum(c * w for c, w in zip(confidences, weights))
            
            return min(100.0, max(30.0, weighted_confidence))
            
        except Exception as e:
            logger.error(f"Error calculating assessment confidence: {str(e)}")
            return 60.0
    
    def _default_enhanced_match_quality(self) -> EnhancedMatchQuality:
        """Return default enhanced match quality when analysis fails"""
        from app.services.soul_compatibility_service import SoulCompatibilityService
        from app.services.advanced_soul_matching import AdvancedSoulMatchingService  
        from app.services.emotional_depth_service import EmotionalDepthService
        
        # Create default component scores
        default_soul = compatibility_service._default_compatibility_score()
        default_advanced = advanced_matching_service._default_advanced_compatibility_score()
        default_depth = emotional_depth_service._default_depth_compatibility()
        
        return EnhancedMatchQuality(
            total_compatibility=60.0,
            match_quality_tier=MatchQualityTier.MODERATE,
            connection_prediction=ConnectionPrediction.EXPLORATORY_CONNECTION,
            soul_compatibility=default_soul,
            advanced_compatibility=default_advanced,
            emotional_depth_compatibility=default_depth,
            relationship_timeline="Connection development depends on mutual engagement",
            connection_strengths=["Potential for meaningful connection"],
            growth_opportunities=["Opportunity for mutual understanding"],
            potential_challenges=["Getting to know each other takes time"],
            recommended_approach="Take time to understand each other authentically",
            first_date_suggestion="Coffee or comfortable setting for conversation",
            conversation_starters=[
                "What brings you joy?",
                "What are you passionate about?",
                "How do you like to spend free time?"
            ],
            assessment_confidence=50.0,
            algorithm_version="enhanced_v1.0",
            analysis_timestamp=datetime.utcnow()
        )


# Global service instance
enhanced_match_quality_service = EnhancedMatchQualityService()