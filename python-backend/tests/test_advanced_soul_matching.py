"""
Tests for Advanced Soul Matching System
Comprehensive tests for emotional depth analysis and enhanced match quality
"""

import pytest
from datetime import datetime, date
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch

from app.models.user import User
from app.models.daily_revelation import DailyRevelation
from app.services.emotional_depth_service import (
    EmotionalDepthService,
    EmotionalDepthLevel,
    VulnerabilityIndicator
)
from app.services.enhanced_match_quality_service import (
    EnhancedMatchQualityService,
    MatchQualityTier,
    ConnectionPrediction
)
from app.services.advanced_soul_matching import AdvancedSoulMatchingService


class TestEmotionalDepthService:
    """Test suite for emotional depth analysis"""
    
    @pytest.fixture
    def emotional_depth_service(self):
        return EmotionalDepthService()
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def user_with_rich_responses(self):
        """User with rich emotional responses"""
        user = Mock(spec=User)
        user.id = 1
        user.emotional_responses = {
            "relationship_values": "I deeply value authentic connection and genuine intimacy. Trust and vulnerability are essential for me to feel truly connected with someone. I believe in growing together and supporting each other's personal development.",
            "life_philosophy": "I'm constantly working on understanding my emotions better and learning from my experiences. Empathy and compassion are core to who I am. I find meaning in helping others and building meaningful relationships.",
            "ideal_connection": "I want someone I can share my fears, dreams, and deepest thoughts with. Someone who understands my struggles and celebrates my growth. Mutual vulnerability and emotional openness are crucial."
        }
        user.core_values = {
            "authenticity": "Being genuine and true to myself and others",
            "growth": "Continuous learning and personal development",
            "compassion": "Deep empathy and care for others' well-being"
        }
        user.interests = ["psychology", "meditation", "deep conversations", "personal growth"]
        return user
    
    @pytest.fixture
    def user_with_surface_responses(self):
        """User with surface-level responses"""
        user = Mock(spec=User)
        user.id = 2
        user.emotional_responses = {
            "relationship_values": "I like to have fun and enjoy life. Looking for someone nice.",
            "life_philosophy": "Live life to the fullest. Be happy.",
            "ideal_connection": "Someone fun to hang out with."
        }
        user.core_values = {
            "fun": "Having a good time",
            "happiness": "Being happy"
        }
        user.interests = ["movies", "music"]
        return user
    
    def test_emotional_vocabulary_analysis(self, emotional_depth_service, user_with_rich_responses):
        """Test emotional vocabulary analysis"""
        text_data = " ".join(user_with_rich_responses.emotional_responses.values())
        vocab = emotional_depth_service._analyze_emotional_vocabulary(text_data)
        
        # Should find sophisticated emotional words
        assert len(vocab) > 5
        assert any(word in text_data.lower() for word in vocab)
    
    def test_vulnerability_expression_analysis(self, emotional_depth_service, user_with_rich_responses):
        """Test vulnerability expression analysis"""
        text_data = " ".join(user_with_rich_responses.emotional_responses.values())
        vulnerability_score = emotional_depth_service._analyze_vulnerability_expression(text_data)
        
        # Rich responses should have high vulnerability score
        assert vulnerability_score > 60.0
        assert vulnerability_score <= 100.0
    
    def test_authenticity_markers_analysis(self, emotional_depth_service, user_with_rich_responses):
        """Test authenticity markers detection"""
        text_data = " ".join(user_with_rich_responses.emotional_responses.values())
        authenticity_score = emotional_depth_service._analyze_authenticity_markers(text_data)
        
        # Should detect authentic expression
        assert authenticity_score > 40.0
        assert authenticity_score <= 100.0
    
    def test_depth_level_classification(self, emotional_depth_service):
        """Test emotional depth level classification"""
        # Test different depth levels
        assert emotional_depth_service._classify_depth_level(95.0) == EmotionalDepthLevel.PROFOUND
        assert emotional_depth_service._classify_depth_level(80.0) == EmotionalDepthLevel.DEEP
        assert emotional_depth_service._classify_depth_level(65.0) == EmotionalDepthLevel.MODERATE
        assert emotional_depth_service._classify_depth_level(35.0) == EmotionalDepthLevel.EMERGING
        assert emotional_depth_service._classify_depth_level(15.0) == EmotionalDepthLevel.SURFACE
    
    def test_analyze_emotional_depth_with_revelations(self, emotional_depth_service, user_with_rich_responses, mock_db):
        """Test emotional depth analysis with daily revelations"""
        # Mock revelations query
        mock_revelations = [
            Mock(content="I struggle with vulnerability but I'm working on opening up more"),
            Mock(content="Today I felt deeply connected to my authentic self through meditation")
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_revelations
        
        depth_metrics = emotional_depth_service.analyze_emotional_depth(user_with_rich_responses, mock_db)
        
        # Should produce meaningful metrics
        assert depth_metrics.overall_depth > 50.0
        assert depth_metrics.emotional_vocabulary >= 5
        assert depth_metrics.depth_level in EmotionalDepthLevel
        assert len(depth_metrics.vulnerability_types) > 0
        assert depth_metrics.confidence > 30.0
    
    def test_depth_compatibility_calculation(self, emotional_depth_service, user_with_rich_responses, user_with_surface_responses, mock_db):
        """Test depth compatibility calculation"""
        # Mock database calls for both users
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        compatibility = emotional_depth_service.calculate_depth_compatibility(
            user_with_rich_responses, user_with_surface_responses, mock_db
        )
        
        # Should calculate compatibility metrics
        assert 0.0 <= compatibility.compatibility_score <= 100.0
        assert 0.0 <= compatibility.depth_harmony <= 100.0
        assert 0.0 <= compatibility.vulnerability_match <= 100.0
        assert 0.0 <= compatibility.growth_alignment <= 100.0
        assert compatibility.connection_potential is not None
        assert compatibility.recommended_approach is not None


class TestAdvancedSoulMatchingService:
    """Test suite for advanced soul matching algorithms"""
    
    @pytest.fixture
    def advanced_matching_service(self):
        return AdvancedSoulMatchingService()
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def compatible_users(self):
        """Two highly compatible users"""
        user1 = Mock(spec=User)
        user1.id = 1
        user1.emotional_responses = {
            "values": "I value deep connection, authenticity, and mutual growth in relationships",
            "communication": "I prefer meaningful conversations and emotional openness"
        }
        user1.interests = ["psychology", "philosophy", "meditation", "personal growth"]
        user1.personality_traits = {"openness": 85, "empathy": 90, "emotional_stability": 80}
        
        user2 = Mock(spec=User)
        user2.id = 2
        user2.emotional_responses = {
            "values": "Authentic connection and personal development are most important to me",
            "communication": "I love deep conversations and sharing vulnerabilities"
        }
        user2.interests = ["mindfulness", "psychology", "self-development", "meaningful conversations"]
        user2.personality_traits = {"openness": 80, "empathy": 85, "emotional_stability": 75}
        
        return user1, user2
    
    def test_emotional_intelligence_compatibility(self, advanced_matching_service, compatible_users):
        """Test emotional intelligence compatibility calculation"""
        user1, user2 = compatible_users
        
        ei_compatibility = advanced_matching_service._calculate_emotional_intelligence_compatibility(user1, user2)
        
        # Should have high compatibility for similar EI profiles
        assert ei_compatibility >= 60.0
        assert ei_compatibility <= 100.0
    
    def test_growth_potential_calculation(self, advanced_matching_service, compatible_users):
        """Test growth potential calculation"""
        user1, user2 = compatible_users
        
        growth_potential = advanced_matching_service._calculate_growth_potential(user1, user2)
        
        # Should calculate growth potential
        assert 0.0 <= growth_potential <= 100.0
    
    def test_relationship_prediction(self, advanced_matching_service, compatible_users):
        """Test relationship dynamic prediction"""
        user1, user2 = compatible_users
        
        prediction = advanced_matching_service._predict_relationship_dynamic(
            user1, user2, total_score=85.0, ei_compatibility=80.0, growth_potential=85.0
        )
        
        # Should provide meaningful prediction
        assert isinstance(prediction, str)
        assert len(prediction) > 20
        assert any(keyword in prediction.lower() for keyword in ['partnership', 'connection', 'growth', 'companionship'])
    
    def test_first_date_suggestion(self, advanced_matching_service, compatible_users):
        """Test first date suggestion generation"""
        user1, user2 = compatible_users
        
        suggestion = advanced_matching_service._suggest_first_date_type(
            user1, user2, interests_score=75.0, personality_score=80.0
        )
        
        # Should provide meaningful suggestion
        assert isinstance(suggestion, str)
        assert len(suggestion) > 20
    
    def test_conversation_starters_generation(self, advanced_matching_service, compatible_users):
        """Test conversation starters generation"""
        user1, user2 = compatible_users
        strengths = ["shared values", "emotional compatibility"]
        
        starters = advanced_matching_service._generate_conversation_starters(user1, user2, strengths)
        
        # Should generate multiple relevant starters
        assert isinstance(starters, list)
        assert len(starters) >= 3
        assert all(isinstance(starter, str) for starter in starters)
        assert all(len(starter) > 10 for starter in starters)


class TestEnhancedMatchQualityService:
    """Test suite for comprehensive match quality assessment"""
    
    @pytest.fixture
    def enhanced_match_service(self):
        return EnhancedMatchQualityService()
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def high_quality_match_users(self):
        """Users who should have high match quality"""
        user1 = Mock(spec=User)
        user1.id = 1
        user1.first_name = "Alice"
        user1.last_name = "Johnson"
        user1.date_of_birth = "1990-01-15"
        user1.gender = "female"
        user1.location = "San Francisco, CA"
        user1.interests = ["psychology", "meditation", "hiking", "philosophy", "art"]
        user1.core_values = {
            "authenticity": "Being true to myself and others",
            "growth": "Continuous learning and development",
            "compassion": "Deep empathy for others"
        }
        user1.emotional_responses = {
            "relationship_values": "I deeply value authentic connection, vulnerability, and mutual growth",
            "ideal_evening": "Deep conversation over dinner, sharing dreams and fears",
            "understanding": "I feel understood when someone truly listens and empathizes"
        }
        user1.personality_traits = {"openness": 90, "empathy": 85, "emotional_stability": 80}
        user1.communication_style = {"depth": "deep", "frequency": "moderate", "style": "empathetic"}
        
        user2 = Mock(spec=User)
        user2.id = 2
        user2.first_name = "Bob"
        user2.last_name = "Smith"
        user2.date_of_birth = "1988-06-20"
        user2.gender = "male"
        user2.location = "San Francisco, CA"
        user2.interests = ["philosophy", "psychology", "nature", "deep conversations", "mindfulness"]
        user2.core_values = {
            "authenticity": "Genuine connection with others",
            "personal_growth": "Always learning and evolving",
            "empathy": "Understanding others deeply"
        }
        user2.emotional_responses = {
            "relationship_values": "Authentic emotional connection and personal development together",
            "ideal_evening": "Meaningful conversation and genuine connection",
            "understanding": "Feeling heard and emotionally seen by my partner"
        }
        user2.personality_traits = {"openness": 85, "empathy": 90, "emotional_stability": 82}
        user2.communication_style = {"depth": "deep", "frequency": "moderate", "style": "thoughtful"}
        
        return user1, user2
    
    def test_composite_score_calculation(self, enhanced_match_service):
        """Test composite compatibility score calculation"""
        # Mock component scores
        soul_compat = Mock()
        soul_compat.total_score = 85.0
        
        advanced_compat = Mock()
        advanced_compat.total_score = 80.0
        
        depth_compat = Mock()
        depth_compat.compatibility_score = 88.0
        
        composite_score = enhanced_match_service._calculate_composite_score(
            soul_compat, advanced_compat, depth_compat
        )
        
        # Should calculate weighted average
        expected_score = (85.0 * 0.35) + (80.0 * 0.35) + (88.0 * 0.30)
        assert abs(composite_score - expected_score) < 0.1
    
    def test_match_quality_tier_determination(self, enhanced_match_service):
        """Test match quality tier classification"""
        # Test different score ranges
        assert enhanced_match_service._determine_match_quality_tier(97.0) == MatchQualityTier.TRANSCENDENT
        assert enhanced_match_service._determine_match_quality_tier(92.0) == MatchQualityTier.EXCEPTIONAL
        assert enhanced_match_service._determine_match_quality_tier(85.0) == MatchQualityTier.HIGH
        assert enhanced_match_service._determine_match_quality_tier(75.0) == MatchQualityTier.GOOD
        assert enhanced_match_service._determine_match_quality_tier(65.0) == MatchQualityTier.MODERATE
        assert enhanced_match_service._determine_match_quality_tier(55.0) == MatchQualityTier.EXPLORATORY
        assert enhanced_match_service._determine_match_quality_tier(45.0) == MatchQualityTier.LIMITED
        assert enhanced_match_service._determine_match_quality_tier(30.0) == MatchQualityTier.INCOMPATIBLE
    
    def test_connection_prediction(self, enhanced_match_service):
        """Test connection type prediction"""
        # Mock high compatibility components
        soul_compat = Mock()
        soul_compat.values_score = 85.0
        soul_compat.communication_score = 80.0
        soul_compat.personality_score = 75.0
        
        advanced_compat = Mock()
        advanced_compat.growth_potential = 85.0
        
        depth_compat = Mock()
        depth_compat.depth_harmony = 90.0
        depth_compat.vulnerability_match = 85.0
        
        prediction = enhanced_match_service._predict_connection_type(
            92.0, soul_compat, advanced_compat, depth_compat
        )
        
        # Should predict high-quality connection type
        assert prediction in [
            ConnectionPrediction.SOULMATE_POTENTIAL,
            ConnectionPrediction.TRANSFORMATIONAL,
            ConnectionPrediction.DYNAMIC_GROWTH
        ]
    
    def test_relationship_timeline_generation(self, enhanced_match_service):
        """Test relationship timeline generation"""
        # Mock high compatibility
        advanced_compat = Mock()
        advanced_compat.growth_potential = 85.0
        
        depth_compat = Mock()
        depth_compat.depth_harmony = 80.0
        
        timeline = enhanced_match_service._generate_relationship_timeline(
            90.0, advanced_compat, depth_compat
        )
        
        # Should provide meaningful timeline
        assert isinstance(timeline, str)
        assert len(timeline) > 30
        assert any(timeword in timeline.lower() for timeword in ['weeks', 'months', 'rapid', 'deep'])
    
    def test_connection_strengths_identification(self, enhanced_match_service):
        """Test identification of connection strengths"""
        # Mock high scores in various areas
        soul_compat = Mock()
        soul_compat.values_score = 85.0
        soul_compat.interests_score = 80.0
        soul_compat.communication_score = 85.0
        
        advanced_compat = Mock()
        advanced_compat.emotional_intelligence_compatibility = 85.0
        advanced_compat.growth_potential = 88.0
        advanced_compat.temporal_compatibility = 70.0
        
        depth_compat = Mock()
        depth_compat.vulnerability_match = 85.0
        depth_compat.depth_harmony = 90.0
        depth_compat.growth_alignment = 82.0
        
        strengths = enhanced_match_service._identify_connection_strengths(
            soul_compat, advanced_compat, depth_compat
        )
        
        # Should identify multiple strengths
        assert isinstance(strengths, list)
        assert len(strengths) >= 3
        assert all(isinstance(strength, str) for strength in strengths)
        assert any('values' in strength.lower() for strength in strengths)
    
    def test_assessment_confidence_calculation(self, enhanced_match_service):
        """Test assessment confidence calculation"""
        # Mock component confidences
        soul_compat = Mock()
        soul_compat.confidence = 85.0
        
        advanced_compat = Mock()
        advanced_compat.confidence = 80.0
        
        depth_compat = Mock()
        depth_compat.user1_depth = Mock()
        depth_compat.user1_depth.confidence = 75.0
        depth_compat.user2_depth = Mock()
        depth_compat.user2_depth.confidence = 78.0
        
        confidence = enhanced_match_service._calculate_assessment_confidence(
            soul_compat, advanced_compat, depth_compat
        )
        
        # Should calculate weighted confidence
        assert 30.0 <= confidence <= 100.0
    
    @patch('app.services.enhanced_match_quality_service.SoulCompatibilityService')
    @patch('app.services.enhanced_match_quality_service.AdvancedSoulMatchingService')
    @patch('app.services.enhanced_match_quality_service.EmotionalDepthService')
    def test_comprehensive_assessment_integration(self, mock_depth_service, mock_advanced_service, 
                                                mock_soul_service, enhanced_match_service, 
                                                high_quality_match_users, mock_db):
        """Test full comprehensive match quality assessment"""
        user1, user2 = high_quality_match_users
        
        # Mock service responses
        mock_soul_compat = Mock()
        mock_soul_compat.total_score = 85.0
        mock_soul_compat.confidence = 80.0
        mock_soul_compat.strengths = ["Strong values alignment"]
        mock_soul_compat.growth_areas = ["Communication timing"]
        
        mock_advanced_compat = Mock()
        mock_advanced_compat.total_score = 83.0
        mock_advanced_compat.confidence = 78.0
        mock_advanced_compat.growth_potential = 85.0
        mock_advanced_compat.recommended_first_date = "Coffee and walk in the park"
        mock_advanced_compat.conversation_starters = ["What brings you joy?"]
        
        mock_depth_compat = Mock()
        mock_depth_compat.compatibility_score = 87.0
        mock_depth_compat.depth_harmony = 85.0
        mock_depth_compat.vulnerability_match = 80.0
        mock_depth_compat.growth_alignment = 88.0
        mock_depth_compat.user1_depth = Mock()
        mock_depth_compat.user1_depth.confidence = 75.0
        mock_depth_compat.user2_depth = Mock()
        mock_depth_compat.user2_depth.confidence = 78.0
        
        # Setup mock returns
        enhanced_match_service.soul_compatibility_service.calculate_compatibility.return_value = mock_soul_compat
        enhanced_match_service.advanced_matching_service.calculate_advanced_compatibility.return_value = mock_advanced_compat
        enhanced_match_service.emotional_depth_service.calculate_depth_compatibility.return_value = mock_depth_compat
        
        # Perform assessment
        result = enhanced_match_service.assess_comprehensive_match_quality(user1, user2, mock_db)
        
        # Verify result structure and content
        assert result is not None
        assert 0.0 <= result.total_compatibility <= 100.0
        assert result.match_quality_tier in MatchQualityTier
        assert result.connection_prediction in ConnectionPrediction
        assert isinstance(result.connection_strengths, list)
        assert isinstance(result.growth_opportunities, list)
        assert isinstance(result.potential_challenges, list)
        assert isinstance(result.conversation_starters, list)
        assert result.assessment_confidence >= 30.0
        assert result.algorithm_version == "enhanced_v1.0"
        assert isinstance(result.analysis_timestamp, datetime)


class TestMatchingAccuracyValidation:
    """Integration tests for overall matching accuracy"""
    
    def test_consistent_scoring_across_services(self):
        """Test that scores are consistent across different services"""
        # This would be an integration test with real database
        # For now, we test that services don't crash and return reasonable ranges
        pass
    
    def test_matching_recommendations_quality(self):
        """Test that matching recommendations are actionable and relevant"""
        # Test that conversation starters are appropriate
        # Test that first date suggestions are reasonable  
        # Test that relationship timelines are realistic
        pass
    
    def test_edge_cases_handling(self):
        """Test handling of edge cases"""
        # Empty profiles
        # Incomplete data
        # Extreme compatibility scores
        # Invalid user data
        pass
    
    def test_performance_requirements(self):
        """Test that matching algorithms meet performance requirements"""
        # Algorithm should complete in < 2 seconds
        # Memory usage should be reasonable
        # Should handle concurrent requests
        pass


# Integration test fixtures and utilities
@pytest.fixture
def test_users_database():
    """Create test users with various compatibility profiles"""
    # This would create a test database with various user profiles
    # for comprehensive matching accuracy validation
    pass


@pytest.fixture  
def compatibility_test_cases():
    """Test cases with known compatibility outcomes"""
    # Define test cases with expected match quality outcomes
    # High compatibility couples
    # Medium compatibility couples  
    # Low compatibility couples
    # Edge cases
    pass


# Performance benchmarks
class TestMatchingPerformance:
    """Performance tests for matching algorithms"""
    
    def test_single_match_analysis_performance(self):
        """Test performance of single match analysis"""
        # Should complete comprehensive analysis in < 2 seconds
        pass
    
    def test_batch_matching_performance(self):
        """Test performance of batch matching operations"""
        # Should handle multiple match analyses efficiently
        pass
    
    def test_memory_usage_optimization(self):
        """Test memory usage during matching operations"""
        # Should not exceed reasonable memory limits
        pass


if __name__ == "__main__":
    # Run specific test suites
    pytest.main([__file__, "-v"])