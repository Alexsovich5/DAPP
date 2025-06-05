from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    Boolean,
    JSON,
    Enum,
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class VerificationStatus(str, enum.Enum):
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    full_name = Column(String(100), nullable=True)
    bio = Column(String(500), nullable=True)
    cuisine_preferences = Column(String(255), nullable=True)
    dietary_restrictions = Column(String(255), nullable=True)
    location = Column(String(100), nullable=True)
    avatar_url = Column(String(255), nullable=True)

    # Changed from String to JSON type for proper data storage
    # Store an array of photo URLs
    profile_photos = Column(JSON, nullable=True)

    # Verification fields
    is_verified = Column(Boolean, default=False)
    verification_status = Column(
        Enum(VerificationStatus), default=VerificationStatus.UNVERIFIED, nullable=False
    )
    verification_date = Column(DateTime, nullable=True)
    verification_method = Column(String, nullable=True)

    # Enhanced preference fields
    # beginner, intermediate, expert
    cooking_level = Column(String, nullable=True)
    # morning, afternoon, evening
    preferred_dining_time = Column(String, nullable=True)
    preferred_meal_types = Column(String, nullable=True)
    # homemade, restaurant, both
    preferred_group_size = Column(Integer, nullable=True)
    food_allergies = Column(String, nullable=True)
    special_diets = Column(String, nullable=True)  # kosher, halal, vegan, etc.
    # Changed to JSON for better data storage
    favorite_cuisines = Column(JSON, nullable=True)
    price_range = Column(String, nullable=True)  # budget, mid-range, high-end

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="profile")
