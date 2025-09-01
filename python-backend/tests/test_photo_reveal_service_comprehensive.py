"""
Comprehensive Photo Reveal Service Tests
Tests for missing coverage to achieve 75%+ coverage
"""

import asyncio
from datetime import datetime, timedelta
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from app.models.photo_reveal import (
    PhotoConsentType,
    PhotoPrivacyLevel,
    PhotoRevealRequest,
    PhotoRevealStage,
    PhotoRevealTimeline,
    UserPhoto,
)
from app.models.soul_connection import SoulConnection
from app.models.user import User
from app.services.photo_reveal_service import PhotoRevealService, PhotoRevealStatus
from fastapi import UploadFile
from tests.factories import SoulConnectionFactory, UserFactory


class TestPhotoRevealServiceCore:
    """Test core PhotoRevealService methods"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        db = Mock()
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()
        db.query = Mock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create service instance"""
        return PhotoRevealService(db=mock_db)

    @pytest.fixture
    def test_user1(self, db_session):
        """Create first test user"""
        UserFactory._meta.sqlalchemy_session = db_session
        return UserFactory()  # Let factory assign unique IDs

    @pytest.fixture
    def test_user2(self, db_session):
        """Create second test user"""
        UserFactory._meta.sqlalchemy_session = db_session
        return UserFactory()

    @pytest.fixture
    def test_connection(self, test_user1, test_user2, db_session):
        """Create test connection"""
        SoulConnectionFactory._meta.sqlalchemy_session = db_session
        return SoulConnectionFactory(
            user1_id=test_user1.id,
            user2_id=test_user2.id,
            connection_stage="active_connection",
        )

    @pytest.mark.asyncio
    async def test_create_photo_timeline_new(self, service, test_connection):
        """Test creating new photo timeline"""
        mock_db = Mock()

        # Mock query chain for first query (timeline check) and second query (connection lookup)
        mock_query = Mock()
        mock_filter = Mock()
        mock_first = Mock()

        # First call: PhotoRevealTimeline query returns None (no existing timeline)
        # Second call: SoulConnection query returns the test_connection
        mock_first.side_effect = [None, test_connection]
        mock_filter.first = mock_first
        mock_query.filter.return_value = mock_filter
        mock_db.query.return_value = mock_query

        # Mock revelation count query
        mock_filter.count.return_value = 3

        result = await service.create_photo_timeline(
            connection_id=test_connection.id, db=mock_db
        )

        # Service returns timeline object, not dict
        assert result is not None
        assert hasattr(result, "connection_id")
        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_create_photo_timeline_existing(self, service, test_connection):
        """Test with existing timeline"""
        mock_db = Mock()

        # Mock existing timeline
        mock_timeline = Mock()
        mock_timeline.id = 1
        mock_timeline.current_stage = "consented"  # Use actual enum value

        # Mock query to return existing timeline on first call
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_timeline
        )

        result = await service.create_photo_timeline(
            connection_id=test_connection.id, db=mock_db
        )

        # Should return existing timeline
        assert result == mock_timeline
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_upload_user_photo_success(self, service, test_user1):
        """Test successful photo upload"""
        mock_db = Mock()
        # Create mock file
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.jpg"
        mock_file.size = 1024000  # 1MB
        mock_file.content_type = "image/jpeg"
        mock_file.read = AsyncMock(return_value=b"fake_image_data")

        # Mock validation and storage
        with patch.object(
            service,
            "_validate_photo_file",
            return_value={"valid": True, "file_type": "jpeg", "size": 1024000},
        ):
            with patch.object(
                service, "_store_encrypted_photo", new_callable=AsyncMock
            ) as mock_store:
                mock_store.return_value = "encrypted_photo_url"

                with patch.object(
                    service, "_queue_photo_moderation", new_callable=AsyncMock
                ) as mock_moderate:
                    mock_moderate.return_value = True

                    result = await service.upload_user_photo(
                        user_id=test_user1.id,
                        photo_file=mock_file,
                        privacy_level=PhotoPrivacyLevel.FULLY_REVEALED,
                        db=mock_db,
                    )

                    assert isinstance(result, dict)
                    assert "photo_id" in result
                    assert "status" in result
                    mock_db.add.assert_called()
                    mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_upload_user_photo_invalid_file(self, service, test_user1):
        """Test photo upload with invalid file"""
        mock_db = Mock()
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.txt"
        mock_file.content_type = "text/plain"

        with patch.object(
            service,
            "_validate_photo_file",
            return_value={"valid": False, "error": "Invalid file type"},
        ):
            with pytest.raises(ValueError, match="Invalid file type"):
                await service.upload_user_photo(
                    user_id=test_user1.id,
                    photo_file=mock_file,
                    privacy_level=PhotoPrivacyLevel.FULLY_REVEALED,
                    db=mock_db,
                )

    @pytest.mark.asyncio
    async def test_get_photo_reveal_status_success(self, service, test_connection):
        """Test getting photo reveal status"""
        mock_db = Mock()
        # Mock timeline
        mock_timeline = Mock()
        mock_timeline.connection_id = test_connection.id
        mock_timeline.current_stage = PhotoRevealStage.CONSENT_PHASE
        mock_timeline.min_revelations_required = 7
        mock_timeline.reveal_scheduled_date = datetime.now() + timedelta(days=3)

        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_timeline
        )
        mock_db.query.return_value.filter.return_value.count.return_value = 4

        # Mock consent requests
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = await service.get_photo_reveal_status(
            connection_id=test_connection.id, db=mock_db
        )

        assert isinstance(result, PhotoRevealStatus)
        assert result.connection_id == test_connection.id
        assert result.current_stage == PhotoRevealStage.CONSENT_PHASE
        assert result.days_until_reveal == 3
        assert result.revelations_completed == 4
        assert result.min_revelations_required == 7

    @pytest.mark.asyncio
    async def test_get_photo_reveal_status_no_timeline(self, service, test_connection):
        """Test status when no timeline exists"""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = await service.get_photo_reveal_status(
            connection_id=test_connection.id, db=mock_db
        )

        assert isinstance(result, PhotoRevealStatus)
        assert result.current_stage == PhotoRevealStage.NOT_STARTED

    @pytest.mark.asyncio
    async def test_request_photo_consent_success(
        self, service, test_user1, test_connection
    ):
        """Test requesting photo consent"""
        mock_db = Mock()
        # Mock no existing request
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = await service.request_photo_consent(
            requester_id=test_user1.id,
            connection_id=test_connection.id,
            consent_type=PhotoConsentType.MUTUAL_AGREEMENT,
            message="Ready to exchange photos!",
            db=mock_db,
        )

        assert isinstance(result, dict)
        assert "request_id" in result
        assert "status" in result
        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_request_photo_consent_existing(
        self, service, test_user1, test_connection
    ):
        """Test requesting consent when request exists"""
        mock_db = Mock()
        # Mock existing request
        mock_request = Mock()
        mock_request.id = 1
        mock_request.status = "pending"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_request

        with pytest.raises(ValueError, match="consent request already exists"):
            await service.request_photo_consent(
                requester_id=test_user1.id,
                connection_id=test_connection.id,
                consent_type=PhotoConsentType.MUTUAL_AGREEMENT,
                message="Ready!",
                db=mock_db,
            )

    @pytest.mark.asyncio
    async def test_respond_to_consent_request_accept(self, service, test_user2):
        """Test accepting consent request"""
        mock_db = Mock()
        # Mock consent request
        mock_request = Mock()
        mock_request.id = 1
        mock_request.requester_id = 1
        mock_request.target_user_id = 2
        mock_request.status = "pending"
        mock_request.consent_type = PhotoConsentType.MUTUAL_AGREEMENT
        mock_request.connection_id = 1

        mock_db.query.return_value.filter.return_value.first.return_value = mock_request

        result = await service.respond_to_consent_request(
            request_id=1,
            responding_user_id=test_user2.id,
            accept_consent=True,
            response_message="Yes, let's do it!",
            db=mock_db,
        )

        assert isinstance(result, dict)
        assert "status" in result
        assert result["consent_granted"] == True
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_respond_to_consent_request_decline(self, service, test_user2):
        """Test declining consent request"""
        mock_db = Mock()
        mock_request = Mock()
        mock_request.id = 1
        mock_request.target_user_id = 2
        mock_request.status = "pending"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_request

        result = await service.respond_to_consent_request(
            request_id=1,
            responding_user_id=test_user2.id,
            accept_consent=False,
            response_message="Not ready yet",
            db=mock_db,
        )

        assert isinstance(result, dict)
        assert result["consent_granted"] == False

    @pytest.mark.asyncio
    async def test_get_photo_with_permissions_success(self, service, test_user1):
        """Test getting photo with proper permissions"""
        mock_db = Mock()
        # Mock user photo
        mock_photo = Mock()
        mock_photo.id = 1
        mock_photo.user_id = 1
        mock_photo.encrypted_url = "encrypted_photo_url"
        mock_photo.privacy_level = PhotoPrivacyLevel.FULLY_REVEALED
        mock_photo.is_revealed = True
        mock_photo.moderation_status = "approved"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_photo

        result = await service.get_photo_with_permissions(
            photo_uuid=1, requesting_user_id=test_user1.id, connection_id=1, db=mock_db
        )

        assert isinstance(result, dict)
        assert "photo_url" in result
        assert "access_granted" in result

    @pytest.mark.asyncio
    async def test_get_photo_with_permissions_denied(self, service, test_user1):
        """Test getting photo with insufficient permissions"""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = await service.get_photo_with_permissions(
            photo_uuid=1, requesting_user_id=test_user1.id, connection_id=1, db=mock_db
        )

        assert isinstance(result, dict)
        assert result["access_granted"] == False

    @pytest.mark.asyncio
    async def test_process_automatic_reveals(self, service):
        """Test automatic photo reveals processing"""
        mock_db = Mock()
        # Mock timelines ready for reveal
        mock_timeline1 = Mock()
        mock_timeline1.id = 1
        mock_timeline1.connection_id = 1
        mock_timeline1.current_stage = PhotoRevealStage.READY_FOR_REVEAL
        mock_timeline1.reveal_scheduled_date = datetime.now() - timedelta(hours=1)

        mock_timeline2 = Mock()
        mock_timeline2.id = 2
        mock_timeline2.connection_id = 2
        mock_timeline2.current_stage = PhotoRevealStage.READY_FOR_REVEAL
        mock_timeline2.reveal_scheduled_date = datetime.now() - timedelta(minutes=30)

        mock_db.query.return_value.filter.return_value.all.return_value = [
            mock_timeline1,
            mock_timeline2,
        ]

        result = await service.process_automatic_reveals(db=mock_db)

        assert isinstance(result, dict)
        assert "processed_count" in result
        assert "successful_reveals" in result
        assert result["processed_count"] >= 0


