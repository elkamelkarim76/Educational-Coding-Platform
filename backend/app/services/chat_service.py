import asyncio
import json
from collections import defaultdict
from sqlalchemy.orm import Session
from app.db.models import ChatRoomModel, ChatMessageModel
from datetime import datetime

# subscribers par room
_subscribers = defaultdict(list)


def get_or_create_room(exercise_id: int, db: Session):
    room = db.query(ChatRoomModel).filter_by(exercise_id=exercise_id).first()
    if not room:
        room = ChatRoomModel(exercise_id=exercise_id)
        db.add(room)
        db.commit()
        db.refresh(room)
    return room


def get_recent_messages(exercise_id: int, db: Session):
    room = get_or_create_room(exercise_id, db)
    messages = (
        db.query(ChatMessageModel)
        .filter_by(room_id=room.id)
        .order_by(ChatMessageModel.id.asc())
        .all()
    )
    return [
        {
            "id": m.id,
            "room_id": m.room_id,
            "user_id": m.user_id,
            "username": f"user_{m.user_id}",
            "content": m.content,
            "created_at": m.sent_at.isoformat(),
        }
        for m in messages
    ]


async def post_message(exercise_id: int, payload, db: Session):
    room = get_or_create_room(exercise_id, db)

    message = ChatMessageModel(
    room_id=room.id,
    user_id=payload.user_id,
    content=payload.content,
    sent_at=datetime.utcnow()   
)
    db.add(message)
    db.commit()
    db.refresh(message)

    data = {
        "id": message.id,
        "room_id": message.room_id,
        "user_id": message.user_id,
        "username": f"user_{message.user_id}",
        "content": message.content,
        "created_at": message.sent_at.isoformat(),
    }

    # notifier tous les abonnés
    for queue in _subscribers[room.id]:
        await queue.put(data)

    return data


async def sse_stream(exercise_id: int, db: Session):
    room = get_or_create_room(exercise_id, db)
    queue = asyncio.Queue()
    _subscribers[room.id].append(queue)

    try:
        while True:
            try:
                data = await asyncio.wait_for(queue.get(), timeout=15)
                yield f"data: {json.dumps(data)}\n\n"
            except asyncio.TimeoutError:
                yield "data: ping\n\n"
    finally:
        _subscribers[room.id].remove(queue)
