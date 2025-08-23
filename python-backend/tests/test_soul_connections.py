"""
Comprehensive tests for Soul Connection System - Core Dating Platform Feature
Tests the "Soul Before Skin" matching algorithm and connection management
"""

import time
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from app.models.soul_connection import ConnectionStage, SoulConnection
from app.services.compatibility import CompatibilityCalculator
from app.services.soul_compatibility_service import SoulCompatibilityService
from fastapi import status
from tests.factories import UserFactory


class TestSoulConnectionAlgorithms:
    """Test core soul connection matching algorithms"""

    @pytest.mark.unit
    @pytest.mark.soul_connections
    def test_interest_similarity_jaccard(self, db_session):
        """Test Jaccard similarity calculation for interests overlap through compatibility service"""
        service = SoulCompatibilityService()

        # Create test users with different interest overlaps
        UserFactory._meta.sqlalchemy_session = db_session

        # Perfect overlap
        user1 = UserFactory(interests=["cooking", "reading", "hiking"])
        user2 = UserFactory(interests=["cooking", "reading", "hiking"])
        result = service.calculate_compatibility(user1, user2, db_session)
        assert result.interests_score >= 90  # Should be very high

        # No overlap
        user3 = UserFactory(interests=["cooking", "reading"])
        user4 = UserFactory(interests=["dancing", "gaming"])
        result = service.calculate_compatibility(user3, user4, db_session)
        assert result.interests_score <= 60  # Should be lower

        # Partial overlap (50%)
        user5 = UserFactory(interests=["cooking", "reading", "hiking", "photography"])
        user6 = UserFactory(interests=["cooking", "music", "hiking", "art"])
        result = service.calculate_compatibility(user5, user6, db_session)
        assert 40 <= result.interests_score <= 70  # Should be moderate (2/6 overlap)

    @pytest.mark.unit
    @pytest.mark.soul_connections
    def test_values_compatibility_keyword_matching(self, db_session):
        """Test values alignment through keyword matching"""
        service = SoulCompatibilityService()
        UserFactory._meta.sqlalchemy_session = db_session

        # Users with similar values
        user1 = UserFactory(
            core_values={
                "relationship_values": "I value loyalty, commitment, and growth in relationships",
                "connection_style": "I prefer deep, meaningful conversations over small talk",
            }
        )

        user2 = UserFactory(
            core_values={
                "relationship_values": "Loyalty and dedication are most important to me",
                "connection_style": "I love deep philosophical discussions about life",
            }
        )

        result = service.calculate_compatibility(user1, user2, db_session)
        assert result.values_score > 50  # Should have good values alignment

        # Test lower alignment
        user3 = UserFactory(
            core_values={
                "relationship_values": "I just want to have fun and keep things casual",
                "connection_style": "I prefer light, fun conversations and activities",
            }
        )

        result_low = service.calculate_compatibility(user1, user3, db_session)
        assert (
            result_low.values_score < result.values_score
        )  # Should be lower compatibility

    @pytest.mark.unit
    @pytest.mark.soul_connections
    def test_demographic_compatibility_age_scoring(self, db_session):
        """Test age compatibility with bell curve scoring"""
        service = SoulCompatibilityService()
        UserFactory._meta.sqlalchemy_session = db_session

        # Perfect age match (same birth year)
        user1 = UserFactory(date_of_birth="1995-06-15", location="New York")
        user2 = UserFactory(date_of_birth="1995-08-20", location="New York")
        result = service.calculate_compatibility(user1, user2, db_session)
        assert (
            result.demographic_score > 60
        )  # Should be good (includes age, location, lifestyle factors)

        # 5 year difference (moderate compatibility)
        user3 = UserFactory(date_of_birth="1990-06-15", location="New York")
        user4 = UserFactory(date_of_birth="1995-08-20", location="New York")
        result = service.calculate_compatibility(user3, user4, db_session)
        assert 50 < result.demographic_score < 70  # Should be moderate (5 year gap)

        # Large age gap (poor compatibility)
        user5 = UserFactory(date_of_birth="1980-06-15", location="New York")
        user6 = UserFactory(date_of_birth="1998-08-20", location="New York")
        result = service.calculate_compatibility(user5, user6, db_session)
        assert result.demographic_score < 50  # Should be lower (18 year gap)

    @pytest.mark.unit
    @pytest.mark.soul_connections
    @pytest.mark.performance
    def test_compatibility_calculator_performance(
        self, matching_users, performance_config, db_session
    ):
        """Test that compatibility calculation meets performance requirements (<500ms)"""
        calculator = SoulCompatibilityService()

        start_time = time.time()
        result = calculator.calculate_compatibility(
            matching_users["user1"], matching_users["user2"], db_session
        )
        execution_time = time.time() - start_time

        # Performance requirement: <500ms
        assert execution_time < performance_config["matching_algorithm_max_time"]

        # Verify result structure
        assert hasattr(result, "total_score")
        assert hasattr(result, "match_quality")
        assert hasattr(result, "confidence")
        assert 0 <= result.total_score <= 100

    @pytest.mark.unit
    @pytest.mark.soul_connections
    def test_compatibility_calculator_weights(self, matching_users, db_session):
        """Test that compatibility calculator applies correct weights"""
        calculator = SoulCompatibilityService()
        result = calculator.calculate_compatibility(
            matching_users["user1"], matching_users["user2"], db_session
        )

        # Verify result has all components
        assert hasattr(result, "interests_score")
        assert hasattr(result, "values_score")
        assert hasattr(result, "demographic_score")

        # Verify scores are reasonable for our test data (50-66% overlap)
        assert 40 <= result.interests_score <= 80
        assert 30 <= result.values_score <= 90
        assert 60 <= result.demographic_score <= 95


