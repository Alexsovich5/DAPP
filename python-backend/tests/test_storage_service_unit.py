"""
Unit tests for storage service functionality
Tests file upload, validation, and security methods without AWS dependencies
"""

import pytest
import os
from unittest.mock import Mock, patch, AsyncMock
from botocore.exceptions import ClientError
from fastapi import UploadFile

from app.services.storage import (
    upload_file,
    delete_file,
    validate_file_upload,
    generate_secure_filename
)


@pytest.mark.unit
@pytest.mark.security
class TestStorageService:
    """Test suite for storage service functions"""
    
    def test_validate_file_upload_valid_jpeg(self):
        """Test file validation with valid JPEG file"""
        filename = "test.jpg"
        file_data = b"fake_image_data" * 100  # Small file
        content_type = "image/jpeg"
        
        result = validate_file_upload(filename, file_data, content_type)
        assert result is True
    
    def test_validate_file_upload_valid_png(self):
        """Test file validation with valid PNG file"""
        filename = "test.png"
        file_data = b"fake_image_data" * 100
        content_type = "image/png"
        
        result = validate_file_upload(filename, file_data, content_type)
        assert result is True
    
    def test_validate_file_upload_valid_webp(self):
        """Test file validation with valid WebP file"""
        filename = "test.webp"
        file_data = b"fake_image_data" * 100
        content_type = "image/webp"
        
        result = validate_file_upload(filename, file_data, content_type)
        assert result is True
    
    def test_validate_file_upload_file_too_large(self):
        """Test file validation with file exceeding size limit"""
        filename = "test.jpg"
        # Create file larger than 5MB
        file_data = b"x" * (6 * 1024 * 1024)  # 6MB
        content_type = "image/jpeg"
        
        result = validate_file_upload(filename, file_data, content_type)
        assert result is False
    
    def test_validate_file_upload_invalid_content_type(self):
        """Test file validation with invalid content type"""
        filename = "test.txt"
        file_data = b"fake_text_data"
        content_type = "text/plain"
        
        result = validate_file_upload(filename, file_data, content_type)
        assert result is False
    
    def test_validate_file_upload_invalid_extension(self):
        """Test file validation with invalid file extension"""
        filename = "test.exe"
        file_data = b"fake_executable_data"
        content_type = "image/jpeg"  # Even with valid content type
        
        result = validate_file_upload(filename, file_data, content_type)
        assert result is False
    
    def test_validate_file_upload_mismatched_extension_content_type(self):
        """Test file validation with mismatched extension and content type"""
        filename = "test.txt"  # Text extension
        file_data = b"fake_image_data"
        content_type = "image/jpeg"  # Image content type
        
        result = validate_file_upload(filename, file_data, content_type)
        assert result is False
    
    def test_validate_file_upload_case_insensitive_extensions(self):
        """Test file validation handles case-insensitive extensions"""
        filename = "TEST.JPG"  # Uppercase extension
        file_data = b"fake_image_data" * 100
        content_type = "image/jpeg"
        
        result = validate_file_upload(filename, file_data, content_type)
        assert result is True
    
    def test_validate_file_upload_edge_case_5mb_exactly(self):
        """Test file validation with exactly 5MB file (should pass)"""
        filename = "test.jpg"
        file_data = b"x" * (5 * 1024 * 1024)  # Exactly 5MB
        content_type = "image/jpeg"
        
        result = validate_file_upload(filename, file_data, content_type)
        assert result is True
    
    def test_validate_file_upload_gif_support(self):
        """Test file validation supports GIF files"""
        filename = "animated.gif"
        file_data = b"fake_gif_data" * 100
        content_type = "image/gif"
        
        result = validate_file_upload(filename, file_data, content_type)
        assert result is True
    
    def test_generate_secure_filename_basic(self):
        """Test secure filename generation with basic filename"""
        original = "profile_photo.jpg"
        
        result = generate_secure_filename(original)
        
        # Should contain UUID prefix, underscore, original name (sanitized), and extension
        assert result.endswith("_profile_photo.jpg")
        assert len(result) > len(original)  # Should be longer due to UUID prefix
        assert "_" in result
    
    def test_generate_secure_filename_with_spaces(self):
        """Test secure filename generation replaces spaces"""
        original = "my profile photo.jpg"
        
        result = generate_secure_filename(original)
        
        # Spaces should be replaced with underscores
        assert "my_profile_photo.jpg" in result
        assert " " not in result
    
    def test_generate_secure_filename_with_special_chars(self):
        """Test secure filename generation removes special characters"""
        original = "photo@#$%^&*.jpg"
        
        result = generate_secure_filename(original)
        
        # Special characters should be replaced with underscores
        assert "photo_______.jpg" in result
        assert "@" not in result
        assert "#" not in result
    
    def test_generate_secure_filename_path_traversal_protection(self):
        """Test secure filename generation prevents path traversal"""
        original = "../../../evil.jpg"
        
        result = generate_secure_filename(original)
        
        # Should only contain the basename, no path separators
        assert "evil.jpg" in result
        assert ".." not in result
        assert "/" not in result
        assert "\\" not in result
    
    def test_generate_secure_filename_preserves_extension(self):
        """Test secure filename generation preserves file extension"""
        test_files = [
            "test.jpg",
            "document.pdf", 
            "image.png",
            "archive.zip"
        ]
        
        for original in test_files:
            result = generate_secure_filename(original)
            original_ext = os.path.splitext(original)[1]
            assert result.endswith(original_ext)
    
    def test_generate_secure_filename_no_extension(self):
        """Test secure filename generation with file without extension"""
        original = "README"
        
        result = generate_secure_filename(original)
        
        assert "README" in result
        assert len(result) > len(original)  # Should have UUID prefix
    
    def test_generate_secure_filename_uuid_uniqueness(self):
        """Test that generated filenames are unique"""
        original = "test.jpg"
        
        result1 = generate_secure_filename(original)
        result2 = generate_secure_filename(original)
        
        # Results should be different due to UUID
        assert result1 != result2
        both_end_with_test_jpg = result1.endswith("_test.jpg") and result2.endswith("_test.jpg")
        assert both_end_with_test_jpg
    
    @pytest.mark.asyncio
    async def test_upload_file_success(self):
        """Test successful file upload to S3"""
        # Mock UploadFile
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.jpg"
        mock_file.file = Mock()
        
        # Mock S3 client
        with patch('app.services.storage.s3_client') as mock_s3:
            mock_s3.upload_fileobj.return_value = None
            
            with patch('app.services.storage.BUCKET_NAME', 'test-bucket'):
                result = await upload_file(mock_file, "profiles")
        
        # Should return S3 URL
        assert result.startswith("https://test-bucket.s3.amazonaws.com/profiles/")
        assert result.endswith(".jpg")
        mock_s3.upload_fileobj.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_file_client_error(self):
        """Test file upload handles S3 client errors"""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.jpg"
        mock_file.file = Mock()
        
        # Mock S3 client to raise ClientError
        with patch('app.services.storage.s3_client') as mock_s3:
            mock_s3.upload_fileobj.side_effect = ClientError(
                error_response={'Error': {'Code': 'AccessDenied', 'Message': 'Access Denied'}},
                operation_name='upload_fileobj'
            )
            
            with pytest.raises(ClientError):
                await upload_file(mock_file, "profiles")
    
    @pytest.mark.asyncio
    async def test_upload_file_generates_unique_filename(self):
        """Test that upload generates unique filename"""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "test.jpg"
        mock_file.file = Mock()
        
        with patch('app.services.storage.s3_client') as mock_s3:
            mock_s3.upload_fileobj.return_value = None
            
            with patch('app.services.storage.BUCKET_NAME', 'test-bucket'):
                with patch('os.urandom', return_value=b'1234567890123456'):  # Mock random bytes
                    result = await upload_file(mock_file, "profiles")
        
        # Should contain the mocked hex value
        expected_hex = '31323334353637383930313233343536'  # hex of '1234567890123456'
        assert expected_hex in result
    
    @pytest.mark.asyncio
    async def test_delete_file_success(self):
        """Test successful file deletion from S3"""
        file_url = "https://test-bucket.s3.amazonaws.com/profiles/test123.jpg"
        
        with patch('app.services.storage.s3_client') as mock_s3:
            mock_s3.delete_object.return_value = None
            
            with patch('app.services.storage.BUCKET_NAME', 'test-bucket'):
                result = await delete_file(file_url)
        
        assert result is True
        mock_s3.delete_object.assert_called_once_with(
            Bucket='test-bucket',
            Key='profiles/test123.jpg'
        )
    
    @pytest.mark.asyncio
    async def test_delete_file_client_error(self):
        """Test file deletion handles S3 client errors"""
        file_url = "https://test-bucket.s3.amazonaws.com/profiles/test123.jpg"
        
        with patch('app.services.storage.s3_client') as mock_s3:
            mock_s3.delete_object.side_effect = ClientError(
                error_response={'Error': {'Code': 'NoSuchKey', 'Message': 'Key not found'}},
                operation_name='delete_object'
            )
            
            with patch('app.services.storage.BUCKET_NAME', 'test-bucket'):
                with pytest.raises(ClientError):
                    await delete_file(file_url)
    
    @pytest.mark.asyncio
    async def test_delete_file_extracts_key_correctly(self):
        """Test file deletion extracts the correct S3 key from URL"""
        file_url = "https://my-bucket.s3.amazonaws.com/uploads/images/photo123.png"
        
        with patch('app.services.storage.s3_client') as mock_s3:
            mock_s3.delete_object.return_value = None
            
            with patch('app.services.storage.BUCKET_NAME', 'my-bucket'):
                await delete_file(file_url)
        
        # Should extract the correct key after the bucket name
        mock_s3.delete_object.assert_called_once_with(
            Bucket='my-bucket',
            Key='uploads/images/photo123.png'
        )


