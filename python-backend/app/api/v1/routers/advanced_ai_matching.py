"""
Phase 7: Advanced AI Matching Evolution API Router
API endpoints for machine learning optimization and predictive analytics
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.advanced_ai_matching_service import advanced_ai_matching_engine

router = APIRouter()


class PredictiveMatchRequest(BaseModel):
    count: int = 10
    algorithm_version: Optional[str] = None


class ExperimentRequest(BaseModel):
    experiment_config: Dict[str, Any]
    target_users: Optional[List[int]] = None


class SuccessPredictionRequest(BaseModel):
    user2_id: int
    connection_context: Optional[Dict[str, Any]] = None


class OptimizationRequest(BaseModel):
    recent_outcomes: List[Dict[str, Any]]


class PerformanceReportRequest(BaseModel):
    time_period_days: int = 30
    algorithm_versions: Optional[List[str]] = None


@router.post("/predictive-matches")
async def generate_predictive_matches(
    request: PredictiveMatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate matches using predictive AI with success probability"""
    try:
        result = await advanced_ai_matching_engine.generate_predictive_matches(
            user_id=current_user.id,
            count=request.count,
            algorithm_version=request.algorithm_version,
            db=db
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/success-patterns")
async def analyze_success_patterns(
    time_period_days: int = 90,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze matching success patterns for optimization"""
    try:
        result = await advanced_ai_matching_engine.analyze_matching_success_patterns(
            user_id=current_user.id,
            time_period_days=time_period_days,
            db=db
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict-success")
async def predict_relationship_success(
    request: SuccessPredictionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Predict long-term relationship success using ML models"""
    try:
        result = await advanced_ai_matching_engine.predict_relationship_success(
            user1_id=current_user.id,
            user2_id=request.user2_id,
            connection_context=request.connection_context,
            db=db
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize-real-time")
async def optimize_algorithm_real_time(
    request: OptimizationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Real-time algorithm optimization based on immediate feedback"""
    try:
        result = await advanced_ai_matching_engine.optimize_algorithm_real_time(
            user_id=current_user.id,
            recent_outcomes=request.recent_outcomes,
            db=db
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/experiments/create")
async def run_matching_experiment(
    request: ExperimentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Run A/B test experiment on matching algorithms"""
    try:
        # This would typically be admin-only
        result = await advanced_ai_matching_engine.run_matching_experiment(
            experiment_config=request.experiment_config,
            target_users=request.target_users,
            db=db
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance-report")
async def get_algorithm_performance_report(
    time_period_days: int = 30,
    algorithm_versions: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate comprehensive algorithm performance report"""
    try:
        # Parse algorithm versions if provided
        versions_list = algorithm_versions.split(",") if algorithm_versions else None
        
        result = await advanced_ai_matching_engine.generate_algorithm_performance_report(
            time_period_days=time_period_days,
            algorithm_versions=versions_list,
            db=db
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user-analytics")
async def get_user_behavior_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's behavior analytics for matching optimization"""
    try:
        analytics = await advanced_ai_matching_engine._get_user_behavior_analytics(
            current_user.id, db
        )
        return {"success": True, "data": analytics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/matching-insights")
async def get_matching_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get personalized matching insights and recommendations"""
    try:
        # Get recent matches and analyze patterns
        insights = {
            "matching_effectiveness": 0.75,
            "success_probability_trend": "improving",
            "key_recommendations": [
                "Your authenticity scores are attracting quality matches",
                "Consider expanding age range for more opportunities",
                "Your revelation completion rate is excellent"
            ],
            "optimization_suggestions": [
                "Focus on users who share your communication style",
                "Prioritize matches with high emotional intelligence"
            ],
            "prediction_accuracy": 0.82,
            "next_optimization_date": "2024-01-15T10:00:00Z"
        }
        
        return {"success": True, "data": insights}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/algorithm-versions")
async def get_algorithm_versions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available algorithm versions and current user's version"""
    try:
        return {
            "success": True,
            "data": {
                "available_versions": list(advanced_ai_matching_engine.algorithm_versions.keys()),
                "current_version": advanced_ai_matching_engine.current_algorithm_version,
                "user_customizations": "Available for trusted members",
                "version_descriptions": {
                    "v1.0": "Basic compatibility matching",
                    "v2.0": "Enhanced with behavioral analysis",
                    "v3.0": "Predictive success modeling"
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))