import uuid
import pytest
from app.models.user import User, Student, Faculty, Course
from app.models.project import Project
from app.models.team import Team, TeamMember
from app.models.scm import ConfigurationItem, CIVersion
from app.models.baseline import Baseline, baseline_items


@pytest.fixture
def setup_cr_graph_context(db_session, faculty_user, student_user):
    course = Course(
        id=uuid.uuid4(),
        code="CSE3005",
        name="Software Maintenance",
        department="Computer Science and Engineering",
        faculty_user_id=faculty_user.id,
    )
    db_session.add(course)
    db_session.flush()

    proj = Project(
        id=uuid.uuid4(),
        course_id=course.id,
        faculty_user_id=faculty_user.id,
        name="Graph Maintenance Project",
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
        title="Impact Analyzers",
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

    # Create 3 CIs: CI-001 -> CI-002 (depends on 1) -> CI-003 (depends on 2)
    ci1 = ConfigurationItem(
        id=uuid.uuid4(),
        team_id=team.id,
        ci_code="CI-001",
        name="Core Auth Spec",
        ci_type="requirements",
        owner_user_id=student_user.id,
        status="approved",
        is_locked=True,
    )
    ci2 = ConfigurationItem(
        id=uuid.uuid4(),
        team_id=team.id,
        ci_code="CI-002",
        name="User DB Schema",
        ci_type="database_design",
        owner_user_id=student_user.id,
        status="approved",
        is_locked=True,
    )
    ci3 = ConfigurationItem(
        id=uuid.uuid4(),
        team_id=team.id,
        ci_code="CI-003",
        name="Auth Service API",
        ci_type="backend",
        owner_user_id=student_user.id,
        status="draft",
        is_locked=False,
    )
    ci2.dependencies.append(ci1)
    ci3.dependencies.append(ci2)

    db_session.add_all([ci1, ci2, ci3])
    db_session.flush()

    # Version and Baseline for CI-001
    v1 = CIVersion(
        id=uuid.uuid4(),
        ci_id=ci1.id,
        major=1,
        minor=0,
        version_label="1.0",
        content_sha256="1111111111111111111111111111111111111111111111111111111111111111",
        change_description="Auth spec v1",
        kind="upload",
        status="approved",
        approved_by=faculty_user.id,
        created_by=student_user.id,
    )
    db_session.add(v1)
    db_session.flush()
    ci1.current_version_id = v1.id

    bl = Baseline(
        id=uuid.uuid4(),
        team_id=team.id,
        code="BL-001",
        name="Initial Security Baseline",
        status="locked",
        created_by=faculty_user.id,
    )
    db_session.add(bl)
    db_session.flush()
    db_session.execute(baseline_items.insert().values([{"baseline_id": bl.id, "ci_version_id": v1.id}]))

    db_session.commit()
    return {"team": team, "ci1": ci1, "ci2": ci2, "ci3": ci3, "baseline": bl}


def test_cr_creation_impact_analysis_and_lifecycle(
    client, setup_cr_graph_context, auth_headers_student, auth_headers_faculty
):
    team = setup_cr_graph_context["team"]
    ci1 = setup_cr_graph_context["ci1"]
    ci2 = setup_cr_graph_context["ci2"]
    ci3 = setup_cr_graph_context["ci3"]

    # 1. Create CR affecting only CI-001 directly
    cr_res = client.post(f"/api/v1/teams/{team.id}/change-requests", headers=auth_headers_student, json={
        "title": "Migrate to OAuth 2.1 & Passkeys",
        "description": "Deprecate password login in favor of WebAuthn credentials.",
        "reason": "Security audit recommendation.",
        "priority": "high",
        "affected_ci_ids": [str(ci1.id)],
        "components": ["backend", "database"],
    })
    assert cr_res.status_code == 201
    cr_data = cr_res.json()
    cr_id = cr_data["id"]
    assert cr_data["status"] == "draft"

    # 2. Query Impact Analysis: CI-002 and CI-003 must be detected as indirectly affected!
    impact_res = client.get(f"/api/v1/change-requests/{cr_id}/impact", headers=auth_headers_student)
    assert impact_res.status_code == 200
    impact = impact_res.json()

    direct_codes = [c["ci_code"] for c in impact["directly_affected_cis"]]
    assert "CI-001" in direct_codes

    indirect_codes = [c["ci_code"] for c in impact["indirectly_affected_cis"]]
    assert "CI-002" in indirect_codes
    assert "CI-003" in indirect_codes

    # Affected baselines
    bl_codes = [b["code"] for b in impact["affected_baselines"]]
    assert "BL-001" in bl_codes

    # 3. Transition: Draft -> Submitted (Student)
    sub_res = client.post(f"/api/v1/change-requests/{cr_id}/transition", headers=auth_headers_student, json={
        "to_status": "submitted",
        "comment": "Submitting for review",
    })
    assert sub_res.status_code == 200
    assert sub_res.json()["status"] == "submitted"

    # 4. Transition: Submitted -> Under Review (Faculty)
    rev_res = client.post(f"/api/v1/change-requests/{cr_id}/transition", headers=auth_headers_faculty, json={
        "to_status": "under_review",
        "comment": "Reviewing impact graph",
    })
    assert rev_res.status_code == 200
    assert rev_res.json()["status"] == "under_review"

    # 5. Reject without comment must fail
    fail_rej = client.post(f"/api/v1/change-requests/{cr_id}/transition", headers=auth_headers_faculty, json={
        "to_status": "rejected",
        "comment": "",
    })
    assert fail_rej.status_code == 400

    # 6. Approve CR (Faculty)
    appr_res = client.post(f"/api/v1/change-requests/{cr_id}/transition", headers=auth_headers_faculty, json={
        "to_status": "approved",
        "comment": "Approved. Proceed with branch cr-oauth.",
    })
    assert appr_res.status_code == 200
    assert appr_res.json()["status"] == "approved"
