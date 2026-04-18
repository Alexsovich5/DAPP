"""
Messages API Router - Phase 4 Real-time Messaging
Soul-themed messaging with emotional context and real-time delivery
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.message_service import message_service
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)
router = APIRouter(tags=["messages"])


# Pydantic models for request/response


class SendMessageRequest(BaseModel):
    connection_id: int
    content: str
    emotional_context: Optional[Dict[str, Any]] = None


class SendMessageResponse(BaseModel):
    success: bool
    message_id: Optional[int]
    message: str
    delivered: bool
    error: Optional[str] = None


class TypingStatusRequest(BaseModel):
    connection_id: int
    is_typing: bool
    emotional_state: Optional[str] = None


class ConversationMessage(BaseModel):
    id: int
    sender_id: int
    content: str
    message_type: str
    is_soul_revelation: bool
    is_read: bool
    created_at: str
    is_own_message: bool


class ConversationResponse(BaseModel):
    success: bool
    messages: List[ConversationMessage]
    total_messages: int
    connection: Dict[str, Any]
    pagination: Dict[str, Any]


# Message endpoints


@router.post("/send", response_model=SendMessageResponse)
async def send_message(
    message_data: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send a message in a soul connection with emotional context
    """
    try:
        result = await message_service.send_message(
            sender_id=current_user.id,
            connection_id=message_data.connection_id,
            content=message_data.content,
            emotional_context=message_data.emotional_context,
            db=db,
        )

        return SendMessageResponse(
            success=result.success,
            message_id=result.message_id,
            message=result.message,
            delivered=result.delivered,
            error=result.error,
        )

    except Exception as e:
        logger.error(f"Error in send message endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}",
        )


