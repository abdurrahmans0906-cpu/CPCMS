import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ProgressScreenshotOut(BaseModel):
    id: uuid.UUID
    file_id: uuid.UUID
    caption: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ProgressReportCreate(BaseModel):
    review_id: Optional[uuid.UUID] = None
    seq: int = Field(default=1, ge=1)
    requirements_pct: int = Field(..., ge=0, le=100)
    design_pct: int = Field(..., ge=0, le=100)
    implementation_pct: int = Field(..., ge=0, le=100)
    testing_pct: int = Field(..., ge=0, le=100)
    documentation_pct: int = Field(..., ge=0, le=100)
    notes: str = Field(..., min_length=5)


class ProgressCommentRequest(BaseModel):
    faculty_comment: str = Field(..., min_length=2)


class ProgressReportOut(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    review_id: Optional[uuid.UUID] = None
    review_title: Optional[str] = None
    seq: int
    requirements_pct: int
    design_pct: int
    implementation_pct: int
    testing_pct: int
    documentation_pct: int
    overall_progress_pct: float = 0.0
    notes: str
    submitted_by: uuid.UUID
    submitted_by_name: Optional[str] = None
    faculty_comment: Optional[str] = None
    screenshots: List[ProgressScreenshotOut] = []
    created_at: datetime

    class Config:
        from_attributes = True


class SubmissionCreate(BaseModel):
    kind: str = Field(..., pattern="^(github|zip|source|release_package)$")
    version_label: Optional[str] = None
    commit_sha: Optional[str] = None
    repo_url: Optional[str] = None
    notes: Optional[str] = None


class SubmissionDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(accepted|rejected)$")
    feedback: Optional[str] = None


class SubmissionOut(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    kind: str
    version_label: Optional[str] = None
    commit_sha: Optional[str] = None
    repo_url: Optional[str] = None
    file_id: Optional[uuid.UUID] = None
    original_file_name: Optional[str] = None
    notes: Optional[str] = None
    submitted_by: uuid.UUID
    submitted_by_name: Optional[str] = None
    is_late: bool
    status: str
    faculty_feedback: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