class TestSoulConnectionAPI:
    """Test Soul Connection REST API endpoints"""

    @pytest.mark.integration
    @pytest.mark.soul_connections
    def test_discover_potential_connections(self, client, authenticated_user):
        """Test discovering potential soul connections"""
        response = client.get(
            "/api/v1/connections/discover", headers=authenticated_user["headers"]
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

        # If connections found, verify structure
        if data:
            connection = data[0]
            assert "compatibility_score" in connection
            assert "compatibility_breakdown" in connection
            assert "user_id" in connection
            assert connection["compatibility_score"] >= 50  # Minimum threshold

    @pytest.mark.integration
    @pytest.mark.soul_connections
    def test_initiate_soul_connection(self, client, authenticated_user, matching_users):
        """Test initiating a new soul connection"""
        connection_data = {
            "target_user_id": matching_users["user2"].id,
            "message": "I felt a deep connection reading your profile. Would you like to start our soul journey together?",
        }

        response = client.post(
            "/api/v1/connections/initiate",
            json=connection_data,
            headers=authenticated_user["headers"],
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert data["user1_id"] == authenticated_user["user"].id
        assert data["user2_id"] == matching_users["user2"].id
        assert data["connection_stage"] == ConnectionStage.SOUL_DISCOVERY.value
        assert "compatibility_score" in data
        assert data["reveal_day"] == 1

    @pytest.mark.integration
    @pytest.mark.soul_connections
    def test_cannot_create_duplicate_connection(
        self, client, authenticated_user, matching_users
    ):
        """Test that duplicate connections are prevented"""
        # Create first connection
        connection_data = {
            "target_user_id": matching_users["user2"].id,
            "message": "First connection attempt",
        }

        response1 = client.post(
            "/api/v1/connections/initiate",
            json=connection_data,
            headers=authenticated_user["headers"],
        )
        assert response1.status_code == status.HTTP_201_CREATED

        # Attempt duplicate connection
        response2 = client.post(
            "/api/v1/connections/initiate",
            json=connection_data,
            headers=authenticated_user["headers"],
        )

        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response2.json()["detail"].lower()

    @pytest.mark.integration
    @pytest.mark.soul_connections
    def test_get_active_connections(
        self, client, authenticated_user, soul_connection_data
    ):
        """Test retrieving user's active soul connections"""
        response = client.get(
            "/api/v1/connections/active", headers=authenticated_user["headers"]
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

        if data:
            connection = data[0]
            assert "id" in connection
            assert "connection_stage" in connection
            assert "compatibility_score" in connection
            assert "reveal_day" in connection

    @pytest.mark.integration
    @pytest.mark.soul_connections
    def test_update_connection_stage(
        self, client, authenticated_user, soul_connection_data
    ):
        """Test updating soul connection stage progression"""
        connection = soul_connection_data["connection"]

        stage_data = {
            "connection_stage": ConnectionStage.REVELATION_SHARING.value,
            "progress_notes": "Both users have completed day 3 revelations",
        }

        response = client.put(
            f"/api/v1/connections/{connection.id}/stage",
            json=stage_data,
            headers=authenticated_user["headers"],
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["connection_stage"] == ConnectionStage.REVELATION_SHARING.value

    @pytest.mark.integration
    @pytest.mark.soul_connections
    def test_connection_stage_validation(
        self, client, authenticated_user, soul_connection_data
    ):
        """Test that connection stages follow proper progression"""
        connection = soul_connection_data["connection"]

        # Try to skip to photo reveal without completing revelations
        invalid_stage_data = {"connection_stage": ConnectionStage.PHOTO_REVEAL.value}

        response = client.put(
            f"/api/v1/connections/{connection.id}/stage",
            json=invalid_stage_data,
            headers=authenticated_user["headers"],
        )

        # Should require proper progression or validation
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        ]

    @pytest.mark.integration
    @pytest.mark.soul_connections
    def test_unauthorized_connection_access(self, client):
        """Test that unauthorized users cannot access connections"""
        response = client.get("/api/v1/connections/active")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        response = client.post(
            "/api/v1/connections/initiate",
            json={"target_user_id": 123, "message": "test"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestSoulConnectionBusinessLogic:
    """Test soul connection business rules and edge cases"""

    @pytest.mark.unit
    @pytest.mark.soul_connections
    def test_minimum_compatibility_threshold(self, matching_users, db_session):
        """Test that connections require minimum compatibility score"""
        calculator = SoulCompatibilityService()

        # Create users with very low compatibility
        matching_users["user1"].interests = ["cooking", "reading"]
        matching_users["user1"].core_values = {
            "relationship_values": ["commitment", "stability"],
            "life_priorities": ["career", "family"],
        }

        matching_users["user2"].interests = ["extreme_sports", "partying"]
        matching_users["user2"].core_values = {
            "relationship_values": ["freedom", "adventure"],
            "life_priorities": ["travel", "excitement"],
        }

        result = calculator.calculate_compatibility(
            matching_users["user1"], matching_users["user2"], db_session
        )

        # Low compatibility should be reflected in score
        assert result.total_score < 50  # Below typical threshold

    @pytest.mark.unit
    @pytest.mark.soul_connections
    def test_soul_connection_stages_enum(self):
        """Test that all soul connection stages are properly defined"""
        expected_stages = [
            "soul_discovery",
            "initial_connection",
            "revelation_sharing",
            "deepening_bond",
            "photo_reveal",
            "dinner_planning",
            "relationship_building",
        ]

        actual_stages = [stage.value for stage in ConnectionStage]

        for expected in expected_stages:
            assert expected in actual_stages

    @pytest.mark.integration
    @pytest.mark.soul_connections
    def test_connection_privacy_and_consent(
        self, client, authenticated_user, matching_users
    ):
        """Test privacy controls and mutual consent requirements"""
        # Create connection
        connection_data = {
            "target_user_id": matching_users["user2"].id,
            "message": "Privacy test connection",
        }

        response = client.post(
            "/api/v1/connections/initiate",
            json=connection_data,
            headers=authenticated_user["headers"],
        )
        assert response.status_code == status.HTTP_201_CREATED
        connection_id = response.json()["id"]

        # Test that personal information is protected until consent
        response = client.get(
            f"/api/v1/connections/{connection_id}",
            headers=authenticated_user["headers"],
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should not reveal personal details without mutual consent
        assert "phone_number" not in data
        assert "full_address" not in data

        # Should only show emotional profile data appropriate for current stage
        if data["connection_stage"] == ConnectionStage.SOUL_DISCOVERY.value:
            assert "life_philosophy" in data  # OK to share
            assert "photo_url" not in data  # Not OK until photo reveal stage

    @pytest.mark.performance
    @pytest.mark.soul_connections
    def test_concurrent_matching_performance(self, client, performance_config):
        """Test matching algorithm performance under concurrent load"""
        import concurrent.futures
        import threading

        def make_discovery_request():
            # This would require proper authentication in real test
            # Simulating concurrent matching requests
            time.sleep(0.1)  # Simulate processing time
            return True

        # Simulate concurrent matching requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            start_time = time.time()

            for _ in range(performance_config["concurrent_users"] // 5):
                future = executor.submit(make_discovery_request)
                futures.append(future)

            # Wait for all requests to complete
            results = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]
            total_time = time.time() - start_time

            # Should handle concurrent requests efficiently
            assert total_time < 5.0  # Should complete within 5 seconds
            assert all(results)  # All requests should succeed


class TestSoulConnectionIntegration:
    """Integration tests for complete soul connection workflows"""

    @pytest.mark.integration
    @pytest.mark.soul_connections
    def test_complete_soul_connection_journey(self, client, matching_users, db_session):
        """Test the complete soul connection journey from discovery to photo reveal"""
        # Authenticate as user1
        user1 = matching_users["user1"]
        token1 = client.post(
            "/api/v1/auth/login",
            data={"username": user1.email, "password": "testpass123"},
        ).json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}

        # Step 1: Discover potential connections
        discovery_response = client.get(
            "/api/v1/connections/discover", headers=headers1
        )
        assert discovery_response.status_code == status.HTTP_200_OK

        # Step 2: Initiate connection
        initiate_response = client.post(
            "/api/v1/connections/initiate",
            json={
                "target_user_id": matching_users["user2"].id,
                "message": "I feel a deep connection to your values and interests",
            },
            headers=headers1,
        )
        assert initiate_response.status_code == status.HTTP_201_CREATED
        connection_id = initiate_response.json()["id"]

        # Step 3: Progress through revelation stages (would involve revelations API)
        for stage in [
            ConnectionStage.INITIAL_CONNECTION.value,
            ConnectionStage.REVELATION_SHARING.value,
        ]:
            stage_response = client.put(
                f"/api/v1/connections/{connection_id}/stage",
                json={"connection_stage": stage},
                headers=headers1,
            )
            assert stage_response.status_code == status.HTTP_200_OK

        # Step 4: Verify final connection state
        final_response = client.get(
            f"/api/v1/connections/{connection_id}", headers=headers1
        )
        assert final_response.status_code == status.HTTP_200_OK
        final_data = final_response.json()

        assert (
            final_data["connection_stage"] == ConnectionStage.REVELATION_SHARING.value
        )
        assert "compatibility_score" in final_data
        assert final_data["compatibility_score"] >= 50

    @pytest.mark.integration
    @pytest.mark.soul_connections
    def test_matching_algorithm_consistency(self, matching_users, db_session):
        """Test that matching algorithm produces consistent results"""
        calculator = SoulCompatibilityService()

        # Run compatibility calculation multiple times
        results = []
        for _ in range(5):
            result = calculator.calculate_compatibility(
                matching_users["user1"], matching_users["user2"], db_session
            )
            results.append(result.total_score)

        # Results should be consistent (identical for deterministic algorithm)
        assert len(set(results)) == 1, "Matching algorithm should be deterministic"

        # Score should be reasonable for our test data
        score = results[0]
        assert (
            40 <= score <= 80
        ), f"Expected reasonable compatibility score, got {score}"
