import logging
from typing import Any, Dict, List

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import User as UserSchema
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

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


def calculate_emotional_depth_score(data: OnboardingData) -> float:
    """
    Calculate emotional depth score based on onboarding responses.
    Score is between 0-100 based on response quality and depth.
    """
    score = 0.0

    # Check emotional response depth (30 points)
    if len(data.relationship_values) > 50:
        score += 10
    if len(data.ideal_evening) > 50:
        score += 10
    if len(data.feeling_understood) > 50:
        score += 10

    # Check core values completeness (20 points)
    if data.core_values and len(data.core_values) > 0:
        score += 20

    # Check personality traits (20 points)
    if data.personality_traits and len(data.personality_traits) > 0:
        score += 20

    # Check communication style (15 points)
    if data.communication_style and len(data.communication_style) > 0:
        score += 15

    # Check interests diversity (15 points)
    if data.interests and len(data.interests) >= 3:
        score += 15
    elif data.interests and len(data.interests) > 0:
        score += 10

    return min(score, 100.0)


@router.post("/complete", response_model=UserSchema)
def complete_onboarding(
    onboarding_data: OnboardingData,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Complete the emotional onboarding process and update user profile.
    """
    try:
        logger.info(f"Completing onboarding for user: {current_user.email}")

        # Update user with onboarding data
        current_user.emotional_onboarding_completed = True
        current_user.interests = onboarding_data.interests
        current_user.core_values = onboarding_data.core_values
        current_user.personality_traits = onboarding_data.personality_traits
        current_user.communication_style = onboarding_data.communication_style

        # Store emotional responses for matching algorithms
        current_user.emotional_responses = {
            "relationship_values": onboarding_data.relationship_values,
            "ideal_evening": onboarding_data.ideal_evening,
            "feeling_understood": onboarding_data.feeling_understood,
        }

        # Calculate initial emotional depth score (0-100)
        emotional_depth_score = calculate_emotional_depth_score(onboarding_data)
        current_user.emotional_depth_score = emotional_depth_score

        # Commit the changes
        db.commit()
        db.refresh(current_user)

        logger.info(f"Onboarding completed successfully for user: {current_user.email}")

        return current_user

    except Exception as e:
        logger.error(
            f"Error completing onboarding for user {current_user.email}: {str(e)}"
        )
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete onboarding: {str(e)}",
        )


@router.get("/status", response_model=dict)
def get_onboarding_status(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get the current onboarding status for the user.
    """
    return {
        "completed": current_user.emotional_onboarding_completed or False,
        "has_interests": bool(current_user.interests),
        "profile_complete": current_user.is_profile_complete or False,
    }


@router.options("/complete")
async def handle_onboarding_complete_options():
    """Handle OPTIONS requests for onboarding complete endpoint"""
    return {"message": "OK"}
