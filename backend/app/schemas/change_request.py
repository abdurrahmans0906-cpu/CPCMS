import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CRItemOut(BaseModel):
    ci_id: uuid.UUID
    ci_code: str
    ci_name: str
    ci_type: str
    is_locked: bool
    note: Optional[str] = None

    class Config:
        from_attributes = True


class ChangeTransitionOut(BaseModel):
    id: uuid.UUID
    cr_id: uuid.UUID
    from_status: str
    to_status: str
    actor_id: Optional[uuid.UUID] = None
    actor_name: Optional[str] = None
    comment: Optional[str] = None
    at: datetime

    class Config:
        from_attributes = True


class ChangeRequestCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=250)
    description: str = Field(..., min_length=5)
    reason: str = Field(..., min_length=5)
    priority: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    affected_ci_ids: List[uuid.UUID] = []
    components: List[str] = []  # backend, database, frontend, test_cases, documentation, other


class ChangeRequestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    reason: Optional[str] = None
    priority: Optional[str] = None
    affected_ci_ids: Optional[List[uuid.UUID]] = None
    components: Optional[List[str]] = None


class CRTransitionRequest(BaseModel):
    to_status: str = Field(..., pattern="^(draft|submitted|under_review|approved|rejected|implemented|verified|closed)$")
    comment: Optional[str] = None
    implemented_commit_sha: Optional[str] = None
    implemented_version_id: Optional[uuid.UUID] = None


class ChangeRequestOut(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    cr_code: str  # CR-2026-001
    title: str
    description: str
    reason: str
    priority: str
    status: str
    created_by: uuid.UUID
    created_by_name: Optional[str] = None
    implemented_commit_sha: Optional[str] = None
    implemented_version_id: Optional[uuid.UUID] = None
    components: List[str] = []
    items: List[CRItemOut] = []
    transitions: List[ChangeTransitionOut] = []
    created_at: datetime

    class Config:
        from_attributes = True


class CRImpactOut(BaseModel):
    cr_id: uuid.UUID
    cr_code: str
    components: List[str] = []
    directly_affected_cis: List[Dict[str, Any]] = []
    indirectly_affected_cis: List[Dict[str, Any]] = []
    locked_cis: List[Dict[str, Any]] = []
    affected_baselines: List[Dict[str, Any]] = []