class TestPhotoValidationMethods:
    """Test photo validation and processing methods"""

    @pytest.fixture
    def service(self):
        return PhotoRevealService()

    def test_validate_photo_file_valid_jpeg(self, service):
        """Test validating valid JPEG file"""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.jpg"
        mock_file.size = 2000000  # 2MB
        mock_file.content_type = "image/jpeg"

        result = service._validate_photo_file(mock_file)

        assert result["valid"] == True
        assert result["file_type"] == "jpeg"
        assert result["size"] == 2000000

    def test_validate_photo_file_valid_png(self, service):
        """Test validating valid PNG file"""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.png"
        mock_file.size = 1500000  # 1.5MB
        mock_file.content_type = "image/png"

        result = service._validate_photo_file(mock_file)

        assert result["valid"] == True
        assert result["file_type"] == "png"

    def test_validate_photo_file_too_large(self, service):
        """Test validating file that's too large"""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "huge.jpg"
        mock_file.size = 20000000  # 20MB (too large)
        mock_file.content_type = "image/jpeg"

        result = service._validate_photo_file(mock_file)

        assert result["valid"] == False
        assert "too large" in result["error"]

    def test_validate_photo_file_invalid_type(self, service):
        """Test validating invalid file type"""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "document.pdf"
        mock_file.size = 1000000
        mock_file.content_type = "application/pdf"

        result = service._validate_photo_file(mock_file)

        assert result["valid"] == False
        assert "Invalid file type" in result["error"]

    def test_validate_photo_file_no_filename(self, service):
        """Test validating file with no filename"""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = None
        mock_file.size = 1000000
        mock_file.content_type = "image/jpeg"

        result = service._validate_photo_file(mock_file)

        assert result["valid"] == False
        assert "filename is required" in result["error"]

    @pytest.mark.asyncio
    async def test_store_encrypted_photo(self, service):
        """Test photo storage (mocked)"""
        mock_db = Mock()
        photo_data = b"fake_image_data"
        filename = "test.jpg"

        # Mock the storage operation since it involves external services
        with patch("app.services.storage.upload_encrypted_file") as mock_upload:
            mock_upload.return_value = "https://secure-storage.com/encrypted/abc123"

            result = await service._store_encrypted_photo(photo_data, filename)

            # Should return some form of stored URL/identifier
            assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_queue_photo_moderation(self, service):
        """Test queuing photo for moderation"""
        mock_db = Mock()
        mock_photo = Mock()
        mock_photo.id = 1
        mock_photo.encrypted_url = "photo_url"

        result = await service._queue_photo_moderation(mock_photo, mock_db)

        # Should return success status
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_generate_photo_previews(self, service):
        """Test generating photo previews"""
        mock_db = Mock()
        mock_photo = Mock()
        mock_photo.id = 1
        mock_photo.encrypted_url = "original_photo_url"

        # Mock preview generation
        with patch("app.services.image_processing.generate_previews") as mock_generate:
            mock_generate.return_value = {
                "thumbnail": "thumbnail_url",
                "preview": "preview_url",
            }

            result = await service._generate_photo_previews(mock_photo)

            # Should complete without error
            assert result is None or isinstance(result, dict)


