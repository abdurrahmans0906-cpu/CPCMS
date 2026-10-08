import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, Integer, DateTime, ForeignKey, UniqueConstraint, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    number = Column(Integer, nullable=False)
    title = Column(String(200), nullable=False)
    status = Column(String(50), nullable=False, default="Created")
    formed_by = Column(String(20), nullable=False, default="student")  # student, faculty
    is_delayed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    project = relationship("Project", back_populates="teams")
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    invitations = relationship("TeamInvitation", back_populates="team", cascade="all, delete-orphan")
    proposals = relationship("Proposal", back_populates="team", cascade="all, delete-orphan", order_by="Proposal.revision_no.desc()")
    configuration_items = relationship("ConfigurationItem", back_populates="team", cascade="all, delete-orphan")
    baselines = relationship("Baseline", back_populates="team", cascade="all, delete-orphan")
    change_requests = relationship("ChangeRequest", back_populates="team", cascade="all, delete-orphan")
    repository = relationship("Repository", back_populates="team", uselist=False, cascade="all, delete-orphan")
    progress_reports = relationship("ProgressReport", back_populates="team", cascade="all, delete-orphan", order_by="ProgressReport.seq")
    submissions = relationship("Submission", back_populates="team", cascade="all, delete-orphan")
    evaluations = relationship("Evaluation", back_populates="team", cascade="all, delete-orphan")
    releases = relationship("Release", back_populates="team", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("project_id", "number", name="uq_team_project_number"),
        CheckConstraint("formed_by IN ('student', 'faculty')", name="chk_team_formed_by"),
    )


class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    student_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False, default="member")  # leader, member
    joined_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    team = relationship("Team", back_populates="members")
    project = relationship("Project")
    student_user = relationship("User")

    __table_args__ = (
        UniqueConstraint("project_id", "student_user_id", name="uq_project_student_one_team"),
        CheckConstraint("role IN ('leader', 'member')", name="chk_member_role"),
    )


class TeamInvitation(Base):
    __tablename__ = "team_invitations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    invitee_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="pending")  # pending, accepted, rejected, expired, cancelled
    responded_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    team = relationship("Team", back_populates="invitations")
    inviter = relationship("User", foreign_keys=[invited_by])
    invitee = relationship("User", foreign_keys=[invitee_user_id])

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'accepted', 'rejected', 'expired', 'cancelled')", name="chk_invitation_status"),
    )
