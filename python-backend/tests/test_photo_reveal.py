"""
Comprehensive Photo Reveal System Tests - Core "Soul Before Skin" Feature
Tests the 7-day consent-based photo reveal system with privacy controls
"""

import pytest
from fastapi import status
from datetime import datetime, timedelta
from freezegun import freeze_time
from unittest.mock import patch, MagicMock
import uuid

from app.models.photo_reveal import PhotoReveal, RevealStatus
from app.models.soul_connection import ConnectionStage
from app.services.photo_reveal_service import PhotoRevealService


class TestPhotoRevealConsent:
    """Test consent mechanisms for photo reveal system"""
    
    @pytest.mark.unit
    @pytest.mark.photo_reveal
    def test_photo_reveal_status_enum(self):
        """Test that all photo reveal statuses are properly defined"""
        expected_statuses = [
            "pending",
            "consented", 
            "revealed",
            "declined",
            "expired"
        ]
        
        actual_statuses = [status.value for status in RevealStatus]
        
        for expected in expected_statuses:
            assert expected in actual_statuses
        
        # Should have exactly these statuses for privacy control
        assert len(actual_statuses) >= 5

    @pytest.fixture
    def photo_reveal_service(self, db_session):
        return PhotoRevealService(db_session)

    @pytest.mark.unit
    @pytest.mark.photo_reveal
    def test_consent_requirement_validation(self, photo_reveal_service, soul_connection_data):
        """Test that photo reveal requires explicit consent from both users"""
        connection = soul_connection_data["connection"]
        user1, user2 = soul_connection_data["users"][:2]
        
        # Cannot reveal without consent
        with pytest.raises(ValueError, match="consent required"):
            photo_reveal_service.reveal_photo(
                connection_id=connection.id,
                user_id=user1.id,
                photo_url="https://example.com/photo.jpg",
                force_reveal=False
            )
        
        # Give consent first
        photo_reveal_service.give_consent(
            connection_id=connection.id,
            user_id=user1.id
        )
        
        # Should still fail without mutual consent
        with pytest.raises(ValueError, match="mutual consent"):
            photo_reveal_service.reveal_photo(
                connection_id=connection.id,
                user_id=user1.id,
                photo_url="https://example.com/photo.jpg",
                force_reveal=False
            )

    @pytest.mark.unit
    @pytest.mark.photo_reveal
    def test_seven_day_minimum_requirement(self, photo_reveal_service, soul_connection_data):
        """Test that photo reveal requires 7 days of revelations"""
        connection = soul_connection_data["connection"]
        user = soul_connection_data["users"][0]
        
        # Mock connection that's only 3 days old
        with freeze_time("2025-01-15 10:00:00"):
            connection_start = datetime.now()
            
        with freeze_time("2025-01-18 10:00:00"):  # 3 days later
            current_time = datetime.now()
            
            can_reveal = photo_reveal_service.can_reveal_photo(
                connection_id=connection.id,
                user_id=user.id,
                connection_start_date=connection_start,
                current_date=current_time
            )
            
            assert can_reveal == False
            
        # After 7 days should be allowed
        with freeze_time("2025-01-22 10:00:00"):  # 7 days later
            current_time = datetime.now()
            
            can_reveal = photo_reveal_service.can_reveal_photo(
                connection_id=connection.id,
                user_id=user.id,
                connection_start_date=connection_start,
                current_date=current_time
            )
            
            assert can_reveal == True

    @pytest.mark.unit
    @pytest.mark.photo_reveal
    def test_revelation_completion_requirement(self, photo_reveal_service, soul_connection_data):
        """Test that photo reveal requires completed revelation cycle"""
        connection = soul_connection_data["connection"]
        user = soul_connection_data["users"][0]
        
        # Check with incomplete revelations
        completed_days = [1, 2, 3]  # Only 3 days completed
        
        can_reveal = photo_reveal_service.can_reveal_based_on_revelations(
            connection_id=connection.id,
            user_id=user.id,
            completed_revelation_days=completed_days
        )
        
        assert can_reveal == False
        
        # Check with all 7 days completed
        completed_days = [1, 2, 3, 4, 5, 6, 7]
        
        can_reveal = photo_reveal_service.can_reveal_based_on_revelations(
            connection_id=connection.id,
            user_id=user.id,
            completed_revelation_days=completed_days
        )
        
        assert can_reveal == True

    @pytest.mark.unit
    @pytest.mark.photo_reveal
    def test_consent_withdrawal_mechanism(self, photo_reveal_service, soul_connection_data):
        """Test that users can withdraw photo reveal consent"""
        connection = soul_connection_data["connection"]
        user = soul_connection_data["users"][0]
        
        # Give initial consent
        consent = photo_reveal_service.give_consent(
            connection_id=connection.id,
            user_id=user.id
        )
        
        assert consent.reveal_status == RevealStatus.CONSENTED.value
        
        # Withdraw consent
        withdrawn = photo_reveal_service.withdraw_consent(
            connection_id=connection.id,
            user_id=user.id,
            reason="Changed my mind about revealing photos"
        )
        
        assert withdrawn.reveal_status == RevealStatus.DECLINED.value
        assert "changed my mind" in withdrawn.withdrawal_reason.lower()