@router.get("/conversation/{connection_id}")
async def get_conversation_messages(
    connection_id: int,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get messages for a conversation with pagination and emotional context
    """
    try:
        result = await message_service.get_conversation_messages(
            user_id=current_user.id,
            connection_id=connection_id,
            limit=limit,
            offset=offset,
            db=db,
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=result["error"]
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve messages",
        )


@router.get("/conversations")
async def get_user_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all conversations for the current user with summary information
    """
    try:
        result = await message_service.get_user_conversations(
            user_id=current_user.id, db=db
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"],
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user conversations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversations",
        )


@router.post("/typing-status")
async def update_typing_status(
    typing_data: TypingStatusRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update typing status with real-time broadcast to connection partner
    """
    try:
        success = await message_service.update_typing_status(
            user_id=current_user.id,
            connection_id=typing_data.connection_id,
            is_typing=typing_data.is_typing,
            emotional_state=typing_data.emotional_state,
            db=db,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found or access denied",
            )

        return {
            "success": True,
            "message": "Typing status updated successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating typing status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update typing status",
        )


@router.post("/mark-read/{connection_id}")
async def mark_messages_as_read(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Mark all messages in a connection as read
    """
    try:
        success = await message_service.mark_messages_as_read(
            user_id=current_user.id, connection_id=connection_id, db=db
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found or access denied",
            )

        return {"success": True, "message": "Messages marked as read"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking messages as read: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark messages as read",
        )


@router.get("/statistics")
async def get_message_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get messaging statistics for the current user
    """
    try:
        from app.models.message import Message
        from app.models.soul_connection import SoulConnection
        from sqlalchemy import func, or_

        # Get user's total messages sent
        total_sent = (
            db.query(Message).filter(Message.sender_id == current_user.id).count()
        )

        # Get user's total messages received
        user_connections = (
            db.query(SoulConnection)
            .filter(
                or_(
                    SoulConnection.user1_id == current_user.id,
                    SoulConnection.user2_id == current_user.id,
                )
            )
            .all()
        )

        connection_ids = [c.id for c in user_connections]
        total_received = (
            db.query(Message)
            .filter(
                Message.connection_id.in_(connection_ids),
                Message.sender_id != current_user.id,
            )
            .count()
            if connection_ids
            else 0
        )

        # Get unread messages count
        unread_count = (
            db.query(Message)
            .filter(
                Message.connection_id.in_(connection_ids),
                Message.sender_id != current_user.id,
                Message.is_read.is_(False),
            )
            .count()
            if connection_ids
            else 0
        )

        # Get active conversations count
        active_conversations = len(
            [c for c in user_connections if c.status == "active"]
        )

        # Message type distribution (text / revelation / photo / system)
        message_type_counts = (
            db.query(Message.message_type, func.count(Message.id).label("count"))
            .filter(Message.sender_id == current_user.id)
            .group_by(Message.message_type)
            .order_by(func.count(Message.id).desc())
            .all()
        )

        return {
            "success": True,
            "statistics": {
                "messages": {
                    "sent": total_sent,
                    "received": total_received,
                    "unread": unread_count,
                },
                "conversations": {
                    "active": active_conversations,
                    "total": len(user_connections),
                },
                "message_types": [
                    {"type": mtype, "count": count}
                    for mtype, count in message_type_counts
                ],
            },
            "generated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error getting message statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get statistics",
        )


@router.get("/last/{connection_id}")
async def get_last_message(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get the last message for a specific connection
    Used for conversation list previews
    """
    try:
        from app.models.message import Message
        from app.models.soul_connection import SoulConnection
        from sqlalchemy import or_

        # Verify user has access to this connection
        connection = (
            db.query(SoulConnection)
            .filter(
                SoulConnection.id == connection_id,
                or_(
                    SoulConnection.user1_id == current_user.id,
                    SoulConnection.user2_id == current_user.id,
                ),
            )
            .first()
        )

        if not connection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found or access denied",
            )

        # Get the last message for this connection
        last_message = (
            db.query(Message)
            .filter(Message.connection_id == connection_id)
            .order_by(Message.created_at.desc())
            .first()
        )

        if not last_message:
            # No messages yet - return empty state
            return {
                "success": True,
                "has_messages": False,
                "connection_id": connection_id,
                "message": None,
            }

        # Get sender info
        sender = db.query(User).filter(User.id == last_message.sender_id).first()

        return {
            "success": True,
            "has_messages": True,
            "connection_id": connection_id,
            "message": {
                "id": last_message.id,
                "sender_id": last_message.sender_id,
                "sender_name": (
                    f"{sender.first_name} {sender.last_name}" if sender else "Unknown"
                ),
                "is_own_message": last_message.sender_id == current_user.id,
                "content": last_message.message_text,
                "message_type": last_message.message_type,
                "is_read": last_message.is_read,
                "created_at": last_message.created_at.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting last message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get last message",
        )


@router.get("/search")
async def search_messages(
    query: str = Query(..., min_length=1),
    connection_id: Optional[int] = Query(None),
    limit: int = Query(default=20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Search messages by content with optional connection filtering
    """
    try:
        from app.models.message import Message
        from app.models.soul_connection import SoulConnection
        from sqlalchemy import or_

        # Get user's accessible connections
        user_connections = (
            db.query(SoulConnection.id)
            .filter(
                or_(
                    SoulConnection.user1_id == current_user.id,
                    SoulConnection.user2_id == current_user.id,
                )
            )
            .subquery()
        )

        # Base query for messages user can access
        base_query = db.query(Message).filter(
            Message.connection_id.in_(user_connections)
        )

        # Add connection filter if specified
        if connection_id:
            # Verify user has access to this connection
            connection = (
                db.query(SoulConnection)
                .filter(
                    SoulConnection.id == connection_id,
                    or_(
                        SoulConnection.user1_id == current_user.id,
                        SoulConnection.user2_id == current_user.id,
                    ),
                )
                .first()
            )

            if not connection:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Connection not found or access denied",
                )

            base_query = base_query.filter(Message.connection_id == connection_id)

        # Search in message text (case-insensitive)
        search_results = (
            base_query.filter(Message.message_text.ilike(f"%{query}%"))
            .order_by(Message.created_at.desc())
            .limit(limit)
            .all()
        )

        # Format results
        formatted_results = []
        for message in search_results:
            # Get sender info
            sender = db.query(User).filter(User.id == message.sender_id).first()

            formatted_results.append(
                {
                    "id": message.id,
                    "connection_id": message.connection_id,
                    "sender": {
                        "id": message.sender_id,
                        "name": (
                            f"{sender.first_name} {sender.last_name}"
                            if sender
                            else "Unknown"
                        ),
                        "is_current_user": message.sender_id == current_user.id,
                    },
                    "content": message.message_text,
                    "message_type": message.message_type,
                    "created_at": message.created_at.isoformat(),
                }
            )

        return {
            "success": True,
            "query": query,
            "results": formatted_results,
            "total_results": len(formatted_results),
            "connection_filter": connection_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search messages",
        )
