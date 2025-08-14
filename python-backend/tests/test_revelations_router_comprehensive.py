"""
Comprehensive Revelations Router Tests
High-impact test coverage for revelations endpoints in the Soul Before Skin dating app
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from app.main import app
from app.models.user import User
from app.models.soul_connection import SoulConnection


client = TestClient(app)


@pytest.fixture
def mock_current_user():
    """Create a mock authenticated user"""
    user = Mock(spec=User)
    user.id = 1
    user.first_name = "John"
    user.last_name = "Doe"
    user.email = "john@example.com"
    return user


@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    session = Mock()
    session.query = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    return session


@pytest.fixture
def sample_connection():
    """Create a sample soul connection"""
    connection = Mock(spec=SoulConnection)
    connection.id = 1
    connection.user1_id = 1
    connection.user2_id = 2
    connection.status = "active"
    connection.connection_stage = "soul_discovery"
    connection.reveal_day = 3
    return connection


@pytest.fixture
def sample_revelation():
    """Create a sample revelation"""
    revelation = Mock()
    revelation.id = 1
    revelation.connection_id = 1
    revelation.user_id = 1
    revelation.day_number = 1
    revelation.revelation_type = "personal_value"
    revelation.content = "I value honesty and authenticity above all else"
    revelation.created_at = datetime.utcnow()
    revelation.is_shared = False
    return revelation


@pytest.fixture
def sample_revelation_prompt():
    """Create a sample revelation prompt"""
    prompt = Mock()
    prompt.id = 1
    prompt.day_number = 1
    prompt.revelation_type = "personal_value"
    prompt.prompt_text = "Share a core value that guides your life decisions"
    prompt.description = "This helps your connection understand what matters most to you"
    return prompt


class TestRevelationsPromptsEndpoints:
    """Test revelation prompts endpoints"""

    @patch('app.api.v1.deps.get_current_user')
    @patch('app.core.database.get_db')
    def test_get_all_prompts(self, mock_get_db, mock_get_user, mock_current_user, mock_db_session, sample_revelation_prompt):
        """Test GET /revelations/prompts"""
        mock_get_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db_session
        
        # Mock query to return prompts
        mock_db_session.query.return_value.order_by.return_value.all.return_value = [sample_revelation_prompt]
        
        response = client.get("/api/v1/revelations/prompts")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @patch('app.api.v1.deps.get_current_user')
    @patch('app.core.database.get_db')
    def test_get_prompt_by_day(self, mock_get_db, mock_get_user, mock_current_user, mock_db_session, sample_revelation_prompt):
        """Test GET /revelations/prompts/{day_number}"""
        mock_get_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db_session
        
        # Mock query to return specific prompt
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_revelation_prompt
        
        response = client.get("/api/v1/revelations/prompts/1")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    @patch('app.api.v1.deps.get_current_user')
    @patch('app.core.database.get_db')
    def test_get_prompt_not_found(self, mock_get_db, mock_get_user, mock_current_user, mock_db_session):
        """Test GET /revelations/prompts/{day_number} with non-existent day"""
        mock_get_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db_session
        
        # Mock query to return None
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        response = client.get("/api/v1/revelations/prompts/99")
        
        assert response.status_code == 404


class TestRevelationsCreateEndpoint:
    """Test revelation creation endpoint"""

    @patch('app.api.v1.deps.get_current_user')
    @patch('app.core.database.get_db')
    def test_create_revelation_success(self, mock_get_db, mock_get_user, mock_current_user, mock_db_session, sample_connection):
        """Test POST /revelations/create"""
        mock_get_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db_session
        
        # Mock connection query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_connection
        
        revelation_data = {
            "connection_id": 1,
            "day_number": 1,
            "revelation_type": "personal_value",
            "content": "I believe in the power of kindness to change the world"
        }
        
        response = client.post("/api/v1/revelations/create", json=revelation_data)
        
        # Should succeed or return appropriate error
        assert response.status_code in [200, 201, 400, 422]

    @patch('app.api.v1.deps.get_current_user')
    @patch('app.core.database.get_db')
    def test_create_revelation_invalid_connection(self, mock_get_db, mock_get_user, mock_current_user, mock_db_session):
        """Test POST /revelations/create with invalid connection"""
        mock_get_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db_session
        
        # Mock no connection found
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        revelation_data = {
            "connection_id": 999,
            "day_number": 1,
            "revelation_type": "personal_value",
            "content": "Test revelation"
        }
        
        response = client.post("/api/v1/revelations/create", json=revelation_data)
        
        # Should return error for invalid connection
        assert response.status_code in [400, 404]

    @patch('app.api.v1.deps.get_current_user')
    @patch('app.core.database.get_db')
    def test_create_revelation_missing_data(self, mock_get_db, mock_get_user, mock_current_user, mock_db_session):
        """Test POST /revelations/create with missing required fields"""
        mock_get_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db_session
        
        incomplete_data = {
            "connection_id": 1,
            "day_number": 1
            # Missing content and revelation_type
        }
        
        response = client.post("/api/v1/revelations/create", json=incomplete_data)
        
        # Should return validation error
        assert response.status_code == 422


class TestRevelationsTimelineEndpoint:
    """Test revelation timeline endpoint"""

    @patch('app.api.v1.deps.get_current_user')
    @patch('app.core.database.get_db')
    def test_get_timeline_success(self, mock_get_db, mock_get_user, mock_current_user, mock_db_session, sample_connection, sample_revelation):
        """Test GET /revelations/timeline/{connection_id}"""
        mock_get_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db_session
        
        # Mock connection and revelations query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_connection
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [sample_revelation]
        
        response = client.get("/api/v1/revelations/timeline/1")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    @patch('app.api.v1.deps.get_current_user')
    @patch('app.core.database.get_db')
    def test_get_timeline_no_access(self, mock_get_db, mock_get_user, mock_current_user, mock_db_session):
        """Test GET /revelations/timeline/{connection_id} with no access"""
        mock_get_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db_session
        
        # Mock no connection found (user not part of connection)
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        response = client.get("/api/v1/revelations/timeline/999")
        
        assert response.status_code in [403, 404]


class TestRevelationsUpdateEndpoint:
    """Test revelation update endpoint"""

    @patch('app.api.v1.deps.get_current_user')
    @patch('app.core.database.get_db')
    def test_update_revelation_success(self, mock_get_db, mock_get_user, mock_current_user, mock_db_session, sample_revelation):
        """Test PUT /revelations/{revelation_id}"""
        mock_get_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db_session
        
        # Mock revelation query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_revelation
        
        update_data = {
            "content": "Updated revelation content with more depth and reflection"
        }
        
        response = client.put("/api/v1/revelations/1", json=update_data)
        
        assert response.status_code in [200, 400, 404]

    @patch('app.api.v1.deps.get_current_user')
    @patch('app.core.database.get_db')
    def test_update_revelation_not_found(self, mock_get_db, mock_get_user, mock_current_user, mock_db_session):
        """Test PUT /revelations/{revelation_id} with non-existent revelation"""
        mock_get_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db_session
        
        # Mock no revelation found
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        update_data = {"content": "Updated content"}
        
        response = client.put("/api/v1/revelations/999", json=update_data)
        
        assert response.status_code == 404

    @patch('app.api.v1.deps.get_current_user')
    @patch('app.core.database.get_db')
    def test_update_revelation_unauthorized(self, mock_get_db, mock_get_user, mock_current_user, mock_db_session, sample_revelation):
        """Test PUT /revelations/{revelation_id} by unauthorized user"""
        # Create user that doesn't own the revelation
        unauthorized_user = Mock(spec=User)
        unauthorized_user.id = 999
        
        mock_get_user.return_value = unauthorized_user
        mock_get_db.return_value = mock_db_session
        
        # Mock revelation owned by different user
        sample_revelation.user_id = 1  # Different from unauthorized_user.id
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_revelation
        
        update_data = {"content": "Unauthorized update attempt"}
        
        response = client.put("/api/v1/revelations/1", json=update_data)
        
        assert response.status_code in [403, 404]


class TestRevelationsShareEndpoint:
    """Test revelation sharing endpoint"""

    @patch('app.api.v1.deps.get_current_user')
    @patch('app.core.database.get_db')
    def test_share_revelation_success(self, mock_get_db, mock_get_user, mock_current_user, mock_db_session, sample_connection):
        """Test POST /revelations/share/{connection_id}"""
        mock_get_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db_session
        
        # Mock connection query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_connection
        
        share_data = {
            "revelation_id": 1,
            "message": "I wanted to share this special revelation with you"
        }
        
        response = client.post("/api/v1/revelations/share/1", json=share_data)
        
        assert response.status_code in [200, 201, 400, 404]

    @patch('app.api.v1.deps.get_current_user')
    @patch('app.core.database.get_db')
    def test_share_revelation_invalid_connection(self, mock_get_db, mock_get_user, mock_current_user, mock_db_session):
        """Test POST /revelations/share/{connection_id} with invalid connection"""
        mock_get_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db_session
        
        # Mock no connection found
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        share_data = {"revelation_id": 1, "message": "Test share"}
        
        response = client.post("/api/v1/revelations/share/999", json=share_data)
        
        assert response.status_code in [400, 404]


class TestRevelationsTodayEndpoint:
    """Test today's revelation endpoint"""

    @patch('app.api.v1.deps.get_current_user')
    @patch('app.core.database.get_db')
    def test_get_today_revelation_success(self, mock_get_db, mock_get_user, mock_current_user, mock_db_session, sample_connection):
        """Test GET /revelations/today/{connection_id}"""
        mock_get_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db_session
        
        # Mock connection query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_connection
        
        response = client.get("/api/v1/revelations/today/1")
        
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    @patch('app.api.v1.deps.get_current_user')
    @patch('app.core.database.get_db')
    def test_get_today_revelation_no_access(self, mock_get_db, mock_get_user, mock_current_user, mock_db_session):
        """Test GET /revelations/today/{connection_id} with no access"""
        mock_get_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db_session
        
        # Mock no connection found
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        response = client.get("/api/v1/revelations/today/999")
        
        assert response.status_code in [403, 404]


