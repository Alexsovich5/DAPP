"""
Phase 6: Advanced Personalization & Content Intelligence Service
AI-powered dynamic content personalization and user experience adaptation
"""
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import json
import random
import math
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.user import User
from app.models.ai_models import UserProfile, CompatibilityPrediction
from app.models.personalization_models import (
    UserPersonalizationProfile, PersonalizedContent, ContentFeedback,
    AlgorithmOptimization, ConversationFlowAnalytics,
    PersonalizationStrategy, ContentType
)

logger = logging.getLogger(__name__)


class PersonalizationEngine:
    """
    Advanced AI-powered personalization engine for content intelligence
    """
    
    def __init__(self):
        self.content_templates = self._load_content_templates()
        self.personalization_weights = {
            "behavioral_patterns": 0.35,
            "compatibility_score": 0.25,
            "communication_style": 0.20,
            "emotional_state": 0.15,
            "feedback_history": 0.05
        }
    
    async def get_or_create_personalization_profile(
        self, 
        user_id: int, 
        db: Session
    ) -> UserPersonalizationProfile:
        """Get or create personalization profile for user"""
        profile = db.query(UserPersonalizationProfile).filter(
            UserPersonalizationProfile.user_id == user_id
        ).first()
        
        if not profile:
            profile = UserPersonalizationProfile(
                user_id=user_id,
                preferred_communication_style="balanced",
                conversation_pace_preference="moderate",
                revelation_timing_preference="gradual",
                content_depth_preference="medium"
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)
            
            # Initialize with behavioral analysis
            await self._analyze_initial_user_behavior(user_id, profile, db)
        
        return profile

    async def generate_conversation_starters(
        self,
        user_id: int,
        target_user_id: int,
        count: int = 5,
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """Generate personalized conversation starters using AI"""
        try:
            # Get personalization profiles
            user_profile = await self.get_or_create_personalization_profile(user_id, db)
            target_profile = await self.get_or_create_personalization_profile(target_user_id, db)
            
            # Get compatibility data
            compatibility = db.query(CompatibilityPrediction).filter(
                and_(
                    CompatibilityPrediction.user1_id == user_id,
                    CompatibilityPrediction.user2_id == target_user_id
                )
            ).first()
            
            # Generate starters based on personalization
            starters = []
            for i in range(count):
                starter = await self._generate_personalized_starter(
                    user_profile, target_profile, compatibility, db
                )
                if starter:
                    starters.append(starter)
            
            return starters[:count]
            
        except Exception as e:
            logger.error(f"Error generating conversation starters: {str(e)}")
            return self._get_fallback_starters(count)

    async def generate_revelation_prompts(
        self,
        user_id: int,
        revelation_day: int,
        connection_context: Dict[str, Any],
        db: Session
    ) -> List[Dict[str, Any]]:
        """Generate adaptive revelation prompts based on user behavior and connection progress"""
        try:
            user_profile = await self.get_or_create_personalization_profile(user_id, db)
            
            # Analyze conversation flow for this connection
            flow_analysis = await self._analyze_conversation_flow(
                user_id, connection_context.get("connection_id"), db
            )
            
            # Generate context-aware prompts
            prompts = []
            base_prompts = self._get_revelation_templates(revelation_day)
            
            for template in base_prompts:
                personalized_prompt = await self._personalize_revelation_prompt(
                    template, user_profile, flow_analysis, connection_context
                )
                prompts.append(personalized_prompt)
            
            return prompts
            
        except Exception as e:
            logger.error(f"Error generating revelation prompts: {str(e)}")
            return self._get_fallback_revelation_prompts(revelation_day)

    async def generate_smart_replies(
        self,
        user_id: int,
        conversation_context: Dict[str, Any],
        last_message: str,
        db: Session
    ) -> List[Dict[str, Any]]:
        """Generate intelligent reply suggestions based on conversation context"""
        try:
            user_profile = await self.get_or_create_personalization_profile(user_id, db)
            
            # Analyze message sentiment and intent
            message_analysis = self._analyze_message_content(last_message)
            
            # Generate contextual replies
            replies = []
            reply_strategies = [
                "empathetic_response",
                "curious_follow_up", 
                "shared_experience",
                "deeper_connection",
                "playful_response"
            ]
            
            for strategy in reply_strategies[:3]:  # Generate 3 smart replies
                reply = await self._generate_smart_reply(
                    user_profile, message_analysis, strategy, conversation_context
                )
                if reply:
                    replies.append(reply)
            
            return replies
            
        except Exception as e:
            logger.error(f"Error generating smart replies: {str(e)}")
            return self._get_fallback_replies()

    async def personalize_ui_experience(
        self,
        user_id: int,
        current_context: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """Generate UI/UX personalizations based on user behavior patterns"""
        try:
            user_profile = await self.get_or_create_personalization_profile(user_id, db)
            
            # Analyze user interaction patterns
            ui_preferences = await self._analyze_ui_interaction_patterns(user_id, db)
            
            personalizations = {
                "theme_adjustments": self._get_theme_personalizations(user_profile, ui_preferences),
                "layout_preferences": self._get_layout_personalizations(user_profile, ui_preferences),
                "animation_settings": self._get_animation_personalizations(user_profile),
                "content_density": self._get_content_density_preferences(user_profile),
                "interaction_hints": self._get_personalized_hints(user_profile, current_context)
            }
            
            return personalizations
            
        except Exception as e:
            logger.error(f"Error personalizing UI experience: {str(e)}")
            return self._get_default_ui_settings()

    async def record_content_feedback(
        self,
        user_id: int,
        content_id: int,
        feedback_data: Dict[str, Any],
        db: Session
    ) -> bool:
        """Record user feedback on personalized content for optimization"""
        try:
            user_profile = await self.get_or_create_personalization_profile(user_id, db)
            
            feedback = ContentFeedback(
                user_profile_id=user_profile.id,
                content_id=content_id,
                feedback_type=feedback_data.get("type", "implicit"),
                feedback_score=feedback_data.get("score"),
                feedback_text=feedback_data.get("text"),
                interaction_duration=feedback_data.get("duration"),
                follow_up_actions=feedback_data.get("actions"),
                context_data=feedback_data.get("context"),
                session_id=feedback_data.get("session_id"),
                device_type=feedback_data.get("device_type")
            )
            
            db.add(feedback)
            
            # Update personalization profile with new feedback
            await self._update_personalization_from_feedback(
                user_profile, feedback, db
            )
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error recording content feedback: {str(e)}")
            db.rollback()
            return False

    async def optimize_algorithm_performance(
        self,
        optimization_type: str,
        target_metrics: Dict[str, float],
        db: Session
    ) -> Dict[str, Any]:
        """Real-time algorithm optimization based on performance metrics"""
        try:
            # Get current algorithm performance
            current_performance = await self._get_current_algorithm_metrics(
                optimization_type, db
            )
            
            # Calculate optimization parameters
            optimization_params = self._calculate_optimization_parameters(
                current_performance, target_metrics
            )
            
            # Create optimization record
            optimization = AlgorithmOptimization(
                optimization_type=optimization_type,
                algorithm_version=f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                optimization_strategy=PersonalizationStrategy.LEARNING_ADAPTATION.value,
                parameters=optimization_params,
                target_metrics=target_metrics,
                baseline_metrics=current_performance,
                is_active=True
            )
            
            db.add(optimization)
            db.commit()
            
            return {
                "optimization_id": optimization.id,
                "parameters": optimization_params,
                "expected_improvement": self._calculate_expected_improvement(
                    current_performance, target_metrics
                )
            }
            
        except Exception as e:
            logger.error(f"Error optimizing algorithm performance: {str(e)}")
            return {"error": str(e)}

    # Private methods for core functionality

    async def _generate_personalized_starter(
        self,
        user_profile: UserPersonalizationProfile,
        target_profile: UserPersonalizationProfile,
        compatibility: Optional[CompatibilityPrediction],
        db: Session
    ) -> Dict[str, Any]:
        """Generate a single personalized conversation starter"""
        
        # Get communication style preferences
        user_style = user_profile.get_communication_style_vector()
        target_style = target_profile.get_communication_style_vector()
        
        # Choose optimal communication style for both users
        optimal_style = self._calculate_optimal_communication_style(user_style, target_style)
        
        # Select appropriate template category
        template_category = self._select_template_category(
            optimal_style, compatibility, user_profile.topic_preferences
        )
        
        # Generate personalized content
        template = random.choice(self.content_templates["conversation_starters"][template_category])
        
        personalized_content = self._personalize_template(
            template, user_profile, target_profile, compatibility
        )
        
        # Create content record
        content = PersonalizedContent(
            user_profile_id=user_profile.id,
            target_user_id=target_profile.user_id,
            content_type=ContentType.CONVERSATION_STARTER.value,
            content_text=personalized_content["text"],
            content_metadata=personalized_content["metadata"],
            generation_strategy=PersonalizationStrategy.COMPATIBILITY_BASED.value,
            generation_context={
                "user_style": user_style,
                "target_style": target_style,
                "optimal_style": optimal_style,
                "template_category": template_category
            },
            ai_confidence_score=personalized_content["confidence"]
        )
        
        db.add(content)
        db.commit()
        
        return {
            "id": content.id,
            "text": personalized_content["text"],
            "category": template_category,
            "confidence": personalized_content["confidence"],
            "metadata": personalized_content["metadata"]
        }

    def _load_content_templates(self) -> Dict[str, Any]:
        """Load content templates for personalization"""
        return {
            "conversation_starters": {
                "casual_fun": [
                    {
                        "template": "I noticed you enjoy {interest}! What's the most {adjective} experience you've had with it?",
                        "variables": ["interest", "adjective"],
                        "tone": "casual",
                        "depth": "light"
                    },
                    {
                        "template": "Your {trait} energy really comes through in your profile. What's something that always makes you smile?",
                        "variables": ["trait"],
                        "tone": "warm", 
                        "depth": "medium"
                    }
                ],
                "deep_connection": [
                    {
                        "template": "I'm curious about your perspective on {topic}. What's shaped your view on this?",
                        "variables": ["topic"],
                        "tone": "thoughtful",
                        "depth": "deep"
                    },
                    {
                        "template": "Reading about your values around {value}, I'm wondering - what experience taught you the importance of this?",
                        "variables": ["value"],
                        "tone": "sincere",
                        "depth": "deep"
                    }
                ],
                "shared_interests": [
                    {
                        "template": "I see we both love {common_interest}! What drew you to it initially?",
                        "variables": ["common_interest"],
                        "tone": "enthusiastic",
                        "depth": "medium"
                    }
                ]
            },
            "revelation_prompts": {
                "day_1": [
                    {
                        "template": "Share something that brings you genuine joy and explain why it resonates with your soul.",
                        "focus": "personal_joy",
                        "emotional_depth": "medium"
                    }
                ],
                "day_2": [
                    {
                        "template": "Describe a moment when you felt truly understood by someone. What made it special?",
                        "focus": "connection_memory", 
                        "emotional_depth": "deep"
                    }
                ]
            }
        }

    def _calculate_optimal_communication_style(
        self, 
        user_style: Dict[str, float], 
        target_style: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate optimal communication style for both users"""
        optimal_style = {}
        
        for dimension in user_style.keys():
            user_val = user_style[dimension]
            target_val = target_style[dimension]
            
            # Find middle ground weighted slightly toward more expressive style
            if dimension in ["enthusiasm", "emotional_openness"]:
                optimal_style[dimension] = max(user_val, target_val) * 0.7 + min(user_val, target_val) * 0.3
            else:
                optimal_style[dimension] = (user_val + target_val) / 2
        
        return optimal_style

    def _personalize_template(
        self,
        template: Dict[str, Any],
        user_profile: UserPersonalizationProfile,
        target_profile: UserPersonalizationProfile,
        compatibility: Optional[CompatibilityPrediction]
    ) -> Dict[str, Any]:
        """Personalize a content template with user-specific data"""
        
        personalized_text = template["template"]
        metadata = {
            "template_id": template.get("id"),
            "personalization_factors": []
        }
        
        # Replace variables with personalized content
        for variable in template.get("variables", []):
            replacement = self._get_variable_replacement(
                variable, user_profile, target_profile, compatibility
            )
            personalized_text = personalized_text.replace(f"{{{variable}}}", replacement)
            metadata["personalization_factors"].append({
                "variable": variable,
                "value": replacement
            })
        
        # Calculate confidence score
        confidence = self._calculate_personalization_confidence(
            template, user_profile, target_profile, compatibility
        )
        
        return {
            "text": personalized_text,
            "metadata": metadata,
            "confidence": confidence
        }

    def _get_variable_replacement(
        self,
        variable: str,
        user_profile: UserPersonalizationProfile,
        target_profile: UserPersonalizationProfile,
        compatibility: Optional[CompatibilityPrediction]
    ) -> str:
        """Get appropriate replacement for template variables"""
        
        if variable == "interest":
            interests = target_profile.user.interests or []
            return random.choice(interests) if interests else "exploring new things"
        
        elif variable == "adjective":
            style = user_profile.preferred_communication_style
            adjectives = {
                "casual": ["fun", "exciting", "cool", "awesome"],
                "formal": ["remarkable", "significant", "notable", "impressive"],
                "playful": ["wild", "amazing", "incredible", "fantastic"],
                "balanced": ["interesting", "meaningful", "special", "memorable"]
            }
            return random.choice(adjectives.get(style, adjectives["balanced"]))
        
        elif variable == "trait":
            # Analyze personality traits from AI profile
            if target_profile.user.ai_profile:
                traits = ["creative", "thoughtful", "adventurous", "genuine", "passionate"]
                return random.choice(traits)
            return "authentic"
        
        elif variable == "topic":
            if compatibility and compatibility.compatibility_breakdown:
                common_areas = compatibility.compatibility_breakdown.keys()
                topics = {
                    "values": "personal values",
                    "goals": "life goals", 
                    "interests": "shared interests",
                    "communication": "meaningful connections"
                }
                for area in common_areas:
                    if area in topics:
                        return topics[area]
            return "authentic connections"
        
        return "meaningful experiences"

    def _calculate_personalization_confidence(
        self,
        template: Dict[str, Any],
        user_profile: UserPersonalizationProfile,
        target_profile: UserPersonalizationProfile,
        compatibility: Optional[CompatibilityPrediction]
    ) -> float:
        """Calculate confidence score for personalized content"""
        
        base_confidence = 0.6
        
        # Boost confidence if we have rich user data
        if user_profile.communication_patterns:
            base_confidence += 0.1
        
        if target_profile.user.interests:
            base_confidence += 0.1
        
        if compatibility and compatibility.compatibility_score > 0.7:
            base_confidence += 0.15
        
        if user_profile.content_engagement_scores:
            # Check historical performance for this template type
            template_type = template.get("tone", "general")
            historical_scores = user_profile.content_engagement_scores.get(template_type, [])
            if historical_scores:
                avg_score = sum(historical_scores) / len(historical_scores)
                base_confidence += (avg_score - 0.5) * 0.1
        
        return min(base_confidence, 0.95)

    def _get_fallback_starters(self, count: int) -> List[Dict[str, Any]]:
        """Get fallback conversation starters when personalization fails"""
        fallbacks = [
            {
                "id": None,
                "text": "I'd love to know what makes you genuinely happy. What brings joy to your everyday life?",
                "category": "general",
                "confidence": 0.5,
                "metadata": {"fallback": True}
            },
            {
                "id": None,
                "text": "What's something you're passionate about that you could talk about for hours?",
                "category": "general", 
                "confidence": 0.5,
                "metadata": {"fallback": True}
            },
            {
                "id": None,
                "text": "I'm curious about your perspective on meaningful connections. What makes a conversation truly special for you?",
                "category": "general",
                "confidence": 0.5,
                "metadata": {"fallback": True}
            }
        ]
        
        return fallbacks[:count]

    async def _analyze_initial_user_behavior(
        self,
        user_id: int,
        profile: UserPersonalizationProfile,
        db: Session
    ) -> None:
        """Analyze initial user behavior patterns for new profiles"""
        
        # This would analyze user's activity patterns, response times, etc.
        # For now, setting reasonable defaults that can be updated with real data
        
        profile.communication_patterns = {
            "formality_score": 0.5,
            "enthusiasm_score": 0.6,
            "emotional_openness": 0.5,
            "preferred_depth": 0.6,
            "typical_response_speed": 0.5
        }
        
        profile.engagement_patterns = {
            "peak_activity_hours": [19, 20, 21, 22],  # Evening hours
            "average_session_length": 1800,  # 30 minutes
            "preferred_interaction_frequency": "daily"
        }
        
        profile.topic_preferences = {
            "lifestyle": 0.7,
            "values": 0.8,
            "hobbies": 0.6,
            "goals": 0.7,
            "experiences": 0.8
        }
        
        db.commit()


# Initialize the global personalization engine
personalization_engine = PersonalizationEngine()