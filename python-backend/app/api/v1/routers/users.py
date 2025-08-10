from typing import Any, List
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy import and_, not_, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.profile import Profile
from app.models.match import Match, MatchStatus  # Added MatchStatus import
from app.schemas.auth import User as UserSchema, UserProfileUpdate
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserSchema)
def get_current_user_info(current_user: User = Depends(get_current_user)) -> Any:
    """Get current user information."""
    return current_user


@router.put("/me", response_model=UserSchema)
def update_current_user_profile(
    profile_update: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Update current user profile information."""
    
    # Update user fields
    update_data = profile_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if hasattr(current_user, field):
            setattr(current_user, field, value)
    
    # Auto-calculate profile completion
    current_user.is_profile_complete = _calculate_profile_completeness(current_user)
    
    # Save to database
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    return current_user


def _calculate_profile_completeness(user: User) -> bool:
    """Calculate if user profile is complete enough for matching."""
    required_fields = [
        user.first_name,
        user.last_name,
        user.date_of_birth,
        user.gender,
        user.location,
    ]
    
    # Check if all required fields are filled
    if not all(field for field in required_fields):
        return False
    
    # Check if at least some optional fields are filled
    optional_score = 0
    if user.bio:
        optional_score += 1
    if user.interests and len(user.interests) > 0:
        optional_score += 1
    if user.dietary_preferences and len(user.dietary_preferences) > 0:
        optional_score += 1
    
    # Profile is complete if required fields + at least 1 optional field
    return optional_score >= 1


@router.post("/me/profile-picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Upload profile picture for current user."""
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Validate file size (5MB limit)
    max_size = 5 * 1024 * 1024  # 5MB
    file_content = await file.read()
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must be less than 5MB"
        )
    
    # Reset file pointer
    await file.seek(0)
    
    # Create upload directory if it doesn't exist
    upload_dir = Path("uploads/profile_pictures")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_extension = Path(file.filename).suffix if file.filename else '.jpg'
    unique_filename = f"{current_user.id}_{uuid.uuid4().hex}{file_extension}"
    file_path = upload_dir / unique_filename
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Update user profile picture URL
        profile_picture_url = f"/uploads/profile_pictures/{unique_filename}"
        current_user.profile_picture = profile_picture_url
        
        # Update profile completeness
        current_user.is_profile_complete = _calculate_profile_completeness(current_user)
        
        db.add(current_user)
        db.commit()
        db.refresh(current_user)
        
        return {
            "message": "Profile picture uploaded successfully",
            "profile_picture_url": profile_picture_url
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


def _calculate_cuisine_score(user_preferences: str, match_preferences: str) -> float:
    """Calculate cuisine preference compatibility score"""
    if not user_preferences or not match_preferences:
        return 0

    user_cuisines = set(c.strip().lower() for c in user_preferences.split(","))
    match_cuisines = set(c.strip().lower() for c in match_preferences.split(","))
    common_cuisines = user_cuisines.intersection(match_cuisines)
    denominator = max(len(user_cuisines), len(match_cuisines))
    score = (len(common_cuisines) / denominator) * 30
    return score


def _calculate_location_score(user_location: str, match_location: str) -> float:
    """Calculate location compatibility score"""
    if not user_location or not match_location:
        return 0
    return 25 if user_location.lower() == match_location.lower() else 0


def _calculate_dietary_score(user_restrictions: str, match_restrictions: str) -> float:
    """Calculate dietary restrictions compatibility score"""
    if not user_restrictions or not match_restrictions:
        return 0
    return 25 if user_restrictions.lower() == match_restrictions.lower() else 0


def _calculate_success_rate_score(db: Session, user_id: int) -> float:
    """Calculate match success rate score"""
    user_matches = (
        db.query(Match)
        .filter(
            or_(Match.sender_id == user_id, Match.receiver_id == user_id),
            Match.status == MatchStatus.ACCEPTED,
        )
        .count()
    )
    total_matches = (
        db.query(Match)
        .filter(or_(Match.sender_id == user_id, Match.receiver_id == user_id))
        .count()
    )
    return (user_matches / total_matches) * 20 if total_matches > 0 else 0


def _get_matched_user_ids(db: Session, current_user_id: int) -> set:
    """Get set of user IDs that are already matched"""
    matched_users = (
        db.query(Match)
        .filter(
            or_(
                Match.sender_id == current_user_id, Match.receiver_id == current_user_id
            )
        )
        .all()
    )

    matched_ids = {current_user_id}
    for match in matched_users:
        matched_ids.add(match.sender_id)
        matched_ids.add(match.receiver_id)
    return matched_ids


@router.get("/potential-matches", response_model=List[UserSchema])
def get_potential_matches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 10,
) -> Any:
    """
    Get potential dinner matches for the current user.
    Returns users that:
    - Are not the current user
    - Have not been matched with (either sent or received)
    - Have active profiles
    - Are ranked by compatibility based on:
        - Cuisine preference overlap (30%)
        - Location proximity (25%)
        - Dietary restrictions compatibility (25%)
        - Match history success rate (20%)
    """
    if not current_user.profile:
        return []

    matched_user_ids = _get_matched_user_ids(db, current_user.id)

    # Query for potential matches with their profiles
    potential_matches = (
        db.query(User, Profile)
        .join(Profile)
        .filter(and_(User.is_active.is_(True), not_(User.id.in_(matched_user_ids))))
        .all()
    )

    # Calculate compatibility scores
    scored_matches = []
    for user, profile in potential_matches:
        score = sum(
            [
                _calculate_cuisine_score(
                    current_user.profile.cuisine_preferences,
                    profile.cuisine_preferences,
                ),
                _calculate_location_score(
                    current_user.profile.location, profile.location
                ),
                _calculate_dietary_score(
                    current_user.profile.dietary_restrictions,
                    profile.dietary_restrictions,
                ),
                _calculate_success_rate_score(db, user.id),
            ]
        )
        scored_matches.append((user, score))

    # Sort by compatibility score and paginate
    scored_matches.sort(key=lambda x: x[1], reverse=True)
    return [match[0] for match in scored_matches[skip : skip + limit]]


