"""
Photo Reveal API Router - Phase 4 Soul Before Skin Photo Management
Complete API endpoints for photo upload, consent, timeline, and reveal management
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.photo_reveal import PhotoRevealStage, PhotoConsentType, PhotoPrivacyLevel
from app.services.photo_reveal_service import photo_reveal_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["photo_reveal"])


# Pydantic models for request/response

class PhotoUploadResponse(BaseModel):
    success: bool
    photo_id: Optional[int]
    photo_uuid: Optional[str]
    message: str
    requires_moderation: bool
    processing_status: str


class PhotoRevealStatusResponse(BaseModel):
    connection_id: int
    current_stage: str
    days_until_reveal: int
    revelations_completed: int
    min_revelations_required: int
    progress_percentage: float
    user1_consent_status: str
    user2_consent_status: str
    mutual_consent_achieved: bool
    photos_revealed: bool
    can_request_early_reveal: bool
    reveal_eligible: bool


class ConsentRequestData(BaseModel):
    connection_id: int
    request_type: str  # timeline_based, manual_request, mutual_agreement
    message: Optional[str] = None
    emotional_context: Optional[Dict[str, Any]] = None


class ConsentResponseData(BaseModel):
    approved: bool
    response_message: Optional[str] = None
    granted_privacy_level: Optional[str] = None  # fully_revealed, lightly_blurred, etc.


class PhotoAccessResponse(BaseModel):
    success: bool
    photo_url: Optional[str]
    privacy_level: str
    can_view: bool
    owner_id: int
    upload_timestamp: str


# Photo upload endpoints

@router.post("/upload", response_model=PhotoUploadResponse)
async def upload_photo(
    file: UploadFile = File(...),
    is_primary: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a new user photo with automatic processing and moderation
    """
    try:
        result = await photo_reveal_service.upload_user_photo(
            user_id=current_user.id,
            photo_file=file,
            is_primary=is_primary,
            db=db
        )
        
        return PhotoUploadResponse(**result.__dict__)
        
    except Exception as e:
        logger.error(f"Error in photo upload endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Photo upload failed: {str(e)}"
        )


