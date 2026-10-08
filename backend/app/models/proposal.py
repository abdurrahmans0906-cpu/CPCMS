import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, DateTime, ForeignKey, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base


class Proposal(Base):
    __tablename__ = "proposals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    revision_no = Column(Integer, nullable=False, default=1)
    title = Column(String(250), nullable=False)
    abstract = Column(String, nullable=False)
    problem_statement = Column(String, nullable=False)
    objectives = Column(String, nullable=False)
    theme_id = Column(UUID(as_uuid=True), ForeignKey("project_themes.id", ondelete="SET NULL"), nullable=True, index=True)
    expected_outcome = Column(String, nullable=False)

    status = Column(String(30), nullable=False, default="submitted")  # submitted, approved, rejected, revision_required
    faculty_feedback = Column(String, nullable=True)
    submitted_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    team = relationship("Team", back_populates="proposals")
    theme = relationship("ProjectTheme")
    submitter = relationship("User", foreign_keys=[submitted_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    __table_args__ = (
        CheckConstraint("status IN ('submitted', 'approved', 'rejected', 'revision_required')", name="chk_proposal_status"),
    )
