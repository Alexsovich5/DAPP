import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation

from app.services.ai_matching import (
    PrivacyFirstMatchingAI,
    ai_matching_service,
    get_ai_matching_service
)


class TestPrivacyFirstMatchingAI:
    
    @pytest.fixture
    def ai_service(self):
        return PrivacyFirstMatchingAI()
    
    @pytest.fixture
    def mock_db(self):
        return Mock()
    
    @pytest.fixture
    def mock_profile(self):
        profile = Mock()
        profile.life_philosophy = "I believe in living authentically and pursuing meaningful connections"
        profile.core_values = {
            "authenticity": "Being true to oneself",
            "growth": "Continuous learning and development",
            "compassion": "Caring for others"
        }
        profile.interests = ["philosophy", "hiking", "reading", "music"]
        profile.personality_traits = {
            "introverted": "Enjoys quiet reflection and deep conversations",
            "creative": "Loves artistic expression and innovation",
            "empathetic": "Deeply understands others' emotions"
        }
        profile.communication_style = {
            "preferred_medium": "face_to_face",
            "conversation_style": "deep",
            "emotional_expression": "open",
            "conflict_resolution": "collaborative"
        }
        profile.responses = {
            "ideal_evening": "Meaningful conversation over dinner with someone special",
            "core_belief": "Everyone deserves to be understood and loved"
        }
        return profile
    
    @pytest.fixture
    def mock_user1(self, mock_profile):
        user = Mock()
        user.id = 123
        user.profile = mock_profile
        return user
    
    @pytest.fixture
    def mock_user2(self):
        user = Mock()
        user.id = 456
        profile = Mock()
        profile.life_philosophy = "Life is about building deep relationships and personal growth"
        profile.core_values = {
            "authenticity": "Honest communication",
            "adventure": "Exploring new experiences",
            "family": "Strong family bonds"
        }
        profile.interests = ["philosophy", "travel", "cooking", "art"]
        profile.personality_traits = {
            "extroverted": "Energized by social interactions",
            "analytical": "Logical problem-solving approach",
            "caring": "Always there for friends and family"
        }
        profile.communication_style = {
            "preferred_medium": "phone",
            "conversation_style": "thoughtful",
            "emotional_expression": "expressive", 
            "conflict_resolution": "discussion"
        }
        profile.responses = {
            "ideal_evening": "Exploring a new city with interesting company",
            "core_belief": "Growth comes through meaningful relationships"
        }
        user.profile = profile
        return user

    def test_service_initialization(self, ai_service):
        """Test AI service initialization"""
        assert isinstance(ai_service.vectorizer, TfidfVectorizer)
        assert isinstance(ai_service.lda_model, LatentDirichletAllocation)
        assert ai_service.is_initialized is False
        assert len(ai_service.compatibility_weights) == 6
        assert len(ai_service.starter_templates) > 0

    @pytest.mark.asyncio
    async def test_initialize_models_sufficient_data(self, ai_service, mock_db):
        """Test model initialization with sufficient data"""
        # Mock profile data
        mock_profiles = []
        for i in range(15):
            profile = Mock()
            profile.life_philosophy = f"Philosophy {i}"
            profile.core_values = {"value": f"test_value_{i}"}
            profile.interests = [f"interest_{i}"]
            mock_profiles.append(profile)
        
        mock_db.query.return_value.filter.return_value.all.return_value = mock_profiles
        
        with patch.object(ai_service, 'combine_profile_text_from_profile') as mock_combine:
            mock_combine.return_value = "test profile text"
            
            await ai_service.initialize_models(mock_db)
            
            assert ai_service.is_initialized is True

    @pytest.mark.asyncio
    async def test_initialize_models_insufficient_data(self, ai_service, mock_db):
        """Test model initialization with insufficient data"""
        # Mock insufficient profile data
        mock_profiles = [Mock() for _ in range(5)]  # Less than 10
        mock_db.query.return_value.filter.return_value.all.return_value = mock_profiles
        
        await ai_service.initialize_models(mock_db)
        
        assert ai_service.is_initialized is True

    @pytest.mark.asyncio
    async def test_initialize_models_error_handling(self, ai_service, mock_db):
        """Test model initialization error handling"""
        mock_db.query.side_effect = Exception("Database error")
        
        await ai_service.initialize_models(mock_db)
        
        assert ai_service.is_initialized is True

    def test_preprocess_text(self, ai_service):
        """Test text preprocessing"""
        text = "Hello, World! This is a TEST... with punctuation!!!"
        result = ai_service.preprocess_text(text)
        
        assert result == "hello world this is a test with punctuation"

    def test_preprocess_text_empty(self, ai_service):
        """Test preprocessing empty text"""
        assert ai_service.preprocess_text("") == ""
        assert ai_service.preprocess_text(None) == ""

    def test_combine_profile_text_from_profile(self, ai_service, mock_profile):
        """Test combining profile text"""
        result = ai_service.combine_profile_text_from_profile(mock_profile)
        
        assert "authenticity" in result.lower()
        assert "philosophy" in result.lower()
        assert "introverted" in result.lower()
        assert len(result) > 0

    def test_combine_profile_text_from_profile_empty(self, ai_service):
        """Test combining text from empty profile"""
        empty_profile = Mock()
        empty_profile.life_philosophy = None
        empty_profile.core_values = None
        empty_profile.interests = None
        empty_profile.personality_traits = None
        empty_profile.communication_style = None
        empty_profile.responses = None
        
        result = ai_service.combine_profile_text_from_profile(empty_profile)
        assert result == ""

    def test_combine_profile_text(self, ai_service, mock_user1):
        """Test combining profile text from user"""
        result = ai_service.combine_profile_text(mock_user1)
        
        assert "authenticity" in result.lower()
        assert "philosophy" in result.lower()

    @pytest.mark.asyncio
    async def test_calculate_semantic_similarity_initialized(self, ai_service, mock_user1, mock_user2):
        """Test semantic similarity calculation when models are initialized"""
        ai_service.is_initialized = True
        
        # Mock vectorizer behavior
        mock_tfidf_matrix = np.array([[1, 0, 0], [0.8, 0.2, 0]])
        mock_similarity = np.array([[1.0, 0.85], [0.85, 1.0]])
        
        with patch.object(ai_service.vectorizer, 'transform', return_value=mock_tfidf_matrix):
            with patch('app.services.ai_matching.cosine_similarity', return_value=mock_similarity):
                result = await ai_service.calculate_semantic_similarity(mock_user1, mock_user2)
                
                assert isinstance(result, float)
                assert 0 <= result <= 1

    @pytest.mark.asyncio
    async def test_calculate_semantic_similarity_not_initialized(self, ai_service, mock_user1, mock_user2):
        """Test semantic similarity calculation when models are not initialized"""
        ai_service.is_initialized = False
        
        with patch.object(ai_service, 'calculate_keyword_similarity', return_value=0.7) as mock_keyword:
            result = await ai_service.calculate_semantic_similarity(mock_user1, mock_user2)
            
            assert result == 0.7
            mock_keyword.assert_called_once()

    @pytest.mark.asyncio
    async def test_calculate_semantic_similarity_empty_text(self, ai_service, mock_user1):
        """Test semantic similarity with empty text"""
        empty_user = Mock()
        empty_user.profile = Mock()
        empty_user.profile.life_philosophy = None
        empty_user.profile.core_values = None
        empty_user.profile.interests = None
        empty_user.profile.personality_traits = None
        empty_user.profile.communication_style = None
        empty_user.profile.responses = None
        
        result = await ai_service.calculate_semantic_similarity(mock_user1, empty_user)
        
        assert result == 0.0

    @pytest.mark.asyncio
    async def test_calculate_semantic_similarity_error(self, ai_service, mock_user1, mock_user2):
        """Test semantic similarity calculation error handling"""
        ai_service.is_initialized = True
        
        with patch.object(ai_service.vectorizer, 'transform', side_effect=Exception("Transform error")):
            result = await ai_service.calculate_semantic_similarity(mock_user1, mock_user2)
            
            assert result == 0.0

    def test_calculate_keyword_similarity(self, ai_service):
        """Test keyword similarity calculation"""
        text1 = "I love philosophy and deep conversations"
        text2 = "Philosophy and meaningful discussions are important"
        
        result = ai_service.calculate_keyword_similarity(text1, text2)
        
        assert isinstance(result, float)
        assert 0 <= result <= 1
        assert result > 0  # Should have some overlap

    def test_calculate_keyword_similarity_empty(self, ai_service):
        """Test keyword similarity with empty texts"""
        assert ai_service.calculate_keyword_similarity("", "test") == 0.0
        assert ai_service.calculate_keyword_similarity("test", "") == 0.0
        assert ai_service.calculate_keyword_similarity("", "") == 0.0

    @pytest.mark.asyncio
    async def test_analyze_communication_compatibility(self, ai_service, mock_user1, mock_user2):
        """Test communication compatibility analysis"""
        result = await ai_service.analyze_communication_compatibility(mock_user1, mock_user2)
        
        assert isinstance(result, float)
        assert 0 <= result <= 1

    @pytest.mark.asyncio
    async def test_analyze_communication_compatibility_missing_data(self, ai_service, mock_user1):
        """Test communication compatibility with missing data"""
        empty_user = Mock()
        empty_user.profile = Mock()
        empty_user.profile.communication_style = None
        
        result = await ai_service.analyze_communication_compatibility(mock_user1, empty_user)
        
        assert result == 0.5  # Neutral score for missing data

    @pytest.mark.asyncio
    async def test_analyze_communication_compatibility_error(self, ai_service, mock_user1, mock_user2):
        """Test communication compatibility error handling"""
        with patch.object(mock_user1.profile, 'communication_style', side_effect=Exception("Access error")):
            result = await ai_service.analyze_communication_compatibility(mock_user1, mock_user2)
            
            assert result == 0.5

    def test_are_compatible_preferences(self, ai_service):
        """Test preference compatibility checking"""
        # Test compatible conversation styles
        assert ai_service.are_compatible_preferences("deep", "thoughtful", "conversation_style") is True
        assert ai_service.are_compatible_preferences("casual", "relaxed", "conversation_style") is True
        
        # Test incompatible preferences
        assert ai_service.are_compatible_preferences("deep", "casual", "conversation_style") is False
        
        # Test unknown aspect
        assert ai_service.are_compatible_preferences("test1", "test2", "unknown_aspect") is False

    @pytest.mark.asyncio
    async def test_analyze_emotional_compatibility(self, ai_service, mock_user1, mock_user2):
        """Test emotional compatibility analysis"""
        with patch.object(ai_service, 'calculate_emotional_depth', side_effect=[0.8, 0.7]):
            with patch.object(ai_service, 'compare_emotional_styles', return_value=0.6):
                result = await ai_service.analyze_emotional_compatibility(mock_user1, mock_user2)
                
                assert isinstance(result, float)
                assert 0 <= result <= 1

    @pytest.mark.asyncio
    async def test_analyze_emotional_compatibility_error(self, ai_service, mock_user1, mock_user2):
        """Test emotional compatibility error handling"""
        with patch.object(ai_service, 'calculate_emotional_depth', side_effect=Exception("Depth error")):
            result = await ai_service.analyze_emotional_compatibility(mock_user1, mock_user2)
            
            assert result == 0.5

    def test_calculate_emotional_depth(self, ai_service, mock_user1):
        """Test emotional depth calculation"""
        result = ai_service.calculate_emotional_depth(mock_user1)
        
        assert isinstance(result, float)
        assert 0 <= result <= 1

    def test_calculate_emotional_depth_empty_profile(self, ai_service):
        """Test emotional depth with empty profile"""
        empty_user = Mock()
        empty_user.profile = Mock()
        empty_user.profile.life_philosophy = None
        empty_user.profile.responses = None
        empty_user.profile.personality_traits = None
        
        result = ai_service.calculate_emotional_depth(empty_user)
        
        assert result == 0.0

    def test_compare_emotional_styles(self, ai_service):
        """Test emotional style comparison"""
        personality1 = {"introverted": "deep thinker", "empathetic": "caring"}
        personality2 = {"extroverted": "social", "caring": "supportive"}
        
        result = ai_service.compare_emotional_styles(personality1, personality2)
        
        assert isinstance(result, float)
        assert 0 <= result <= 1

    def test_compare_emotional_styles_empty(self, ai_service):
        """Test emotional style comparison with empty data"""
        assert ai_service.compare_emotional_styles({}, {"trait": "value"}) == 0.5
        assert ai_service.compare_emotional_styles({"trait": "value"}, {}) == 0.5
        assert ai_service.compare_emotional_styles({}, {}) == 0.5

    def test_are_complementary_traits(self, ai_service):
        """Test complementary trait identification"""
        assert ai_service.are_complementary_traits("introverted", "extroverted") is True
        assert ai_service.are_complementary_traits("creative", "analytical") is True
        assert ai_service.are_complementary_traits("introverted", "introverted") is False
        assert ai_service.are_complementary_traits("unknown1", "unknown2") is False

    @pytest.mark.asyncio
    async def test_analyze_life_goals_compatibility(self, ai_service, mock_user1, mock_user2):
        """Test life goals compatibility analysis"""
        with patch.object(ai_service, 'extract_life_goals', side_effect=[["goal1", "goal2"], ["goal1", "goal3"]]):
            with patch.object(ai_service, 'calculate_goal_alignment', return_value=0.75):
                result = await ai_service.analyze_life_goals_compatibility(mock_user1, mock_user2)
                
                assert result == 0.75

    @pytest.mark.asyncio
    async def test_analyze_life_goals_compatibility_missing_data(self, ai_service, mock_user1):
        """Test life goals compatibility with missing data"""
        empty_user = Mock()
        empty_user.profile = Mock()
        empty_user.profile.core_values = None
        
        result = await ai_service.analyze_life_goals_compatibility(mock_user1, empty_user)
        
        assert result == 0.5

    @pytest.mark.asyncio
    async def test_analyze_life_goals_compatibility_error(self, ai_service, mock_user1, mock_user2):
        """Test life goals compatibility error handling"""
        with patch.object(ai_service, 'extract_life_goals', side_effect=Exception("Extract error")):
            result = await ai_service.analyze_life_goals_compatibility(mock_user1, mock_user2)
            
            assert result == 0.5

    def test_extract_life_goals(self, ai_service):
        """Test life goal extraction"""
        core_values = {"family": "Important to me", "career": "Growth focused"}
        responses = {"future": "I want to achieve great things", "random": "Just text"}
        
        result = ai_service.extract_life_goals(core_values, responses)
        
        assert len(result) > 0
        assert any("family" in goal for goal in result)

    def test_extract_life_goals_empty(self, ai_service):
        """Test life goal extraction with empty data"""
        result = ai_service.extract_life_goals({}, {})
        
        assert result == []

    def test_calculate_goal_alignment(self, ai_service):
        """Test goal alignment calculation"""
        goals1 = ["family is important", "career growth", "travel the world"]
        goals2 = ["family values", "professional development", "health and fitness"]
        
        result = ai_service.calculate_goal_alignment(goals1, goals2)
        
        assert isinstance(result, float)
        assert 0 <= result <= 1

    def test_calculate_goal_alignment_empty(self, ai_service):
        """Test goal alignment with empty goals"""
        assert ai_service.calculate_goal_alignment([], ["goal"]) == 0.5
        assert ai_service.calculate_goal_alignment(["goal"], []) == 0.5
        assert ai_service.calculate_goal_alignment([], []) == 0.5

    def test_categorize_goals(self, ai_service):
        """Test goal categorization"""
        goals = ["I want a family", "career advancement", "travel the world"]
        categories = {
            "family": ["family", "children"],
            "career": ["career", "work"],
            "travel": ["travel", "explore"]
        }
        
        result = ai_service.categorize_goals(goals, categories)
        
        assert "family" in result
        assert "career" in result
        assert "travel" in result

    @pytest.mark.asyncio
    async def test_analyze_personality_compatibility(self, ai_service, mock_user1, mock_user2):
        """Test personality compatibility analysis"""
        with patch.object(ai_service, 'calculate_personality_similarity', return_value=0.7):
            with patch.object(ai_service, 'calculate_personality_complementarity', return_value=0.6):
                result = await ai_service.analyze_personality_compatibility(mock_user1, mock_user2)
                
                expected = 0.7 * 0.6 + 0.6 * 0.4  # Weighted average
                assert abs(result - expected) < 0.01

    @pytest.mark.asyncio
    async def test_analyze_personality_compatibility_missing_data(self, ai_service, mock_user1):
        """Test personality compatibility with missing data"""
        empty_user = Mock()
        empty_user.profile = Mock()
        empty_user.profile.personality_traits = None
        
        result = await ai_service.analyze_personality_compatibility(mock_user1, empty_user)
        
        assert result == 0.5

    @pytest.mark.asyncio
    async def test_analyze_personality_compatibility_error(self, ai_service, mock_user1, mock_user2):
        """Test personality compatibility error handling"""
        with patch.object(ai_service, 'calculate_personality_similarity', side_effect=Exception("Similarity error")):
            result = await ai_service.analyze_personality_compatibility(mock_user1, mock_user2)
            
            assert result == 0.5

    def test_calculate_personality_similarity(self, ai_service):
        """Test personality similarity calculation"""
        traits1 = {"introverted": "quiet and thoughtful", "creative": "artistic"}
        traits2 = {"introverted": "quiet and reflective", "analytical": "logical"}
        
        result = ai_service.calculate_personality_similarity(traits1, traits2)
        
        assert isinstance(result, float)
        assert 0 <= result <= 1

    def test_calculate_personality_similarity_no_common(self, ai_service):
        """Test personality similarity with no common traits"""
        traits1 = {"trait1": "description1"}
        traits2 = {"trait2": "description2"}
        
        result = ai_service.calculate_personality_similarity(traits1, traits2)
        
        assert result == 0.0

    def test_calculate_personality_complementarity(self, ai_service):
        """Test personality complementarity calculation"""
        traits1 = {"introverted": "quiet"}
        traits2 = {"extroverted": "social"}
        
        with patch.object(ai_service, 'are_complementary_traits', return_value=True):
            result = ai_service.calculate_personality_complementarity(traits1, traits2)
            
            assert result == 1.0

    def test_calculate_personality_complementarity_empty(self, ai_service):
        """Test personality complementarity with empty traits"""
        result = ai_service.calculate_personality_complementarity({}, {})
        
        assert result == 0.5

    @pytest.mark.asyncio
    async def test_calculate_comprehensive_compatibility(self, ai_service, mock_user1, mock_user2):
        """Test comprehensive compatibility calculation"""
        # Mock all component methods
        with patch.object(ai_service, 'calculate_semantic_similarity', return_value=0.8):
            with patch.object(ai_service, 'analyze_communication_compatibility', return_value=0.7):
                with patch.object(ai_service, 'analyze_emotional_compatibility', return_value=0.9):
                    with patch.object(ai_service, 'analyze_life_goals_compatibility', return_value=0.6):
                        with patch.object(ai_service, 'analyze_personality_compatibility', return_value=0.75):
                            with patch.object(ai_service, 'calculate_interest_overlap', return_value=0.5):
                                with patch.object(ai_service, 'calculate_confidence_level', return_value=0.85):
                                    with patch.object(ai_service, 'identify_unique_connection_factors', return_value=["factor1"]):
                                        result = await ai_service.calculate_comprehensive_compatibility(mock_user1, mock_user2)
                                        
                                        assert "ai_compatibility_score" in result
                                        assert "confidence_level" in result
                                        assert "compatibility_breakdown" in result
                                        assert "unique_connection_potential" in result
                                        assert "analysis_timestamp" in result
                                        
                                        assert isinstance(result["ai_compatibility_score"], float)
                                        assert 0 <= result["ai_compatibility_score"] <= 100

    @pytest.mark.asyncio
    async def test_calculate_comprehensive_compatibility_error(self, ai_service, mock_user1, mock_user2):
        """Test comprehensive compatibility error handling"""
        with patch.object(ai_service, 'calculate_semantic_similarity', side_effect=Exception("Analysis error")):
            result = await ai_service.calculate_comprehensive_compatibility(mock_user1, mock_user2)
            
            assert result["ai_compatibility_score"] == 50.0
            assert result["confidence_level"] == 10.0
            assert "error" in result

    def test_calculate_interest_overlap(self, ai_service, mock_user1, mock_user2):
        """Test interest overlap calculation"""
        result = ai_service.calculate_interest_overlap(mock_user1, mock_user2)
        
        assert isinstance(result, float)
        assert 0 <= result <= 1
        # Should have some overlap since both have "philosophy"
        assert result > 0

    def test_calculate_interest_overlap_empty(self, ai_service, mock_user1):
        """Test interest overlap with empty interests"""
        empty_user = Mock()
        empty_user.profile = Mock()
        empty_user.profile.interests = None
        
        result = ai_service.calculate_interest_overlap(mock_user1, empty_user)
        
        assert result == 0.0

    def test_calculate_confidence_level(self, ai_service, mock_user1, mock_user2):
        """Test confidence level calculation"""
        result = ai_service.calculate_confidence_level(mock_user1, mock_user2)
        
        assert isinstance(result, float)
        assert 0 <= result <= 1

    def test_calculate_confidence_level_empty_profiles(self, ai_service):
        """Test confidence level with empty profiles"""
        empty_user1 = Mock()
        empty_user1.profile = Mock()
        empty_user1.profile.life_philosophy = None
        empty_user1.profile.core_values = None
        empty_user1.profile.interests = None
        empty_user1.profile.personality_traits = None
        empty_user1.profile.communication_style = None
        empty_user1.profile.responses = None
        
        empty_user2 = Mock()
        empty_user2.profile = Mock()
        empty_user2.profile.life_philosophy = None
        empty_user2.profile.core_values = None
        empty_user2.profile.interests = None
        empty_user2.profile.personality_traits = None
        empty_user2.profile.communication_style = None
        empty_user2.profile.responses = None
        
        result = ai_service.calculate_confidence_level(empty_user1, empty_user2)
        
        assert result == 0.0

    @pytest.mark.asyncio
    async def test_identify_unique_connection_factors(self, ai_service, mock_user1, mock_user2):
        """Test unique connection factor identification"""
        result = await ai_service.identify_unique_connection_factors(mock_user1, mock_user2)
        
        assert isinstance(result, list)
        assert len(result) <= 3  # Should return top 3
        # Should find shared philosophy interest
        assert any("philosophy" in factor for factor in result)

    @pytest.mark.asyncio
    async def test_identify_unique_connection_factors_error(self, ai_service, mock_user1, mock_user2):
        """Test unique connection factors error handling"""
        with patch.object(mock_user1.profile, 'interests', side_effect=Exception("Access error")):
            result = await ai_service.identify_unique_connection_factors(mock_user1, mock_user2)
            
            assert result == []

    @pytest.mark.asyncio
    async def test_generate_conversation_starters(self, ai_service, mock_user1, mock_user2):
        """Test conversation starter generation"""
        mock_compatibility = {
            "compatibility_breakdown": {
                "life_goals": 80.0,
                "communication_style": 75.0,
                "personality_match": 70.0
            },
            "unique_connection_potential": ["shared passion for philosophy"]
        }
        
        with patch.object(ai_service, 'calculate_comprehensive_compatibility', return_value=mock_compatibility):
            result = await ai_service.generate_conversation_starters(mock_user1, mock_user2)
            
            assert isinstance(result, list)
            assert len(result) <= 3
            assert all(isinstance(starter, str) for starter in result)
            assert len(result) > 0

    @pytest.mark.asyncio
    async def test_generate_conversation_starters_no_matches(self, ai_service):
        """Test conversation starters with no compatibility matches"""
        empty_user1 = Mock()
        empty_user1.profile = Mock()
        empty_user1.profile.interests = []
        
        empty_user2 = Mock()
        empty_user2.profile = Mock()
        empty_user2.profile.interests = []
        
        mock_compatibility = {
            "compatibility_breakdown": {
                "life_goals": 30.0,
                "communication_style": 40.0,
                "personality_match": 35.0
            },
            "unique_connection_potential": []
        }
        
        with patch.object(ai_service, 'calculate_comprehensive_compatibility', return_value=mock_compatibility):
            result = await ai_service.generate_conversation_starters(empty_user1, empty_user2)
            
            assert len(result) == 1
            assert "passionate about" in result[0]

    @pytest.mark.asyncio
    async def test_generate_conversation_starters_error(self, ai_service, mock_user1, mock_user2):
        """Test conversation starter generation error handling"""
        with patch.object(ai_service, 'calculate_comprehensive_compatibility', side_effect=Exception("Analysis error")):
            result = await ai_service.generate_conversation_starters(mock_user1, mock_user2)
            
            assert len(result) == 1
            assert "passionate about" in result[0]

    def test_global_service_instance(self):
        """Test global service instance"""
        assert ai_matching_service is not None
        assert isinstance(ai_matching_service, PrivacyFirstMatchingAI)

    @pytest.mark.asyncio
    async def test_get_ai_matching_service(self):
        """Test getting AI matching service"""
        result = await get_ai_matching_service()
        
        assert result is ai_matching_service

    def test_compatibility_weights_sum(self, ai_service):
        """Test that compatibility weights sum to 1.0"""
        total_weight = sum(ai_service.compatibility_weights.values())
        
        assert abs(total_weight - 1.0) < 0.01  # Allow for small floating point errors

    def test_starter_templates_format(self, ai_service):
        """Test that starter templates have proper format"""
        for template in ai_service.starter_templates:
            assert isinstance(template, str)
            assert len(template) > 10  # Should be meaningful length
            assert "{" in template  # Should have format placeholders

    @pytest.mark.asyncio
    async def test_comprehensive_workflow(self, ai_service, mock_user1, mock_user2, mock_db):
        """Test complete AI matching workflow"""
        # Initialize models
        await ai_service.initialize_models(mock_db)
        
        # Calculate compatibility
        compatibility = await ai_service.calculate_comprehensive_compatibility(mock_user1, mock_user2)
        
        # Generate conversation starters
        starters = await ai_service.generate_conversation_starters(mock_user1, mock_user2)
        
        # Verify results
        assert "ai_compatibility_score" in compatibility
        assert len(starters) > 0
        assert ai_service.is_initialized is True

    def test_edge_case_empty_strings(self, ai_service):
        """Test edge cases with empty strings"""
        # Test preprocess with various empty inputs
        assert ai_service.preprocess_text("   ") == ""
        assert ai_service.preprocess_text("\n\t") == ""
        
        # Test keyword similarity with whitespace
        assert ai_service.calculate_keyword_similarity("   ", "test") == 0.0
        assert ai_service.calculate_keyword_similarity("test", "   ") == 0.0

    def test_edge_case_special_characters(self, ai_service):
        """Test handling of special characters"""
        text_with_special = "Hello! @#$%^&*() World???"
        result = ai_service.preprocess_text(text_with_special)
        
        # Should remove special characters but keep words
        assert "hello" in result
        assert "world" in result
        assert "@" not in result
        assert "!" not in result

    def test_edge_case_unicode_text(self, ai_service):
        """Test handling of unicode text"""
        unicode_text = "Café, naïve, résumé"
        result = ai_service.preprocess_text(unicode_text)
        
        # Should handle unicode gracefully
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_performance_large_profiles(self, ai_service):
        """Test performance with large profile data"""
        # Create users with large profile content
        large_user1 = Mock()
        large_user1.profile = Mock()
        large_user1.profile.life_philosophy = "Large text " * 1000
        large_user1.profile.core_values = {f"value_{i}": f"description_{i}" for i in range(100)}
        large_user1.profile.interests = [f"interest_{i}" for i in range(50)]
        large_user1.profile.personality_traits = {f"trait_{i}": f"desc_{i}" for i in range(20)}
        large_user1.profile.communication_style = {"style": "test"}
        large_user1.profile.responses = {f"q_{i}": f"answer_{i}" for i in range(50)}
        
        large_user2 = Mock()
        large_user2.profile = Mock()
        large_user2.profile.life_philosophy = "Different text " * 1000
        large_user2.profile.core_values = {f"value_{i}": f"description_{i}" for i in range(100, 200)}
        large_user2.profile.interests = [f"interest_{i}" for i in range(25, 75)]
        large_user2.profile.personality_traits = {f"trait_{i}": f"desc_{i}" for i in range(10, 30)}
        large_user2.profile.communication_style = {"style": "test"}
        large_user2.profile.responses = {f"q_{i}": f"answer_{i}" for i in range(25, 75)}
        
        # Test that it completes without timeout (should be fast)
        import time
        start_time = time.time()
        
        result = await ai_service.calculate_comprehensive_compatibility(large_user1, large_user2)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within reasonable time (5 seconds)
        assert execution_time < 5.0
        assert "ai_compatibility_score" in result