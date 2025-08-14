"""
Enhanced Compatibility Service Tests
Comprehensive test coverage for CompatibilityCalculator service
"""
import pytest
from typing import Dict, List
from unittest.mock import Mock, patch

from app.services.compatibility import CompatibilityCalculator


@pytest.fixture
def calculator():
    """Create a CompatibilityCalculator instance for testing"""
    return CompatibilityCalculator()


@pytest.fixture
def sample_interests_1():
    """Sample user 1 interests"""
    return ["hiking", "photography", "cooking", "travel", "reading"]


@pytest.fixture  
def sample_interests_2():
    """Sample user 2 interests"""
    return ["hiking", "cooking", "music", "art", "fitness"]


@pytest.fixture
def sample_values_1():
    """Sample user 1 values responses"""
    return {
        "relationship_values": "I value loyalty and commitment in relationships. I want someone faithful and dedicated.",
        "connection_style": "I love deep meaningful conversations about philosophy and life.",
        "future_goals": "I want to grow together and explore new adventures."
    }


@pytest.fixture
def sample_values_2():
    """Sample user 2 values responses"""
    return {
        "relationship_values": "Loyalty is important to me. I believe in committed relationships.",
        "connection_style": "I enjoy quality time together and sharing activities.",
        "future_goals": "I want stability and to build a family together."
    }


class TestInterestSimilarity:
    """Test interest similarity calculations"""
    
    def test_identical_interests(self, calculator):
        """Test with identical interest lists"""
        interests = ["hiking", "cooking", "travel"]
        similarity = calculator.calculate_interest_similarity(interests, interests)
        assert similarity == 1.0
    
    def test_no_overlap_interests(self, calculator):
        """Test with completely different interests"""
        interests1 = ["hiking", "cooking", "travel"]
        interests2 = ["gaming", "movies", "sports"]
        similarity = calculator.calculate_interest_similarity(interests1, interests2)
        assert similarity == 0.0
    
    def test_partial_overlap_interests(self, calculator, sample_interests_1, sample_interests_2):
        """Test with partial overlap (hiking, cooking shared)"""
        similarity = calculator.calculate_interest_similarity(sample_interests_1, sample_interests_2)
        # 2 shared interests (hiking, cooking) out of 8 total unique interests
        expected = 2 / 8  # 0.25
        assert similarity == expected
    
    def test_empty_interests_list(self, calculator):
        """Test with empty interest lists"""
        interests = ["hiking", "cooking"]
        assert calculator.calculate_interest_similarity([], interests) == 0.0
        assert calculator.calculate_interest_similarity(interests, []) == 0.0
        assert calculator.calculate_interest_similarity([], []) == 0.0
    
    def test_case_insensitive_interests(self, calculator):
        """Test case insensitive matching"""
        interests1 = ["HIKING", "Cooking", "TRAVEL"]
        interests2 = ["hiking", "COOKING", "travel"]
        similarity = calculator.calculate_interest_similarity(interests1, interests2)
        assert similarity == 1.0
    
    def test_whitespace_handling_interests(self, calculator):
        """Test whitespace handling in interests"""
        interests1 = [" hiking ", "cooking", " travel"]
        interests2 = ["hiking", " cooking ", "travel "]
        similarity = calculator.calculate_interest_similarity(interests1, interests2)
        assert similarity == 1.0


class TestValuesCompatibility:
    """Test values compatibility calculations"""
    
    def test_values_compatibility_with_overlap(self, calculator, sample_values_1, sample_values_2):
        """Test values compatibility with some shared values"""
        compatibility = calculator.calculate_values_compatibility(sample_values_1, sample_values_2)
        assert 0.0 <= compatibility <= 1.0
        assert compatibility > 0.0  # Should have some compatibility
    
    def test_empty_values_responses(self, calculator):
        """Test with empty values responses"""
        values = {"test": "value"}
        assert calculator.calculate_values_compatibility({}, values) == 0.0
        assert calculator.calculate_values_compatibility(values, {}) == 0.0
        assert calculator.calculate_values_compatibility({}, {}) == 0.0
    
    def test_no_matching_questions(self, calculator):
        """Test when users answered different questions"""
        values1 = {"question1": "answer1"}
        values2 = {"question2": "answer2"}
        compatibility = calculator.calculate_values_compatibility(values1, values2)
        assert compatibility == 0.0
    
    def test_identical_values_responses(self, calculator):
        """Test with identical values responses"""
        values = {
            "relationship_values": "I value loyalty and commitment above all else",
            "connection_style": "Deep meaningful conversations are essential to me"
        }
        compatibility = calculator.calculate_values_compatibility(values, values)
        assert compatibility > 0.5  # Should be high compatibility


