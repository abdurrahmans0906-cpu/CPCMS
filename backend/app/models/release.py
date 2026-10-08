import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base


class Release(Base):
    __tablename__ = "releases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False)  # REL-1.0.0
    version = Column(String(30), nullable=False)
    baseline_id = Column(UUID(as_uuid=True), ForeignKey("baselines.id", ondelete="CASCADE"), nullable=False, index=True)
    commit_sha = Column(String(40), nullable=True)
    test_status = Column(String(20), nullable=False, default="not_run")  # not_run, passed, failed
    doc_status = Column(String(20), nullable=False, default="pending")  # pending, approved
    status = Column(String(20), nullable=False, default="requested")  # requested, approved, rejected
    notes = Column(String, nullable=True)
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    team = relationship("Team", back_populates="releases")
    baseline = relationship("Baseline")
    requester = relationship("User", foreign_keys=[requested_by])
    approver = relationship("User", foreign_keys=[approved_by])

    __table_args__ = (
        CheckConstraint("test_status IN ('not_run', 'passed', 'failed')", name="chk_release_test_status"),
        CheckConstraint("doc_status IN ('pending', 'approved')", name="chk_release_doc_status"),
        CheckConstraint("status IN ('requested', 'approved', 'rejected')", name="chk_release_status"),
    )