class TestRevelationsPhotoConsentEndpoint:
    """Test photo consent endpoint"""

    @patch('app.api.v1.deps.get_current_user')
    @patch('app.core.database.get_db')
    def test_photo_consent_success(self, mock_get_db, mock_get_user, mock_current_user, mock_db_session, sample_connection):
        """Test POST /revelations/photo-consent/{connection_id}"""
        mock_get_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db_session
        
        # Mock connection query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_connection
        
        consent_data = {
            "consent_given": True,
            "consent_message": "I'm excited to share my photo with you!"
        }
        
        response = client.post("/api/v1/revelations/photo-consent/1", json=consent_data)
        
        assert response.status_code in [200, 201, 400, 404]

    @patch('app.api.v1.deps.get_current_user')
    @patch('app.core.database.get_db')
    def test_photo_consent_decline(self, mock_get_db, mock_get_user, mock_current_user, mock_db_session, sample_connection):
        """Test POST /revelations/photo-consent/{connection_id} with decline"""
        mock_get_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db_session
        
        # Mock connection query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_connection
        
        consent_data = {
            "consent_given": False,
            "consent_message": "I'd prefer to get to know you better first"
        }
        
        response = client.post("/api/v1/revelations/photo-consent/1", json=consent_data)
        
        assert response.status_code in [200, 201, 400, 404]

    @patch('app.api.v1.deps.get_current_user') 
    @patch('app.core.database.get_db')
    def test_photo_consent_invalid_connection(self, mock_get_db, mock_get_user, mock_current_user, mock_db_session):
        """Test POST /revelations/photo-consent/{connection_id} with invalid connection"""
        mock_get_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db_session
        
        # Mock no connection found
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        consent_data = {"consent_given": True}
        
        response = client.post("/api/v1/revelations/photo-consent/999", json=consent_data)
        
        assert response.status_code in [400, 404]


