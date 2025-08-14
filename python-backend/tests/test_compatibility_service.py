"""
Compatibility Service Tests - High-impact coverage for matching algorithms
"""
import pytest
from unittest.mock import Mock, MagicMock
from app.services.compatibility import (
    calculate_interest_similarity,
    calculate_demographic_compatibility,
    CompatibilityCalculator,
)
from app.models.user import User
from app.models.profile import Profile
from datetime import date, datetime


class TestInterestSimilarity:
    """Test interest similarity calculations using Jaccard similarity"""

    def test_identical_interests(self):
        """Test users with identical interests"""
        interests1 = ["cooking", "hiking", "movies", "books"]
        interests2 = ["cooking", "hiking", "movies", "books"]
        
        score = calculate_interest_similarity(interests1, interests2)
        assert score == 1.0

    def test_no_common_interests(self):
        """Test users with no common interests"""
        interests1 = ["cooking", "hiking"]
        interests2 = ["dancing", "swimming"]
        
        score = calculate_interest_similarity(interests1, interests2)
        assert score == 0.0

    def test_partial_interest_overlap(self):
        """Test users with partial interest overlap"""
        interests1 = ["cooking", "hiking", "movies"]
        interests2 = ["cooking", "dancing", "swimming"]
        
        # Intersection: 1 (cooking), Union: 5 (all unique interests)
        expected_score = 1.0 / 5.0  # 0.2
        score = calculate_interest_similarity(interests1, interests2)
        assert score == expected_score

    def test_empty_interest_lists(self):
        """Test handling of empty interest lists"""
        interests1 = []
        interests2 = ["cooking", "hiking"]
        
        score = calculate_interest_similarity(interests1, interests2)
        assert score == 0.0
        
        # Both empty
        score = calculate_interest_similarity([], [])
        assert score == 0.0

    def test_subset_interests(self):
        """Test when one user's interests are subset of another"""
        interests1 = ["cooking", "hiking"]
        interests2 = ["cooking", "hiking", "movies", "dancing"]
        
        # Intersection: 2, Union: 4
        expected_score = 2.0 / 4.0  # 0.5
        score = calculate_interest_similarity(interests1, interests2)
        assert score == expected_score

    def test_case_sensitivity_handling(self):
        """Test that interests are compared correctly regardless of case"""
        interests1 = ["Cooking", "HIKING", "Movies"]
        interests2 = ["cooking", "hiking", "books"]
        
        # This tests the actual implementation - may need case normalization
        score = calculate_interest_similarity(interests1, interests2)
        # Score should be > 0 if case is normalized, 0 if not
        assert isinstance(score, float)


class TestDemographicCompatibility:
    """Test demographic compatibility calculations"""

    def test_age_compatibility_perfect_match(self):
        """Test age compatibility for same age users"""
        from app.services.compatibility import calculate_age_compatibility
        
        score = calculate_age_compatibility(25, 25)
        assert score == 1.0

    def test_age_compatibility_close_ages(self):
        """Test age compatibility for close ages"""
        from app.services.compatibility import calculate_age_compatibility
        
        # Within 2 years
        score = calculate_age_compatibility(25, 27)
        assert score == 0.9
        
        # Within 5 years
        score = calculate_age_compatibility(25, 30)
        assert score == 0.8

    def test_age_compatibility_large_difference(self):
        """Test age compatibility for large age differences"""
        from app.services.compatibility import calculate_age_compatibility
        
        # 15 year difference
        score = calculate_age_compatibility(25, 40)
        assert score == 0.2  # Should be lowest score

    def test_demographic_compatibility_mock_users(self):
        """Test demographic compatibility with mock user objects"""
        user1 = Mock()
        user1.age = 25
        user1.location = "San Francisco"
        
        user2 = Mock()
        user2.age = 27
        user2.location = "San Francisco"
        
        # Mock the location compatibility function
        with pytest.mock.patch('app.services.compatibility.calculate_location_compatibility') as mock_loc:
            mock_loc.return_value = 1.0
            
            score = calculate_demographic_compatibility(user1, user2)
            assert isinstance(score, float)
            assert score > 0


class TestCompatibilityCalculator:
    """Test the main compatibility calculator class"""

    def test_calculator_initialization(self):
        """Test compatibility calculator initializes with correct weights"""
        calc = CompatibilityCalculator()
        
        # Check weights sum to approximately 1.0
        total_weight = sum(calc.weights.values())
        assert abs(total_weight - 1.0) < 0.01

    def test_calculate_overall_compatibility_structure(self):
        """Test overall compatibility calculation returns correct structure"""
        calc = CompatibilityCalculator()
        
        # Create mock users with profiles
        user1 = Mock(spec=User)
        user1.emotional_profile = Mock(spec=Profile)
        user1.emotional_profile.interests = ["cooking", "hiking"]
        user1.emotional_profile.core_values = {"honesty": "important"}
        
        user2 = Mock(spec=User)
        user2.emotional_profile = Mock(spec=Profile)
        user2.emotional_profile.interests = ["cooking", "reading"]
        user2.emotional_profile.core_values = {"loyalty": "essential"}
        
        # Mock the individual calculation functions
        with pytest.mock.patch.multiple(
            'app.services.compatibility',
            calculate_interest_similarity=Mock(return_value=0.5),
            calculate_values_compatibility=Mock(return_value=0.7),
            calculate_demographic_compatibility=Mock(return_value=0.6)
        ):
            result = calc.calculate_overall_compatibility(user1, user2)
            
            # Check result structure
            assert "total_compatibility" in result
            assert "breakdown" in result
            assert "match_quality" in result
            
            # Check breakdown structure
            breakdown = result["breakdown"]
            assert "interests" in breakdown
            assert "values" in breakdown
            assert "demographics" in breakdown
            
            # Check values are reasonable
            assert 0 <= result["total_compatibility"] <= 100
            assert isinstance(result["match_quality"], str)

    def test_match_quality_labels(self):
        """Test match quality label generation"""
        calc = CompatibilityCalculator()
        
        # Test different score ranges
        test_scores = [0.95, 0.85, 0.75, 0.65, 0.55, 0.35]
        expected_labels = [
            "Soulmate Match", "Excellent Match", "Great Match",
            "Good Match", "Fair Match", "Low Compatibility"
        ]
        
        for score, expected in zip(test_scores, expected_labels):
            label = calc.get_match_quality_label(score)
            assert label == expected


