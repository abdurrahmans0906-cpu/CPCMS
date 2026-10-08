import os
import sys
import uuid
from datetime import datetime, timezone, timedelta

# Ensure backend root is on PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db import SessionLocal
from app.models.user import User, Student, Faculty, Course
from app.models.project import (
    Project, ProjectTheme, ProjectOutcome, ProjectCITemplate,
    ProjectDeadline, EvaluationCriteria, Review, ReviewSlot, ProjectStudent
)
from app.models.team import Team, TeamMember, TeamInvitation
from app.models.proposal import Proposal
from app.models.scm import ConfigurationItem, CIVersion, FileModel, ci_dependencies
from app.models.baseline import Baseline, baseline_items
from app.models.change_request import ChangeRequest, ChangeRequestItem, ChangeRequestComponent, ChangeTransition
from app.models.evaluation import Evaluation, EvaluationScore
from app.models.release import Release
from app.models.git import Repository, Branch, Commit
from app.models.notification import Notification
from app.models.audit import AuditLog
from app.security import hash_password


def seed_database():
    db = SessionLocal()
    try:
        print("--- Starting CPCMS Database Seeding ---")

        # Clean existing data in reverse dependency order
        print("Purging existing data...")
        db.execute(baseline_items.delete())
        db.execute(ci_dependencies.delete())
        db.query(AuditLog).delete()
        db.query(Notification).delete()
        db.query(EvaluationScore).delete()
        db.query(Evaluation).delete()
        db.query(Release).delete()
        db.query(Commit).delete()
        db.query(Branch).delete()
        db.query(Repository).delete()
        db.query(ChangeTransition).delete()
        db.query(ChangeRequestComponent).delete()
        db.query(ChangeRequestItem).delete()
        db.query(ChangeRequest).delete()
        db.query(CIVersion).delete()
        db.query(ConfigurationItem).delete()
        db.query(FileModel).delete()
        db.query(Baseline).delete()
        db.query(Proposal).delete()
        db.query(TeamInvitation).delete()
        db.query(TeamMember).delete()
        db.query(Team).delete()
        db.query(ProjectStudent).delete()
        db.query(ReviewSlot).delete()
        db.query(Review).delete()
        db.query(EvaluationCriteria).delete()
        db.query(ProjectDeadline).delete()
        db.query(ProjectCITemplate).delete()
        db.query(ProjectOutcome).delete()
        db.query(ProjectTheme).delete()
        db.query(Project).delete()
        db.query(Course).delete()
        db.query(Student).delete()
        db.query(Faculty).delete()
        db.query(User).delete()
        db.commit()

        now = datetime.now(timezone.utc)
        pwd_hash = hash_password("Password123!")

        print("Creating Faculty account...")
        faculty_user = User(
            id=uuid.uuid4(),
            role="FACULTY",
            name="Dr. K. Meenakshi",
            email="meenakshi.k@univ.edu",
            password_hash=pwd_hash,
            is_active=True,
            created_at=now - timedelta(days=30),
        )
        db.add(faculty_user)
        db.flush()

        faculty_profile = Faculty(
            user_id=faculty_user.id,
            faculty_code="FAC1042",
            department="Computer Science and Engineering",
        )
        db.add(faculty_profile)

        print("Creating 12 Student accounts...")
        students_data = [
            ("Rahul Sharma", "23MIS0475", "rahul.sharma@univ.edu"),
            ("Priya Nair", "23MIS0480", "priya.nair@univ.edu"),
            ("Amit Patel", "23MIS0485", "amit.patel@univ.edu"),
            ("Sneha Reddy", "23MIS0490", "sneha.reddy@univ.edu"),
            ("Karthik Iyer", "23MIS0495", "karthik.iyer@univ.edu"),
            ("Ananya Deshmukh", "23MIS0500", "ananya.deshmukh@univ.edu"),
            ("Rohan Gupta", "23MIS0505", "rohan.gupta@univ.edu"),
            ("Divya Menon", "23MIS0510", "divya.menon@univ.edu"),
            ("Vikram Joshi", "23MIS0515", "vikram.joshi@univ.edu"),
            ("Pooja Verma", "23MIS0520", "pooja.verma@univ.edu"),
            ("Siddharth Rao", "23MIS0525", "siddharth.rao@univ.edu"),
            ("Kavita Sen", "23MIS0530", "kavita.sen@univ.edu"),
        ]

        student_users = {}
        for name, reg, email in students_data:
            s_user = User(
                id=uuid.uuid4(),
                role="STUDENT",
                name=name,
                email=email,
                password_hash=pwd_hash,
                is_active=True,
                created_at=now - timedelta(days=25),
            )
            db.add(s_user)
            db.flush()

            s_prof = Student(
                user_id=s_user.id,
                register_number=reg,
                department="Computer Science and Engineering",
            )
            db.add(s_prof)
            student_users[reg] = s_user

        print("Creating Course...")
        course = Course(
            id=uuid.uuid4(),
            code="CSE3001",
            name="Software Engineering",
            department="Computer Science and Engineering",
            faculty_user_id=faculty_user.id,
            created_at=now - timedelta(days=20),
        )
        db.add(course)
        db.flush()

        print("Creating Project...")
        project = Project(
            id=uuid.uuid4(),
            course_id=course.id,
            faculty_user_id=faculty_user.id,
            name="Capstone SCM Web Platform 2026",
            semester="Fall",
            academic_year="2026-2027",
            description="Design and implementation of an end-to-end Course Project Configuration and Management System with baseline control, change auditing, and Git integration.",
            problem_statement="Academic project workflows lack rigorous configuration identification, automated change impact analysis, and verifiable release audit trails.",
            objectives="1. Implement SCM core with immutable versioning\n2. Automate change request workflows\n3. Establish baseline governance\n4. Provide status accounting",
            min_team_size=3,
            max_team_size=4,
            team_formation_mode="hybrid",
            team_formation_deadline=now + timedelta(days=14),
            max_projects_per_student=2,
            allowed_file_exts=[".pdf", ".docx", ".zip", ".txt", ".md", ".json"],
            max_file_mb=25,
            late_policy="allow_penalty",
            late_penalty_percent=10,
            versioning_required=True,
            git_required=True,
            baseline_frequency="per_milestone",
            change_request_required=True,
            approval_required=True,
            branching_policy="gitflow_lite",
            total_marks=100,
            grade_bands={"S": 90, "A": 80, "B": 70, "C": 60, "D": 50, "F": 0},
            status="active",
            created_at=now - timedelta(days=18),
        )
        db.add(project)
        db.flush()

        # Enroll all 12 students in project_students
        for name, reg, email in students_data:
            s_user = student_users[reg]
            db.add(ProjectStudent(
                id=uuid.uuid4(),
                project_id=project.id,
                register_number=reg,
                student_user_id=s_user.id,
                added_at=now - timedelta(days=18),
            ))

        # Themes
        t1 = ProjectTheme(id=uuid.uuid4(), project_id=project.id, name="Enterprise Cloud Systems")
        t2 = ProjectTheme(id=uuid.uuid4(), project_id=project.id, name="Decentralized Ledgers")
        t3 = ProjectTheme(id=uuid.uuid4(), project_id=project.id, name="AI-Assisted Development")
        db.add_all([t1, t2, t3])
        db.flush()

        # Outcomes
        db.add_all([
            ProjectOutcome(id=uuid.uuid4(), project_id=project.id, position=1, text="Formulate rigorous Software Requirements Specifications (SRS)"),
            ProjectOutcome(id=uuid.uuid4(), project_id=project.id, position=2, text="Architect modular system blueprints with dependency matrices"),
            ProjectOutcome(id=uuid.uuid4(), project_id=project.id, position=3, text="Establish controlled baselines and maintain configuration status accounting"),
        ])

        # CI Templates
        db.add_all([
            ProjectCITemplate(id=uuid.uuid4(), project_id=project.id, position=1, name="SRS Document", ci_type="requirements"),
            ProjectCITemplate(id=uuid.uuid4(), project_id=project.id, position=2, name="System Architecture & DB Schema", ci_type="architecture"),
            ProjectCITemplate(id=uuid.uuid4(), project_id=project.id, position=3, name="Backend Core API", ci_type="backend"),
            ProjectCITemplate(id=uuid.uuid4(), project_id=project.id, position=4, name="Frontend Web Application", ci_type="frontend"),
            ProjectCITemplate(id=uuid.uuid4(), project_id=project.id, position=5, name="Test Suite & Audit Matrix", ci_type="test_cases"),
        ])

        # Deadlines
        db.add_all([
            ProjectDeadline(id=uuid.uuid4(), project_id=project.id, kind="team_formation", title="Team Formation Deadline", due_at=now + timedelta(days=5)),
            ProjectDeadline(id=uuid.uuid4(), project_id=project.id, kind="proposal", title="Proposal & Theme Selection", due_at=now + timedelta(days=12)),
            ProjectDeadline(id=uuid.uuid4(), project_id=project.id, kind="srs", title="SRS & Functional Baseline BL-001", due_at=now + timedelta(days=25)),
            ProjectDeadline(id=uuid.uuid4(), project_id=project.id, kind="review", title="Mid-Semester Evaluation Review", due_at=now + timedelta(days=45)),
            ProjectDeadline(id=uuid.uuid4(), project_id=project.id, kind="final", title="Final Release REL-1.0.0 Submission", due_at=now + timedelta(days=70)),
        ])

        # Criteria (Sum = 100)
        c1 = EvaluationCriteria(id=uuid.uuid4(), project_id=project.id, position=1, name="SRS & Requirements Engineering", max_marks=20)
        c2 = EvaluationCriteria(id=uuid.uuid4(), project_id=project.id, position=2, name="Architecture & SCM Baselines", max_marks=25)
        c3 = EvaluationCriteria(id=uuid.uuid4(), project_id=project.id, position=3, name="Implementation & Testing", max_marks=35)
        c4 = EvaluationCriteria(id=uuid.uuid4(), project_id=project.id, position=4, name="Status Accounting & Audit Compliance", max_marks=20)
        db.add_all([c1, c2, c3, c4])

        # Reviews
        r1 = Review(
            id=uuid.uuid4(),
            project_id=project.id,
            title="Mid-Semester SCM Audit Review",
            start_at=now + timedelta(days=45),
            mode="offline",
            venue="Lab 304, CS Block",
            agenda="Verification of baseline BL-001, audit log compliance, and change requests.",
            instructions="Each team has 15 minutes to present architecture diffs and test matrices."
        )
        r2 = Review(
            id=uuid.uuid4(),
            project_id=project.id,
            title="Final Project Evaluation & Demonstration",
            start_at=now + timedelta(days=70),
            mode="online",
            meeting_link="https://meet.univ.edu/cse3001-eval",
            agenda="Final release audit, demonstration of working build, and code inspection.",
            instructions="Ensure all CIs are approved, test reports attached, and release tag verified."
        )
        db.add_all([r1, r2])
        db.flush()

        print("--- Seeding Team 1 (Forming stage) ---")
        team1 = Team(
            id=uuid.uuid4(),
            project_id=project.id,
            number=1,
            title="CloudSync Distributed File System",
            status="team_formation",
            formed_by="student",
            is_delayed=False,
            created_at=now - timedelta(days=10),
        )
        db.add(team1)
        db.flush()

        db.add(TeamMember(
            team_id=team1.id,
            project_id=project.id,
            student_user_id=student_users["23MIS0475"].id,
            role="leader",
            joined_at=now - timedelta(days=10),
        ))
        db.add(TeamMember(
            team_id=team1.id,
            project_id=project.id,
            student_user_id=student_users["23MIS0480"].id,
            role="member",
            joined_at=now - timedelta(days=9),
        ))
        # Pending invitation to Amit Patel
        db.add(TeamInvitation(
            id=uuid.uuid4(),
            team_id=team1.id,
            invited_by=student_users["23MIS0475"].id,
            invitee_user_id=student_users["23MIS0485"].id,
            status="pending",
            created_at=now - timedelta(days=2),
        ))

        print("--- Seeding Team 2 (Development stage with Baselines and CR) ---")
        team2 = Team(
            id=uuid.uuid4(),
            project_id=project.id,
            number=2,
            title="DevSecOps CI/CD Automation Pipeline",
            status="development",
            formed_by="student",
            is_delayed=False,
            created_at=now - timedelta(days=15),
        )
        db.add(team2)
        db.flush()

        for idx, reg in enumerate(["23MIS0490", "23MIS0495", "23MIS0500", "23MIS0505"]):
            db.add(TeamMember(
                team_id=team2.id,
                project_id=project.id,
                student_user_id=student_users[reg].id,
                role="leader" if idx == 0 else "member",
                joined_at=now - timedelta(days=15),
            ))

        # Approved Proposal for Team 2
        prop2 = Proposal(
            id=uuid.uuid4(),
            team_id=team2.id,
            revision_no=1,
            title="Automated Pipeline for Static Security Analysis and Artifact Auditing",
            abstract="A comprehensive CI/CD pipeline integrated with SCM hooks to scan commits, enforce branching rules, and log baseline changes.",
            problem_statement="Modern software projects frequently suffer from configuration drift and unauthorized production pushes.",
            objectives="1. Construct static analysis pipeline\n2. Enforce immutable release tags\n3. Provide automatic audit reports",
            theme_id=t1.id,
            expected_outcome="Automated verification harness running against all baseline revisions.",
            status="approved",
            faculty_feedback="Solid proposal with clear SCM alignment. Approved to begin development.",
            submitted_by=student_users["23MIS0490"].id,
            reviewed_by=faculty_user.id,
            reviewed_at=now - timedelta(days=12),
            created_at=now - timedelta(days=14),
        )
        db.add(prop2)
        db.flush()

        # Files and CIs for Team 2
        f1 = FileModel(
            id=uuid.uuid4(),
            original_name="srs_devsecops_v1.0.md",
            stored_path="uploads/seed/srs_v1.md",
            mime="text/markdown",
            size_bytes=4200,
            sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            uploaded_by=student_users["23MIS0490"].id,
            created_at=now - timedelta(days=10),
        )
        f2 = FileModel(
            id=uuid.uuid4(),
            original_name="db_schema_v1.0.sql",
            stored_path="uploads/seed/db_schema_v1.sql",
            mime="text/plain",
            size_bytes=2150,
            sha256="ca978112ca1bbdcafac231b39a23dc4da786eff8147c4e72b9807785afee48bb",
            uploaded_by=student_users["23MIS0495"].id,
            created_at=now - timedelta(days=9),
        )
        db.add_all([f1, f2])
        db.flush()

        ci2_1 = ConfigurationItem(
            id=uuid.uuid4(),
            team_id=team2.id,
            ci_code="CI-001",
            name="Software Requirements Specification",
            ci_type="requirements",
            owner_user_id=student_users["23MIS0490"].id,
            status="approved",
            is_locked=True,
            created_at=now - timedelta(days=10),
            updated_at=now - timedelta(days=7),
        )
        ci2_2 = ConfigurationItem(
            id=uuid.uuid4(),
            team_id=team2.id,
            ci_code="CI-002",
            name="Database Schema & Data Dictionary",
            ci_type="database_design",
            owner_user_id=student_users["23MIS0495"].id,
            status="approved",
            is_locked=True,
            created_at=now - timedelta(days=9),
            updated_at=now - timedelta(days=7),
        )
        ci2_3 = ConfigurationItem(
            id=uuid.uuid4(),
            team_id=team2.id,
            ci_code="CI-003",
            name="Backend Microservice Core",
            ci_type="backend",
            owner_user_id=student_users["23MIS0500"].id,
            status="draft",
            is_locked=False,
            created_at=now - timedelta(days=5),
            updated_at=now - timedelta(days=5),
        )
        # Dependencies: CI-002 depends on CI-001, CI-003 depends on CI-002
        ci2_2.dependencies.append(ci2_1)
        ci2_3.dependencies.append(ci2_2)

        db.add_all([ci2_1, ci2_2, ci2_3])
        db.flush()

        v1_1 = CIVersion(
            id=uuid.uuid4(),
            ci_id=ci2_1.id,
            major=1,
            minor=0,
            version_label="1.0",
            file_id=f1.id,
            content_sha256=f1.sha256,
            change_description="Initial SRS draft baseline revision",
            kind="upload",
            status="approved",
            approved_by=faculty_user.id,
            approved_at=now - timedelta(days=7),
            created_by=student_users["23MIS0490"].id,
            created_at=now - timedelta(days=10),
        )
        v2_1 = CIVersion(
            id=uuid.uuid4(),
            ci_id=ci2_2.id,
            major=1,
            minor=0,
            version_label="1.0",
            file_id=f2.id,
            content_sha256=f2.sha256,
            change_description="Initial Relational schema DDL",
            kind="upload",
            status="approved",
            approved_by=faculty_user.id,
            approved_at=now - timedelta(days=7),
            created_by=student_users["23MIS0495"].id,
            created_at=now - timedelta(days=9),
        )
        db.add_all([v1_1, v2_1])
        db.flush()

        ci2_1.current_version_id = v1_1.id
        ci2_2.current_version_id = v2_1.id

        # Locked Baseline BL-001 for Team 2
        bl2 = Baseline(
            id=uuid.uuid4(),
            team_id=team2.id,
            code="BL-001",
            name="Functional Baseline (SRS & Schema)",
            description="Initial approved requirements and schema architecture baseline.",
            status="locked",
            created_by=faculty_user.id,
            locked_at=now - timedelta(days=7),
            created_at=now - timedelta(days=7),
        )
        db.add(bl2)
        db.flush()

        db.execute(baseline_items.insert().values([
            {"baseline_id": bl2.id, "ci_version_id": v1_1.id},
            {"baseline_id": bl2.id, "ci_version_id": v2_1.id},
        ]))

        # Approved Change Request CR-2026-001 for Team 2
        cr2 = ChangeRequest(
            id=uuid.uuid4(),
            team_id=team2.id,
            cr_code="CR-2026-001",
            title="Modify Authentication Schema for Multi-Tenant Support",
            description="Extend user and token models with tenant_id and organization roles to support multi-tenancy requirements.",
            reason="Enterprise security standard compliance mandate and organizational isolation requirements.",
            priority="high",
            status="approved",
            created_by=student_users["23MIS0490"].id,
            created_at=now - timedelta(days=4),
        )
        db.add(cr2)
        db.flush()

        db.add(ChangeRequestItem(cr_id=cr2.id, ci_id=ci2_1.id, note="Update SRS Auth Section 3.4"))
        db.add(ChangeRequestItem(cr_id=cr2.id, ci_id=ci2_2.id, note="Add tenant_id foreign keys"))
        db.add(ChangeRequestComponent(cr_id=cr2.id, component="backend"))
        db.add(ChangeRequestComponent(cr_id=cr2.id, component="database"))

        db.add_all([
            ChangeTransition(
                id=uuid.uuid4(),
                cr_id=cr2.id,
                from_status="none",
                to_status="draft",
                actor_id=student_users["23MIS0490"].id,
                comment="Draft created",
                at=now - timedelta(days=4),
            ),
            ChangeTransition(
                id=uuid.uuid4(),
                cr_id=cr2.id,
                from_status="draft",
                to_status="submitted",
                actor_id=student_users["23MIS0490"].id,
                comment="Submitted for faculty review",
                at=now - timedelta(days=3),
            ),
            ChangeTransition(
                id=uuid.uuid4(),
                cr_id=cr2.id,
                from_status="submitted",
                to_status="under_review",
                actor_id=faculty_user.id,
                comment="Reviewing architectural impact",
                at=now - timedelta(days=2),
            ),
            ChangeTransition(
                id=uuid.uuid4(),
                cr_id=cr2.id,
                from_status="under_review",
                to_status="approved",
                actor_id=faculty_user.id,
                comment="Approved. Proceed with branch cr-2026-001 and commit changes.",
                at=now - timedelta(days=1),
            ),
        ])

        print("--- Seeding Team 3 (Released stage with Evaluation) ---")
        team3 = Team(
            id=uuid.uuid4(),
            project_id=project.id,
            number=3,
            title="Smart Health Monitoring IoT Hub",
            status="released",
            formed_by="student",
            is_delayed=False,
            created_at=now - timedelta(days=22),
        )
        db.add(team3)
        db.flush()

        for idx, reg in enumerate(["23MIS0510", "23MIS0515", "23MIS0520", "23MIS0525"]):
            db.add(TeamMember(
                team_id=team3.id,
                project_id=project.id,
                student_user_id=student_users[reg].id,
                role="leader" if idx == 0 else "member",
                joined_at=now - timedelta(days=22),
            ))

        # Approved Proposal
        prop3 = Proposal(
            id=uuid.uuid4(),
            team_id=team3.id,
            revision_no=1,
            title="Low-Power IoT Gateway with Real-time Telemetry",
            abstract="An edge IoT gateway aggregating vital sign metrics and publishing encrypted packets via MQTT with fault-tolerant local caching.",
            problem_statement="Remote patient monitoring in rural clinics is disrupted by erratic internet connectivity and unvalidated device firmwares.",
            objectives="1. Edge gateway telemetry caching\n2. Firmware configuration verification\n3. End-to-end audit compliance",
            theme_id=t3.id,
            expected_outcome="Functional hardware gateway and cloud dashboard receiving streaming patient vitals.",
            status="approved",
            faculty_feedback="Excellent scope and feasibility. Approved.",
            submitted_by=student_users["23MIS0510"].id,
            reviewed_by=faculty_user.id,
            reviewed_at=now - timedelta(days=20),
            created_at=now - timedelta(days=21),
        )
        db.add(prop3)
        db.flush()

        # Files, CIs, and Versions for Team 3
        f3_1 = FileModel(
            id=uuid.uuid4(),
            original_name="iot_srs_v1.0.md",
            stored_path="uploads/seed/iot_srs.md",
            mime="text/markdown",
            size_bytes=5100,
            sha256="7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
            uploaded_by=student_users["23MIS0510"].id,
            created_at=now - timedelta(days=18),
        )
        f3_2 = FileModel(
            id=uuid.uuid4(),
            original_name="test_report_pass.pdf",
            stored_path="uploads/seed/test_report.pdf",
            mime="application/pdf",
            size_bytes=18400,
            sha256="4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a",
            uploaded_by=student_users["23MIS0515"].id,
            created_at=now - timedelta(days=3),
        )
        f3_3 = FileModel(
            id=uuid.uuid4(),
            original_name="user_manual_v1.0.pdf",
            stored_path="uploads/seed/manual.pdf",
            mime="application/pdf",
            size_bytes=24300,
            sha256="ef2d127de37b942baad06145e54b0c619a1f22327b2ebbcfbec78f5564afe39d",
            uploaded_by=student_users["23MIS0520"].id,
            created_at=now - timedelta(days=3),
        )
        db.add_all([f3_1, f3_2, f3_3])
        db.flush()

        ci3_1 = ConfigurationItem(
            id=uuid.uuid4(),
            team_id=team3.id,
            ci_code="CI-001",
            name="SRS Document",
            ci_type="requirements",
            owner_user_id=student_users["23MIS0510"].id,
            status="approved",
            is_locked=True,
            created_at=now - timedelta(days=18),
            updated_at=now - timedelta(days=15),
        )
        ci3_2 = ConfigurationItem(
            id=uuid.uuid4(),
            team_id=team3.id,
            ci_code="CI-002",
            name="Automated Test Suite Execution Report",
            ci_type="test_report",
            owner_user_id=student_users["23MIS0515"].id,
            status="approved",
            is_locked=True,
            created_at=now - timedelta(days=4),
            updated_at=now - timedelta(days=2),
        )
        ci3_3 = ConfigurationItem(
            id=uuid.uuid4(),
            team_id=team3.id,
            ci_code="CI-003",
            name="User Manual & Deployment Guide",
            ci_type="documentation",
            owner_user_id=student_users["23MIS0520"].id,
            status="approved",
            is_locked=True,
            created_at=now - timedelta(days=4),
            updated_at=now - timedelta(days=2),
        )
        db.add_all([ci3_1, ci3_2, ci3_3])
        db.flush()

        v3_1 = CIVersion(
            id=uuid.uuid4(),
            ci_id=ci3_1.id,
            major=1,
            minor=0,
            version_label="1.0",
            file_id=f3_1.id,
            content_sha256=f3_1.sha256,
            change_description="Approved SRS baseline version",
            kind="upload",
            status="approved",
            approved_by=faculty_user.id,
            approved_at=now - timedelta(days=15),
            created_by=student_users["23MIS0510"].id,
            created_at=now - timedelta(days=18),
        )
        v3_2 = CIVersion(
            id=uuid.uuid4(),
            ci_id=ci3_2.id,
            major=1,
            minor=0,
            version_label="1.0",
            file_id=f3_2.id,
            content_sha256=f3_2.sha256,
            change_description="All 48 unit and integration tests passed 100%",
            kind="upload",
            status="approved",
            approved_by=faculty_user.id,
            approved_at=now - timedelta(days=2),
            created_by=student_users["23MIS0515"].id,
            created_at=now - timedelta(days=3),
        )
        v3_3 = CIVersion(
            id=uuid.uuid4(),
            ci_id=ci3_3.id,
            major=1,
            minor=0,
            version_label="1.0",
            file_id=f3_3.id,
            content_sha256=f3_3.sha256,
            change_description="User manual and deployment instructions",
            kind="upload",
            status="approved",
            approved_by=faculty_user.id,
            approved_at=now - timedelta(days=2),
            created_by=student_users["23MIS0520"].id,
            created_at=now - timedelta(days=3),
        )
        db.add_all([v3_1, v3_2, v3_3])
        db.flush()

        ci3_1.current_version_id = v3_1.id
        ci3_2.current_version_id = v3_2.id
        ci3_3.current_version_id = v3_3.id

        # Locked Product Baseline
        bl3 = Baseline(
            id=uuid.uuid4(),
            team_id=team3.id,
            code="BL-001",
            name="Product Release Baseline v1.0",
            description="Locked release baseline containing all verified deliverables and test reports.",
            status="locked",
            created_by=faculty_user.id,
            locked_at=now - timedelta(days=2),
            created_at=now - timedelta(days=2),
        )
        db.add(bl3)
        db.flush()

        db.execute(baseline_items.insert().values([
            {"baseline_id": bl3.id, "ci_version_id": v3_1.id},
            {"baseline_id": bl3.id, "ci_version_id": v3_2.id},
            {"baseline_id": bl3.id, "ci_version_id": v3_3.id},
        ]))

        # Approved Release REL-1.0.0
        rel3 = Release(
            id=uuid.uuid4(),
            team_id=team3.id,
            baseline_id=bl3.id,
            code="REL-1.0.0",
            version="1.0.0",
            notes="Production release v1.0.0. Includes fault-tolerant edge gateway, AES encryption, and MQTT telemetry broker.",
            test_status="passed",
            doc_status="approved",
            status="approved",
            requested_by=student_users["23MIS0510"].id,
            approved_by=faculty_user.id,
            created_at=now - timedelta(days=2),
        )
        db.add(rel3)
        db.flush()

        # Evaluation Records for Team 3
        eval3 = Evaluation(
            id=uuid.uuid4(),
            team_id=team3.id,
            evaluated_by=faculty_user.id,
            stage="final",
            total_marks=94,
            grade="S",
            feedback="Exemplary software configuration management practices, zero audit gaps, and fully verified release bundle.",
            created_at=now - timedelta(days=1),
        )
        db.add(eval3)
        db.flush()

        db.add_all([
            EvaluationScore(id=uuid.uuid4(), evaluation_id=eval3.id, criterion_id=c1.id, marks=19),
            EvaluationScore(id=uuid.uuid4(), evaluation_id=eval3.id, criterion_id=c2.id, marks=24),
            EvaluationScore(id=uuid.uuid4(), evaluation_id=eval3.id, criterion_id=c3.id, marks=33),
            EvaluationScore(id=uuid.uuid4(), evaluation_id=eval3.id, criterion_id=c4.id, marks=18),
        ])

        # Notifications
        db.add(Notification(
            id=uuid.uuid4(),
            user_id=student_users["23MIS0510"].id,
            kind="release_approved",
            message="Congratulations! Your Release REL-1.0.0 has been approved with Grade S (94/100).",
            link=f"/teams/{team3.id}",
            is_read=False,
            created_at=now - timedelta(days=1),
        ))

        db.commit()
        print("Database seeded successfully!")
        print("\n--- Seed Credentials Summary ---")
        print("Faculty Account:")
        print("  Email:    meenakshi.k@univ.edu (or Faculty ID: FAC1042)")
        print("  Password: Password123!")
        print("\nStudent Accounts (Password: Password123!):")
        for name, reg, email in students_data:
            print(f"  {name:18} | Register No: {reg:10} | Email: {email}")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
