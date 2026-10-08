import uuid
import pytest
from sqlalchemy import text
from app.models.user import User, Student, Course
from app.models.project import Project
from app.models.team import Team
from app.models.scm import ConfigurationItem, CIVersion
from app.models.audit import AuditLog


def test_audit_logs_immutability_trigger(db_session, faculty_user):
    # 1. Insert an audit log record
    log = AuditLog(
        action="TEST_ACTION",
        entity_type="project",
        entity_id=str(uuid.uuid4()),
        actor_user_id=faculty_user.id,
        note="Initial immutable log",
    )
    db_session.add(log)
    db_session.commit()
    log_id = log.id

    # 2. Direct SQL UPDATE must be rejected by PostgreSQL trigger
    with pytest.raises(Exception) as exc_update:
        db_session.execute(
            text("UPDATE audit_logs SET note = 'Tampered log' WHERE id = :id"),
            {"id": log_id}
        )
        db_session.commit()
    db_session.rollback()
    assert "immutable" in str(exc_update.value).lower()

    # 3. Direct SQL DELETE must be rejected by PostgreSQL trigger
    with pytest.raises(Exception) as exc_delete:
        db_session.execute(
            text("DELETE FROM audit_logs WHERE id = :id"),
            {"id": log_id}
        )
        db_session.commit()
    db_session.rollback()
    assert "immutable" in str(exc_delete.value).lower()


def test_ci_versions_immutability_trigger(db_session, faculty_user, student_user):
    # Setup CI and Version
    course = Course(
        id=uuid.uuid4(),
        code="CSE3007",
        name="Trigger Test Course",
        department="Computer Science and Engineering",
        faculty_user_id=faculty_user.id,
    )
    db_session.add(course)
    db_session.flush()

    proj = Project(
        id=uuid.uuid4(),
        course_id=course.id,
        faculty_user_id=faculty_user.id,
        name="Trigger Test Proj",
        semester="Fall",
        academic_year="2026-2027",
        total_marks=100,
        status="active",
    )
    db_session.add(proj)
    db_session.flush()

    team = Team(
        id=uuid.uuid4(),
        project_id=proj.id,
        number=1,
        title="Trigger Team",
        status="development",
        formed_by="student",
    )
    db_session.add(team)
    db_session.flush()

    ci = ConfigurationItem(
        id=uuid.uuid4(),
        team_id=team.id,
        ci_code="CI-001",
        name="Spec File",
        ci_type="requirements",
        owner_user_id=student_user.id,
        status="draft",
    )
    db_session.add(ci)
    db_session.flush()

    ver_id = uuid.uuid4()
    ver = CIVersion(
        id=ver_id,
        ci_id=ci.id,
        major=1,
        minor=0,
        version_label="1.0",
        content_sha256="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        change_description="Initial description",
        kind="upload",
        status="draft",
        created_by=student_user.id,
    )
    db_session.add(ver)
    db_session.commit()

    # 1. Direct SQL DELETE of version must be blocked by trigger
    with pytest.raises(Exception) as exc_del:
        db_session.execute(
            text("DELETE FROM ci_versions WHERE id = :id"),
            {"id": ver_id}
        )
        db_session.commit()
    db_session.rollback()
    assert "cannot be deleted" in str(exc_del.value).lower() or "immutable" in str(exc_del.value).lower()

    # 2. Direct SQL UPDATE of immutable column (content_sha256) must be blocked
    with pytest.raises(Exception) as exc_upd:
        db_session.execute(
            text("UPDATE ci_versions SET content_sha256 = 'tampered' WHERE id = :id"),
            {"id": ver_id}
        )
        db_session.commit()
    db_session.rollback()
    assert "immutable" in str(exc_upd.value).lower()

    # 3. Direct SQL UPDATE of mutable columns (status) should succeed!
    db_session.execute(
        text("UPDATE ci_versions SET status = 'approved' WHERE id = :id"),
        {"id": ver_id}
    )
    db_session.commit()

    db_session.refresh(ver)
    assert ver.status == "approved"
