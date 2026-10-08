import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ReleaseCreate(BaseModel):
    code: str = Field(..., min_length=3, max_length=50)  # REL-1.0.0
    version: str = Field(..., min_length=1, max_length=30)
    baseline_id: uuid.UUID
    commit_sha: Optional[str] = None
    notes: Optional[str] = None


class ReleaseDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(approved|rejected)$")
    test_status: Optional[str] = Field(default=None, pattern="^(not_run|passed|failed)$")
    doc_status: Optional[str] = Field(default=None, pattern="^(pending|approved)$")
    feedback: Optional[str] = None


class ReleaseOut(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    code: str
    version: str
    baseline_id: uuid.UUID
    baseline_code: Optional[str] = None
    baseline_name: Optional[str] = None
    commit_sha: Optional[str] = None
    test_status: str
    doc_status: str
    status: str
    notes: Optional[str] = None
    requested_by: uuid.UUID
    requested_by_name: Optional[str] = None
    approved_by: Optional[uuid.UUID] = None
    approved_by_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
