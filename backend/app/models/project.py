import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, Integer, Numeric, DateTime, ForeignKey,
    UniqueConstraint, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import relationship
from app.db import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    faculty_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    semester = Column(String(50), nullable=False)
    academic_year = Column(String(50), nullable=False)
    description = Column(String, nullable=True)
    problem_statement = Column(String, nullable=True)
    objectives = Column(String, nullable=True)

    min_team_size = Column(Integer, nullable=False, default=1)
    max_team_size = Column(Integer, nullable=False, default=4)
    team_formation_mode = Column(String(20), nullable=False, default="student")  # student, faculty, hybrid
    team_formation_deadline = Column(DateTime(timezone=True), nullable=True)
    max_projects_per_student = Column(Integer, nullable=False, default=1)

    allowed_file_exts = Column(ARRAY(String), default=lambda: ["pdf", "zip", "docx", "md", "txt", "py", "ts", "json"])
    max_file_mb = Column(Integer, nullable=False, default=25)
    late_policy = Column(String(20), nullable=False, default="allow_flagged")  # reject, allow_flagged, allow_penalty
    late_penalty_percent = Column(Numeric(5, 2), nullable=False, default=0.0)

    versioning_required = Column(Boolean, nullable=False, default=True)
    git_required = Column(Boolean, nullable=False, default=False)
    baseline_frequency = Column(String(50), nullable=False, default="per_review")
    change_request_required = Column(Boolean, nullable=False, default=True)
    approval_required = Column(Boolean, nullable=False, default=True)
    branching_policy = Column(String(20), nullable=False, default="none")  # none, gitflow_lite

    total_marks = Column(Integer, nullable=False, default=100)
    grade_bands = Column(JSONB, nullable=False, default=lambda: [
        {"grade": "S", "min": 90, "max": 100},
        {"grade": "A", "min": 80, "max": 89},
        {"grade": "B", "min": 70, "max": 79},
        {"grade": "C", "min": 60, "max": 69},
        {"grade": "D", "min": 50, "max": 59},
        {"grade": "F", "min": 0, "max": 49}
    ])
    status = Column(String(20), nullable=False, default="active")  # active, archived
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    course = relationship("Course", back_populates="projects")
    faculty_user = relationship("User")
    themes = relationship("ProjectTheme", back_populates="project", cascade="all, delete-orphan")
    outcomes = relationship("ProjectOutcome", back_populates="project", cascade="all, delete-orphan", order_by="ProjectOutcome.position")
    ci_templates = relationship("ProjectCITemplate", back_populates="project", cascade="all, delete-orphan", order_by="ProjectCITemplate.position")
    deadlines = relationship("ProjectDeadline", back_populates="project", cascade="all, delete-orphan")
    evaluation_criteria = relationship("EvaluationCriteria", back_populates="project", cascade="all, delete-orphan", order_by="EvaluationCriteria.position")
    reviews = relationship("Review", back_populates="project", cascade="all, delete-orphan")
    enrolled_students = relationship("ProjectStudent", back_populates="project", cascade="all, delete-orphan")
    teams = relationship("Team", back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("min_team_size <= max_team_size", name="chk_team_size_min_max"),
        CheckConstraint("team_formation_mode IN ('student', 'faculty', 'hybrid')", name="chk_project_formation_mode"),
        CheckConstraint("late_policy IN ('reject', 'allow_flagged', 'allow_penalty')", name="chk_project_late_policy"),
        CheckConstraint("branching_policy IN ('none', 'gitflow_lite')", name="chk_project_branching_policy"),
        CheckConstraint("status IN ('active', 'archived')", name="chk_project_status"),
    )


class ProjectTheme(Base):
    __tablename__ = "project_themes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project", back_populates="themes")


class ProjectOutcome(Base):
    __tablename__ = "project_outcomes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    position = Column(Integer, nullable=False, default=1)
    text = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project", back_populates="outcomes")


class ProjectCITemplate(Base):
    __tablename__ = "project_ci_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    position = Column(Integer, nullable=False, default=1)
    name = Column(String(100), nullable=False)
    ci_type = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project", back_populates="ci_templates")


class ProjectDeadline(Base):
    __tablename__ = "project_deadlines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    kind = Column(String(30), nullable=False)  # team_formation, proposal, srs, review, final, other
    title = Column(String(200), nullable=False)
    due_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project", back_populates="deadlines")

    __table_args__ = (
        CheckConstraint("kind IN ('team_formation', 'proposal', 'srs', 'review', 'final', 'other')", name="chk_deadline_kind"),
    )


class EvaluationCriteria(Base):
    __tablename__ = "evaluation_criteria"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    position = Column(Integer, nullable=False, default=1)
    name = Column(String(100), nullable=False)
    max_marks = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project", back_populates="evaluation_criteria")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    start_at = Column(DateTime(timezone=True), nullable=False)
    mode = Column(String(20), nullable=False, default="online")  # online, offline
    meeting_link = Column(String, nullable=True)
    venue = Column(String, nullable=True)
    agenda = Column(String, nullable=True)
    instructions = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project", back_populates="reviews")
    slots = relationship("ReviewSlot", back_populates="review", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("mode IN ('online', 'offline')", name="chk_review_mode"),
    )


class ReviewSlot(Base):
    __tablename__ = "review_slots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id = Column(UUID(as_uuid=True), ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False, index=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    start_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    review = relationship("Review", back_populates="slots")
    team = relationship("Team")


class ProjectStudent(Base):
    __tablename__ = "project_students"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    register_number = Column(String(50), nullable=False, index=True)
    student_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    added_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project", back_populates="enrolled_students")
    student_user = relationship("User")

    __table_args__ = (
        UniqueConstraint("project_id", "register_number", name="uq_project_student_reg"),
    )
