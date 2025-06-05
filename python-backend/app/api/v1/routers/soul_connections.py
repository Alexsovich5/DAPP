from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.soul_connection import SoulConnection
from app.schemas.soul_connection import (
    SoulConnectionCreate, 
    SoulConnectionResponse, 
    SoulConnectionUpdate,
    DiscoveryRequest,
    DiscoveryResponse,
    CompatibilityResponse
)
from app.services.compatibility import get_compatibility_calculator

logger = logging.getLogger(__name__)
router = APIRouter(tags=["soul-connections"])


@router.get("/discover", response_model=List[DiscoveryResponse])
def discover_soul_connections(
    max_results: int = Query(default=10, ge=1, le=50),
    min_compatibility: float = Query(default=50.0, ge=0, le=100),
    hide_photos: bool = Query(default=True),
    age_range_min: Optional[int] = Query(default=None, ge=18, le=100),
    age_range_max: Optional[int] = Query(default=None, ge=18, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Discover potential soul connections using local compatibility algorithms.
    Filters out users already connected and applies compatibility scoring.
    """
    try:
        # Get compatibility calculator
        calculator = get_compatibility_calculator()
        
        # Get existing connections to exclude
        existing_connections = db.query(SoulConnection).filter(
            (SoulConnection.user1_id == current_user.id) |
            (SoulConnection.user2_id == current_user.id)
        ).all()
        
        excluded_user_ids = set()
        for conn in existing_connections:
            excluded_user_ids.add(conn.user1_id)
            excluded_user_ids.add(conn.user2_id)
        excluded_user_ids.add(current_user.id)  # Exclude self
        
        # Build query for potential matches
        query = db.query(User).filter(
            User.id.notin_(excluded_user_ids),
            User.is_active == True,
            User.emotional_onboarding_completed == True
        )
        
        # Apply age filters if specified
        if age_range_min or age_range_max:
            # Note: date_of_birth is stored as string, need to calculate age
            # For MVP, we'll skip age filtering and implement in next iteration
            pass
        
        potential_matches = query.limit(max_results * 3).all()  # Get more for filtering
        
        # Calculate compatibility for each potential match
        discovery_results = []
        current_user_data = {
            'interests': current_user.interests or [],
            'core_values': current_user.core_values or {},
            'age': 25,  # Default for MVP, calculate from date_of_birth later
            'location': current_user.location or ''
        }
        
        for user in potential_matches:
            user_data = {
                'interests': user.interests or [],
                'core_values': user.core_values or {},
                'age': 25,  # Default for MVP
                'location': user.location or ''
            }
            
            compatibility = calculator.calculate_overall_compatibility(
                current_user_data, user_data
            )
            
            # Filter by minimum compatibility
            if compatibility['total_compatibility'] >= min_compatibility:
                # Create profile preview (limited info for soul discovery)
                profile_preview = {
                    'first_name': user.first_name,
                    'age': 25,  # Calculate from date_of_birth
                    'location': user.location,
                    'bio': user.bio[:100] + '...' if user.bio and len(user.bio) > 100 else user.bio,
                    'interests': user.interests[:3] if user.interests else [],  # Show only first 3
                    'emotional_depth_score': float(user.emotional_depth_score) if user.emotional_depth_score else None
                }
                
                discovery_results.append(DiscoveryResponse(
                    user_id=user.id,
                    compatibility=CompatibilityResponse(**compatibility),
                    profile_preview=profile_preview,
                    is_photo_hidden=hide_photos
                ))
        
        # Sort by compatibility score and limit results
        discovery_results.sort(key=lambda x: x.compatibility.total_compatibility, reverse=True)
        return discovery_results[:max_results]
        
    except Exception as e:
        logger.error(f"Error in discover_soul_connections: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error discovering connections"
        )


@router.post("/initiate", response_model=SoulConnectionResponse)
def initiate_soul_connection(
    connection_data: SoulConnectionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initiate a new soul connection with another user.
    Calculates initial compatibility and sets up the connection.
    """
    try:
        # Check if target user exists and has completed onboarding
        target_user = db.query(User).filter(
            User.id == connection_data.user2_id,
            User.is_active == True,
            User.emotional_onboarding_completed == True
        ).first()
        
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target user not found or hasn't completed emotional onboarding"
            )
        
        # Check if connection already exists
        existing_connection = db.query(SoulConnection).filter(
            ((SoulConnection.user1_id == current_user.id) & (SoulConnection.user2_id == connection_data.user2_id)) |
            ((SoulConnection.user1_id == connection_data.user2_id) & (SoulConnection.user2_id == current_user.id))
        ).first()
        
        if existing_connection:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Connection already exists with this user"
            )
        
        # Calculate initial compatibility
        calculator = get_compatibility_calculator()
        current_user_data = {
            'interests': current_user.interests or [],
            'core_values': current_user.core_values or {},
            'age': 25,  # Default for MVP
            'location': current_user.location or ''
        }
        target_user_data = {
            'interests': target_user.interests or [],
            'core_values': target_user.core_values or {},
            'age': 25,  # Default for MVP
            'location': target_user.location or ''
        }
        
        compatibility = calculator.calculate_overall_compatibility(
            current_user_data, target_user_data
        )
        
        # Create new soul connection
        new_connection = SoulConnection(
            user1_id=current_user.id,
            user2_id=connection_data.user2_id,
            initiated_by=current_user.id,
            compatibility_score=compatibility['total_compatibility'],
            compatibility_breakdown=compatibility,
            connection_stage=connection_data.connection_stage,
            reveal_day=connection_data.reveal_day,
            status=connection_data.status
        )
        
        db.add(new_connection)
        db.commit()
        db.refresh(new_connection)
        
        logger.info(f"New soul connection created: {current_user.id} -> {connection_data.user2_id}")
        return new_connection
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating soul connection: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating soul connection"
        )


