from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ....core.database import get_db
from ....models.user import User
from ....models.soul_connection import SoulConnection
from ....models.message import Message, MessageType
from ....api.v1.deps import get_current_user
from ....services.realtime import manager


router = APIRouter()


class SendMessageRequest(BaseModel):
    receiver_id: int
    content: str
    message_type: MessageType = MessageType.TEXT


def _find_connection(
    db: Session, current_user_id: int, other_user_id: int
) -> Optional[SoulConnection]:
    return (
        db.query(SoulConnection)
        .filter(
            ((SoulConnection.user1_id == current_user_id) &
             (SoulConnection.user2_id == other_user_id))
            |
            ((SoulConnection.user1_id == other_user_id) &
             (SoulConnection.user2_id == current_user_id))
        )
        .first()
    )


@router.get("/chat/{user_id}")
def get_chat_messages(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    connection = _find_connection(db, current_user.id, user_id)
    if connection is None:
        raise HTTPException(status_code=404, detail="Connection not found")

    if current_user.id not in {connection.user1_id, connection.user2_id}:
        raise HTTPException(
            status_code=403, detail="Not authorized for this connection"
        )

    messages = (
        db.query(Message)
        .filter(Message.connection_id == connection.id)
        .order_by(Message.created_at.asc())
        .all()
    )
    return [
        {
            "id": m.id,
            "senderId": m.sender_id,
            "content": m.message_text,
            "timestamp": m.created_at.isoformat(),
            "isRead": m.is_read,
            "type": m.message_type,
        }
        for m in messages
    ]


@router.post("/chat/send")
def send_message(
    payload: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    connection = _find_connection(db, current_user.id, payload.receiver_id)
    if connection is None:
        raise HTTPException(status_code=404, detail="Connection not found")

    if current_user.id not in {connection.user1_id, connection.user2_id}:
        raise HTTPException(
            status_code=403, detail="Not authorized for this connection"
        )

    message = Message(
        connection_id=connection.id,
        sender_id=current_user.id,
        message_text=payload.content,
        message_type=payload.message_type,
        created_at=datetime.utcnow(),
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    response = {
        "id": message.id,
        "senderId": message.sender_id,
        "content": message.message_text,
        "timestamp": message.created_at.isoformat(),
        "isRead": message.is_read,
        "type": message.message_type,
    }

    # Broadcast to all WS clients (basic MVP)
    try:
        import asyncio
        asyncio.create_task(
            manager.broadcast(
                {
                    "type": "message",
                    "data": response,
                    "timestamp": int(datetime.utcnow().timestamp() * 1000),
                }
            )
        )
    except RuntimeError:
        # No running loop in this context; fire-and-forget best-effort
        pass

    return response


@router.post("/chat/{user_id}/read")
def mark_read(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    connection = _find_connection(db, current_user.id, user_id)
    if connection is None:
        raise HTTPException(status_code=404, detail="Connection not found")

    if current_user.id not in {connection.user1_id, connection.user2_id}:
        raise HTTPException(
            status_code=403, detail="Not authorized for this connection"
        )

    db.query(Message).filter(
        Message.connection_id == connection.id,
        Message.sender_id != current_user.id,
    ).update({Message.is_read: True})
    db.commit()

    return {"status": "ok"}


# WebSocket endpoint mounted via FastAPI app (defined in main using app.mount)
@router.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo through broadcast for connected peers
            await manager.send_to_all_except({
                "type": "event",
                "data": data
            }, except_ws=websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
