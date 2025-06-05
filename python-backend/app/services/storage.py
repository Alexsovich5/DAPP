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

        # Upload file
        await s3_client.upload_fileobj(
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

        # Delete file
        await s3_client.delete_object(Bucket=BUCKET_NAME, Key=key)
        return True
    except ClientError as e:
        logger.error(f"Error deleting file: {e}")
        raise
