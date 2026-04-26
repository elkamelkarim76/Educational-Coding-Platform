"""
TAI Backend API - Programming Learning Platform
"""

import json
from fastapi import FastAPI, Depends, Query, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.schemas.schemas import (
    ExerciseFullCreate, TestRunRequest, CompileRequest, StudentSubmissionPayload,
    CourseCreate, UnitCreate, UnitUpdate, CourseUpdate, Exercise
)
from app.services.create_exercise import create_exercise, get_exercise_for_update, update_exercise
from app.services.compiler import compile_and_run_logic, compile_logic
from app.services.exercise_run import get_exercise_for_student, test_student_code
from app.services.info_navigation import get_all_units, get_unit_structure
from app.services.unit_update import (
    create_course, delete_course, delete_exercise,
    create_unit, update_unit, delete_unit, update_course
)
from app.services.chat import (
    manager, get_or_create_room, save_message, get_room_history, serialize_message
)
from app.db.database import get_db, SessionLocal

app = FastAPI(
    title="TAI Programming Platform API",
    description="Backend API for a programming learning platform.",
    version="1.0.0"
)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:4200",
    "http://localhost:4200"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── UNIT ─────────────────────────────────────────────────────────────

@app.post("/create-unit")
def create_unit_endpoint(unit_data: UnitCreate, db: Session = Depends(get_db)):
    return create_unit(unit_data, db)

@app.put("/unit/{unit_id}")
def update_unit_endpoint(unit_id: int, update_data: UnitUpdate, db: Session = Depends(get_db)):
    return update_unit(unit_id, update_data, db)

@app.delete("/unit/{unit_id}")
def delete_unit_endpoint(unit_id: int, db: Session = Depends(get_db)):
    delete_unit(unit_id, db)
    return None


# ── COURSE ───────────────────────────────────────────────────────────

@app.post("/create-course")
def create_course_endpoint(course_data: CourseCreate, db: Session = Depends(get_db)):
    return create_course(course_data, db)

@app.delete("/course/{course_id}")
def delete_course_endpoint(course_id: int, db: Session = Depends(get_db)):
    delete_course(course_id, db)
    return None

@app.put("/course/{course_id}")
def update_course_endpoint(course_id: int, update_data: CourseUpdate, db: Session = Depends(get_db)):
    return update_course(course_id, update_data, db)


# ── EXERCISE (TEACHER) ───────────────────────────────────────────────

@app.post("/exercises")
def create_exercise_endpoint(exercise_data: ExerciseFullCreate, db: Session = Depends(get_db)):
    return create_exercise(exercise_data, db)

@app.delete("/exercise/{exercise_id}")
def delete_exercise_endpoint(exercise_id: int, db: Session = Depends(get_db)):
    delete_exercise(exercise_id, db)
    return None

@app.get("/update/exercise/{exercise_id}")
def get_exercise_for_teacher_endpoint(exercise_id: int, db: Session = Depends(get_db)):
    return get_exercise_for_update(exercise_id, db)

@app.put("/exercise/{exercise_id}")
def update_exercise_endpoint(exercise_data: Exercise, db: Session = Depends(get_db)):
    return update_exercise(exercise_data, db)

@app.post("/run_test")
async def test_exercise_endpoint(request: TestRunRequest):
    return await compile_and_run_logic(request.files, request.language, request.argv)

@app.post("/compilation")
async def compilation_teacher_code_endpoint(request: CompileRequest):
    return await compile_logic(request.files, request.language)


# ── EXERCISE (STUDENT) ───────────────────────────────────────────────

@app.get("/student/unit/{unit_id}/course/{course_id}/exercise/{exercise_id}")
def get_exercise_student_endpoint(unit_id: int, course_id: int, exercise_id: int, db: Session = Depends(get_db)):
    return get_exercise_for_student(unit_id, course_id, exercise_id, db)

@app.post("/student/unit/{unit_id}/course/{course_id}/exercise/{exercise_id}")
async def test_student_code_endpoint(exercise_id: int, payload: StudentSubmissionPayload, db: Session = Depends(get_db)):
    return await test_student_code(db, exercise_id, payload)


# ── NAVIGATION ───────────────────────────────────────────────────────

@app.get("/units")
def get_all_units_summary(user_id: int, db: Session = Depends(get_db)):
    return get_all_units(user_id, db)

@app.get("/unit/{unit_id}/courses")
def get_unit_courses_and_exercises(unit_id: int, user_id: int, db: Session = Depends(get_db)):
    return get_unit_structure(unit_id, user_id, db)

@app.get("/")
def root():
    return {"message": "Hello World Docker"}


# ── CHAT ─────────────────────────────────────────────────────────────

@app.get("/chat/exercise/{exercise_id}/history")
def get_chat_history(exercise_id: int, db: Session = Depends(get_db)):
    """Retourne les 50 derniers messages du salon de l'exercice."""
    room = get_or_create_room(exercise_id, db)
    messages = get_room_history(room.id, db)
    return {
        "room_id": room.id,
        "exercise_id": exercise_id,
        "messages": [serialize_message(m) for m in messages],
    }


@app.websocket("/ws/chat/{exercise_id}/{user_id}")
async def websocket_chat(websocket: WebSocket, exercise_id: int, user_id: int):
    """Connexion WebSocket temps réel pour le chat d'un exercice."""
    db: Session = SessionLocal()
    try:
        room = get_or_create_room(exercise_id, db)
        await manager.connect(websocket, room.id)

        # Envoyer l'historique au client dès la connexion
        history = get_room_history(room.id, db)
        await websocket.send_text(json.dumps({
            "type": "history",
            "messages": [serialize_message(m) for m in history],
        }, default=str))

        # Boucle d'écoute
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            content = payload.get("content", "").strip()
            if not content:
                continue
            msg = save_message(room.id, user_id, content, db)
            db.refresh(msg)
            await manager.broadcast(room.id, {
                "type": "message",
                **serialize_message(msg),
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket, room.id)
    finally:
        db.close()


# ── CHAT SSE (nouvelles routes) ───────────────────────────────────────

from fastapi.responses import StreamingResponse
from app.services.chat_service import get_recent_messages, post_message, sse_stream
from app.schemas.chat_schemas import ChatMessageCreate

@app.get("/chat/{exercise_id}/messages")
def get_chat_messages(exercise_id: int, db: Session = Depends(get_db)):
    return get_recent_messages(exercise_id, db)

@app.post("/chat/{exercise_id}/messages")
async def send_chat_message(exercise_id: int, payload: ChatMessageCreate, db: Session = Depends(get_db)):
    return await post_message(exercise_id, payload, db)

@app.get("/chat/{exercise_id}/stream")
async def stream_chat(exercise_id: int, db: Session = Depends(get_db)):
    return StreamingResponse(
        sse_stream(exercise_id, db),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
