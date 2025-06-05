from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.match import Match, MatchStatus
from app.models.user import User
from app.schemas.match import MatchCreate, MatchUpdate, Match as MatchSchema
from app.api.v1.deps import get_current_user

# Error messages
MATCH_NOT_FOUND = "Match not found"
MATCH_EXISTS = "A pending match request already exists"
INVALID_MATCH = "Cannot create a match with yourself"
RECIPIENT_NOT_FOUND = "Recipient not found"
NOT_AUTHORIZED = "Only the match recipient can update the status"
INVALID_UPDATE = "Can only update pending matches"

router = APIRouter(prefix="/matches", tags=["matches"])


@router.post("", response_model=MatchSchema)
def create_match(
    match_in: MatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Create a new dinner match request."""
    if match_in.recipient_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=INVALID_MATCH
        )

    recipient = db.query(User).filter(User.id == match_in.recipient_id).first()
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=RECIPIENT_NOT_FOUND
        )

    existing_match = (
        db.query(Match)
        .filter(
            Match.sender_id == current_user.id,
            Match.receiver_id == match_in.recipient_id,
            Match.status == MatchStatus.PENDING,
        )
        .first()
    )

    if existing_match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=MATCH_EXISTS
        )

    match = Match(
        sender_id=current_user.id,
        receiver_id=match_in.recipient_id,
        restaurant_preference=match_in.restaurant_preference,
        proposed_date=match_in.proposed_date,
        status=MatchStatus.PENDING,
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return match


@router.get("/sent", response_model=List[MatchSchema])
def get_sent_matches(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Any:
    """Get all matches sent by the current user."""
    return db.query(Match).filter(Match.sender_id == current_user.id).all()


@router.get("/received", response_model=List[MatchSchema])
def get_received_matches(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Any:
    """Get all matches received by the current user."""
    return db.query(Match).filter(Match.receiver_id == current_user.id).all()


@router.put("/{match_id}", response_model=MatchSchema)
def update_match(
    match_id: int,
    match_in: MatchUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Update a match (accept/reject and update details)."""
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=MATCH_NOT_FOUND
        )

    if match.receiver_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=NOT_AUTHORIZED
        )

    if match.status != MatchStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=INVALID_UPDATE
        )

    for field, value in match_in.dict(exclude_unset=True).items():
        setattr(match, field, value)

    db.commit()
    db.refresh(match)
    return match