@pytest.mark.unit
@pytest.mark.security
class TestStorageServiceEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_validate_file_upload_empty_filename(self):
        """Test file validation with empty filename"""
        filename = ""
        file_data = b"fake_image_data"
        content_type = "image/jpeg"
        
        result = validate_file_upload(filename, file_data, content_type)
        assert result is False
    
    def test_validate_file_upload_no_extension(self):
        """Test file validation with filename without extension"""
        filename = "imagefile"  # No extension
        file_data = b"fake_image_data"
        content_type = "image/jpeg"
        
        result = validate_file_upload(filename, file_data, content_type)
        assert result is False
    
    def test_validate_file_upload_multiple_dots(self):
        """Test file validation with filename containing multiple dots"""
        filename = "my.backup.file.jpg"
        file_data = b"fake_image_data"
        content_type = "image/jpeg"
        
        result = validate_file_upload(filename, file_data, content_type)
        assert result is True  # Should work, extension is .jpg
    
    def test_generate_secure_filename_very_long_name(self):
        """Test secure filename generation with very long filename"""
        original = "a" * 200 + ".jpg"  # Very long filename
        
        result = generate_secure_filename(original)
        
        # Should still work and include the extension
        assert result.endswith(".jpg")
        assert "a" * 200 in result  # Original name should be preserved
    
    def test_generate_secure_filename_unicode_characters(self):
        """Test secure filename generation with unicode characters"""
        original = "файл.jpg"  # Cyrillic characters
        
        result = generate_secure_filename(original)
        
        # The regex [^\w\-_.] preserves unicode word characters, so cyrillic should remain
        # but should have UUID prefix and be safe
        assert "файл" in result  # Unicode word characters are preserved
        assert result.endswith(".jpg")
        assert len(result) > len(original)  # Should have UUID prefix
    
    @pytest.mark.asyncio
    async def test_upload_file_no_extension(self):
        """Test file upload with no extension"""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "README"  # No extension
        mock_file.file = Mock()
        
        with patch('app.services.storage.s3_client') as mock_s3:
            mock_s3.upload_fileobj.return_value = None
            
            result = await upload_file(mock_file, "docs")
        
        # Should still work, just no extension in result
        assert "docs/" in result
        assert not result.endswith(".")
    
    @pytest.mark.asyncio
    async def test_delete_file_malformed_url(self):
        """Test file deletion with malformed URL"""
        malformed_url = "not-a-valid-s3-url"
        
        with patch('app.services.storage.s3_client') as mock_s3:
            # This should raise an exception when trying to split the URL
            with pytest.raises(IndexError):
                await delete_file(malformed_url)


