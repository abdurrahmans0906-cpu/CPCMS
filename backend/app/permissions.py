from typing import Optional, Union
import uuid
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db import get_db
from app.security import decode_token
from app.models.user import User, Student, Faculty
from app.models.project import Project, ProjectStudent
from app.models.team import Team, TeamMember

security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing subject",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account does not exist or is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_student(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "STUDENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Action is restricted to students only"
        )
    return current_user


def require_faculty(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "FACULTY":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Action is restricted to faculty only"
        )
    return current_user


def get_project_with_access(
    project_id: uuid.UUID,
    user: User,
    db: Session
) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if user.role == "FACULTY":
        if project.faculty_user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return project

    if user.role == "STUDENT":
        enrollment = db.query(ProjectStudent).filter(
            ProjectStudent.project_id == project_id,
            (ProjectStudent.student_user_id == user.id) | (
                ProjectStudent.register_number == (
                    db.query(Student.register_number).filter(Student.user_id == user.id).scalar_subquery()
                )
            )
        ).first()
        if not enrollment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        return project

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")


def get_team_with_access(
    team_id: uuid.UUID,
    user: User,
    db: Session
) -> Team:
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    project = db.query(Project).filter(Project.id == team.project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if user.role == "FACULTY":
        if project.faculty_user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
        return team

    if user.role == "STUDENT":
        # Check membership
        membership = db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.student_user_id == user.id
        ).first()
        if not membership:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
        return team

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")


def is_team_leader_or_faculty(team: Team, user: User, db: Session) -> bool:
    if user.role == "FACULTY":
        return team.project.faculty_user_id == user.id
    membership = db.query(TeamMember).filter(
        TeamMember.team_id == team.id,
        TeamMember.student_user_id == user.id
    ).first()
    return membership is not None and membership.role == "leader"
