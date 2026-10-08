import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.scm import CIVersionOut


class BaselineCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = None
    ci_version_ids: List[uuid.UUID] = Field(..., min_length=1)


class BaselineOut(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    code: str  # BL-001
    name: str
    description: Optional[str] = None
    status: str  # proposed, locked
    created_by: uuid.UUID
    created_by_name: Optional[str] = None
    approved_by: Optional[uuid.UUID] = None
    approved_by_name: Optional[str] = None
    locked_at: Optional[datetime] = None
    created_at: datetime
    items: List[CIVersionOut] = []

    class Config:
        from_attributes = True
