import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Numeric, DateTime, ForeignKey, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    review_id = Column(UUID(as_uuid=True), ForeignKey("reviews.id", ondelete="SET NULL"), nullable=True, index=True)
    stage = Column(String(20), nullable=False)  # review, final
    total_marks = Column(Numeric(6, 2), nullable=False)
    grade = Column(String(10), nullable=False)
    feedback = Column(String, nullable=True)
    evaluated_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    team = relationship("Team", back_populates="evaluations")
    review = relationship("Review")
    evaluator = relationship("User")
    scores = relationship("EvaluationScore", back_populates="evaluation", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("stage IN ('review', 'final')", name="chk_evaluation_stage"),
    )


class EvaluationScore(Base):
    __tablename__ = "evaluation_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_id = Column(UUID(as_uuid=True), ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False, index=True)
    criterion_id = Column(UUID(as_uuid=True), ForeignKey("evaluation_criteria.id", ondelete="CASCADE"), nullable=False, index=True)
    marks = Column(Numeric(6, 2), nullable=False)
    comment = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    evaluation = relationship("Evaluation", back_populates="scores")
    criterion = relationship("EvaluationCriteria")
