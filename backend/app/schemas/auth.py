import uuid
import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from app.config import settings


class StudentRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    register_number: str = Field(..., min_length=5, max_length=50)
    department: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)

    @field_validator("register_number")
    @classmethod
    def validate_register_number(cls, v: str) -> str:
        reg = v.strip().upper()
        pattern = settings.STUDENT_REG_PATTERN
        if pattern and not re.match(pattern, reg):
            raise ValueError(f"Register number '{reg}' does not match required format (e.g. 23MIS0475).")
        return reg

    @field_validator("email")
    @classmethod
    def validate_email_domain(cls, v: EmailStr) -> EmailStr:
        domains = settings.allowed_email_domains_list
        if domains:
            email_domain = v.split("@")[-1].lower()
            if email_domain not in domains:
                raise ValueError(f"Email domain '{email_domain}' is not allowed. Allowed domains: {', '.join(domains)}")
        return v

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Password and confirmation password do not match.")
        return self


class FacultyRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    faculty_code: str = Field(..., min_length=2, max_length=50)
    department: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8)
    invite_code: str = Field(..., min_length=1)

    @field_validator("faculty_code")
    @classmethod
    def clean_faculty_code(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("invite_code")
    @classmethod
    def validate_invite_code(cls, v: str) -> str:
        if v.strip() != settings.FACULTY_INVITE_CODE:
            raise ValueError("Invalid faculty invite code.")
        return v


class LoginRequest(BaseModel):
    identifier: str = Field(..., min_length=2)  # register_number / faculty_code / email
    password: str = Field(..., min_length=1)


class UserOut(BaseModel):
    id: uuid.UUID
    role: str
    name: str
    email: str
    register_number: Optional[str] = None
    faculty_code: Optional[str] = None
    department: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
