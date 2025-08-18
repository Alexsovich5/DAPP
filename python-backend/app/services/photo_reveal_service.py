"""
Photo Reveal Service - Phase 4 Soul Before Skin Core Logic
Comprehensive photo reveal timeline, consent management, and security
"""
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from pathlib import Path
import json

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import UploadFile, HTTPException

from app.models.user import User
from app.models.soul_connection import SoulConnection
from app.models.daily_revelation import DailyRevelation
from app.models.photo_reveal import (
    UserPhoto, PhotoRevealTimeline, PhotoRevealRequest, PhotoRevealPermission,
    PhotoRevealEvent, PhotoModerationLog, PhotoRevealStage, PhotoConsentType,
    PhotoPrivacyLevel
)
from app.services.analytics_service import analytics_service
from app.models.soul_analytics import AnalyticsEventType

logger = logging.getLogger(__name__)


@dataclass
class PhotoRevealStatus:
    """Current photo reveal status for a connection"""
    connection_id: int
    current_stage: PhotoRevealStage
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


@dataclass
class PhotoUploadResult:
    """Result of photo upload operation"""
    success: bool
    photo_id: Optional[int]
    photo_uuid: Optional[str]
    message: str
    requires_moderation: bool
    processing_status: str


@dataclass
class ConsentRequestResult:
    """Result of photo consent request"""
    success: bool
    request_id: Optional[int]
    status: str
    message: str
    expires_at: Optional[datetime]
    can_retry_at: Optional[datetime]


