from __future__ import annotations

from typing import Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from ....api.v1.deps import get_current_user
from ....models.user import User
from ....services.user_safety_simplified import (
    UserSafetyService,
    UserReport as SafetyUserReport,
    ReportCategory,
)
router = APIRouter(prefix="/safety", tags=["safety"])


class UserReportRequest(BaseModel):
    reported_user_id: int
    category: ReportCategory
    description: str = Field(min_length=10)
    evidence: Dict[str, Any] = Field(default_factory=dict)


# Global safety service instance (in production, this would be properly injected)
_safety_service_instance = None

def get_user_safety_service() -> UserSafetyService:
    global _safety_service_instance
    if _safety_service_instance is None:
        _safety_service_instance = UserSafetyService()
    return _safety_service_instance


@router.post("/report")
async def report_user(
    payload: UserReportRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    safety_service: UserSafetyService = Depends(get_user_safety_service),
) -> Dict[str, Any]:
    try:
        report = SafetyUserReport(
            reporter_id=current_user.id,
            reported_user_id=payload.reported_user_id,
            category=payload.category,
            description=payload.description,
            evidence=payload.evidence,
            timestamp=datetime.utcnow(),
            ip_address=request.client.host if request.client else "unknown",
        )

        result = await safety_service.submit_report(report)
        return {"status": "report_received", **result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to submit report: {e}"
        )


@router.get("/status/{user_id}")
async def get_user_safety_status(
    user_id: int,
    current_user: User = Depends(get_current_user),
    safety_service: UserSafetyService = Depends(get_user_safety_service),
) -> Dict[str, Any]:
    """Get safety status for a specific user (admin only or own status)"""
    
    # Users can only check their own status, admins can check any user
    if current_user.id != user_id and not getattr(current_user, 'is_admin', False):
        raise HTTPException(
            status_code=403, detail="Can only check your own safety status"
        )
    
    try:
        status = await safety_service.get_user_safety_status(user_id)
        return status
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get safety status: {e}"
        )


@router.get("/reports/summary")
async def get_reports_summary(
    current_user: User = Depends(get_current_user),
    safety_service: UserSafetyService = Depends(get_user_safety_service),
) -> Dict[str, Any]:
    """Get summary of all reports (admin only)"""
    
    # Check if user has admin privileges
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(
            status_code=403, detail="Admin privileges required"
        )
    
    try:
        summary = await safety_service.get_reports_summary()
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get reports summary: {e}"
        )


@router.get("/categories")
async def get_report_categories() -> Dict[str, Any]:
    """Get available report categories and their descriptions"""
    
    categories = {
        "harassment": "Bullying, threats, or unwanted contact",
        "fake_profile": "Profile appears to be fake or impersonation",
        "inappropriate_photos": "Photos contain inappropriate content",
        "spam": "Sending unsolicited messages or promotional content",
        "scam": "Attempting to scam or defraud other users",
        "violence_threats": "Threats of violence or self-harm",
        "hate_speech": "Content promoting hatred or discrimination", 
        "underage": "User appears to be under 18 years old",
        "impersonation": "Pretending to be someone else",
        "other": "Other safety concerns not listed above"
    }
    
    return {
        "categories": categories,
        "message": "Select the category that best describes the safety issue"
    }
