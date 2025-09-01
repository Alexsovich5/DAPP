#!/usr/bin/env python3
"""
Comprehensive AI Matching Service Tests
Tests for the AI-powered matching and compatibility scoring system
"""

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import numpy as np
import pytest
from app.models.profile import Profile as EmotionalProfile
from app.models.soul_connection import ConnectionStage, SoulConnection
from app.models.user import User
from app.services.ai_matching_service import AIMatchingService


# Mock schemas since they may not exist yet
class CompatibilityScore:
    pass


class MatchRecommendation:
    pass


@pytest.fixture
def service():
    """Create AI matching service instance"""
    return AIMatchingService()


@pytest.fixture
def mock_db():
    """Create mock database session"""
    db = Mock()
    db.query = Mock()
    db.add = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    db.rollback = Mock()
    return db


@pytest.fixture
def test_user1():
    """Create test user 1"""
    user = Mock(spec=User)
    user.id = 1
    user.username = "soulseeker1"
    user.date_of_birth = datetime(1990, 1, 1)
    user.gender = "male"
    user.location = "New York, NY"
    user.interests = ["music", "travel", "philosophy", "cooking"]
    return user


@pytest.fixture
def test_user2():
    """Create test user 2"""
    user = Mock(spec=User)
    user.id = 2
    user.username = "dreamchaser2"
    user.date_of_birth = datetime(1992, 6, 15)
    user.gender = "female"
    user.location = "Brooklyn, NY"
    user.interests = ["art", "travel", "yoga", "music"]
    return user


@pytest.fixture
def ai_user_profile1():
    """Create comprehensive AI user profile for user 1 based on UserProfile model"""
    from app.models.ai_models import UserProfile

    profile = Mock(spec=UserProfile)

    # Basic attributes
    profile.id = 1
    profile.user_id = 1

    # AI-Generated Profile Vectors (required by service)
    profile.personality_vector = [
        0.8,
        0.7,
        0.6,
        0.75,
        0.3,
        0.85,
        0.65,
        0.9,
    ] * 16  # 128-dim
    profile.interests_vector = [0.1, 0.8, 0.6, 0.4, 0.9, 0.7, 0.3, 0.85] * 8  # 64-dim
    profile.values_vector = [0.9, 0.8, 0.7, 0.6, 0.5, 0.8, 0.75, 0.65] * 4  # 32-dim
    profile.communication_vector = [
        0.7,
        0.6,
        0.8,
        0.5,
        0.4,
        0.9,
        0.3,
        0.75,
    ] * 2  # 16-dim

    # Big 5 Personality Scores
    profile.openness_score = 0.8
    profile.conscientiousness_score = 0.7
    profile.extraversion_score = 0.6
    profile.agreeableness_score = 0.75
    profile.neuroticism_score = 0.3

    # Extended Personality Traits
    profile.emotional_intelligence = 0.8
    profile.attachment_style = "secure"
    profile.love_language_primary = "quality_time"
    profile.love_language_secondary = "acts_of_service"

    # Communication Analysis
    profile.communication_style = "expressive"
    profile.conversation_depth_preference = 0.85
    profile.response_time_pattern = {"average_hours": 2.5, "preferred_time": "evening"}
    profile.emoji_usage_pattern = {"frequency": "moderate", "sentiment": "positive"}

    # Behavioral Patterns
    profile.activity_patterns = {
        "peak_hours": [19, 20, 21],
        "days_active": [1, 2, 3, 4, 5],
    }
    profile.engagement_patterns = {
        "messages_per_conversation": 15,
        "response_rate": 0.9,
    }
    profile.decision_patterns = {
        "swipe_right_rate": 0.3,
        "message_initiation_rate": 0.7,
    }

    # AI Confidence Scores
    profile.profile_completeness_score = 95.0
    profile.ai_confidence_level = 0.9
    profile.data_quality_score = 0.85

    # Learning and Adaptation
    profile.learning_rate = 0.1
    profile.last_updated_by_ai = datetime.now()
    profile.ai_update_frequency = 7
    profile.manual_overrides = {}

    # Privacy and Consent
    profile.ai_profiling_consent = True
    profile.data_sharing_level = "aggregated"

    # Timestamps
    profile.created_at = datetime.now() - timedelta(days=30)
    profile.updated_at = datetime.now()

    return profile


