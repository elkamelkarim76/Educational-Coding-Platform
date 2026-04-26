"""
TAI Backend API - Programming Learning Platform

This module defines all FastAPI routes for the TAI platform where teachers
create coding exercises and students submit solutions for automated testing.
"""
from app.services.analytics import get_exercise_analytics
from fastapi import FastAPI, Depends, Query, status
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
from app.db.database import get_db

# Create all the table if it's the first time c
#models.Base.metadata.create_all(bind=engine) used before alembic, now it's alembic which will configure the db


app = FastAPI(
    title="TAI Programming Platform API",
    description="Backend API for a programming learning platform where teachers create exercises and students submit solutions for automated testing.",
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


# Endpoints related to a unit 

@app.post("/create-unit")
def create_unit_endpoint(unit_data: UnitCreate, db: Session = Depends(get_db)):
    """Create a new unit"""
    result = create_unit(unit_data, db)
    return result


@app.put("/unit/{unit_id}")
def update_unit_endpoint(unit_id: int, update_data: UnitUpdate, db: Session = Depends(get_db)):
    """Update an existing unit"""
    result = update_unit(unit_id, update_data, db)
    return result


@app.delete("/unit/{unit_id}")
def delete_unit_endpoint(unit_id: int, db: Session = Depends(get_db)):
    """Delete a unit and all its children (courses, exercises)."""
    delete_unit(unit_id, db)
    return None

@app.get("/analytics/exercises")
def get_analytics_endpoint(db: Session = Depends(get_db)):
    """Retourne les vraies stats agrégées par exercice."""
    return get_exercise_analytics(db)

# Endpoints related to a course 

@app.post("/create-course")
def create_course_endpoint(course_data: CourseCreate, db: Session = Depends(get_db)):
    """Create a new course within a unit."""
    print(course_data)
    result = create_course(course_data, db)
    return result


@app.delete("/course/{course_id}")
def delete_course_endpoint(course_id: int, db: Session = Depends(get_db)):
    """Delete a course and all its exercises."""
    delete_course(course_id, db)
    return None


@app.put("/course/{course_id}")
def update_course_endpoint(course_id: int, update_data: CourseUpdate, db: Session = Depends(get_db)):
    """Update an existing course"""
    result = update_course(course_id, update_data, db)
    return result

# Endpoints teacher  exercise
  
@app.post("/exercises")
def create_exercise_endpoint(exercise_data: ExerciseFullCreate, db : Session = Depends(get_db)):
    """ Route call after the teacher use the button 'VALIDER'. """
    print(exercise_data)
    result = create_exercise(exercise_data, db)
    return result

@app.delete("/exercise/{exercise_id}")
def delete_exercise_endpoint(exercise_id: int, db: Session = Depends(get_db)):
    """Delete an exercise and all its components."""
    delete_exercise(exercise_id, db)
    return None


@app.get("/update/exercise/{exercise_id}")
def get_exercise_for_teacher_endpoint(exercise_id: int, db: Session = Depends(get_db)):
    """Get full exercise with reconstructed files (markers included) for teacher editing."""
    result = get_exercise_for_update(exercise_id, db)
    return result


@app.put("/exercise/{exercise_id}")
def update_exercise_endpoint(exercise_data: Exercise, db: Session = Depends(get_db)):
    """Full update of an exercise (replaces files, tests, hints)."""
    print(exercise_data)
    result = update_exercise(exercise_data, db)
    return result


# Endpoint use for teacher testing  (Compile & Run)

@app.post("/run_test")
async def test_exercise_endpoint(request: TestRunRequest):
    """Compile and run code with test arguments (used by teacher to test exercises)."""
    result = await compile_and_run_logic(request.files, request.language, request.argv)
    return result


@app.post("/compilation")
async def compilation_teacher_code_endpoint(request: CompileRequest):
    """Compile code without execution (used by teacher to check for errors)."""
    print(request)
    result = await compile_logic(request.files, request.language)
    return result





# Endpoint for student 

@app.get("/student/unit/{unit_id}/course/{course_id}/exercise/{exercise_id}")
def get_exercise_student_endpoint(
    unit_id: int,
    course_id: int,
    exercise_id: int,
    db: Session = Depends(get_db)
):
    """Get an exercise for a student (with TODO placeholders instead of solutions)."""
    exercise = get_exercise_for_student(unit_id, course_id, exercise_id, db)
    return exercise


@app.post("/student/unit/{unit_id}/course/{course_id}/exercise/{exercise_id}")
async def test_student_code_endpoint(
    exercise_id: int,
    payload: StudentSubmissionPayload,
    db: Session = Depends(get_db)
):
    """Submit student solution for testing and grading."""
    results = await test_student_code(db, exercise_id, payload)
    return results


# Navigation Endpoints (Dashboard, unit page and side navigation panel in exercise-run)

@app.get("/units")
def get_all_units_summary(user_id: int, db: Session = Depends(get_db)):
    """Get a summary of all units for the dashboard."""
    results = get_all_units(user_id, db)
    return results


@app.get("/unit/{unit_id}/courses")
def get_unit_courses_and_exercises(
    unit_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get the structure of a unit with all its courses and exercises."""
    print("test")
    results = get_unit_structure(unit_id, user_id, db)
    return results

@app.get("/")
def root():
    return {"message": "Hello World Docker"}
