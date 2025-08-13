"""
Messages API Router - Phase 4 Real-time Messaging
Soul-themed messaging with emotional context and real-time delivery
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User, UserEmotionalState
from app.services.message_service import get_message_service

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
    emotional_state: str
    message_energy: str
    is_soul_revelation: bool
    is_read: bool
    created_at: str
    read_at: Optional[str]
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
    db: Session = Depends(get_db)
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
            db=db
        )
        
        return SendMessageResponse(
            success=result.success,
            message_id=result.message_id,
            message=result.message,
            delivered=result.delivered,
            error=result.error
        )
        
    except Exception as e:
        logger.error(f"Error in send message endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )


@router.get("/conversation/{connection_id}")
async def get_conversation_messages(
    connection_id: int,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
            db=db
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve messages"
        )


@router.get("/conversations")
async def get_user_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all conversations for the current user with summary information
    """
    try:
        result = await message_service.get_user_conversations(
            user_id=current_user.id,
            db=db
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user conversations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversations"
        )


@router.post("/typing-status")
async def update_typing_status(
    typing_data: TypingStatusRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
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
            db=db
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found or access denied"
            )
        
        return {
            "success": True,
            "message": "Typing status updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating typing status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update typing status"
        )


@router.post("/mark-read/{connection_id}")
async def mark_messages_as_read(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark all messages in a connection as read
    """
    try:
        success = await message_service.mark_messages_as_read(
            user_id=current_user.id,
            connection_id=connection_id,
            db=db
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Connection not found or access denied"
            )
        
        return {
            "success": True,
            "message": "Messages marked as read"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking messages as read: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark messages as read"
        )


@router.get("/statistics")
async def get_message_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get messaging statistics for the current user
    """
    try:
        from app.models.message import Message
        from app.models.soul_connection import SoulConnection
        from sqlalchemy import func, or_
        
        # Get user's total messages sent
        total_sent = db.query(Message).filter(
            Message.sender_id == current_user.id
        ).count()
        
        # Get user's total messages received
        user_connections = db.query(SoulConnection).filter(
            or_(
                SoulConnection.user1_id == current_user.id,
                SoulConnection.user2_id == current_user.id
            )
        ).all()
        
        connection_ids = [c.id for c in user_connections]
        total_received = db.query(Message).filter(
            Message.connection_id.in_(connection_ids),
            Message.sender_id != current_user.id
        ).count() if connection_ids else 0
        
        # Get unread messages count
        unread_count = db.query(Message).filter(
            Message.connection_id.in_(connection_ids),
            Message.sender_id != current_user.id,
            Message.is_read == False
        ).count() if connection_ids else 0
        
        # Get active conversations count
        active_conversations = len([c for c in user_connections if c.status == "active"])
        
        # Get most used emotional states
        emotional_states = db.query(
            Message.emotional_state,
            func.count(Message.id).label('count')
        ).filter(
            Message.sender_id == current_user.id
        ).group_by(Message.emotional_state).order_by(
            func.count(Message.id).desc()
        ).limit(5).all()
        
        return {
            "success": True,
            "statistics": {
                "messages": {
                    "sent": total_sent,
                    "received": total_received,
                    "unread": unread_count
                },
                "conversations": {
                    "active": active_conversations,
                    "total": len(user_connections)
                },
                "emotional_patterns": [
                    {"state": state, "count": count} 
                    for state, count in emotional_states
                ]
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting message statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get statistics"
        )


@router.get("/search")
async def search_messages(
    query: str = Query(..., min_length=1),
    connection_id: Optional[int] = Query(None),
    limit: int = Query(default=20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search messages by content with optional connection filtering
    """
    try:
        from app.models.message import Message
        from app.models.soul_connection import SoulConnection
        from sqlalchemy import or_, and_
        
        # Get user's accessible connections
        user_connections = db.query(SoulConnection.id).filter(
            or_(
                SoulConnection.user1_id == current_user.id,
                SoulConnection.user2_id == current_user.id
            )
        ).subquery()
        
        # Base query for messages user can access
        base_query = db.query(Message).filter(
            Message.connection_id.in_(user_connections)
        )
        
        # Add connection filter if specified
        if connection_id:
            # Verify user has access to this connection
            connection = db.query(SoulConnection).filter(
                SoulConnection.id == connection_id,
                or_(
                    SoulConnection.user1_id == current_user.id,
                    SoulConnection.user2_id == current_user.id
                )
            ).first()
            
            if not connection:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Connection not found or access denied"
                )
            
            base_query = base_query.filter(Message.connection_id == connection_id)
        
        # Search in message content (case-insensitive)
        search_results = base_query.filter(
            Message.content.ilike(f"%{query}%")
        ).order_by(Message.created_at.desc()).limit(limit).all()
        
        # Format results
        formatted_results = []
        for message in search_results:
            # Get sender info
            sender = db.query(User).filter(User.id == message.sender_id).first()
            
            formatted_results.append({
                "id": message.id,
                "connection_id": message.connection_id,
                "sender": {
                    "id": message.sender_id,
                    "name": f"{sender.first_name} {sender.last_name}" if sender else "Unknown",
                    "is_current_user": message.sender_id == current_user.id
                },
                "content": message.content,
                "emotional_state": message.emotional_state,
                "created_at": message.created_at.isoformat(),
                "match_context": self._get_match_context(message.content, query)
            })
        
        return {
            "success": True,
            "query": query,
            "results": formatted_results,
            "total_results": len(formatted_results),
            "connection_filter": connection_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search messages"
        )

    def _get_match_context(self, content: str, query: str, context_chars: int = 50) -> str:
        """Get context around search match"""
        try:
            query_lower = query.lower()
            content_lower = content.lower()
            
            start_idx = content_lower.find(query_lower)
            if start_idx == -1:
                return content[:100] + "..." if len(content) > 100 else content
            
            # Get context around the match
            context_start = max(0, start_idx - context_chars)
            context_end = min(len(content), start_idx + len(query) + context_chars)
            
            context = content[context_start:context_end]
            
            # Add ellipsis if truncated
            if context_start > 0:
                context = "..." + context
            if context_end < len(content):
                context = context + "..."
            
            return context
            
        except Exception:
            return content[:100] + "..." if len(content) > 100 else content