import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class EvaluationScoreCreate(BaseModel):
    criterion_id: uuid.UUID
    marks: float = Field(..., ge=0)
    comment: Optional[str] = None


class EvaluationScoreOut(BaseModel):
    id: uuid.UUID
    criterion_id: uuid.UUID
    criterion_name: Optional[str] = None
    max_marks: Optional[int] = None
    marks: float
    comment: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class EvaluationCreate(BaseModel):
    review_id: Optional[uuid.UUID] = None
    stage: str = Field(..., pattern="^(review|final)$")
    scores: List[EvaluationScoreCreate] = Field(..., min_length=1)
    feedback: Optional[str] = None


class EvaluationOut(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    review_id: Optional[uuid.UUID] = None
    review_title: Optional[str] = None
    stage: str
    total_marks: float
    grade: str
    feedback: Optional[str] = None
    evaluated_by: uuid.UUID
    evaluated_by_name: Optional[str] = None
    scores: List[EvaluationScoreOut] = []
    created_at: datetime

    class Config:
        from_attributes = True
