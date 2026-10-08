import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, UniqueConstraint, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base


class ChangeRequest(Base):
    __tablename__ = "change_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    cr_code = Column(String(50), nullable=False)  # CR-2026-001
    title = Column(String(250), nullable=False)
    description = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    priority = Column(String(20), nullable=False, default="medium")  # low, medium, high, critical
    status = Column(String(30), nullable=False, default="draft")  # draft, submitted, under_review, approved, rejected, implemented, verified, closed
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    implemented_commit_sha = Column(String(40), nullable=True)
    implemented_version_id = Column(UUID(as_uuid=True), ForeignKey("ci_versions.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    team = relationship("Team", back_populates="change_requests")
    creator = relationship("User", foreign_keys=[created_by])
    implemented_version = relationship("CIVersion", foreign_keys=[implemented_version_id])
    items = relationship("ChangeRequestItem", back_populates="change_request", cascade="all, delete-orphan")
    components = relationship("ChangeRequestComponent", back_populates="change_request", cascade="all, delete-orphan")
    transitions = relationship("ChangeTransition", back_populates="change_request", cascade="all, delete-orphan", order_by="ChangeTransition.at")

    __table_args__ = (
        UniqueConstraint("team_id", "cr_code", name="uq_team_cr_code"),
        CheckConstraint("priority IN ('low', 'medium', 'high', 'critical')", name="chk_cr_priority"),
        CheckConstraint("status IN ('draft', 'submitted', 'under_review', 'approved', 'rejected', 'implemented', 'verified', 'closed')", name="chk_cr_status"),
    )


class ChangeRequestItem(Base):
    __tablename__ = "change_request_items"

    cr_id = Column(UUID(as_uuid=True), ForeignKey("change_requests.id", ondelete="CASCADE"), primary_key=True)
    ci_id = Column(UUID(as_uuid=True), ForeignKey("configuration_items.id", ondelete="CASCADE"), primary_key=True)
    note = Column(String, nullable=True)

    change_request = relationship("ChangeRequest", back_populates="items")
    ci = relationship("ConfigurationItem")

    __table_args__ = (
        Index("idx_cr_items_ci", "ci_id"),
    )


class ChangeRequestComponent(Base):
    __tablename__ = "change_request_components"

    cr_id = Column(UUID(as_uuid=True), ForeignKey("change_requests.id", ondelete="CASCADE"), primary_key=True)
    component = Column(String(50), primary_key=True)  # backend, database, frontend, test_cases, documentation, other

    change_request = relationship("ChangeRequest", back_populates="components")

    __table_args__ = (
        CheckConstraint("component IN ('backend', 'database', 'frontend', 'test_cases', 'documentation', 'other')", name="chk_cr_component"),
    )


class ChangeTransition(Base):
    __tablename__ = "change_transitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cr_id = Column(UUID(as_uuid=True), ForeignKey("change_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    from_status = Column(String(30), nullable=False)
    to_status = Column(String(30), nullable=False)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    comment = Column(String, nullable=True)
    at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    change_request = relationship("ChangeRequest", back_populates="transitions")
    actor = relationship("User")