@pytest.fixture
def ai_user_profile2():
    """Create comprehensive AI user profile for user 2 based on UserProfile model"""
    from app.models.ai_models import UserProfile

    profile = Mock(spec=UserProfile)

    # Basic attributes
    profile.id = 2
    profile.user_id = 2

    # AI-Generated Profile Vectors (required by service)
    profile.personality_vector = [
        0.85,
        0.65,
        0.5,
        0.8,
        0.35,
        0.9,
        0.7,
        0.75,
    ] * 16  # 128-dim
    profile.interests_vector = [0.2, 0.9, 0.7, 0.3, 0.8, 0.6, 0.4, 0.95] * 8  # 64-dim
    profile.values_vector = [0.8, 0.9, 0.6, 0.7, 0.4, 0.85, 0.65, 0.75] * 4  # 32-dim
    profile.communication_vector = [
        0.6,
        0.8,
        0.7,
        0.6,
        0.3,
        0.85,
        0.4,
        0.65,
    ] * 2  # 16-dim

    # Big 5 Personality Scores
    profile.openness_score = 0.85
    profile.conscientiousness_score = 0.65
    profile.extraversion_score = 0.5
    profile.agreeableness_score = 0.8
    profile.neuroticism_score = 0.35

    # Extended Personality Traits
    profile.emotional_intelligence = 0.85
    profile.attachment_style = "secure"
    profile.love_language_primary = "acts_of_service"
    profile.love_language_secondary = "words_of_affirmation"

    # Communication Analysis
    profile.communication_style = "diplomatic"
    profile.conversation_depth_preference = 0.9
    profile.response_time_pattern = {"average_hours": 1.5, "preferred_time": "morning"}
    profile.emoji_usage_pattern = {"frequency": "high", "sentiment": "warm"}

    # Behavioral Patterns
    profile.activity_patterns = {
        "peak_hours": [8, 9, 10, 18, 19],
        "days_active": [1, 2, 3, 4, 5, 6],
    }
    profile.engagement_patterns = {
        "messages_per_conversation": 22,
        "response_rate": 0.95,
    }
    profile.decision_patterns = {
        "swipe_right_rate": 0.25,
        "message_initiation_rate": 0.6,
    }

    # AI Confidence Scores
    profile.profile_completeness_score = 90.0
    profile.ai_confidence_level = 0.85
    profile.data_quality_score = 0.88

    # Learning and Adaptation
    profile.learning_rate = 0.12
    profile.last_updated_by_ai = datetime.now()
    profile.ai_update_frequency = 7
    profile.manual_overrides = {}

    # Privacy and Consent
    profile.ai_profiling_consent = True
    profile.data_sharing_level = "aggregated"

    # Timestamps
    profile.created_at = datetime.now() - timedelta(days=45)
    profile.updated_at = datetime.now()

    return profile


