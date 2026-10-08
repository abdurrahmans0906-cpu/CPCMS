import uuid
from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class CIVersionOut(BaseModel):
    id: uuid.UUID
    ci_id: uuid.UUID
    major: int
    minor: int
    version_label: str
    file_id: Optional[uuid.UUID] = None
    original_file_name: Optional[str] = None
    file_size_bytes: Optional[int] = 0
    content_sha256: str
    change_description: str
    created_by: uuid.UUID
    created_by_name: Optional[str] = None
    status: str
    approved_by: Optional[uuid.UUID] = None
    approved_by_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    commit_sha: Optional[str] = None
    kind: str
    rollback_of_version_id: Optional[uuid.UUID] = None
    change_request_id: Optional[uuid.UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CIDependencyOut(BaseModel):
    id: uuid.UUID
    ci_code: str
    name: str
    ci_type: str
    is_locked: bool

    class Config:
        from_attributes = True


class CIOut(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    ci_code: str
    name: str
    ci_type: str
    owner_user_id: Optional[uuid.UUID] = None
    owner_name: Optional[str] = None
    current_version_id: Optional[uuid.UUID] = None
    status: str
    is_locked: bool
    updated_at: datetime
    created_at: datetime
    latest_version: Optional[CIVersionOut] = None
    latest_approved_version: Optional[CIVersionOut] = None
    versions: List[CIVersionOut] = []
    dependencies: List[CIDependencyOut] = []
    baseline_codes: List[str] = []

    class Config:
        from_attributes = True


class CICreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    ci_type: str = Field(..., pattern="^(requirements|srs|architecture|database_design|backend|frontend|test_cases|test_report|documentation|other)$")
    owner_user_id: Optional[uuid.UUID] = None


class CIUpdate(BaseModel):
    name: Optional[str] = None
    owner_user_id: Optional[uuid.UUID] = None


class CIVersionDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(approved|rejected)$")
    comment: Optional[str] = None


class RollbackRequest(BaseModel):
    target_version_id: uuid.UUID
    reason: str = Field(..., min_length=5)
    bump_type: str = Field(default="minor", pattern="^(major|minor)$")
    change_request_id: Optional[uuid.UUID] = None


class DependenciesUpdateRequest(BaseModel):
    depends_on_ci_ids: List[uuid.UUID]


class VersionCompareOut(BaseModel):
    from_metadata: Dict[str, Any]
    to_metadata: Dict[str, Any]
    is_text: bool
    message: Optional[str] = None
    unified_diff: Optional[str] = None
    added_count: int = 0
    removed_count: int = 0
    modified_count: int = 0
