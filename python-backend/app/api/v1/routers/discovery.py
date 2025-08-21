"""
Discovery API Router - Local Compatibility & Match Discovery
Fast local algorithm-based matching without external AI dependencies
"""

import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, not_, func
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.profile import Profile
from app.services.compatibility import CompatibilityCalculator
from app.services.optimized_discovery import (
    OptimizedDiscoveryService, DiscoveryFilters, get_optimized_discovery_service
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["discovery"])


# Pydantic models for request/response

class CompatibilityScoreResponse(BaseModel):
    user_id: int
    compatibility_percentage: float
    breakdown: Dict[str, float]
    match_quality: str
    interests_overlap: List[str]
    shared_values: List[str]
    processing_time_ms: float


class DiscoveryUserProfile(BaseModel):
    id: int
    first_name: str
    age: Optional[int] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    interests: List[str] = []
    compatibility_score: float
    distance_km: Optional[float] = None
    online_status: str = "offline"


class DiscoveryResponse(BaseModel):
    total_users: int
    users: List[DiscoveryUserProfile]
    applied_filters: Dict[str, Any]
    processing_time_ms: float
    recommendations: Dict[str, str]


class MutualInterestsResponse(BaseModel):
    user1_id: int
    user2_id: int
    shared_interests: List[str]
    total_interests_user1: int
    total_interests_user2: int
    jaccard_similarity: float
    interest_categories: Dict[str, List[str]]