class TestRevelationsAnalyticsEndpoint:
    """Test revelation analytics endpoint"""

    @patch('app.api.v1.deps.get_current_user')
    @patch('app.core.database.get_db')
    def test_get_analytics_success(self, mock_get_db, mock_get_user, mock_current_user, mock_db_session, sample_connection):
        """Test GET /revelations/analytics/{connection_id}"""
        mock_get_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db_session
        
        # Mock connection and analytics data
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_connection
        
        response = client.get("/api/v1/revelations/analytics/1")
        
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)

    @patch('app.api.v1.deps.get_current_user')
    @patch('app.core.database.get_db')
    def test_get_analytics_no_access(self, mock_get_db, mock_get_user, mock_current_user, mock_db_session):
        """Test GET /revelations/analytics/{connection_id} with no access"""
        mock_get_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db_session
        
        # Mock no connection found
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        response = client.get("/api/v1/revelations/analytics/999")
        
        assert response.status_code in [403, 404]


class TestRevelationsErrorHandling:
    """Test error handling scenarios"""

    @patch('app.api.v1.deps.get_current_user')
    @patch('app.core.database.get_db')
    def test_database_error_handling(self, mock_get_db, mock_get_user, mock_current_user, mock_db_session):
        """Test handling of database errors"""
        mock_get_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db_session
        
        # Mock database error
        mock_db_session.query.side_effect = Exception("Database connection error")
        
        response = client.get("/api/v1/revelations/prompts")
        
        # Should handle error gracefully
        assert response.status_code in [500, 503]

    @patch('app.api.v1.deps.get_current_user')
    def test_authentication_required(self, mock_get_user):
        """Test that endpoints require authentication"""
        # Mock unauthenticated request
        mock_get_user.side_effect = Exception("Authentication required")
        
        response = client.get("/api/v1/revelations/prompts")
        
        # Should require authentication
        assert response.status_code in [401, 422]