class TestResponseValueComparison:
    """Test internal response value comparison method"""
    
    def test_compare_response_values_commitment(self, calculator):
        """Test comparing responses about commitment"""
        response1 = "I value loyalty and being faithful in relationships"
        response2 = "I believe in commitment and being dedicated to relationships" 
        keywords = calculator.value_keywords["relationship_values"]
        
        score = calculator._compare_response_values(response1, response2, keywords)
        assert 0.0 <= score <= 1.0
        # Both responses should match "commitment" keywords: 
        # response1: "loyal", "faithful" → commitment category
        # response2: "committed" (from commitment), "dedicated" → commitment category
        # Should have intersection = 1, union = 1 → score = 1.0
        assert score > 0.0  # Should find shared commitment values
    
    def test_compare_response_values_no_keywords(self, calculator):
        """Test comparing responses with no matching keywords"""
        response1 = "I like pizza and movies"
        response2 = "Cars and technology are interesting"
        keywords = calculator.value_keywords["relationship_values"]
        
        score = calculator._compare_response_values(response1, response2, keywords)
        # May return 0.5 as neutral when no keywords found
        assert score == 0.5
    
    def test_compare_response_values_empty_inputs(self, calculator):
        """Test comparing empty or None responses"""
        keywords = calculator.value_keywords["relationship_values"]
        
        assert calculator._compare_response_values("", "test", keywords) == 0.0
        assert calculator._compare_response_values("test", "", keywords) == 0.0
        assert calculator._compare_response_values("", "", keywords) == 0.0
        assert calculator._compare_response_values(None, "test", keywords) == 0.0
    
    def test_compare_response_values_case_insensitive(self, calculator):
        """Test case insensitive keyword matching"""
        response1 = "I VALUE LOYALTY AND COMMITMENT"
        response2 = "loyalty and faithful relationships matter"
        keywords = calculator.value_keywords["relationship_values"]
        
        score = calculator._compare_response_values(response1, response2, keywords)
        assert score > 0.0


class TestDemographicCompatibility:
    """Test demographic compatibility calculations"""
    
    def test_calculate_age_compatibility_same_age(self, calculator):
        """Test age compatibility with same age"""
        compatibility = calculator.calculate_age_compatibility(25, 25)
        assert compatibility == 1.0
    
    def test_calculate_age_compatibility_close_ages(self, calculator):
        """Test age compatibility with close ages"""
        # 2 years apart should be 0.9
        compatibility = calculator.calculate_age_compatibility(25, 27)
        assert compatibility == 0.9
        
        # 5 years apart should be 0.8
        compatibility = calculator.calculate_age_compatibility(25, 30)
        assert compatibility == 0.8
    
    def test_calculate_age_compatibility_large_gap(self, calculator):
        """Test age compatibility with large age gaps"""
        # 10 years apart should be 0.4
        compatibility = calculator.calculate_age_compatibility(25, 35)
        assert compatibility == 0.4
        
        # 15+ years apart should be 0.2
        compatibility = calculator.calculate_age_compatibility(25, 45)
        assert compatibility == 0.2
    
    def test_calculate_location_compatibility_same_city(self, calculator):
        """Test location compatibility in same city"""
        location = {"city": "San Francisco", "state": "CA", "country": "USA"}
        compatibility = calculator.calculate_location_compatibility(location, location)
        assert compatibility == 1.0
    
    def test_calculate_location_compatibility_same_state(self, calculator):
        """Test location compatibility in same state"""
        location1 = {"city": "San Francisco", "state": "CA", "country": "USA"}
        location2 = {"city": "Los Angeles", "state": "CA", "country": "USA"}
        compatibility = calculator.calculate_location_compatibility(location1, location2)
        assert compatibility == 0.8
    
    def test_calculate_location_compatibility_different_countries(self, calculator):
        """Test location compatibility in different countries"""
        location1 = {"city": "San Francisco", "state": "CA", "country": "USA"}
        location2 = {"city": "London", "state": "England", "country": "UK"}
        compatibility = calculator.calculate_location_compatibility(location1, location2)
        assert compatibility == 0.2
    
    def test_calculate_demographic_compatibility(self, calculator):
        """Test overall demographic compatibility calculation"""
        user1 = Mock()
        user1.age = 25
        user1.location = {"city": "SF", "state": "CA", "country": "USA"}
        
        user2 = Mock()
        user2.age = 27
        user2.location = {"city": "LA", "state": "CA", "country": "USA"}
        
        compatibility = calculator.calculate_demographic_compatibility(user1, user2)
        # Should be weighted combination of age (0.9) and location (0.8)
        expected = (0.9 * 0.4) + (0.8 * 0.6)
        assert compatibility == expected


