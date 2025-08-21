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


@router.post("/create", response_model=DailyRevelationResponse, status_code=status.HTTP_201_CREATED)
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
            ((SoulConnection.user1_id == current_user.id) | (SoulConnection.user2_id == current_user.id))
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
    consent_data: Dict[str, Any] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Give consent for photo reveal with enhanced mutual consent workflow.
    """
    try:
        connection = db.query(SoulConnection).filter(
            SoulConnection.id == connection_id,
            ((SoulConnection.user1_id == current_user.id) | (SoulConnection.user2_id == current_user.id)),
            SoulConnection.status == "active"
        ).first()
        
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        # Import revelation service for validation
        from app.services.revelation_service import RevelationService
        revelation_service = RevelationService(db)
        
        # Check photo reveal eligibility before allowing consent
        eligibility = revelation_service.check_photo_reveal_eligibility(db, connection_id)
        if not eligibility["eligible"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Not eligible for photo reveal: {eligibility['reason']}"
            )
        
        # Get consent details from request data
        consent_given = consent_data.get("consent", True) if consent_data else True
        consent_message = consent_data.get("message", "") if consent_data else ""
        
        # Update consent based on which user is giving it
        user_consent_field = "user1_photo_consent" if connection.user1_id == current_user.id else "user2_photo_consent"
        user_consent_status_field = "user1_consent_status" if connection.user1_id == current_user.id else "user2_consent_status"
        
        if hasattr(connection, user_consent_field):
            setattr(connection, user_consent_field, consent_given)
        
        # Update consent status in photo timeline if exists
        from app.models.photo_reveal import PhotoRevealTimeline
        timeline = db.query(PhotoRevealTimeline).filter(
            PhotoRevealTimeline.connection_id == connection_id
        ).first()
        
        if timeline:
            if connection.user1_id == current_user.id:
                timeline.user1_consent_status = "granted" if consent_given else "declined"
            else:
                timeline.user2_consent_status = "granted" if consent_given else "declined"
        
        # Update user's global photo sharing consent if field exists
        if hasattr(current_user, 'photo_sharing_consent'):
            current_user.photo_sharing_consent = consent_given
        
        # Check if both have consented
        mutual_consent = False
        if hasattr(connection, 'has_mutual_photo_consent'):
            mutual_consent = connection.has_mutual_photo_consent()
        elif hasattr(connection, 'user1_photo_consent') and hasattr(connection, 'user2_photo_consent'):
            mutual_consent = connection.user1_photo_consent and connection.user2_photo_consent
        
        # Update timeline mutual consent status
        if timeline and mutual_consent:
            timeline.mutual_consent_achieved = True
            timeline.consent_achieved_at = datetime.utcnow()
            
            # Update connection stage progression
            if hasattr(connection, 'photo_revealed_at'):
                connection.photo_revealed_at = datetime.utcnow()
            if hasattr(connection, 'connection_stage'):
                connection.connection_stage = "dinner_planning"
                
            # Update timeline tracking
            revelation_service.update_connection_timeline(db, connection_id, "photo_reveal_consented")
        
        # Record consent event for analytics
        from app.models.photo_reveal import PhotoRevealEvent
        if timeline:
            consent_event = PhotoRevealEvent.create_event(
                timeline_id=timeline.id,
                connection_id=connection_id,
                event_type="consent_given" if consent_given else "consent_declined",
                user_id=current_user.id,
                event_data={
                    "consent_type": "timeline_based",
                    "has_message": bool(consent_message),
                    "partner_id": connection.get_partner_id(current_user.id)
                },
                description=f"Photo reveal consent {'granted' if consent_given else 'declined'}"
            )
            db.add(consent_event)
        
        db.commit()
        
        # Get updated status
        partner_id = connection.get_partner_id(current_user.id)
        partner_consent = False
        if hasattr(connection, 'user1_photo_consent') and hasattr(connection, 'user2_photo_consent'):
            partner_consent = (
                connection.user2_photo_consent if connection.user1_id == current_user.id 
                else connection.user1_photo_consent
            )
        
        response_data = {
            "success": True,
            "userConsent": consent_given,
            "partnerConsent": partner_consent,
            "mutualConsent": mutual_consent,
            "photoRevealed": mutual_consent,
            "connectionStage": getattr(connection, 'connection_stage', 'photo_reveal'),
            "message": (
                "Photos revealed! You can now see each other." if mutual_consent 
                else "Consent recorded. Waiting for partner's consent." if consent_given
                else "Photo reveal consent declined."
            )
        }
        
        # Add timeline data if available
        if timeline:
            response_data["timeline"] = {
                "daysUntilReveal": timeline.calculate_days_until_reveal(),
                "revelationsCompleted": timeline.revelations_completed,
                "progressPercentage": timeline.get_reveal_progress_percentage(),
                "consentAchievedAt": timeline.consent_achieved_at.isoformat() if timeline.consent_achieved_at else None
            }
        
        return response_data
        
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


@router.get("/streak/{connection_id}")
def get_revelation_streak(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get revelation sharing streak for a specific connection.
    """
    try:
        # Verify connection access
        connection = db.query(SoulConnection).filter(
            SoulConnection.id == connection_id,
            ((SoulConnection.user1_id == current_user.id) | (SoulConnection.user2_id == current_user.id))
        ).first()
        
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        # Import revelation service
        from app.services.revelation_service import RevelationService
        revelation_service = RevelationService(db)
        
        # Calculate streak data
        streak_data = revelation_service.calculate_revelation_streak(db, current_user.id, connection_id)
        
        # Get partner streak for comparison
        partner_id = connection.get_partner_id(current_user.id)
        partner_streak_data = revelation_service.calculate_revelation_streak(db, partner_id, connection_id)
        
        return {
            "connectionId": connection_id,
            "userStreak": streak_data,
            "partnerStreak": partner_streak_data,
            "mutualStreak": min(streak_data["current_streak"], partner_streak_data["current_streak"]),
            "streakComparison": {
                "userLongest": streak_data["longest_streak"],
                "partnerLongest": partner_streak_data["longest_streak"],
                "bothConsistent": streak_data["current_streak"] > 0 and partner_streak_data["current_streak"] > 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting revelation streak: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting streak data")


@router.get("/global-streak")
def get_global_revelation_streak(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's global revelation streak across all connections.
    """
    try:
        from app.services.revelation_service import RevelationService
        revelation_service = RevelationService(db)
        
        # Get global streak data
        global_streak = revelation_service.get_global_revelation_streak(db, current_user.id)
        
        # Get individual connection streaks for detailed view
        connections = db.query(SoulConnection).filter(
            (SoulConnection.user1_id == current_user.id) | (SoulConnection.user2_id == current_user.id)
        ).all()
        
        connection_streaks = []
        for connection in connections:
            streak_data = revelation_service.calculate_revelation_streak(db, current_user.id, connection.id)
            
            # Get partner info
            partner_id = connection.get_partner_id(current_user.id)
            partner = db.query(User).filter(User.id == partner_id).first()
            
            connection_streaks.append({
                "connectionId": connection.id,
                "partnerName": partner.first_name if partner else "Unknown",
                "currentStreak": streak_data["current_streak"],
                "longestStreak": streak_data["longest_streak"],
                "totalDays": streak_data["total_days"],
                "streakPercentage": streak_data["streak_percentage"]
            })
        
        return {
            "globalStats": global_streak,
            "connectionBreakdown": connection_streaks,
            "achievements": {
                "consistentSharer": global_streak["longest_overall_streak"] >= 5,
                "perfectWeek": global_streak["longest_overall_streak"] >= 7,
                "multiConnection": global_streak["total_connections_with_streaks"] > 1
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting global revelation streak: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting global streak data")


@router.get("/reminder-check/{connection_id}")
def check_revelation_reminder_needed(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if revelation reminders are needed for a connection.
    Used by background task scheduler.
    """
    try:
        # Verify connection access
        connection = db.query(SoulConnection).filter(
            SoulConnection.id == connection_id,
            ((SoulConnection.user1_id == current_user.id) | (SoulConnection.user2_id == current_user.id))
        ).first()
        
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        from app.services.revelation_service import RevelationService
        revelation_service = RevelationService(db)
        
        reminder_data = revelation_service.check_revelation_reminder_eligibility(db, connection_id)
        
        return {
            "connectionId": connection_id,
            **reminder_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking reminder eligibility: {str(e)}")
        raise HTTPException(status_code=500, detail="Error checking reminder eligibility")


@router.post("/scheduler/start")
async def start_revelation_scheduler(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start the revelation reminder scheduler (admin only).
    """
    try:
        # Check if user has admin privileges (simplified check)
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        from app.services.revelation_scheduler import get_revelation_scheduler
        scheduler = get_revelation_scheduler()
        
        if scheduler.is_running:
            return {"success": False, "message": "Scheduler already running"}
        
        # Start scheduler in background
        import asyncio
        asyncio.create_task(scheduler.start_scheduler())
        
        return {
            "success": True,
            "message": "Revelation scheduler started",
            "status": scheduler.get_scheduler_status()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting revelation scheduler: {str(e)}")
        raise HTTPException(status_code=500, detail="Error starting scheduler")


@router.post("/scheduler/stop")
async def stop_revelation_scheduler(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Stop the revelation reminder scheduler (admin only).
    """
    try:
        # Check if user has admin privileges (simplified check)
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        from app.services.revelation_scheduler import get_revelation_scheduler
        scheduler = get_revelation_scheduler()
        
        await scheduler.stop_scheduler()
        
        return {
            "success": True,
            "message": "Revelation scheduler stopped",
            "status": scheduler.get_scheduler_status()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping revelation scheduler: {str(e)}")
        raise HTTPException(status_code=500, detail="Error stopping scheduler")


@router.get("/scheduler/status")
def get_scheduler_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get revelation scheduler status.
    """
    try:
        from app.services.revelation_scheduler import get_revelation_scheduler
        scheduler = get_revelation_scheduler()
        
        return {
            "schedulerStatus": scheduler.get_scheduler_status(),
            "features": {
                "dailyReminders": True,
                "streakMaintenance": True,
                "pushNotifications": True
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting scheduler status")


@router.post("/scheduler/trigger-reminders")
async def trigger_daily_reminders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manually trigger daily revelation reminders (admin only).
    """
    try:
        # Check if user has admin privileges
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        from app.services.revelation_scheduler import get_revelation_scheduler
        scheduler = get_revelation_scheduler()
        
        result = await scheduler.trigger_daily_reminders(db)
        
        return {
            "triggerResult": result,
            "message": "Daily reminders triggered manually"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering daily reminders: {str(e)}")
        raise HTTPException(status_code=500, detail="Error triggering daily reminders")


@router.post("/scheduler/trigger-streak-maintenance")
async def trigger_streak_maintenance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manually trigger streak maintenance (admin only).
    """
    try:
        # Check if user has admin privileges
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        from app.services.revelation_scheduler import get_revelation_scheduler
        scheduler = get_revelation_scheduler()
        
        result = await scheduler.trigger_streak_maintenance(db)
        
        return {
            "triggerResult": result,
            "message": "Streak maintenance triggered manually"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering streak maintenance: {str(e)}")
        raise HTTPException(status_code=500, detail="Error triggering streak maintenance")


@router.get("/progress/{connection_id}")
def get_revelation_progress(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed revelation progress with timeline visualization data.
    """
    try:
        # Verify connection access
        connection = db.query(SoulConnection).filter(
            SoulConnection.id == connection_id,
            ((SoulConnection.user1_id == current_user.id) | (SoulConnection.user2_id == current_user.id))
        ).first()
        
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        from app.services.revelation_service import RevelationService
        revelation_service = RevelationService(db)
        
        # Calculate comprehensive progress data
        progress_data = revelation_service.calculate_revelation_progress(db, connection_id)
        
        if "error" in progress_data:
            raise HTTPException(status_code=500, detail=progress_data["error"])
        
        return {
            "success": True,
            "progressData": progress_data,
            "lastUpdated": connection.updated_at.isoformat() if connection.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting revelation progress: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting progress data")


@router.post("/timeline/update/{connection_id}")
def update_connection_timeline(
    connection_id: int,
    stage_update: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update connection timeline with stage progression.
    """
    try:
        # Verify connection access
        connection = db.query(SoulConnection).filter(
            SoulConnection.id == connection_id,
            ((SoulConnection.user1_id == current_user.id) | (SoulConnection.user2_id == current_user.id))
        ).first()
        
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        from app.services.revelation_service import RevelationService
        revelation_service = RevelationService(db)
        
        # Update timeline
        result = revelation_service.update_connection_timeline(db, connection_id, stage_update)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to update timeline"))
        
        return {
            "success": True,
            "timelineUpdate": result,
            "message": f"Timeline updated: {stage_update}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating connection timeline: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating timeline")


@router.post("/advance-day/{connection_id}")
def advance_revelation_day(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manually advance revelation day (admin only for testing).
    """
    try:
        # Check if user has admin privileges
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Verify connection access
        connection = db.query(SoulConnection).filter(
            SoulConnection.id == connection_id,
            ((SoulConnection.user1_id == current_user.id) | (SoulConnection.user2_id == current_user.id))
        ).first()
        
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        from app.services.revelation_service import RevelationService
        revelation_service = RevelationService(db)
        
        # Advance day
        result = revelation_service.advance_revelation_day(db, connection_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to advance day"))
        
        return {
            "success": True,
            "dayAdvancement": result,
            "message": result.get("message", "Day advanced successfully")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error advancing revelation day: {str(e)}")
        raise HTTPException(status_code=500, detail="Error advancing revelation day")


@router.get("/insights/{connection_id}")
def get_revelation_insights(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized insights about revelation progress and quality.
    """
    try:
        # Verify connection access
        connection = db.query(SoulConnection).filter(
            SoulConnection.id == connection_id,
            ((SoulConnection.user1_id == current_user.id) | (SoulConnection.user2_id == current_user.id))
        ).first()
        
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        from app.services.revelation_service import RevelationService
        revelation_service = RevelationService(db)
        
        # Get progress data which includes insights
        progress_data = revelation_service.calculate_revelation_progress(db, connection_id)
        
        if "error" in progress_data:
            raise HTTPException(status_code=500, detail=progress_data["error"])
        
        # Extract and enhance insights
        insights = progress_data.get("insights", [])
        statistics = progress_data.get("statistics", {})
        quality_metrics = progress_data.get("quality_metrics", {})
        
        # Generate actionable recommendations
        recommendations = []
        
        if statistics.get("mutual_completion_percentage", 0) < 50:
            recommendations.append({
                "type": "engagement",
                "title": "Boost Mutual Sharing",
                "description": "Encourage your partner to share more by being vulnerable first",
                "action": "Share a deeper revelation today"
            })
        
        if quality_metrics.get("average_length", 0) < 50:
            recommendations.append({
                "type": "depth",
                "title": "Add More Detail",
                "description": "Share more context and emotion in your revelations",
                "action": "Write at least 100 characters in your next revelation"
            })
        
        if quality_metrics.get("consistency", 0) < 0.7:
            recommendations.append({
                "type": "consistency",
                "title": "Stay Consistent",
                "description": "Regular sharing builds stronger emotional bonds",
                "action": "Set a daily reminder to share your revelation"
            })
        
        return {
            "connectionId": connection_id,
            "insights": insights,
            "statistics": statistics,
            "qualityMetrics": quality_metrics,
            "recommendations": recommendations,
            "connectionHealth": {
                "score": round((statistics.get("mutual_completion_percentage", 0) + quality_metrics.get("emotional_depth", 0) * 100) / 2, 1),
                "status": "excellent" if statistics.get("mutual_completion_percentage", 0) >= 80 else "good" if statistics.get("mutual_completion_percentage", 0) >= 60 else "developing"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting revelation insights: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting insights")


@router.get("/photo-consent/status/{connection_id}")
def get_photo_consent_status(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed photo consent status for mutual consent workflow.
    """
    try:
        # Verify connection access
        connection = db.query(SoulConnection).filter(
            SoulConnection.id == connection_id,
            ((SoulConnection.user1_id == current_user.id) | (SoulConnection.user2_id == current_user.id))
        ).first()
        
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        # Get photo timeline if exists
        from app.models.photo_reveal import PhotoRevealTimeline
        timeline = db.query(PhotoRevealTimeline).filter(
            PhotoRevealTimeline.connection_id == connection_id
        ).first()
        
        # Check photo reveal eligibility
        from app.services.revelation_service import RevelationService
        revelation_service = RevelationService(db)
        eligibility = revelation_service.check_photo_reveal_eligibility(db, connection_id)
        
        # Get partner info
        partner_id = connection.get_partner_id(current_user.id)
        partner = db.query(User).filter(User.id == partner_id).first()
        
        # Build consent status
        user_consent = False
        partner_consent = False
        
        if hasattr(connection, 'user1_photo_consent') and hasattr(connection, 'user2_photo_consent'):
            if connection.user1_id == current_user.id:
                user_consent = connection.user1_photo_consent
                partner_consent = connection.user2_photo_consent
            else:
                user_consent = connection.user2_photo_consent
                partner_consent = connection.user1_photo_consent
        
        # Get timeline consent status
        timeline_consent = {}
        if timeline:
            timeline_consent = {
                "user1Status": timeline.user1_consent_status,
                "user2Status": timeline.user2_consent_status,
                "mutualConsentAchieved": timeline.mutual_consent_achieved,
                "consentAchievedAt": timeline.consent_achieved_at.isoformat() if timeline.consent_achieved_at else None,
                "photosRevealed": timeline.photos_revealed,
                "photoRevealCompletedAt": timeline.photo_reveal_completed_at.isoformat() if timeline.photo_reveal_completed_at else None
            }
        
        return {
            "connectionId": connection_id,
            "eligibility": eligibility,
            "consent": {
                "userConsent": user_consent,
                "partnerConsent": partner_consent,
                "mutualConsent": user_consent and partner_consent,
                "canGiveConsent": eligibility["eligible"] and not user_consent,
                "waitingForPartner": user_consent and not partner_consent
            },
            "timeline": timeline_consent,
            "partner": {
                "id": partner_id,
                "name": partner.first_name if partner else "Unknown"
            },
            "connectionStage": getattr(connection, 'connection_stage', 'revelation_phase'),
            "photoRevealedAt": connection.photo_revealed_at.isoformat() if hasattr(connection, 'photo_revealed_at') and connection.photo_revealed_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting photo consent status: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting consent status")


@router.post("/photo-consent/withdraw/{connection_id}")
def withdraw_photo_consent(
    connection_id: int,
    withdrawal_data: Dict[str, Any] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Withdraw photo reveal consent with proper mutual consent handling.
    """
    try:
        # Verify connection access
        connection = db.query(SoulConnection).filter(
            SoulConnection.id == connection_id,
            ((SoulConnection.user1_id == current_user.id) | (SoulConnection.user2_id == current_user.id))
        ).first()
        
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        # Get withdrawal reason
        withdrawal_reason = withdrawal_data.get("reason", "") if withdrawal_data else ""
        
        # Update consent status
        if hasattr(connection, 'user1_photo_consent') and hasattr(connection, 'user2_photo_consent'):
            if connection.user1_id == current_user.id:
                connection.user1_photo_consent = False
            else:
                connection.user2_photo_consent = False
        
        # Update timeline consent status
        from app.models.photo_reveal import PhotoRevealTimeline
        timeline = db.query(PhotoRevealTimeline).filter(
            PhotoRevealTimeline.connection_id == connection_id
        ).first()
        
        if timeline:
            if connection.user1_id == current_user.id:
                timeline.user1_consent_status = "withdrawn"
            else:
                timeline.user2_consent_status = "withdrawn"
            
            # Reset mutual consent if it was previously achieved
            if timeline.mutual_consent_achieved:
                timeline.mutual_consent_achieved = False
                timeline.consent_achieved_at = None
                
                # Revoke photo permissions if photos were revealed
                if timeline.photos_revealed:
                    from app.models.photo_reveal import PhotoRevealPermission
                    permissions = db.query(PhotoRevealPermission).filter(
                        PhotoRevealPermission.connection_id == connection_id,
                        PhotoRevealPermission.is_active == True
                    ).all()
                    
                    for permission in permissions:
                        permission.is_active = False
                        permission.revoked_at = datetime.utcnow()
                    
                    timeline.photos_revealed = False
                    timeline.photo_reveal_completed_at = None
                    
                    # Update connection stage back to revelation phase
                    if hasattr(connection, 'connection_stage'):
                        connection.connection_stage = "revelation_phase"
        
        # Record withdrawal event
        if timeline:
            from app.models.photo_reveal import PhotoRevealEvent
            withdrawal_event = PhotoRevealEvent.create_event(
                timeline_id=timeline.id,
                connection_id=connection_id,
                event_type="consent_withdrawn",
                user_id=current_user.id,
                event_data={
                    "reason": withdrawal_reason,
                    "partner_id": connection.get_partner_id(current_user.id),
                    "previous_mutual_consent": timeline.mutual_consent_achieved
                },
                description="Photo reveal consent withdrawn"
            )
            db.add(withdrawal_event)
        
        db.commit()
        
        return {
            "success": True,
            "message": "Photo consent withdrawn successfully",
            "mutualConsentRevoked": True,
            "photosHidden": True,
            "connectionStage": getattr(connection, 'connection_stage', 'revelation_phase'),
            "canReConsent": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error withdrawing photo consent: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error withdrawing consent")


@router.get("/photo-consent/timeline/{connection_id}")
def get_photo_consent_timeline(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed photo consent timeline and history.
    """
    try:
        # Verify connection access
        connection = db.query(SoulConnection).filter(
            SoulConnection.id == connection_id,
            ((SoulConnection.user1_id == current_user.id) | (SoulConnection.user2_id == current_user.id))
        ).first()
        
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        # Get photo timeline
        from app.models.photo_reveal import PhotoRevealTimeline, PhotoRevealEvent
        timeline = db.query(PhotoRevealTimeline).filter(
            PhotoRevealTimeline.connection_id == connection_id
        ).first()
        
        if not timeline:
            return {
                "connectionId": connection_id,
                "timelineExists": False,
                "message": "Photo timeline not yet created"
            }
        
        # Get consent events
        consent_events = db.query(PhotoRevealEvent).filter(
            PhotoRevealEvent.timeline_id == timeline.id,
            PhotoRevealEvent.event_type.in_([
                "consent_requested", "consent_given", "consent_declined", 
                "consent_withdrawn", "photos_revealed"
            ])
        ).order_by(PhotoRevealEvent.created_at.asc()).all()
        
        # Build timeline data
        timeline_data = {
            "connectionId": connection_id,
            "timelineExists": True,
            "currentStage": timeline.current_stage.value,
            "daysUntilReveal": timeline.calculate_days_until_reveal(),
            "revelationsCompleted": timeline.revelations_completed,
            "minRevelationsRequired": timeline.min_revelations_required,
            "progressPercentage": timeline.get_reveal_progress_percentage(),
            "eligibleForReveal": timeline.is_reveal_eligible(),
            "consentStatus": {
                "user1Status": timeline.user1_consent_status,
                "user2Status": timeline.user2_consent_status,
                "mutualConsentAchieved": timeline.mutual_consent_achieved,
                "consentAchievedAt": timeline.consent_achieved_at.isoformat() if timeline.consent_achieved_at else None
            },
            "photoReveal": {
                "photosRevealed": timeline.photos_revealed,
                "photoRevealCompletedAt": timeline.photo_reveal_completed_at.isoformat() if timeline.photo_reveal_completed_at else None,
                "revealMethod": timeline.reveal_method.value if timeline.reveal_method else None
            },
            "events": []
        }
        
        # Add consent events to timeline
        for event in consent_events:
            user = db.query(User).filter(User.id == event.user_id).first() if event.user_id else None
            
            timeline_data["events"].append({
                "eventType": event.event_type,
                "eventDescription": event.event_description,
                "userId": event.user_id,
                "userName": user.first_name if user else "System",
                "eventData": event.event_data,
                "createdAt": event.created_at.isoformat(),
                "systemGenerated": event.system_generated
            })
        
        return timeline_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting photo consent timeline: {str(e)}")
        raise HTTPException(status_code=500, detail="Error getting consent timeline")