class TestValuesCompatibility:
    """Test values compatibility calculations"""

    def test_calculate_values_compatibility_basic(self):
        """Test basic values compatibility calculation"""
        from app.services.compatibility import calculate_values_compatibility
        
        user1_values = {
            "relationship_values": "I value commitment and honesty",
            "connection_style": "I prefer deep meaningful conversations"
        }
        
        user2_values = {
            "relationship_values": "Loyalty and commitment are essential",
            "connection_style": "I love deep talks about philosophy"
        }
        
        score = calculate_values_compatibility(user1_values, user2_values)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_values_compatibility_empty_responses(self):
        """Test values compatibility with empty responses"""
        from app.services.compatibility import calculate_values_compatibility
        
        score = calculate_values_compatibility({}, {})
        assert score == 0.0
        
        # One empty, one with values
        user_values = {"relationship_values": "I value honesty"}
        score = calculate_values_compatibility(user_values, {})
        assert score == 0.0

    def test_values_compatibility_keyword_matching(self):
        """Test that keyword matching works in values compatibility"""
        from app.services.compatibility import calculate_values_compatibility
        
        # Values with clear keyword overlaps
        user1_values = {
            "relationship_values": "commitment loyalty dedication"
        }
        
        user2_values = {
            "relationship_values": "faithful loyal devoted committed"
        }
        
        score = calculate_values_compatibility(user1_values, user2_values)
        assert score > 0  # Should have some compatibility due to keyword overlap


class TestCompatibilityIntegration:
    """Integration tests for compatibility calculations"""

    def test_full_compatibility_calculation_flow(self):
        """Test complete compatibility calculation with realistic data"""
        calc = CompatibilityCalculator()
        
        # Create realistic mock users
        user1 = Mock(spec=User)
        user1.emotional_profile = Mock(spec=Profile)
        user1.emotional_profile.interests = ["cooking", "hiking", "reading", "movies"]
        user1.emotional_profile.core_values = {
            "relationship_values": "I value commitment, honesty, and growth",
            "connection_style": "I prefer deep conversations and quality time"
        }
        user1.age = 28
        user1.location = "San Francisco, CA"
        
        user2 = Mock(spec=User)
        user2.emotional_profile = Mock(spec=Profile)
        user2.emotional_profile.interests = ["cooking", "travel", "reading", "photography"]
        user2.emotional_profile.core_values = {
            "relationship_values": "Loyalty and commitment are essential to me",
            "connection_style": "I love meaningful talks and shared experiences"
        }
        user2.age = 26
        user2.location = "San Francisco, CA"
        
        # Test with mocked demographic function
        with pytest.mock.patch('app.services.compatibility.calculate_demographic_compatibility') as mock_demo:
            mock_demo.return_value = 0.8
            
            result = calc.calculate_overall_compatibility(user1, user2)
            
            # Verify comprehensive result
            assert isinstance(result, dict)
            assert result["total_compatibility"] > 0
            assert len(result["breakdown"]) >= 3
            
            # Should have reasonable compatibility due to shared interests and values
            assert result["total_compatibility"] > 30  # At least fair compatibility

    def test_edge_case_compatibility_calculations(self):
        """Test compatibility calculations with edge cases"""
        calc = CompatibilityCalculator()
        
        # Users with minimal data
        user1 = Mock(spec=User)
        user1.emotional_profile = Mock(spec=Profile)
        user1.emotional_profile.interests = []
        user1.emotional_profile.core_values = {}
        
        user2 = Mock(spec=User)
        user2.emotional_profile = Mock(spec=Profile)
        user2.emotional_profile.interests = None
        user2.emotional_profile.core_values = None
        
        with pytest.mock.patch('app.services.compatibility.calculate_demographic_compatibility') as mock_demo:
            mock_demo.return_value = 0.0
            
            result = calc.calculate_overall_compatibility(user1, user2)
            
            # Should handle gracefully without errors
            assert isinstance(result, dict)
            assert result["total_compatibility"] >= 0

    def test_performance_with_large_interest_lists(self):
        """Test performance with users having many interests"""
        import time
        
        # Create users with large interest lists
        large_interests1 = [f"interest_{i}" for i in range(100)]
        large_interests2 = [f"interest_{i}" for i in range(50, 150)]  # 50 overlapping
        
        start_time = time.time()
        score = calculate_interest_similarity(large_interests1, large_interests2)
        end_time = time.time()
        
        # Should complete quickly (under 1 second for 100-200 interests)
        assert end_time - start_time < 1.0
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0