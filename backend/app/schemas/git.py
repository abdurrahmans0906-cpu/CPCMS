import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class BranchOut(BaseModel):
    id: uuid.UUID
    repo_id: uuid.UUID
    name: str
    head_sha: str
    follows_policy: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CommitOut(BaseModel):
    id: uuid.UUID
    repo_id: uuid.UUID
    sha: str
    branch: str
    author_name: str
    author_login: Optional[str] = None
    message: str
    committed_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class RepositoryCreate(BaseModel):
    url: str = Field(..., min_length=10, max_length=500)


class RepositoryOut(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    url: str
    owner: str
    name: str
    default_branch: str
    last_synced_at: Optional[datetime] = None
    last_sync_error: Optional[str] = None
    branches: List[BranchOut] = []
    commits: List[CommitOut] = []
    created_at: datetime

    class Config:
        from_attributes = True
