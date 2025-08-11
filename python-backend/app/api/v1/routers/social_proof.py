"""
Phase 7: Social Proof & Community Features API Router
API endpoints for trust, verification, and community validation
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.social_proof_service import social_proof_engine

router = APIRouter()


class VerificationRequest(BaseModel):
    verification_type: str
    verification_data: Dict[str, Any]


class CommunityFeedbackRequest(BaseModel):
    subject_user_id: int
    connection_id: int
    feedback_type: str
    ratings: Dict[str, float]
    feedback_text: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class SuccessStoryRequest(BaseModel):
    user2_id: int
    connection_id: int
    title: str
    content: str
    story_type: str = "relationship_success"
    both_consent: bool


class ReferralRequest(BaseModel):
    referee_email: str
    message: Optional[str] = ""
    context: Optional[Dict[str, Any]] = None


class SafetyReportRequest(BaseModel):
    reported_user_id: int
    report_type: str
    description: str
    severity: str = "medium"
    evidence: Optional[Dict[str, Any]] = None
    connection_context: Optional[Dict[str, Any]] = None


@router.post("/verification/initiate")
async def initiate_verification(
    request: VerificationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Initiate user verification process"""
    try:
        result = await social_proof_engine.initiate_user_verification(
            user_id=current_user.id,
            verification_type=request.verification_type,
            verification_data=request.verification_data,
            db=db
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback/submit")
async def submit_community_feedback(
    request: CommunityFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit community feedback about user interaction"""
    try:
        result = await social_proof_engine.submit_community_feedback(
            reviewer_id=current_user.id,
            subject_user_id=request.subject_user_id,
            connection_id=request.connection_id,
            feedback_data={
                "type": request.feedback_type,
                "ratings": request.ratings,
                "text": request.feedback_text,
                "context": request.context
            },
            db=db
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/success-story/create")
async def create_success_story(
    request: SuccessStoryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a success story for the community"""
    try:
        result = await social_proof_engine.create_success_story(
            user1_id=current_user.id,
            user2_id=request.user2_id,
            connection_id=request.connection_id,
            story_data={
                "title": request.title,
                "content": request.content,
                "type": request.story_type,
                "both_consent": request.both_consent
            },
            db=db
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/referral/create")
async def create_referral(
    request: ReferralRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create friend referral"""
    try:
        result = await social_proof_engine.process_referral_system(
            referrer_id=current_user.id,
            referee_email=request.referee_email,
            referral_data={
                "message": request.message,
                "context": request.context
            },
            db=db
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/social-proof/indicators")
async def get_social_proof_indicators(
    context: str = "profile_view",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get social proof indicators for user profile"""
    try:
        result = await social_proof_engine.generate_social_proof_indicators(
            user_id=current_user.id,
            context=context,
            db=db
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/social-proof/indicators/{user_id}")
async def get_user_social_proof_indicators(
    user_id: int,
    context: str = "profile_view",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get social proof indicators for specific user"""
    try:
        result = await social_proof_engine.generate_social_proof_indicators(
            user_id=user_id,
            context=context,
            db=db
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/safety/report")
async def report_safety_concern(
    request: SafetyReportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Report safety concerns about users"""
    try:
        result = await social_proof_engine.report_safety_concern(
            reporter_id=current_user.id,
            reported_user_id=request.reported_user_id,
            report_data={
                "type": request.report_type,
                "description": request.description,
                "severity": request.severity,
                "evidence": request.evidence,
                "connection_context": request.connection_context
            },
            db=db
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trust-score")
async def get_user_trust_score(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's trust score"""
    try:
        trust_score = await social_proof_engine._get_user_trust_score(current_user.id, db)
        trust_level = await social_proof_engine._get_trust_level(current_user.id, db)
        
        return {
            "success": True,
            "data": {
                "trust_score": trust_score,
                "trust_level": trust_level,
                "score_breakdown": {
                    "verification_component": "Available in detailed view",
                    "community_feedback_component": "Available in detailed view"
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/community/success-stories")
async def get_community_success_stories(
    limit: int = 10,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get approved community success stories"""
    try:
        # This would fetch approved success stories from database
        return {
            "success": True,
            "data": {
                "stories": [
                    {
                        "id": 1,
                        "title": "Found My Soul Partner",
                        "preview": "After 7 days of revelations, we knew we were meant to be...",
                        "success_type": "relationship_success",
                        "inspiration_score": 0.95
                    }
                ],
                "total": 1,
                "inspiration_message": "These stories show the power of soul-before-skin connections"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))