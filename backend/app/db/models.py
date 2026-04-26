# Table postgresql in Python/SqlAlchemy

from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, UniqueConstraint, DateTime, Enum as SqlEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
from app.core.enums import Language, Visibility, UserRole, SubmissionStatus, ProgressStatus


class UserModel(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    firstname = Column(String, nullable=False)
    lastname = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    mdp_hash = Column(String, nullable=False)
    role = Column(SqlEnum(UserRole), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    unit_authored = relationship("UnitModel", back_populates="author")
    submission_histories = relationship("SubmissionHistoryModel", back_populates="user")
    exercise_progresses = relationship("ExerciseProgressModel", back_populates="user")


class UnitModel(Base):
    __tablename__ = "unit"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"))
    visibility = Column(SqlEnum(Visibility), default=Visibility.PRIVATE, nullable=False)
    difficulty = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    author = relationship("UserModel", back_populates="unit_authored")
    courses = relationship("CourseModel", back_populates="unit", cascade="all, delete-orphan")


class CourseModel(Base):
    __tablename__ = "course"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    unit_id = Column(Integer, ForeignKey("unit.id", ondelete="CASCADE"), nullable=False)
    visibility = Column(SqlEnum(Visibility), default=Visibility.PRIVATE, nullable=False)
    difficulty = Column(Integer, nullable=False)
    position = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    unit = relationship("UnitModel", back_populates="courses")
    exercises = relationship("ExerciseModel", back_populates="course", cascade="all, delete-orphan")


class ExerciseModel(Base):
    __tablename__ = "exercise"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    visibility = Column(SqlEnum(Visibility), default=Visibility.PRIVATE, nullable=False)
    language = Column(SqlEnum(Language), nullable=False)
    difficulty = Column(Integer, nullable=False)
    position = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    course = relationship("CourseModel", back_populates="exercises")
    files = relationship("ExerciseFileModel", back_populates="exercise", cascade="all, delete-orphan")
    tests = relationship("TestCaseModel", back_populates="exercise", cascade="all, delete-orphan")
    hints = relationship("HintModel", back_populates="exercise", cascade="all, delete-orphan")


class ExerciseFileModel(Base):
    __tablename__ = "exercise_file"

    id = Column(Integer, primary_key=True, index=True)
    exercise_id = Column(Integer, ForeignKey("exercise.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    template_without_marker = Column(Text, nullable=False)
    extension = Column(String, nullable=False)
    is_main = Column(Boolean, default=False, nullable=False)
    editable = Column(Boolean, default=False, nullable=False)
    position = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    exercise = relationship("ExerciseModel", back_populates="files")
    markers = relationship("ExerciseMarkerModel", back_populates="file", cascade="all, delete-orphan")


class ExerciseMarkerModel(Base):
    __tablename__ = "exercise_marker"

    id = Column(Integer, primary_key=True, index=True)
    exercise_file_id = Column(Integer, ForeignKey("exercise_file.id", ondelete="CASCADE"), nullable=False)
    marker_id = Column(String, nullable=False)
    solution_content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint('exercise_file_id', 'marker_id', name='unique_marker_per_file'),)

    file = relationship("ExerciseFileModel", back_populates="markers")


class TestCaseModel(Base):
    __tablename__ = "test_case"

    id = Column(Integer, primary_key=True, index=True)
    exercise_id = Column(Integer, ForeignKey("exercise.id", ondelete="CASCADE"), nullable=False)
    argv = Column(Text)
    comment = Column(Text)
    expected_output = Column(Text, nullable=False)
    position = Column(Integer, nullable=False)

    exercise = relationship("ExerciseModel", back_populates="tests")


class HintModel(Base):
    __tablename__ = "hint"

    id = Column(Integer, primary_key=True, index=True)
    exercise_id = Column(Integer, ForeignKey("exercise.id", ondelete="CASCADE"), nullable=False)
    unlock_after_attempts = Column(Integer, nullable=False)
    body = Column(Text, nullable=False)
    position = Column(Integer, nullable=False)

    exercise = relationship("ExerciseModel", back_populates="hints")


# Student monitoring

class SubmissionHistoryModel(Base):
    __tablename__ = "submission_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercise.id", ondelete="CASCADE"), nullable=False)
    status = Column(SqlEnum(SubmissionStatus), nullable=False)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("UserModel", back_populates="submission_histories")
    exercise = relationship("ExerciseModel")
    submission_markers = relationship("SubmissionMarkerModel", back_populates="submission_history", cascade="all, delete-orphan")
    submission_results = relationship("SubmissionResultModel", back_populates="submission_history", cascade="all, delete-orphan")


class SubmissionMarkerModel(Base):
    __tablename__ = "submission_marker"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submission_history.id", ondelete="CASCADE"), nullable=False)
    exercise_file_id = Column(Integer, ForeignKey("exercise_file.id", ondelete="CASCADE"), nullable=False)
    marker_id = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    submission_history = relationship("SubmissionHistoryModel", back_populates="submission_markers")
    original_file = relationship("ExerciseFileModel")


class SubmissionResultModel(Base):
    __tablename__ = "submission_result"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submission_history.id", ondelete="CASCADE"), nullable=False)
    test_case_id = Column(Integer, ForeignKey("test_case.id", ondelete="CASCADE"), nullable=False)
    status = Column(SqlEnum(SubmissionStatus), nullable=False)
    error_log = Column(Text, nullable=True)
    actual_output = Column(Text, nullable=False)

    submission_history = relationship("SubmissionHistoryModel", back_populates="submission_results")
    test_case = relationship("TestCaseModel")


class ExerciseProgressModel(Base):
    __tablename__ = "exercise_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercise.id", ondelete="CASCADE"), nullable=False)
    status = Column(SqlEnum(ProgressStatus), default=ProgressStatus.NOT_STARTED, nullable=False)
    attempts_count = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("UserModel", back_populates="exercise_progresses")
    exercise = relationship("ExerciseModel")


class HintViewModel(Base):
    __tablename__ = "hint_view"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    hint_id = Column(Integer, ForeignKey("hint.id", ondelete="CASCADE"), nullable=False)
    viewed_at = Column(DateTime(timezone=True), server_default=func.now())

    hint = relationship("HintModel")
    user = relationship("UserModel")


# ── CHAT ─────────────────────────────────────────────────────────────

class ChatRoomModel(Base):
    __tablename__ = "chat_room"

    id = Column(Integer, primary_key=True, index=True)
    exercise_id = Column(Integer, ForeignKey("exercise.id", ondelete="CASCADE"), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    exercise = relationship("ExerciseModel")
    messages = relationship("ChatMessageModel", back_populates="room", cascade="all, delete-orphan")


class ChatMessageModel(Base):
    __tablename__ = "chat_message"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("chat_room.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())

    room = relationship("ChatRoomModel", back_populates="messages")
    user = relationship("UserModel")
