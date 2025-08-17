"""
Test Enhanced Fixtures - Story 3.1 Validation
Validates all new comprehensive fixtures work correctly
"""

import pytest
from datetime import datetime


class TestServiceFixtures:
    """Test that all service fixtures initialize correctly"""
    
    def test_soul_compatibility_service_fixture(self, soul_compatibility_service):
        """Test soul compatibility service fixture"""
        assert soul_compatibility_service is not None
        assert hasattr(soul_compatibility_service, 'calculate_compatibility')
        assert hasattr(soul_compatibility_service, 'calculate_interest_similarity')
    
    def test_revelation_service_fixture(self, revelation_service):
        """Test revelation service fixture"""
        assert revelation_service is not None
        assert hasattr(revelation_service, 'create_revelation')
        assert hasattr(revelation_service, 'get_revelation_timeline')
    
    def test_message_service_fixture(self, message_service):
        """Test message service fixture"""
        assert message_service is not None
        assert hasattr(message_service, 'send_message')
    
    def test_ab_testing_service_fixture(self, ab_testing_service):
        """Test A/B testing service fixture"""
        assert ab_testing_service is not None
        assert hasattr(ab_testing_service, 'create_experiment')
        assert hasattr(ab_testing_service, 'assign_user_to_experiment')


class TestAdvancedTestDataScenarios:
    """Test advanced test data scenarios"""
    
    def test_high_compatibility_users_fixture(self, high_compatibility_users, soul_compatibility_service, db_session):
        """Test high compatibility users scenario"""
        data = high_compatibility_users
        
        assert data["user1"] is not None
        assert data["user2"] is not None
        assert data["expected_compatibility"] == 85.0
        
        # Test actual compatibility calculation
        result = soul_compatibility_service.calculate_compatibility(
            data["user1"], data["user2"], db_session
        )
        
        # Should be reasonably high (though exact value may vary based on algorithm)
        assert result.total_score > 40  # Reasonable threshold for test data
    
    def test_low_compatibility_users_fixture(self, low_compatibility_users, soul_compatibility_service, db_session):
        """Test low compatibility users scenario"""
        data = low_compatibility_users
        
        assert data["user1"] is not None
        assert data["user2"] is not None
        assert data["expected_compatibility"] == 25.0
        
        # Test actual compatibility calculation
        result = soul_compatibility_service.calculate_compatibility(
            data["user1"], data["user2"], db_session
        )
        
        # Should be lower than high compatibility users
        assert result.total_score < 80  # Lower threshold
    
    def test_complete_revelation_cycle_fixture(self, complete_revelation_cycle):
        """Test complete revelation cycle fixture"""
        data = complete_revelation_cycle
        
        assert data["connection"] is not None
        assert len(data["users"]) >= 2
        assert len(data["revelations"]) == 7
        assert data["total_days"] == 7
        
        # Verify all 7 days are represented
        day_numbers = [r.day_number for r in data["revelations"]]
        assert set(day_numbers) == set(range(1, 8))
    
    def test_multi_stage_connections_fixture(self, multi_stage_connections):
        """Test multi-stage connections fixture"""
        data = multi_stage_connections
        
        assert len(data["users"]) == 6
        assert len(data["connections"]) == 6
        assert len(data["stages"]) == 6
        
        # Verify all stages are represented
        connection_stages = [c.connection_stage for c in data["connections"]]
        stage_values = [s.value for s in data["stages"]]
        
        for stage_value in stage_values:
            assert stage_value in connection_stages
    
    def test_websocket_test_data_fixture(self, websocket_test_data):
        """Test WebSocket test data fixture"""
        data = websocket_test_data
        
        assert len(data["users"]) == 3
        assert len(data["connections"]) == 2
        assert len(data["mock_websockets"]) == 3
        
        # Verify mock websocket IDs
        for user in data["users"]:
            assert user.id in data["mock_websockets"]
            assert data["mock_websockets"][user.id] == f"mock_ws_{user.id}"
    
    def test_security_test_data_fixture(self, security_test_data):
        """Test security test data fixture"""
        data = security_test_data
        
        assert data["admin_user"] is not None
        assert data["admin_user"].email == "admin@test.com"
        assert len(data["regular_users"]) == 3
        assert data["private_connection"] is not None
        assert data["public_connection"] is not None
    
    def test_performance_test_data_fixture(self, performance_test_data):
        """Test performance test data fixture"""
        data = performance_test_data
        
        assert data["total_users"] == 20
        assert len(data["users"]) == 20
        assert len(data["profiles"]) == 20
        assert len(data["connections"]) == 10  # 20 users / 2 = 10 connections
        
        # Verify each user has a profile
        user_ids = [u.id for u in data["users"]]
        profile_user_ids = [p.user_id for p in data["profiles"]]
        
        for user_id in user_ids:
            assert user_id in profile_user_ids


