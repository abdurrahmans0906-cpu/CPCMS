import uuid
from datetime import datetime, timezone, timedelta
from app.models.user import User, Student, Faculty, Course
from app.models.project import Project, ProjectStudent
from app.models.team import Team, TeamMember


def test_course_and_project_lifecycle(client, faculty_user, auth_headers_faculty):
    # 1. Create Course
    course_res = client.post("/api/v1/courses", headers=auth_headers_faculty, json={
        "code": "CSE4001",
        "name": "Cloud Computing Architecture",
        "department": "Computer Science and Engineering",
    })
    assert course_res.status_code == 201
    course_id = course_res.json()["id"]

    # 2. Create Project
    now = datetime.now(timezone.utc)
    proj_payload = {
        "course_id": course_id,
        "name": "Distributed Storage Engine",
        "semester": "Fall",
        "academic_year": "2026-2027",
        "description": "Build high performance blob store.",
        "problem_statement": "Storage scaling bottlenecks.",
        "objectives": "1. Build consensus layer\n2. Replicate partitions",
        "min_team_size": 2,
        "max_team_size": 3,
        "team_formation_mode": "hybrid",
        "team_formation_deadline": (now + timedelta(days=10)).isoformat(),
        "max_projects_per_student": 1,
        "allowed_file_exts": [".pdf", ".zip", ".md"],
        "max_file_mb": 20,
        "late_policy": "allow_penalty",
        "late_penalty_percent": 10.0,
        "versioning_required": True,
        "git_required": True,
        "baseline_frequency": "per_review",
        "change_request_required": True,
        "approval_required": True,
        "branching_policy": "gitflow_lite",
        "total_marks": 100,
        "themes": ["Distributed Systems", "Cloud Infrastructure"],
        "outcomes": ["Understand Raft consensus", "Build blob engine"],
        "ci_templates": [
            {"name": "SRS Spec", "ci_type": "requirements", "position": 1},
            {"name": "API Service", "ci_type": "backend", "position": 2},
        ],
        "deadlines": [
            {"kind": "proposal", "title": "Proposal Submission", "due_at": (now + timedelta(days=5)).isoformat()},
        ],
        "criteria": [
            {"name": "Architecture", "max_marks": 50, "position": 1},
            {"name": "Implementation", "max_marks": 50, "position": 2},
        ],
    }
    proj_res = client.post("/api/v1/projects", headers=auth_headers_faculty, json=proj_payload)
    assert proj_res.status_code == 201
    proj_data = proj_res.json()
    assert proj_data["name"] == "Distributed Storage Engine"
    assert len(proj_data["themes"]) == 2
    assert len(proj_data["evaluation_criteria"]) == 2


def test_student_enrollment_and_project_limit(client, db_session, faculty_user, student_user, auth_headers_faculty):
    # Setup Course and Project with max_projects_per_student = 1
    course = Course(
        id=uuid.uuid4(),
        code="CSE2002",
        name="Data Structures",
        department="Computer Science and Engineering",
        faculty_user_id=faculty_user.id,
    )
    db_session.add(course)
    db_session.flush()

    proj1 = Project(
        id=uuid.uuid4(),
        course_id=course.id,
        faculty_user_id=faculty_user.id,
        name="Project One",
        semester="Fall",
        academic_year="2026-2027",
        min_team_size=1,
        max_team_size=2,
        max_projects_per_student=1,
        total_marks=100,
        status="active",
    )
    proj2 = Project(
        id=uuid.uuid4(),
        course_id=course.id,
        faculty_user_id=faculty_user.id,
        name="Project Two",
        semester="Fall",
        academic_year="2026-2027",
        min_team_size=1,
        max_team_size=2,
        max_projects_per_student=1,
        total_marks=100,
        status="active",
    )
    db_session.add_all([proj1, proj2])
    db_session.commit()

    # Enroll in Project 1
    res1 = client.post(f"/api/v1/projects/{proj1.id}/students", headers=auth_headers_faculty, json={
        "register_numbers": student_user.student_profile.register_number
    })
    assert res1.status_code == 200

    # Attempt to enroll in Project 2 (exceeds max_projects_per_student = 1)
    res2 = client.post(f"/api/v1/projects/{proj2.id}/students", headers=auth_headers_faculty, json={
        "register_numbers": student_user.student_profile.register_number
    })
    assert res2.status_code == 400
    assert "limit" in res2.json()["detail"].lower()


def test_team_formation_invitation_flow(
    client, db_session, faculty_user, student_user, student_user_2,
    auth_headers_faculty, auth_headers_student
):
    # Setup Course and Project
    course = Course(
        id=uuid.uuid4(),
        code="CSE3003",
        name="Web Engineering",
        department="Computer Science and Engineering",
        faculty_user_id=faculty_user.id,
    )
    db_session.add(course)
    db_session.flush()

    proj = Project(
        id=uuid.uuid4(),
        course_id=course.id,
        faculty_user_id=faculty_user.id,
        name="Social Graph Application",
        semester="Fall",
        academic_year="2026-2027",
        min_team_size=2,
        max_team_size=3,
        team_formation_mode="hybrid",
        max_projects_per_student=2,
        total_marks=100,
        status="active",
    )
    db_session.add(proj)
    db_session.flush()

    # Enroll both students
    db_session.add(ProjectStudent(
        id=uuid.uuid4(),
        project_id=proj.id,
        register_number=student_user.student_profile.register_number,
        student_user_id=student_user.id,
    ))
    db_session.add(ProjectStudent(
        id=uuid.uuid4(),
        project_id=proj.id,
        register_number=student_user_2.student_profile.register_number,
        student_user_id=student_user_2.id,
    ))
    db_session.commit()

    # Student 1 creates Team
    team_res = client.post(f"/api/v1/projects/{proj.id}/teams", headers=auth_headers_student, json={
        "title": "Graph Masters"
    })
    assert team_res.status_code == 201
    team_data = team_res.json()
    team_id = team_data["id"]
    assert team_data["title"] == "Graph Masters"
    assert len(team_data["members"]) == 1
    assert team_data["members"][0]["role"] == "leader"

    # Student 1 invites Student 2
    inv_res = client.post(f"/api/v1/teams/{team_id}/invitations", headers=auth_headers_student, json={
        "invitee_register_number": student_user_2.student_profile.register_number
    })
    assert inv_res.status_code == 201
    inv_id = inv_res.json()["id"]

    # Student 2 accepts invitation
    from app.security import create_access_token
    token_s2 = create_access_token({"sub": str(student_user_2.id), "role": "STUDENT"})
    headers_s2 = {"Authorization": f"Bearer {token_s2}"}

    resp_inv = client.post(f"/api/v1/invitations/{inv_id}/accept", headers=headers_s2)
    assert resp_inv.status_code == 200

    # Verify team has 2 members
    t_check = client.get(f"/api/v1/teams/{team_id}", headers=auth_headers_student)
    assert t_check.status_code == 200
    assert len(t_check.json()["members"]) == 2
