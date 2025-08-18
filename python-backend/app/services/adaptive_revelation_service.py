"""
Phase 6: Adaptive Revelation Prompts System
Intelligent, context-aware revelation prompt generation based on user behavior and connection dynamics
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import random
import math
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.user import User
from app.models.soul_connection import SoulConnection
from app.models.daily_revelation import DailyRevelation
from app.models.personalization_models import (
    UserPersonalizationProfile, PersonalizedContent, ContentFeedback,
    ConversationFlowAnalytics, ContentType, PersonalizationStrategy
)
from app.services.personalization_service import personalization_engine

logger = logging.getLogger(__name__)


class AdaptiveRevelationEngine:
    """
    Advanced AI-powered revelation prompt generation system
    Creates personalized, adaptive prompts based on user behavior and connection context
    """
    
    def __init__(self):
        self.revelation_themes = self._load_revelation_themes()
        self.adaptive_weights = {
            "user_personality": 0.25,
            "connection_compatibility": 0.20,
            "conversation_flow": 0.20,
            "emotional_state": 0.15,
            "timing_patterns": 0.10,
            "previous_engagement": 0.10
        }
        
        # Revelation depth progression over 7-day cycle
        self.depth_progression = {
            1: {"depth": "light", "emotional_intensity": 0.3},
            2: {"depth": "medium", "emotional_intensity": 0.4},
            3: {"depth": "medium", "emotional_intensity": 0.5},
            4: {"depth": "medium-deep", "emotional_intensity": 0.6},
            5: {"depth": "deep", "emotional_intensity": 0.7},
            6: {"depth": "deep", "emotional_intensity": 0.8},
            7: {"depth": "profound", "emotional_intensity": 0.9}
        }

    async def generate_adaptive_revelation_prompts(
        self,
        user_id: int,
        connection_id: int,
        revelation_day: int,
        count: int = 3,
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """
        Generate adaptive revelation prompts based on comprehensive user analysis
        """
        try:
            # Get user and connection context
            user = db.query(User).filter(User.id == user_id).first()
            connection = db.query(SoulConnection).filter(SoulConnection.id == connection_id).first()
            
            if not user or not connection:
                return self._get_fallback_prompts(revelation_day, count)
            
            # Get comprehensive user context
            context = await self._build_revelation_context(user, connection, revelation_day, db)
            
            # Generate personalized prompts
            prompts = []
            for i in range(count):
                prompt = await self._generate_single_adaptive_prompt(
                    context, revelation_day, i, db
                )
                if prompt:
                    prompts.append(prompt)
            
            # Ensure we have enough prompts
            while len(prompts) < count:
                fallback = self._get_fallback_prompts(revelation_day, 1)[0]
                prompts.append(fallback)
            
            return prompts[:count]
            
        except Exception as e:
            logger.error(f"Error generating adaptive revelation prompts: {str(e)}")
            return self._get_fallback_prompts(revelation_day, count)

    async def _build_revelation_context(
        self,
        user: User,
        connection: SoulConnection,
        revelation_day: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        Build comprehensive context for revelation prompt generation
        """
        # Get personalization profile
        personalization_profile = await personalization_engine.get_or_create_personalization_profile(
            user.id, db
        )
        
        # Get partner information
        partner_id = connection.user2_id if connection.user1_id == user.id else connection.user1_id
        partner = db.query(User).filter(User.id == partner_id).first()
        
        # Get previous revelations
        previous_revelations = db.query(DailyRevelation).filter(
            and_(
                DailyRevelation.user_id == user.id,
                DailyRevelation.connection_id == connection.id,
                DailyRevelation.day_number < revelation_day
            )
        ).order_by(DailyRevelation.day_number.desc()).limit(5).all()
        
        # Get conversation flow analytics
        flow_analytics = db.query(ConversationFlowAnalytics).filter(
            and_(
                ConversationFlowAnalytics.user_id == user.id,
                ConversationFlowAnalytics.connection_id == connection.id
            )
        ).order_by(ConversationFlowAnalytics.analysis_date.desc()).first()
        
        # Analyze user's revelation patterns
        revelation_patterns = await self._analyze_user_revelation_patterns(user.id, db)
        
        # Get timing preferences
        timing_analysis = await self._analyze_optimal_timing(user.id, db)
        
        return {
            "user": user,
            "partner": partner,
            "connection": connection,
            "personalization_profile": personalization_profile,
            "revelation_day": revelation_day,
            "depth_settings": self.depth_progression[revelation_day],
            "previous_revelations": previous_revelations,
            "flow_analytics": flow_analytics,
            "revelation_patterns": revelation_patterns,
            "timing_analysis": timing_analysis,
            "compatibility_score": connection.compatibility_score or 0.7,
            "connection_stage": connection.connection_stage or "soul_discovery"
        }

    async def _generate_single_adaptive_prompt(
        self,
        context: Dict[str, Any],
        revelation_day: int,
        variation_index: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        Generate a single adaptive revelation prompt based on context
        """
        # Select appropriate theme based on day and user preferences
        theme = self._select_optimal_theme(context, revelation_day, variation_index)
        
        # Get base template for the theme
        base_template = self._get_base_template(theme, revelation_day)
        
        # Personalize the template
        personalized_prompt = await self._personalize_revelation_template(
            base_template, context, theme
        )
        
        # Calculate confidence score
        confidence = self._calculate_prompt_confidence(personalized_prompt, context)
        
        # Create and store the prompt
        prompt_content = PersonalizedContent(
            user_profile_id=context["personalization_profile"].id,
            target_user_id=context["partner"].id,
            content_type=ContentType.REVELATION_PROMPT.value,
            content_text=personalized_prompt["text"],
            content_metadata=personalized_prompt["metadata"],
            generation_strategy=PersonalizationStrategy.BEHAVIORAL_ANALYSIS.value,
            generation_context={
                "revelation_day": revelation_day,
                "theme": theme,
                "variation_index": variation_index,
                "compatibility_score": context["compatibility_score"],
                "connection_stage": context["connection_stage"]
            },
            ai_confidence_score=confidence
        )
        
        db.add(prompt_content)
        db.commit()
        
        return {
            "id": prompt_content.id,
            "text": personalized_prompt["text"],
            "theme": theme,
            "focus": personalized_prompt["focus"],
            "emotional_depth": context["depth_settings"]["depth"],
            "confidence": confidence,
            "metadata": personalized_prompt["metadata"],
            "timing_recommendation": self._get_timing_recommendation(context),
            "follow_up_suggestions": self._generate_follow_up_suggestions(theme, context)
        }

    def _select_optimal_theme(
        self,
        context: Dict[str, Any],
        revelation_day: int,
        variation_index: int
    ) -> str:
        """
        Select the most appropriate revelation theme based on context analysis
        """
        available_themes = self.revelation_themes[revelation_day]
        user_preferences = context["personalization_profile"].topic_preferences or {}
        
        # Score each theme based on user preferences and context
        theme_scores = {}
        for theme_name, theme_data in available_themes.items():
            score = 0.0
            
            # User preference alignment
            if theme_name in user_preferences:
                score += user_preferences[theme_name] * 0.4
            
            # Compatibility with partner
            compatibility_bonus = context["compatibility_score"] * 0.3
            if theme_data.get("requires_high_compatibility", False) and compatibility_bonus < 0.6:
                score -= 0.2
            else:
                score += compatibility_bonus * 0.2
            
            # Previous revelation analysis
            previous_themes = [rev.revelation_type for rev in context["previous_revelations"]]
            if theme_name not in previous_themes:
                score += 0.2  # Bonus for variety
            else:
                score -= 0.1  # Penalty for repetition
            
            # Communication style compatibility
            comm_style = context["personalization_profile"].preferred_communication_style
            if theme_data.get("communication_style") == comm_style:
                score += 0.3
            
            theme_scores[theme_name] = score
        
        # Select theme with highest score, with some randomness for variation
        sorted_themes = sorted(theme_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Use variation_index to add controlled randomness
        if variation_index == 0:
            return sorted_themes[0][0]  # Best match
        elif variation_index == 1 and len(sorted_themes) > 1:
            return sorted_themes[1][0]  # Second best
        else:
            # Weighted random selection from top themes
            top_themes = sorted_themes[:3]
            weights = [score for _, score in top_themes]
            total_weight = sum(weights)
            if total_weight > 0:
                weights = [w/total_weight for w in weights]
                return random.choices([theme for theme, _ in top_themes], weights=weights)[0]
            else:
                return sorted_themes[0][0]

    def _get_base_template(self, theme: str, revelation_day: int) -> Dict[str, Any]:
        """
        Get base template for the selected theme and day
        """
        day_themes = self.revelation_themes.get(revelation_day, {})
        theme_data = day_themes.get(theme, {})
        
        if not theme_data or not theme_data.get("templates"):
            # Fallback to a generic template
            return {
                "template": "Share something meaningful about {topic} and how it has shaped who you are today.",
                "variables": ["topic"],
                "focus": "personal_growth",
                "tone": "reflective"
            }
        
        # Select template variation
        templates = theme_data["templates"]
        return random.choice(templates)

    async def _personalize_revelation_template(
        self,
        base_template: Dict[str, Any],
        context: Dict[str, Any],
        theme: str
    ) -> Dict[str, Any]:
        """
        Personalize revelation template based on user context
        """
        personalized_text = base_template["template"]
        metadata = {
            "theme": theme,
            "base_template_id": base_template.get("id"),
            "personalization_factors": []
        }
        
        # Replace template variables with personalized content
        for variable in base_template.get("variables", []):
            replacement = self._get_variable_replacement(
                variable, context, theme, base_template
            )
            personalized_text = personalized_text.replace(f"{{{variable}}}", replacement)
            metadata["personalization_factors"].append({
                "variable": variable,
                "value": replacement
            })
        
        # Adjust tone based on user's communication style
        personalized_text = self._adjust_tone_for_user(
            personalized_text, context["personalization_profile"], base_template
        )
        
        # Add contextual elements based on connection progress
        personalized_text = self._add_contextual_elements(
            personalized_text, context
        )
        
        return {
            "text": personalized_text,
            "focus": base_template.get("focus", "general"),
            "metadata": metadata
        }

    def _get_variable_replacement(
        self,
        variable: str,
        context: Dict[str, Any],
        theme: str,
        template: Dict[str, Any]
    ) -> str:
        """
        Get appropriate replacement for template variables
        """
        user = context["user"]
        partner = context["partner"]
        revelation_day = context["revelation_day"]
        
        if variable == "topic":
            # Select topic based on theme and user interests
            user_interests = user.interests or []
            if theme == "passions_and_dreams":
                topics = ["your biggest dream", "something you're passionate about", "a goal that drives you"]
            elif theme == "meaningful_memories":
                topics = ["a moment that changed you", "a memory you treasure", "an experience that taught you something important"]
            elif theme == "values_and_beliefs":
                topics = ["what matters most to you", "a value you hold dear", "something you believe strongly in"]
            elif theme == "personal_growth":
                topics = ["a challenge you've overcome", "how you've grown recently", "a lesson life taught you"]
            else:
                topics = ["something meaningful to you", "what makes you unique", "your perspective on life"]
            
            # Personalize topic selection based on user data
            if user_interests:
                relevant_interests = [interest for interest in user_interests if len(interest) > 3]
                if relevant_interests:
                    topics.extend([f"your interest in {interest}" for interest in relevant_interests[:2]])
            
            return random.choice(topics)
        
        elif variable == "connection_context":
            compatibility = context["compatibility_score"]
            if compatibility > 0.8:
                return "given how connected we seem to be"
            elif compatibility > 0.6:
                return "as we're getting to know each other better"
            else:
                return "as we explore this connection"
        
        elif variable == "depth_indicator":
            depth = context["depth_settings"]["depth"]
            if depth in ["deep", "profound"]:
                return "something deeply personal"
            elif depth == "medium-deep":
                return "something meaningful"
            else:
                return "something important"
        
        elif variable == "partner_name":
            return partner.first_name if partner and partner.first_name else "you"
        
        elif variable == "timeframe":
            if revelation_day <= 3:
                return "recently"
            elif revelation_day <= 5:
                return "in your life"
            else:
                return "throughout your journey"
        
        return "something special"

    def _adjust_tone_for_user(
        self,
        text: str,
        profile: UserPersonalizationProfile,
        template: Dict[str, Any]
    ) -> str:
        """
        Adjust the tone of the revelation prompt based on user's communication style
        """
        user_style = profile.preferred_communication_style
        base_tone = template.get("tone", "neutral")
        
        # Style-specific adjustments
        if user_style == "casual":
            # Make it more conversational
            text = text.replace("Share something", "Tell me about something")
            text = text.replace("Describe", "What's")
            if not text.endswith("?"):
                text = text.rstrip(".") + "?"
        
        elif user_style == "formal":
            # Make it more structured
            if not text.startswith("I would love to"):
                text = "I would love to know: " + text.lower()
        
        elif user_style == "playful":
            # Add warmth and curiosity
            playful_starters = [
                "I'm curious - ",
                "Here's something I'd love to know about you: ",
                "Share with me "
            ]
            if not any(text.startswith(starter) for starter in playful_starters):
                text = random.choice(playful_starters) + text.lower()
        
        return text

    def _add_contextual_elements(
        self,
        text: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Add contextual elements based on connection progress and compatibility
        """
        revelation_day = context["revelation_day"]
        compatibility = context["compatibility_score"]
        connection_stage = context["connection_stage"]
        
        # Add day-specific context
        if revelation_day == 1:
            if "first" not in text.lower():
                text = f"For our first revelation: {text}"
        elif revelation_day == 7:
            text = f"For our final revelation before we potentially meet: {text}"
        elif revelation_day >= 5:
            if compatibility > 0.7:
                text = f"As we've been connecting so well: {text}"
        
        # Add connection stage context
        if connection_stage == "deeper_connection" and revelation_day >= 4:
            if "connection" not in text.lower():
                text = text + " I feel like we're really starting to understand each other."
        
        return text

    def _calculate_prompt_confidence(
        self,
        personalized_prompt: Dict[str, Any],
        context: Dict[str, Any]
    ) -> float:
        """
        Calculate confidence score for the generated prompt
        """
        base_confidence = 0.7
        
        # Boost confidence based on personalization depth
        personalization_factors = personalized_prompt["metadata"].get("personalization_factors", [])
        if len(personalization_factors) >= 3:
            base_confidence += 0.1
        
        # Boost based on user data richness
        profile = context["personalization_profile"]
        if profile.communication_patterns:
            base_confidence += 0.05
        if profile.topic_preferences:
            base_confidence += 0.05
        
        # Boost based on compatibility
        compatibility = context["compatibility_score"]
        if compatibility > 0.8:
            base_confidence += 0.1
        elif compatibility > 0.6:
            base_confidence += 0.05
        
        # Reduce confidence for early days with limited data
        if context["revelation_day"] <= 2 and not context["previous_revelations"]:
            base_confidence -= 0.1
        
        return min(base_confidence, 0.95)

    def _get_timing_recommendation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate timing recommendation for the revelation
        """
        timing_analysis = context.get("timing_analysis", {})
        user_patterns = context["personalization_profile"].engagement_patterns or {}
        
        # Get optimal hours from user patterns
        peak_hours = user_patterns.get("peak_activity_hours", [19, 20, 21])
        
        return {
            "recommended_hours": peak_hours,
            "optimal_day_time": "evening",
            "reasoning": "Based on your typical engagement patterns",
            "urgency": "moderate"
        }

    def _generate_follow_up_suggestions(
        self,
        theme: str,
        context: Dict[str, Any]
    ) -> List[str]:
        """
        Generate follow-up conversation suggestions
        """
        suggestions = []
        
        if theme == "meaningful_memories":
            suggestions = [
                "What made that moment so special?",
                "How did that experience change you?",
                "Do you have other memories like that?"
            ]
        elif theme == "values_and_beliefs":
            suggestions = [
                "What shaped that belief for you?",
                "How do you live that value daily?",
                "Has that ever been challenged?"
            ]
        elif theme == "personal_growth":
            suggestions = [
                "What did that teach you about yourself?",
                "How has that growth affected your relationships?",
                "What advice would you give to someone facing something similar?"
            ]
        else:
            suggestions = [
                "That's really meaningful - tell me more",
                "How has that influenced who you are today?",
                "What would you want others to know about that?"
            ]
        
        return suggestions[:2]  # Return top 2 suggestions

    async def _analyze_user_revelation_patterns(
        self,
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        Analyze user's revelation sharing patterns for optimization
        """
        revelations = db.query(DailyRevelation).filter(
            DailyRevelation.user_id == user_id
        ).order_by(DailyRevelation.created_at.desc()).limit(20).all()
        
        if not revelations:
            return {"pattern": "new_user", "preferences": {}}
        
        # Analyze revelation types and engagement
        type_counts = {}
        avg_length = 0
        
        for rev in revelations:
            rev_type = rev.revelation_type or "general"
            type_counts[rev_type] = type_counts.get(rev_type, 0) + 1
            avg_length += len(rev.content or "") / len(revelations)
        
        preferred_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "pattern": "established_user",
            "preferred_types": [t[0] for t in preferred_types[:3]],
            "average_length": avg_length,
            "total_revelations": len(revelations),
            "engagement_trend": "increasing" if len(revelations) >= 10 else "developing"
        }

    async def _analyze_optimal_timing(
        self,
        user_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        Analyze optimal timing patterns for the user
        """
        # This would analyze when user typically engages with revelations
        # For now, returning default patterns
        return {
            "optimal_hours": [19, 20, 21, 22],
            "best_days": ["monday", "wednesday", "friday"],
            "response_time_pattern": "evening_responder"
        }

    def _load_revelation_themes(self) -> Dict[int, Dict[str, Any]]:
        """
        Load revelation themes and templates for each day
        """
        return {
            1: {
                "simple_joy": {
                    "templates": [
                        {
                            "template": "What's something that always brings a genuine smile to your face? {depth_indicator} about a source of joy in your life.",
                            "variables": ["depth_indicator"],
                            "focus": "happiness",
                            "tone": "warm"
                        }
                    ],
                    "communication_style": "casual",
                    "requires_high_compatibility": False
                },
                "personal_values": {
                    "templates": [
                        {
                            "template": "Share {depth_indicator} about what matters most to you in life and why it's become so important.",
                            "variables": ["depth_indicator"],
                            "focus": "values",
                            "tone": "reflective"
                        }
                    ],
                    "communication_style": "balanced",
                    "requires_high_compatibility": False
                }
            },
            2: {
                "meaningful_memories": {
                    "templates": [
                        {
                            "template": "Tell me about a moment when you felt truly understood by someone. What made that experience so special {connection_context}?",
                            "variables": ["connection_context"],
                            "focus": "connection_memory",
                            "tone": "intimate"
                        }
                    ],
                    "communication_style": "balanced",
                    "requires_high_compatibility": False
                },
                "personal_growth": {
                    "templates": [
                        {
                            "template": "Describe a time when you discovered something new about yourself. How did that realization change your perspective {timeframe}?",
                            "variables": ["timeframe"],
                            "focus": "self_discovery",
                            "tone": "curious"
                        }
                    ]
                }
            },
            3: {
                "passions_and_dreams": {
                    "templates": [
                        {
                            "template": "What's a dream or goal that excites you when you think about it? Share what draws you to {topic} and what it means to you.",
                            "variables": ["topic"],
                            "focus": "aspirations",
                            "tone": "enthusiastic"
                        }
                    ]
                },
                "vulnerability_sharing": {
                    "templates": [
                        {
                            "template": "Share a moment when you had to be brave or step outside your comfort zone. What did you learn about yourself in that experience?",
                            "variables": [],
                            "focus": "courage",
                            "tone": "supportive"
                        }
                    ],
                    "requires_high_compatibility": True
                }
            },
            # Continue for days 4-7...
            4: {
                "deeper_connections": {
                    "templates": [
                        {
                            "template": "What does authentic connection mean to you? Share your thoughts on what makes relationships truly meaningful {connection_context}.",
                            "variables": ["connection_context"],
                            "focus": "relationship_philosophy",
                            "tone": "thoughtful"
                        }
                    ],
                    "requires_high_compatibility": True
                }
            },
            5: {
                "profound_moments": {
                    "templates": [
                        {
                            "template": "Describe a moment that fundamentally changed how you see the world or yourself. What wisdom did you gain from that experience?",
                            "variables": [],
                            "focus": "transformation",
                            "tone": "profound"
                        }
                    ],
                    "requires_high_compatibility": True
                }
            },
            6: {
                "soul_essence": {
                    "templates": [
                        {
                            "template": "If you could share the essence of who you are in your most authentic moment, what would you want {partner_name} to understand about your soul?",
                            "variables": ["partner_name"],
                            "focus": "authentic_self",
                            "tone": "intimate"
                        }
                    ],
                    "requires_high_compatibility": True
                }
            },
            7: {
                "future_together": {
                    "templates": [
                        {
                            "template": "As we approach the possibility of meeting in person, what are you most excited about discovering when we share the same space?",
                            "variables": [],
                            "focus": "anticipation",
                            "tone": "hopeful"
                        }
                    ],
                    "requires_high_compatibility": True
                }
            }
        }

    def _get_fallback_prompts(self, revelation_day: int, count: int) -> List[Dict[str, Any]]:
        """
        Get fallback revelation prompts when personalization fails
        """
        fallback_prompts = {
            1: [
                {
                    "id": None,
                    "text": "Share something that brings you genuine joy and explain why it resonates with your soul.",
                    "theme": "simple_joy",
                    "focus": "happiness",
                    "emotional_depth": "light",
                    "confidence": 0.5,
                    "metadata": {"fallback": True}
                }
            ],
            2: [
                {
                    "id": None,
                    "text": "Describe a moment when you felt truly understood by someone. What made it special?",
                    "theme": "meaningful_memories", 
                    "focus": "connection_memory",
                    "emotional_depth": "medium",
                    "confidence": 0.5,
                    "metadata": {"fallback": True}
                }
            ],
            # Add more fallback prompts for other days...
        }
        
        day_prompts = fallback_prompts.get(revelation_day, fallback_prompts[1])
        return (day_prompts * count)[:count]


# Initialize the global adaptive revelation engine
adaptive_revelation_engine = AdaptiveRevelationEngine()