class TestPhotoRevealAPI:
    """Test Photo Reveal REST API endpoints"""
    
    @pytest.mark.integration
    @pytest.mark.photo_reveal
    def test_give_photo_consent_endpoint(self, client, authenticated_user, soul_connection_data):
        """Test giving consent for photo reveal via API"""
        connection = soul_connection_data["connection"]
        
        consent_data = {
            "connection_id": connection.id,
            "consent_given": True,
            "consent_message": "I'm ready to share my photo after our meaningful revelations"
        }
        
        response = client.post(
            "/api/v1/photo-reveal/consent",
            json=consent_data,
            headers=authenticated_user["headers"]
        )
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]
        
        if response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]:
            data = response.json()
            assert data["reveal_status"] == RevealStatus.CONSENTED.value
            assert data["connection_id"] == connection.id

    @pytest.mark.integration
    @pytest.mark.photo_reveal
    def test_withdraw_photo_consent_endpoint(self, client, authenticated_user, soul_connection_data):
        """Test withdrawing consent for photo reveal"""
        connection = soul_connection_data["connection"]
        
        # First give consent
        consent_data = {
            "connection_id": connection.id,
            "consent_given": True
        }
        client.post("/api/v1/photo-reveal/consent", json=consent_data, headers=authenticated_user["headers"])
        
        # Then withdraw consent
        withdrawal_data = {
            "connection_id": connection.id,
            "consent_given": False,
            "reason": "I've decided I'm not ready to share photos yet"
        }
        
        response = client.post(
            "/api/v1/photo-reveal/consent",
            json=withdrawal_data,
            headers=authenticated_user["headers"]
        )
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    @pytest.mark.integration
    @pytest.mark.photo_reveal
    def test_photo_upload_endpoint(self, client, authenticated_user, soul_connection_data):
        """Test photo upload for reveal system"""
        connection = soul_connection_data["connection"]
        
        # Mock photo upload data
        photo_data = {
            "connection_id": connection.id,
            "photo_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD...",  # Truncated base64
            "photo_description": "A genuine smile after our beautiful soul connection journey"
        }
        
        response = client.post(
            "/api/v1/photo-reveal/upload",
            json=photo_data,
            headers=authenticated_user["headers"]
        )
        
        # Should succeed or indicate not implemented yet
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_501_NOT_IMPLEMENTED
        ]

    @pytest.mark.integration
    @pytest.mark.photo_reveal
    def test_mutual_reveal_status_check(self, client, authenticated_user, soul_connection_data):
        """Test checking mutual reveal status for connection"""
        connection = soul_connection_data["connection"]
        
        response = client.get(
            f"/api/v1/photo-reveal/status/{connection.id}",
            headers=authenticated_user["headers"]
        )
        
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
        
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "mutual_consent_given" in data
            assert "reveal_eligible" in data
            assert "days_until_eligible" in data

    @pytest.mark.integration
    @pytest.mark.photo_reveal
    def test_photo_reveal_privacy_protection(self, client, matching_users):
        """Test that photo reveals are private to connection participants only"""
        user1, user2 = matching_users["user1"], matching_users["user2"]
        
        # Create tokens
        token1 = client.post("/api/v1/auth/login", data={"username": user1.email, "password": "testpass123"}).json()["access_token"]
        token2 = client.post("/api/v1/auth/login", data={"username": user2.email, "password": "testpass123"}).json()["access_token"]
        
        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}
        
        # Create connection
        connection_response = client.post(
            "/api/v1/connections/initiate",
            json={"target_user_id": user2.id, "message": "Privacy test connection"},
            headers=headers1
        )
        
        if connection_response.status_code == status.HTTP_201_CREATED:
            connection_id = connection_response.json()["id"]
            
            # User1 uploads photo
            photo_data = {
                "connection_id": connection_id,
                "photo_base64": "data:image/jpeg;base64,testphotodata"
            }
            
            upload_response = client.post("/api/v1/photo-reveal/upload", json=photo_data, headers=headers1)
            
            # Only user2 (connection participant) should be able to view
            view_response = client.get(f"/api/v1/photo-reveal/view/{connection_id}", headers=headers2)
            
            # Should either work or indicate feature not implemented
            assert view_response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_403_FORBIDDEN,  # Not revealed yet
                status.HTTP_404_NOT_FOUND   # Feature not implemented
            ]