@pytest.mark.integration
class TestStorageServiceIntegration:
    """Test storage service integration scenarios"""
    
    def test_all_supported_image_types(self):
        """Test that all supported image types are validated correctly"""
        supported_types = [
            ("test.jpg", "image/jpeg"),
            ("test.jpeg", "image/jpg"), 
            ("test.png", "image/png"),
            ("test.gif", "image/gif"),
            ("test.webp", "image/webp")
        ]
        
        file_data = b"fake_image_data" * 100
        
        for filename, content_type in supported_types:
            result = validate_file_upload(filename, file_data, content_type)
            assert result is True, f"Failed for {filename} with {content_type}"
    
    def test_common_invalid_types(self):
        """Test that common invalid file types are rejected"""
        invalid_types = [
            ("document.pdf", "application/pdf"),
            ("script.js", "application/javascript"),
            ("style.css", "text/css"),
            ("data.json", "application/json"),
            ("archive.zip", "application/zip"),
            ("executable.exe", "application/x-executable")
        ]
        
        file_data = b"fake_file_data"
        
        for filename, content_type in invalid_types:
            result = validate_file_upload(filename, file_data, content_type)
            assert result is False, f"Should reject {filename} with {content_type}"
    
    @pytest.mark.asyncio
    async def test_upload_delete_workflow(self):
        """Test complete upload and delete workflow"""
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "profile.jpg"
        mock_file.file = Mock()
        
        with patch('app.services.storage.s3_client') as mock_s3:
            mock_s3.upload_fileobj.return_value = None
            mock_s3.delete_object.return_value = None
            
            # Upload file
            upload_result = await upload_file(mock_file, "profiles")
            assert upload_result.startswith("https://")
            
            # Delete file
            delete_result = await delete_file(upload_result)
            assert delete_result is True
            
            # Verify both operations were called
            mock_s3.upload_fileobj.assert_called_once()
            mock_s3.delete_object.assert_called_once()