import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class TeamMemberOut(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    student_user_id: uuid.UUID
    student_name: str
    student_register_number: str
    student_email: str
    department: Optional[str] = None
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True


class TeamInvitationCreate(BaseModel):
    invitee_register_number: str = Field(..., min_length=3)


class TeamInvitationOut(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    team_number: Optional[int] = None
    team_title: Optional[str] = None
    project_id: Optional[uuid.UUID] = None
    project_name: Optional[str] = None
    invited_by: uuid.UUID
    invited_by_name: str
    invitee_user_id: uuid.UUID
    invitee_name: str
    invitee_register_number: str
    status: str
    responded_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TeamCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)


class TeamFacultyCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    member_register_numbers: List[str] = []
    leader_register_number: Optional[str] = None


class TeamMemberAdd(BaseModel):
    student_user_id: uuid.UUID
    role: str = Field(default="member", pattern="^(leader|member)$")


class TeamUpdate(BaseModel):
    title: Optional[str] = None
    is_delayed: Optional[bool] = None


class StatusTransitionRequest(BaseModel):
    target_status: str = Field(..., min_length=2)
    comment: Optional[str] = None


class TeamOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    project_name: Optional[str] = None
    number: int
    title: str
    status: str
    formed_by: str
    is_delayed: bool
    created_at: datetime
    members: List[TeamMemberOut] = []
    member_count: int = 0
    overall_progress: Optional[float] = 0.0

    class Config:
        from_attributes = True
