import uuid
from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, field_validator


class ThemeCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)


class ThemeOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class OutcomeCreate(BaseModel):
    position: int = Field(default=1, ge=1)
    text: str = Field(..., min_length=3)


class OutcomeOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    position: int
    text: str
    created_at: datetime

    class Config:
        from_attributes = True


class CITemplateCreate(BaseModel):
    position: int = Field(default=1, ge=1)
    name: str = Field(..., min_length=2, max_length=100)
    ci_type: str = Field(..., min_length=2, max_length=50)


class CITemplateOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    position: int
    name: str
    ci_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class DeadlineCreate(BaseModel):
    kind: str = Field(..., pattern="^(team_formation|proposal|srs|review|final|other)$")
    title: str = Field(..., min_length=2, max_length=200)
    due_at: datetime


class DeadlineOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    kind: str
    title: str
    due_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class CriteriaCreate(BaseModel):
    position: int = Field(default=1, ge=1)
    name: str = Field(..., min_length=2, max_length=100)
    max_marks: int = Field(..., gt=0)


class CriteriaOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    position: int
    name: str
    max_marks: int
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewSlotCreate(BaseModel):
    team_id: uuid.UUID
    start_at: datetime


class ReviewSlotOut(BaseModel):
    id: uuid.UUID
    review_id: uuid.UUID
    team_id: uuid.UUID
    team_number: Optional[int] = None
    team_title: Optional[str] = None
    start_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class ReviewCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    start_at: datetime
    mode: str = Field(default="online", pattern="^(online|offline)$")
    meeting_link: Optional[str] = None
    venue: Optional[str] = None
    agenda: Optional[str] = None
    instructions: Optional[str] = None


class ReviewOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    start_at: datetime
    mode: str
    meeting_link: Optional[str] = None
    venue: Optional[str] = None
    agenda: Optional[str] = None
    instructions: Optional[str] = None
    slots: List[ReviewSlotOut] = []
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectStudentOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    register_number: str
    student_user_id: Optional[uuid.UUID] = None
    student_name: Optional[str] = None
    student_email: Optional[str] = None
    department: Optional[str] = None
    is_registered: bool = False
    team_id: Optional[uuid.UUID] = None
    team_number: Optional[int] = None
    added_at: datetime

    class Config:
        from_attributes = True


class StudentEnrollBulkRequest(BaseModel):
    register_numbers: str  # Comma or newline separated list


class ProjectCreate(BaseModel):
    course_id: uuid.UUID
    name: str = Field(..., min_length=2, max_length=200)
    semester: str = Field(..., min_length=1, max_length=50)
    academic_year: str = Field(..., min_length=4, max_length=50)
    description: Optional[str] = None
    problem_statement: Optional[str] = None
    objectives: Optional[str] = None

    min_team_size: int = Field(default=1, ge=1)
    max_team_size: int = Field(default=4, ge=1)
    team_formation_mode: str = Field(default="student", pattern="^(student|faculty|hybrid)$")
    team_formation_deadline: Optional[datetime] = None
    max_projects_per_student: int = Field(default=1, ge=1)

    allowed_file_exts: List[str] = ["pdf", "zip", "docx", "md", "txt", "py", "ts", "json"]
    max_file_mb: int = Field(default=25, ge=1, le=200)
    late_policy: str = Field(default="allow_flagged", pattern="^(reject|allow_flagged|allow_penalty)$")
    late_penalty_percent: float = Field(default=0.0, ge=0.0, le=100.0)

    versioning_required: bool = True
    git_required: bool = False
    baseline_frequency: str = "per_review"
    change_request_required: bool = True
    approval_required: bool = True
    branching_policy: str = Field(default="none", pattern="^(none|gitflow_lite)$")

    total_marks: int = Field(default=100, gt=0)
    grade_bands: List[Dict[str, Any]] = [
        {"grade": "S", "min": 90, "max": 100},
        {"grade": "A", "min": 80, "max": 89},
        {"grade": "B", "min": 70, "max": 79},
        {"grade": "C", "min": 60, "max": 69},
        {"grade": "D", "min": 50, "max": 59},
        {"grade": "F", "min": 0, "max": 49}
    ]

    # Optional initial related items
    themes: Optional[List[str]] = []
    outcomes: Optional[List[str]] = []
    ci_templates: Optional[List[Dict[str, Any]]] = []
    deadlines: Optional[List[DeadlineCreate]] = []
    criteria: Optional[List[CriteriaCreate]] = []

    @field_validator("max_team_size")
    @classmethod
    def validate_sizes(cls, v: int, info):
        min_size = info.data.get("min_team_size", 1)
        if v < min_size:
            raise ValueError("max_team_size cannot be smaller than min_team_size")
        return v


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    semester: Optional[str] = None
    academic_year: Optional[str] = None
    description: Optional[str] = None
    problem_statement: Optional[str] = None
    objectives: Optional[str] = None
    min_team_size: Optional[int] = None
    max_team_size: Optional[int] = None
    team_formation_mode: Optional[str] = None
    team_formation_deadline: Optional[datetime] = None
    max_projects_per_student: Optional[int] = None
    allowed_file_exts: Optional[List[str]] = None
    max_file_mb: Optional[int] = None
    late_policy: Optional[str] = None
    late_penalty_percent: Optional[float] = None
    versioning_required: Optional[bool] = None
    git_required: Optional[bool] = None
    baseline_frequency: Optional[str] = None
    change_request_required: Optional[bool] = None
    approval_required: Optional[bool] = None
    branching_policy: Optional[str] = None
    total_marks: Optional[int] = None
    grade_bands: Optional[List[Dict[str, Any]]] = None
    status: Optional[str] = None


class ProjectOut(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    course_code: Optional[str] = None
    course_name: Optional[str] = None
    faculty_user_id: uuid.UUID
    faculty_name: Optional[str] = None
    name: str
    semester: str
    academic_year: str
    description: Optional[str] = None
    problem_statement: Optional[str] = None
    objectives: Optional[str] = None

    min_team_size: int
    max_team_size: int
    team_formation_mode: str
    team_formation_deadline: Optional[datetime] = None
    max_projects_per_student: int

    allowed_file_exts: List[str]
    max_file_mb: int
    late_policy: str
    late_penalty_percent: float

    versioning_required: bool
    git_required: bool
    baseline_frequency: str
    change_request_required: bool
    approval_required: bool
    branching_policy: str

    total_marks: int
    grade_bands: List[Dict[str, Any]]
    status: str
    created_at: datetime

    themes: List[ThemeOut] = []
    outcomes: List[OutcomeOut] = []
    ci_templates: List[CITemplateOut] = []
    deadlines: List[DeadlineOut] = []
    evaluation_criteria: List[CriteriaOut] = []

    # Student context info if requested by student
    user_team_id: Optional[uuid.UUID] = None
    user_team_number: Optional[int] = None
    user_team_status: Optional[str] = None

    class Config:
        from_attributes = True


class ProjectSummaryOut(BaseModel):
    id: uuid.UUID
    name: str
    course_code: str
    semester: str
    academic_year: str
    team_count: int
    student_count: int
    status: str
    teams_by_status: Dict[str, int] = {}
