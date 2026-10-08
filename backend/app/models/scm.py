import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, Integer, BigInteger, DateTime, ForeignKey,
    UniqueConstraint, CheckConstraint, Index, Table
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base

# Association table for CI dependencies
ci_dependencies = Table(
    "ci_dependencies",
    Base.metadata,
    Column("ci_id", UUID(as_uuid=True), ForeignKey("configuration_items.id", ondelete="CASCADE"), primary_key=True),
    Column("depends_on_ci_id", UUID(as_uuid=True), ForeignKey("configuration_items.id", ondelete="CASCADE"), primary_key=True),
    Index("idx_ci_dep_depends_on", "depends_on_ci_id")
)


class FileModel(Base):
    __tablename__ = "files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_name = Column(String(255), nullable=False)
    stored_path = Column(String(500), nullable=False)
    mime = Column(String(100), nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    sha256 = Column(String(64), nullable=False, index=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    uploader = relationship("User")


class ConfigurationItem(Base):
    __tablename__ = "configuration_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    ci_code = Column(String(50), nullable=False)  # CI-001 per team
    name = Column(String(150), nullable=False)
    ci_type = Column(String(50), nullable=False)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    current_version_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String(30), nullable=False, default="draft")  # draft, under_review, approved, rejected
    is_locked = Column(Boolean, nullable=False, default=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    team = relationship("Team", back_populates="configuration_items")
    owner = relationship("User")
    versions = relationship("CIVersion", back_populates="ci", foreign_keys="CIVersion.ci_id", cascade="all, delete-orphan", order_by="CIVersion.created_at.desc()")

    # Dependencies relationship
    dependencies = relationship(
        "ConfigurationItem",
        secondary=ci_dependencies,
        primaryjoin="ConfigurationItem.id == ci_dependencies.c.ci_id",
        secondaryjoin="ConfigurationItem.id == ci_dependencies.c.depends_on_ci_id",
        backref="depended_on_by"
    )

    __table_args__ = (
        UniqueConstraint("team_id", "ci_code", name="uq_team_ci_code"),
        CheckConstraint("ci_type IN ('requirements', 'srs', 'architecture', 'database_design', 'backend', 'frontend', 'test_cases', 'test_report', 'documentation', 'other')", name="chk_ci_type"),
        CheckConstraint("status IN ('draft', 'under_review', 'approved', 'rejected')", name="chk_ci_status"),
    )


class CIVersion(Base):
    __tablename__ = "ci_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ci_id = Column(UUID(as_uuid=True), ForeignKey("configuration_items.id", ondelete="CASCADE"), nullable=False, index=True)
    major = Column(Integer, nullable=False)
    minor = Column(Integer, nullable=False)
    version_label = Column(String(30), nullable=False)  # e.g. "1.0", "1.1", "2.0 (rollback to 1.0)"
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id", ondelete="SET NULL"), nullable=True, index=True)
    content_sha256 = Column(String(64), nullable=False, index=True)
    change_description = Column(String, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    status = Column(String(30), nullable=False, default="draft")  # draft, submitted, approved, rejected
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    commit_sha = Column(String(40), nullable=True)
    kind = Column(String(20), nullable=False, default="upload")  # upload, rollback
    rollback_of_version_id = Column(UUID(as_uuid=True), ForeignKey("ci_versions.id", ondelete="SET NULL"), nullable=True, index=True)
    change_request_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    ci = relationship("ConfigurationItem", back_populates="versions", foreign_keys=[ci_id])
    file = relationship("FileModel")
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])
    rollback_of = relationship("CIVersion", remote_side=[id])

    __table_args__ = (
        UniqueConstraint("ci_id", "major", "minor", name="uq_ci_major_minor"),
        CheckConstraint("kind IN ('upload', 'rollback')", name="chk_version_kind"),
        CheckConstraint("status IN ('draft', 'submitted', 'approved', 'rejected')", name="chk_version_status"),
    )