class TestAIMatchingServiceCore:
    """Test core AI matching functionality"""

    @pytest.mark.asyncio
    async def test_calculate_ai_compatibility(
        self,
        service,
        test_user1,
        test_user2,
        ai_user_profile1,
        ai_user_profile2,
        mock_db,
    ):
        """Test AI compatibility calculation"""

        # Mock the UserProfile database queries
        # The service may make multiple queries, so we need to handle different user_ids
        def mock_query_behavior(*args, **kwargs):
            mock_query = Mock()
            mock_filter = Mock()

            def mock_filter_behavior(*args, **kwargs):
                # Return the appropriate profile based on what's being filtered
                # This is a simplified approach - return user1 profile first, then user2
                mock_result = Mock()
                if not hasattr(mock_filter_behavior, "call_count"):
                    mock_filter_behavior.call_count = 0
                mock_filter_behavior.call_count += 1

                if mock_filter_behavior.call_count % 2 == 1:
                    mock_result.first.return_value = ai_user_profile1
                else:
                    mock_result.first.return_value = ai_user_profile2

                return mock_result

            mock_query.filter.side_effect = mock_filter_behavior
            return mock_query

        mock_db.query.side_effect = mock_query_behavior

        result = await service.calculate_ai_compatibility(
            user1_id=1, user2_id=2, db=mock_db
        )

        # Verify the result structure
        assert result is not None
        # Check the actual attributes from CompatibilityPrediction model
        assert hasattr(result, "overall_compatibility") or hasattr(
            result, "compatibility_score"
        )
        assert hasattr(result, "confidence_level") or hasattr(
            result, "prediction_confidence"
        )

        # The service returns values in 0-1 range
        if hasattr(result, "overall_compatibility"):
            assert 0 <= result.overall_compatibility <= 1
        elif hasattr(result, "compatibility_score"):
            assert 0 <= result.compatibility_score <= 1

    @pytest.mark.asyncio
    async def test_generate_match_recommendations(self, service, test_user1, mock_db):
        """Test generating match recommendations"""
        # Mock potential matches
        mock_matches = [test_user1]
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = (
            mock_matches
        )

        with patch.object(
            service,
            "calculate_ai_compatibility",
            return_value={"compatibility_score": 85, "confidence": 0.9},
        ):
            results = await service.generate_match_recommendations(
                user_id=1, limit=10, db=mock_db
            )

        assert isinstance(results, list)
        assert len(results) <= 10

    def test_calculate_personality_compatibility(
        self, service, emotional_profile1, emotional_profile2
    ):
        """Test personality compatibility calculation"""
        score = service._calculate_personality_compatibility(
            emotional_profile1.personality_traits, emotional_profile2.personality_traits
        )

        assert isinstance(score, float)
        assert 0 <= score <= 1
        # These profiles should be highly compatible
        assert score > 0.7

    def test_calculate_values_alignment(
        self, service, emotional_profile1, emotional_profile2
    ):
        """Test values alignment calculation"""
        score = service._calculate_values_alignment(
            emotional_profile1.core_values, emotional_profile2.core_values
        )

        assert isinstance(score, float)
        assert 0 <= score <= 1
        # They share "growth" as primary value
        assert score > 0.5

    def test_calculate_communication_compatibility(
        self, service, emotional_profile1, emotional_profile2
    ):
        """Test communication style compatibility"""
        score = service._calculate_communication_compatibility(
            emotional_profile1.communication_style,
            emotional_profile2.communication_style,
        )

        assert isinstance(score, float)
        assert 0 <= score <= 1

    def test_calculate_emotional_resonance(
        self, service, emotional_profile1, emotional_profile2
    ):
        """Test emotional resonance calculation"""
        resonance = service._calculate_emotional_resonance(
            emotional_profile1, emotional_profile2
        )

        assert isinstance(resonance, dict)
        assert "score" in resonance
        assert "depth_compatibility" in resonance
        assert "wavelength_match" in resonance

    @pytest.mark.asyncio
    async def test_generate_compatibility_insights(
        self, service, test_user1, test_user2, emotional_profile1, emotional_profile2
    ):
        """Test generating compatibility insights"""
        test_user1.emotional_profile = emotional_profile1
        test_user2.emotional_profile = emotional_profile2

        insights = await service.generate_compatibility_insights(
            user1=test_user1, user2=test_user2
        )

        assert isinstance(insights, dict)
        assert "strengths" in insights
        assert "growth_areas" in insights
        assert "communication_tips" in insights
        assert len(insights["strengths"]) > 0

    @pytest.mark.asyncio
    async def test_predict_relationship_success(self, service, mock_db):
        """Test relationship success prediction"""
        mock_connection = Mock(spec=SoulConnection)
        mock_connection.compatibility_score = 85.0
        mock_connection.total_messages_exchanged = 50
        mock_connection.mutual_engagement_score = 0.8

        with patch.object(service, "_run_success_prediction_model", return_value=0.75):
            prediction = await service.predict_relationship_success(
                connection=mock_connection, db=mock_db
            )

        assert isinstance(prediction, dict)
        assert "success_probability" in prediction
        assert "confidence" in prediction
        assert 0 <= prediction["success_probability"] <= 1

    def test_extract_personality_vector(self, service, emotional_profile1):
        """Test personality vector extraction"""
        vector = service._extract_personality_vector(emotional_profile1)

        assert isinstance(vector, np.ndarray) or isinstance(vector, list)
        assert len(vector) > 0
        # Check values are normalized
        if isinstance(vector, np.ndarray):
            assert np.all(vector >= 0) and np.all(vector <= 1)

    def test_calculate_interest_overlap(self, service, test_user1, test_user2):
        """Test interest overlap calculation"""
        score = service._calculate_interest_overlap(
            test_user1.interests, test_user2.interests
        )

        assert isinstance(score, float)
        assert 0 <= score <= 1
        # They share "music" and "travel"
        assert score > 0.3

    @pytest.mark.asyncio
    async def test_update_match_score_with_interactions(self, service, mock_db):
        """Test updating match score based on interactions"""
        mock_connection = Mock(spec=SoulConnection)
        mock_connection.id = 1
        mock_connection.compatibility_score = 75.0
        mock_connection.total_messages_exchanged = 100
        mock_connection.mutual_engagement_score = 0.85

        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_connection
        )

        updated_score = await service.update_match_score_with_interactions(
            connection_id=1, db=mock_db
        )

        assert isinstance(updated_score, float)
        assert updated_score >= 75.0  # Should improve with good engagement
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_get_compatibility_breakdown(
        self, service, test_user1, test_user2, emotional_profile1, emotional_profile2
    ):
        """Test detailed compatibility breakdown"""
        test_user1.emotional_profile = emotional_profile1
        test_user2.emotional_profile = emotional_profile2

        breakdown = await service.get_compatibility_breakdown(
            user1=test_user1, user2=test_user2
        )

        assert isinstance(breakdown, dict)
        assert "personality" in breakdown
        assert "values" in breakdown
        assert "communication" in breakdown
        assert "interests" in breakdown
        assert "emotional_depth" in breakdown
        assert all(0 <= v <= 100 for v in breakdown.values())

    @pytest.mark.asyncio
    async def test_find_soulmate_candidates(self, service, mock_db):
        """Test finding soulmate candidates"""
        mock_users = [Mock(spec=User) for _ in range(5)]
        mock_db.query.return_value.filter.return_value.all.return_value = mock_users

        with patch.object(
            service,
            "calculate_ai_compatibility",
            return_value={"compatibility_score": 90, "confidence": 0.95},
        ):
            candidates = await service.find_soulmate_candidates(
                user_id=1, min_score=85, db=mock_db
            )

        assert isinstance(candidates, list)
        assert all("user" in c and "score" in c for c in candidates)

    def test_calculate_growth_potential(
        self, service, emotional_profile1, emotional_profile2
    ):
        """Test relationship growth potential calculation"""
        potential = service._calculate_growth_potential(
            emotional_profile1, emotional_profile2
        )

        assert isinstance(potential, float)
        assert 0 <= potential <= 1
        # Both value growth highly
        assert potential > 0.7