class PhotoRevealService:
    """Comprehensive photo reveal and consent management service"""
    
    def __init__(self):
        self.max_photos_per_user = 6
        self.supported_formats = ['jpg', 'jpeg', 'png', 'webp']
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.consent_request_expiry_hours = 48
        self.photo_storage_path = "/secure/photos"  # Encrypted storage
        
        logger.info("Photo Reveal Service initialized")
    
    async def create_photo_timeline(self, connection_id: int, db: Session) -> PhotoRevealTimeline:
        """Create photo reveal timeline for a new connection"""
        try:
            # Check if timeline already exists
            existing = db.query(PhotoRevealTimeline).filter(
                PhotoRevealTimeline.connection_id == connection_id
            ).first()
            
            if existing:
                return existing
            
            # Get connection details
            connection = db.query(SoulConnection).filter(
                SoulConnection.id == connection_id
            ).first()
            
            if not connection:
                raise ValueError(f"Connection {connection_id} not found")
            
            # Create new timeline
            timeline = PhotoRevealTimeline(
                connection_id=connection_id,
                connection_started_at=connection.created_at,
                revelation_cycle_days=7,
                min_revelations_required=5,
                current_stage=PhotoRevealStage.HIDDEN
            )
            
            # Calculate reveal eligibility date
            timeline.photo_reveal_eligible_at = (
                connection.created_at + timedelta(days=timeline.revelation_cycle_days)
            )
            
            db.add(timeline)
            db.commit()
            db.refresh(timeline)
            
            # Create initial event after timeline is committed
            initial_event = PhotoRevealEvent.create_event(
                timeline_id=timeline.id,
                connection_id=connection_id,
                event_type="timeline_created",
                description="Photo reveal timeline initiated"
            )
            db.add(initial_event)
            db.commit()
            
            logger.info(f"Created photo timeline for connection {connection_id}")
            return timeline
            
        except Exception as e:
            logger.error(f"Error creating photo timeline: {str(e)}")
            db.rollback()
            raise
    
    async def upload_user_photo(
        self, 
        user_id: int, 
        photo_file: UploadFile, 
        is_primary: bool,
        db: Session
    ) -> PhotoUploadResult:
        """Upload and process user photo with security and moderation"""
        try:
            # Validate file
            validation_result = self._validate_photo_file(photo_file)
            if not validation_result["valid"]:
                return PhotoUploadResult(
                    success=False,
                    photo_id=None,
                    photo_uuid=None,
                    message=validation_result["error"],
                    requires_moderation=False,
                    processing_status="validation_failed"
                )
            
            # Check user photo limits
            existing_photos = db.query(UserPhoto).filter(
                UserPhoto.user_id == user_id
            ).count()
            
            if existing_photos >= self.max_photos_per_user:
                return PhotoUploadResult(
                    success=False,
                    photo_id=None,
                    photo_uuid=None,
                    message=f"Maximum {self.max_photos_per_user} photos allowed",
                    requires_moderation=False,
                    processing_status="limit_exceeded"
                )
            
            # Generate secure storage details
            file_content = await photo_file.read()
            encryption_key = secrets.token_hex(32)
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # Create photo record
            photo = UserPhoto(
                user_id=user_id,
                original_filename=photo_file.filename,
                file_path=f"{self.photo_storage_path}/{user_id}/{file_hash}",
                file_size=len(file_content),
                mime_type=photo_file.content_type,
                is_profile_primary=is_primary,
                encryption_key_hash=hashlib.sha256(encryption_key.encode()).hexdigest(),
                privacy_level=PhotoPrivacyLevel.COMPLETELY_HIDDEN,  # Start hidden
                moderation_status="pending"
            )
            
            # If setting as primary, unset other primary photos
            if is_primary:
                db.query(UserPhoto).filter(
                    UserPhoto.user_id == user_id,
                    UserPhoto.is_profile_primary == True
                ).update({"is_profile_primary": False})
            
            db.add(photo)
            db.commit()
            db.refresh(photo)
            
            # Store encrypted file (would implement actual encrypted storage)
            await self._store_encrypted_photo(photo, file_content, encryption_key)
            
            # Queue for moderation
            moderation_required = await self._queue_photo_moderation(photo, db)
            
            # Generate preview versions
            await self._generate_photo_previews(photo)
            
            # Update processing status
            photo.blur_versions_generated = True
            photo.silhouette_generated = True
            photo.processing_complete = True
            db.commit()
            
            # Track analytics
            await analytics_service.track_user_event(
                user_id=user_id,
                event_type=AnalyticsEventType.PHOTO_UPLOAD,
                event_data={
                    "photo_id": photo.id,
                    "is_primary": is_primary,
                    "file_size": photo.file_size,
                    "requires_moderation": moderation_required
                },
                db=db
            )
            
            logger.info(f"Successfully uploaded photo for user {user_id}")
            
            return PhotoUploadResult(
                success=True,
                photo_id=photo.id,
                photo_uuid=str(photo.photo_uuid),
                message="Photo uploaded successfully",
                requires_moderation=moderation_required,
                processing_status="completed"
            )
            
        except Exception as e:
            logger.error(f"Error uploading photo: {str(e)}")
            db.rollback()
            return PhotoUploadResult(
                success=False,
                photo_id=None,
                photo_uuid=None,
                message=f"Upload failed: {str(e)}",
                requires_moderation=False,
                processing_status="failed"
            )
    
    async def get_photo_reveal_status(self, connection_id: int, db: Session) -> PhotoRevealStatus:
        """Get current photo reveal status for a connection"""
        try:
            # Get or create timeline
            timeline = await self._get_or_create_timeline(connection_id, db)
            
            # Get connection for user IDs
            connection = db.query(SoulConnection).filter(
                SoulConnection.id == connection_id
            ).first()
            
            if not connection:
                raise ValueError(f"Connection {connection_id} not found")
            
            # Update revelation count
            await self._update_revelation_count(timeline, db)
            
            # Update timeline status
            await self._update_timeline_status(timeline, db)
            
            # Check early reveal eligibility
            can_request_early = await self._can_request_early_reveal(timeline, connection, db)
            
            return PhotoRevealStatus(
                connection_id=connection_id,
                current_stage=timeline.current_stage,
                days_until_reveal=timeline.calculate_days_until_reveal(),
                revelations_completed=timeline.revelations_completed,
                min_revelations_required=timeline.min_revelations_required,
                progress_percentage=timeline.get_reveal_progress_percentage(),
                user1_consent_status=timeline.user1_consent_status,
                user2_consent_status=timeline.user2_consent_status,
                mutual_consent_achieved=timeline.mutual_consent_achieved,
                photos_revealed=timeline.photos_revealed,
                can_request_early_reveal=can_request_early,
                reveal_eligible=timeline.is_reveal_eligible()
            )
            
        except Exception as e:
            logger.error(f"Error getting photo reveal status: {str(e)}")
            raise
    
    async def request_photo_consent(
        self,
        connection_id: int,
        requester_id: int,
        request_type: PhotoConsentType,
        message: Optional[str] = None,
        emotional_context: Optional[Dict] = None,
        db: Session = None
    ) -> ConsentRequestResult:
        """Request photo reveal consent from connection partner"""
        try:
            # Get timeline and connection
            timeline = await self._get_or_create_timeline(connection_id, db)
            connection = db.query(SoulConnection).filter(
                SoulConnection.id == connection_id
            ).first()
            
            if not connection:
                raise ValueError(f"Connection {connection_id} not found")
            
            # Determine partner
            partner_id = connection.get_partner_id(requester_id)
            if not partner_id:
                raise ValueError("Invalid requester for this connection")
            
            # Check if request is allowed
            eligibility_check = await self._check_consent_request_eligibility(
                timeline, requester_id, request_type, db
            )
            
            if not eligibility_check["allowed"]:
                return ConsentRequestResult(
                    success=False,
                    request_id=None,
                    status="not_allowed",
                    message=eligibility_check["reason"],
                    expires_at=None,
                    can_retry_at=eligibility_check.get("retry_at")
                )
            
            # Get partner's primary photo
            partner_photo = db.query(UserPhoto).filter(
                UserPhoto.user_id == partner_id,
                UserPhoto.is_profile_primary == True
            ).first()
            
            if not partner_photo:
                return ConsentRequestResult(
                    success=False,
                    request_id=None,
                    status="no_photo",
                    message="Partner has no photos to reveal",
                    expires_at=None,
                    can_retry_at=None
                )
            
            # Create consent request
            expires_at = datetime.utcnow() + timedelta(hours=self.consent_request_expiry_hours)
            
            consent_request = PhotoRevealRequest(
                timeline_id=timeline.id,
                photo_id=partner_photo.id,
                requester_id=requester_id,
                photo_owner_id=partner_id,
                request_type=request_type,
                request_message=message,
                emotional_context=emotional_context or {},
                expires_at=expires_at,
                requested_privacy_level=PhotoPrivacyLevel.FULLY_REVEALED
            )
            
            db.add(consent_request)
            
            # Update timeline stage
            if timeline.current_stage == PhotoRevealStage.HIDDEN:
                timeline.current_stage = PhotoRevealStage.CONSENT_REQUESTED
            
            # Create event
            event = PhotoRevealEvent.create_event(
                timeline_id=timeline.id,
                connection_id=connection_id,
                event_type="consent_requested",
                user_id=requester_id,
                event_data={
                    "request_type": request_type.value,
                    "partner_id": partner_id,
                    "has_message": bool(message)
                },
                description=f"Photo reveal consent requested via {request_type.value}"
            )
            db.add(event)
            
            db.commit()
            db.refresh(consent_request)
            
            # Send real-time notification to partner
            await self._send_consent_request_notification(consent_request, db)
            
            # Track analytics
            await analytics_service.track_user_event(
                user_id=requester_id,
                event_type=AnalyticsEventType.PHOTO_CONSENT_REQUESTED,
                event_data={
                    "connection_id": connection_id,
                    "request_type": request_type.value,
                    "partner_id": partner_id
                },
                db=db,
                connection_id=connection_id
            )
            
            logger.info(f"Photo consent requested: user {requester_id} -> {partner_id}")
            
            return ConsentRequestResult(
                success=True,
                request_id=consent_request.id,
                status="pending",
                message="Consent request sent successfully",
                expires_at=expires_at,
                can_retry_at=None
            )
            
        except Exception as e:
            logger.error(f"Error requesting photo consent: {str(e)}")
            db.rollback()
            return ConsentRequestResult(
                success=False,
                request_id=None,
                status="error",
                message=f"Failed to send request: {str(e)}",
                expires_at=None,
                can_retry_at=None
            )
    
    async def respond_to_consent_request(
        self,
        request_id: int,
        user_id: int,
        approved: bool,
        response_message: Optional[str] = None,
        granted_privacy_level: Optional[PhotoPrivacyLevel] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Respond to a photo reveal consent request"""
        try:
            # Get consent request
            request = db.query(PhotoRevealRequest).filter(
                PhotoRevealRequest.id == request_id
            ).first()
            
            if not request:
                raise ValueError(f"Consent request {request_id} not found")
            
            # Verify user is the photo owner
            if request.photo_owner_id != user_id:
                raise ValueError("User not authorized to respond to this request")
            
            # Check if request can still be responded to
            if not request.can_be_approved():
                return {
                    "success": False,
                    "message": "Request has expired or already been responded to"
                }
            
            # Update request
            request.status = "approved" if approved else "declined"
            request.responded_at = datetime.utcnow()
            request.response_message = response_message
            
            if approved:
                request.granted_privacy_level = (
                    granted_privacy_level or PhotoPrivacyLevel.FULLY_REVEALED
                )
                
                # Create permission
                permission = PhotoRevealPermission(
                    photo_id=request.photo_id,
                    connection_id=request.timeline.connection_id,
                    viewer_id=request.requester_id,
                    photo_owner_id=user_id,
                    privacy_level=request.granted_privacy_level,
                    granted_through_request_id=request.id,
                    grant_method=request.request_type
                )
                db.add(permission)
                
                # Update timeline
                timeline = request.timeline
                if user_id == timeline.connection.user1_id:
                    timeline.user1_consent_status = "granted"
                else:
                    timeline.user2_consent_status = "granted"
                
                # Check for mutual consent
                await self._check_mutual_consent(timeline, db)
                
                # Create approval event
                event = PhotoRevealEvent.create_event(
                    timeline_id=timeline.id,
                    connection_id=timeline.connection_id,
                    event_type="consent_granted",
                    user_id=user_id,
                    event_data={
                        "requester_id": request.requester_id,
                        "privacy_level": request.granted_privacy_level.value
                    },
                    description="Photo reveal consent granted"
                )
                db.add(event)
                
                # Track analytics
                await analytics_service.track_user_event(
                    user_id=user_id,
                    event_type=AnalyticsEventType.PHOTO_CONSENT_GIVEN,
                    event_data={
                        "connection_id": timeline.connection_id,
                        "requester_id": request.requester_id,
                        "privacy_level": request.granted_privacy_level.value
                    },
                    db=db,
                    connection_id=timeline.connection_id
                )
                
            else:
                # Handle decline
                request.decline_reason = response_message
                
                # Update timeline status
                timeline = request.timeline
                if user_id == timeline.connection.user1_id:
                    timeline.user1_consent_status = "declined"
                else:
                    timeline.user2_consent_status = "declined"
                
                # Create decline event
                event = PhotoRevealEvent.create_event(
                    timeline_id=timeline.id,
                    connection_id=timeline.connection_id,
                    event_type="consent_declined",
                    user_id=user_id,
                    event_data={
                        "requester_id": request.requester_id,
                        "reason": response_message
                    },
                    description="Photo reveal consent declined"
                )
                db.add(event)
            
            db.commit()
            
            # Send notification to requester
            await self._send_consent_response_notification(request, approved, db)
            
            logger.info(f"Consent request {request_id} {'approved' if approved else 'declined'}")
            
            return {
                "success": True,
                "approved": approved,
                "message": "Response recorded successfully",
                "mutual_consent_achieved": request.timeline.mutual_consent_achieved if approved else False
            }
            
        except Exception as e:
            logger.error(f"Error responding to consent request: {str(e)}")
            db.rollback()
            return {
                "success": False,
                "message": f"Failed to respond: {str(e)}"
            }
    
    async def get_photo_with_permissions(
        self,
        photo_uuid: str,
        viewer_id: int,
        privacy_level: Optional[PhotoPrivacyLevel] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Get photo with appropriate privacy level based on permissions"""
        try:
            # Get photo
            photo = db.query(UserPhoto).filter(
                UserPhoto.photo_uuid == photo_uuid
            ).first()
            
            if not photo:
                raise ValueError("Photo not found")
            
            # Check if viewer has permission
            permission = db.query(PhotoRevealPermission).filter(
                PhotoRevealPermission.photo_id == photo.id,
                PhotoRevealPermission.viewer_id == viewer_id,
                PhotoRevealPermission.is_active == True
            ).first()
            
            # Determine allowed privacy level
            allowed_level = PhotoPrivacyLevel.COMPLETELY_HIDDEN
            if permission and permission.is_valid():
                allowed_level = permission.privacy_level
            elif photo.user_id == viewer_id:  # Owner can always see their own photo
                allowed_level = PhotoPrivacyLevel.FULLY_REVEALED
            
            # Use requested level if lower than allowed
            effective_level = privacy_level or allowed_level
            if self._privacy_level_value(effective_level) > self._privacy_level_value(allowed_level):
                effective_level = allowed_level
            
            # Record view if permission exists
            if permission:
                permission.record_view()
                db.commit()
            
            # Get appropriate photo URL
            photo_url = photo.get_reveal_url(effective_level, viewer_id)
            
            return {
                "success": True,
                "photo_url": photo_url,
                "privacy_level": effective_level.value,
                "can_view": photo_url is not None,
                "owner_id": photo.user_id,
                "upload_timestamp": photo.upload_timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting photo with permissions: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def process_automatic_reveals(self, db: Session) -> Dict[str, int]:
        """Process automatic photo reveals for eligible timelines"""
        try:
            # Get timelines eligible for automatic reveal
            eligible_timelines = db.query(PhotoRevealTimeline).filter(
                PhotoRevealTimeline.auto_reveal_enabled == True,
                PhotoRevealTimeline.photos_revealed == False,
                PhotoRevealTimeline.current_stage != PhotoRevealStage.DECLINED
            ).all()
            
            processed = 0
            revealed = 0
            
            for timeline in eligible_timelines:
                processed += 1
                
                # Check if eligible for reveal
                if timeline.is_reveal_eligible():
                    # Check if both users have photos
                    connection = timeline.connection
                    user1_photo = db.query(UserPhoto).filter(
                        UserPhoto.user_id == connection.user1_id,
                        UserPhoto.is_profile_primary == True
                    ).first()
                    
                    user2_photo = db.query(UserPhoto).filter(
                        UserPhoto.user_id == connection.user2_id,
                        UserPhoto.is_profile_primary == True
                    ).first()
                    
                    if user1_photo and user2_photo:
                        # Automatically grant mutual consent
                        await self._execute_automatic_reveal(timeline, db)
                        revealed += 1
                        
                        logger.info(f"Automatic photo reveal executed for connection {timeline.connection_id}")
            
            logger.info(f"Processed {processed} timelines, {revealed} automatic reveals executed")
            
            return {
                "processed": processed,
                "revealed": revealed,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error processing automatic reveals: {str(e)}")
            return {
                "processed": 0,
                "revealed": 0,
                "success": False,
                "error": str(e)
            }
    
    # Helper methods
    
    def _validate_photo_file(self, photo_file: UploadFile) -> Dict[str, Any]:
        """Validate uploaded photo file"""
        if not photo_file.filename:
            return {"valid": False, "error": "No file provided"}
        
        # Check file extension
        file_ext = photo_file.filename.lower().split('.')[-1]
        if file_ext not in self.supported_formats:
            return {
                "valid": False, 
                "error": f"Unsupported format. Allowed: {', '.join(self.supported_formats)}"
            }
        
        # Check file size (would need to read file size from headers or stream)
        # This is simplified - in production would check actual file size
        
        # Check MIME type
        if not photo_file.content_type.startswith('image/'):
            return {"valid": False, "error": "File must be an image"}
        
        return {"valid": True}
    
    async def _store_encrypted_photo(self, photo: UserPhoto, file_content: bytes, encryption_key: str):
        """Store photo with encryption (placeholder implementation)"""
        # In production, would implement actual encrypted file storage
        logger.info(f"Storing encrypted photo {photo.id} at {photo.file_path}")
    
    async def _queue_photo_moderation(self, photo: UserPhoto, db: Session) -> bool:
        """Queue photo for AI and/or manual moderation"""
        try:
            moderation_log = PhotoModerationLog(
                photo_id=photo.id,
                moderation_type="ai_scan",
                moderator_type="system",
                status="pending",
                ai_model_version="v1.0"
            )
            
            db.add(moderation_log)
            db.commit()
            
            # In production, would trigger actual AI moderation pipeline
            logger.info(f"Queued photo {photo.id} for moderation")
            return True
            
        except Exception as e:
            logger.error(f"Error queuing moderation: {str(e)}")
            return False
    
    async def _generate_photo_previews(self, photo: UserPhoto):
        """Generate blurred and silhouette versions"""
        # In production, would implement actual image processing
        logger.info(f"Generated preview versions for photo {photo.id}")
    
    async def _get_or_create_timeline(self, connection_id: int, db: Session) -> PhotoRevealTimeline:
        """Get existing timeline or create new one"""
        timeline = db.query(PhotoRevealTimeline).filter(
            PhotoRevealTimeline.connection_id == connection_id
        ).first()
        
        if not timeline:
            timeline = await self.create_photo_timeline(connection_id, db)
        
        return timeline
    
    async def _update_revelation_count(self, timeline: PhotoRevealTimeline, db: Session):
        """Update the revelation count for timeline"""
        revelation_count = db.query(DailyRevelation).filter(
            DailyRevelation.connection_id == timeline.connection_id
        ).count()
        
        timeline.revelations_completed = revelation_count
        timeline.days_until_reveal = timeline.calculate_days_until_reveal()
    
    async def _update_timeline_status(self, timeline: PhotoRevealTimeline, db: Session):
        """Update timeline current stage based on current state"""
        if timeline.photos_revealed:
            timeline.current_stage = PhotoRevealStage.REVEALED
        elif timeline.mutual_consent_achieved:
            timeline.current_stage = PhotoRevealStage.MUTUAL_CONSENT
        elif timeline.user1_consent_status == "declined" or timeline.user2_consent_status == "declined":
            timeline.current_stage = PhotoRevealStage.DECLINED
        
        db.commit()
    
    async def _can_request_early_reveal(self, timeline: PhotoRevealTimeline, connection: SoulConnection, db: Session) -> bool:
        """Check if early reveal request is allowed"""
        if not timeline.early_reveal_allowed:
            return False
        
        if timeline.photos_revealed:
            return False
        
        # Check if minimum revelations completed
        if timeline.revelations_completed < 3:  # Need at least 3 revelations for early request
            return False
        
        # Check recent request cooldown
        recent_request = db.query(PhotoRevealRequest).filter(
            PhotoRevealRequest.timeline_id == timeline.id,
            PhotoRevealRequest.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).first()
        
        return recent_request is None
    
    async def _check_consent_request_eligibility(
        self,
        timeline: PhotoRevealTimeline,
        requester_id: int,
        request_type: PhotoConsentType,
        db: Session
    ) -> Dict[str, Any]:
        """Check if consent request is eligible"""
        
        # Check if photos already revealed
        if timeline.photos_revealed:
            return {"allowed": False, "reason": "Photos already revealed"}
        
        # Check if user already has pending request
        pending_request = db.query(PhotoRevealRequest).filter(
            PhotoRevealRequest.timeline_id == timeline.id,
            PhotoRevealRequest.requester_id == requester_id,
            PhotoRevealRequest.status == "pending"
        ).first()
        
        if pending_request:
            return {"allowed": False, "reason": "Request already pending"}
        
        # Check request type specific rules
        if request_type == PhotoConsentType.TIMELINE_BASED:
            if not timeline.is_reveal_eligible():
                return {
                    "allowed": False, 
                    "reason": f"Timeline not yet eligible. {timeline.calculate_days_until_reveal()} days remaining"
                }
        
        elif request_type == PhotoConsentType.MANUAL_REQUEST:
            if timeline.revelations_completed < 3:
                return {
                    "allowed": False,
                    "reason": "Need at least 3 revelations for early request"
                }
        
        return {"allowed": True}
    
    async def _check_mutual_consent(self, timeline: PhotoRevealTimeline, db: Session):
        """Check and update mutual consent status"""
        if (timeline.user1_consent_status == "granted" and 
            timeline.user2_consent_status == "granted" and
            not timeline.mutual_consent_achieved):
            
            timeline.mutual_consent_achieved = True
            timeline.consent_achieved_at = datetime.utcnow()
            timeline.current_stage = PhotoRevealStage.MUTUAL_CONSENT
            
            # Execute photo reveal
            await self._execute_photo_reveal(timeline, db)
    
    async def _execute_photo_reveal(self, timeline: PhotoRevealTimeline, db: Session):
        """Execute actual photo reveal process"""
        try:
            # Create mutual permissions
            connection = timeline.connection
            
            # User1's photo to User2
            user1_photo = db.query(UserPhoto).filter(
                UserPhoto.user_id == connection.user1_id,
                UserPhoto.is_profile_primary == True
            ).first()
            
            # User2's photo to User1
            user2_photo = db.query(UserPhoto).filter(
                UserPhoto.user_id == connection.user2_id,
                UserPhoto.is_profile_primary == True
            ).first()
            
            if user1_photo:
                permission1 = PhotoRevealPermission(
                    photo_id=user1_photo.id,
                    connection_id=timeline.connection_id,
                    viewer_id=connection.user2_id,
                    photo_owner_id=connection.user1_id,
                    privacy_level=PhotoPrivacyLevel.FULLY_REVEALED,
                    grant_method=PhotoConsentType.MUTUAL_AGREEMENT
                )
                db.add(permission1)
            
            if user2_photo:
                permission2 = PhotoRevealPermission(
                    photo_id=user2_photo.id,
                    connection_id=timeline.connection_id,
                    viewer_id=connection.user1_id,
                    photo_owner_id=connection.user2_id,
                    privacy_level=PhotoPrivacyLevel.FULLY_REVEALED,
                    grant_method=PhotoConsentType.MUTUAL_AGREEMENT
                )
                db.add(permission2)
            
            # Update timeline
            timeline.photos_revealed = True
            timeline.photo_reveal_completed_at = datetime.utcnow()
            timeline.current_stage = PhotoRevealStage.REVEALED
            
            # Create reveal event
            event = PhotoRevealEvent.create_event(
                timeline_id=timeline.id,
                connection_id=timeline.connection_id,
                event_type="photos_revealed",
                event_data={
                    "reveal_method": "mutual_consent",
                    "user1_id": connection.user1_id,
                    "user2_id": connection.user2_id
                },
                description="Photos mutually revealed"
            )
            db.add(event)
            
            db.commit()
            
            # Send notifications
            await self._send_photo_reveal_notifications(timeline, db)
            
            logger.info(f"Photo reveal executed for connection {timeline.connection_id}")
            
        except Exception as e:
            logger.error(f"Error executing photo reveal: {str(e)}")
            db.rollback()
            raise
    
    async def _execute_automatic_reveal(self, timeline: PhotoRevealTimeline, db: Session):
        """Execute automatic reveal based on timeline completion"""
        # Automatically grant mutual consent
        timeline.user1_consent_status = "granted"
        timeline.user2_consent_status = "granted"
        timeline.mutual_consent_achieved = True
        timeline.consent_achieved_at = datetime.utcnow()
        timeline.reveal_method = PhotoConsentType.TIMELINE_BASED
        
        await self._execute_photo_reveal(timeline, db)
    
    def _privacy_level_value(self, level: PhotoPrivacyLevel) -> int:
        """Get numeric value for privacy level comparison"""
        values = {
            PhotoPrivacyLevel.COMPLETELY_HIDDEN: 0,
            PhotoPrivacyLevel.SILHOUETTE: 1,
            PhotoPrivacyLevel.HEAVILY_BLURRED: 2,
            PhotoPrivacyLevel.LIGHTLY_BLURRED: 3,
            PhotoPrivacyLevel.FULLY_REVEALED: 4
        }
        return values.get(level, 0)
    
    async def _send_consent_request_notification(self, request: PhotoRevealRequest, db: Session):
        """Send real-time notification for consent request"""
        # Would integrate with WebSocket/notification system
        logger.info(f"Notification sent for consent request {request.id}")
    
    async def _send_consent_response_notification(self, request: PhotoRevealRequest, approved: bool, db: Session):
        """Send notification for consent response"""
        logger.info(f"Notification sent for consent response {request.id}: {'approved' if approved else 'declined'}")
    
    async def _send_photo_reveal_notifications(self, timeline: PhotoRevealTimeline, db: Session):
        """Send notifications for completed photo reveal"""
        logger.info(f"Photo reveal notifications sent for connection {timeline.connection_id}")


# Global service instance
photo_reveal_service = PhotoRevealService()