class TestOverallCompatibility:
    """Test overall compatibility calculation"""
    
    def test_calculate_overall_compatibility_complete_data(self, calculator):
        """Test overall compatibility with complete data"""
        user1 = Mock()
        user1.emotional_profile.interests = ["hiking", "cooking", "travel"]
        user1.emotional_profile.core_values = {
            "relationship_values": "I value loyalty and commitment",
            "connection_style": "Deep conversations are important"
        }
        user1.age = 25
        user1.location = {"city": "SF", "state": "CA", "country": "USA"}
        
        user2 = Mock()
        user2.emotional_profile.interests = ["hiking", "cooking", "music"]
        user2.emotional_profile.core_values = {
            "relationship_values": "Commitment and loyalty matter to me",
            "connection_style": "I enjoy quality time together"
        }
        user2.age = 27
        user2.location = {"city": "LA", "state": "CA", "country": "USA"}
        
        result = calculator.calculate_overall_compatibility(user1, user2)
        
        assert "total_compatibility" in result
        assert "breakdown" in result
        assert "match_quality" in result
        assert 0.0 <= result["total_compatibility"] <= 100.0
        assert "interests" in result["breakdown"]
        assert "values" in result["breakdown"]
        assert "demographics" in result["breakdown"]
    
    def test_calculate_overall_compatibility_missing_data(self, calculator):
        """Test overall compatibility with missing data"""
        user1 = Mock()
        user1.emotional_profile.interests = []
        user1.emotional_profile.core_values = {}
        user1.age = 25
        user1.location = {"city": "SF", "state": "CA", "country": "USA"}
        
        user2 = Mock()
        user2.emotional_profile.interests = ["hiking"]
        user2.emotional_profile.core_values = {"test": "value"}
        user2.age = 27
        user2.location = {"city": "LA", "state": "CA", "country": "USA"}
        
        result = calculator.calculate_overall_compatibility(user1, user2)
        
        # Should still return valid structure even with missing data
        assert "total_compatibility" in result
        assert isinstance(result["total_compatibility"], (int, float))
        assert 0.0 <= result["total_compatibility"] <= 100.0
    
    def test_get_match_quality_label(self, calculator):
        """Test match quality labeling"""
        assert calculator.get_match_quality_label(0.9) == "excellent"
        assert calculator.get_match_quality_label(0.75) == "very_good"
        assert calculator.get_match_quality_label(0.65) == "good"
        assert calculator.get_match_quality_label(0.45) == "fair"
        assert calculator.get_match_quality_label(0.25) == "poor"


class TestPersonalityCompatibility:
    """Test personality compatibility calculations"""
    
    def test_calculate_personality_compatibility_extroversion(self, calculator):
        """Test personality compatibility for extroversion"""
        traits1 = {"extroversion": 0.8, "openness": 0.6, "agreeableness": 0.7}
        traits2 = {"extroversion": 0.9, "openness": 0.5, "agreeableness": 0.8}
        
        compatibility = calculator.calculate_personality_compatibility(traits1, traits2)
        assert 0.0 <= compatibility <= 1.0
    
    def test_calculate_personality_compatibility_empty_traits(self, calculator):
        """Test personality compatibility with empty traits"""
        traits = {"extroversion": 0.5}
        assert calculator.calculate_personality_compatibility({}, traits) == 0.0
        assert calculator.calculate_personality_compatibility(traits, {}) == 0.0
        assert calculator.calculate_personality_compatibility({}, {}) == 0.0
    
    def test_calculate_personality_compatibility_identical_traits(self, calculator):
        """Test personality compatibility with identical traits"""
        traits = {"extroversion": 0.7, "openness": 0.6, "agreeableness": 0.8}
        compatibility = calculator.calculate_personality_compatibility(traits, traits)
        assert compatibility == 1.0