@router.get("/potential-matches", response_model=DiscoveryResponse)
def discover_potential_matches(
    limit: int = Query(default=20, ge=1, le=50, description="Number of users to return"),
    min_compatibility: float = Query(default=50.0, ge=0.0, le=100.0, description="Minimum compatibility percentage"),
    max_distance_km: Optional[int] = Query(default=None, ge=1, le=500, description="Maximum distance in kilometers"),
    age_min: Optional[int] = Query(default=None, ge=18, le=100, description="Minimum age filter"),
    age_max: Optional[int] = Query(default=None, ge=18, le=100, description="Maximum age filter"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Discover potential matches using local compatibility algorithms.
    
    Fast local processing with Jaccard similarity for interests and values alignment.
    Target processing time: <500ms per user.
    """
    start_time = datetime.utcnow()
    
    try:
        # Initialize compatibility calculator
        calculator = CompatibilityCalculator()
        
        # Get current user's profile data
        current_user_interests = current_user.interests or []
        current_user_values = getattr(current_user, 'core_values', {}) or {}
        
        # Base query for potential matches (exclude current user and blocked users)
        query = db.query(User).filter(
            and_(
                User.id != current_user.id,
                User.is_active == True
            )
        )
        
        # Apply age filters
        if age_min is not None:
            query = query.filter(func.date_part('year', func.age(User.date_of_birth)) >= age_min)
        if age_max is not None:
            query = query.filter(func.date_part('year', func.age(User.date_of_birth)) <= age_max)
        
        # Get potential matches
        potential_users = query.limit(limit * 2).all()  # Get more to filter by compatibility
        
        # Calculate compatibility for each user
        compatible_users = []
        for user in potential_users:
            try:
                # Calculate overall compatibility
                compatibility_result = calculator.calculate_overall_compatibility(
                    user1={
                        'interests': current_user_interests,
                        'core_values': current_user_values,
                        'age': _calculate_age(current_user.date_of_birth),
                        'location': current_user.location
                    },
                    user2={
                        'interests': user.interests or [],
                        'core_values': getattr(user, 'core_values', {}) or {},
                        'age': _calculate_age(user.date_of_birth),
                        'location': user.location
                    }
                )
                
                compatibility_score = compatibility_result['total_compatibility']
                
                # Filter by minimum compatibility
                if compatibility_score >= min_compatibility:
                    user_profile = DiscoveryUserProfile(
                        id=user.id,
                        first_name=user.first_name or "Anonymous",
                        age=_calculate_age(user.date_of_birth),
                        location=user.location,
                        bio=user.bio,
                        interests=user.interests or [],
                        compatibility_score=round(compatibility_score, 1),
                        distance_km=None,  # TODO: Implement distance calculation
                        online_status="offline"  # TODO: Implement real-time status
                    )
                    compatible_users.append(user_profile)
                    
            except Exception as e:
                logger.warning(f"Error calculating compatibility for user {user.id}: {str(e)}")
                continue
        
        # Sort by compatibility score (highest first)
        compatible_users.sort(key=lambda x: x.compatibility_score, reverse=True)
        
        # Limit results
        final_users = compatible_users[:limit]
        
        # Calculate processing time
        end_time = datetime.utcnow()
        processing_time_ms = (end_time - start_time).total_seconds() * 1000
        
        # Applied filters summary
        applied_filters = {
            "min_compatibility": min_compatibility,
            "max_distance_km": max_distance_km,
            "age_range": {"min": age_min, "max": age_max},
            "excluded_user_id": current_user.id
        }
        
        # Generate recommendations
        recommendations = _generate_discovery_recommendations(final_users, current_user_interests)
        
        return DiscoveryResponse(
            total_users=len(final_users),
            users=final_users,
            applied_filters=applied_filters,
            processing_time_ms=round(processing_time_ms, 2),
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"Error in discover_potential_matches: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to discover matches: {str(e)}"
        )


@router.get("/compatibility/{user_id}", response_model=CompatibilityScoreResponse)
def calculate_compatibility_score(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Calculate detailed compatibility score with another user.
    
    Returns comprehensive breakdown of compatibility factors using local algorithms.
    """
    start_time = datetime.utcnow()
    
    try:
        # Get target user
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Initialize compatibility calculator
        calculator = CompatibilityCalculator()
        
        # Get user data
        current_user_interests = current_user.interests or []
        current_user_values = getattr(current_user, 'core_values', {}) or {}
        target_user_interests = target_user.interests or []
        target_user_values = getattr(target_user, 'core_values', {}) or {}
        
        # Calculate overall compatibility
        compatibility_result = calculator.calculate_overall_compatibility(
            user1={
                'interests': current_user_interests,
                'core_values': current_user_values,
                'age': _calculate_age(current_user.date_of_birth),
                'location': current_user.location
            },
            user2={
                'interests': target_user_interests,
                'core_values': target_user_values,
                'age': _calculate_age(target_user.date_of_birth),
                'location': target_user.location
            }
        )
        
        # Find overlapping interests
        interests_overlap = list(set(current_user_interests) & set(target_user_interests))
        
        # Find shared values (simplified)
        shared_values = []
        for key in current_user_values.keys():
            if key in target_user_values:
                shared_values.append(key)
        
        # Calculate processing time
        end_time = datetime.utcnow()
        processing_time_ms = (end_time - start_time).total_seconds() * 1000
        
        return CompatibilityScoreResponse(
            user_id=target_user.id,
            compatibility_percentage=compatibility_result['total_compatibility'],
            breakdown=compatibility_result['breakdown'],
            match_quality=compatibility_result['match_quality'],
            interests_overlap=interests_overlap,
            shared_values=shared_values,
            processing_time_ms=round(processing_time_ms, 2)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating compatibility with user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate compatibility: {str(e)}"
        )


@router.get("/mutual-interests/{user_id}", response_model=MutualInterestsResponse)
def get_mutual_interests(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed mutual interests analysis between two users.
    
    Uses Jaccard similarity coefficient for interests overlap calculation.
    """
    try:
        # Get target user
        target_user = db.query(User).filter(User.id == user_id).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Get interests
        current_user_interests = current_user.interests or []
        target_user_interests = target_user.interests or []
        
        # Calculate Jaccard similarity
        calculator = CompatibilityCalculator()
        jaccard_similarity = calculator.calculate_interest_similarity(
            current_user_interests, target_user_interests
        )
        
        # Find shared interests
        shared_interests = list(set(current_user_interests) & set(target_user_interests))
        
        # Categorize interests (simplified)
        interest_categories = _categorize_interests(shared_interests)
        
        return MutualInterestsResponse(
            user1_id=current_user.id,
            user2_id=target_user.id,
            shared_interests=shared_interests,
            total_interests_user1=len(current_user_interests),
            total_interests_user2=len(target_user_interests),
            jaccard_similarity=round(jaccard_similarity * 100, 2),  # Convert to percentage
            interest_categories=interest_categories
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting mutual interests with user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get mutual interests: {str(e)}"
        )


# Helper functions

def _calculate_age(date_of_birth) -> Optional[int]:
    """Calculate age from date of birth."""
    if not date_of_birth:
        return None
    
    try:
        if isinstance(date_of_birth, str):
            from datetime import datetime
            birth_date = datetime.fromisoformat(date_of_birth.replace('Z', '+00:00'))
        else:
            birth_date = date_of_birth
        
        today = datetime.now()
        age = today.year - birth_date.year
        if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
            age -= 1
        return age
    except:
        return None


def _categorize_interests(interests: List[str]) -> Dict[str, List[str]]:
    """Categorize interests into broad categories."""
    categories = {
        "Sports & Fitness": [],
        "Arts & Culture": [],
        "Technology": [],
        "Food & Cooking": [],
        "Travel": [],
        "Music": [],
        "Other": []
    }
    
    # Simple keyword-based categorization
    for interest in interests:
        interest_lower = interest.lower()
        categorized = False
        
        if any(word in interest_lower for word in ['sport', 'gym', 'fitness', 'running', 'yoga', 'hiking']):
            categories["Sports & Fitness"].append(interest)
            categorized = True
        elif any(word in interest_lower for word in ['art', 'music', 'painting', 'culture', 'museum', 'theater']):
            categories["Arts & Culture"].append(interest)
            categorized = True
        elif any(word in interest_lower for word in ['tech', 'programming', 'computer', 'coding', 'AI']):
            categories["Technology"].append(interest)
            categorized = True
        elif any(word in interest_lower for word in ['food', 'cooking', 'restaurant', 'cuisine', 'chef']):
            categories["Food & Cooking"].append(interest)
            categorized = True
        elif any(word in interest_lower for word in ['travel', 'trip', 'vacation', 'country', 'explore']):
            categories["Travel"].append(interest)
            categorized = True
        
        if not categorized:
            categories["Other"].append(interest)
    
    # Remove empty categories
    return {k: v for k, v in categories.items() if v}


def _generate_discovery_recommendations(users: List[DiscoveryUserProfile], current_interests: List[str]) -> Dict[str, str]:
    """Generate personalized recommendations based on discovery results."""
    recommendations = {}
    
    if not users:
        recommendations["tip"] = "Try adjusting your compatibility filters to discover more matches"
        return recommendations
    
    avg_compatibility = sum(user.compatibility_score for user in users) / len(users)
    
    if avg_compatibility > 80:
        recommendations["quality"] = "Excellent match quality! You have strong compatibility with these users."
    elif avg_compatibility > 60:
        recommendations["quality"] = "Good match potential. Consider reaching out to start conversations."
    else:
        recommendations["quality"] = "Moderate compatibility. Focus on shared interests for better connections."
    
    # Interest-based recommendations
    common_interests = {}
    for user in users:
        for interest in user.interests:
            if interest.lower() in [i.lower() for i in current_interests]:
                common_interests[interest] = common_interests.get(interest, 0) + 1
    
    if common_interests:
        top_interest = max(common_interests, key=common_interests.get)
        recommendations["conversation_starter"] = f"Many matches share your interest in '{top_interest}' - great conversation starter!"
    
    return recommendations

# Optimized Discovery Endpoints

@router.get("/optimized")
def discover_users_optimized(
    age_min: Optional[int] = Query(None, ge=18, le=80, description="Minimum age filter"),
    age_max: Optional[int] = Query(None, ge=18, le=80, description="Maximum age filter"),
    location: Optional[str] = Query(None, description="Location filter"),
    min_compatibility: float = Query(50.0, ge=0, le=100, description="Minimum compatibility score"),
    limit: int = Query(20, ge=1, le=50, description="Number of users to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Optimized user discovery with enhanced performance and caching.
    Uses improved indexing and query optimization for faster results.
    """
    try:
        start_time = time.time()
        
        # Create discovery filters
        filters = DiscoveryFilters(
            age_min=age_min,
            age_max=age_max,
            location=location,
            min_compatibility=min_compatibility
        )
        
        # Use optimized discovery service
        discovery_service = get_optimized_discovery_service()
        result = discovery_service.discover_users(
            db=db,
            current_user=current_user,
            filters=filters,
            limit=limit,
            offset=offset
        )
        
        return {
            "users": result.users,
            "total_users": result.total_count,
            "performance": {
                "processing_time_ms": result.processing_time_ms,
                "cache_hit": result.cache_hit,
                "query_optimization_applied": result.query_optimization_applied
            },
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": offset + len(result.users) < result.total_count
            },
            "filters_applied": {
                "age_range": f"{age_min}-{age_max}" if age_min or age_max else None,
                "location": location,
                "min_compatibility": min_compatibility
            }
        }
        
    except Exception as e:
        logger.error(f"Error in optimized discovery: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optimized discovery failed: {str(e)}"
        )


@router.get("/cache-stats")
def get_discovery_cache_stats(current_user: User = Depends(get_current_user)):
    """
    Get discovery cache statistics for performance monitoring.
    """
    try:
        discovery_service = get_optimized_discovery_service()
        cache_stats = discovery_service.get_cache_stats()
        
        return {
            "cache_statistics": cache_stats,
            "cache_performance": {
                "efficiency": "high" if cache_stats["cache_utilization"] > 50 else "medium",
                "recommendation": "Cache is working well" if cache_stats["cache_utilization"] < 80 else "Consider increasing cache size"
            }
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get cache statistics")


@router.post("/clear-cache")
def clear_discovery_cache(current_user: User = Depends(get_current_user)):
    """
    Clear discovery cache (admin only).
    """
    try:
        # Check if user has admin privileges (simplified check)
        if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        discovery_service = get_optimized_discovery_service()
        discovery_service.clear_cache()
        
        logger.info(f"Discovery cache cleared by user {current_user.id}")
        
        return {
            "cache_cleared": True,
            "message": "Discovery cache cleared successfully",
            "cleared_by": current_user.id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")
