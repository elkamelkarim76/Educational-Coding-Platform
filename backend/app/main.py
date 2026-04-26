"""
TAI Backend API - Programming Learning Platform
"""

from fastapi import FastAPI, Depends, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import UserModel

from app.schemas.schemas import (
    RegisterRequest, LoginRequest, TokenResponse, CurrentUserResponse,
    ExerciseFullCreate, TestRunRequest, CompileRequest, StudentSubmissionPayload,
    CourseCreate, UnitCreate, UnitUpdate, CourseUpdate, Exercise
)

from app.core.security import hash_password, verify_password, create_access_token
from app.core.dependencies import get_current_user, require_teacher

from app.services.create_exercise import (
    create_exercise,
    get_exercise_for_update,
    update_exercise
)

from app.services.compiler import compile_and_run_logic, compile_logic
from app.services.exercise_run import get_exercise_for_student, test_student_code
from app.services.info_navigation import get_all_units, get_unit_structure

from app.services.unit_update import (
    create_course,
    delete_course,
    delete_exercise,
    create_unit,
    update_unit,
    delete_unit,
    update_course
)


app = FastAPI()


# CORS (déjà existant)
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


# =========================
# AUTH
# =========================

@app.post("/register", response_model=CurrentUserResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):

    existing_user = db.query(UserModel).filter(UserModel.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already used")

    # mot de passe hashé
    new_user = UserModel(
        firstname=payload.firstname,
        lastname=payload.lastname,
        email=payload.email,
        mdp_hash=hash_password(payload.password),
        role=payload.role,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@app.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):

    user = db.query(UserModel).filter(UserModel.email == payload.email).first()

    if user is None or not verify_password(payload.password, user.mdp_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # création du token JWT
    token = create_access_token(user.id, str(user.role))

    return {"access_token": token, "token_type": "bearer"}


@app.get("/me", response_model=CurrentUserResponse)
def me(current_user: UserModel = Depends(get_current_user)):
    # récupération user via token
    return current_user


# =========================
# UNIT (SÉCURISÉ)
# =========================

@app.post("/create-unit")
def create_unit_endpoint(
    unit_data: UnitCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_teacher)  # réservé teacher
):
    return create_unit(unit_data, current_user.id, db)


@app.put("/unit/{unit_id}")
def update_unit_endpoint(
    unit_id: int,
    update_data: UnitUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_teacher)
):
    return update_unit(unit_id, update_data, current_user.id, db)


@app.delete("/unit/{unit_id}")
def delete_unit_endpoint(
    unit_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_teacher)
):
    delete_unit(unit_id, current_user.id, db)
    return None


# =========================
# COURSE (SÉCURISÉ)
# =========================

@app.post("/create-course")
def create_course_endpoint(
    course_data: CourseCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_teacher)
):
    return create_course(course_data, current_user.id, db)


@app.put("/course/{course_id}")
def update_course_endpoint(
    course_id: int,
    update_data: CourseUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_teacher)
):
    return update_course(course_id, update_data, current_user.id, db)


@app.delete("/course/{course_id}")
def delete_course_endpoint(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_teacher)
):
    delete_course(course_id, current_user.id, db)
    return None


# =========================
# EXERCISE (SÉCURISÉ)
# =========================

@app.post("/exercises")
def create_exercise_endpoint(
    exercise_data: ExerciseFullCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_teacher)
):
    return create_exercise(exercise_data, db)


@app.delete("/exercise/{exercise_id}")
def delete_exercise_endpoint(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_teacher)
):
    delete_exercise(exercise_id, current_user.id, db)
    return None


@app.get("/update/exercise/{exercise_id}")
def get_exercise_for_teacher_endpoint(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_teacher)
):
    return get_exercise_for_update(exercise_id, db)


@app.put("/exercise/{exercise_id}")
def update_exercise_endpoint(
    exercise_data: Exercise,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_teacher)
):
    return update_exercise(exercise_data, db)


# =========================
# TEACHER TEST (SÉCURISÉ)
# =========================

@app.post("/run_test")
async def test_exercise_endpoint(
    request: TestRunRequest,
    current_user: UserModel = Depends(require_teacher)
):
    return await compile_and_run_logic(request.files, request.language, request.argv)


@app.post("/compilation")
async def compilation_teacher_code_endpoint(
    request: CompileRequest,
    current_user: UserModel = Depends(require_teacher)
):
    return await compile_logic(request.files, request.language)


# =========================
# STUDENT (SÉCURISÉ)
# =========================

@app.get("/student/unit/{unit_id}/course/{course_id}/exercise/{exercise_id}")
def get_exercise_student_endpoint(
    unit_id: int,
    course_id: int,
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)  # connecté obligatoire
):
    return get_exercise_for_student(unit_id, course_id, exercise_id, db)


@app.post("/student/unit/{unit_id}/course/{course_id}/exercise/{exercise_id}")
async def test_student_code_endpoint(
    exercise_id: int,
    payload: StudentSubmissionPayload,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    # user_id vient du token, pas du frontend
    return await test_student_code(db, exercise_id, payload, current_user.id)


# =========================
# NAVIGATION
# =========================

@app.get("/units")
def get_all_units_summary(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    return get_all_units(current_user.id, db)


@app.get("/unit/{unit_id}/courses")
def get_unit_courses_and_exercises(
    unit_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    return get_unit_structure(unit_id, current_user.id, db)


@app.get("/")
def root():
    return {"message": "Hello World"}