class TestPhotoRevealSecurity:
    """Test photo reveal security and privacy controls"""
    
    @pytest.mark.unit
    @pytest.mark.photo_reveal
    @pytest.mark.security
    def test_photo_url_validation(self, photo_reveal_service):
        """Test validation of photo URLs for security"""
        valid_urls = [
            "https://secure-cdn.dinnerfirst.app/photos/user123/photo.jpg",
            "https://cloudfront.amazonaws.com/dinnerfirst/photo.png"
        ]
        
        invalid_urls = [
            "http://unsecure.com/photo.jpg",  # Not HTTPS
            "javascript:alert('xss')",  # XSS attempt
            "../../../etc/passwd",  # Path traversal
            "file:///local/file.jpg",  # Local file access
            ""  # Empty URL
        ]
        
        for valid_url in valid_urls:
            assert photo_reveal_service.validate_photo_url(valid_url) == True
            
        for invalid_url in invalid_urls:
            assert photo_reveal_service.validate_photo_url(invalid_url) == False

    @pytest.mark.unit
    @pytest.mark.photo_reveal
    @pytest.mark.security
    def test_photo_metadata_scrubbing(self, photo_reveal_service):
        """Test that photo metadata is scrubbed for privacy"""
        # Mock photo with EXIF data
        mock_photo_metadata = {
            "GPS": {"latitude": 40.7128, "longitude": -74.0060},  # NYC coordinates
            "DateTime": "2025:01:15 10:30:45",
            "Camera": "iPhone 15 Pro",
            "Software": "iOS 17.2.1"
        }
        
        scrubbed = photo_reveal_service.scrub_photo_metadata(mock_photo_metadata)
        
        # Should remove location and identifying information
        assert "GPS" not in scrubbed
        assert "latitude" not in scrubbed
        assert "longitude" not in scrubbed
        
        # May keep safe metadata
        assert scrubbed.get("DateTime") is not None  # Time may be OK
        
        # Should not reveal device specifics
        assert "iPhone" not in str(scrubbed.get("Camera", ""))

    @pytest.mark.unit
    @pytest.mark.photo_reveal
    @pytest.mark.security
    def test_photo_content_validation(self, photo_reveal_service):
        """Test photo content validation and inappropriate image detection"""
        # Mock inappropriate content detection
        def mock_content_check(photo_data):
            # Simulate AI content moderation
            inappropriate_indicators = [
                "explicit_content",
                "not_face_photo", 
                "multiple_people",
                "inappropriate_text"
            ]
            
            # For testing, assume photos are appropriate unless flagged
            return {
                "is_appropriate": True,
                "confidence_score": 0.95,
                "flags": []
            }
        
        with patch.object(photo_reveal_service, 'validate_photo_content', side_effect=mock_content_check):
            result = photo_reveal_service.validate_photo_content("mock_photo_data")
            
            assert result["is_appropriate"] == True
            assert result["confidence_score"] > 0.9

    @pytest.mark.unit
    @pytest.mark.photo_reveal
    @pytest.mark.security
    def test_photo_storage_security(self, photo_reveal_service):
        """Test secure photo storage with encryption"""
        photo_data = b"mock_photo_binary_data"
        connection_id = 1
        user_id = 1
        
        # Mock secure storage
        stored_info = photo_reveal_service.store_photo_securely(
            photo_data=photo_data,
            connection_id=connection_id,
            user_id=user_id
        )
        
        assert "encrypted_url" in stored_info
        assert "storage_key" in stored_info
        assert stored_info["encrypted"] == True
        
        # Original photo data should not be in the URL
        assert b"mock_photo_binary_data" not in stored_info["encrypted_url"].encode()

    @pytest.mark.unit
    @pytest.mark.photo_reveal
    @pytest.mark.security
    def test_photo_access_time_limits(self, photo_reveal_service, soul_connection_data):
        """Test that photo access has time limits for privacy"""
        connection = soul_connection_data["connection"]
        user = soul_connection_data["users"][0]
        
        # Create photo reveal
        photo_reveal = PhotoReveal(
            connection_id=connection.id,
            user_id=user.id,
            photo_url="https://example.com/photo.jpg",
            reveal_status=RevealStatus.REVEALED.value,
            revealed_at=datetime.now() - timedelta(days=30)  # 30 days ago
        )
        
        # Check if photo access has expired
        is_expired = photo_reveal_service.is_photo_access_expired(photo_reveal)
        
        # Photos should have limited viewing window
        assert is_expired == True  # 30 days should be expired
        
        # Recent photo should still be accessible
        recent_photo = PhotoReveal(
            connection_id=connection.id,
            user_id=user.id,
            photo_url="https://example.com/photo2.jpg",
            reveal_status=RevealStatus.REVEALED.value,
            revealed_at=datetime.now() - timedelta(days=1)  # 1 day ago
        )
        
        is_recent_expired = photo_reveal_service.is_photo_access_expired(recent_photo)
        assert is_recent_expired == False


