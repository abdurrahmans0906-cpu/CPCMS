import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class CourseCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=150)
    department: str = Field(..., min_length=2, max_length=100)


class CourseOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    department: str
    faculty_user_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True