class TestAIMatchingServiceML:
    """Test machine learning components"""

    def test_run_ml_model(self, service):
        """Test ML model execution"""
        features = np.array([0.8, 0.7, 0.85, 0.6, 0.9])

        with patch("app.services.ai_matching_service.load_model") as mock_load:
            mock_model = Mock()
            mock_model.predict.return_value = np.array([0.85])
            mock_load.return_value = mock_model

            result = service._run_ml_model(features)

        assert isinstance(result, float)
        assert 0 <= result <= 1

    def test_prepare_ml_features(
        self, service, test_user1, test_user2, emotional_profile1, emotional_profile2
    ):
        """Test ML feature preparation"""
        test_user1.emotional_profile = emotional_profile1
        test_user2.emotional_profile = emotional_profile2

        features = service._prepare_ml_features(test_user1, test_user2)

        assert isinstance(features, (list, np.ndarray))
        assert len(features) > 0

    def test_run_success_prediction_model(self, service):
        """Test success prediction model"""
        connection_features = {
            "compatibility_score": 85,
            "messages_exchanged": 100,
            "engagement_score": 0.8,
            "days_active": 30,
        }

        with patch(
            "app.services.ai_matching_service.load_prediction_model"
        ) as mock_load:
            mock_model = Mock()
            mock_model.predict_proba.return_value = np.array([[0.2, 0.8]])
            mock_load.return_value = mock_model

            result = service._run_success_prediction_model(connection_features)

        assert isinstance(result, float)
        assert 0 <= result <= 1


class TestAIMatchingServiceOptimization:
    """Test optimization and caching"""

    @pytest.mark.asyncio
    async def test_batch_compatibility_calculation(self, service, test_user1, mock_db):
        """Test batch processing of compatibility scores"""
        mock_users = [Mock(spec=User) for _ in range(10)]

        with patch.object(
            service,
            "calculate_ai_compatibility",
            return_value={"compatibility_score": 75, "confidence": 0.8},
        ):
            results = await service.batch_calculate_compatibility(
                user=test_user1, candidates=mock_users, db=mock_db
            )

        assert len(results) == len(mock_users)
        assert all("user_id" in r and "score" in r for r in results)

    @pytest.mark.asyncio
    async def test_cache_compatibility_score(self, service, mock_db):
        """Test caching of compatibility scores"""
        # First calculation
        with patch.object(service, "_get_cached_score", return_value=None):
            with patch.object(service, "_cache_score") as mock_cache:
                score = await service.get_or_calculate_compatibility(
                    user1_id=1, user2_id=2, db=mock_db
                )
                mock_cache.assert_called_once()

        # Second calculation should use cache
        with patch.object(service, "_get_cached_score", return_value=85.0):
            cached_score = await service.get_or_calculate_compatibility(
                user1_id=1, user2_id=2, db=mock_db
            )
            assert cached_score == 85.0

    def test_optimize_matching_algorithm(self, service):
        """Test matching algorithm optimization"""
        with patch.object(service, "_get_algorithm_version", return_value="v2.1"):
            version = service.get_current_algorithm_version()
            assert version == "v2.1"


class TestAIMatchingServiceEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_calculate_compatibility_missing_profile(
        self, service, test_user1, test_user2, mock_db
    ):
        """Test compatibility with missing emotional profile"""
        test_user1.emotional_profile = None
        test_user2.emotional_profile = None

        result = await service.calculate_ai_compatibility(
            user1=test_user1, user2=test_user2, db=mock_db
        )

        assert result["compatibility_score"] < 50  # Low score for missing profiles
        assert result["confidence"] < 0.5

    @pytest.mark.asyncio
    async def test_handle_ml_model_failure(
        self, service, test_user1, test_user2, mock_db
    ):
        """Test handling ML model failures"""
        with patch.object(
            service, "_run_ml_model", side_effect=Exception("Model error")
        ):
            # Should fall back to rule-based calculation
            result = await service.calculate_ai_compatibility(
                user1=test_user1, user2=test_user2, db=mock_db
            )

        assert isinstance(result, dict)
        assert "compatibility_score" in result

    def test_handle_empty_interests(self, service):
        """Test handling empty interest lists"""
        score = service._calculate_interest_overlap([], [])
        assert score == 0

        score = service._calculate_interest_overlap(["music"], [])
        assert score == 0

    def test_handle_invalid_personality_traits(self, service):
        """Test handling invalid personality trait values"""
        invalid_traits1 = {"openness": 1.5, "conscientiousness": -0.2}
        invalid_traits2 = {"openness": 0.8, "conscientiousness": 0.7}

        # Should normalize invalid values
        score = service._calculate_personality_compatibility(
            invalid_traits1, invalid_traits2
        )
        assert 0 <= score <= 1

    @pytest.mark.asyncio
    async def test_concurrent_compatibility_calculations(self, service, mock_db):
        """Test handling concurrent calculations"""
        import asyncio

        tasks = []
        for i in range(10):
            user1 = Mock(spec=User)
            user1.id = i
            user2 = Mock(spec=User)
            user2.id = i + 100

            task = service.calculate_ai_compatibility(user1, user2, mock_db)
            tasks.append(task)

        with patch.object(service, "_run_ml_model", return_value=0.75):
            results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert all(isinstance(r, dict) for r in results)


class TestAIMatchingServiceIntegration:
    """Test integration with other services"""

    @pytest.mark.asyncio
    async def test_integration_with_soul_compatibility(self, service, mock_db):
        """Test integration with soul compatibility service"""
        with patch(
            "app.services.soul_compatibility_service.SoulCompatibilityService"
        ) as mock_soul:
            mock_soul_instance = mock_soul.return_value
            mock_soul_instance.calculate_compatibility.return_value = Mock(
                total_score=80
            )

            combined_score = await service.calculate_combined_compatibility(
                user1_id=1, user2_id=2, db=mock_db
            )

            assert isinstance(combined_score, float)
            assert 0 <= combined_score <= 100

    @pytest.mark.asyncio
    async def test_trigger_match_notification(self, service, mock_db):
        """Test triggering notifications for high matches"""
        high_match = {"user_id": 2, "compatibility_score": 92}

        with patch(
            "app.services.notification_service.send_match_notification"
        ) as mock_notify:
            await service._trigger_high_match_notification(
                user_id=1, match=high_match, db=mock_db
            )
            mock_notify.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_preferences_from_interactions(self, service, mock_db):
        """Test updating user preferences based on interactions"""
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_interactions = [
            {"matched_user_traits": {"openness": 0.8}},
            {"matched_user_traits": {"openness": 0.85}},
        ]

        mock_db.query.return_value.filter.return_value.all.return_value = (
            mock_interactions
        )

        preferences = await service.learn_user_preferences(user_id=1, db=mock_db)

        assert isinstance(preferences, dict)
        assert "preferred_traits" in preferences