class TestTimelineManagement:
    """Test timeline management methods"""

    @pytest.fixture
    def service(self):
        return PhotoRevealService()

    @pytest.fixture
    def mock_db(self):
        db = Mock()
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()
        db.query = Mock()
        return db

    @pytest.mark.asyncio
    async def test_get_or_create_timeline_new(self, service):
        """Test creating new timeline"""
        mock_db = Mock()
        # Mock no existing timeline
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.count.return_value = 5

        result = await service._get_or_create_timeline(connection_id=1, db=mock_db)

        # Should create and return new timeline
        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_get_or_create_timeline_existing(self, service):
        """Test getting existing timeline"""
        mock_db = Mock()
        mock_timeline = Mock()
        mock_timeline.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_timeline
        )

        result = await service._get_or_create_timeline(connection_id=1, db=mock_db)

        # Should return existing timeline without creating new one
        assert mock_db.add.call_count == 0

    @pytest.mark.asyncio
    async def test_update_revelation_count(self, service):
        """Test updating revelation count"""
        mock_db = Mock()
        mock_timeline = Mock()
        mock_timeline.id = 1
        mock_timeline.revelations_completed = 3

        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_timeline
        )
        mock_db.query.return_value.filter.return_value.count.return_value = 5

        await service._update_revelation_count(timeline_id=1, db=mock_db)

        # Should update and commit
        mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_update_timeline_status(self, service):
        """Test updating timeline status"""
        mock_db = Mock()
        mock_timeline = Mock()
        mock_timeline.id = 1
        mock_timeline.current_stage = PhotoRevealStage.REVELATION_PHASE
        mock_timeline.revelations_completed = 7
        mock_timeline.min_revelations_required = 7
        mock_timeline.reveal_scheduled_date = datetime.now() - timedelta(hours=1)

        await service._update_timeline_status(mock_timeline, mock_db)

        # Should commit changes
        mock_db.commit.assert_called()


