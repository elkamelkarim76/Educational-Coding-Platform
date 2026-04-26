import json
from typing import Dict, List
from fastapi import WebSocket
from sqlalchemy.orm import Session
from app.db.models import ChatRoomModel, ChatMessageModel
from app.db.database import SessionLocal

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: int):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: int):
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast(self, room_id: int, message: dict):
        if room_id in self.active_connections:
            payload = json.dumps(message, default=str)
            for connection in self.active_connections[room_id]:
                await connection.send_text(payload)

manager = ConnectionManager()

def get_or_create_room(exercise_id: int, db: Session) -> ChatRoomModel:
    room = db.query(ChatRoomModel).filter(ChatRoomModel.exercise_id == exercise_id).first()
    if not room:
        room = ChatRoomModel(exercise_id=exercise_id)
        db.add(room)
        db.commit()
        db.refresh(room)
    return room

def save_message(room_id: int, user_id: int, content: str, db: Session) -> ChatMessageModel:
    msg = ChatMessageModel(room_id=room_id, user_id=user_id, content=content)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

def get_room_history(room_id: int, db: Session, limit: int = 50) -> list:
    return (
        db.query(ChatMessageModel)
        .filter(ChatMessageModel.room_id == room_id)
        .order_by(ChatMessageModel.sent_at.asc())
        .limit(limit)
        .all()
    )

def serialize_message(msg: ChatMessageModel) -> dict:
    return {
        "id": msg.id,
        "room_id": msg.room_id,
        "user_id": msg.user_id,
        "user_firstname": msg.user.firstname if msg.user else "Inconnu",
        "user_lastname": msg.user.lastname if msg.user else "",
        "content": msg.content,
        "sent_at": msg.sent_at.isoformat(),
    }
