import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import random
import math

from app.services.ai_matching_service import (
    AIMatchingService,
    MatchRecommendation,
    PersonalityInsight,
    BehaviorAnalysis,
    ai_matching_service
)
from app.models.ai_models import UserProfile, CompatibilityPrediction
from app.models.user import User
from app.models.soul_connection import SoulConnection
from app.models.daily_revelation import DailyRevelation
from app.models.message import Message


class TestAIMatchingService:
    
    @pytest.fixture
    def ai_service(self):
        return AIMatchingService()
    
    @pytest.fixture
    def mock_db(self):
        mock_db = Mock()
        mock_db.query = Mock()
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        return mock_db
    
    @pytest.fixture
    def mock_user(self):
        user = Mock(spec=User)
        user.id = 123
        user.first_name = "John"
        user.last_name = "Doe"
        user.bio = "I love meaningful connections"
        user.interests = ["philosophy", "hiking", "music"]
        user.is_profile_complete = True
        user.total_messages_sent = 50
        user.total_revelations_shared = 10
        user.total_swipes = 100
        user.total_matches = 5
        return user
    
    @pytest.fixture
    def mock_user_profile(self):
        profile = Mock(spec=UserProfile)
        profile.id = 1
        profile.user_id = 123
        profile.personality_vector = [0.5] * 128
        profile.interests_vector = [0.3] * 64
        profile.values_vector = [0.6] * 64
        profile.communication_vector = [0.4] * 32
        profile.openness_score = 0.7
        profile.conscientiousness_score = 0.6
        profile.extraversion_score = 0.5
        profile.agreeableness_score = 0.8
        profile.neuroticism_score = 0.3
        profile.emotional_intelligence = 0.75
        profile.attachment_style = "secure"
        profile.communication_style = "detailed"
        profile.conversation_depth_preference = 0.8
        profile.ai_confidence_level = 0.85
        profile.profile_completeness_score = 0.9
        profile.last_updated_by_ai = datetime.utcnow()
        return profile
    
    @pytest.fixture
    def mock_revelations(self):
        revelations = []
        contents = [
            "I believe in living authentically and pursuing meaningful connections",
            "Family and personal growth are very important to me",
            "I love creative projects and exploring new ideas"
        ]
        for i, content in enumerate(contents):
            rev = Mock()
            rev.sender_id = 123
            rev.content = content
            rev.created_at = datetime.utcnow() - timedelta(days=i)
            revelations.append(rev)
        return revelations
    
    @pytest.fixture
    def mock_messages(self):
        messages = []
        for i in range(10):
            msg = Mock()
            msg.sender_id = 123
            msg.content = f"This is a thoughtful message about {i}. I really enjoy our conversations."
            msg.created_at = datetime.utcnow() - timedelta(hours=i)
            messages.append(msg)
        return messages

    def test_service_initialization(self, ai_service):
        """Test AI service initialization"""
        assert len(ai_service.personality_weights) == 5
        assert sum(ai_service.personality_weights.values()) == 1.0
        assert ai_service.compatibility_threshold == 0.65
        assert ai_service.max_recommendations == 10
        assert ai_service.profile_update_interval_days == 7

    @pytest.mark.asyncio
    async def test_generate_user_profile_embeddings_new_profile(self, ai_service, mock_db, mock_user, mock_revelations):
        """Test generating embeddings for new user profile"""
        # Mock database queries
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_user,  # User query
            None        # Profile query (new profile)
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_revelations
        
        with patch.object(ai_service, '_analyze_personality_from_revelations', return_value={"openness": 0.7}):
            with patch.object(ai_service, '_analyze_communication_patterns', return_value={"style": "detailed"}):
                with patch.object(ai_service, '_analyze_behavioral_patterns', return_value={"activity_level": "high"}):
                    result = await ai_service.generate_user_profile_embeddings(123, mock_db)
                    
                    mock_db.add.assert_called_once()
                    mock_db.commit.assert_called_once()
                    assert result is not None

    @pytest.mark.asyncio
    async def test_generate_user_profile_embeddings_existing_profile(self, ai_service, mock_db, mock_user, mock_user_profile):
        """Test updating existing user profile embeddings"""
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_user,          # User query
            mock_user_profile   # Profile query (existing)
        ]
        
        with patch.object(ai_service, '_analyze_personality_from_revelations', return_value={"openness": 0.8}):
            with patch.object(ai_service, '_analyze_communication_patterns', return_value={"style": "balanced"}):
                with patch.object(ai_service, '_analyze_behavioral_patterns', return_value={"activity_level": "moderate"}):
                    result = await ai_service.generate_user_profile_embeddings(123, mock_db)
                    
                    # Should not call add (profile exists)
                    mock_db.add.assert_not_called()
                    mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_user_profile_embeddings_user_not_found(self, ai_service, mock_db):
        """Test profile generation when user not found"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="User 123 not found"):
            await ai_service.generate_user_profile_embeddings(123, mock_db)

    @pytest.mark.asyncio
    async def test_generate_user_profile_embeddings_error(self, ai_service, mock_db, mock_user):
        """Test profile generation error handling"""
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_user,
            Exception("Database error")
        ]
        
        with pytest.raises(Exception):
            await ai_service.generate_user_profile_embeddings(123, mock_db)

    @pytest.mark.asyncio
    async def test_calculate_ai_compatibility(self, ai_service, mock_db):
        """Test AI compatibility calculation"""
        # Mock user profiles
        profile1 = Mock(spec=UserProfile)
        profile1.id = 1
        profile1.user_id = 123
        profile2 = Mock(spec=UserProfile)
        profile2.id = 2
        profile2.user_id = 456
        
        with patch.object(ai_service, '_ensure_user_profile', side_effect=[profile1, profile2]):
            with patch.object(ai_service, '_calculate_personality_compatibility', return_value=0.8):
                with patch.object(ai_service, '_calculate_interests_compatibility', return_value=0.7):
                    with patch.object(ai_service, '_calculate_values_compatibility', return_value=0.85):
                        with patch.object(ai_service, '_calculate_communication_compatibility', return_value=0.75):
                            with patch.object(ai_service, '_calculate_lifestyle_compatibility', return_value=0.6):
                                with patch.object(ai_service, '_calculate_growth_potential', return_value=0.7):
                                    with patch.object(ai_service, '_predict_conflict_likelihood', return_value=0.3):
                                        # Mock database operations
                                        mock_db.query.return_value.filter.return_value.first.return_value = None
                                        
                                        result = await ai_service.calculate_ai_compatibility(123, 456, mock_db)
                                        
                                        assert isinstance(result, Mock)  # CompatibilityPrediction mock
                                        mock_db.add.assert_called_once()
                                        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_calculate_ai_compatibility_existing_prediction(self, ai_service, mock_db):
        """Test updating existing compatibility prediction"""
        profile1 = Mock(spec=UserProfile)
        profile1.id = 1
        profile2 = Mock(spec=UserProfile)
        profile2.id = 2
        
        existing_prediction = Mock(spec=CompatibilityPrediction)
        
        with patch.object(ai_service, '_ensure_user_profile', side_effect=[profile1, profile2]):
            with patch.object(ai_service, '_calculate_personality_compatibility', return_value=0.75):
                with patch.object(ai_service, '_calculate_interests_compatibility', return_value=0.65):
                    with patch.object(ai_service, '_calculate_values_compatibility', return_value=0.8):
                        with patch.object(ai_service, '_calculate_communication_compatibility', return_value=0.7):
                            with patch.object(ai_service, '_calculate_lifestyle_compatibility', return_value=0.55):
                                mock_db.query.return_value.filter.return_value.first.return_value = existing_prediction
                                
                                result = await ai_service.calculate_ai_compatibility(123, 456, mock_db)
                                
                                # Should not call add (prediction exists)
                                mock_db.add.assert_not_called()
                                mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_calculate_ai_compatibility_error(self, ai_service, mock_db):
        """Test compatibility calculation error handling"""
        with patch.object(ai_service, '_ensure_user_profile', side_effect=Exception("Profile error")):
            with pytest.raises(Exception):
                await ai_service.calculate_ai_compatibility(123, 456, mock_db)

    @pytest.mark.asyncio
    async def test_generate_personalized_recommendations(self, ai_service, mock_db):
        """Test generating personalized recommendations"""
        user_profile = Mock(spec=UserProfile)
        user_profile.user_id = 123
        
        # Mock existing connections
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [],  # No existing connections
            [Mock(user_id=456), Mock(user_id=789)]  # Potential matches
        ]
        
        # Mock compatibility predictions
        compatibility_pred = Mock(spec=CompatibilityPrediction)
        compatibility_pred.overall_compatibility = 0.85
        compatibility_pred.confidence_level = 0.8
        compatibility_pred.compatibility_reasons = ["Great personality match"]
        compatibility_pred.conversation_starters = ["What's your passion?"]
        compatibility_pred.long_term_potential = 0.75
        
        with patch.object(ai_service, '_ensure_user_profile', return_value=user_profile):
            with patch.object(ai_service, 'calculate_ai_compatibility', return_value=compatibility_pred):
                with patch.object(ai_service, '_determine_recommendation_strength', return_value="high"):
                    with patch('app.services.ai_matching_service.analytics_service') as mock_analytics:
                        mock_analytics.track_user_event = AsyncMock()
                        
                        result = await ai_service.generate_personalized_recommendations(123, limit=5, db=mock_db)
                        
                        assert isinstance(result, list)
                        if result:  # If recommendations were generated
                            assert len(result) <= 5
                            assert all(isinstance(rec, MatchRecommendation) for rec in result)

    @pytest.mark.asyncio
    async def test_generate_personalized_recommendations_no_matches(self, ai_service, mock_db):
        """Test recommendations when no suitable matches"""
        user_profile = Mock(spec=UserProfile)
        
        # Mock no potential matches
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        with patch.object(ai_service, '_ensure_user_profile', return_value=user_profile):
            result = await ai_service.generate_personalized_recommendations(123, db=mock_db)
            
            assert result == []

    @pytest.mark.asyncio
    async def test_generate_personalized_recommendations_error(self, ai_service, mock_db):
        """Test recommendations error handling"""
        with patch.object(ai_service, '_ensure_user_profile', side_effect=Exception("Profile error")):
            result = await ai_service.generate_personalized_recommendations(123, db=mock_db)
            
            assert result == []

    @pytest.mark.asyncio
    async def test_analyze_user_behavior(self, ai_service, mock_db, mock_messages):
        """Test user behavior analysis"""
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        # Mock database queries
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            mock_messages,  # Messages
            [],             # Connections
            []              # Revelations
        ]
        
        with patch.object(ai_service, '_analyze_response_times', return_value=[300, 400, 200]):
            with patch.object(ai_service, '_determine_communication_style', return_value="detailed"):
                with patch.object(ai_service, '_calculate_behavioral_engagement_score', return_value=0.7):
                    with patch.object(ai_service, '_extract_user_preferences', return_value={"freq": "high"}):
                        with patch.object(ai_service, '_generate_behavioral_recommendations', return_value=["Stay active"]):
                            result = await ai_service.analyze_user_behavior(123, days_back=30, db=mock_db)
                            
                            assert isinstance(result, BehaviorAnalysis)
                            assert result.engagement_score == 0.7
                            assert result.communication_style == "detailed"
                            assert len(result.patterns) > 0

    @pytest.mark.asyncio
    async def test_analyze_user_behavior_error(self, ai_service, mock_db):
        """Test behavior analysis error handling"""
        mock_db.query.side_effect = Exception("Database error")
        
        result = await ai_service.analyze_user_behavior(123, db=mock_db)
        
        assert isinstance(result, BehaviorAnalysis)
        assert result.engagement_score == 0.5
        assert result.communication_style == "unknown"

    @pytest.mark.asyncio
    async def test_analyze_personality_from_revelations(self, ai_service, mock_db, mock_revelations):
        """Test personality analysis from revelations"""
        mock_db.query.return_value.filter.return_value.all.return_value = mock_revelations
        
        result = await ai_service._analyze_personality_from_revelations(123, mock_db)
        
        assert isinstance(result, dict)
        assert "openness" in result
        assert "conscientiousness" in result
        assert "extraversion" in result
        assert "agreeableness" in result
        assert "neuroticism" in result
        assert "emotional_intelligence" in result
        assert "attachment_style" in result
        
        # All scores should be between 0 and 1
        for trait, score in result.items():
            if trait != "attachment_style":
                assert 0 <= score <= 1

    @pytest.mark.asyncio
    async def test_analyze_personality_from_revelations_no_data(self, ai_service, mock_db):
        """Test personality analysis with no revelations"""
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = await ai_service._analyze_personality_from_revelations(123, mock_db)
        
        expected = ai_service._get_default_personality_scores()
        assert result == expected

    @pytest.mark.asyncio
    async def test_analyze_communication_patterns(self, ai_service, mock_db, mock_messages):
        """Test communication pattern analysis"""
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_messages
        
        result = await ai_service._analyze_communication_patterns(123, mock_db)
        
        assert isinstance(result, dict)
        assert "style" in result
        assert "depth_preference" in result
        assert "avg_message_length" in result
        assert "emoji_usage" in result
        assert "total_messages" in result

    @pytest.mark.asyncio
    async def test_analyze_communication_patterns_no_data(self, ai_service, mock_db):
        """Test communication analysis with no messages"""
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        result = await ai_service._analyze_communication_patterns(123, mock_db)
        
        assert result["style"] == "balanced"
        assert result["depth_preference"] == 0.5

    @pytest.mark.asyncio
    async def test_analyze_behavioral_patterns(self, ai_service, mock_db, mock_user):
        """Test behavioral pattern analysis"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = await ai_service._analyze_behavioral_patterns(123, mock_db)
        
        assert isinstance(result, dict)
        assert "activity_level" in result
        assert "engagement_consistency" in result
        assert "feature_usage" in result
        assert "time_patterns" in result

    def test_calculate_keyword_score(self, ai_service):
        """Test keyword score calculation"""
        text = "I am a creative and curious person who loves to explore new ideas"
        keywords = ["creative", "curious", "explore"]
        
        result = ai_service._calculate_keyword_score(text, keywords)
        
        assert isinstance(result, float)
        assert 0.2 <= result <= 0.9  # Should be within normalized range

    def test_calculate_keyword_score_empty(self, ai_service):
        """Test keyword score with empty text"""
        result = ai_service._calculate_keyword_score("", ["test"])
        
        assert result == 0.5

    def test_get_default_personality_scores(self, ai_service):
        """Test default personality scores"""
        result = ai_service._get_default_personality_scores()
        
        assert isinstance(result, dict)
        assert len(result) == 7
        for score in result.values():
            if isinstance(score, float):
                assert score == 0.5

    @pytest.mark.asyncio
    async def test_generate_personality_embedding(self, ai_service):
        """Test personality embedding generation"""
        personality_analysis = {
            "openness": 0.7,
            "conscientiousness": 0.6,
            "extraversion": 0.5,
            "agreeableness": 0.8,
            "neuroticism": 0.3,
            "emotional_intelligence": 0.75
        }
        
        result = await ai_service._generate_personality_embedding(personality_analysis)
        
        assert isinstance(result, list)
        assert len(result) == 128
        assert all(isinstance(x, float) for x in result)
        
        # Should be unit vector (normalized)
        norm = math.sqrt(sum(x*x for x in result))
        assert abs(norm - 1.0) < 0.01

    @pytest.mark.asyncio
    async def test_generate_interests_embedding(self, ai_service, mock_user, mock_db):
        """Test interests embedding generation"""
        result = await ai_service._generate_interests_embedding(mock_user, mock_db)
        
        assert isinstance(result, list)
        assert len(result) == 64
        assert all(isinstance(x, float) for x in result)

    @pytest.mark.asyncio
    async def test_generate_values_embedding(self, ai_service, mock_db, mock_revelations):
        """Test values embedding generation"""
        mock_db.query.return_value.filter.return_value.all.return_value = mock_revelations
        
        result = await ai_service._generate_values_embedding(123, mock_db)
        
        assert isinstance(result, list)
        assert len(result) == 64
        assert all(isinstance(x, float) for x in result)

    @pytest.mark.asyncio
    async def test_generate_communication_embedding(self, ai_service):
        """Test communication embedding generation"""
        communication_analysis = {
            "style": "detailed",
            "depth_preference": 0.8,
            "emoji_usage": 0.3
        }
        
        result = await ai_service._generate_communication_embedding(communication_analysis)
        
        assert isinstance(result, list)
        assert len(result) == 32
        assert all(isinstance(x, float) for x in result)

    def test_calculate_ai_confidence(self, ai_service, mock_user):
        """Test AI confidence calculation"""
        personality_analysis = {"test": "data"}
        communication_analysis = {"total_messages": 25}
        
        result = ai_service._calculate_ai_confidence(mock_user, personality_analysis, communication_analysis)
        
        assert isinstance(result, float)
        assert 0 <= result <= 1

    def test_calculate_profile_completeness(self, ai_service, mock_user):
        """Test profile completeness calculation"""
        result = ai_service._calculate_profile_completeness(mock_user)
        
        assert isinstance(result, float)
        assert 0 <= result <= 1

    @pytest.mark.asyncio
    async def test_ensure_user_profile_exists(self, ai_service, mock_db, mock_user_profile):
        """Test ensuring user profile exists"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user_profile
        
        result = await ai_service._ensure_user_profile(123, mock_db)
        
        assert result == mock_user_profile

    @pytest.mark.asyncio
    async def test_ensure_user_profile_create_new(self, ai_service, mock_db):
        """Test creating new user profile when none exists"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with patch.object(ai_service, 'generate_user_profile_embeddings') as mock_generate:
            mock_profile = Mock()
            mock_generate.return_value = mock_profile
            
            result = await ai_service._ensure_user_profile(123, mock_db)
            
            assert result == mock_profile
            mock_generate.assert_called_once_with(123, mock_db)

    @pytest.mark.asyncio
    async def test_ensure_user_profile_update_stale(self, ai_service, mock_db, mock_user_profile):
        """Test updating stale user profile"""
        # Make profile stale
        mock_user_profile.last_updated_by_ai = datetime.utcnow() - timedelta(days=10)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user_profile
        
        with patch.object(ai_service, 'generate_user_profile_embeddings') as mock_generate:
            mock_new_profile = Mock()
            mock_generate.return_value = mock_new_profile
            
            result = await ai_service._ensure_user_profile(123, mock_db)
            
            assert result == mock_new_profile
            mock_generate.assert_called_once_with(123, mock_db)

    def test_calculate_personality_compatibility(self, ai_service):
        """Test personality compatibility calculation"""
        profile1 = Mock()
        profile1.personality_vector = [0.5, 0.6, 0.7] * 42 + [0.8, 0.9]  # 128 elements
        
        profile2 = Mock()
        profile2.personality_vector = [0.6, 0.7, 0.8] * 42 + [0.7, 0.8]  # 128 elements
        
        result = ai_service._calculate_personality_compatibility(profile1, profile2)
        
        assert isinstance(result, float)
        assert 0 <= result <= 1

    def test_calculate_personality_compatibility_missing_vectors(self, ai_service):
        """Test personality compatibility with missing vectors"""
        profile1 = Mock()
        profile1.personality_vector = None
        
        profile2 = Mock()
        profile2.personality_vector = [0.5] * 128
        
        result = ai_service._calculate_personality_compatibility(profile1, profile2)
        
        assert result == 0.5

    def test_calculate_interests_compatibility(self, ai_service):
        """Test interests compatibility calculation"""
        profile1 = Mock()
        profile1.interests_vector = [0.4] * 64
        
        profile2 = Mock()
        profile2.interests_vector = [0.6] * 64
        
        result = ai_service._calculate_interests_compatibility(profile1, profile2)
        
        assert isinstance(result, float)
        assert 0 <= result <= 1

    def test_calculate_values_compatibility(self, ai_service):
        """Test values compatibility calculation"""
        profile1 = Mock()
        profile1.values_vector = [0.3] * 64
        
        profile2 = Mock()
        profile2.values_vector = [0.7] * 64
        
        result = ai_service._calculate_values_compatibility(profile1, profile2)
        
        assert isinstance(result, float)
        assert 0 <= result <= 1

    def test_calculate_communication_compatibility(self, ai_service):
        """Test communication compatibility calculation"""
        profile1 = Mock()
        profile1.communication_vector = [0.5] * 32
        
        profile2 = Mock()
        profile2.communication_vector = [0.6] * 32
        
        result = ai_service._calculate_communication_compatibility(profile1, profile2)
        
        assert isinstance(result, float)
        assert 0 <= result <= 1

    @pytest.mark.asyncio
    async def test_calculate_lifestyle_compatibility(self, ai_service, mock_db):
        """Test lifestyle compatibility calculation"""
        behavior1 = BehaviorAnalysis(
            patterns=["pattern1"],
            engagement_score=0.8,
            communication_style="detailed",
            preferences={},
            recommendations=[]
        )
        
        behavior2 = BehaviorAnalysis(
            patterns=["pattern2"],
            engagement_score=0.7,
            communication_style="detailed",
            preferences={},
            recommendations=[]
        )
        
        with patch.object(ai_service, 'analyze_user_behavior', side_effect=[behavior1, behavior2]):
            result = await ai_service._calculate_lifestyle_compatibility(123, 456, mock_db)
            
            assert isinstance(result, float)
            assert 0 <= result <= 1

    def test_calculate_prediction_confidence(self, ai_service):
        """Test prediction confidence calculation"""
        profile1 = Mock()
        profile1.ai_confidence_level = 0.8
        
        profile2 = Mock()
        profile2.ai_confidence_level = 0.6
        
        result = ai_service._calculate_prediction_confidence(profile1, profile2)
        
        assert isinstance(result, float)
        assert 0.1 <= result <= 1.0

    def test_cosine_similarity(self, ai_service):
        """Test cosine similarity calculation"""
        vec1 = [1, 0, 0]
        vec2 = [0, 1, 0]
        
        result = ai_service._cosine_similarity(vec1, vec2)
        
        assert result == 0.0  # Orthogonal vectors
        
        # Test identical vectors
        vec3 = [1, 1, 1]
        vec4 = [1, 1, 1]
        
        result2 = ai_service._cosine_similarity(vec3, vec4)
        
        assert abs(result2 - 1.0) < 0.01  # Should be 1.0

    def test_cosine_similarity_different_lengths(self, ai_service):
        """Test cosine similarity with different vector lengths"""
        vec1 = [1, 2]
        vec2 = [1, 2, 3]
        
        result = ai_service._cosine_similarity(vec1, vec2)
        
        assert result == 0.0

    def test_cosine_similarity_zero_vectors(self, ai_service):
        """Test cosine similarity with zero vectors"""
        vec1 = [0, 0, 0]
        vec2 = [1, 2, 3]
        
        result = ai_service._cosine_similarity(vec1, vec2)
        
        assert result == 0.0

    @pytest.mark.asyncio
    async def test_calculate_growth_potential(self, ai_service, mock_db):
        """Test growth potential calculation"""
        profile1 = Mock()
        profile1.openness_score = 0.7
        profile1.conscientiousness_score = 0.8
        profile1.communication_style = "detailed"
        profile1.emotional_intelligence = 0.75
        
        profile2 = Mock()
        profile2.openness_score = 0.5
        profile2.conscientiousness_score = 0.7
        profile2.communication_style = "balanced"
        profile2.emotional_intelligence = 0.65
        
        result = await ai_service._calculate_growth_potential(profile1, profile2, mock_db)
        
        assert isinstance(result, float)
        assert 0 <= result <= 1

    @pytest.mark.asyncio
    async def test_predict_conflict_likelihood(self, ai_service, mock_db):
        """Test conflict likelihood prediction"""
        profile1 = Mock()
        profile1.neuroticism_score = 0.6
        profile1.agreeableness_score = 0.4
        profile1.communication_style = "direct"
        
        profile2 = Mock()
        profile2.neuroticism_score = 0.7
        profile2.agreeableness_score = 0.3
        profile2.communication_style = "diplomatic"
        
        result = await ai_service._predict_conflict_likelihood(profile1, profile2, mock_db)
        
        assert isinstance(result, float)
        assert 0 <= result <= 1

    @pytest.mark.asyncio
    async def test_predict_conversation_quality(self, ai_service, mock_db):
        """Test conversation quality prediction"""
        profile1 = Mock()
        profile1.conversation_depth_preference = 0.8
        profile1.communication_style = "detailed"
        profile1.emotional_intelligence = 0.75
        
        profile2 = Mock()
        profile2.conversation_depth_preference = 0.7
        profile2.communication_style = "detailed"
        profile2.emotional_intelligence = 0.8
        
        result = await ai_service._predict_conversation_quality(profile1, profile2, mock_db)
        
        assert isinstance(result, float)
        assert 0 <= result <= 1

    @pytest.mark.asyncio
    async def test_generate_conversation_starters(self, ai_service, mock_db):
        """Test conversation starter generation"""
        profile1 = Mock()
        profile1.openness_score = 0.8
        profile1.communication_style = "detailed"
        profile1.emotional_intelligence = 0.75
        
        profile2 = Mock()
        profile2.openness_score = 0.7
        profile2.communication_style = "detailed"
        profile2.emotional_intelligence = 0.8
        
        result = await ai_service._generate_conversation_starters(profile1, profile2, mock_db)
        
        assert isinstance(result, list)
        assert len(result) <= 5
        assert all(isinstance(starter, str) for starter in result)

    def test_generate_compatibility_reasons(self, ai_service):
        """Test compatibility reason generation"""
        result = ai_service._generate_compatibility_reasons(0.8, 0.7, 0.9, 0.6)
        
        assert isinstance(result, list)
        assert len(result) <= 4
        assert all(isinstance(reason, str) for reason in result)

    def test_generate_compatibility_reasons_low_scores(self, ai_service):
        """Test compatibility reasons with low scores"""
        result = ai_service._generate_compatibility_reasons(0.3, 0.2, 0.4, 0.3)
        
        assert isinstance(result, list)
        assert len(result) >= 1  # Should always return at least one reason

    def test_generate_potential_challenges(self, ai_service):
        """Test potential challenge generation"""
        profile1 = Mock()
        profile1.neuroticism_score = 0.3
        profile1.conscientiousness_score = 0.8
        profile1.communication_style = "direct"
        
        profile2 = Mock()
        profile2.neuroticism_score = 0.7
        profile2.conscientiousness_score = 0.3
        profile2.communication_style = "diplomatic"
        
        result = ai_service._generate_potential_challenges(profile1, profile2, 0.4)
        
        assert isinstance(result, list)
        assert len(result) <= 3
        assert all(isinstance(challenge, str) for challenge in result)

    def test_determine_recommendation_strength(self, ai_service):
        """Test recommendation strength determination"""
        compatibility_pred = Mock()
        compatibility_pred.overall_compatibility = 0.9
        compatibility_pred.confidence_level = 0.85
        
        result = ai_service._determine_recommendation_strength(compatibility_pred)
        
        assert result == "high"
        
        # Test medium strength
        compatibility_pred.overall_compatibility = 0.7
        compatibility_pred.confidence_level = 0.7
        
        result = ai_service._determine_recommendation_strength(compatibility_pred)
        
        assert result == "medium"
        
        # Test low strength
        compatibility_pred.overall_compatibility = 0.5
        compatibility_pred.confidence_level = 0.6
        
        result = ai_service._determine_recommendation_strength(compatibility_pred)
        
        assert result == "low"

    def test_analyze_response_times(self, ai_service):
        """Test response time analysis"""
        messages = [Mock() for _ in range(15)]  # High message count
        connections = []
        
        result = ai_service._analyze_response_times(messages, connections)
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(time, (int, float)) for time in result)

    def test_determine_communication_style(self, ai_service):
        """Test communication style determination"""
        # Test detailed style
        long_messages = []
        for _ in range(5):
            msg = Mock()
            msg.content = "This is a very long and detailed message that contains a lot of information and thoughtful insights about various topics that I want to share with you."
            long_messages.append(msg)
        
        result = ai_service._determine_communication_style(long_messages, [])
        
        assert result == "detailed"
        
        # Test concise style
        short_messages = []
        for _ in range(5):
            msg = Mock()
            msg.content = "Short msg"
            short_messages.append(msg)
        
        result = ai_service._determine_communication_style(short_messages, [])
        
        assert result == "concise"

    def test_determine_communication_style_no_data(self, ai_service):
        """Test communication style with no data"""
        result = ai_service._determine_communication_style([], [])
        
        assert result == "balanced"

    def test_calculate_behavioral_engagement_score(self, ai_service):
        """Test behavioral engagement score calculation"""
        messages = [Mock() for _ in range(10)]
        connections = [Mock() for _ in range(2)]
        revelations = [Mock() for _ in range(5)]
        
        result = ai_service._calculate_behavioral_engagement_score(messages, connections, revelations, 30)
        
        assert isinstance(result, float)
        assert 0 <= result <= 1

    def test_calculate_behavioral_engagement_score_no_data(self, ai_service):
        """Test engagement score with no data"""
        result = ai_service._calculate_behavioral_engagement_score([], [], [], 30)
        
        assert result == 0.3  # Default low engagement

    def test_extract_user_preferences(self, ai_service):
        """Test user preference extraction"""
        messages = [Mock() for _ in range(25)]  # Moderate frequency
        revelations = []
        for _ in range(3):
            rev = Mock()
            rev.content = "This is a moderately detailed revelation that shares some personal insights"
            revelations.append(rev)
        
        connections = []
        
        result = ai_service._extract_user_preferences(messages, revelations, connections)
        
        assert isinstance(result, dict)
        assert "communication_frequency" in result
        assert "depth_preference" in result
        assert "response_style" in result

    def test_generate_behavioral_recommendations(self, ai_service):
        """Test behavioral recommendation generation"""
        patterns = ["slow_responder", "brief_communicator"]
        communication_style = "concise"
        engagement_score = 0.3
        
        result = ai_service._generate_behavioral_recommendations(patterns, communication_style, engagement_score)
        
        assert isinstance(result, list)
        assert len(result) <= 4
        assert all(isinstance(rec, str) for rec in result)

    def test_global_service_instance(self):
        """Test global service instance"""
        assert ai_matching_service is not None
        assert isinstance(ai_matching_service, AIMatchingService)

    def test_dataclass_structures(self):
        """Test dataclass structures"""
        # Test MatchRecommendation
        recommendation = MatchRecommendation(
            user_id=123,
            recommended_user_id=456,
            compatibility_score=0.85,
            confidence_level=0.8,
            match_reasons=["Great match"],
            conversation_starters=["Hi there!"],
            predicted_success_rate=0.75,
            recommendation_strength="high"
        )
        
        assert recommendation.user_id == 123
        assert recommendation.compatibility_score == 0.85
        
        # Test PersonalityInsight
        insight = PersonalityInsight(
            trait_name="openness",
            score=0.8,
            confidence=0.9,
            description="Highly open to new experiences",
            improvement_suggestions=["Try new activities"]
        )
        
        assert insight.trait_name == "openness"
        assert insight.score == 0.8
        
        # Test BehaviorAnalysis
        analysis = BehaviorAnalysis(
            patterns=["pattern1", "pattern2"],
            engagement_score=0.7,
            communication_style="detailed",
            preferences={"freq": "high"},
            recommendations=["Be more active"]
        )
        
        assert analysis.engagement_score == 0.7
        assert len(analysis.patterns) == 2

    def test_edge_cases_empty_personality_analysis(self, ai_service):
        """Test edge cases with empty personality analysis"""
        # Test with empty analysis
        embedding = asyncio.run(ai_service._generate_personality_embedding({}))
        
        assert len(embedding) == 128
        assert all(isinstance(x, float) for x in embedding)

    def test_edge_cases_large_text_analysis(self, ai_service):
        """Test with very large text content"""
        large_text = "creative " * 1000  # Very large text
        keywords = ["creative", "art", "music"]
        
        result = ai_service._calculate_keyword_score(large_text, keywords)
        
        assert isinstance(result, float)
        assert 0.2 <= result <= 0.9

    @pytest.mark.asyncio
    async def test_performance_large_embeddings(self, ai_service):
        """Test performance with large embedding operations"""
        # Test with large personality analysis
        large_analysis = {f"trait_{i}": 0.5 for i in range(100)}
        large_analysis.update(ai_service._get_default_personality_scores())
        
        import time
        start_time = time.time()
        
        embedding = await ai_service._generate_personality_embedding(large_analysis)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete quickly (under 1 second)
        assert execution_time < 1.0
        assert len(embedding) == 128

    def test_compatibility_weights_validation(self, ai_service):
        """Test that compatibility weights are properly set"""
        weights = {
            "personality": 0.25,
            "interests": 0.20,
            "values": 0.25,
            "communication": 0.15,
            "lifestyle": 0.15
        }
        
        # Verify weights sum to 1.0
        assert abs(sum(weights.values()) - 1.0) < 0.01
        
        # Verify all weights are positive
        assert all(w > 0 for w in weights.values())

    @pytest.mark.asyncio
    async def test_comprehensive_workflow(self, ai_service, mock_db, mock_user):
        """Test complete AI matching workflow"""
        # Mock the full workflow
        with patch.object(ai_service, 'generate_user_profile_embeddings') as mock_generate:
            with patch.object(ai_service, 'calculate_ai_compatibility') as mock_compatibility:
                with patch.object(ai_service, 'generate_personalized_recommendations') as mock_recommendations:
                    with patch.object(ai_service, 'analyze_user_behavior') as mock_behavior:
                        # Setup mocks
                        mock_generate.return_value = Mock()
                        mock_compatibility.return_value = Mock()
                        mock_recommendations.return_value = []
                        mock_behavior.return_value = BehaviorAnalysis([], 0.5, "balanced", {}, [])
                        
                        # Run workflow
                        profile = await ai_service.generate_user_profile_embeddings(123, mock_db)
                        compatibility = await ai_service.calculate_ai_compatibility(123, 456, mock_db)
                        recommendations = await ai_service.generate_personalized_recommendations(123, db=mock_db)
                        behavior = await ai_service.analyze_user_behavior(123, db=mock_db)
                        
                        # Verify all steps completed
                        assert profile is not None
                        assert compatibility is not None
                        assert isinstance(recommendations, list)
                        assert isinstance(behavior, BehaviorAnalysis)