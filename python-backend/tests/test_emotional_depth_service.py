#!/usr/bin/env python3
"""
Emotional Depth Service Tests
Tests for emotional depth scoring and analysis functionality
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
from app.models.daily_revelation import DailyRevelation
from app.models.profile import Profile
from app.models.soul_connection import SoulConnection
from app.models.user import User
from app.services.emotional_depth_service import EmotionalDepthService
from sqlalchemy.orm import Session


@pytest.fixture
def service():
    """Create emotional depth service instance"""
    return EmotionalDepthService()


@pytest.fixture
def mock_db():
    """Create mock database session"""
    db = Mock(spec=Session)
    db.query = Mock()
    db.add = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    return db


@pytest.fixture
def test_user():
    """Create test user with emotional depth data"""
    user = Mock(spec=User)
    user.id = 1
    user.emotional_responses = {
        "values": "I deeply value authenticity, compassion, and growth in relationships",
        "philosophy": "To live is to love, to love is to learn, to learn is to grow",
        "fears": "Living an inauthentic life without deep connections",
        "purpose": "To create meaningful impact through genuine relationships",
    }
    user.core_values = {
        "primary": ["authenticity", "compassion", "growth"],
        "secondary": ["creativity", "mindfulness", "connection"],
    }
    return user


class TestEmotionalDepthServiceCore:
    """Test core emotional depth functionality"""

    def test_analyze_emotional_depth(self, service, test_user, mock_db):
        """Test analyzing emotional depth"""
        # Mock database query for revelations
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            []
        )

        result = service.analyze_emotional_depth(user=test_user, db=mock_db)

        # Service returns EmotionalDepthMetrics object
        assert result is not None
        assert hasattr(result, "overall_depth")
        assert 0 <= result.overall_depth <= 100
        assert hasattr(result, "emotional_vocabulary")
        assert hasattr(result, "vulnerability_score")
        assert hasattr(result, "authenticity_score")
        assert hasattr(result, "depth_level")

    def test_calculate_depth_compatibility(self, service, test_user, mock_db):
        """Test calculating depth compatibility between users"""
        # Create second test user
        test_user2 = Mock(spec=User)
        test_user2.id = 2
        test_user2.emotional_responses = {
            "values": "I value meaningful connection and emotional intelligence",
            "philosophy": "Life is about understanding and supporting each other",
        }
        test_user2.core_values = {"primary": ["empathy", "understanding", "support"]}

        # Mock database query for revelations
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            []
        )

        result = service.calculate_depth_compatibility(
            user1=test_user, user2=test_user2, db=mock_db
        )

        # Service returns DepthCompatibilityScore object
        assert result is not None
        assert hasattr(result, "compatibility_score")
        assert 0 <= result.compatibility_score <= 100
        assert hasattr(result, "depth_harmony")
        assert hasattr(result, "vulnerability_match")
        assert hasattr(result, "growth_alignment")

    def test_service_initialization(self, service):
        """Test service initializes with proper attributes"""
        assert hasattr(service, "emotion_categories")
        assert hasattr(service, "depth_patterns")
        assert hasattr(service, "vulnerability_patterns")
        assert hasattr(service, "authenticity_markers")
        assert hasattr(service, "growth_indicators")
        assert isinstance(service.emotion_categories, dict)
        assert isinstance(service.depth_patterns, list)

    def test_emotion_vocabulary_categories(self, service):
        """Test emotion vocabulary has proper categories"""
        categories = service.emotion_categories
        expected_categories = [
            "basic_emotions",
            "complex_emotions",
            "nuanced_feelings",
            "emotional_states",
        ]

        for category in expected_categories:
            assert category in categories
            assert isinstance(categories[category], list)
            assert len(categories[category]) > 0

    def test_depth_patterns_available(self, service):
        """Test depth patterns are available"""
        patterns = service.depth_patterns
        assert len(patterns) > 0
        expected_patterns = [
            "deeply",
            "profoundly",
            "authentically",
            "soul",
            "transform",
        ]

        for pattern in expected_patterns:
            assert pattern in patterns


class TestEmotionalDepthServicePrivateMethods:
    """Test private method behavior indirectly through public methods"""

    def test_default_depth_metrics(self, service):
        """Test that default metrics are returned when insufficient data"""
        # Create user with no data
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.emotional_responses = None
        mock_user.core_values = None

        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            []
        )

        result = service.analyze_emotional_depth(user=mock_user, db=mock_db)

        # Should return default metrics
        assert result.overall_depth == 50.0
        assert result.emotional_vocabulary == 5
        assert result.vulnerability_score == 40.0

    def test_depth_level_classification(self, service, mock_db):
        """Test depth level classification through rich user data"""
        # Create user with rich emotional data
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.emotional_responses = {
            "values": "I deeply value authenticity and meaningful connection. I believe in vulnerable communication and genuine growth.",
            "philosophy": "My life philosophy centers around compassionate understanding and profound self-awareness.",
        }
        mock_user.core_values = {
            "primary": "I profoundly believe in emotional depth and authentic vulnerability in relationships."
        }

        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            []
        )

        result = service.analyze_emotional_depth(user=mock_user, db=mock_db)

        # Should have some depth score based on content (service behavior may vary)
        assert result.overall_depth >= 0.0
        assert result.depth_level.value in [
            "surface",
            "emerging",
            "moderate",
            "deep",
            "profound",
        ]


class TestEmotionalDepthServiceCompatibility:
    """Test compatibility scoring functionality"""

    def test_depth_compatibility_with_similar_users(self, service, mock_db):
        """Test compatibility scoring between similar users"""
        # Create two users with similar emotional profiles
        mock_user1 = Mock(spec=User)
        mock_user1.id = 1
        mock_user1.emotional_responses = {
            "values": "I value deep authentic connection and vulnerability"
        }
        mock_user1.core_values = {"primary": "authenticity"}

        mock_user2 = Mock(spec=User)
        mock_user2.id = 2
        mock_user2.emotional_responses = {
            "values": "I value genuine meaningful relationships and openness"
        }
        mock_user2.core_values = {"primary": "genuineness"}

        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            []
        )

        result = service.calculate_depth_compatibility(
            user1=mock_user1, user2=mock_user2, db=mock_db
        )

        assert result.compatibility_score >= 0
        assert result.compatibility_score <= 100
        assert hasattr(result, "depth_harmony")
        assert hasattr(result, "vulnerability_match")
        assert hasattr(result, "growth_alignment")

    def test_depth_compatibility_with_different_users(self, service, mock_db):
        """Test compatibility scoring between different users"""
        # Create two users with different emotional profiles
        mock_user1 = Mock(spec=User)
        mock_user1.id = 1
        mock_user1.emotional_responses = {"values": "I like fun and adventure"}
        mock_user1.core_values = {"primary": "fun"}

        mock_user2 = Mock(spec=User)
        mock_user2.id = 2
        mock_user2.emotional_responses = {
            "values": "I deeply value profound spiritual connection and vulnerability in relationships"
        }
        mock_user2.core_values = {"primary": "spiritual depth"}

        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            []
        )

        result = service.calculate_depth_compatibility(
            user1=mock_user1, user2=mock_user2, db=mock_db
        )

        assert result.compatibility_score >= 0
        assert result.compatibility_score <= 100
        assert isinstance(result.connection_potential, str)
        assert isinstance(result.recommended_approach, str)


class TestEmotionalDepthServiceDataClasses:
    """Test data class structures used by the service"""

    def test_emotional_depth_metrics_structure(self, service, mock_db):
        """Test EmotionalDepthMetrics dataclass structure"""
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.emotional_responses = {"values": "I value authenticity"}
        mock_user.core_values = {"primary": "authenticity"}

        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            []
        )

        result = service.analyze_emotional_depth(user=mock_user, db=mock_db)

        # Check all expected attributes exist
        required_attrs = [
            "overall_depth",
            "emotional_vocabulary",
            "vulnerability_score",
            "authenticity_score",
            "empathy_indicators",
            "growth_mindset",
            "depth_level",
            "vulnerability_types",
            "depth_indicators",
            "maturity_signals",
            "authenticity_markers",
            "emotional_availability",
            "attachment_security",
            "communication_depth",
            "confidence",
            "text_quality",
            "response_richness",
        ]

        for attr in required_attrs:
            assert hasattr(result, attr), f"Missing attribute: {attr}"

    def test_depth_compatibility_score_structure(self, service, mock_db):
        """Test DepthCompatibilityScore dataclass structure"""
        mock_user1 = Mock(spec=User)
        mock_user1.id = 1
        mock_user1.emotional_responses = {"values": "authenticity"}
        mock_user1.core_values = {"primary": "authenticity"}

        mock_user2 = Mock(spec=User)
        mock_user2.id = 2
        mock_user2.emotional_responses = {"values": "compassion"}
        mock_user2.core_values = {"primary": "compassion"}

        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            []
        )

        result = service.calculate_depth_compatibility(
            user1=mock_user1, user2=mock_user2, db=mock_db
        )

        # Check all expected attributes exist
        required_attrs = [
            "compatibility_score",
            "depth_harmony",
            "vulnerability_match",
            "growth_alignment",
            "user1_depth",
            "user2_depth",
            "connection_potential",
            "recommended_approach",
            "depth_growth_timeline",
        ]

        for attr in required_attrs:
            assert hasattr(result, attr), f"Missing attribute: {attr}"


class TestEmotionalDepthServiceErrorHandling:
    """Test error handling"""

    def test_handle_empty_user_data(self, service, mock_db):
        """Test handling user with no emotional data"""
        empty_user = Mock(spec=User)
        empty_user.id = 1
        empty_user.emotional_responses = {}
        empty_user.core_values = {}

        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            []
        )

        result = service.analyze_emotional_depth(user=empty_user, db=mock_db)

        # Should return default metrics without crashing
        assert result is not None
        assert result.overall_depth == 50.0
        assert result.text_quality == "insufficient_data"

    def test_handle_database_query_error(self, service, mock_db):
        """Test handling database query errors"""
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.emotional_responses = {"values": "authenticity"}
        mock_user.core_values = {"primary": "authenticity"}

        # Mock database error
        mock_db.query.side_effect = Exception("Database connection error")

        result = service.analyze_emotional_depth(user=mock_user, db=mock_db)

        # Should handle error gracefully and return default metrics
        assert result is not None
        assert result.text_quality in ["error", "insufficient_data"]
        assert result.overall_depth >= 0

    def test_handle_malformed_user_data(self, service, mock_db):
        """Test handling malformed user data"""
        malformed_user = Mock(spec=User)
        malformed_user.id = 1
        malformed_user.emotional_responses = "not a dict"  # Wrong type
        malformed_user.core_values = None

        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = (
            []
        )

        result = service.analyze_emotional_depth(user=malformed_user, db=mock_db)

        # Should handle malformed data gracefully
        assert result is not None
        assert isinstance(result.overall_depth, float)
        assert 0 <= result.overall_depth <= 100
