import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, Integer, DateTime, ForeignKey, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base


class ProgressReport(Base):
    __tablename__ = "progress_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    review_id = Column(UUID(as_uuid=True), ForeignKey("reviews.id", ondelete="SET NULL"), nullable=True, index=True)
    seq = Column(Integer, nullable=False)
    requirements_pct = Column(Integer, nullable=False, default=0)
    design_pct = Column(Integer, nullable=False, default=0)
    implementation_pct = Column(Integer, nullable=False, default=0)
    testing_pct = Column(Integer, nullable=False, default=0)
    documentation_pct = Column(Integer, nullable=False, default=0)
    notes = Column(String, nullable=False)
    submitted_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    faculty_comment = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    team = relationship("Team", back_populates="progress_reports")
    review = relationship("Review")
    submitter = relationship("User")
    screenshots = relationship("ProgressScreenshot", back_populates="progress_report", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("requirements_pct BETWEEN 0 AND 100", name="chk_prog_req"),
        CheckConstraint("design_pct BETWEEN 0 AND 100", name="chk_prog_des"),
        CheckConstraint("implementation_pct BETWEEN 0 AND 100", name="chk_prog_imp"),
        CheckConstraint("testing_pct BETWEEN 0 AND 100", name="chk_prog_test"),
        CheckConstraint("documentation_pct BETWEEN 0 AND 100", name="chk_prog_doc"),
    )


class ProgressScreenshot(Base):
    __tablename__ = "progress_screenshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    progress_report_id = Column(UUID(as_uuid=True), ForeignKey("progress_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id", ondelete="CASCADE"), nullable=False, index=True)
    caption = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    progress_report = relationship("ProgressReport", back_populates="screenshots")
    file = relationship("FileModel")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    kind = Column(String(30), nullable=False)  # github, zip, source, release_package
    version_label = Column(String(30), nullable=True)
    commit_sha = Column(String(40), nullable=True)
    repo_url = Column(String(500), nullable=True)
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id", ondelete="SET NULL"), nullable=True, index=True)
    notes = Column(String, nullable=True)
    submitted_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    is_late = Column(Boolean, nullable=False, default=False)
    status = Column(String(20), nullable=False, default="submitted")  # submitted, accepted, rejected
    faculty_feedback = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    team = relationship("Team", back_populates="submissions")
    file = relationship("FileModel")
    submitter = relationship("User")

    __table_args__ = (
        CheckConstraint("kind IN ('github', 'zip', 'source', 'release_package')", name="chk_submission_kind"),
        CheckConstraint("status IN ('submitted', 'accepted', 'rejected')", name="chk_submission_status"),
    )