@router.get("/my-photos")
async def get_my_photos(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's uploaded photos with metadata"""
    try:
        from app.models.photo_reveal import UserPhoto
        
        photos = db.query(UserPhoto).filter(
            UserPhoto.user_id == current_user.id
        ).order_by(UserPhoto.created_at.desc()).all()
        
        photo_list = []
        for photo in photos:
            photo_data = {
                "id": photo.id,
                "photo_uuid": str(photo.photo_uuid),
                "original_filename": photo.original_filename,
                "file_size": photo.file_size,
                "is_profile_primary": photo.is_profile_primary,
                "privacy_level": photo.privacy_level.value,
                "moderation_status": photo.moderation_status,
                "processing_complete": photo.processing_complete,
                "total_reveals": photo.total_reveals,
                "upload_timestamp": photo.upload_timestamp.isoformat(),
                "photo_url": photo.get_reveal_url(PhotoPrivacyLevel.FULLY_REVEALED, current_user.id)
            }
            photo_list.append(photo_data)
        
        return {
            "success": True,
            "photos": photo_list,
            "total_photos": len(photo_list),
            "max_allowed": photo_reveal_service.max_photos_per_user
        }
        
    except Exception as e:
        logger.error(f"Error getting user photos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve photos"
        )


# Photo reveal timeline endpoints

@router.get("/timeline/{connection_id}", response_model=PhotoRevealStatusResponse)
async def get_photo_reveal_status(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get photo reveal timeline status for a specific connection
    """
    try:
        # Verify user is part of this connection
        from app.models.soul_connection import SoulConnection
        
        connection = db.query(SoulConnection).filter(
            SoulConnection.id == connection_id,
            ((SoulConnection.user1_id == current_user.id) | 
             (SoulConnection.user2_id == current_user.id))
        ).first()
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found or access denied"
            )
        
        status_result = await photo_reveal_service.get_photo_reveal_status(
            connection_id=connection_id,
            db=db
        )
        
        return PhotoRevealStatusResponse(
            connection_id=status_result.connection_id,
            current_stage=status_result.current_stage.value,
            days_until_reveal=status_result.days_until_reveal,
            revelations_completed=status_result.revelations_completed,
            min_revelations_required=status_result.min_revelations_required,
            progress_percentage=status_result.progress_percentage,
            user1_consent_status=status_result.user1_consent_status,
            user2_consent_status=status_result.user2_consent_status,
            mutual_consent_achieved=status_result.mutual_consent_achieved,
            photos_revealed=status_result.photos_revealed,
            can_request_early_reveal=status_result.can_request_early_reveal,
            reveal_eligible=status_result.reveal_eligible
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting photo reveal status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get reveal status"
        )


@router.get("/timeline/{connection_id}/events")
async def get_reveal_timeline_events(
    connection_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get photo reveal timeline events for a connection"""
    try:
        # Verify access
        from app.models.soul_connection import SoulConnection
        from app.models.photo_reveal import PhotoRevealEvent
        
        connection = db.query(SoulConnection).filter(
            SoulConnection.id == connection_id,
            ((SoulConnection.user1_id == current_user.id) | 
             (SoulConnection.user2_id == current_user.id))
        ).first()
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found or access denied"
            )
        
        events = db.query(PhotoRevealEvent).filter(
            PhotoRevealEvent.connection_id == connection_id
        ).order_by(PhotoRevealEvent.created_at.desc()).limit(limit).all()
        
        event_list = []
        for event in events:
            event_data = {
                "id": event.id,
                "event_type": event.event_type,
                "user_id": event.user_id,
                "event_description": event.event_description,
                "system_generated": event.system_generated,
                "revelation_day": event.revelation_day,
                "emotional_state": event.emotional_state,
                "connection_energy_level": event.connection_energy_level,
                "days_since_connection": event.days_since_connection,
                "created_at": event.created_at.isoformat(),
                "event_data": event.event_data
            }
            event_list.append(event_data)
        
        return {
            "success": True,
            "events": event_list,
            "connection_id": connection_id,
            "total_events": len(event_list)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting timeline events: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get timeline events"
        )


# Photo consent endpoints

@router.post("/consent/request")
async def request_photo_consent(
    request_data: ConsentRequestData,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Request photo reveal consent from connection partner
    """
    try:
        # Validate request type
        try:
            consent_type = PhotoConsentType(request_data.request_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid request type: {request_data.request_type}"
            )
        
        # Verify user is part of connection
        from app.models.soul_connection import SoulConnection
        
        connection = db.query(SoulConnection).filter(
            SoulConnection.id == request_data.connection_id,
            ((SoulConnection.user1_id == current_user.id) | 
             (SoulConnection.user2_id == current_user.id))
        ).first()
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found or access denied"
            )
        
        result = await photo_reveal_service.request_photo_consent(
            connection_id=request_data.connection_id,
            requester_id=current_user.id,
            request_type=consent_type,
            message=request_data.message,
            emotional_context=request_data.emotional_context,
            db=db
        )
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )
        
        return {
            "success": result.success,
            "request_id": result.request_id,
            "status": result.status,
            "message": result.message,
            "expires_at": result.expires_at.isoformat() if result.expires_at else None,
            "can_retry_at": result.can_retry_at.isoformat() if result.can_retry_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error requesting photo consent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to request consent"
        )


@router.post("/consent/respond/{request_id}")
async def respond_to_consent_request(
    request_id: int,
    response_data: ConsentResponseData,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Respond to a photo reveal consent request
    """
    try:
        # Validate privacy level if provided
        granted_privacy_level = None
        if response_data.granted_privacy_level:
            try:
                granted_privacy_level = PhotoPrivacyLevel(response_data.granted_privacy_level)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid privacy level: {response_data.granted_privacy_level}"
                )
        
        result = await photo_reveal_service.respond_to_consent_request(
            request_id=request_id,
            user_id=current_user.id,
            approved=response_data.approved,
            response_message=response_data.response_message,
            granted_privacy_level=granted_privacy_level,
            db=db
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error responding to consent request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to respond to consent request"
        )


@router.get("/consent/pending")
async def get_pending_consent_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get pending photo consent requests for current user"""
    try:
        from app.models.photo_reveal import PhotoRevealRequest
        
        # Get requests where user is the photo owner
        pending_requests = db.query(PhotoRevealRequest).filter(
            PhotoRevealRequest.photo_owner_id == current_user.id,
            PhotoRevealRequest.status == "pending"
        ).order_by(PhotoRevealRequest.created_at.desc()).all()
        
        request_list = []
        for request in pending_requests:
            request_data = {
                "id": request.id,
                "connection_id": request.timeline.connection_id,
                "requester_id": request.requester_id,
                "requester_name": f"{request.requester.first_name} {request.requester.last_name}",
                "request_type": request.request_type.value,
                "request_message": request.request_message,
                "emotional_context": request.emotional_context,
                "requested_at": request.requested_at.isoformat(),
                "expires_at": request.expires_at.isoformat() if request.expires_at else None,
                "is_expired": request.is_expired(),
                "can_be_approved": request.can_be_approved(),
                "requested_privacy_level": request.requested_privacy_level.value
            }
            request_list.append(request_data)
        
        return {
            "success": True,
            "pending_requests": request_list,
            "total_pending": len(request_list)
        }
        
    except Exception as e:
        logger.error(f"Error getting pending requests: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get pending requests"
        )


# Photo access endpoints

@router.get("/view/{photo_uuid}", response_model=PhotoAccessResponse)
async def get_photo_with_privacy(
    photo_uuid: str,
    privacy_level: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get photo with appropriate privacy level based on permissions
    """
    try:
        # Validate privacy level if provided
        requested_privacy_level = None
        if privacy_level:
            try:
                requested_privacy_level = PhotoPrivacyLevel(privacy_level)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid privacy level: {privacy_level}"
                )
        
        result = await photo_reveal_service.get_photo_with_permissions(
            photo_uuid=photo_uuid,
            viewer_id=current_user.id,
            privacy_level=requested_privacy_level,
            db=db
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("error", "Photo not found")
            )
        
        return PhotoAccessResponse(
            success=result["success"],
            photo_url=result["photo_url"],
            privacy_level=result["privacy_level"],
            can_view=result["can_view"],
            owner_id=result["owner_id"],
            upload_timestamp=result["upload_timestamp"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting photo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve photo"
        )


@router.get("/permissions/active")
async def get_active_photo_permissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get active photo viewing permissions for current user"""
    try:
        from app.models.photo_reveal import PhotoRevealPermission
        
        permissions = db.query(PhotoRevealPermission).filter(
            PhotoRevealPermission.viewer_id == current_user.id,
            PhotoRevealPermission.is_active == True
        ).all()
        
        permission_list = []
        for permission in permissions:
            if permission.is_valid():
                permission_data = {
                    "id": permission.id,
                    "photo_id": permission.photo_id,
                    "photo_uuid": str(permission.photo.photo_uuid),
                    "connection_id": permission.connection_id,
                    "photo_owner_id": permission.photo_owner_id,
                    "photo_owner_name": f"{permission.photo_owner.first_name} {permission.photo_owner.last_name}",
                    "privacy_level": permission.privacy_level.value,
                    "granted_at": permission.granted_at.isoformat(),
                    "expires_at": permission.expires_at.isoformat() if permission.expires_at else None,
                    "total_views": permission.total_views,
                    "last_viewed_at": permission.last_viewed_at.isoformat() if permission.last_viewed_at else None,
                    "grant_method": permission.grant_method.value
                }
                permission_list.append(permission_data)
        
        return {
            "success": True,
            "permissions": permission_list,
            "total_permissions": len(permission_list)
        }
        
    except Exception as e:
        logger.error(f"Error getting permissions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get permissions"
        )


# Admin/system endpoints

@router.post("/admin/process-automatic-reveals")
async def process_automatic_reveals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process automatic photo reveals for eligible timelines
    (Admin endpoint - would have proper admin authentication in production)
    """
    try:
        # In production, would check admin permissions
        
        result = await photo_reveal_service.process_automatic_reveals(db)
        
        return {
            "success": result["success"],
            "processed_timelines": result["processed"],
            "automatic_reveals_executed": result["revealed"],
            "error": result.get("error"),
            "processed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing automatic reveals: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process automatic reveals"
        )


@router.get("/admin/timeline-stats")
async def get_photo_reveal_statistics(
    days: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get photo reveal system statistics"""
    try:
        from app.models.photo_reveal import PhotoRevealTimeline, PhotoRevealRequest, UserPhoto
        from sqlalchemy import func
        
        # In production, would check admin permissions
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Timeline stats
        total_timelines = db.query(PhotoRevealTimeline).count()
        active_timelines = db.query(PhotoRevealTimeline).filter(
            PhotoRevealTimeline.photos_revealed == False,
            PhotoRevealTimeline.current_stage != PhotoRevealStage.DECLINED
        ).count()
        
        completed_reveals = db.query(PhotoRevealTimeline).filter(
            PhotoRevealTimeline.photos_revealed == True,
            PhotoRevealTimeline.photo_reveal_completed_at >= cutoff_date
        ).count()
        
        # Request stats
        total_requests = db.query(PhotoRevealRequest).filter(
            PhotoRevealRequest.created_at >= cutoff_date
        ).count()
        
        approved_requests = db.query(PhotoRevealRequest).filter(
            PhotoRevealRequest.created_at >= cutoff_date,
            PhotoRevealRequest.status == "approved"
        ).count()
        
        # Photo stats
        total_photos = db.query(UserPhoto).count()
        photos_uploaded_recently = db.query(UserPhoto).filter(
            UserPhoto.upload_timestamp >= cutoff_date
        ).count()
        
        # Calculate rates
        approval_rate = (approved_requests / max(1, total_requests)) * 100
        reveal_completion_rate = (completed_reveals / max(1, active_timelines + completed_reveals)) * 100
        
        return {
            "success": True,
            "period_days": days,
            "timeline_stats": {
                "total_timelines": total_timelines,
                "active_timelines": active_timelines,
                "completed_reveals": completed_reveals,
                "reveal_completion_rate": round(reveal_completion_rate, 1)
            },
            "request_stats": {
                "total_requests": total_requests,
                "approved_requests": approved_requests,
                "approval_rate": round(approval_rate, 1)
            },
            "photo_stats": {
                "total_photos": total_photos,
                "recent_uploads": photos_uploaded_recently
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting reveal statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get statistics"
        )