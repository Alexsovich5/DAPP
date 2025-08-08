from __future__ import annotations

from typing import Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from ....api.v1.deps import get_current_user
from ....models.user import User
from ....services.user_safety import (
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


# Dependency factory placeholders – wire your actual implementations
def get_user_safety_service() -> UserSafetyService:
    # In a full app, inject DB, Redis, and moderation deps here
    raise HTTPException(
        status_code=503, detail="Safety service not configured"
    )


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
