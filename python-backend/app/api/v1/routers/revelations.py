from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.soul_connection import SoulConnection
from app.models.daily_revelation import DailyRevelation, RevelationType
from app.schemas.daily_revelation import (
    DailyRevelationCreate,
    DailyRevelationResponse,
    DailyRevelationUpdate,
    RevelationTimelineResponse,
    RevelationPrompt
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["revelations"])

# Revelation prompts for the 7-day cycle
REVELATION_PROMPTS = {
    1: {
        "revelation_type": RevelationType.PERSONAL_VALUE,
        "prompt_text": "Share a personal value that's important to you in relationships",
        "example_response": "I deeply value loyalty and trust. Once someone enters my life, I believe in being completely honest and dependable with them."
    },
    2: {
        "revelation_type": RevelationType.MEANINGFUL_EXPERIENCE,
        "prompt_text": "Describe a meaningful experience that shaped who you are today",
        "example_response": "Traveling alone to a new country taught me that I'm more resilient than I thought and that genuine connections can happen anywhere."
    },
    3: {
        "revelation_type": RevelationType.HOPE_OR_DREAM,
        "prompt_text": "Share a hope or dream that excites you about the future",
        "example_response": "I dream of creating a home filled with warmth and laughter, where friends feel welcomed and love is the foundation."
    },
    4: {
        "revelation_type": RevelationType.WHAT_MAKES_LAUGH,
        "prompt_text": "Describe what makes you laugh and brings joy to your everyday life",
        "example_response": "I find joy in silly moments - dancing in the kitchen while cooking, random conversations with strangers, and those unexpected moments of perfect timing."
    },
    5: {
        "revelation_type": RevelationType.CHALLENGE_OVERCOME,
        "prompt_text": "Share a challenge you've overcome and what it taught you",
        "example_response": "Learning to set boundaries taught me that saying 'no' to some things means saying 'yes' to what truly matters to me."
    },
    6: {
        "revelation_type": RevelationType.IDEAL_CONNECTION,
        "prompt_text": "Describe your ideal way to connect with someone special",
        "example_response": "I love deep conversations over coffee that stretch for hours, where time disappears and we discover unexpected common ground."
    },
    7: {
        "revelation_type": RevelationType.PHOTO_REVEAL,
        "prompt_text": "If you feel a connection, this is the day to share your photo and see each other",
        "example_response": "After sharing our souls this week, I'm excited to put a face to the amazing person I've been getting to know."
    }
}


@router.get("/prompts", response_model=List[RevelationPrompt])
def get_revelation_prompts():
    """
    Get all revelation prompts for the 7-day cycle.
    """
    return [
        RevelationPrompt(
            day_number=day,
            revelation_type=prompt["revelation_type"],
            prompt_text=prompt["prompt_text"],
            example_response=prompt["example_response"]
        )
        for day, prompt in REVELATION_PROMPTS.items()
    ]


@router.get("/prompts/{day_number}", response_model=RevelationPrompt)
def get_revelation_prompt(day_number: int):
    """
    Get revelation prompt for a specific day.
    """
    if day_number not in REVELATION_PROMPTS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid day number. Must be between 1 and 7."
        )
    
    prompt = REVELATION_PROMPTS[day_number]
    return RevelationPrompt(
        day_number=day_number,
        revelation_type=prompt["revelation_type"],
        prompt_text=prompt["prompt_text"],
        example_response=prompt["example_response"]
    )


