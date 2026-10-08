import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    url = Column(String(500), nullable=False)
    owner = Column(String(100), nullable=False)
    name = Column(String(100), nullable=False)
    default_branch = Column(String(100), nullable=False, default="main")
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    last_sync_error = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    team = relationship("Team", back_populates="repository")
    branches = relationship("Branch", back_populates="repository", cascade="all, delete-orphan")
    commits = relationship("Commit", back_populates="repository", cascade="all, delete-orphan", order_by="Commit.committed_at.desc()")


class Branch(Base):
    __tablename__ = "branches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repo_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    head_sha = Column(String(40), nullable=False)
    follows_policy = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    repository = relationship("Repository", back_populates="branches")


class Commit(Base):
    __tablename__ = "commits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repo_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True)
    sha = Column(String(40), nullable=False, index=True)
    branch = Column(String(150), nullable=False)
    author_name = Column(String(100), nullable=False)
    author_login = Column(String(100), nullable=True)
    message = Column(String, nullable=False)
    committed_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    repository = relationship("Repository", back_populates="commits")
