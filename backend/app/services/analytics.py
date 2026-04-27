from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models import (
    ExerciseModel, ExerciseProgressModel,
    SubmissionHistoryModel, HintViewModel, CourseModel, UnitModel
)
from app.core.enums import SubmissionStatus

def get_exercise_analytics(db: Session):
    """
    Pour chaque exercice, retourne les vraies stats agrégées
    depuis submission_history, exercise_progress et hint_view.
    """
    exercises = db.query(ExerciseModel).all()
    results = []

    for ex in exercises:
        # Nombre total de soumissions pour cet exercice (tous étudiants)
        total = db.query(func.count(SubmissionHistoryModel.id))\
            .filter(SubmissionHistoryModel.exercise_id == ex.id)\
            .scalar() or 0

        # Nombre de soumissions réussies
        success = db.query(func.count(SubmissionHistoryModel.id))\
            .filter(
                SubmissionHistoryModel.exercise_id == ex.id,
                SubmissionHistoryModel.status == SubmissionStatus.SUCCESS
            ).scalar() or 0

        # Moyenne des tentatives par étudiant
        avg_try = db.query(func.avg(ExerciseProgressModel.attempts_count))\
            .filter(ExerciseProgressModel.exercise_id == ex.id)\
            .scalar() or 0

        # Nombre total de consultations d'indices
        hints = db.query(func.count(HintViewModel.id))\
            .join(HintViewModel.hint)\
            .filter_by(exercise_id=ex.id)\
            .scalar() or 0

        results.append({
            "id":          ex.id,
            "name":        ex.name,
            "courseName":  ex.course.name,
            "unitName":    ex.course.unit.name,
            "lang":        ex.language.value,
            "attempts":    total,
            "success":     success,
            "avgTry":      round(float(avg_try), 1),
            "hints":       hints,
        })

    return results