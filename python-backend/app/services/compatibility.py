from typing import List, Dict, Any, Tuple
import re
from datetime import datetime


class CompatibilityCalculator:
    """
    Local compatibility algorithms for Soul Before Skin matching.
    All processing done locally without external API dependencies.
    Target processing time: <500ms
    """
    
    def __init__(self):
        self.weights = {
            "interests": 0.25,
            "values": 0.30,
            "demographics": 0.20,
            "communication": 0.15,
            "personality": 0.10
        }
        
        # Value keywords for semantic matching
        self.value_keywords = {
            "relationship_values": {
                "commitment": ["loyal", "faithful", "dedicated", "devoted", "committed", "stable"],
                "growth": ["learn", "improve", "develop", "evolve", "grow", "better"],
                "adventure": ["explore", "travel", "new", "experience", "adventure", "exciting"],
                "stability": ["secure", "steady", "reliable", "consistent", "stable", "safe"],
                "independence": ["free", "independent", "space", "individual", "autonomous"],
                "family": ["family", "children", "kids", "marriage", "home", "domestic"]
            },
            "connection_style": {
                "deep_talks": ["meaningful", "deep", "philosophy", "soul", "profound", "spiritual"],
                "shared_activities": ["together", "activities", "hobbies", "fun", "shared", "do"],
                "quality_time": ["present", "attention", "focus", "listen", "time", "together"],
                "physical_affection": ["touch", "affection", "close", "intimate", "physical", "hug"]
            }
        }

    def calculate_interest_similarity(self, user1_interests: List[str], user2_interests: List[str]) -> float:
        """
        Calculate Jaccard similarity coefficient for interests overlap.
        Returns: 0.0 to 1.0 (higher = more similar)
        """
        if not user1_interests or not user2_interests:
            return 0.0
            
        # Convert to lowercase sets for case-insensitive comparison
        set1 = set([interest.lower().strip() for interest in user1_interests])
        set2 = set([interest.lower().strip() for interest in user2_interests])
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        if union == 0:
            return 0.0
        
        return intersection / union

    def calculate_values_compatibility(self, user1_responses: Dict, user2_responses: Dict) -> float:
        """
        Compare responses to core values questions using keyword matching.
        Returns: 0.0 to 1.0 based on shared values alignment
        """
        if not user1_responses or not user2_responses:
            return 0.0
            
        compatibility_scores = []
        
        for question_key in user1_responses.keys():
            if question_key in user2_responses:
                score = self._compare_response_values(
                    user1_responses[question_key],
                    user2_responses[question_key],
                    self.value_keywords.get(question_key, {})
                )
                compatibility_scores.append(score)
        
        return sum(compatibility_scores) / len(compatibility_scores) if compatibility_scores else 0.0

    def _compare_response_values(self, response1: str, response2: str, keywords: Dict) -> float:
        """
        Compare two text responses using keyword matching.
        Returns: 0.0 to 1.0 based on shared value indicators
        """
        if not response1 or not response2:
            return 0.0
            
        # Convert to lowercase for comparison
        resp1_lower = response1.lower()
        resp2_lower = response2.lower()
        
        # Find matching value categories
        user1_values = set()
        user2_values = set()
        
        for value_category, keyword_list in keywords.items():
            for keyword in keyword_list:
                if keyword in resp1_lower:
                    user1_values.add(value_category)
                if keyword in resp2_lower:
                    user2_values.add(value_category)
        
        # Calculate overlap
        if not user1_values and not user2_values:
            return 0.5  # Neutral if no keywords found
        
        intersection = len(user1_values.intersection(user2_values))
        union = len(user1_values.union(user2_values))
        
        return intersection / union if union > 0 else 0.0

    def calculate_age_compatibility(self, age1: int, age2: int) -> float:
        """
        Age compatibility with bell curve - optimal within 5 years.
        Returns: 0.0 to 1.0 based on age difference
        """
        age_diff = abs(age1 - age2)
        
        if age_diff == 0:
            return 1.0
        elif age_diff <= 2:
            return 0.9
        elif age_diff <= 5:
            return 0.8
        elif age_diff <= 8:
            return 0.6
        elif age_diff <= 12:
            return 0.4
        else:
            return 0.2

    def calculate_location_compatibility(self, location1, location2) -> float:
        """
        Calculate location compatibility supporting both string and dict formats.
        Returns: 0.0 to 1.0 based on location similarity
        """
        if not location1 or not location2:
            return 0.5  # Neutral if location not provided
        
        # Handle dictionary format
        if isinstance(location1, dict) and isinstance(location2, dict):
            # Same city check
            if (location1.get("city") and location2.get("city") and 
                location1["city"].lower() == location2["city"].lower()):
                return 1.0
            
            # Same state check
            if (location1.get("state") and location2.get("state") and 
                location1["state"].lower() == location2["state"].lower()):
                return 0.8
            
            # Same country check
            if (location1.get("country") and location2.get("country") and 
                location1["country"].lower() == location2["country"].lower()):
                return 0.4
            
            return 0.2  # Different countries
        
        # Handle string format (legacy support)
        if isinstance(location1, str) and isinstance(location2, str):
            loc1_lower = location1.lower().strip()
            loc2_lower = location2.lower().strip()
            
            # Exact match
            if loc1_lower == loc2_lower:
                return 1.0
            
            # City match (assuming format: "City, State")
            city1 = loc1_lower.split(',')[0].strip()
            city2 = loc2_lower.split(',')[0].strip()
            
            if city1 == city2:
                return 0.9
            
            # State match
            if ',' in loc1_lower and ',' in loc2_lower:
                state1 = loc1_lower.split(',')[-1].strip()
                state2 = loc2_lower.split(',')[-1].strip()
                if state1 == state2:
                    return 0.6
            
            return 0.3  # Different locations but willing to consider
        
        return 0.5  # Mixed format or invalid data

    def calculate_demographic_compatibility(self, user1, user2) -> float:
        """
        Calculate compatibility based on age and location.
        Supports both dict and object formats.
        Returns: 0.0 to 1.0 based on demographic alignment
        """
        age_score = 0.5  # Default if age not available
        location_score = 0.5  # Default if location not available
        
        # Handle both dict and object formats for user data
        if isinstance(user1, dict):
            user1_age = user1.get('age')
            user1_location = user1.get('location')
        else:
            user1_age = getattr(user1, 'age', None)
            user1_location = getattr(user1, 'location', None)
        
        if isinstance(user2, dict):
            user2_age = user2.get('age')
            user2_location = user2.get('location')
        else:
            user2_age = getattr(user2, 'age', None)
            user2_location = getattr(user2, 'location', None)
        
        # Calculate age compatibility
        if user1_age and user2_age:
            age_score = self.calculate_age_compatibility(user1_age, user2_age)
        
        # Calculate location compatibility
        if user1_location and user2_location:
            location_score = self.calculate_location_compatibility(user1_location, user2_location)
        
        return (age_score * 0.4) + (location_score * 0.6)

    def calculate_overall_compatibility(self, user1, user2) -> Dict[str, Any]:
        """
        Calculate comprehensive compatibility score between two users.
        Supports both dict and object formats.
        
        Returns:
            Dict with total compatibility, breakdown, and match quality
        """
        # Extract data from user objects or dicts
        if hasattr(user1, 'emotional_profile'):
            user1_interests = user1.emotional_profile.interests
            user1_values = user1.emotional_profile.core_values
        else:
            user1_interests = user1.get('interests', []) if isinstance(user1, dict) else []
            user1_values = user1.get('core_values', {}) if isinstance(user1, dict) else {}
        
        if hasattr(user2, 'emotional_profile'):
            user2_interests = user2.emotional_profile.interests
            user2_values = user2.emotional_profile.core_values
        else:
            user2_interests = user2.get('interests', []) if isinstance(user2, dict) else []
            user2_values = user2.get('core_values', {}) if isinstance(user2, dict) else {}
        
        # Calculate individual scores
        interest_score = self.calculate_interest_similarity(user1_interests, user2_interests)
        values_score = self.calculate_values_compatibility(user1_values, user2_values)
        demographic_score = self.calculate_demographic_compatibility(user1, user2)
        
        # For MVP, simplified communication and personality scoring
        communication_score = 0.7  # Default moderate compatibility
        personality_score = 0.6   # Default moderate compatibility
        
        # Calculate weighted total
        total_score = (
            interest_score * self.weights["interests"] +
            values_score * self.weights["values"] +
            demographic_score * self.weights["demographics"] +
            communication_score * self.weights["communication"] +
            personality_score * self.weights["personality"]
        )
        
        return {
            "total_compatibility": round(total_score * 100, 1),
            "breakdown": {
                "interests": round(interest_score * 100, 1),
                "values": round(values_score * 100, 1),
                "demographics": round(demographic_score * 100, 1),
                "communication": round(communication_score * 100, 1),
                "personality": round(personality_score * 100, 1)
            },
            "match_quality": self.get_match_quality_label(total_score),
            "explanation": self._generate_compatibility_explanation(
                total_score, interest_score, values_score, demographic_score
            )
        }

    def get_match_quality_label(self, score: float) -> str:
        """Convert compatibility score to descriptive label."""
        if score >= 0.85:
            return "excellent"
        elif score >= 0.70:
            return "very_good"
        elif score >= 0.55:
            return "good"
        elif score >= 0.40:
            return "fair"
        else:
            return "poor"

    def _generate_compatibility_explanation(self, total: float, interests: float, values: float, demographics: float) -> str:
        """Generate human-readable explanation of compatibility."""
        explanations = []
        
        if interests >= 0.7:
            explanations.append("shared interests create natural conversation topics")
        elif interests >= 0.4:
            explanations.append("some common interests provide connection points")
        
        if values >= 0.7:
            explanations.append("strong alignment in core values and relationship goals")
        elif values >= 0.4:
            explanations.append("compatible values foundation for deeper connection")
        
        if demographics >= 0.7:
            explanations.append("well-matched in lifestyle and location preferences")
        
        if not explanations:
            explanations.append("potential for discovering unexpected connections")
        
        return "This match shows " + " and ".join(explanations) + "."

    def calculate_personality_compatibility(self, traits1: Dict, traits2: Dict) -> float:
        """
        Calculate personality compatibility based on trait differences.
        Returns: 0.0 to 1.0 based on personality alignment
        """
        if not traits1 or not traits2:
            return 0.0
        
        # Find common traits
        common_traits = set(traits1.keys()).intersection(set(traits2.keys()))
        if not common_traits:
            return 0.0
        
        # Calculate compatibility for each common trait
        trait_scores = []
        for trait in common_traits:
            # Calculate similarity (1 - absolute difference)
            diff = abs(traits1[trait] - traits2[trait])
            similarity = 1.0 - diff
            trait_scores.append(similarity)
        
        return sum(trait_scores) / len(trait_scores)

    def calculate_communication_compatibility(self, style1: Dict, style2: Dict) -> float:
        """
        Calculate communication style compatibility.
        Returns: 0.0 to 1.0 based on communication alignment
        """
        if not style1 or not style2:
            return 0.0
        
        compatibility_scores = []
        
        # Numeric style comparisons
        numeric_styles = ["directness", "emotional_expression"]
        for style in numeric_styles:
            if style in style1 and style in style2:
                diff = abs(style1[style] - style2[style])
                similarity = 1.0 - diff
                compatibility_scores.append(similarity)
        
        # Categorical style comparisons
        categorical_styles = ["conflict_resolution"]
        for style in categorical_styles:
            if style in style1 and style in style2:
                if style1[style] == style2[style]:
                    compatibility_scores.append(1.0)
                else:
                    compatibility_scores.append(0.3)  # Some compatibility even if different
        
        return sum(compatibility_scores) / len(compatibility_scores) if compatibility_scores else 0.0

    def _normalize_score(self, score: float) -> float:
        """Normalize score to 0.0-1.0 range."""
        return max(0.0, min(1.0, score))

    def _weighted_average(self, scores: List[float], weights: List[float]) -> float:
        """Calculate weighted average of scores."""
        if not scores or not weights or len(scores) != len(weights):
            return 0.0
        
        weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
        weight_sum = sum(weights)
        
        return weighted_sum / weight_sum if weight_sum > 0 else 0.0


def get_compatibility_calculator() -> CompatibilityCalculator:
    """Factory function to create compatibility calculator instance."""
    return CompatibilityCalculator()