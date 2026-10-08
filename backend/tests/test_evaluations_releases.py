import uuid
import pytest
from app.models.user import User, Student, Faculty, Course
from app.models.project import Project, EvaluationCriteria
from app.models.team import Team, TeamMember
from app.models.scm import ConfigurationItem, CIVersion
from app.models.baseline import Baseline, baseline_items


@pytest.fixture
def setup_eval_rel_context(db_session, faculty_user, student_user):
    course = Course(
        id=uuid.uuid4(),
        code="CSE3006",
        name="Capstone Project",
        department="Computer Science and Engineering",
        faculty_user_id=faculty_user.id,
    )
    db_session.add(course)
    db_session.flush()

    proj = Project(
        id=uuid.uuid4(),
        course_id=course.id,
        faculty_user_id=faculty_user.id,
        name="Evaluation & Release Testing",
        semester="Fall",
        academic_year="2026-2027",
        total_marks=100,
        status="active",
    )
    db_session.add(proj)
    db_session.flush()

    c1 = EvaluationCriteria(id=uuid.uuid4(), project_id=proj.id, position=1, name="SRS", max_marks=40)
    c2 = EvaluationCriteria(id=uuid.uuid4(), project_id=proj.id, position=2, name="Implementation", max_marks=60)
    db_session.add_all([c1, c2])

    team = Team(
        id=uuid.uuid4(),
        project_id=proj.id,
        number=1,
        title="Release Champions",
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

    # CIs & Approved Versions
    ci_doc = ConfigurationItem(
        id=uuid.uuid4(),
        team_id=team.id,
        ci_code="CI-001",
        name="SRS Spec",
        ci_type="requirements",
        owner_user_id=student_user.id,
        status="approved",
        is_locked=True,
    )
    ci_test = ConfigurationItem(
        id=uuid.uuid4(),
        team_id=team.id,
        ci_code="CI-002",
        name="Test Suite Report",
        ci_type="test_report",
        owner_user_id=student_user.id,
        status="approved",
        is_locked=True,
    )
    db_session.add_all([ci_doc, ci_test])
    db_session.flush()

    v1 = CIVersion(
        id=uuid.uuid4(),
        ci_id=ci_doc.id,
        major=1,
        minor=0,
        version_label="1.0",
        content_sha256="1234567890123456789012345678901234567890123456789012345678901234",
        change_description="SRS approved",
        kind="upload",
        status="approved",
        approved_by=faculty_user.id,
        created_by=student_user.id,
    )
    v2 = CIVersion(
        id=uuid.uuid4(),
        ci_id=ci_test.id,
        major=1,
        minor=0,
        version_label="1.0",
        content_sha256="9876543210987654321098765432109876543210987654321098765432109876",
        change_description="Test report approved",
        kind="upload",
        status="approved",
        approved_by=faculty_user.id,
        created_by=student_user.id,
    )
    db_session.add_all([v1, v2])
    db_session.flush()

    ci_doc.current_version_id = v1.id
    ci_test.current_version_id = v2.id

    bl = Baseline(
        id=uuid.uuid4(),
        team_id=team.id,
        code="BL-001",
        name="Final Release Baseline",
        status="locked",
        created_by=faculty_user.id,
    )
    db_session.add(bl)
    db_session.flush()
    db_session.execute(baseline_items.insert().values([
        {"baseline_id": bl.id, "ci_version_id": v1.id},
        {"baseline_id": bl.id, "ci_version_id": v2.id},
    ]))

    db_session.commit()
    return {"project": proj, "team": team, "c1": c1, "c2": c2, "baseline": bl}


def test_evaluations_marks_and_grade_calculation(
    client, setup_eval_rel_context, auth_headers_faculty
):
    team = setup_eval_rel_context["team"]
    c1 = setup_eval_rel_context["c1"]
    c2 = setup_eval_rel_context["c2"]

    # 1. Invalid evaluation (exceeding criterion max marks)
    bad_res = client.post(f"/api/v1/teams/{team.id}/evaluations", headers=auth_headers_faculty, json={
        "stage": "final",
        "scores": [
            {"criterion_id": str(c1.id), "marks": 45},  # Max is 40!
            {"criterion_id": str(c2.id), "marks": 55},
        ],
        "feedback": "Invalid score test",
    })
    assert bad_res.status_code == 400

    # 2. Valid evaluation (38/40 + 56/60 = 94/100 -> Grade S)
    good_res = client.post(f"/api/v1/teams/{team.id}/evaluations", headers=auth_headers_faculty, json={
        "stage": "final",
        "scores": [
            {"criterion_id": str(c1.id), "marks": 38},
            {"criterion_id": str(c2.id), "marks": 56},
        ],
        "feedback": "Outstanding implementation and SCM compliance.",
    })
    assert good_res.status_code == 201
    eval_data = good_res.json()
    assert eval_data["total_marks"] == 94.0
    assert eval_data["grade"] == "S"


def test_release_creation_and_approval(
    client, setup_eval_rel_context, auth_headers_student, auth_headers_faculty
):
    team = setup_eval_rel_context["team"]
    bl = setup_eval_rel_context["baseline"]

    # 1. Request Release
    rel_res = client.post(f"/api/v1/teams/{team.id}/releases", headers=auth_headers_student, json={
        "code": "REL-1.0.0",
        "baseline_id": str(bl.id),
        "version": "1.0.0",
        "notes": "Candidate release 1.0.0",
    })
    assert rel_res.status_code == 201
    rel_data = rel_res.json()
    rel_id = rel_data["id"]
    assert rel_data["code"] == "REL-1.0.0"
    assert rel_data["status"] == "requested"

    # 2. Approve Release (Faculty)
    appr_res = client.post(f"/api/v1/releases/{rel_id}/decision", headers=auth_headers_faculty, json={
        "decision": "approved",
        "test_status": "passed",
        "doc_status": "approved",
        "feedback": "Approved for release.",
    })
    assert appr_res.status_code == 200
    assert appr_res.json()["status"] == "approved"
