"""
AI Matching Service - Phase 5 Revolutionary Soul-Based AI Matching
Advanced machine learning for deep compatibility analysis and personalized matching
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import json
import asyncio
import math
import random

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from app.models.user import User
from app.models.ai_models import (
    UserProfile, CompatibilityPrediction, PersonalizedRecommendation,
    MLModel, ModelPrediction, BehavioralPattern
)
from app.models.soul_connection import SoulConnection
from app.models.daily_revelation import DailyRevelation
from app.models.message import Message
from app.services.analytics_service import analytics_service
from app.models.soul_analytics import AnalyticsEventType

logger = logging.getLogger(__name__)


@dataclass
class MatchRecommendation:
    """AI-generated match recommendation"""
    user_id: int
    recommended_user_id: int
    compatibility_score: float
    confidence_level: float
    match_reasons: List[str]
    conversation_starters: List[str]
    predicted_success_rate: float
    recommendation_strength: str  # high, medium, low


@dataclass
class PersonalityInsight:
    """AI-generated personality insight"""
    trait_name: str
    score: float
    confidence: float
    description: str
    improvement_suggestions: List[str]


@dataclass
class BehaviorAnalysis:
    """User behavior analysis result"""
    patterns: List[str]
    engagement_score: float
    communication_style: str
    preferences: Dict[str, Any]
    recommendations: List[str]


class AIMatchingService:
    """Revolutionary AI-powered matching service with soul-based intelligence"""
    
    def __init__(self):
        self.personality_weights = {
            "openness": 0.2,
            "conscientiousness": 0.15,
            "extraversion": 0.2,
            "agreeableness": 0.25,
            "neuroticism": 0.2
        }
        
        self.compatibility_threshold = 0.65  # Minimum compatibility for recommendations
        self.max_recommendations = 10
        self.profile_update_interval_days = 7
        
        logger.info("AI Matching Service initialized with soul-based intelligence")
    
    async def generate_user_profile_embeddings(
        self,
        user_id: int,
        db: Session
    ) -> UserProfile:
        """Generate comprehensive AI profile embeddings for a user"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Get or create user profile
            profile = db.query(UserProfile).filter(
                UserProfile.user_id == user_id
            ).first()
            
            if not profile:
                profile = UserProfile(user_id=user_id)
                db.add(profile)
            
            # Analyze user's revelations for personality insights
            personality_analysis = await self._analyze_personality_from_revelations(user_id, db)
            
            # Analyze communication patterns
            communication_analysis = await self._analyze_communication_patterns(user_id, db)
            
            # Analyze behavioral patterns
            behavior_analysis = await self._analyze_behavioral_patterns(user_id, db)
            
            # Generate embeddings
            personality_vector = await self._generate_personality_embedding(personality_analysis)
            interests_vector = await self._generate_interests_embedding(user, db)
            values_vector = await self._generate_values_embedding(user_id, db)
            communication_vector = await self._generate_communication_embedding(communication_analysis)
            
            # Update profile with AI insights
            profile.personality_vector = personality_vector
            profile.interests_vector = interests_vector
            profile.values_vector = values_vector
            profile.communication_vector = communication_vector
            
            # Big Five personality scores
            profile.openness_score = personality_analysis.get("openness", 0.5)
            profile.conscientiousness_score = personality_analysis.get("conscientiousness", 0.5)
            profile.extraversion_score = personality_analysis.get("extraversion", 0.5)
            profile.agreeableness_score = personality_analysis.get("agreeableness", 0.5)
            profile.neuroticism_score = personality_analysis.get("neuroticism", 0.5)
            
            # Extended personality traits
            profile.emotional_intelligence = personality_analysis.get("emotional_intelligence", 0.5)
            profile.attachment_style = personality_analysis.get("attachment_style", "secure")
            profile.communication_style = communication_analysis.get("style", "balanced")
            profile.conversation_depth_preference = communication_analysis.get("depth_preference", 0.7)
            
            # AI confidence and completeness
            profile.ai_confidence_level = self._calculate_ai_confidence(user, personality_analysis, communication_analysis)
            profile.profile_completeness_score = self._calculate_profile_completeness(user)
            profile.last_updated_by_ai = datetime.utcnow()
            
            db.commit()
            db.refresh(profile)
            
            logger.info(f"Generated AI profile embeddings for user {user_id}")
            return profile
            
        except Exception as e:
            logger.error(f"Error generating user profile embeddings: {str(e)}")
            raise
    
    async def calculate_ai_compatibility(
        self,
        user1_id: int,
        user2_id: int,
        db: Session
    ) -> CompatibilityPrediction:
        """Calculate advanced AI-powered compatibility between two users"""
        try:
            # Ensure both users have AI profiles
            profile1 = await self._ensure_user_profile(user1_id, db)
            profile2 = await self._ensure_user_profile(user2_id, db)
            
            # Calculate compatibility components
            personality_compat = self._calculate_personality_compatibility(profile1, profile2)
            interests_compat = self._calculate_interests_compatibility(profile1, profile2)
            values_compat = self._calculate_values_compatibility(profile1, profile2)
            communication_compat = self._calculate_communication_compatibility(profile1, profile2)
            
            # Advanced compatibility factors
            lifestyle_compat = await self._calculate_lifestyle_compatibility(user1_id, user2_id, db)
            growth_potential = await self._calculate_growth_potential(profile1, profile2, db)
            conflict_prediction = await self._predict_conflict_likelihood(profile1, profile2, db)
            
            # Overall compatibility with weighted average
            weights = {
                "personality": 0.25,
                "interests": 0.20,
                "values": 0.25,
                "communication": 0.15,
                "lifestyle": 0.15
            }
            
            overall_compatibility = (
                personality_compat * weights["personality"] +
                interests_compat * weights["interests"] +
                values_compat * weights["values"] +
                communication_compat * weights["communication"] +
                lifestyle_compat * weights["lifestyle"]
            )
            
            # Calculate confidence level
            confidence = self._calculate_prediction_confidence(profile1, profile2)
            
            # Generate insights and recommendations
            compatibility_reasons = self._generate_compatibility_reasons(
                personality_compat, interests_compat, values_compat, communication_compat
            )
            
            potential_challenges = self._generate_potential_challenges(
                profile1, profile2, conflict_prediction
            )
            
            conversation_starters = await self._generate_conversation_starters(
                profile1, profile2, db
            )
            
            # Create or update compatibility prediction
            prediction = db.query(CompatibilityPrediction).filter(
                and_(
                    CompatibilityPrediction.user1_profile_id == profile1.id,
                    CompatibilityPrediction.user2_profile_id == profile2.id
                )
            ).first()
            
            if not prediction:
                prediction = CompatibilityPrediction(
                    user1_profile_id=profile1.id,
                    user2_profile_id=profile2.id,
                    model_id=1  # Default model ID for now
                )
                db.add(prediction)
            
            # Update prediction with AI results
            prediction.overall_compatibility = overall_compatibility
            prediction.confidence_level = confidence
            prediction.personality_compatibility = personality_compat
            prediction.values_compatibility = values_compat
            prediction.interests_compatibility = interests_compat
            prediction.communication_compatibility = communication_compat
            prediction.lifestyle_compatibility = lifestyle_compat
            prediction.conversation_quality_prediction = await self._predict_conversation_quality(profile1, profile2, db)
            prediction.long_term_potential = growth_potential
            prediction.conflict_likelihood = conflict_prediction
            prediction.compatibility_reasons = compatibility_reasons
            prediction.potential_challenges = potential_challenges
            prediction.conversation_starters = conversation_starters
            prediction.prediction_version = "v1.0"
            prediction.prediction_date = datetime.utcnow()
            
            db.commit()
            db.refresh(prediction)
            
            logger.info(f"Calculated AI compatibility: {overall_compatibility:.3f} for users {user1_id}-{user2_id}")
            return prediction
            
        except Exception as e:
            logger.error(f"Error calculating AI compatibility: {str(e)}")
            raise
    
    async def generate_personalized_recommendations(
        self,
        user_id: int,
        limit: int = 10,
        db: Session = None
    ) -> List[MatchRecommendation]:
        """Generate AI-powered personalized match recommendations"""
        try:
            user_profile = await self._ensure_user_profile(user_id, db)
            
            # Get potential matches (users not already connected)
            existing_connections = db.query(SoulConnection.user1_id, SoulConnection.user2_id).filter(
                or_(
                    SoulConnection.user1_id == user_id,
                    SoulConnection.user2_id == user_id
                )
            ).all()
            
            excluded_user_ids = set()
            for conn in existing_connections:
                excluded_user_ids.add(conn.user1_id)
                excluded_user_ids.add(conn.user2_id)
            excluded_user_ids.discard(user_id)  # Remove self
            
            # Get potential match candidates with AI profiles
            potential_matches = db.query(UserProfile).filter(
                and_(
                    UserProfile.user_id != user_id,
                    ~UserProfile.user_id.in_(excluded_user_ids),
                    UserProfile.ai_confidence_level > 0.3  # Only users with decent AI confidence
                )
            ).limit(50).all()  # Get broader set for analysis
            
            recommendations = []
            
            # Calculate compatibility with each potential match
            for match_profile in potential_matches:
                compatibility_pred = await self.calculate_ai_compatibility(
                    user_id, match_profile.user_id, db
                )
                
                if compatibility_pred.overall_compatibility >= self.compatibility_threshold:
                    # Generate recommendation strength
                    strength = self._determine_recommendation_strength(compatibility_pred)
                    
                    recommendation = MatchRecommendation(
                        user_id=user_id,
                        recommended_user_id=match_profile.user_id,
                        compatibility_score=compatibility_pred.overall_compatibility,
                        confidence_level=compatibility_pred.confidence_level,
                        match_reasons=compatibility_pred.compatibility_reasons or [],
                        conversation_starters=compatibility_pred.conversation_starters or [],
                        predicted_success_rate=compatibility_pred.long_term_potential or 0.5,
                        recommendation_strength=strength
                    )
                    
                    recommendations.append(recommendation)
            
            # Sort by compatibility score and confidence
            recommendations.sort(
                key=lambda x: (x.compatibility_score * x.confidence_level),
                reverse=True
            )
            
            # Limit results
            final_recommendations = recommendations[:limit]
            
            # Track analytics
            await analytics_service.track_user_event(
                user_id=user_id,
                event_type=AnalyticsEventType.AI_RECOMMENDATIONS_GENERATED,
                event_data={
                    "recommendations_count": len(final_recommendations),
                    "avg_compatibility": sum(r.compatibility_score for r in final_recommendations) / len(final_recommendations) if final_recommendations else 0,
                    "high_strength_count": len([r for r in final_recommendations if r.recommendation_strength == "high"])
                },
                db=db
            )
            
            logger.info(f"Generated {len(final_recommendations)} AI recommendations for user {user_id}")
            return final_recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return []
    
    async def analyze_user_behavior(
        self,
        user_id: int,
        days_back: int = 30,
        db: Session = None
    ) -> BehaviorAnalysis:
        """Analyze user behavior patterns using AI"""
        try:
            # Collect behavioral data
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Message patterns
            messages = db.query(Message).filter(
                Message.sender_id == user_id,
                Message.created_at >= cutoff_date
            ).all()
            
            # Connection patterns
            connections = db.query(SoulConnection).filter(
                or_(
                    SoulConnection.user1_id == user_id,
                    SoulConnection.user2_id == user_id
                ),
                SoulConnection.created_at >= cutoff_date
            ).all()
            
            # Revelation patterns
            revelations = db.query(DailyRevelation).filter(
                DailyRevelation.sender_id == user_id,
                DailyRevelation.created_at >= cutoff_date
            ).all()
            
            # Analyze patterns
            patterns = []
            
            # Communication frequency analysis
            if messages:
                avg_daily_messages = len(messages) / days_back
                if avg_daily_messages > 5:
                    patterns.append("high_communication_frequency")
                elif avg_daily_messages < 1:
                    patterns.append("low_communication_frequency")
                else:
                    patterns.append("moderate_communication_frequency")
            
            # Response time analysis
            response_times = self._analyze_response_times(messages, connections)
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                if avg_response_time < 300:  # 5 minutes
                    patterns.append("quick_responder")
                elif avg_response_time > 3600:  # 1 hour
                    patterns.append("slow_responder")
            
            # Engagement depth analysis
            if revelations:
                revelation_length = [len(r.content) for r in revelations if r.content]
                if revelation_length:
                    avg_length = sum(revelation_length) / len(revelation_length)
                    if avg_length > 200:
                        patterns.append("deep_sharer")
                    elif avg_length < 50:
                        patterns.append("brief_communicator")
            
            # Determine communication style
            communication_style = self._determine_communication_style(messages, revelations)
            
            # Calculate engagement score
            engagement_score = self._calculate_behavioral_engagement_score(
                messages, connections, revelations, days_back
            )
            
            # Generate preferences
            preferences = self._extract_user_preferences(messages, revelations, connections)
            
            # Generate recommendations
            behavior_recommendations = self._generate_behavioral_recommendations(
                patterns, communication_style, engagement_score
            )
            
            analysis = BehaviorAnalysis(
                patterns=patterns,
                engagement_score=engagement_score,
                communication_style=communication_style,
                preferences=preferences,
                recommendations=behavior_recommendations
            )
            
            logger.info(f"Analyzed behavior for user {user_id}: {len(patterns)} patterns detected")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing user behavior: {str(e)}")
            return BehaviorAnalysis(
                patterns=[],
                engagement_score=0.5,
                communication_style="unknown",
                preferences={},
                recommendations=[]
            )
    
    # Helper methods for AI processing
    
    async def _analyze_personality_from_revelations(
        self,
        user_id: int,
        db: Session
    ) -> Dict[str, float]:
        """Analyze personality from user's revelations using NLP"""
        revelations = db.query(DailyRevelation).filter(
            DailyRevelation.sender_id == user_id
        ).all()
        
        if not revelations:
            return self._get_default_personality_scores()
        
        # Combine all revelation text
        text_content = " ".join([r.content for r in revelations if r.content])
        
        # Basic personality analysis (in production, would use advanced NLP)
        personality_scores = {}
        
        # Openness indicators
        openness_keywords = ["creative", "curious", "new", "explore", "adventure", "art", "different", "unique"]
        personality_scores["openness"] = self._calculate_keyword_score(text_content, openness_keywords)
        
        # Conscientiousness indicators
        conscientiousness_keywords = ["plan", "organize", "goal", "achieve", "responsible", "careful", "detail"]
        personality_scores["conscientiousness"] = self._calculate_keyword_score(text_content, conscientiousness_keywords)
        
        # Extraversion indicators
        extraversion_keywords = ["people", "social", "party", "friends", "outgoing", "energy", "excitement"]
        personality_scores["extraversion"] = self._calculate_keyword_score(text_content, extraversion_keywords)
        
        # Agreeableness indicators
        agreeableness_keywords = ["kind", "caring", "help", "understand", "empathy", "support", "harmony"]
        personality_scores["agreeableness"] = self._calculate_keyword_score(text_content, agreeableness_keywords)
        
        # Neuroticism (inverted - emotional stability)
        stability_keywords = ["calm", "stable", "peaceful", "confident", "secure", "relaxed"]
        personality_scores["neuroticism"] = 1.0 - self._calculate_keyword_score(text_content, stability_keywords)
        
        # Emotional intelligence
        eq_keywords = ["feel", "emotion", "understand", "connect", "empathy", "aware", "sensitive"]
        personality_scores["emotional_intelligence"] = self._calculate_keyword_score(text_content, eq_keywords)
        
        # Attachment style (simplified)
        secure_keywords = ["trust", "secure", "comfortable", "open", "reliable"]
        anxious_keywords = ["worry", "anxious", "need", "fear", "clingy"]
        avoidant_keywords = ["independent", "space", "alone", "self-sufficient"]
        
        secure_score = self._calculate_keyword_score(text_content, secure_keywords)
        anxious_score = self._calculate_keyword_score(text_content, anxious_keywords)
        avoidant_score = self._calculate_keyword_score(text_content, avoidant_keywords)
        
        if secure_score > anxious_score and secure_score > avoidant_score:
            personality_scores["attachment_style"] = "secure"
        elif anxious_score > avoidant_score:
            personality_scores["attachment_style"] = "anxious"
        else:
            personality_scores["attachment_style"] = "avoidant"
        
        return personality_scores
    
    async def _analyze_communication_patterns(
        self,
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Analyze user's communication patterns"""
        messages = db.query(Message).filter(
            Message.sender_id == user_id
        ).order_by(Message.created_at.desc()).limit(100).all()
        
        if not messages:
            return {
                "style": "balanced",
                "depth_preference": 0.5,
                "response_pattern": "moderate",
                "emoji_usage": 0.3
            }
        
        # Analyze message characteristics
        total_length = sum(len(msg.content) for msg in messages)
        avg_length = total_length / len(messages)
        
        # Communication style analysis
        if avg_length > 150:
            style = "detailed"
            depth_preference = 0.8
        elif avg_length < 50:
            style = "concise" 
            depth_preference = 0.4
        else:
            style = "balanced"
            depth_preference = 0.6
        
        # Emoji usage (simplified analysis)
        emoji_count = sum(msg.content.count('😊') + msg.content.count('❤️') + 
                         msg.content.count('😍') + msg.content.count('🥰') for msg in messages)
        emoji_usage = min(1.0, emoji_count / len(messages) * 0.1)
        
        return {
            "style": style,
            "depth_preference": depth_preference,
            "avg_message_length": avg_length,
            "emoji_usage": emoji_usage,
            "total_messages": len(messages)
        }
    
    async def _analyze_behavioral_patterns(
        self,
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """Analyze broader behavioral patterns"""
        # Get user activity data
        user = db.query(User).filter(User.id == user_id).first()
        
        patterns = {
            "activity_level": "moderate",
            "engagement_consistency": 0.5,
            "feature_usage": {},
            "time_patterns": {}
        }
        
        # Activity level analysis
        if user.total_messages_sent > 100:
            patterns["activity_level"] = "high"
        elif user.total_messages_sent < 10:
            patterns["activity_level"] = "low"
        
        # Feature usage patterns
        patterns["feature_usage"]["revelations"] = user.total_revelations_shared or 0
        patterns["feature_usage"]["swipes"] = user.total_swipes or 0
        patterns["feature_usage"]["matches"] = user.total_matches or 0
        
        return patterns
    
    def _calculate_keyword_score(self, text: str, keywords: List[str]) -> float:
        """Calculate personality trait score based on keyword presence"""
        if not text:
            return 0.5
        
        text_lower = text.lower()
        keyword_count = sum(text_lower.count(keyword.lower()) for keyword in keywords)
        word_count = len(text.split())
        
        if word_count == 0:
            return 0.5
        
        # Normalize score between 0.2 and 0.9 (avoid extremes)
        raw_score = keyword_count / word_count * 10
        normalized_score = min(0.9, max(0.2, 0.5 + raw_score))
        
        return normalized_score
    
    def _get_default_personality_scores(self) -> Dict[str, float]:
        """Return default personality scores when no data is available"""
        return {
            "openness": 0.5,
            "conscientiousness": 0.5,
            "extraversion": 0.5,
            "agreeableness": 0.5,
            "neuroticism": 0.5,
            "emotional_intelligence": 0.5,
            "attachment_style": "secure"
        }
    
    async def _generate_personality_embedding(
        self,
        personality_analysis: Dict[str, Any]
    ) -> List[float]:
        """Generate 128-dimensional personality embedding vector"""
        # Create a comprehensive personality vector
        # In production, this would use a trained neural network
        embedding = []
        
        # Big Five components (25 dimensions each = 125 total)
        for trait in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
            score = personality_analysis.get(trait, 0.5)
            # Create 25 dimensional sub-vector for each trait
            trait_vector = [score + random.gauss(0, 0.1) for _ in range(25)]
            embedding.extend(trait_vector)
        
        # Additional dimensions for emotional intelligence (3 dimensions)
        eq_score = personality_analysis.get("emotional_intelligence", 0.5)
        embedding.extend([eq_score, eq_score * 0.8, eq_score * 1.2])
        
        # Ensure exactly 128 dimensions
        while len(embedding) < 128:
            embedding.append(0.5)
        
        # Normalize to unit vector
        embedding = embedding[:128]
        norm = math.sqrt(sum(x*x for x in embedding))
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        return embedding
    
    async def _generate_interests_embedding(
        self,
        user: User,
        db: Session
    ) -> List[float]:
        """Generate interests embedding from user data"""
        # Get user interests (simplified - would use embeddings in production)
        interests = user.interests or []
        
        # Create 64-dimensional interests vector
        interest_categories = [
            "sports", "music", "art", "travel", "food", "movies", "books", "technology",
            "nature", "fitness", "cooking", "photography", "dancing", "gaming", "fashion", "science"
        ]
        
        embedding = []
        for category in interest_categories:
            # Check if user has interest in this category
            score = 0.1  # Default low score
            for interest in interests:
                if category.lower() in str(interest).lower():
                    score = 0.8
                    break
            embedding.extend([score, score * 0.9, score * 1.1, score * 0.7])  # 4 dims per category
        
        # Pad to 64 dimensions
        while len(embedding) < 64:
            embedding.append(0.1)
        
        return embedding[:64]
    
    async def _generate_values_embedding(
        self,
        user_id: int,
        db: Session
    ) -> List[float]:
        """Generate values embedding from user revelations and profile"""
        revelations = db.query(DailyRevelation).filter(
            DailyRevelation.sender_id == user_id
        ).all()
        
        # Analyze values from revelations
        text_content = " ".join([r.content for r in revelations if r.content])
        
        value_categories = {
            "family": ["family", "children", "parents", "siblings", "relatives"],
            "career": ["work", "career", "success", "achievement", "goals"],
            "spirituality": ["spiritual", "faith", "believe", "religion", "soul"],
            "health": ["health", "fitness", "wellness", "exercise", "nutrition"],
            "creativity": ["creative", "art", "music", "write", "create"],
            "adventure": ["adventure", "travel", "explore", "new", "experience"],
            "security": ["security", "stable", "safe", "comfortable", "secure"],
            "freedom": ["freedom", "independent", "free", "liberty", "choice"]
        }
        
        embedding = []
        for category, keywords in value_categories.items():
            score = self._calculate_keyword_score(text_content, keywords)
            # Create 8 dimensions per value category (64 total)
            category_vector = [score + random.gauss(0, 0.05) for _ in range(8)]
            embedding.extend(category_vector)
        
        return embedding[:64]
    
    async def _generate_communication_embedding(
        self,
        communication_analysis: Dict[str, Any]
    ) -> List[float]:
        """Generate communication style embedding"""
        style = communication_analysis.get("style", "balanced")
        depth_pref = communication_analysis.get("depth_preference", 0.5)
        emoji_usage = communication_analysis.get("emoji_usage", 0.3)
        
        # Create 32-dimensional communication vector
        embedding = []
        
        # Style encoding (12 dimensions)
        if style == "detailed":
            embedding.extend([0.9, 0.8, 0.7] * 4)
        elif style == "concise":
            embedding.extend([0.2, 0.3, 0.1] * 4)
        else:  # balanced
            embedding.extend([0.5, 0.6, 0.4] * 4)
        
        # Depth preference (10 dimensions)
        embedding.extend([depth_pref] * 10)
        
        # Emoji and emotional expression (10 dimensions)
        embedding.extend([emoji_usage] * 10)
        
        return embedding[:32]
    
    def _calculate_ai_confidence(
        self,
        user: User,
        personality_analysis: Dict[str, Any],
        communication_analysis: Dict[str, Any]
    ) -> float:
        """Calculate confidence level for AI analysis"""
        confidence_factors = []
        
        # Data completeness
        if user.is_profile_complete:
            confidence_factors.append(0.3)
        else:
            confidence_factors.append(0.1)
        
        # Revelation data quality
        total_messages = communication_analysis.get("total_messages", 0)
        if total_messages > 50:
            confidence_factors.append(0.4)
        elif total_messages > 10:
            confidence_factors.append(0.3)
        else:
            confidence_factors.append(0.1)
        
        # Activity level
        if user.total_revelations_shared and user.total_revelations_shared > 5:
            confidence_factors.append(0.3)
        else:
            confidence_factors.append(0.2)
        
        return min(1.0, sum(confidence_factors))
    
    def _calculate_profile_completeness(self, user: User) -> float:
        """Calculate how complete the user profile is"""
        completeness_score = 0.0
        
        if user.first_name and user.last_name:
            completeness_score += 0.2
        if user.bio:
            completeness_score += 0.2
        if user.interests:
            completeness_score += 0.2
        if user.is_profile_complete:
            completeness_score += 0.4
        
        return min(1.0, completeness_score)
    
    async def _ensure_user_profile(self, user_id: int, db: Session) -> UserProfile:
        """Ensure user has an AI profile, creating one if needed"""
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()
        
        if not profile:
            profile = await self.generate_user_profile_embeddings(user_id, db)
        elif not profile.last_updated_by_ai or \
             (datetime.utcnow() - profile.last_updated_by_ai).days > self.profile_update_interval_days:
            # Update stale profile
            profile = await self.generate_user_profile_embeddings(user_id, db)
        
        return profile
    
    def _calculate_personality_compatibility(
        self,
        profile1: UserProfile,
        profile2: UserProfile
    ) -> float:
        """Calculate personality compatibility using Big Five model"""
        if not profile1.personality_vector or not profile2.personality_vector:
            return 0.5
        
        # Calculate cosine similarity between personality vectors
        vec1 = profile1.personality_vector
        vec2 = profile2.personality_vector
        
        similarity = self._cosine_similarity(vec1, vec2)
        
        # Convert to 0-1 scale (cosine similarity ranges from -1 to 1)
        compatibility = (similarity + 1) / 2
        
        return min(1.0, max(0.0, compatibility))
    
    def _calculate_interests_compatibility(
        self,
        profile1: UserProfile,
        profile2: UserProfile
    ) -> float:
        """Calculate interests compatibility"""
        if not profile1.interests_vector or not profile2.interests_vector:
            return 0.5
        
        vec1 = profile1.interests_vector
        vec2 = profile2.interests_vector
        
        similarity = self._cosine_similarity(vec1, vec2)
        compatibility = (similarity + 1) / 2
        
        return min(1.0, max(0.0, compatibility))
    
    def _calculate_values_compatibility(
        self,
        profile1: UserProfile,
        profile2: UserProfile
    ) -> float:
        """Calculate values compatibility"""
        if not profile1.values_vector or not profile2.values_vector:
            return 0.5
        
        vec1 = profile1.values_vector
        vec2 = profile2.values_vector
        
        similarity = self._cosine_similarity(vec1, vec2)
        compatibility = (similarity + 1) / 2
        
        return min(1.0, max(0.0, compatibility))
    
    def _calculate_communication_compatibility(
        self,
        profile1: UserProfile,
        profile2: UserProfile
    ) -> float:
        """Calculate communication style compatibility"""
        if not profile1.communication_vector or not profile2.communication_vector:
            return 0.5
        
        vec1 = profile1.communication_vector
        vec2 = profile2.communication_vector
        
        similarity = self._cosine_similarity(vec1, vec2)
        compatibility = (similarity + 1) / 2
        
        return min(1.0, max(0.0, compatibility))
    
    async def _calculate_lifestyle_compatibility(
        self,
        user1_id: int,
        user2_id: int,
        db: Session
    ) -> float:
        """Calculate lifestyle compatibility based on user behavior"""
        # Get behavioral patterns for both users
        behavior1 = await self.analyze_user_behavior(user1_id, db=db)
        behavior2 = await self.analyze_user_behavior(user2_id, db=db)
        
        # Compare activity levels
        activity_compat = 1.0 - abs(behavior1.engagement_score - behavior2.engagement_score)
        
        # Compare communication styles
        style_compat = 0.8 if behavior1.communication_style == behavior2.communication_style else 0.5
        
        # Overall lifestyle compatibility
        lifestyle_compat = (activity_compat * 0.6) + (style_compat * 0.4)
        
        return min(1.0, max(0.0, lifestyle_compat))
    
    def _calculate_prediction_confidence(
        self,
        profile1: UserProfile,
        profile2: UserProfile
    ) -> float:
        """Calculate confidence in the compatibility prediction"""
        conf1 = profile1.ai_confidence_level or 0.5
        conf2 = profile2.ai_confidence_level or 0.5
        
        # Confidence is the harmonic mean of individual confidences
        combined_confidence = 2 * (conf1 * conf2) / (conf1 + conf2) if (conf1 + conf2) > 0 else 0.5
        
        return min(1.0, max(0.1, combined_confidence))
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(vec1) != len(vec2):
            return 0.0
        
        # Calculate dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        
        # Calculate magnitudes
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(a * a for a in vec2))
        
        # Avoid division by zero
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    async def _calculate_growth_potential(
        self,
        profile1: UserProfile,
        profile2: UserProfile,
        db: Session
    ) -> float:
        """Calculate potential for mutual growth in relationship"""
        # Complementary traits can indicate growth potential
        growth_score = 0.0
        
        # Different but compatible personality traits
        if profile1.openness_score and profile2.openness_score:
            openness_diff = abs(profile1.openness_score - profile2.openness_score)
            if 0.1 < openness_diff < 0.4:  # Some difference but not too much
                growth_score += 0.2
        
        # Similar values but different perspectives
        if profile1.conscientiousness_score and profile2.conscientiousness_score:
            consc_avg = (profile1.conscientiousness_score + profile2.conscientiousness_score) / 2
            if consc_avg > 0.6:  # Both reasonably conscientious
                growth_score += 0.2
        
        # Communication compatibility for growth
        if profile1.communication_style != profile2.communication_style:
            growth_score += 0.15  # Different styles can complement
        else:
            growth_score += 0.1   # Similar styles provide stability
        
        # Emotional intelligence combination
        if profile1.emotional_intelligence and profile2.emotional_intelligence:
            ei_avg = (profile1.emotional_intelligence + profile2.emotional_intelligence) / 2
            growth_score += ei_avg * 0.3
        
        return min(1.0, max(0.0, growth_score))
    
    async def _predict_conflict_likelihood(
        self,
        profile1: UserProfile,
        profile2: UserProfile,
        db: Session
    ) -> float:
        """Predict likelihood of conflicts based on personality traits"""
        conflict_factors = []
        
        # High neuroticism increases conflict likelihood
        if profile1.neuroticism_score and profile2.neuroticism_score:
            avg_neuroticism = (profile1.neuroticism_score + profile2.neuroticism_score) / 2
            conflict_factors.append(avg_neuroticism * 0.4)
        
        # Very low agreeableness can increase conflicts
        if profile1.agreeableness_score and profile2.agreeableness_score:
            min_agreeableness = min(profile1.agreeableness_score, profile2.agreeableness_score)
            if min_agreeableness < 0.3:
                conflict_factors.append(0.3)
        
        # Communication style mismatches
        if (profile1.communication_style and profile2.communication_style and
            profile1.communication_style != profile2.communication_style):
            if (profile1.communication_style == "direct" and profile2.communication_style == "diplomatic"):
                conflict_factors.append(0.2)
        
        # Calculate average conflict likelihood
        if conflict_factors:
            return sum(conflict_factors) / len(conflict_factors)
        
        return 0.3  # Default moderate conflict likelihood
    
    async def _predict_conversation_quality(
        self,
        profile1: UserProfile,
        profile2: UserProfile,
        db: Session
    ) -> float:
        """Predict quality of conversations between users"""
        quality_factors = []
        
        # Similar conversation depth preferences
        if profile1.conversation_depth_preference and profile2.conversation_depth_preference:
            depth_similarity = 1.0 - abs(profile1.conversation_depth_preference - profile2.conversation_depth_preference)
            quality_factors.append(depth_similarity * 0.4)
        
        # Communication style compatibility
        if profile1.communication_style and profile2.communication_style:
            if profile1.communication_style == profile2.communication_style:
                quality_factors.append(0.3)
            else:
                quality_factors.append(0.2)  # Different styles can still work
        
        # Emotional intelligence
        if profile1.emotional_intelligence and profile2.emotional_intelligence:
            avg_ei = (profile1.emotional_intelligence + profile2.emotional_intelligence) / 2
            quality_factors.append(avg_ei * 0.3)
        
        if quality_factors:
            return sum(quality_factors) / len(quality_factors)
        
        return 0.6  # Default moderate conversation quality
    
    async def _generate_conversation_starters(
        self,
        profile1: UserProfile,
        profile2: UserProfile,
        db: Session
    ) -> List[str]:
        """Generate AI-powered conversation starters"""
        starters = []
        
        # Based on shared personality traits
        if (profile1.openness_score and profile2.openness_score and
            profile1.openness_score > 0.6 and profile2.openness_score > 0.6):
            starters.append("What's the most creative project you've worked on recently?")
            starters.append("If you could explore any new skill, what would it be?")
        
        # Based on communication styles
        if profile1.communication_style == "detailed" or profile2.communication_style == "detailed":
            starters.append("I'd love to hear your thoughts on something you're passionate about.")
            starters.append("What's a topic you could talk about for hours?")
        
        # Based on emotional intelligence
        if (profile1.emotional_intelligence and profile2.emotional_intelligence and
            (profile1.emotional_intelligence + profile2.emotional_intelligence) / 2 > 0.7):
            starters.append("What's something that's been on your mind lately?")
            starters.append("How do you like to connect with people on a deeper level?")
        
        # Fallback generic starters
        if not starters:
            starters = [
                "What's been the highlight of your week so far?",
                "If you could have dinner with anyone, who would it be?",
                "What's something you've learned recently that fascinated you?"
            ]
        
        return starters[:5]  # Return max 5 starters
    
    def _generate_compatibility_reasons(
        self,
        personality_compat: float,
        interests_compat: float,
        values_compat: float,
        communication_compat: float
    ) -> List[str]:
        """Generate human-readable compatibility reasons"""
        reasons = []
        
        if personality_compat > 0.7:
            reasons.append("Your personalities complement each other beautifully")
        elif personality_compat > 0.5:
            reasons.append("You share similar personality traits")
        
        if interests_compat > 0.7:
            reasons.append("You have many shared interests and passions")
        elif interests_compat > 0.5:
            reasons.append("Your interests align well together")
        
        if values_compat > 0.7:
            reasons.append("Your core values are deeply aligned")
        elif values_compat > 0.5:
            reasons.append("You share important life values")
        
        if communication_compat > 0.7:
            reasons.append("Your communication styles are highly compatible")
        elif communication_compat > 0.5:
            reasons.append("You communicate in similar ways")
        
        # Ensure we always return at least one reason
        if not reasons:
            reasons.append("You have a good fundamental compatibility")
        
        return reasons[:4]  # Return max 4 reasons
    
    def _generate_potential_challenges(
        self,
        profile1: UserProfile,
        profile2: UserProfile,
        conflict_prediction: float
    ) -> List[str]:
        """Generate potential relationship challenges"""
        challenges = []
        
        if conflict_prediction > 0.6:
            challenges.append("May need to work on communication during disagreements")
        
        # Based on personality differences
        if (profile1.neuroticism_score and profile2.neuroticism_score and
            abs(profile1.neuroticism_score - profile2.neuroticism_score) > 0.4):
            challenges.append("Different approaches to handling stress")
        
        if (profile1.conscientiousness_score and profile2.conscientiousness_score and
            abs(profile1.conscientiousness_score - profile2.conscientiousness_score) > 0.5):
            challenges.append("Different levels of organization and planning")
        
        # Communication style mismatches
        if (profile1.communication_style and profile2.communication_style and
            profile1.communication_style != profile2.communication_style):
            challenges.append("May need to adapt to different communication preferences")
        
        # Ensure constructive framing
        if not challenges:
            challenges.append("Every relationship has growth opportunities")
        
        return challenges[:3]  # Return max 3 challenges
    
    def _determine_recommendation_strength(self, compatibility_pred) -> str:
        """Determine recommendation strength based on compatibility and confidence"""
        score = compatibility_pred.overall_compatibility
        confidence = compatibility_pred.confidence_level
        
        # Combined score weighted by confidence
        combined_score = score * confidence
        
        if combined_score > 0.8:
            return "high"
        elif combined_score > 0.6:
            return "medium"
        else:
            return "low"
    
    def _analyze_response_times(self, messages, connections) -> List[float]:
        """Analyze message response times"""
        # Simplified implementation - in production would analyze actual response patterns
        response_times = []
        
        # Mock response time analysis based on message frequency
        if len(messages) > 10:
            # Frequent messager - likely quick responder
            response_times = [300, 180, 450, 200, 350]  # Average ~5 minutes
        elif len(messages) > 3:
            response_times = [1800, 900, 2400, 1200]     # Average ~30 minutes
        else:
            response_times = [3600, 7200, 1800]          # Average ~1+ hours
        
        return response_times
    
    def _determine_communication_style(self, messages, revelations) -> str:
        """Determine user's communication style"""
        if not messages and not revelations:
            return "balanced"
        
        # Analyze message length and emotional depth
        total_content = []
        if messages:
            total_content.extend([msg.content for msg in messages if msg.content])
        if revelations:
            total_content.extend([rev.content for rev in revelations if rev.content])
        
        if not total_content:
            return "balanced"
        
        avg_length = sum(len(content) for content in total_content) / len(total_content)
        
        if avg_length > 200:
            return "detailed"
        elif avg_length < 50:
            return "concise"
        else:
            return "balanced"
    
    def _calculate_behavioral_engagement_score(self, messages, connections, revelations, days_back) -> float:
        """Calculate user engagement score based on behavior"""
        engagement_factors = []
        
        # Message frequency
        if messages:
            msg_per_day = len(messages) / days_back
            engagement_factors.append(min(1.0, msg_per_day / 5.0))  # Normalize to 5 messages/day = 1.0
        
        # Revelation participation
        if revelations:
            rev_per_week = len(revelations) / (days_back / 7)
            engagement_factors.append(min(1.0, rev_per_week / 2.0))  # 2 revelations/week = 1.0
        
        # Connection activity
        if connections:
            engagement_factors.append(0.7)  # Base engagement for having connections
        
        if engagement_factors:
            return sum(engagement_factors) / len(engagement_factors)
        
        return 0.3  # Default low engagement
    
    def _extract_user_preferences(self, messages, revelations, connections) -> Dict[str, Any]:
        """Extract user preferences from behavior"""
        preferences = {
            "communication_frequency": "moderate",
            "depth_preference": "balanced",
            "response_style": "thoughtful"
        }
        
        # Analyze communication frequency
        if len(messages) > 50:
            preferences["communication_frequency"] = "high"
        elif len(messages) < 10:
            preferences["communication_frequency"] = "low"
        
        # Analyze depth preference from revelations
        if revelations:
            avg_revelation_length = sum(len(r.content or "") for r in revelations) / len(revelations)
            if avg_revelation_length > 150:
                preferences["depth_preference"] = "deep"
            elif avg_revelation_length < 50:
                preferences["depth_preference"] = "light"
        
        return preferences
    
    def _generate_behavioral_recommendations(self, patterns, communication_style, engagement_score) -> List[str]:
        """Generate behavioral improvement recommendations"""
        recommendations = []
        
        if engagement_score < 0.4:
            recommendations.append("Consider being more active in conversations to improve connections")
        
        if "slow_responder" in patterns:
            recommendations.append("Try to respond to messages more promptly to maintain connection momentum")
        
        if "brief_communicator" in patterns:
            recommendations.append("Consider sharing more detailed thoughts to deepen emotional connections")
        
        if communication_style == "concise":
            recommendations.append("Sometimes longer messages can help build deeper emotional bonds")
        
        # Always include a positive recommendation
        recommendations.append("Continue being authentic in your communications")
        
        return recommendations[:4]  # Return max 4 recommendations


# Global service instance
ai_matching_service = AIMatchingService()