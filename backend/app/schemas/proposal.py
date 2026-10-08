import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, model_validator


class ProposalCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=250)
    abstract: str = Field(..., min_length=10)
    problem_statement: str = Field(..., min_length=10)
    objectives: str = Field(..., min_length=10)
    theme_id: Optional[uuid.UUID] = None
    expected_outcome: str = Field(..., min_length=10)


class ProposalDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(approved|rejected|revision_required)$")
    feedback: Optional[str] = None

    @model_validator(mode="after")
    def feedback_required_for_rejection_or_revision(self):
        if self.decision in ["rejected", "revision_required"] and not (self.feedback and self.feedback.strip()):
            raise ValueError("Faculty feedback is mandatory when rejecting or requesting modifications on a proposal.")
        return self


class ProposalOut(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    revision_no: int
    title: str
    abstract: str
    problem_statement: str
    objectives: str
    theme_id: Optional[uuid.UUID] = None
    theme_name: Optional[str] = None
    expected_outcome: str
    status: str
    faculty_feedback: Optional[str] = None
    submitted_by: uuid.UUID
    submitted_by_name: Optional[str] = None
    reviewed_by: Optional[uuid.UUID] = None
    reviewed_by_name: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
