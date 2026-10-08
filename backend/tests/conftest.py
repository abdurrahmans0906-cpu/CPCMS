import os
import sys
import uuid
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import Base, get_db
from app.main import app
from app.config import settings
from app.security import hash_password, create_access_token
from app.models.user import User, Student, Faculty, Course
from app.models.project import (
    Project, ProjectTheme, ProjectOutcome, ProjectCITemplate,
    ProjectDeadline, EvaluationCriteria, Review, ProjectStudent
)
from app.models.team import Team, TeamMember
from app.models.scm import ConfigurationItem, CIVersion, FileModel, ci_dependencies
from app.models.baseline import Baseline, baseline_items
from app.models.change_request import ChangeRequest, ChangeRequestItem, ChangeRequestComponent, ChangeTransition
from app.models.evaluation import Evaluation, EvaluationScore
from app.models.release import Release

TEST_DATABASE_URL = "postgresql+psycopg://postgres:1234567890@127.0.0.1:5432/cpcms_test"

engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Ensure schema exists on the test database."""
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup at end of session if desired


from sqlalchemy import text

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for a test, clearing tables before run."""
    db = TestingSessionLocal()
    try:
        db.execute(text("ALTER TABLE audit_logs DISABLE TRIGGER ALL;"))
        db.execute(text("ALTER TABLE ci_versions DISABLE TRIGGER ALL;"))
        db.execute(text("""
            TRUNCATE TABLE 
                users, courses, projects, project_students, teams, team_members, 
                team_invitations, proposals, files, configuration_items, ci_versions, 
                baselines, change_requests, change_request_items, change_request_components, 
                change_transitions, evaluations, evaluation_scores, releases, audit_logs, 
                notifications, refresh_tokens, repositories, branches, commits CASCADE;
        """))
        db.execute(text("ALTER TABLE audit_logs ENABLE TRIGGER ALL;"))
        db.execute(text("ALTER TABLE ci_versions ENABLE TRIGGER ALL;"))
        db.commit()
    except Exception as e:
        db.rollback()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def faculty_user(db_session):
    now = datetime.now(timezone.utc)
    user = User(
        id=uuid.uuid4(),
        role="FACULTY",
        name="Dr. Test Faculty",
        email="faculty.test@univ.edu",
        password_hash=hash_password("Password123!"),
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    prof = Faculty(
        user_id=user.id,
        faculty_code="FAC9999",
        department="Computer Science and Engineering",
    )
    db_session.add(prof)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def student_user(db_session):
    now = datetime.now(timezone.utc)
    user = User(
        id=uuid.uuid4(),
        role="STUDENT",
        name="Test Student",
        email="student.test@univ.edu",
        password_hash=hash_password("Password123!"),
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    prof = Student(
        user_id=user.id,
        register_number="23MIS0999",
        department="Computer Science and Engineering",
    )
    db_session.add(prof)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def student_user_2(db_session):
    user = User(
        id=uuid.uuid4(),
        role="STUDENT",
        name="Second Student",
        email="student2.test@univ.edu",
        password_hash=hash_password("Password123!"),
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    prof = Student(
        user_id=user.id,
        register_number="23MIS0998",
        department="Computer Science and Engineering",
    )
    db_session.add(prof)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers_faculty(faculty_user):
    token = create_access_token({"sub": str(faculty_user.id), "role": "FACULTY"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_student(student_user):
    token = create_access_token({"sub": str(student_user.id), "role": "STUDENT"})
    return {"Authorization": f"Bearer {token}"}