@router.post("/create", response_model=DailyRevelationResponse)
def create_revelation(
    revelation_data: DailyRevelationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new daily revelation for a soul connection.
    """
    try:
        # Verify connection exists and user is part of it
        connection = db.query(SoulConnection).filter(
            SoulConnection.id == revelation_data.connection_id,
            ((SoulConnection.user1_id == current_user.id) | (SoulConnection.user2_id == current_user.id)),
            SoulConnection.status == "active"
        ).first()
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Soul connection not found or you don't have access"
            )
        
        # Verify day number is valid and sequential
        if revelation_data.day_number < 1 or revelation_data.day_number > 7:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Day number must be between 1 and 7"
            )
        
        # Check if revelation for this day already exists from this user
        existing_revelation = db.query(DailyRevelation).filter(
            DailyRevelation.connection_id == revelation_data.connection_id,
            DailyRevelation.sender_id == current_user.id,
            DailyRevelation.day_number == revelation_data.day_number
        ).first()
        
        if existing_revelation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already shared a revelation for this day"
            )
        
        # Create new revelation
        new_revelation = DailyRevelation(
            connection_id=revelation_data.connection_id,
            sender_id=current_user.id,
            day_number=revelation_data.day_number,
            revelation_type=revelation_data.revelation_type,
            content=revelation_data.content
        )
        
        db.add(new_revelation)
        db.commit()
        db.refresh(new_revelation)
        
        # Update connection stage if needed
        if revelation_data.day_number == 7 and revelation_data.revelation_type == RevelationType.PHOTO_REVEAL:
            connection.connection_stage = "photo_reveal"
            db.commit()
        
        logger.info(f"New revelation created: User {current_user.id}, Connection {revelation_data.connection_id}, Day {revelation_data.day_number}")
        
        # Return with sender name
        response = DailyRevelationResponse.from_orm(new_revelation)
        response.sender_name = current_user.first_name
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating revelation: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating revelation"
        )


@router.get("/timeline/{connection_id}", response_model=RevelationTimelineResponse)
def get_revelation_timeline(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the complete revelation timeline for a soul connection.
    """
    try:
        # Verify connection exists and user has access
        connection = db.query(SoulConnection).filter(
            SoulConnection.id == connection_id,
            ((SoulConnection.user1_id == current_user.id) | (SoulConnection.user2_id == current_user.id)),
            SoulConnection.status == "active"
        ).first()
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Soul connection not found or you don't have access"
            )
        
        # Get all revelations for this connection
        revelations = db.query(DailyRevelation).filter(
            DailyRevelation.connection_id == connection_id
        ).order_by(DailyRevelation.day_number, DailyRevelation.created_at).all()
        
        # Get user names for display
        user1 = db.query(User).filter(User.id == connection.user1_id).first()
        user2 = db.query(User).filter(User.id == connection.user2_id).first()
        
        # Enhance revelations with sender names
        enhanced_revelations = []
        for rev in revelations:
            rev_response = DailyRevelationResponse.from_orm(rev)
            if rev.sender_id == connection.user1_id:
                rev_response.sender_name = user1.first_name if user1 else "Unknown"
            else:
                rev_response.sender_name = user2.first_name if user2 else "Unknown"
            enhanced_revelations.append(rev_response)
        
        # Determine current day and next revelation type
        current_day = connection.reveal_day
        next_revelation_type = None
        if current_day <= 7:
            next_revelation_type = REVELATION_PROMPTS.get(current_day, {}).get("revelation_type")
        
        is_cycle_complete = current_day > 7 or all(
            any(r.day_number == day and r.sender_id == uid for r in revelations)
            for day in range(1, 8)
            for uid in [connection.user1_id, connection.user2_id]
        )
        
        return RevelationTimelineResponse(
            connection_id=connection_id,
            current_day=current_day,
            revelations=enhanced_revelations,
            next_revelation_type=next_revelation_type,
            is_cycle_complete=is_cycle_complete
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting revelation timeline: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving revelation timeline"
        )


@router.put("/{revelation_id}", response_model=DailyRevelationResponse)
def update_revelation(
    revelation_id: int,
    update_data: DailyRevelationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a revelation (mark as read, edit content if sender).
    """
    try:
        revelation = db.query(DailyRevelation).filter(
            DailyRevelation.id == revelation_id
        ).first()
        
        if not revelation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Revelation not found"
            )
        
        # Verify user has access to this revelation's connection
        connection = db.query(SoulConnection).filter(
            SoulConnection.id == revelation.connection_id,
            ((SoulConnection.user1_id == current_user.id) | (SoulConnection.user2_id == current_user.id))
        ).first()
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this revelation"
            )
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        
        # Only sender can edit content
        if "content" in update_dict and revelation.sender_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the sender can edit revelation content"
            )
        
        for field, value in update_dict.items():
            setattr(revelation, field, value)
        
        db.commit()
        db.refresh(revelation)
        
        logger.info(f"Revelation updated: {revelation_id}")
        return revelation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating revelation: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating revelation"
        )