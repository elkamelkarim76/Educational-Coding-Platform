"""
Unit and Course C"R"UD service.

This module provides create, update, and delete methods for
units, courses, and exercises.
"""

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import UnitModel, CourseModel, ExerciseModel
from app.schemas.schemas import (
    UnitSummary, CourseNav,
    CourseCreate, UnitCreate, UnitUpdate, CourseUpdate
)


# Course methods

def create_course(course_data: CourseCreate, author_id: int, db: Session) -> CourseNav:
    unit = db.query(UnitModel).filter(UnitModel.id == course_data.unit_id).first()
    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    if unit.author_id != author_id:
        raise HTTPException(
           status_code=status.HTTP_403_FORBIDDEN,
           detail="You cannot add a course to another teacher's unit"
    )

    # Find max position and increment
    max_position = db.query(func.max(CourseModel.position))\
        .filter(CourseModel.unit_id == course_data.unit_id)\
        .scalar()

    new_position = (max_position + 1) if max_position is not None else 1

    # Create course record
    new_course_db = CourseModel(
        name=course_data.name,
        description=course_data.description,
        unit_id=course_data.unit_id,
        difficulty=course_data.difficulty,
        visibility=course_data.visibility,
        position=new_position
    )

    db.add(new_course_db)
    db.commit()
    db.refresh(new_course_db)

    return CourseNav(
        id=new_course_db.id,
        name=new_course_db.name,
        description=new_course_db.description,
        visibility=new_course_db.visibility,
        difficulty=new_course_db.difficulty,
        position=new_course_db.position,
        author_id=unit.author_id,
        exercises=[]
    )


def delete_course(course_id: int, author_id: int, db: Session) -> None:
    """
    Delete a course and all its exercises.
    """
    course = db.query(CourseModel).filter(CourseModel.id == course_id).first()

    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    unit = db.query(UnitModel).filter(UnitModel.id == course.unit_id).first()

    if unit.author_id != author_id:
        raise HTTPException(
           status_code=status.HTTP_403_FORBIDDEN,
           detail="You cannot delete another teacher's course"
    )

    db.delete(course)
    db.commit()

    return None


def update_course(course_id: int, update_data: CourseUpdate, author_id: int, db: Session) -> CourseNav:
    """
    Update an existing course (partial update supported).
    """
    course = db.query(CourseModel).filter(CourseModel.id == course_id).first()

    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    unit = db.query(UnitModel).filter(UnitModel.id == course.unit_id).first()

    if unit.author_id != author_id:
        raise HTTPException(
           status_code=status.HTTP_403_FORBIDDEN,
           detail="You cannot update another teacher's course"
    )

    # Only update provided fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        if value is not None:
            setattr(course, field, value)

    db.commit()
    db.refresh(course)

    # Get unit for author_id

    return CourseNav(
        id=course.id,
        name=course.name,
        description=course.description,
        visibility=course.visibility,
        difficulty=course.difficulty,
        position=course.position,
        author_id=unit.author_id if unit else 0,
        exercises=[]
    )


# Exercise methods

def delete_exercise(exercise_id: int, db: Session) -> None:
    """
    Delete an exercise and all its components.
    Cascade delete removes files, markers, tests, hints, and submissions.
    """
    exercise = db.query(ExerciseModel).filter(ExerciseModel.id == exercise_id).first()

    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")

    db.delete(exercise)
    db.commit()

    return None


# Unit methods

def create_unit(unit_data: UnitCreate, author_id: int, db: Session) -> UnitSummary:
    new_unit_db = UnitModel(
        name=unit_data.name,
        description=unit_data.description,
        difficulty=unit_data.difficulty,
        visibility=unit_data.visibility,
        author_id=author_id
    )

    db.add(new_unit_db)
    db.commit()
    db.refresh(new_unit_db)

    return UnitSummary(
        id=new_unit_db.id,
        name=new_unit_db.name,
        description=new_unit_db.description,
        visibility=new_unit_db.visibility,
        difficulty=new_unit_db.difficulty,
        author_id=new_unit_db.author_id
    )

def update_unit(unit_id: int, update_data: UnitUpdate, author_id: int, db: Session) -> UnitSummary:
    """
    Update an existing unit (partial update supported).
    """
    unit = db.query(UnitModel).filter(UnitModel.id == unit_id).first()

    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    if unit.author_id != author_id:
        raise HTTPException(
           status_code=status.HTTP_403_FORBIDDEN,
           detail="You cannot update another teacher's unit"
    )
    # Only update provided fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        if value is not None:
            setattr(unit, field, value)

    db.commit()
    db.refresh(unit)

    return UnitSummary(
        id=unit.id,
        name=unit.name,
        description=unit.description,
        visibility=unit.visibility,
        difficulty=unit.difficulty,
        author_id=unit.author_id
    )


def delete_unit(unit_id: int, author_id: int, db: Session) -> None:
    """
    Delete a unit and all its children.
    Cascade delete removes all courses, exercises, and related data.
    """
    unit = db.query(UnitModel).filter(UnitModel.id == unit_id).first()

    if not unit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unit not found")
    if unit.author_id != author_id:
        raise HTTPException(
           status_code=status.HTTP_403_FORBIDDEN,
           detail="You cannot delete another teacher's unit"
    )
    db.delete(unit)
    db.commit()

    return None



