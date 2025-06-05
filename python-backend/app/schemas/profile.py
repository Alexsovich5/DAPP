from pydantic import BaseModel, HttpUrl, validator
from typing import Optional, List, Union
from enum import Enum
from datetime import datetime

# Constants for URL prefixes
HTTP_PREFIX = "http://"
HTTPS_PREFIX = "https://"


class VerificationStatus(str, Enum):
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"


class ProfileBase(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None

    # Photo fields - make URLs more flexible by accepting strings
    avatar_url: Optional[Union[HttpUrl, str]] = None
    profile_photos: Optional[List[Union[HttpUrl, str]]] = None

    # Basic preferences
    cuisine_preferences: Optional[str] = None
    dietary_restrictions: Optional[str] = None

    # Enhanced preferences
    cooking_level: Optional[str] = None
    preferred_dining_time: Optional[str] = None
    preferred_meal_types: Optional[str] = None
    preferred_group_size: Optional[int] = None
    food_allergies: Optional[str] = None
    special_diets: Optional[str] = None

    # Validators to handle string URLs
    @validator("avatar_url", pre=True)
    def validate_avatar_url(cls, v):
        if isinstance(v, str) and v and not v.startswith((HTTP_PREFIX, HTTPS_PREFIX)):
            return f"{HTTPS_PREFIX}{v}"
        return v

    @validator("profile_photos", each_item=True, pre=True)
    def validate_profile_photos(cls, v):
        if isinstance(v, str) and v:
            if not (v.startswith(HTTP_PREFIX) or v.startswith(HTTPS_PREFIX)):
                return f"{HTTPS_PREFIX}{v}"
        return v


class ProfileCreate(ProfileBase):
    pass


class ProfileUpdate(ProfileBase):
    pass


class Profile(ProfileBase):
    id: int
    user_id: int
    is_verified: Optional[bool] = False
    verification_status: Optional[VerificationStatus] = VerificationStatus.UNVERIFIED
    verification_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class ProfilePhoto(BaseModel):
    """Schema for profile photo upload response"""

    url: str


class VerificationRequest(BaseModel):
    """Schema for profile verification request"""

    verification_method: str
    verification_document: Optional[str] = None