class TestCommunicationCompatibility:
    """Test communication compatibility calculations"""
    
    def test_calculate_communication_compatibility_similar_styles(self, calculator):
        """Test communication compatibility with similar styles"""
        style1 = {
            "directness": 0.7,
            "emotional_expression": 0.6,
            "conflict_resolution": "collaborative"
        }
        style2 = {
            "directness": 0.8,
            "emotional_expression": 0.7,
            "conflict_resolution": "collaborative"
        }
        
        compatibility = calculator.calculate_communication_compatibility(style1, style2)
        assert 0.0 <= compatibility <= 1.0
        assert compatibility > 0.5  # Should be high for similar styles
    
    def test_calculate_communication_compatibility_empty_styles(self, calculator):
        """Test communication compatibility with empty styles"""
        style = {"directness": 0.5}
        assert calculator.calculate_communication_compatibility({}, style) == 0.0
        assert calculator.calculate_communication_compatibility(style, {}) == 0.0


class TestUtilityMethods:
    """Test utility and helper methods"""
    
    def test_normalize_score(self, calculator):
        """Test score normalization"""
        assert calculator._normalize_score(0.5) == 0.5
        assert calculator._normalize_score(1.5) == 1.0
        assert calculator._normalize_score(-0.5) == 0.0
    
    def test_weighted_average(self, calculator):
        """Test weighted average calculation"""
        scores = [0.8, 0.6, 0.9]
        weights = [0.5, 0.3, 0.2]
        expected = (0.8 * 0.5) + (0.6 * 0.3) + (0.9 * 0.2)
        result = calculator._weighted_average(scores, weights)
        # Use approximate equality for floating point comparison
        assert abs(result - expected) < 0.0001
    
    def test_weighted_average_empty_inputs(self, calculator):
        """Test weighted average with empty inputs"""
        assert calculator._weighted_average([], []) == 0.0
        assert calculator._weighted_average([0.5], []) == 0.0
        assert calculator._weighted_average([], [0.5]) == 0.0


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_malformed_interests_data(self, calculator):
        """Test handling of malformed interests data"""
        # Test with None values
        assert calculator.calculate_interest_similarity(None, ["test"]) == 0.0
        assert calculator.calculate_interest_similarity(["test"], None) == 0.0
        
        # Test with non-string interests (should handle gracefully)
        malformed_interests = ["hiking", 123, "cooking"]  # Mixed types
        normal_interests = ["hiking", "cooking"]
        
        try:
            result = calculator.calculate_interest_similarity(malformed_interests, normal_interests)
            assert 0.0 <= result <= 1.0
        except Exception:
            # If it throws an exception, that's acceptable for malformed data
            pass
    
    def test_malformed_values_data(self, calculator):
        """Test handling of malformed values data"""
        # Test with None responses
        values1 = {"test": None}
        values2 = {"test": "valid response"}
        compatibility = calculator.calculate_values_compatibility(values1, values2)
        assert compatibility == 0.0
    
    def test_missing_location_data(self, calculator):
        """Test handling missing location data"""
        location1 = {"city": "SF"}  # Missing state, country
        location2 = {"state": "CA"}  # Missing city, country
        
        # Should handle gracefully without crashing
        try:
            compatibility = calculator.calculate_location_compatibility(location1, location2)
            assert 0.0 <= compatibility <= 1.0
        except Exception:
            pytest.fail("Should handle missing location data gracefully")


class TestPerformanceRequirements:
    """Test performance requirements"""
    
    def test_compatibility_calculation_performance(self, calculator):
        """Test that compatibility calculation meets <500ms requirement"""
        import time
        
        # Create realistic test data
        user1 = Mock()
        user1.emotional_profile.interests = ["hiking", "cooking", "travel", "photography", "reading"]
        user1.emotional_profile.core_values = {
            "relationship_values": "I value loyalty, commitment and deep emotional connection in relationships",
            "connection_style": "I love deep meaningful conversations about life, philosophy and personal growth",
            "future_goals": "I want to explore the world together and build a loving family"
        }
        user1.age = 28
        user1.location = {"city": "San Francisco", "state": "CA", "country": "USA"}
        
        user2 = Mock()
        user2.emotional_profile.interests = ["hiking", "cooking", "music", "art", "fitness"]
        user2.emotional_profile.core_values = {
            "relationship_values": "Loyalty and faithfulness are extremely important to me in relationships",
            "connection_style": "I enjoy quality time together and sharing new experiences",
            "future_goals": "I want stability and to grow together as a couple"
        }
        user2.age = 26
        user2.location = {"city": "Los Angeles", "state": "CA", "country": "USA"}
        
        start_time = time.time()
        result = calculator.calculate_overall_compatibility(user1, user2)
        end_time = time.time()
        
        processing_time = (end_time - start_time) * 1000  # Convert to milliseconds
        assert processing_time < 500, f"Processing took {processing_time}ms, should be <500ms"
        assert result is not None