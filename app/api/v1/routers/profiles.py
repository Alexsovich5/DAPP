from typing import Any
import logging
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.models.profile import Profile, VerificationStatus
from app.schemas.profile import (
    ProfileCreate,
    ProfileUpdate,
    Profile as ProfileSchema,
    ProfilePhoto,
    VerificationRequest,
)
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.services.storage import upload_file, delete_file

# Configure logging
logger = logging.getLogger(__name__)

# Error messages
PROFILE_NOT_FOUND = "Profile not found"
PROFILE_EXISTS = "Profile already exists for this user"
INVALID_FILE_TYPE = "Invalid file type. Only images are allowed"
MAX_PHOTOS_REACHED = "Maximum number of photos reached"

router = APIRouter(tags=["profiles"])


@router.post("/", response_model=ProfileSchema)
def create_profile(
    profile_in: ProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Create new profile for current user."""
    if current_user.profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=PROFILE_EXISTS
        )

    try:
        # Convert profile data to dict and prepare for database
        profile_data = profile_in.dict()

        # Ensure profile_photos is initialized correctly for JSON column
        if profile_data.get("profile_photos") is None:
            profile_data["profile_photos"] = []

        # Ensure favorite_cuisines is initialized correctly for JSON column
        if profile_data.get("favorite_cuisines") is None:
            profile_data["favorite_cuisines"] = []

        # Create and save profile
        profile = Profile(**profile_data, user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
        logger.info(f"Created profile for user: {current_user.id}")
        return profile
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating profile: {str(e)}",
        )


@router.get("/", response_model=ProfileSchema)
@router.get("/me", response_model=ProfileSchema)
def get_my_profile(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Any:
    """Get current user's profile."""
    if not current_user.profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=PROFILE_NOT_FOUND
        )
    return current_user.profile


@router.put("/", response_model=ProfileSchema)
@router.put("/me", response_model=ProfileSchema)
def update_my_profile(
    profile_in: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Update current user's profile."""
    if not current_user.profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=PROFILE_NOT_FOUND
        )

    for field, value in profile_in.dict(exclude_unset=True).items():
        setattr(current_user.profile, field, value)

    db.commit()
    db.refresh(current_user.profile)
    return current_user.profile


@router.get("/{user_id}", response_model=ProfileSchema)
def get_profile(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get profile by user ID."""
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=PROFILE_NOT_FOUND
        )
    return profile


@router.post("/photos", response_model=ProfilePhoto)
async def upload_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Upload a new profile photo."""
    if not current_user.profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=PROFILE_NOT_FOUND
        )

    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=INVALID_FILE_TYPE
        )

    try:
        # Check photo limit - initialize empty list if None
        current_photos = current_user.profile.profile_photos or []
        if len(current_photos) >= 5:  # Maximum 5 photos per profile
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=MAX_PHOTOS_REACHED
            )

        # Upload file and get URL
        file_url = await upload_file(file, f"profiles/{current_user.id}")

        # Update profile - handle both list and None cases
        photos = current_user.profile.profile_photos or []
        photos.append(file_url)
        current_user.profile.profile_photos = photos

        db.commit()
        db.refresh(current_user.profile)
        logger.info(f"Added photo for user: {current_user.id}")

        return ProfilePhoto(url=file_url)
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error uploading photo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading photo: {str(e)}",
        )


@router.delete("/photos/{photo_url:path}")
async def delete_photo(
    photo_url: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Delete a profile photo."""
    if not current_user.profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=PROFILE_NOT_FOUND
        )

    try:
        # Remove photo from profile - ensure it's a list
        photos = current_user.profile.profile_photos or []
        if photo_url not in photos:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found"
            )

        photos.remove(photo_url)
        current_user.profile.profile_photos = photos

        # Delete from storage
        await delete_file(photo_url)

        db.commit()
        logger.info(f"Deleted photo for user: {current_user.id}")
        return {"message": "Photo deleted successfully"}
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting photo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting photo: {str(e)}",
        )


@router.post("/verify", response_model=ProfileSchema)
async def request_verification(
    verification: VerificationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Request profile verification."""
    if not current_user.profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=PROFILE_NOT_FOUND
        )

    # Update verification status
    current_user.profile.verification_status = VerificationStatus.PENDING
    current_user.profile.verification_method = verification.verification_method

    if verification.verification_document:
        current_user.profile.verification_document_url = (
            verification.verification_document
        )

    db.commit()
    db.refresh(current_user.profile)

    return current_user.profile


@router.put("/verify/{user_id}/approve")
async def approve_verification(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Approve a user's verification request (admin only)."""
    # Admin check should be implemented here
    # For now, allowing any authenticated user to approve verification

    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=PROFILE_NOT_FOUND
        )

    profile.verification_status = VerificationStatus.VERIFIED
    profile.is_verified = True
    profile.verification_date = datetime.utcnow()

    db.commit()
    return {"message": "Profile verification approved"}
