# Privacy and GDPR Compliance API Endpoints
# RESTful API for privacy management and data subject rights

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import logging

from app.core.security import get_current_user
from app.services.privacy_compliance import (
    PrivacyComplianceService, DataCategory, DataSubjectRight, 
    ProcessingPurpose, PrivacyRequest
)
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic models for API requests/responses

class ConsentRequest(BaseModel):
    categories: List[str] = Field(..., description="List of consent categories")
    
class ConsentWithdrawalRequest(BaseModel):
    data_category: str = Field(..., description="Data category to withdraw consent for")
    processing_purpose: str = Field(..., description="Processing purpose to withdraw consent for")

class DataSubjectRightsRequest(BaseModel):
    request_type: str = Field(..., description="Type of data subject right request")
    data_categories: List[str] = Field(default=[], description="Specific data categories (optional)")
    notes: str = Field(default="", description="Additional notes or details")

class RectificationRequest(BaseModel):
    field_name: str = Field(..., description="Field to be corrected")
    current_value: str = Field(..., description="Current incorrect value")
    correct_value: str = Field(..., description="Correct value")
    reason: str = Field(..., description="Reason for correction")

class PrivacyPreferencesUpdate(BaseModel):
    marketing_emails: Optional[bool] = None
    push_notifications: Optional[bool] = None
    location_sharing: Optional[bool] = None
    analytics_participation: Optional[bool] = None
    data_sharing_research: Optional[bool] = None

# Dependency to get privacy service
async def get_privacy_service() -> PrivacyComplianceService:
    # In production, this would be injected properly
    from app.core.database import get_database
    from app.core.redis import get_redis
    from app.services.storage import get_storage_service
    
    return PrivacyComplianceService(
        database=get_database(),
        redis_client=get_redis(),
        storage_service=get_storage_service()
    )

