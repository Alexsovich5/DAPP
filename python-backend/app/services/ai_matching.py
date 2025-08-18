# AI-Enhanced Matching Service for Dinner First Dating Platform
# Privacy-first local AI processing for semantic compatibility analysis

from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import LatentDirichletAllocation
import re
import json

from ..core.database import get_db
from ..models.user import User
from ..models.profile import Profile
from ..models.match import Match
from ..schemas.matching import CompatibilityAnalysis, ConversationStarter
from ..core.config import settings

logger = logging.getLogger(__name__)

class PrivacyFirstMatchingAI:
    """
    Advanced AI matching system that processes all data locally
    to ensure user privacy while providing sophisticated compatibility analysis
    """
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95
        )
        self.lda_model = LatentDirichletAllocation(
            n_components=10,
            random_state=42,
            max_iter=100
        )
        self.is_initialized = False
        
        # Compatibility weights for different aspects
        self.compatibility_weights = {
            "semantic_similarity": 0.25,
            "communication_style": 0.20,
            "emotional_depth": 0.20,
            "life_goals": 0.15,
            "personality_match": 0.10,
            "interest_overlap": 0.10
        }
        
        # Conversation starter templates
        self.starter_templates = [
            "I noticed we both value {common_value}. What does that mean to you?",
            "Your perspective on {topic} really resonates with me. How did you develop that viewpoint?",
            "We seem to share an interest in {interest}. What draws you to it?",
            "I find your approach to {life_aspect} intriguing. Could you tell me more?",
            "Our compatibility suggests we might have great conversations about {discussion_topic}."
        ]
    
    async def initialize_models(self, db: Session):
        """Initialize AI models with existing user data for better performance"""
        try:
            # Get all user profiles for model training
            profiles = db.query(Profile).filter(
                Profile.life_philosophy.isnot(None),
                Profile.core_values.isnot(None)
            ).all()
            
            if len(profiles) < 10:
                logger.warning("Insufficient data for AI model initialization. Using basic algorithms.")
                self.is_initialized = True
                return
            
            # Prepare text data for training
            profile_texts = []
            for profile in profiles:
                text = self.combine_profile_text_from_profile(profile)
                if text.strip():
                    profile_texts.append(text)
            
            if profile_texts:
                # Train TF-IDF vectorizer
                self.vectorizer.fit(profile_texts)
                
                # Train LDA model for topic modeling
                tfidf_matrix = self.vectorizer.transform(profile_texts)
                self.lda_model.fit(tfidf_matrix)
                
                logger.info(f"AI models initialized with {len(profile_texts)} profiles")
            
            self.is_initialized = True
            
        except Exception as e:
            logger.error(f"Error initializing AI models: {str(e)}")
            self.is_initialized = True  # Continue with basic functionality
    
    def preprocess_text(self, text: str) -> str:
        """Clean and preprocess text for analysis"""
        if not text:
            return ""
        
        # Remove special characters and normalize
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def combine_profile_text_from_profile(self, profile: Profile) -> str:
        """Combine all profile text for semantic analysis"""
        text_components = []
        
        # Add main profile fields
        if profile.life_philosophy:
            text_components.append(profile.life_philosophy)
        
        # Add core values
        if profile.core_values:
            if isinstance(profile.core_values, dict):
                for key, value in profile.core_values.items():
                    if isinstance(value, str):
                        text_components.append(f"{key}: {value}")
                    elif isinstance(value, list):
                        text_components.append(f"{key}: {' '.join(value)}")
        
        # Add interests
        if profile.interests:
            text_components.append(" ".join(profile.interests))
        
        # Add personality traits
        if profile.personality_traits:
            if isinstance(profile.personality_traits, dict):
                for trait, description in profile.personality_traits.items():
                    if isinstance(description, str):
                        text_components.append(f"{trait}: {description}")
        
        # Add communication style
        if profile.communication_style:
            if isinstance(profile.communication_style, dict):
                for style, preference in profile.communication_style.items():
                    if isinstance(preference, str):
                        text_components.append(f"{style}: {preference}")
        
        # Add onboarding responses
        if profile.responses:
            if isinstance(profile.responses, dict):
                for question, response in profile.responses.items():
                    if isinstance(response, str):
                        text_components.append(response)
        
        combined_text = " ".join(filter(None, text_components))
        return self.preprocess_text(combined_text)
    
    def combine_profile_text(self, user: User) -> str:
        """Combine all profile text for semantic analysis"""
        return self.combine_profile_text_from_profile(user.profile)
    
    async def calculate_semantic_similarity(self, user1: User, user2: User) -> float:
        """Calculate semantic similarity between two user profiles"""
        try:
            # Get combined profile texts
            text1 = self.combine_profile_text(user1)
            text2 = self.combine_profile_text(user2)
            
            if not text1 or not text2:
                return 0.0
            
            if not self.is_initialized:
                # Fallback to simple keyword matching
                return self.calculate_keyword_similarity(text1, text2)
            
            # Use TF-IDF vectorization for semantic similarity
            texts = [text1, text2]
            tfidf_matrix = self.vectorizer.transform(texts)
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            return float(similarity_matrix[0, 1])
            
        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {str(e)}")
            return 0.0
    
    def calculate_keyword_similarity(self, text1: str, text2: str) -> float:
        """Fallback method for calculating similarity using keyword overlap"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    async def analyze_communication_compatibility(self, user1: User, user2: User) -> float:
        """Analyze compatibility in communication styles"""
        try:
            comm1 = user1.profile.communication_style or {}
            comm2 = user2.profile.communication_style or {}
            
            if not comm1 or not comm2:
                return 0.5  # Neutral score when data is missing
            
            compatibility_score = 0.0
            total_aspects = 0
            
            # Compare communication preferences
            for aspect in ['preferred_medium', 'conversation_style', 'emotional_expression', 'conflict_resolution']:
                if aspect in comm1 and aspect in comm2:
                    total_aspects += 1
                    pref1 = str(comm1[aspect]).lower()
                    pref2 = str(comm2[aspect]).lower()
                    
                    if pref1 == pref2:
                        compatibility_score += 1.0
                    elif self.are_compatible_preferences(pref1, pref2, aspect):
                        compatibility_score += 0.7
                    else:
                        compatibility_score += 0.3
            
            return compatibility_score / total_aspects if total_aspects > 0 else 0.5
            
        except Exception as e:
            logger.error(f"Error analyzing communication compatibility: {str(e)}")
            return 0.5
    
    def are_compatible_preferences(self, pref1: str, pref2: str, aspect: str) -> bool:
        """Check if two preferences are compatible even if not identical"""
        compatible_pairs = {
            'conversation_style': [
                ('deep', 'thoughtful'),
                ('casual', 'relaxed'),
                ('humorous', 'playful')
            ],
            'emotional_expression': [
                ('open', 'expressive'),
                ('reserved', 'thoughtful'),
                ('balanced', 'moderate')
            ]
        }
        
        if aspect in compatible_pairs:
            for pair in compatible_pairs[aspect]:
                if (pref1 in pair and pref2 in pair):
                    return True
        
        return False
    
    async def analyze_emotional_compatibility(self, user1: User, user2: User) -> float:
        """Analyze emotional depth and compatibility"""
        try:
            # Analyze depth of profile responses
            depth1 = self.calculate_emotional_depth(user1)
            depth2 = self.calculate_emotional_depth(user2)
            
            # Similar emotional depths tend to be more compatible
            depth_difference = abs(depth1 - depth2)
            depth_compatibility = max(0, 1 - depth_difference)
            
            # Analyze emotional expression styles
            personality1 = user1.profile.personality_traits or {}
            personality2 = user2.profile.personality_traits or {}
            
            emotional_style_score = self.compare_emotional_styles(personality1, personality2)
            
            return (depth_compatibility * 0.6 + emotional_style_score * 0.4)
            
        except Exception as e:
            logger.error(f"Error analyzing emotional compatibility: {str(e)}")
            return 0.5
    
    def calculate_emotional_depth(self, user: User) -> float:
        """Calculate the emotional depth of a user's profile"""
        depth_indicators = 0
        total_possible = 0
        
        # Check life philosophy depth
        if user.profile.life_philosophy:
            total_possible += 1
            if len(user.profile.life_philosophy) > 100:
                depth_indicators += 1
        
        # Check response depth
        if user.profile.responses:
            for response in user.profile.responses.values():
                if isinstance(response, str):
                    total_possible += 1
                    if len(response) > 50:
                        depth_indicators += 1
        
        # Check personality trait descriptions
        if user.profile.personality_traits:
            for trait_desc in user.profile.personality_traits.values():
                if isinstance(trait_desc, str):
                    total_possible += 1
                    if len(trait_desc) > 30:
                        depth_indicators += 1
        
        return depth_indicators / total_possible if total_possible > 0 else 0.0
    
    def compare_emotional_styles(self, personality1: dict, personality2: dict) -> float:
        """Compare emotional expression styles between two personalities"""
        if not personality1 or not personality2:
            return 0.5
        
        # Define complementary and compatible traits
        compatible_traits = {
            'introverted': ['thoughtful', 'deep', 'reflective'],
            'extroverted': ['social', 'expressive', 'outgoing'],
            'empathetic': ['caring', 'understanding', 'supportive'],
            'analytical': ['logical', 'structured', 'thoughtful']
        }
        
        compatibility_score = 0.0
        comparisons = 0
        
        for trait1, desc1 in personality1.items():
            for trait2, desc2 in personality2.items():
                comparisons += 1
                
                # Direct match
                if trait1 == trait2:
                    compatibility_score += 1.0
                # Compatible traits
                elif (trait1 in compatible_traits and 
                      any(comp in str(desc2).lower() for comp in compatible_traits[trait1])):
                    compatibility_score += 0.8
                # Complementary traits
                elif self.are_complementary_traits(trait1, trait2):
                    compatibility_score += 0.6
                else:
                    compatibility_score += 0.3
        
        return compatibility_score / comparisons if comparisons > 0 else 0.5
    
    def are_complementary_traits(self, trait1: str, trait2: str) -> bool:
        """Check if two personality traits are complementary"""
        complementary_pairs = [
            ('introverted', 'extroverted'),
            ('spontaneous', 'organized'),
            ('creative', 'analytical'),
            ('adventurous', 'homebody'),
            ('emotional', 'logical')
        ]
        
        trait1_lower = trait1.lower()
        trait2_lower = trait2.lower()
        
        for pair in complementary_pairs:
            if (trait1_lower in pair and trait2_lower in pair and trait1_lower != trait2_lower):
                return True
        
        return False
    
    async def analyze_life_goals_compatibility(self, user1: User, user2: User) -> float:
        """Analyze compatibility in life goals and values"""
        try:
            values1 = user1.profile.core_values or {}
            values2 = user2.profile.core_values or {}
            
            if not values1 or not values2:
                return 0.5
            
            # Extract life goals and important values
            goals1 = self.extract_life_goals(values1, user1.profile.responses or {})
            goals2 = self.extract_life_goals(values2, user2.profile.responses or {})
            
            # Calculate goal alignment
            alignment_score = self.calculate_goal_alignment(goals1, goals2)
            
            return alignment_score
            
        except Exception as e:
            logger.error(f"Error analyzing life goals compatibility: {str(e)}")
            return 0.5
    
    def extract_life_goals(self, core_values: dict, responses: dict) -> List[str]:
        """Extract life goals from core values and responses"""
        goals = []
        
        # Extract from core values
        for key, value in core_values.items():
            if isinstance(value, str):
                goals.append(value.lower())
            elif isinstance(value, list):
                goals.extend([str(v).lower() for v in value])
        
        # Extract from responses that might contain goals
        goal_related_keywords = ['goal', 'want', 'hope', 'dream', 'future', 'aspire', 'achieve']
        for response in responses.values():
            if isinstance(response, str):
                response_lower = response.lower()
                if any(keyword in response_lower for keyword in goal_related_keywords):
                    goals.append(response_lower)
        
        return goals
    
    def calculate_goal_alignment(self, goals1: List[str], goals2: List[str]) -> float:
        """Calculate alignment between two sets of life goals"""
        if not goals1 or not goals2:
            return 0.5
        
        # Define goal categories and their keywords
        goal_categories = {
            'family': ['family', 'children', 'kids', 'marriage', 'parent'],
            'career': ['career', 'job', 'work', 'professional', 'business'],
            'travel': ['travel', 'explore', 'adventure', 'world', 'places'],
            'health': ['health', 'fitness', 'wellness', 'exercise', 'active'],
            'creativity': ['creative', 'art', 'music', 'writing', 'design'],
            'education': ['learn', 'education', 'knowledge', 'study', 'grow'],
            'spirituality': ['spiritual', 'meaning', 'purpose', 'values', 'faith'],
            'community': ['community', 'service', 'help', 'volunteer', 'social']
        }
        
        # Categorize goals
        categories1 = self.categorize_goals(goals1, goal_categories)
        categories2 = self.categorize_goals(goals2, goal_categories)
        
        # Calculate category overlap
        common_categories = set(categories1.keys()).intersection(set(categories2.keys()))
        total_categories = set(categories1.keys()).union(set(categories2.keys()))
        
        if not total_categories:
            return 0.5
        
        alignment_score = len(common_categories) / len(total_categories)
        
        # Boost score for high-priority categories
        priority_boost = 0.0
        high_priority_categories = ['family', 'career', 'spirituality']
        
        for category in high_priority_categories:
            if category in common_categories:
                priority_boost += 0.1
        
        return min(1.0, alignment_score + priority_boost)
    
    def categorize_goals(self, goals: List[str], categories: dict) -> dict:
        """Categorize goals into predefined categories"""
        categorized = {}
        
        for goal in goals:
            for category, keywords in categories.items():
                if any(keyword in goal for keyword in keywords):
                    if category not in categorized:
                        categorized[category] = []
                    categorized[category].append(goal)
        
        return categorized
    
    async def analyze_personality_compatibility(self, user1: User, user2: User) -> float:
        """Analyze overall personality compatibility"""
        try:
            traits1 = user1.profile.personality_traits or {}
            traits2 = user2.profile.personality_traits or {}
            
            if not traits1 or not traits2:
                return 0.5
            
            # Calculate personality similarity and complementarity
            similarity_score = self.calculate_personality_similarity(traits1, traits2)
            complementarity_score = self.calculate_personality_complementarity(traits1, traits2)
            
            # Balance between similarity and complementarity
            return (similarity_score * 0.6 + complementarity_score * 0.4)
            
        except Exception as e:
            logger.error(f"Error analyzing personality compatibility: {str(e)}")
            return 0.5
    
    def calculate_personality_similarity(self, traits1: dict, traits2: dict) -> float:
        """Calculate personality similarity"""
        common_traits = set(traits1.keys()).intersection(set(traits2.keys()))
        
        if not common_traits:
            return 0.0
        
        similarity_sum = 0.0
        for trait in common_traits:
            desc1 = str(traits1[trait]).lower()
            desc2 = str(traits2[trait]).lower()
            
            # Simple text similarity
            words1 = set(desc1.split())
            words2 = set(desc2.split())
            
            if words1 and words2:
                overlap = len(words1.intersection(words2))
                union = len(words1.union(words2))
                similarity_sum += overlap / union
        
        return similarity_sum / len(common_traits)
    
    def calculate_personality_complementarity(self, traits1: dict, traits2: dict) -> float:
        """Calculate how well personalities complement each other"""
        complementary_score = 0.0
        total_comparisons = 0
        
        for trait1, desc1 in traits1.items():
            for trait2, desc2 in traits2.items():
                total_comparisons += 1
                
                if self.are_complementary_traits(trait1, trait2):
                    complementary_score += 1.0
                elif trait1 == trait2:
                    # Same traits can be good too
                    complementary_score += 0.8
                else:
                    complementary_score += 0.2
        
        return complementary_score / total_comparisons if total_comparisons > 0 else 0.5
    
    async def calculate_comprehensive_compatibility(self, user1: User, user2: User) -> Dict[str, Any]:
        """Calculate comprehensive compatibility analysis"""
        try:
            # Calculate individual compatibility aspects
            semantic_similarity = await self.calculate_semantic_similarity(user1, user2)
            communication_compatibility = await self.analyze_communication_compatibility(user1, user2)
            emotional_compatibility = await self.analyze_emotional_compatibility(user1, user2)
            life_goals_compatibility = await self.analyze_life_goals_compatibility(user1, user2)
            personality_compatibility = await self.analyze_personality_compatibility(user1, user2)
            interest_overlap = self.calculate_interest_overlap(user1, user2)
            
            # Calculate weighted overall score
            overall_score = (
                semantic_similarity * self.compatibility_weights["semantic_similarity"] +
                communication_compatibility * self.compatibility_weights["communication_style"] +
                emotional_compatibility * self.compatibility_weights["emotional_depth"] +
                life_goals_compatibility * self.compatibility_weights["life_goals"] +
                personality_compatibility * self.compatibility_weights["personality_match"] +
                interest_overlap * self.compatibility_weights["interest_overlap"]
            )
            
            # Calculate confidence level based on data completeness
            confidence_level = self.calculate_confidence_level(user1, user2)
            
            # Identify unique connection factors
            unique_factors = await self.identify_unique_connection_factors(user1, user2)
            
            return {
                "ai_compatibility_score": round(overall_score * 100, 1),
                "confidence_level": round(confidence_level * 100, 1),
                "compatibility_breakdown": {
                    "semantic_similarity": round(semantic_similarity * 100, 1),
                    "communication_style": round(communication_compatibility * 100, 1),
                    "emotional_depth": round(emotional_compatibility * 100, 1),
                    "life_goals": round(life_goals_compatibility * 100, 1),
                    "personality_match": round(personality_compatibility * 100, 1),
                    "interest_overlap": round(interest_overlap * 100, 1)
                },
                "unique_connection_potential": unique_factors,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating comprehensive compatibility: {str(e)}")
            return {
                "ai_compatibility_score": 50.0,
                "confidence_level": 10.0,
                "compatibility_breakdown": {},
                "unique_connection_potential": [],
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "error": "Analysis failed, using default score"
            }
    
    def calculate_interest_overlap(self, user1: User, user2: User) -> float:
        """Calculate interest overlap using Jaccard similarity"""
        interests1 = set(user1.profile.interests or [])
        interests2 = set(user2.profile.interests or [])
        
        if not interests1 or not interests2:
            return 0.0
        
        intersection = len(interests1.intersection(interests2))
        union = len(interests1.union(interests2))
        
        return intersection / union if union > 0 else 0.0
    
    def calculate_confidence_level(self, user1: User, user2: User) -> float:
        """Calculate confidence level based on profile completeness"""
        def profile_completeness(user: User) -> float:
            score = 0.0
            
            if user.profile.life_philosophy:
                score += 0.2
            if user.profile.core_values:
                score += 0.2
            if user.profile.interests:
                score += 0.2
            if user.profile.personality_traits:
                score += 0.2
            if user.profile.communication_style:
                score += 0.1
            if user.profile.responses:
                score += 0.1
            
            return score
        
        completeness1 = profile_completeness(user1)
        completeness2 = profile_completeness(user2)
        
        return (completeness1 + completeness2) / 2
    
    async def identify_unique_connection_factors(self, user1: User, user2: User) -> List[str]:
        """Identify unique factors that could create strong connections"""
        unique_factors = []
        
        try:
            # Find uncommon shared interests
            interests1 = set(user1.profile.interests or [])
            interests2 = set(user2.profile.interests or [])
            common_interests = interests1.intersection(interests2)
            
            # Define rare interests that create stronger bonds
            rare_interests = {
                'philosophy', 'meditation', 'poetry', 'volunteering', 'astronomy',
                'classical music', 'archaeology', 'linguistics', 'sustainable living'
            }
            
            rare_common = common_interests.intersection(rare_interests)
            if rare_common:
                unique_factors.extend([f"shared passion for {interest}" for interest in rare_common])
            
            # Find complementary personality traits
            traits1 = user1.profile.personality_traits or {}
            traits2 = user2.profile.personality_traits or {}
            
            complementary_pairs = [
                ('introverted', 'extroverted'),
                ('creative', 'analytical'),
                ('spontaneous', 'organized')
            ]
            
            for trait1, trait2 in complementary_pairs:
                if (trait1 in str(traits1).lower() and trait2 in str(traits2).lower()) or \
                   (trait2 in str(traits1).lower() and trait1 in str(traits2).lower()):
                    unique_factors.append(f"complementary {trait1}-{trait2} dynamic")
            
            # Find shared values depth
            values1 = user1.profile.core_values or {}
            values2 = user2.profile.core_values or {}
            
            deep_value_keywords = ['meaning', 'purpose', 'authentic', 'growth', 'compassion']
            
            for keyword in deep_value_keywords:
                if (any(keyword in str(v).lower() for v in values1.values()) and
                    any(keyword in str(v).lower() for v in values2.values())):
                    unique_factors.append(f"shared commitment to {keyword}")
            
            return unique_factors[:3]  # Return top 3 unique factors
            
        except Exception as e:
            logger.error(f"Error identifying unique connection factors: {str(e)}")
            return []
    
    async def generate_conversation_starters(self, user1: User, user2: User) -> List[str]:
        """Generate personalized conversation starters based on compatibility analysis"""
        try:
            compatibility = await self.calculate_comprehensive_compatibility(user1, user2)
            starters = []
            
            # Find common interests
            interests1 = set(user1.profile.interests or [])
            interests2 = set(user2.profile.interests or [])
            common_interests = list(interests1.intersection(interests2))
            
            # Interest-based starters
            if common_interests:
                interest = common_interests[0]
                starters.append(f"I noticed we both enjoy {interest}. What drew you to it?")
            
            # Value-based starters
            breakdown = compatibility.get("compatibility_breakdown", {})
            if breakdown.get("life_goals", 0) > 70:
                starters.append("Our life perspectives seem quite aligned. What's a goal you're excited about right now?")
            
            # Communication style starters
            if breakdown.get("communication_style", 0) > 70:
                starters.append("I have a feeling we'd have great conversations. What's something you've been thinking about lately?")
            
            # Unique factor starters
            unique_factors = compatibility.get("unique_connection_potential", [])
            if unique_factors:
                factor = unique_factors[0]
                starters.append(f"I'm curious about your perspective on {factor.replace('shared ', '').replace('commitment to ', '')}.")
            
            # Personality-based starters
            if breakdown.get("personality_match", 0) > 60:
                starters.append("Your approach to life seems really thoughtful. How do you typically navigate important decisions?")
            
            # Default thoughtful starter
            if not starters:
                starters.append("I'd love to hear more about what makes you feel most fulfilled in life.")
            
            return starters[:3]  # Return top 3 starters
            
        except Exception as e:
            logger.error(f"Error generating conversation starters: {str(e)}")
            return ["I'd love to get to know you better. What's something you're passionate about?"]

# Global instance
ai_matching_service = PrivacyFirstMatchingAI()

async def get_ai_matching_service() -> PrivacyFirstMatchingAI:
    """Get the AI matching service instance"""
    return ai_matching_service