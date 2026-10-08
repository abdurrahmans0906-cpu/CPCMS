import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, UniqueConstraint, CheckConstraint, Index, Table
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base

baseline_items = Table(
    "baseline_items",
    Base.metadata,
    Column("baseline_id", UUID(as_uuid=True), ForeignKey("baselines.id", ondelete="CASCADE"), primary_key=True),
    Column("ci_version_id", UUID(as_uuid=True), ForeignKey("ci_versions.id", ondelete="CASCADE"), primary_key=True),
    Index("idx_baseline_items_version", "ci_version_id")
)


class Baseline(Base):
    __tablename__ = "baselines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(50), nullable=False)  # BL-001 per team
    name = Column(String(150), nullable=False)
    description = Column(String, nullable=True)
    status = Column(String(20), nullable=False, default="proposed")  # proposed, locked
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    locked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    team = relationship("Team", back_populates="baselines")
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])
    ci_versions = relationship("CIVersion", secondary=baseline_items, backref="baselines")

    __table_args__ = (
        UniqueConstraint("team_id", "code", name="uq_team_baseline_code"),
        CheckConstraint("status IN ('proposed', 'locked')", name="chk_baseline_status"),
    )
