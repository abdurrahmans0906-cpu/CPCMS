from datetime import datetime, timezone, timedelta
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db import get_db
from app.config import settings
from app.security import (
    hash_password, verify_password, create_access_token,
    generate_refresh_token, hash_refresh_token
)
from app.models.user import User, Student, Faculty, RefreshToken
from app.models.project import ProjectStudent
from app.schemas.auth import (
    StudentRegisterRequest, FacultyRegisterRequest,
    LoginRequest, TokenResponse, UserOut
)
from app.permissions import get_current_user
from app.services.audit import record_audit

router = APIRouter(prefix="/auth", tags=["Auth"])


def _build_user_out(user: User) -> UserOut:
    reg_no = user.student_profile.register_number if user.student_profile else None
    fac_code = user.faculty_profile.faculty_code if user.faculty_profile else None
    dept = (
        user.student_profile.department
        if user.student_profile
        else (user.faculty_profile.department if user.faculty_profile else None)
    )
    return UserOut(
        id=user.id,
        role=user.role,
        name=user.name,
        email=user.email,
        register_number=reg_no,
        faculty_code=fac_code,
        department=dept,
        is_active=user.is_active,
        created_at=user.created_at
    )


@router.post("/register/student", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_student(payload: StudentRegisterRequest, db: Session = Depends(get_db)):
    # Check email uniqueness
    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    # Check register number uniqueness
    reg_clean = payload.register_number.strip().upper()
    if db.query(Student).filter(Student.register_number == reg_clean).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Register number '{reg_clean}' is already registered."
        )

    user = User(
        role="STUDENT",
        name=payload.name.strip(),
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        is_active=True
    )
    db.add(user)
    db.flush()

    student = Student(
        user_id=user.id,
        register_number=reg_clean,
        department=payload.department.strip()
    )
    db.add(student)

    # Link any pre-enrolled project students matching this register number!
    db.query(ProjectStudent).filter(
        ProjectStudent.register_number == reg_clean,
        ProjectStudent.student_user_id.is_(None)
    ).update({"student_user_id": user.id}, synchronize_session=False)

    record_audit(
        db=db,
        action="STUDENT_REGISTER",
        entity_type="user",
        entity_id=user.id,
        actor=user,
        note=f"Student registered: {user.name} ({reg_clean})"
    )
    db.commit()
    db.refresh(user)
    return _build_user_out(user)


@router.post("/register/faculty", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_faculty(payload: FacultyRegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this official email address already exists."
        )

    fac_code = payload.faculty_code.strip().upper()
    if db.query(Faculty).filter(Faculty.faculty_code == fac_code).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Faculty ID '{fac_code}' is already registered."
        )

    user = User(
        role="FACULTY",
        name=payload.name.strip(),
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        is_active=True
    )
    db.add(user)
    db.flush()

    faculty = Faculty(
        user_id=user.id,
        faculty_code=fac_code,
        department=payload.department.strip()
    )
    db.add(faculty)

    record_audit(
        db=db,
        action="FACULTY_REGISTER",
        entity_type="user",
        entity_id=user.id,
        actor=user,
        note=f"Faculty registered: {user.name} ({fac_code})"
    )
    db.commit()
    db.refresh(user)
    return _build_user_out(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    ident = payload.identifier.strip()
    now = datetime.now(timezone.utc)

    # Find user by email, student register_number, or faculty_code
    user = (
        db.query(User)
        .outerjoin(Student, User.id == Student.user_id)
        .outerjoin(Faculty, User.id == Faculty.user_id)
        .filter(
            or_(
                User.email == ident.lower(),
                Student.register_number == ident.upper(),
                Faculty.faculty_code == ident.upper()
            )
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please verify your identifier and password."
        )

    # Check lockout
    if user.locked_until and user.locked_until > now:
        remaining_minutes = int((user.locked_until - now).total_seconds() / 60) + 1
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is temporarily locked due to multiple failed login attempts. Try again in {remaining_minutes} minute(s)."
        )

    # Verify password
    if not verify_password(payload.password, user.password_hash):
        user.failed_attempts += 1
        if user.failed_attempts >= 5:
            user.locked_until = now + timedelta(minutes=10)
            user.failed_attempts = 0
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account locked for 10 minutes following 5 consecutive failed attempts."
            )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid credentials. Attempt {user.failed_attempts} of 5 before temporary lockout."
        )

    # Successful login: reset failed attempts
    user.failed_attempts = 0
    user.locked_until = None

    # Issue access token
    access_token = create_access_token({"sub": str(user.id), "role": user.role})

    # Issue rotating refresh token
    raw_refresh = generate_refresh_token()
    token_hash = hash_refresh_token(raw_refresh)
    expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    refresh_obj = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at
    )
    db.add(refresh_obj)
    db.commit()
    db.refresh(user)

    # Set httpOnly SameSite cookie
    response.set_cookie(
        key="cpcms_refresh",
        value=raw_refresh,
        httponly=True,
        samesite="lax",
        secure=False,  # Can be True in HTTPS production
        expires=int(timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS).total_seconds())
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=_build_user_out(user)
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    cookie_token = request.cookies.get("cpcms_refresh")
    if not cookie_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token cookie missing."
        )

    token_hash = hash_refresh_token(cookie_token)
    now = datetime.now(timezone.utc)

    db_token = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash,
        RefreshToken.revoked_at.is_(None),
        RefreshToken.expires_at > now
    ).first()

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token."
        )

    user = db.query(User).filter(User.id == db_token.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account inactive or not found."
        )

    # Rotate refresh token: revoke current
    db_token.revoked_at = now

    new_raw_refresh = generate_refresh_token()
    new_token_hash = hash_refresh_token(new_raw_refresh)
    new_expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    new_refresh_obj = RefreshToken(
        user_id=user.id,
        token_hash=new_token_hash,
        expires_at=new_expires_at
    )
    db.add(new_refresh_obj)
    db.commit()

    new_access_token = create_access_token({"sub": str(user.id), "role": user.role})

    response.set_cookie(
        key="cpcms_refresh",
        value=new_raw_refresh,
        httponly=True,
        samesite="lax",
        secure=False,
        expires=int(timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS).total_seconds())
    )

    return TokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        user=_build_user_out(user)
    )


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    cookie_token = request.cookies.get("cpcms_refresh")
    if cookie_token:
        token_hash = hash_refresh_token(cookie_token)
        db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).update(
            {"revoked_at": datetime.now(timezone.utc)}
        )
        db.commit()

    response.delete_cookie(key="cpcms_refresh")
    return {"detail": "Logged out successfully."}


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return _build_user_out(current_user)