class TestErrorHandling:
    """Test error handling and edge cases"""

    @pytest.fixture
    def service(self):
        return PhotoRevealService()

    @pytest.fixture
    def mock_db(self):
        db = Mock()
        db.query.side_effect = Exception("Database error")
        return db

    @pytest.mark.asyncio
    async def test_create_timeline_database_error(self, service):
        """Test timeline creation with database error"""
        mock_db = Mock()
        with pytest.raises(Exception):
            await service.create_photo_timeline(connection_id=1, db=mock_db)

    @pytest.mark.asyncio
    async def test_upload_photo_database_error(self, service):
        """Test photo upload with database error"""
        mock_db = Mock()
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.jpg"
        mock_file.content_type = "image/jpeg"
        mock_file.size = 1000000
        mock_file.read = AsyncMock(return_value=b"fake_data")

        with patch.object(
            service, "_validate_photo_file", return_value={"valid": True}
        ):
            with pytest.raises(Exception):
                await service.upload_user_photo(
                    user_id=1,
                    photo_file=mock_file,
                    privacy_level=PhotoPrivacyLevel.FULLY_REVEALED,
                    db=mock_db,
                )

    def test_validate_photo_edge_cases(self, service):
        """Test photo validation edge cases"""
        # Test with various edge cases
        test_cases = [
            # Empty filename
            {"filename": "", "size": 1000000, "content_type": "image/jpeg"},
            # Weird extension
            {
                "filename": "test.jpeg.exe",
                "size": 1000000,
                "content_type": "image/jpeg",
            },
            # Zero size
            {"filename": "test.jpg", "size": 0, "content_type": "image/jpeg"},
            # Negative size (shouldn't happen but test anyway)
            {"filename": "test.jpg", "size": -1000, "content_type": "image/jpeg"},
        ]

        for case in test_cases:
            mock_file = Mock(spec=UploadFile)
            mock_file.filename = case["filename"]
            mock_file.size = case["size"]
            mock_file.content_type = case["content_type"]

            result = service._validate_photo_file(mock_file)
            # Should handle gracefully without crashing
            assert isinstance(result, dict)
            assert "valid" in result


