from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import User as UserSchema
from app.api.v1.deps import get_current_user
from pydantic import BaseModel
from typing import Optional, List, Dict

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["onboarding"])


class OnboardingData(BaseModel):
    relationship_values: str
    ideal_evening: str
    feeling_understood: str
    core_values: Dict
    personality_traits: Dict
    communication_style: Dict
    interests: List[str]


@router.post("/complete", response_model=UserSchema)
def complete_onboarding(
    onboarding_data: OnboardingData,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Complete the emotional onboarding process and update user profile.
    """
    try:
        logger.info(f"Completing onboarding for user: {current_user.email}")
        
        # Update user with onboarding data
        current_user.emotional_onboarding_completed = True
        current_user.interests = onboarding_data.interests
        
        # Store additional emotional data as JSON (you might want to create separate tables for this)
        # For now, we'll store it in existing fields or you can add new JSON fields to the user model
        
        # Commit the changes
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"Onboarding completed successfully for user: {current_user.email}")
        
        return current_user
        
    except Exception as e:
        logger.error(f"Error completing onboarding for user {current_user.email}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete onboarding: {str(e)}"
        )


@router.get("/status", response_model=dict)
def get_onboarding_status(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get the current onboarding status for the user.
    """
    return {
        "completed": current_user.emotional_onboarding_completed or False,
        "has_interests": bool(current_user.interests),
        "profile_complete": current_user.is_profile_complete or False
    }


@router.options("/complete")
async def handle_onboarding_complete_options():
    """Handle OPTIONS requests for onboarding complete endpoint"""
    return {"message": "OK"}