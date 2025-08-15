import pytest
from fastapi.testclient import TestClient
from fastapi import status
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session
from datetime import datetime, date

from app.main import app
from app.models.user import User
from app.models.ai_models import UserProfile
from app.api.v1.routers.ai_matching import _get_trait_suggestions, _calculate_age


class TestAIMatchingRouter:
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_user(self):
        user = Mock(spec=User)
        user.id = 123
        user.email = "test@example.com"
        user.username = "testuser"
        user.first_name = "John"
        user.last_name = "Doe"
        user.date_of_birth = "1990-05-15"
        user.bio = "Adventure seeker and coffee lover"
        user.interests = ["travel", "photography", "hiking"]
        user.location = "San Francisco, CA"
        return user
    
    @pytest.fixture
    def mock_target_user(self):
        user = Mock(spec=User)
        user.id = 456
        user.email = "target@example.com"
        user.username = "targetuser"
        user.first_name = "Jane"
        user.last_name = "Smith"
        user.date_of_birth = "1992-08-20"
        user.bio = "Love reading and outdoor activities"
        user.interests = ["reading", "hiking", "yoga"]
        user.location = "Oakland, CA"
        return user
    
    @pytest.fixture
    def mock_user_profile(self, mock_user):
        profile = Mock(spec=UserProfile)
        profile.user_id = mock_user.id
        profile.openness_score = 0.8
        profile.conscientiousness_score = 0.7
        profile.extraversion_score = 0.6
        profile.agreeableness_score = 0.9
        profile.neuroticism_score = 0.3
        profile.ai_confidence_level = 0.85
        profile.profile_completeness_score = 0.92
        profile.last_updated_by_ai = datetime.utcnow()
        
        # Mock methods
        profile.get_personality_summary.return_value = {
            "openness": 0.8,
            "conscientiousness": 0.7,
            "extraversion": 0.6,
            "agreeableness": 0.9,
            "neuroticism": 0.3
        }
        return profile
    
    @pytest.fixture
    def mock_match_recommendations(self):
        return [
            Mock(
                recommended_user_id=456,
                compatibility_score=0.89,
                confidence_level=0.82,
                match_reasons=["High emotional compatibility", "Shared interests in travel"],
                conversation_starters=["What's your favorite travel destination?", "Tell me about your photography"],
                predicted_success_rate=0.75,
                recommendation_strength="strong"
            ),
            Mock(
                recommended_user_id=789,
                compatibility_score=0.76,
                confidence_level=0.71,
                match_reasons=["Similar personality traits", "Compatible communication style"],
                conversation_starters=["What book are you reading?", "How do you like to spend weekends?"],
                predicted_success_rate=0.65,
                recommendation_strength="moderate"
            )
        ]
    
    @pytest.fixture
    def mock_compatibility_prediction(self):
        compatibility = Mock()
        compatibility.get_compatibility_insights.return_value = {
            "overall_score": 0.82,
            "confidence": 0.78,
            "strengths": ["Emotional compatibility", "Shared values", "Communication style"],
            "potential_challenges": ["Different life goals", "Varying social preferences"],
            "conversation_starters": ["What drives your passion for travel?", "How do you handle stress?"],
            "breakdown": {
                "personality": 0.85,
                "interests": 0.78,
                "values": 0.83,
                "communication": 0.80
            },
            "predictions": {
                "conversation_success": 0.75,
                "date_likelihood": 0.68,
                "long_term_potential": 0.72
            }
        }
        return compatibility
    
    @pytest.fixture
    def mock_behavior_analysis(self):
        analysis = Mock()
        analysis.patterns = ["Active evenings", "Weekend adventurer", "Deep conversationalist"]
        analysis.engagement_score = 0.78
        analysis.communication_style = "thoughtful_and_direct"
        analysis.preferences = {"conversation_depth": "deep", "activity_level": "high"}
        analysis.recommendations = ["Share more about your adventures", "Ask open-ended questions"]
        return analysis
    
    @pytest.fixture
    def auth_headers(self):
        return {"Authorization": "Bearer fake_token"}

    @pytest.mark.asyncio
    async def test_generate_ai_profile_success(self, client, mock_db, mock_user, mock_user_profile, auth_headers):
        """Test successful AI profile generation"""
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.services.ai_matching_service.ai_matching_service.generate_user_profile_embeddings',
                          return_value=mock_user_profile):
                    response = client.get(
                        "/api/v1/ai-matching/profile/generate",
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert data["user_id"] == mock_user.id
                    assert data["ai_confidence_level"] == 0.85
                    assert data["profile_completeness_score"] == 0.92
                    assert len(data["insights"]) == 5  # Big Five traits
                    
                    # Check insights structure
                    openness_insight = next(i for i in data["insights"] if i["trait_name"] == "Openness")
                    assert openness_insight["score"] == 0.8
                    assert openness_insight["percentile"] == 80.0

    @pytest.mark.asyncio
    async def test_generate_ai_profile_service_error(self, client, mock_db, mock_user, auth_headers):
        """Test AI profile generation with service error"""
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.services.ai_matching_service.ai_matching_service.generate_user_profile_embeddings',
                          side_effect=Exception("AI service error")):
                    response = client.get(
                        "/api/v1/ai-matching/profile/generate",
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                    assert "Failed to generate AI profile" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_ai_match_recommendations_success(
        self, client, mock_db, mock_user, mock_target_user, mock_match_recommendations, auth_headers
    ):
        """Test successful AI match recommendations retrieval"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_target_user
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.services.ai_matching_service.ai_matching_service.generate_personalized_recommendations',
                          return_value=mock_match_recommendations):
                    response = client.get(
                        "/api/v1/ai-matching/recommendations?limit=5",
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert len(data) == 2
                    assert data[0]["user_id"] == 456
                    assert data[0]["compatibility_score"] == 0.89
                    assert data[0]["recommendation_strength"] == "strong"
                    assert data[0]["user_profile"]["first_name"] == "Jane"

    @pytest.mark.asyncio
    async def test_get_ai_match_recommendations_with_params(
        self, client, mock_db, mock_user, mock_match_recommendations, auth_headers
    ):
        """Test AI match recommendations with query parameters"""
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.services.ai_matching_service.ai_matching_service.generate_personalized_recommendations',
                          return_value=[]):
                    response = client.get(
                        "/api/v1/ai-matching/recommendations?limit=3&refresh=true",
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert isinstance(data, list)

    def test_get_ai_match_recommendations_invalid_limit(self, client, auth_headers):
        """Test AI match recommendations with invalid limit parameter"""
        response = client.get(
            "/api/v1/ai-matching/recommendations?limit=50",  # Exceeds max limit
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_get_ai_match_recommendations_service_error(self, client, mock_db, mock_user, auth_headers):
        """Test AI match recommendations with service error"""
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.services.ai_matching_service.ai_matching_service.generate_personalized_recommendations',
                          side_effect=Exception("Recommendation service error")):
                    response = client.get(
                        "/api/v1/ai-matching/recommendations",
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                    assert "Failed to generate recommendations" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_compatibility_analysis_success(
        self, client, mock_db, mock_user, mock_target_user, mock_compatibility_prediction, auth_headers
    ):
        """Test successful compatibility analysis"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_target_user
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.services.ai_matching_service.ai_matching_service.calculate_ai_compatibility',
                          return_value=mock_compatibility_prediction):
                    response = client.get(
                        f"/api/v1/ai-matching/compatibility/{mock_target_user.id}",
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert data["overall_score"] == 0.82
                    assert data["confidence"] == 0.78
                    assert len(data["strengths"]) == 3
                    assert len(data["potential_challenges"]) == 2
                    assert "personality" in data["breakdown"]
                    assert "conversation_success" in data["predictions"]

    def test_get_compatibility_analysis_self(self, client, mock_user, auth_headers):
        """Test compatibility analysis with self (should fail)"""
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            response = client.get(
                f"/api/v1/ai-matching/compatibility/{mock_user.id}",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Cannot calculate compatibility with yourself" in response.json()["detail"]

    def test_get_compatibility_analysis_user_not_found(self, client, mock_db, mock_user, auth_headers):
        """Test compatibility analysis with non-existent user"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                response = client.get(
                    "/api/v1/ai-matching/compatibility/999",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_404_NOT_FOUND
                assert "User not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_compatibility_analysis_service_error(
        self, client, mock_db, mock_user, mock_target_user, auth_headers
    ):
        """Test compatibility analysis with service error"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_target_user
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.services.ai_matching_service.ai_matching_service.calculate_ai_compatibility',
                          side_effect=Exception("Compatibility calculation error")):
                    response = client.get(
                        f"/api/v1/ai-matching/compatibility/{mock_target_user.id}",
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                    assert "Failed to analyze compatibility" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_personality_insights_success(
        self, client, mock_db, mock_user, mock_user_profile, mock_behavior_analysis, auth_headers
    ):
        """Test successful personality insights retrieval"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user_profile
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.services.ai_matching_service.ai_matching_service.analyze_user_behavior',
                          return_value=mock_behavior_analysis):
                    response = client.get(
                        "/api/v1/ai-matching/insights/personality",
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert data["success"] is True
                    assert "personality" in data
                    assert "behavior_analysis" in data
                    assert "profile_stats" in data
                    assert data["behavior_analysis"]["engagement_score"] == 0.78
                    assert data["profile_stats"]["ai_confidence"] == 0.85

    def test_get_personality_insights_no_profile(self, client, mock_db, mock_user, auth_headers):
        """Test personality insights when no AI profile exists"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                response = client.get(
                    "/api/v1/ai-matching/insights/personality",
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_404_NOT_FOUND
                assert "AI profile not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_personality_insights_service_error(
        self, client, mock_db, mock_user, mock_user_profile, auth_headers
    ):
        """Test personality insights with service error"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user_profile
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.services.ai_matching_service.ai_matching_service.analyze_user_behavior',
                          side_effect=Exception("Behavior analysis error")):
                    response = client.get(
                        "/api/v1/ai-matching/insights/personality",
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                    assert "Failed to get personality insights" in response.json()["detail"]

    def test_get_trait_suggestions_low_openness(self):
        """Test trait suggestions for low openness"""
        suggestions = _get_trait_suggestions("openness", 0.3)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert any("new hobbies" in suggestion.lower() for suggestion in suggestions)

    def test_get_trait_suggestions_high_conscientiousness(self):
        """Test trait suggestions for high conscientiousness"""
        suggestions = _get_trait_suggestions("conscientiousness", 0.8)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert any("spontaneity" in suggestion.lower() for suggestion in suggestions)

    def test_get_trait_suggestions_unknown_trait(self):
        """Test trait suggestions for unknown trait"""
        suggestions = _get_trait_suggestions("unknown_trait", 0.5)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) == 1
        assert "Continue developing this trait" in suggestions[0]

    def test_calculate_age_valid_date(self):
        """Test age calculation with valid date"""
        # Using a fixed date for testing
        birth_date = "1990-05-15"
        age = _calculate_age(birth_date)
        
        # Age should be reasonable (between 20-40 for this test date)
        assert isinstance(age, int)
        assert 20 <= age <= 40

    def test_calculate_age_invalid_date(self):
        """Test age calculation with invalid date"""
        invalid_dates = ["invalid-date", "1990-13-45", "", None]
        
        for invalid_date in invalid_dates:
            age = _calculate_age(invalid_date)
            assert age is None

    def test_calculate_age_none_input(self):
        """Test age calculation with None input"""
        age = _calculate_age(None)
        assert age is None

    def test_calculate_age_leap_year(self):
        """Test age calculation with leap year birth date"""
        birth_date = "1992-02-29"  # Leap year
        age = _calculate_age(birth_date)
        
        assert isinstance(age, int)
        assert 25 <= age <= 35

    def test_unauthorized_access(self, client):
        """Test unauthorized access to AI matching endpoints"""
        endpoints = [
            "/api/v1/ai-matching/profile/generate",
            "/api/v1/ai-matching/recommendations",
            "/api/v1/ai-matching/compatibility/123",
            "/api/v1/ai-matching/insights/personality"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    @pytest.mark.asyncio
    async def test_recommendations_empty_result(self, client, mock_db, mock_user, auth_headers):
        """Test AI recommendations when no matches are found"""
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.services.ai_matching_service.ai_matching_service.generate_personalized_recommendations',
                          return_value=[]):
                    response = client.get(
                        "/api/v1/ai-matching/recommendations",
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert len(data) == 0

    def test_personality_insights_response_structure(self, client, mock_db, mock_user, mock_user_profile, mock_behavior_analysis, auth_headers):
        """Test personality insights response structure"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user_profile
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.services.ai_matching_service.ai_matching_service.analyze_user_behavior',
                          return_value=mock_behavior_analysis):
                    response = client.get(
                        "/api/v1/ai-matching/insights/personality",
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    
                    # Check required fields
                    required_fields = ["success", "personality", "behavior_analysis", "profile_stats"]
                    for field in required_fields:
                        assert field in data
                    
                    # Check behavior_analysis structure
                    behavior = data["behavior_analysis"]
                    behavior_required = ["patterns", "engagement_score", "communication_style", "preferences", "recommendations"]
                    for field in behavior_required:
                        assert field in behavior
                    
                    # Check profile_stats structure
                    stats = data["profile_stats"]
                    stats_required = ["ai_confidence", "completeness"]
                    for field in stats_required:
                        assert field in stats

    @pytest.mark.asyncio
    async def test_ai_profile_with_missing_traits(self, client, mock_db, mock_user, auth_headers):
        """Test AI profile generation with missing personality traits"""
        incomplete_profile = Mock(spec=UserProfile)
        incomplete_profile.user_id = mock_user.id
        incomplete_profile.openness_score = None  # Missing trait
        incomplete_profile.conscientiousness_score = 0.7
        incomplete_profile.extraversion_score = None  # Missing trait
        incomplete_profile.agreeableness_score = 0.9
        incomplete_profile.neuroticism_score = 0.3
        incomplete_profile.ai_confidence_level = 0.85
        incomplete_profile.profile_completeness_score = 0.60  # Lower due to missing traits
        incomplete_profile.last_updated_by_ai = datetime.utcnow()
        incomplete_profile.get_personality_summary.return_value = {
            "conscientiousness": 0.7,
            "agreeableness": 0.9,
            "neuroticism": 0.3
        }
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.services.ai_matching_service.ai_matching_service.generate_user_profile_embeddings',
                          return_value=incomplete_profile):
                    response = client.get(
                        "/api/v1/ai-matching/profile/generate",
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert data["profile_completeness_score"] == 0.60
                    # Should still handle missing traits gracefully

    @pytest.mark.asyncio
    async def test_compatibility_analysis_edge_cases(self, client, mock_db, mock_user, mock_target_user, auth_headers):
        """Test compatibility analysis with edge case scores"""
        edge_case_compatibility = Mock()
        edge_case_compatibility.get_compatibility_insights.return_value = {
            "overall_score": 0.0,  # Very low compatibility
            "confidence": 1.0,  # Very high confidence
            "strengths": [],  # No strengths
            "potential_challenges": ["Complete incompatibility", "No shared interests"],
            "conversation_starters": [],  # No suggested starters
            "breakdown": {
                "personality": 0.1,
                "interests": 0.0,
                "values": 0.05,
                "communication": 0.15
            },
            "predictions": {
                "conversation_success": 0.1,
                "date_likelihood": 0.05,
                "long_term_potential": 0.02
            }
        }
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_target_user
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.services.ai_matching_service.ai_matching_service.calculate_ai_compatibility',
                          return_value=edge_case_compatibility):
                    response = client.get(
                        f"/api/v1/ai-matching/compatibility/{mock_target_user.id}",
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert data["overall_score"] == 0.0
                    assert data["confidence"] == 1.0
                    assert len(data["strengths"]) == 0
                    assert len(data["conversation_starters"]) == 0

    def test_logging_in_endpoints(self, client, mock_db, mock_user, auth_headers):
        """Test that errors are properly logged in endpoints"""
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.services.ai_matching_service.ai_matching_service.generate_user_profile_embeddings',
                          side_effect=Exception("Test error")):
                    with patch('app.api.v1.routers.ai_matching.logger') as mock_logger:
                        response = client.get(
                            "/api/v1/ai-matching/profile/generate",
                            headers=auth_headers
                        )
                        
                        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
                        mock_logger.error.assert_called_once()
                        error_msg = mock_logger.error.call_args[0][0]
                        assert "Error generating AI profile" in error_msg

    @pytest.mark.asyncio
    async def test_recommendation_user_profile_data_completeness(
        self, client, mock_db, mock_user, mock_match_recommendations, auth_headers
    ):
        """Test that recommendation response includes complete user profile data"""
        # Mock user with all profile fields
        complete_user = Mock(spec=User)
        complete_user.id = 456
        complete_user.first_name = "Jane"
        complete_user.last_name = "Smith"
        complete_user.date_of_birth = "1992-08-20"
        complete_user.bio = "Adventure seeker"
        complete_user.interests = ["travel", "photography"]
        complete_user.location = "San Francisco"
        
        mock_db.query.return_value.filter.return_value.first.return_value = complete_user
        
        with patch('app.api.v1.deps.get_current_user', return_value=mock_user):
            with patch('app.core.database.get_db', return_value=mock_db):
                with patch('app.services.ai_matching_service.ai_matching_service.generate_personalized_recommendations',
                          return_value=mock_match_recommendations[:1]):  # Single recommendation
                    response = client.get(
                        "/api/v1/ai-matching/recommendations",
                        headers=auth_headers
                    )
                    
                    assert response.status_code == status.HTTP_200_OK
                    data = response.json()
                    assert len(data) == 1
                    
                    user_profile = data[0]["user_profile"]
                    assert user_profile["id"] == 456
                    assert user_profile["first_name"] == "Jane"
                    assert user_profile["last_name"] == "Smith"
                    assert user_profile["age"] is not None
                    assert user_profile["bio"] == "Adventure seeker"
                    assert user_profile["interests"] == ["travel", "photography"]
                    assert user_profile["location"] == "San Francisco"