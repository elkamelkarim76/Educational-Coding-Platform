"""
Student exercise service.

This module handles retrieving exercises for students and processing
their code submissions for automated testing and grading.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, selectinload, joinedload
from datetime import datetime

from app.db.models import (
    ExerciseModel, ExerciseFileModel, TestCaseModel, HintModel,
    CourseModel, SubmissionHistoryModel, SubmissionMarkerModel,
    SubmissionResultModel, ExerciseProgressModel
)
from app.schemas.schemas import ExerciseFull, File, Test, Hint, StudentSubmissionPayload, TestResult
from app.core.enums import Visibility, SubmissionStatus, ProgressStatus, TestStatus

from app.utils.parsing import extract_student_solutions, inject_markers_into_template, MarkerData
from app.services.compiler import compile_and_run_logics


# Shared helpers

def get_secure_exercise_or_404(db: Session, exercise_id: int) -> ExerciseModel:
    """
    Fetch exercise with all relationships, checking visibility permissions.
    Loads files (with markers), tests, hints, and parent course/unit in
    optimized queries using selectinload and joinedload.
    """
    exercise = (
        db.query(ExerciseModel)
        .options(
            # selectinload for one-to-many relationships (better performance)
            selectinload(ExerciseModel.files).selectinload(ExerciseFileModel.markers),
            selectinload(ExerciseModel.tests),
            selectinload(ExerciseModel.hints),
            # joinedload for many-to-one relationships
            joinedload(ExerciseModel.course).joinedload(CourseModel.unit)
        )
        .filter(ExerciseModel.id == exercise_id)
        .first()
    )

    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found"
        )

    # Check cascading visibility (exercise, course, or unit is private)
    is_private = (
        exercise.visibility == Visibility.PRIVATE or
        exercise.course.visibility == Visibility.PRIVATE or
        exercise.course.unit.visibility == Visibility.PRIVATE
    )

    if is_private:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Exercise, course, or unit is private"
        )

    return exercise


# Helpers for get_exercise_for_student

def format_files_for_student(sql_files: list[ExerciseFileModel]) -> list[File]:
    """
    Convert ExerciseFileModel objects to File schemas for students.
    """
    formatted_files = []

    for f in sql_files:
        # Students don't receive the main file directly
        if f.is_main:
            continue

        formatted_files.append(
            File(
                id=f.id,
                name=f.name,
                content=f.template_without_marker,
                extension=f.extension,
                is_main=f.is_main,
                editable=f.editable,
                position=f.position
            )
        )

    return formatted_files

def format_tests_for_student(sql_tests: list[TestCaseModel]) -> list[Test]:
    """Convert TestCaseModel objects to Test schemas."""
    formatted_tests = []
    for t in sql_tests:
        formatted_tests.append(
            Test(
                id=t.id,
                argv=t.argv,
                expected_output=t.expected_output,
                comment=t.comment or "",
                position=t.position
            )
        )
    return formatted_tests


def format_hints_for_student(sql_hints: list[HintModel]) -> list[Hint]:
    """Convert HintModel objects to Hint schemas."""
    formatted_hints = []
    for h in sql_hints:
        formatted_hints.append(
            Hint(
                id=h.id,
                body=h.body,
                unlock_after_attempts=h.unlock_after_attempts,
                position=h.position
            )
        )
    return formatted_hints


def get_exercise_for_student(unit_id: int, course_id: int, exercise_id: int, db: Session) -> dict:
    """
    Retrieve an exercise for a student with visibility checks.

    Returns the exercise with template files (TODO placeholders instead
    of solutions), test cases, and hints.

    """
    exercise = get_secure_exercise_or_404(db, exercise_id)

    exercise_detail = ExerciseFull(
        id=exercise.id,
        course_id=exercise.course_id,
        name=exercise.name,
        description=exercise.description,
        visibility=exercise.visibility,
        language=exercise.language,
        difficulty=exercise.difficulty,
        position=exercise.position,
        files=format_files_for_student(exercise.files),
        tests=format_tests_for_student(exercise.tests),
        hints=format_hints_for_student(exercise.hints)
    )

    print("ok")

    return {
        "status": True,
        "message": "Exercise found.",
        "data": exercise_detail.model_dump()
    }


# Helpers for test_student_code

def initialize_submission_history(db: Session, user_id: int, exercise_id: int) -> SubmissionHistoryModel:
    """
    Create a pending submission entry in the database.

    Uses flush() instead of commit() to generate the ID while keeping
    the transaction open for potential rollback.
    """
    submission = SubmissionHistoryModel(
        user_id=user_id,
        exercise_id=exercise_id,
        status=SubmissionStatus.PENDING
    )
    db.add(submission)
    db.flush()
    return submission


def update_student_progress(db: Session, user_id: int, exercise_id: int, is_success: bool) -> None:
    """
    Update or create the student's progress for this exercise.

    Increments attempt count and updates status to VALIDATED if all tests pass.
    """
    progress = db.query(ExerciseProgressModel).filter_by(
        user_id=user_id,
        exercise_id=exercise_id
    ).first()

    if not progress:
        progress = ExerciseProgressModel(
            user_id=user_id,
            exercise_id=exercise_id,
            status=ProgressStatus.IN_PROGRESS,
            attempts_count=0
        )
        db.add(progress)

    progress.attempts_count += 1
    progress.last_activity = datetime.now()

    if is_success:
        progress.status = ProgressStatus.VALIDATED


def process_and_save_markers(
    db: Session,
    submission_id: int,
    payload_files: list[File],
    teacher_files: list[ExerciseFileModel]
) -> list[MarkerData]:
    """
    Extract student solutions from TODO markers and save to database.

    Validates that all expected markers are present in the student's code.
    """
    all_markers: list[MarkerData] = []

    for student_file in payload_files:
        # Find the corresponding teacher file
        teacher_file = next((f for f in teacher_files if f.id == student_file.id), None)

        # Get expected marker IDs for validation
        expected_ids = [m.marker_id for m in teacher_file.markers]

        markers = extract_student_solutions(student_file.content, student_file.extension, expected_ids)
        all_markers.extend(markers)

        for m in markers:
            db.add(SubmissionMarkerModel(
                submission_id=submission_id,
                exercise_file_id=student_file.id,
                marker_id=m.id,
                content=m.content
            ))
    return all_markers


def reconstruct_files_for_compilation(
    exercise_files: list[ExerciseFileModel],
    student_markers: list[MarkerData]
) -> list[File]:
    """
    Merge student solutions into teacher templates for compilation.

    Main and non-editable files keep their original content.
    Editable files have student code injected into TODO sections.
    """
    files_to_compile: list[File] = []

    for tf in exercise_files:
        if tf.is_main or not tf.editable:
            # Main and non-editable files don't have markers
            final_content = tf.template_without_marker
        else:
            # Inject student code into the template
            final_content = inject_markers_into_template(
                tf.template_without_marker,
                student_markers,
                tf.extension
            )

        files_to_compile.append(File(
            id=tf.id,
            name=tf.name,
            content=final_content,
            extension=tf.extension,
            is_main=tf.is_main,
            editable=tf.editable,
            position=tf.position
        ))

    return files_to_compile


def grade_submission(
    db: Session,
    submission_id: int,
    exec_results: list[dict],
    tests: list[TestCaseModel]
) -> tuple[bool, list[TestResult]]:
    """
    Grade execution results by comparing with expected outputs.

    Compares stdout with expected output for each test case,
    saves results to database, and returns formatted results.
    """
    test_responses_list: list[TestResult] = []
    global_success = True

    for i, result in enumerate(exec_results):
        test_case = tests[i]

        print("test result", result)

        # Extract and clean output data
        student_output = (result["data"]["stdout"] or "").strip()
        expected_output = (test_case.expected_output or "").strip()
        error_log = result["data"]["stderr"]
        exit_code = result["data"]["exit_code"]

        # Determine if test passed: exit code 0 and output matches
        is_success = (exit_code == 0) and (student_output == expected_output)

        if not is_success:
            global_success = False

        # Save result to database
        db.add(SubmissionResultModel(
            submission_id=submission_id,
            test_case_id=test_case.id,
            status=SubmissionStatus.SUCCESS if is_success else SubmissionStatus.FAILURE,
            actual_output=student_output,
            error_log=error_log
        ))

        # Build response for frontend
        test_responses_list.append(TestResult(
            id=test_case.id,
            status=TestStatus.SUCCESS if is_success else TestStatus.FAILURE,
            actual_output=student_output,
            error_log=error_log
        ))

    return global_success, test_responses_list

# Main Student Submission Handler
async def test_student_code(
    db: Session,
    exercise_id: int,
    payload: StudentSubmissionPayload,
    user_id: int
) -> dict:
    """
    Process and grade a student's code submission.

    Pipeline:
    1. Security check (exercise exists, not private)
    2. Initialize submission record
    3. Parse and save student solutions from TODO markers
    4. Reconstruct complete files by merging with teacher templates
    5. Compile code
    6. Execute against all test cases
    7. Grade results by comparing outputs
    8. Update student progress

    """
    # Security check 
    exercise = get_secure_exercise_or_404(db, exercise_id)

    try:
        # Initialize submission record
        submission = initialize_submission_history(db, user_id, exercise_id)
        submission_id = submission.id

        #  Parse student solutions and save to database
        all_student_markers: list[MarkerData] = process_and_save_markers(
            db, submission_id, payload.files, exercise.files
        )

        #  Reconstruct files by merging student code with teacher templates
        print("Student Markers", all_student_markers)
        teacher_files: list[ExerciseFileModel] = exercise.files
        files_to_compile: list[File] = reconstruct_files_for_compilation(
            teacher_files, all_student_markers
        )

        # Prepare test cases
        print("Files rebuilt", files_to_compile)
        sorted_tests: list[TestCaseModel] = sorted(exercise.tests, key=lambda t: t.position)
        argvs: list[str] = [t.argv if t.argv else "" for t in sorted_tests]

        #  Compile and execute all tests
        exec_results = await compile_and_run_logics(
            files_to_compile,
            payload.language,
            argvs
        )

        # Check for compilation failure
        # compile_and_run_logics returns a dict if compilation failed
        if isinstance(exec_results, dict) and not exec_results.get("status", True):
            submission.status = SubmissionStatus.FAILURE
            db.commit()
            print("Compilation error", exec_results)
            return exec_results

        print("Execution results", exec_results)

        #Grade results
        global_success, test_responses_list = grade_submission(
            db, submission_id, exec_results, sorted_tests
        )

        # Update submission status
        submission.status = SubmissionStatus.SUCCESS if global_success else SubmissionStatus.FAILURE

        # Update student progress
        update_student_progress(db, user_id, exercise_id, global_success)

        # Commit all changes
        db.commit()

        return {
            "status": True,
            "message": "Grading completed",
            "data": {
                "test_responses": test_responses_list
            }
        }

    except ValueError as e:
        return {
            "status": False,
            "message": "Format error",
            "data": {"format_error": str(e)}
        }

    except Exception as e:
        db.rollback()
        print(f"Error in test_student_code: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal grading error: {str(e)}"
        )
