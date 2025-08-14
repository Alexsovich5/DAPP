"""
Storage Service Tests - High-impact coverage for file operations
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import os
from fastapi import UploadFile
import io

from app.services.storage import (
    validate_file_upload,
    generate_secure_filename,
    upload_file,
    delete_file,
)


class TestFileValidation:
    """Test file validation and security functions"""

    def test_validate_file_upload_valid_image(self):
        """Test validation of valid image file"""
        filename = "test.jpg"
        file_data = b"fake image data" * 100  # Small file
        content_type = "image/jpeg"
        
        assert validate_file_upload(filename, file_data, content_type) is True

    def test_validate_file_upload_file_too_large(self):
        """Test validation rejects files over 5MB"""
        filename = "large.jpg"
        file_data = b"x" * (6 * 1024 * 1024)  # 6MB file
        content_type = "image/jpeg"
        
        assert validate_file_upload(filename, file_data, content_type) is False

    def test_validate_file_upload_invalid_content_type(self):
        """Test validation rejects invalid content types"""
        filename = "test.exe"
        file_data = b"fake data"
        content_type = "application/octet-stream"
        
        assert validate_file_upload(filename, file_data, content_type) is False

    def test_validate_file_upload_invalid_extension(self):
        """Test validation rejects invalid file extensions"""
        filename = "test.exe"
        file_data = b"fake data"
        content_type = "image/jpeg"  # Content type is valid but extension is not
        
        assert validate_file_upload(filename, file_data, content_type) is False

    def test_validate_file_upload_all_allowed_types(self):
        """Test all allowed image types are accepted"""
        allowed_types = [
            ("image/jpeg", "test.jpg"),
            ("image/jpg", "test.jpg"),
            ("image/png", "test.png"),
            ("image/gif", "test.gif"),
            ("image/webp", "test.webp")
        ]
        
        file_data = b"fake data"
        
        for content_type, filename in allowed_types:
            assert validate_file_upload(filename, file_data, content_type) is True


class TestSecureFilename:
    """Test secure filename generation"""

    def test_generate_secure_filename_basic(self):
        """Test basic secure filename generation"""
        original = "test_image.jpg"
        secure = generate_secure_filename(original)
        
        assert secure.endswith("_test_image.jpg")
        assert len(secure) > len(original)  # Should have UUID prefix
        
    def test_generate_secure_filename_path_traversal(self):
        """Test protection against path traversal attacks"""
        malicious = "../../etc/passwd"
        secure = generate_secure_filename(malicious)
        
        assert ".." not in secure
        assert "/" not in secure
        assert secure.endswith("_passwd")

    def test_generate_secure_filename_special_chars(self):
        """Test removal of special characters"""
        original = "test@file#with$special%chars.jpg"
        secure = generate_secure_filename(original)
        
        # Special chars should be replaced with underscores
        assert "@" not in secure
        assert "#" not in secure
        assert "$" not in secure
        assert "%" not in secure
        assert secure.endswith(".jpg")

    def test_generate_secure_filename_no_extension(self):
        """Test filename without extension"""
        original = "filename_without_extension"
        secure = generate_secure_filename(original)
        
        assert secure.endswith("_filename_without_extension")
        assert len(secure) > len(original)


class TestStorageOperations:
    """Test S3 storage operations with mocked AWS"""

    @patch('app.services.storage.s3_client')
    async def test_upload_file_success(self, mock_s3_client):
        """Test successful file upload"""
        # Mock UploadFile
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.jpg"
        mock_file.file = io.BytesIO(b"fake image data")
        
        # Mock S3 client
        mock_s3_client.upload_fileobj = Mock()
        
        result = await upload_file(mock_file, "profiles/123")
        
        # Check that S3 client was called
        mock_s3_client.upload_fileobj.assert_called_once()
        
        # Check return URL format
        assert result.startswith("https://")
        assert "profiles/123" in result
        assert result.endswith(".jpg")

    @patch('app.services.storage.s3_client')
    async def test_upload_file_s3_error(self, mock_s3_client):
        """Test file upload with S3 error"""
        from botocore.exceptions import ClientError
        
        # Mock UploadFile
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.jpg"
        mock_file.file = io.BytesIO(b"fake image data")
        
        # Mock S3 client to raise error
        mock_s3_client.upload_fileobj.side_effect = ClientError(
            error_response={'Error': {'Code': 'AccessDenied'}},
            operation_name='upload_fileobj'
        )
        
        # Should re-raise the ClientError
        with pytest.raises(ClientError):
            await upload_file(mock_file, "profiles/123")

    @patch('app.services.storage.s3_client')
    async def test_delete_file_success(self, mock_s3_client):
        """Test successful file deletion"""
        file_url = "https://test-bucket.s3.amazonaws.com/profiles/123/test.jpg"
        
        # Mock S3 client
        mock_s3_client.delete_object = Mock()
        
        result = await delete_file(file_url)
        
        # Check that S3 client was called
        mock_s3_client.delete_object.assert_called_once()
        assert result is True

    @patch('app.services.storage.s3_client')
    async def test_delete_file_s3_error(self, mock_s3_client):
        """Test file deletion with S3 error"""
        from botocore.exceptions import ClientError
        
        file_url = "https://test-bucket.s3.amazonaws.com/profiles/123/test.jpg"
        
        # Mock S3 client to raise error
        mock_s3_client.delete_object.side_effect = ClientError(
            error_response={'Error': {'Code': 'NoSuchKey'}},
            operation_name='delete_object'
        )
        
        # Should re-raise the ClientError
        with pytest.raises(ClientError):
            await delete_file(file_url)

    @patch.dict(os.environ, {'S3_BUCKET_NAME': 'test-bucket'})
    @patch('app.services.storage.s3_client')
    async def test_file_operations_with_custom_bucket(self, mock_s3_client):
        """Test file operations use custom bucket name from environment"""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.jpg"
        mock_file.file = io.BytesIO(b"fake image data")
        
        mock_s3_client.upload_fileobj = Mock()
        
        result = await upload_file(mock_file, "test/path")
        
        # Check that custom bucket name is used in URL
        assert "test-bucket.s3.amazonaws.com" in result


class TestFileSecurityValidation:
    """Test comprehensive file security validation"""

    def test_filename_edge_cases(self):
        """Test filename generation with edge cases"""
        edge_cases = [
            "",  # Empty filename
            ".",  # Just a dot
            ".hidden",  # Hidden file
            "file.",  # Trailing dot
            "CON.jpg",  # Reserved Windows name
            "very_long_filename_" + "x" * 200 + ".jpg"  # Very long filename
        ]
        
        for case in edge_cases:
            secure = generate_secure_filename(case)
            assert isinstance(secure, str)
            assert len(secure) > 8  # Should have UUID prefix

    def test_validation_boundary_conditions(self):
        """Test file validation boundary conditions"""
        # Exactly 5MB file
        filename = "large.jpg"
        file_data = b"x" * (5 * 1024 * 1024)
        content_type = "image/jpeg"
        
        # Should reject exactly 5MB (exclusive limit)
        assert validate_file_upload(filename, file_data, content_type) is False
        
        # Just under 5MB should pass
        file_data_small = b"x" * (5 * 1024 * 1024 - 1)
        assert validate_file_upload(filename, file_data_small, content_type) is True

    def test_case_insensitive_extensions(self):
        """Test that file extensions are handled case-insensitively"""
        test_cases = [
            ("test.JPG", "image/jpeg"),
            ("test.PNG", "image/png"),
            ("test.GIF", "image/gif"),
            ("test.WEBP", "image/webp")
        ]
        
        file_data = b"fake data"
        
        for filename, content_type in test_cases:
            assert validate_file_upload(filename, file_data, content_type) is True