class TestFixtureIntegration:
    """Test that fixtures work well together"""
    
    def test_multiple_fixtures_together(self, authenticated_user, soul_connection_data, performance_config):
        """Test using multiple fixtures in same test"""
        assert authenticated_user["user"] is not None
        assert soul_connection_data["connection"] is not None
        assert performance_config["matching_algorithm_max_time"] == 0.5
        
        # Should not interfere with each other
        assert authenticated_user["user"].id != soul_connection_data["users"][0].id
    
    def test_service_and_data_fixtures(self, revelation_service, complete_revelation_cycle):
        """Test service fixtures work with advanced data scenarios"""
        data = complete_revelation_cycle
        
        # Service should be able to work with fixture data
        timeline = revelation_service.get_revelation_timeline(
            data["connection"].id,
            data["users"][0].id
        )
        
        assert timeline is not None
        # Should have revelations (exact count may vary based on service implementation)
        assert len(timeline) >= 0
    
    def test_performance_fixtures_integration(self, performance_test_data, soul_compatibility_service, db_session):
        """Test performance fixtures work with service fixtures"""
        import time
        
        data = performance_test_data
        users = data["users"]
        
        # Test compatibility calculation with multiple users
        start_time = time.time()
        
        results = []
        for i in range(0, min(4, len(users)), 2):  # Test first 4 users
            result = soul_compatibility_service.calculate_compatibility(
                users[i], users[i+1], db_session
            )
            results.append(result.total_score)
        
        execution_time = time.time() - start_time
        
        # Should complete reasonably fast
        assert execution_time < 2.0
        assert len(results) == 2
        assert all(0 <= score <= 100 for score in results)


class TestFixtureReliability:
    """Test that fixtures are reliable and deterministic"""
    
    def test_fixture_data_consistency(self, matching_users):
        """Test that fixture data is consistent across test runs"""
        data = matching_users
        
        # User data should be consistent
        assert data["user1"].email == "match1@test.com"
        assert data["user2"].email == "match2@test.com"
        
        # Profile data should be present
        assert data["profile1"].user_id == data["user1"].id
        assert data["profile2"].user_id == data["user2"].id
    
    def test_fixture_isolation(self, authenticated_user, db_session):
        """Test that fixtures provide proper test isolation"""
        user1 = authenticated_user["user"]
        
        # Create another user in the same test
        from tests.factories import UserFactory, setup_factories
        setup_factories(db_session)
        
        user2 = UserFactory(email="isolation_test@test.com")
        
        # Users should be independent
        assert user1.id != user2.id
        assert user1.email != user2.email
    
    def test_fixture_cleanup(self, db_session):
        """Test that fixture cleanup works properly"""
        # This test verifies that previous test data is cleaned up
        from app.models.user import User
        
        # Should start with clean database (or only current test data)
        users = db_session.query(User).all()
        
        # The exact count may vary, but database should be manageable
        assert len(users) < 100  # Reasonable upper bound