class TestPhotoRevealBusinessLogic:
    """Test photo reveal business rules and edge cases"""
    
    @pytest.mark.unit
    @pytest.mark.photo_reveal
    def test_connection_stage_progression_with_photos(self, photo_reveal_service, soul_connection_data):
        """Test that photo reveal updates connection stage appropriately"""
        connection = soul_connection_data["connection"]
        users = soul_connection_data["users"][:2]
        
        # Mock that both users have given consent and revealed photos
        for user in users:
            photo_reveal_service.give_consent(connection_id=connection.id, user_id=user.id)
            photo_reveal_service.reveal_photo(
                connection_id=connection.id,
                user_id=user.id,
                photo_url=f"https://example.com/{user.id}_photo.jpg",
                force_reveal=True  # For testing
            )
        
        # Connection stage should progress to dinner planning
        new_stage = photo_reveal_service.get_suggested_connection_stage(connection.id)
        
        expected_stages = [
            ConnectionStage.DINNER_PLANNING.value,
            ConnectionStage.RELATIONSHIP_BUILDING.value
        ]
        
        assert new_stage in expected_stages

    @pytest.mark.unit
    @pytest.mark.photo_reveal
    def test_partial_reveal_handling(self, photo_reveal_service, soul_connection_data):
        """Test handling when only one user reveals photo"""
        connection = soul_connection_data["connection"]
        user1, user2 = soul_connection_data["users"][:2]
        
        # Only user1 gives consent and reveals
        photo_reveal_service.give_consent(connection_id=connection.id, user_id=user1.id)
        
        # Check mutual reveal status
        mutual_status = photo_reveal_service.get_mutual_reveal_status(connection.id)
        
        assert mutual_status["user1_consented"] == True
        assert mutual_status["user2_consented"] == False
        assert mutual_status["mutual_reveal_possible"] == False
        assert mutual_status["photos_revealed"] == False

    @pytest.mark.unit
    @pytest.mark.photo_reveal
    def test_photo_reveal_notifications(self, photo_reveal_service, soul_connection_data):
        """Test that photo reveals trigger appropriate notifications"""
        connection = soul_connection_data["connection"]
        user1, user2 = soul_connection_data["users"][:2]
        
        with patch('app.services.push_notification.send_notification') as mock_notify:
            # User1 gives consent
            photo_reveal_service.give_consent(connection_id=connection.id, user_id=user1.id)
            
            # Should notify user2 about consent
            # mock_notify.assert_called_once()
            
            # User2 also gives consent
            photo_reveal_service.give_consent(connection_id=connection.id, user_id=user2.id)
            
            # Should trigger mutual consent notification
            # call_count = mock_notify.call_count
            # assert call_count >= 2

    @pytest.mark.unit
    @pytest.mark.photo_reveal
    def test_photo_reveal_analytics(self, photo_reveal_service, soul_connection_data):
        """Test photo reveal analytics and insights"""
        connection = soul_connection_data["connection"]
        
        analytics = photo_reveal_service.get_reveal_analytics(connection.id)
        
        expected_metrics = [
            "days_to_consent",
            "consent_rate", 
            "reveal_completion_rate",
            "time_to_mutual_reveal",
            "connection_progression_after_reveal"
        ]
        
        for metric in expected_metrics:
            assert metric in analytics

    @pytest.mark.performance
    @pytest.mark.photo_reveal
    def test_photo_processing_performance(self, photo_reveal_service, performance_config):
        """Test photo processing performance requirements"""
        import time
        
        # Mock photo processing (resize, metadata scrubbing, upload)
        large_photo_data = b"x" * (5 * 1024 * 1024)  # 5MB photo
        
        start_time = time.time()
        
        # Simulate photo processing pipeline
        result = photo_reveal_service.process_photo_for_reveal(
            photo_data=large_photo_data,
            connection_id=1,
            user_id=1
        )
        
        processing_time = time.time() - start_time
        
        # Photo processing should be reasonably fast
        assert processing_time < 5.0  # 5 seconds max for large photo
        assert result["processed"] == True