@router.get("/active", response_model=List[SoulConnectionResponse])
def get_active_connections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all active soul connections for the current user.
    """
    try:
        connections = db.query(SoulConnection).filter(
            ((SoulConnection.user1_id == current_user.id) | (SoulConnection.user2_id == current_user.id)),
            SoulConnection.status == "active"
        ).all()
        
        # Enhance with user profile data
        enhanced_connections = []
        for conn in connections:
            conn_dict = conn.__dict__.copy()
            
            # Get other user's profile info
            other_user_id = conn.user2_id if conn.user1_id == current_user.id else conn.user1_id
            other_user = db.query(User).filter(User.id == other_user_id).first()
            
            if other_user:
                conn_dict['user1_profile'] = {
                    'id': conn.user1_id,
                    'first_name': current_user.first_name if conn.user1_id == current_user.id else other_user.first_name,
                    'profile_picture': current_user.profile_picture if conn.user1_id == current_user.id else other_user.profile_picture
                }
                conn_dict['user2_profile'] = {
                    'id': conn.user2_id,
                    'first_name': other_user.first_name if conn.user2_id == other_user.id else current_user.first_name,
                    'profile_picture': other_user.profile_picture if conn.user2_id == other_user.id else current_user.profile_picture
                }
            
            enhanced_connections.append(SoulConnectionResponse(**conn_dict))
        
        return enhanced_connections
        
    except Exception as e:
        logger.error(f"Error getting active connections: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving connections"
        )


@router.put("/{connection_id}", response_model=SoulConnectionResponse)
def update_soul_connection(
    connection_id: int,
    update_data: SoulConnectionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a soul connection (progression, consent, etc.).
    """
    try:
        connection = db.query(SoulConnection).filter(
            SoulConnection.id == connection_id,
            ((SoulConnection.user1_id == current_user.id) | (SoulConnection.user2_id == current_user.id))
        ).first()
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Soul connection not found"
            )
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(connection, field, value)
        
        db.commit()
        db.refresh(connection)
        
        logger.info(f"Soul connection updated: {connection_id}")
        return connection
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating soul connection: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating connection"
        )


@router.get("/{connection_id}", response_model=SoulConnectionResponse)
def get_soul_connection(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific soul connection.
    """
    try:
        connection = db.query(SoulConnection).filter(
            SoulConnection.id == connection_id,
            ((SoulConnection.user1_id == current_user.id) | (SoulConnection.user2_id == current_user.id))
        ).first()
        
        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Soul connection not found"
            )
        
        return connection
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting soul connection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving connection"
        )