@router.post("/consent", response_model=Dict)
async def grant_consent(
    request: ConsentRequest,
    current_user: User = Depends(get_current_user),
    privacy_service: PrivacyComplianceService = Depends(get_privacy_service)
):
    """
    Grant consent for specific data processing activities
    """
    try:
        result = await privacy_service.collect_user_consent(
            user_id=current_user.id,
            consent_categories=request.categories
        )
        
        return {
            "success": True,
            "message": "Consent preferences updated successfully",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error updating consent for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update consent preferences")

@router.delete("/consent", response_model=Dict)
async def withdraw_consent(
    request: ConsentWithdrawalRequest,
    current_user: User = Depends(get_current_user),
    privacy_service: PrivacyComplianceService = Depends(get_privacy_service)
):
    """
    Withdraw consent for specific data processing activities
    """
    try:
        # Convert string enums
        data_category = DataCategory(request.data_category)
        processing_purpose = ProcessingPurpose(request.processing_purpose)
        
        result = await privacy_service.withdraw_consent(
            user_id=current_user.id,
            data_category=data_category,
            processing_purpose=processing_purpose
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "success": True,
            "message": "Consent withdrawn successfully",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid category or purpose: {str(e)}")
    except Exception as e:
        logger.error(f"Error withdrawing consent for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to withdraw consent")

@router.get("/dashboard", response_model=Dict)
async def get_privacy_dashboard(
    current_user: User = Depends(get_current_user),
    privacy_service: PrivacyComplianceService = Depends(get_privacy_service)
):
    """
    Get comprehensive privacy dashboard data for the current user
    """
    try:
        dashboard_data = await privacy_service.get_privacy_dashboard_data(current_user.id)
        
        return {
            "success": True,
            "data": dashboard_data
        }
        
    except Exception as e:
        logger.error(f"Error fetching privacy dashboard for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch privacy dashboard")

@router.post("/data-subject-request", response_model=Dict)
async def submit_data_subject_request(
    request: DataSubjectRightsRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    privacy_service: PrivacyComplianceService = Depends(get_privacy_service)
):
    """
    Submit a GDPR data subject rights request
    """
    try:
        # Validate request type
        try:
            request_type = DataSubjectRight(request.request_type)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid request type. Must be one of: {[r.value for r in DataSubjectRight]}"
            )
        
        # Convert data categories
        data_categories = []
        for cat in request.data_categories:
            try:
                data_categories.append(DataCategory(cat))
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid data category: {cat}"
                )
        
        # Create privacy request
        import uuid
        privacy_request = PrivacyRequest(
            request_id=f"DSR_{uuid.uuid4().hex[:8].upper()}",
            user_id=current_user.id,
            request_type=request_type,
            status="pending",
            requested_at=datetime.utcnow(),
            processed_at=None,
            data_categories=data_categories,
            notes=request.notes
        )
        
        # Process request in background for non-urgent requests
        if request_type in [DataSubjectRight.ACCESS, DataSubjectRight.DATA_PORTABILITY]:
            background_tasks.add_task(
                privacy_service.process_data_subject_request,
                privacy_request
            )
            
            return {
                "success": True,
                "request_id": privacy_request.request_id,
                "status": "processing",
                "message": f"Your {request_type.value} request has been submitted and will be processed within 30 days as required by GDPR.",
                "estimated_completion": "30 days"
            }
        else:
            # Process immediately for urgent requests
            result = await privacy_service.process_data_subject_request(privacy_request)
            
            return {
                "success": result["success"],
                "request_id": privacy_request.request_id,
                "data": result
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing data subject request for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process data subject request")

@router.get("/data-export/{request_id}")
async def download_data_export(
    request_id: str,
    current_user: User = Depends(get_current_user),
    privacy_service: PrivacyComplianceService = Depends(get_privacy_service)
):
    """
    Download data export file from a completed access or portability request
    """
    try:
        # Verify request belongs to user and is completed
        request_info = await privacy_service.get_request_info(request_id)
        
        if not request_info or request_info["user_id"] != current_user.id:
            raise HTTPException(status_code=404, detail="Request not found")
        
        if request_info["status"] != "completed":
            raise HTTPException(status_code=400, detail="Request not yet completed")
        
        # Get file path
        file_path = request_info.get("file_path")
        if not file_path:
            raise HTTPException(status_code=404, detail="Export file not found")
        
        return FileResponse(
            path=file_path,
            filename=f"dinner1_data_export_{current_user.id}_{request_id}.zip",
            media_type="application/zip"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading data export {request_id} for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to download data export")

@router.put("/preferences", response_model=Dict)
async def update_privacy_preferences(
    preferences: PrivacyPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    privacy_service: PrivacyComplianceService = Depends(get_privacy_service)
):
    """
    Update user's privacy preferences
    """
    try:
        # Convert preferences to consent updates
        consent_updates = []
        
        if preferences.marketing_emails is not None:
            action = "grant" if preferences.marketing_emails else "withdraw"
            consent_updates.append({
                "category": "marketing",
                "action": action,
                "purpose": ProcessingPurpose.MARKETING
            })
        
        if preferences.location_sharing is not None:
            action = "grant" if preferences.location_sharing else "withdraw"
            consent_updates.append({
                "category": "location_services",
                "action": action,
                "purpose": ProcessingPurpose.MATCHING_SERVICE
            })
        
        if preferences.analytics_participation is not None:
            action = "grant" if preferences.analytics_participation else "withdraw"
            consent_updates.append({
                "category": "analytics",
                "action": action,
                "purpose": ProcessingPurpose.ANALYTICS
            })
        
        # Apply consent updates
        results = []
        for update in consent_updates:
            if update["action"] == "grant":
                result = await privacy_service.collect_user_consent(
                    user_id=current_user.id,
                    consent_categories=[update["category"]]
                )
            else:
                result = await privacy_service.withdraw_consent(
                    user_id=current_user.id,
                    data_category=DataCategory.PROFILE_DATA,  # Simplified mapping
                    processing_purpose=update["purpose"]
                )
            results.append(result)
        
        return {
            "success": True,
            "message": "Privacy preferences updated successfully",
            "updates_applied": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error updating privacy preferences for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update privacy preferences")

@router.post("/rectification", response_model=Dict)
async def request_data_rectification(
    request: RectificationRequest,
    current_user: User = Depends(get_current_user),
    privacy_service: PrivacyComplianceService = Depends(get_privacy_service)
):
    """
    Request correction of inaccurate personal data (GDPR Article 16)
    """
    try:
        # Create rectification request
        import uuid
        privacy_request = PrivacyRequest(
            request_id=f"RECT_{uuid.uuid4().hex[:8].upper()}",
            user_id=current_user.id,
            request_type=DataSubjectRight.RECTIFICATION,
            status="pending",
            requested_at=datetime.utcnow(),
            processed_at=None,
            data_categories=[DataCategory.PROFILE_DATA],
            notes=f"Field: {request.field_name}, Current: {request.current_value}, Correct: {request.correct_value}, Reason: {request.reason}"
        )
        
        result = await privacy_service.process_data_subject_request(privacy_request)
        
        return {
            "success": True,
            "request_id": privacy_request.request_id,
            "message": "Data rectification request submitted successfully",
            "estimated_completion": "48 hours"
        }
        
    except Exception as e:
        logger.error(f"Error processing rectification request for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process rectification request")

@router.get("/requests", response_model=Dict)
async def get_privacy_requests(
    current_user: User = Depends(get_current_user),
    privacy_service: PrivacyComplianceService = Depends(get_privacy_service)
):
    """
    Get history of user's privacy requests
    """
    try:
        requests = await privacy_service.get_user_privacy_requests(current_user.id)
        
        return {
            "success": True,
            "requests": requests
        }
        
    except Exception as e:
        logger.error(f"Error fetching privacy requests for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch privacy requests")

@router.delete("/account", response_model=Dict)
async def request_account_deletion(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    privacy_service: PrivacyComplianceService = Depends(get_privacy_service)
):
    """
    Request complete account deletion (Right to erasure - GDPR Article 17)
    """
    try:
        # Create erasure request for all data categories
        import uuid
        privacy_request = PrivacyRequest(
            request_id=f"DEL_{uuid.uuid4().hex[:8].upper()}",
            user_id=current_user.id,
            request_type=DataSubjectRight.ERASURE,
            status="pending",
            requested_at=datetime.utcnow(),
            processed_at=None,
            data_categories=list(DataCategory),
            notes="Complete account deletion requested by user"
        )
        
        # Process deletion in background
        background_tasks.add_task(
            privacy_service.process_data_subject_request,
            privacy_request
        )
        
        return {
            "success": True,
            "request_id": privacy_request.request_id,
            "message": "Account deletion request submitted. Your account will be deleted within 30 days.",
            "effective_date": "30 days from now",
            "what_happens_next": [
                "Your profile will be immediately hidden from other users",
                "Your personal data will be permanently deleted within 30 days",
                "Some data may be retained for legal compliance purposes",
                "You will receive confirmation once deletion is complete"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error processing account deletion for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process account deletion request")

@router.get("/policy", response_model=Dict)
async def get_privacy_policy():
    """
    Get current privacy policy and terms
    """
    try:
        # In production, this would fetch from database or file system
        privacy_policy = {
            "version": "1.0",
            "effective_date": "2024-01-01",
            "last_updated": "2024-01-01",
            "policy_url": "https://dinner1.com/privacy-policy",
            "contact_email": "privacy@dinner1.com",
            "dpo_contact": "dpo@dinner1.com",
            "key_points": [
                "We process your data to provide matching services",
                "Your data is encrypted and securely stored",
                "You have full control over your privacy settings",
                "We never sell your personal data to third parties",
                "You can download or delete your data at any time"
            ],
            "legal_basis": {
                "matching_service": "Legitimate interest and consent",
                "safety_moderation": "Legitimate interest",
                "communication": "Contract performance",
                "marketing": "Consent"
            },
            "data_retention": {
                "profile_data": "Deleted 7 years after account closure",
                "messages": "Deleted 3 years after account closure", 
                "photos": "Deleted 1 year after removal",
                "location_data": "Deleted after 90 days"
            }
        }
        
        return {
            "success": True,
            "privacy_policy": privacy_policy
        }
        
    except Exception as e:
        logger.error(f"Error fetching privacy policy: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch privacy policy")

# Error handlers
@router.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return HTTPException(status_code=400, detail=str(exc))

@router.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception in privacy API: {str(exc)}")
    return HTTPException(status_code=500, detail="Internal server error")