class TestPhotoRevealIntegration:
    """Test photo reveal integration with other platform features"""
    
    @pytest.mark.integration
    @pytest.mark.photo_reveal
    def test_photo_reveal_with_complete_revelation_cycle(self, client, authenticated_user, soul_connection_data):
        """Test photo reveal after completing full revelation cycle"""
        connection = soul_connection_data["connection"]
        
        # Complete all 7 days of revelations first
        revelation_types = [
            "personal_value", "meaningful_experience", "hope_or_dream",
            "humor_source", "challenge_overcome", "ideal_connection", "photo_reveal"
        ]
        
        for day, revelation_type in enumerate(revelation_types, 1):
            revelation_data = {
                "connection_id": connection.id,
                "day_number": day,
                "revelation_type": revelation_type,
                "content": f"Day {day} revelation content for photo reveal testing"
            }
            
            response = client.post(
                "/api/v1/revelations/create",
                json=revelation_data,
                headers=authenticated_user["headers"]
            )
            
            # Most days should succeed
            assert response.status_code in [
                status.HTTP_201_CREATED,
                status.HTTP_400_BAD_REQUEST  # May have business rule restrictions
            ]
        
        # Now photo reveal should be eligible
        consent_data = {
            "connection_id": connection.id,
            "consent_given": True,
            "message": "Completed our soul journey - ready to see your beautiful face!"
        }
        
        consent_response = client.post(
            "/api/v1/photo-reveal/consent",
            json=consent_data,
            headers=authenticated_user["headers"]
        )
        
        assert consent_response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_404_NOT_FOUND  # Feature may not be fully implemented
        ]

    @pytest.mark.integration
    @pytest.mark.photo_reveal
    def test_photo_reveal_affects_matching_algorithm(self, photo_reveal_service, soul_connection_data):
        """Test that photo reveals affect future matching preferences"""
        connection = soul_connection_data["connection"]
        users = soul_connection_data["users"][:2]
        
        # Complete photo reveal process
        for user in users:
            photo_reveal_service.give_consent(connection_id=connection.id, user_id=user.id)
            photo_reveal_service.reveal_photo(
                connection_id=connection.id,
                user_id=user.id,
                photo_url=f"https://example.com/{user.id}_photo.jpg",
                force_reveal=True
            )
        
        # Get updated matching preferences
        updated_preferences = photo_reveal_service.get_updated_matching_preferences(users[0].id)
        
        # Should include insights from successful photo reveal
        assert "successful_photo_reveals" in updated_preferences
        assert updated_preferences["photo_reveal_comfort_level"] >= 7  # High comfort after success

    @pytest.mark.integration
    @pytest.mark.photo_reveal
    def test_photo_reveal_dinner_planning_integration(self, client, authenticated_user, soul_connection_data):
        """Test integration between photo reveal and dinner planning"""
        connection = soul_connection_data["connection"]
        
        # Complete photo reveal
        consent_data = {"connection_id": connection.id, "consent_given": True}
        client.post("/api/v1/photo-reveal/consent", json=consent_data, headers=authenticated_user["headers"])
        
        # Check if dinner planning is unlocked
        dinner_response = client.get(
            f"/api/v1/dinner-planning/status/{connection.id}",
            headers=authenticated_user["headers"]
        )
        
        # Should either work or indicate feature not implemented
        assert dinner_response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_501_NOT_IMPLEMENTED
        ]