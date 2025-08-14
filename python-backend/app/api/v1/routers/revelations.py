from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
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


@router.get("/timeline/{connection_id}")
def get_revelation_timeline(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the complete revelation timeline for a soul connection.
    Enhanced for Phase 3 frontend integration.
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
        
        # Get partner info
        partner_id = connection.get_partner_id(current_user.id)
        partner = db.query(User).filter(User.id == partner_id).first()
        partner_name = partner.first_name if partner else "Partner"
        
        # Build timeline data structure matching Phase 3 frontend
        timeline_days = []
        for day in range(1, 8):
            user_revelation = next((r for r in revelations if r.day_number == day and r.sender_id == current_user.id), None)
            partner_revelation = next((r for r in revelations if r.day_number == day and r.sender_id == partner_id), None)
            
            prompt = REVELATION_PROMPTS.get(day, {})
            
            timeline_days.append({
                "day": day,
                "prompt": prompt.get("prompt_text", ""),
                "description": prompt.get("example_response", ""),
                "isUnlocked": day <= connection.reveal_day,
                "userShared": user_revelation is not None,
                "partnerShared": partner_revelation is not None,
                "userContent": user_revelation.content if user_revelation else None,
                "partnerContent": partner_revelation.content if partner_revelation else None,
                "userSharedAt": user_revelation.created_at.isoformat() if user_revelation else None,
                "partnerSharedAt": partner_revelation.created_at.isoformat() if partner_revelation else None
            })
        
        # Calculate progress metrics
        user_shared_count = len([r for r in revelations if r.sender_id == current_user.id])
        partner_shared_count = len([r for r in revelations if r.sender_id == partner_id])
        mutual_days = len(set(r.day_number for r in revelations if r.sender_id == current_user.id) & 
                         set(r.day_number for r in revelations if r.sender_id == partner_id))
        
        completion_percentage = ((user_shared_count + partner_shared_count) / 14.0) * 100
        
        # Determine visualization phase
        if connection.reveal_day <= 3:
            phase = "soul_discovery"
        elif connection.reveal_day <= 6:
            phase = "deeper_connection"
        else:
            phase = "photo_reveal"
        
        return {
            "connectionId": connection_id,
            "currentDay": connection.reveal_day,
            "completionPercentage": completion_percentage,
            "timeline": timeline_days,
            "progress": {
                "daysUnlocked": connection.reveal_day,
                "userSharedCount": user_shared_count,
                "partnerSharedCount": partner_shared_count,
                "mutualDays": mutual_days,
                "nextUnlockDay": connection.reveal_day + 1 if connection.reveal_day < 7 else None
            },
            "visualization": {
                "completionRing": completion_percentage,
                "phase": phase
            }
        }
        
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


# Phase 4 Enhanced Endpoints for Frontend Integration

@router.post("/share/{connection_id}")
def share_revelation(
    connection_id: int,
    revelation_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Share a revelation for today's prompt. Enhanced for Phase 3 frontend.
    """
    try:
        # Verify connection and get current day
        connection = db.query(SoulConnection).filter(
            SoulConnection.id == connection_id,
            ((SoulConnection.user1_id == current_user.id) | (SoulConnection.user2_id == current_user.id)),
            SoulConnection.status == "active"
        ).first()
        
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        current_day = connection.reveal_day
        
        # Check if already shared today
        existing = db.query(DailyRevelation).filter(
            DailyRevelation.connection_id == connection_id,
            DailyRevelation.sender_id == current_user.id,
            DailyRevelation.day_number == current_day
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Already shared today")
        
        # Get revelation type for current day
        prompt = REVELATION_PROMPTS.get(current_day)
        if not prompt:
            raise HTTPException(status_code=400, detail="Invalid day")
        
        # Create revelation
        revelation = DailyRevelation(
            connection_id=connection_id,
            sender_id=current_user.id,
            day_number=current_day,
            revelation_type=prompt["revelation_type"],
            content=revelation_data.get("content", "")
        )
        
        db.add(revelation)
        
        # Update user's revelation count if field exists
        if hasattr(current_user, 'total_revelations_shared'):
            current_user.total_revelations_shared += 1
        
        # Update connection progress  
        if hasattr(connection, 'last_activity_at'):
            connection.last_activity_at = datetime.utcnow()
        if current_day == 7:
            if hasattr(connection, 'connection_stage'):
                connection.connection_stage = "photo_reveal"
        
        db.commit()
        
        return {
            "success": True,
            "message": "Revelation shared successfully",
            "dayNumber": current_day,
            "sharedAt": revelation.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sharing revelation: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error sharing revelation")


@router.get("/today/{connection_id}")
def get_today_prompt(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get today's revelation prompt and sharing status.
    """
    try:
        connection = db.query(SoulConnection).filter(
            SoulConnection.id == connection_id,
            ((SoulConnection.user1_id == current_user.id) | (SoulConnection.user2_id == current_user.id)),
            SoulConnection.status == "active"
        ).first()
        
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        current_day = connection.reveal_day
        prompt = REVELATION_PROMPTS.get(current_day)
        
        if not prompt:
            return {
                "dayNumber": current_day,
                "isComplete": True,
                "message": "All revelations complete! Ready for photo reveal."
            }
        
        # Check sharing status
        user_shared = db.query(DailyRevelation).filter(
            DailyRevelation.connection_id == connection_id,
            DailyRevelation.sender_id == current_user.id,
            DailyRevelation.day_number == current_day
        ).first() is not None
        
        partner_id = connection.get_partner_id(current_user.id)
        partner_shared = db.query(DailyRevelation).filter(
            DailyRevelation.connection_id == connection_id,
            DailyRevelation.sender_id == partner_id,
            DailyRevelation.day_number == current_day
        ).first() is not None
        
        return {
            "dayNumber": current_day,
            "prompt": prompt["prompt_text"],
            "description": prompt["example_response"],
            "revelationType": prompt["revelation_type"],
            "userShared": user_shared,
            "partnerShared": partner_shared,
            "canShare": not user_shared,
            "isPhotoDay": current_day == 7
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting today's prompt: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting today's prompt")


@router.post("/photo-consent/{connection_id}")
def give_photo_consent(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Give consent for photo reveal.
    """
    try:
        connection = db.query(SoulConnection).filter(
            SoulConnection.id == connection_id,
            ((SoulConnection.user1_id == current_user.id) | (SoulConnection.user2_id == current_user.id)),
            SoulConnection.status == "active"
        ).first()
        
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        # Update consent based on which user is giving it
        if hasattr(connection, 'user1_photo_consent') and hasattr(connection, 'user2_photo_consent'):
            if connection.user1_id == current_user.id:
                connection.user1_photo_consent = True
            else:
                connection.user2_photo_consent = True
        
        # Update user's global photo sharing consent if field exists
        if hasattr(current_user, 'photo_sharing_consent'):
            current_user.photo_sharing_consent = True
        
        # Check if both have consented
        mutual_consent = False
        if hasattr(connection, 'has_mutual_photo_consent'):
            mutual_consent = connection.has_mutual_photo_consent()
        elif hasattr(connection, 'user1_photo_consent') and hasattr(connection, 'user2_photo_consent'):
            mutual_consent = connection.user1_photo_consent and connection.user2_photo_consent
        
        if mutual_consent:
            if hasattr(connection, 'photo_revealed_at'):
                connection.photo_revealed_at = datetime.utcnow()
            if hasattr(connection, 'connection_stage'):
                connection.connection_stage = "dinner_planning"
        
        db.commit()
        
        return {
            "success": True,
            "mutualConsent": mutual_consent,
            "photoRevealed": mutual_consent,
            "message": "Photos revealed!" if mutual_consent else "Waiting for partner's consent"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error giving photo consent: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error giving photo consent")


@router.get("/analytics/{connection_id}")
def get_revelation_analytics(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get analytics about revelation sharing patterns.
    """
    try:
        from app.models.soul_analytics import SoulConnectionAnalytics
        
        connection = db.query(SoulConnection).filter(
            SoulConnection.id == connection_id,
            ((SoulConnection.user1_id == current_user.id) | (SoulConnection.user2_id == current_user.id))
        ).first()
        
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        # Get or create analytics
        analytics = db.query(SoulConnectionAnalytics).filter(
            SoulConnectionAnalytics.connection_id == connection_id
        ).first()
        
        if not analytics:
            # Calculate basic analytics
            revelations = db.query(DailyRevelation).filter(
                DailyRevelation.connection_id == connection_id
            ).all()
            
            total_revelations = len(revelations)
            completion_rate = (total_revelations / 14.0) * 100
            
            analytics_data = {
                "connectionId": connection_id,
                "revelationCompletionRate": completion_rate,
                "totalRevelationsShared": total_revelations,
                "mutualEngagementScore": connection.mutual_engagement_score or 0,
                "compatibilityScore": connection.compatibility_score or 0,
                "daysActive": connection.get_days_active(),
                "isRecentlyActive": connection.is_recently_active()
            }
        else:
            analytics_data = {
                "connectionId": connection_id,
                "revelationCompletionRate": analytics.revelation_completion_rate or 0,
                "mutualEngagementScore": analytics.mutual_engagement_score or 0,
                "conversationDepthScore": analytics.conversation_depth_score or 0,
                "successPredictionScore": analytics.success_prediction_score or 0
            }
        
        return analytics_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting revelation analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting analytics")