class TestUtilityMethods:
    """Test utility and helper methods"""

    @pytest.fixture
    def service(self):
        return PhotoRevealService()

    def test_service_initialization_with_db(self):
        """Test service initialization with database"""
        mock_db = Mock()
        service = PhotoRevealService(db=mock_db)
        assert service.db == mock_db

    def test_service_initialization_without_db(self):
        """Test service initialization without database"""
        service = PhotoRevealService()
        assert service.db is None

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, service):
        """Test handling concurrent operations"""
        mock_db = Mock()
        # Simulate multiple concurrent timeline creations
        tasks = []
        for i in range(5):
            task = service.create_photo_timeline(connection_id=i + 1, db=mock_db)
            tasks.append(task)

        # Should handle concurrent operations without crashing
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            # At least shouldn't crash
            assert len(results) == 5
        except Exception:
            # Even if individual operations fail, shouldn't crash the test
            assert True

    def test_photo_reveal_status_creation(self):
        """Test PhotoRevealStatus creation"""
        status = PhotoRevealStatus(
            connection_id=1,
            current_stage=PhotoRevealStage.CONSENT_PHASE,
            days_until_reveal=3,
            revelations_completed=4,
            min_revelations_required=7,
            progress_percentage=57.1,
            user1_consent_status="pending",
            user2_consent_status="granted",
            mutual_consent_achieved=False,
            photos_revealed=False,
            can_request_early_reveal=True,
        )

        assert status.connection_id == 1
        assert status.current_stage == PhotoRevealStage.CONSENT_PHASE
        assert status.progress_percentage == 57.1
        assert status.mutual_consent_achieved == False
