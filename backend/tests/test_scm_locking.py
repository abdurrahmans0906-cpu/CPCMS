import io
import uuid
import pytest
from datetime import datetime, timezone
from app.models.user import User, Student, Faculty, Course
from app.models.project import Project, ProjectStudent
from app.models.team import Team, TeamMember
from app.models.scm import ConfigurationItem, CIVersion
from app.models.baseline import Baseline, baseline_items


@pytest.fixture
def setup_scm_context(db_session, faculty_user, student_user):
    course = Course(
        id=uuid.uuid4(),
        code="CSE3004",
        name="Software Architecture",
        department="Computer Science and Engineering",
        faculty_user_id=faculty_user.id,
    )
    db_session.add(course)
    db_session.flush()

    proj = Project(
        id=uuid.uuid4(),
        course_id=course.id,
        faculty_user_id=faculty_user.id,
        name="SCM Arch Project",
        semester="Fall",
        academic_year="2026-2027",
        min_team_size=1,
        max_team_size=2,
        total_marks=100,
        status="active",
    )
    db_session.add(proj)
    db_session.flush()

    team = Team(
        id=uuid.uuid4(),
        project_id=proj.id,
        number=1,
        title="Arch Pioneers",
        status="development",
        formed_by="student",
    )
    db_session.add(team)
    db_session.flush()

    db_session.add(TeamMember(
        team_id=team.id,
        project_id=proj.id,
        student_user_id=student_user.id,
        role="leader",
    ))
    db_session.commit()
    return {"project": proj, "team": team}


def test_ci_creation_and_version_upload(client, setup_scm_context, auth_headers_student):
    team = setup_scm_context["team"]

    # 1. Create CI
    ci_res = client.post(f"/api/v1/teams/{team.id}/cis", headers=auth_headers_student, json={
        "name": "SRS Document",
        "ci_type": "requirements",
    })
    assert ci_res.status_code == 201
    ci_data = ci_res.json()
    ci_id = ci_data["id"]
    assert ci_data["ci_code"] == "CI-001"
    assert ci_data["is_locked"] is False

    # 2. Upload Version 1.0
    file_content = b"# Requirements Document v1.0\nInitial functional specs."
    files = {
        "file": ("srs_v1.md", io.BytesIO(file_content), "text/markdown"),
    }
    data = {
        "change_description": "Initial SRS specification",
        "major_bump": "false",
    }
    ver_res = client.post(
        f"/api/v1/cis/{ci_id}/versions",
        headers=auth_headers_student,
        files=files,
        data=data
    )
    assert ver_res.status_code == 201
    ver_data = ver_res.json()
    assert ver_data["version_label"] == "1.0"
    assert ver_data["status"] == "draft"

    # 3. Duplicate SHA256 upload rejection
    dup_res = client.post(
        f"/api/v1/cis/{ci_id}/versions",
        headers=auth_headers_student,
        files={"file": ("srs_v1_copy.md", io.BytesIO(file_content), "text/markdown")},
        data={"change_description": "Trying duplicate file", "major_bump": "false"}
    )
    assert dup_res.status_code == 400
    assert "identical" in dup_res.json()["detail"].lower() or "sha" in dup_res.json()["detail"].lower()


def test_baseline_locks_cis_and_blocks_direct_edits(
    client, db_session, setup_scm_context, faculty_user, student_user,
    auth_headers_faculty, auth_headers_student
):
    team = setup_scm_context["team"]

    # 1. Create and approve CI Version
    ci = ConfigurationItem(
        id=uuid.uuid4(),
        team_id=team.id,
        ci_code="CI-001",
        name="Architecture Diagram",
        ci_type="architecture",
        owner_user_id=student_user.id,
        status="approved",
        is_locked=False,
    )
    db_session.add(ci)
    db_session.flush()

    ver = CIVersion(
        id=uuid.uuid4(),
        ci_id=ci.id,
        major=1,
        minor=0,
        version_label="1.0",
        content_sha256="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        change_description="Architecture v1.0",
        kind="upload",
        status="approved",
        approved_by=faculty_user.id,
        created_by=student_user.id,
    )
    db_session.add(ver)
    db_session.flush()
    ci.current_version_id = ver.id
    db_session.commit()

    # 2. Faculty creates Baseline containing this version
    bl_res = client.post(f"/api/v1/teams/{team.id}/baselines", headers=auth_headers_faculty, json={
        "name": "Design Baseline",
        "description": "Locked design baseline",
        "ci_version_ids": [str(ver.id)],
    })
    assert bl_res.status_code == 201
    bl_data = bl_res.json()
    assert bl_data["code"] == "BL-001"
    assert bl_data["status"] == "locked"

    # Verify CI is now locked in DB
    db_session.refresh(ci)
    assert ci.is_locked is True

    # 3. Student attempts to upload new version without CR -> MUST FAIL 400
    new_file = b"# Updated Architecture\nUnauthorized direct edit."
    upload_res = client.post(
        f"/api/v1/cis/{ci.id}/versions",
        headers=auth_headers_student,
        files={"file": ("arch_v2.md", io.BytesIO(new_file), "text/markdown")},
        data={"change_description": "Direct edit attempt", "major_bump": "false"}
    )
    assert upload_res.status_code == 400
    assert "locked" in upload_res.json()["detail"].lower()