@router.get("/{user_id}", response_model=UserSchema)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.get("/uploads/{filename}")
async def get_uploaded_file(
    filename: str,
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    """Get uploaded file with authentication."""
    # Security: Only allow access to files that belong to the current user
    # Extract user_id from filename (format: {user_id}_{uuid}.{ext})
    try:
        file_user_id = int(filename.split('_')[0])
    except (ValueError, IndexError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Check if user owns the file
    if file_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    file_path = Path("uploads/profile_pictures") / filename
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    return FileResponse(file_path)


@router.get("/mutual-interests/{user_id}")
def get_mutual_interests(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[str]:
    """Get mutual interests between current user and specified user."""
    
    # Get the other user
    other_user = db.query(User).filter(User.id == user_id).first()
    if not other_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get interests for both users
    current_interests = set(current_user.interests or [])
    other_interests = set(other_user.interests or [])
    
    # Find mutual interests
    mutual = list(current_interests.intersection(other_interests))
    
    return mutual


@router.get("/match-percentage/{user_id}")
def get_match_percentage(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Calculate match percentage between current user and specified user."""
    
    # Get the other user
    other_user = db.query(User).filter(User.id == user_id).first()
    if not other_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Calculate compatibility using existing scoring functions
    scores = {
        "cuisine": _calculate_cuisine_score(
            current_user.profile.cuisine_preferences if current_user.profile else "",
            other_user.profile.cuisine_preferences if other_user.profile else ""
        ),
        "location": _calculate_location_score(
            current_user.location or "",
            other_user.location or ""
        ),
        "dietary": _calculate_dietary_score(
            current_user.profile.dietary_restrictions if current_user.profile else "",
            other_user.profile.dietary_restrictions if other_user.profile else ""
        ),
        "interests": _calculate_interests_compatibility(current_user.interests, other_user.interests),
        "values": _calculate_values_compatibility(current_user, other_user)
    }
    
    # Weighted average (following CLAUDE.md specification)
    weights = {
        "cuisine": 0.25,
        "location": 0.20,
        "dietary": 0.15,
        "interests": 0.25,  # Jaccard similarity from CLAUDE.md
        "values": 0.15
    }
    
    total_score = sum(scores[category] * weights[category] for category in scores)
    percentage = int(total_score * 100)
    
    return {
        "match_percentage": percentage,
        "breakdown": scores,
        "mutual_interests_count": len(list(set(current_user.interests or []).intersection(set(other_user.interests or [])))),
        "compatibility_rating": _get_compatibility_rating(percentage)
    }


def _calculate_interests_compatibility(interests1: List[str], interests2: List[str]) -> float:
    """Calculate Jaccard similarity for interests (as specified in CLAUDE.md)"""
    if not interests1 or not interests2:
        return 0.0
    
    set1 = set(interests1)
    set2 = set(interests2)
    
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    return intersection / union if union > 0 else 0.0


def _calculate_values_compatibility(user1: User, user2: User) -> float:
    """Calculate values compatibility based on user profiles"""
    # Simplified values compatibility based on available data
    score = 0.0
    
    # Age compatibility (closer ages = higher compatibility)
    if user1.date_of_birth and user2.date_of_birth:
        from datetime import date
        today = date.today()
        age1 = today.year - user1.date_of_birth.year - ((today.month, today.day) < (user1.date_of_birth.month, user1.date_of_birth.day))
        age2 = today.year - user2.date_of_birth.year - ((today.month, today.day) < (user2.date_of_birth.month, user2.date_of_birth.day))
        age_diff = abs(age1 - age2)
        
        if age_diff <= 2:
            score += 0.4
        elif age_diff <= 5:
            score += 0.3
        elif age_diff <= 8:
            score += 0.2
        else:
            score += 0.1
    
    # Gender preference compatibility (simplified)
    if user1.gender and user2.gender and user1.gender != user2.gender:
        score += 0.3  # Assume heterosexual preference for simplicity
    
    # Bio similarity (if both have bios)
    if user1.bio and user2.bio:
        # Simple word overlap check
        words1 = set(user1.bio.lower().split())
        words2 = set(user2.bio.lower().split())
        common_words = len(words1.intersection(words2))
        if common_words > 0:
            score += min(0.3, common_words * 0.05)
    
    return min(score, 1.0)


def _get_compatibility_rating(percentage: int) -> str:
    """Get compatibility rating label"""
    if percentage >= 90:
        return "Soulmate Match"
    elif percentage >= 80:
        return "Excellent Match"
    elif percentage >= 70:
        return "Great Match"
    elif percentage >= 60:
        return "Good Match"
    elif percentage >= 50:
        return "Fair Match"
    else:
        return "Low Compatibility"
