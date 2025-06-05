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

    def calculate_location_compatibility(self, location1: str, location2: str) -> float:
        """
        Simple location compatibility based on string matching.
        For MVP, basic city/state matching. Can be enhanced with geocoding.
        Returns: 0.0 to 1.0 based on location similarity
        """
        if not location1 or not location2:
            return 0.5  # Neutral if location not provided
            
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

    def calculate_demographic_compatibility(self, user1_data: Dict, user2_data: Dict) -> float:
        """
        Calculate compatibility based on age and location.
        Returns: 0.0 to 1.0 based on demographic alignment
        """
        age_score = 0.5  # Default if age not available
        location_score = 0.5  # Default if location not available
        
        # Calculate age compatibility
        if user1_data.get('age') and user2_data.get('age'):
            age_score = self.calculate_age_compatibility(
                user1_data['age'], 
                user2_data['age']
            )
        
        # Calculate location compatibility
        if user1_data.get('location') and user2_data.get('location'):
            location_score = self.calculate_location_compatibility(
                user1_data['location'], 
                user2_data['location']
            )
        
        return (age_score * 0.4) + (location_score * 0.6)

    def calculate_overall_compatibility(self, user1_data: Dict, user2_data: Dict) -> Dict[str, Any]:
        """
        Calculate comprehensive compatibility score between two users.
        
        Args:
            user1_data: Dict containing user1's profile data
            user2_data: Dict containing user2's profile data
            
        Returns:
            Dict with total compatibility, breakdown, and match quality
        """
        # Calculate individual scores
        interest_score = self.calculate_interest_similarity(
            user1_data.get('interests', []), 
            user2_data.get('interests', [])
        )
        
        values_score = self.calculate_values_compatibility(
            user1_data.get('core_values', {}), 
            user2_data.get('core_values', {})
        )
        
        demographic_score = self.calculate_demographic_compatibility(
            user1_data, user2_data
        )
        
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
            "match_quality": self._get_match_quality_label(total_score),
            "explanation": self._generate_compatibility_explanation(
                total_score, interest_score, values_score, demographic_score
            )
        }

    def _get_match_quality_label(self, score: float) -> str:
        """Convert compatibility score to descriptive label."""
        if score >= 0.8:
            return "Exceptional Soul Connection"
        elif score >= 0.7:
            return "Strong Compatibility"
        elif score >= 0.6:
            return "Good Potential"
        elif score >= 0.5:
            return "Moderate Match"
        else:
            return "Explore Further"

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


def get_compatibility_calculator() -> CompatibilityCalculator:
    """Factory function to create compatibility calculator instance."""
    return CompatibilityCalculator()