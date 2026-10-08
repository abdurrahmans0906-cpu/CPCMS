import pytest
from app.models.user import User, Student, Faculty


def test_student_registration_success(client, db_session):
    payload = {
        "name": "Karthik Raja",
        "email": "karthik.raja@univ.edu",
        "register_number": "23mis0100",  # Lowercase to test uppercase normalization
        "department": "Computer Science and Engineering",
        "password": "Password123!",
        "confirm_password": "Password123!",
    }
    response = client.post("/api/v1/auth/register/student", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "STUDENT"
    assert data["email"] == "karthik.raja@univ.edu"
    assert data["register_number"] == "23MIS0100"  # Stored uppercase

    # Verify in DB
    user = db_session.query(User).filter(User.email == "karthik.raja@univ.edu").first()
    assert user is not None
    assert user.student_profile.register_number == "23MIS0100"


def test_student_duplicate_register_number_rejected(client, student_user):
    payload = {
        "name": "Duplicate Student",
        "email": "duplicate@univ.edu",
        "register_number": student_user.student_profile.register_number,
        "department": "Computer Science and Engineering",
        "password": "Password123!",
        "confirm_password": "Password123!",
    }
    response = client.post("/api/v1/auth/register/student", json=payload)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_faculty_registration_success(client, db_session):
    payload = {
        "name": "Dr. S. Sundaram",
        "email": "sundaram.s@univ.edu",
        "faculty_code": "FAC2050",
        "department": "Computer Science and Engineering",
        "password": "Password123!",
        "invite_code": "FACULTY2026",
    }
    response = client.post("/api/v1/auth/register/faculty", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "FACULTY"
    assert data["faculty_code"] == "FAC2050"


def test_login_with_email_and_student_id(client, student_user):
    # 1. Login with Email
    res1 = client.post("/api/v1/auth/login", json={
        "identifier": student_user.email,
        "password": "Password123!"
    })
    assert res1.status_code == 200
    assert "access_token" in res1.json()

    # 2. Login with Student ID (register_number)
    res2 = client.post("/api/v1/auth/login", json={
        "identifier": student_user.student_profile.register_number.lower(),
        "password": "Password123!"
    })
    assert res2.status_code == 200
    assert "access_token" in res2.json()


def test_account_lockout_after_5_failed_attempts(client, student_user):
    # 5 failed password attempts
    for _ in range(5):
        res = client.post("/api/v1/auth/login", json={
            "identifier": student_user.email,
            "password": "WrongPassword!"
        })
        assert res.status_code in [400, 401, 403]

    # 6th attempt should return 403 / account locked
    res6 = client.post("/api/v1/auth/login", json={
        "identifier": student_user.email,
        "password": "Password123!"  # Even correct password is now locked
    })
    assert res6.status_code == 403
    assert "locked" in res6.json()["detail"].lower()


def test_get_current_user_me(client, auth_headers_student, student_user):
    response = client.get("/api/v1/auth/me", headers=auth_headers_student)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(student_user.id)
    assert data["email"] == student_user.email
    assert data["role"] == "STUDENT"