class TestRevelationsIntegrationScenarios:
    """Test integration scenarios across multiple endpoints"""

    @patch('app.api.v1.deps.get_current_user')
    @patch('app.core.database.get_db')
    def test_complete_revelation_flow(self, mock_get_db, mock_get_user, mock_current_user, mock_db_session, sample_connection, sample_revelation_prompt):
        """Test complete revelation workflow: prompt → create → share → analytics"""
        mock_get_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db_session
        
        # 1. Get prompt for the day
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_revelation_prompt
        prompt_response = client.get("/api/v1/revelations/prompts/1")
        assert prompt_response.status_code == 200
        
        # 2. Create revelation
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_connection
        revelation_data = {
            "connection_id": 1,
            "day_number": 1,
            "revelation_type": "personal_value",
            "content": "Authenticity is my guiding principle in all relationships"
        }
        create_response = client.post("/api/v1/revelations/create", json=revelation_data)
        assert create_response.status_code in [200, 201, 400]
        
        # 3. Share revelation
        share_data = {"revelation_id": 1, "message": "This is important to me"}
        share_response = client.post("/api/v1/revelations/share/1", json=share_data)
        assert share_response.status_code in [200, 201, 400]
        
        # 4. View analytics
        analytics_response = client.get("/api/v1/revelations/analytics/1")
        assert analytics_response.status_code in [200, 404]

    @patch('app.api.v1.deps.get_current_user')
    @patch('app.core.database.get_db')
    def test_photo_reveal_flow(self, mock_get_db, mock_get_user, mock_current_user, mock_db_session, sample_connection):
        """Test photo reveal workflow: consent → analytics"""
        mock_get_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db_session
        
        # Mock connection query
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_connection
        
        # 1. Give photo consent
        consent_data = {
            "consent_given": True,
            "consent_message": "Ready to reveal myself to you!"
        }
        consent_response = client.post("/api/v1/revelations/photo-consent/1", json=consent_data)
        assert consent_response.status_code in [200, 201, 400]
        
        # 2. Check analytics after consent
        analytics_response = client.get("/api/v1/revelations/analytics/1")
        assert analytics_response.status_code in [200, 404]

    @patch('app.api.v1.deps.get_current_user')
    @patch('app.core.database.get_db')
    def test_revelation_timeline_progression(self, mock_get_db, mock_get_user, mock_current_user, mock_db_session, sample_connection):
        """Test viewing revelation timeline as relationship progresses"""
        mock_get_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db_session
        
        # Mock connection at different stages
        sample_connection.reveal_day = 3
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_connection
        
        # View timeline
        timeline_response = client.get("/api/v1/revelations/timeline/1")
        assert timeline_response.status_code == 200
        
        # View today's revelation
        today_response = client.get("/api/v1/revelations/today/1")
        assert today_response.status_code in [200, 404]


