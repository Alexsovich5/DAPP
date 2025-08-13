import os
import boto3
import logging
from fastapi import UploadFile
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger(__name__)

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "dinner-app-uploads")


async def upload_file(file: UploadFile, path: str) -> str:
    """Upload a file to S3 and return its URL."""
    try:
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        filename = f"{path}/{os.urandom(16).hex()}{file_extension}"

        # Upload file (boto3 S3 client methods are synchronous)
        s3_client.upload_fileobj(
            file.file, BUCKET_NAME, filename, ExtraArgs={"ACL": "public-read"}
        )

        # Return public URL
        return f"https://{BUCKET_NAME}.s3.amazonaws.com/{filename}"
    except ClientError as e:
        logger.error(f"Error uploading file: {e}")
        raise


async def delete_file(file_url: str) -> bool:
    """Delete a file from S3."""
    try:
        # Extract key from URL
        key = file_url.split(f"{BUCKET_NAME}.s3.amazonaws.com/")[1]

        # Delete file (boto3 S3 client methods are synchronous)
        s3_client.delete_object(Bucket=BUCKET_NAME, Key=key)
        return True
    except ClientError as e:
        logger.error(f"Error deleting file: {e}")
        raise


def validate_file_upload(filename: str, file_data: bytes, content_type: str) -> bool:
    """Validate file upload for security and size constraints"""
    # Check file size (max 5MB)
    if len(file_data) > 5 * 1024 * 1024:
        return False
        
    # Check allowed file types
    allowed_types = {
        "image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"
    }
    if content_type not in allowed_types:
        return False
        
    # Check file extension
    allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    file_ext = os.path.splitext(filename.lower())[1]
    if file_ext not in allowed_extensions:
        return False
        
    return True


def generate_secure_filename(original_filename: str) -> str:
    """Generate a secure filename to prevent path traversal and other attacks"""
    import uuid
    import re
    
    # Remove any path separators and suspicious characters
    filename = os.path.basename(original_filename)
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    
    # Get file extension
    name, ext = os.path.splitext(filename)
    
    # Generate unique prefix
    unique_id = str(uuid.uuid4())[:8]
    
    # Create secure filename
    secure_filename = f"{unique_id}_{name}{ext}"
    
    return secure_filename