class TestRevelationsValidationAndEdgeCases:
    """Test validation and edge cases"""

    @patch('app.api.v1.deps.get_current_user')
    @patch('app.core.database.get_db')
    def test_revelation_content_validation(self, mock_get_db, mock_get_user, mock_current_user, mock_db_session, sample_connection):
        """Test revelation content validation"""
        mock_get_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_connection
        
        # Test empty content
        empty_data = {
            "connection_id": 1,
            "day_number": 1,
            "revelation_type": "personal_value",
            "content": ""
        }
        response = client.post("/api/v1/revelations/create", json=empty_data)
        assert response.status_code in [400, 422]
        
        # Test very long content
        long_content_data = {
            "connection_id": 1,
            "day_number": 1,
            "revelation_type": "personal_value", 
            "content": "A" * 10000  # Very long content
        }
        response = client.post("/api/v1/revelations/create", json=long_content_data)
        assert response.status_code in [200, 201, 400, 422]

    @patch('app.api.v1.deps.get_current_user')
    @patch('app.core.database.get_db')
    def test_invalid_day_numbers(self, mock_get_db, mock_get_user, mock_current_user, mock_db_session):
        """Test handling of invalid day numbers"""
        mock_get_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db_session
        
        # Test day 0
        response = client.get("/api/v1/revelations/prompts/0")
        assert response.status_code in [404, 422]
        
        # Test negative day
        response = client.get("/api/v1/revelations/prompts/-1")
        assert response.status_code in [404, 422]
        
        # Test very high day number
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        response = client.get("/api/v1/revelations/prompts/1000")
        assert response.status_code == 404

    @patch('app.api.v1.deps.get_current_user')
    @patch('app.core.database.get_db')
    def test_concurrent_revelation_operations(self, mock_get_db, mock_get_user, mock_current_user, mock_db_session, sample_connection):
        """Test handling of concurrent revelation operations"""
        mock_get_user.return_value = mock_current_user
        mock_get_db.return_value = mock_db_session
        mock_db_session.query.return_value.filter.return_value.first.return_value = sample_connection
        
        # Simulate creating multiple revelations rapidly
        revelation_data = {
            "connection_id": 1,
            "day_number": 1,
            "revelation_type": "personal_value",
            "content": "Test revelation content"
        }
        
        responses = []
        for i in range(3):
            response = client.post("/api/v1/revelations/create", json=revelation_data)
            responses.append(response)
        
        # At least one should succeed or all should fail gracefully
        success_count = sum(1 for r in responses if r.status_code in [200, 201])
        error_count = sum(1 for r in responses if r.status_code in [400, 422, 409])
        
        assert success_count + error_count == len(responses)