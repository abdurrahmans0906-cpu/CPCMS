"""0001 initial schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-10-08 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("failed_attempts", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_users_role", "users", ["role"])
    op.create_index("idx_users_email", "users", ["email"])

    # 2. students
    op.create_table(
        "students",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("register_number", sa.String(50), unique=True, nullable=False),
        sa.Column("department", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_students_reg_no", "students", ["register_number"])

    # 3. faculty
    op.create_table(
        "faculty",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("faculty_code", sa.String(50), unique=True, nullable=False),
        sa.Column("department", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_faculty_code", "faculty", ["faculty_code"])

    # 4. courses
    op.create_table(
        "courses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("department", sa.String(100), nullable=False),
        sa.Column("faculty_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("faculty_user_id", "code", name="uq_courses_faculty_code"),
    )
    op.create_index("idx_courses_faculty", "courses", ["faculty_user_id"])
    op.create_index("idx_courses_code", "courses", ["code"])

    # 5. refresh_tokens
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_refresh_tokens_user", "refresh_tokens", ["user_id"])
    op.create_index("idx_refresh_tokens_hash", "refresh_tokens", ["token_hash"])

    # 6. projects
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("faculty_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("semester", sa.String(50), nullable=False),
        sa.Column("academic_year", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("problem_statement", sa.Text(), nullable=True),
        sa.Column("objectives", sa.Text(), nullable=True),
        sa.Column("min_team_size", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("max_team_size", sa.Integer(), nullable=False, server_default=sa.text("4")),
        sa.Column("team_formation_mode", sa.String(20), nullable=False, server_default=sa.text("'student'")),
        sa.Column("team_formation_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("max_projects_per_student", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("allowed_file_exts", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("max_file_mb", sa.Integer(), nullable=False, server_default=sa.text("25")),
        sa.Column("late_policy", sa.String(20), nullable=False, server_default=sa.text("'allow_flagged'")),
        sa.Column("late_penalty_percent", sa.Numeric(5, 2), nullable=False, server_default=sa.text("0.0")),
        sa.Column("versioning_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("git_required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("baseline_frequency", sa.String(50), nullable=False, server_default=sa.text("'per_review'")),
        sa.Column("change_request_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("approval_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("branching_policy", sa.String(20), nullable=False, server_default=sa.text("'none'")),
        sa.Column("total_marks", sa.Integer(), nullable=False, server_default=sa.text("100")),
        sa.Column("grade_bands", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'active'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("min_team_size <= max_team_size", name="chk_team_size_min_max"),
        sa.CheckConstraint("team_formation_mode IN ('student', 'faculty', 'hybrid')", name="chk_project_formation_mode"),
        sa.CheckConstraint("late_policy IN ('reject', 'allow_flagged', 'allow_penalty')", name="chk_project_late_policy"),
        sa.CheckConstraint("branching_policy IN ('none', 'gitflow_lite')", name="chk_project_branching_policy"),
        sa.CheckConstraint("status IN ('active', 'archived')", name="chk_project_status"),
    )
    op.create_index("idx_projects_course", "projects", ["course_id"])
    op.create_index("idx_projects_faculty", "projects", ["faculty_user_id"])

    # 7. project_themes
    op.create_table(
        "project_themes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_project_themes_proj", "project_themes", ["project_id"])

    # 8. project_outcomes
    op.create_table(
        "project_outcomes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_project_outcomes_proj", "project_outcomes", ["project_id"])

    # 9. project_ci_templates
    op.create_table(
        "project_ci_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("ci_type", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_project_ci_templates_proj", "project_ci_templates", ["project_id"])

    # 10. project_deadlines
    op.create_table(
        "project_deadlines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("kind IN ('team_formation', 'proposal', 'srs', 'review', 'final', 'other')", name="chk_deadline_kind"),
    )
    op.create_index("idx_project_deadlines_proj", "project_deadlines", ["project_id"])

    # 11. evaluation_criteria
    op.create_table(
        "evaluation_criteria",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("max_marks", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_eval_criteria_proj", "evaluation_criteria", ["project_id"])

    # 12. reviews
    op.create_table(
        "reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("mode", sa.String(20), nullable=False, server_default=sa.text("'online'")),
        sa.Column("meeting_link", sa.Text(), nullable=True),
        sa.Column("venue", sa.String(200), nullable=True),
        sa.Column("agenda", sa.Text(), nullable=True),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("mode IN ('online', 'offline')", name="chk_review_mode"),
    )
    op.create_index("idx_reviews_proj", "reviews", ["project_id"])

    # 13. project_students
    op.create_table(
        "project_students",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("register_number", sa.String(50), nullable=False),
        sa.Column("student_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("project_id", "register_number", name="uq_project_student_reg"),
    )
    op.create_index("idx_project_students_proj", "project_students", ["project_id"])
    op.create_index("idx_project_students_reg", "project_students", ["register_number"])
    op.create_index("idx_project_students_user", "project_students", ["student_user_id"])

    # 14. teams
    op.create_table(
        "teams",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default=sa.text("'Created'")),
        sa.Column("formed_by", sa.String(20), nullable=False, server_default=sa.text("'student'")),
        sa.Column("is_delayed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("project_id", "number", name="uq_team_project_number"),
        sa.CheckConstraint("formed_by IN ('student', 'faculty')", name="chk_team_formed_by"),
    )
    op.create_index("idx_teams_project", "teams", ["project_id"])

    # 15. review_slots
    op.create_table(
        "review_slots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("review_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_review_slots_review", "review_slots", ["review_id"])
    op.create_index("idx_review_slots_team", "review_slots", ["team_id"])

    # 16. team_members
    op.create_table(
        "team_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default=sa.text("'member'")),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("project_id", "student_user_id", name="uq_project_student_one_team"),
        sa.CheckConstraint("role IN ('leader', 'member')", name="chk_member_role"),
    )
    op.create_index("idx_team_members_team", "team_members", ["team_id"])
    op.create_index("idx_team_members_user", "team_members", ["student_user_id"])

    # 17. team_invitations
    op.create_table(
        "team_invitations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("invited_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("invitee_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('pending', 'accepted', 'rejected', 'expired', 'cancelled')", name="chk_invitation_status"),
    )
    op.create_index("idx_team_invitations_team", "team_invitations", ["team_id"])
    op.create_index("idx_team_invitations_invitee", "team_invitations", ["invitee_user_id"])

    # 18. proposals
    op.create_table(
        "proposals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("revision_no", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("title", sa.String(250), nullable=False),
        sa.Column("abstract", sa.Text(), nullable=False),
        sa.Column("problem_statement", sa.Text(), nullable=False),
        sa.Column("objectives", sa.Text(), nullable=False),
        sa.Column("theme_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("project_themes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("expected_outcome", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default=sa.text("'submitted'")),
        sa.Column("faculty_feedback", sa.Text(), nullable=True),
        sa.Column("submitted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('submitted', 'approved', 'rejected', 'revision_required')", name="chk_proposal_status"),
    )
    op.create_index("idx_proposals_team", "proposals", ["team_id"])

    # 19. files
    op.create_table(
        "files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("original_name", sa.String(255), nullable=False),
        sa.Column("stored_path", sa.String(500), nullable=False),
        sa.Column("mime", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_files_sha256", "files", ["sha256"])
    op.create_index("idx_files_uploader", "files", ["uploaded_by"])

    # 20. configuration_items
    op.create_table(
        "configuration_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ci_code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("ci_type", sa.String(50), nullable=False),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("current_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("team_id", "ci_code", name="uq_team_ci_code"),
        sa.CheckConstraint("ci_type IN ('requirements', 'srs', 'architecture', 'database_design', 'backend', 'frontend', 'test_cases', 'test_report', 'documentation', 'other')", name="chk_ci_type"),
        sa.CheckConstraint("status IN ('draft', 'under_review', 'approved', 'rejected')", name="chk_ci_status"),
    )
    op.create_index("idx_ci_team", "configuration_items", ["team_id"])
    op.create_index("idx_ci_owner", "configuration_items", ["owner_user_id"])

    # 21. ci_dependencies
    op.create_table(
        "ci_dependencies",
        sa.Column("ci_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("configuration_items.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("depends_on_ci_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("configuration_items.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_index("idx_ci_dependencies_depends", "ci_dependencies", ["depends_on_ci_id"])

    # 22. ci_versions
    op.create_table(
        "ci_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ci_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("configuration_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("major", sa.Integer(), nullable=False),
        sa.Column("minor", sa.Integer(), nullable=False),
        sa.Column("version_label", sa.String(30), nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("files.id", ondelete="SET NULL"), nullable=True),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("change_description", sa.Text(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("commit_sha", sa.String(40), nullable=True),
        sa.Column("kind", sa.String(20), nullable=False, server_default=sa.text("'upload'")),
        sa.Column("rollback_of_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ci_versions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("change_request_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("ci_id", "major", "minor", name="uq_ci_major_minor"),
        sa.CheckConstraint("kind IN ('upload', 'rollback')", name="chk_version_kind"),
        sa.CheckConstraint("status IN ('draft', 'submitted', 'approved', 'rejected')", name="chk_version_status"),
    )
    op.create_index("idx_ci_versions_ci", "ci_versions", ["ci_id"])
    op.create_index("idx_ci_versions_sha", "ci_versions", ["content_sha256"])
    op.create_index("idx_ci_versions_creator", "ci_versions", ["created_by"])
    op.create_index("idx_ci_versions_approver", "ci_versions", ["approved_by"])

    # 23. baselines
    op.create_table(
        "baselines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'proposed'")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("team_id", "code", name="uq_team_baseline_code"),
        sa.CheckConstraint("status IN ('proposed', 'locked')", name="chk_baseline_status"),
    )
    op.create_index("idx_baselines_team", "baselines", ["team_id"])
    op.create_index("idx_baselines_creator", "baselines", ["created_by"])

    # 24. baseline_items
    op.create_table(
        "baseline_items",
        sa.Column("baseline_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("baselines.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("ci_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ci_versions.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_index("idx_baseline_items_version", "baseline_items", ["ci_version_id"])

    # 25. change_requests
    op.create_table(
        "change_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("cr_code", sa.String(50), nullable=False),
        sa.Column("title", sa.String(250), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False, server_default=sa.text("'medium'")),
        sa.Column("status", sa.String(30), nullable=False, server_default=sa.text("'draft'")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("implemented_commit_sha", sa.String(40), nullable=True),
        sa.Column("implemented_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ci_versions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("team_id", "cr_code", name="uq_team_cr_code"),
        sa.CheckConstraint("priority IN ('low', 'medium', 'high', 'critical')", name="chk_cr_priority"),
        sa.CheckConstraint("status IN ('draft', 'submitted', 'under_review', 'approved', 'rejected', 'implemented', 'verified', 'closed')", name="chk_cr_status"),
    )
    op.create_index("idx_change_requests_team", "change_requests", ["team_id"])
    op.create_index("idx_change_requests_creator", "change_requests", ["created_by"])

    # 26. change_request_items
    op.create_table(
        "change_request_items",
        sa.Column("cr_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("change_requests.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("ci_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("configuration_items.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("note", sa.Text(), nullable=True),
    )
    op.create_index("idx_cr_items_ci", "change_request_items", ["ci_id"])

    # 27. change_request_components
    op.create_table(
        "change_request_components",
        sa.Column("cr_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("change_requests.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("component", sa.String(50), primary_key=True),
        sa.CheckConstraint("component IN ('backend', 'database', 'frontend', 'test_cases', 'documentation', 'other')", name="chk_cr_component"),
    )

    # 28. change_transitions
    op.create_table(
        "change_transitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("cr_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("change_requests.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_status", sa.String(30), nullable=False),
        sa.Column("to_status", sa.String(30), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_change_transitions_cr", "change_transitions", ["cr_id"])
    op.create_index("idx_change_transitions_actor", "change_transitions", ["actor_id"])

    # 29. repositories
    op.create_table(
        "repositories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("url", sa.String(500), nullable=False),
        sa.Column("owner", sa.String(100), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("default_branch", sa.String(100), nullable=False, server_default=sa.text("'main'")),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sync_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_repositories_team", "repositories", ["team_id"])

    # 30. branches
    op.create_table(
        "branches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("repo_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("head_sha", sa.String(40), nullable=False),
        sa.Column("follows_policy", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_branches_repo", "branches", ["repo_id"])

    # 31. commits
    op.create_table(
        "commits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("repo_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sha", sa.String(40), nullable=False),
        sa.Column("branch", sa.String(150), nullable=False),
        sa.Column("author_name", sa.String(100), nullable=False),
        sa.Column("author_login", sa.String(100), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("committed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_commits_repo", "commits", ["repo_id"])
    op.create_index("idx_commits_sha", "commits", ["sha"])
    op.create_index("idx_commits_date", "commits", ["committed_at"])

    # 32. progress_reports
    op.create_table(
        "progress_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("review_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reviews.id", ondelete="SET NULL"), nullable=True),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("requirements_pct", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("design_pct", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("implementation_pct", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("testing_pct", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("documentation_pct", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("submitted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("faculty_comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("requirements_pct BETWEEN 0 AND 100", name="chk_prog_req"),
        sa.CheckConstraint("design_pct BETWEEN 0 AND 100", name="chk_prog_des"),
        sa.CheckConstraint("implementation_pct BETWEEN 0 AND 100", name="chk_prog_imp"),
        sa.CheckConstraint("testing_pct BETWEEN 0 AND 100", name="chk_prog_test"),
        sa.CheckConstraint("documentation_pct BETWEEN 0 AND 100", name="chk_prog_doc"),
    )
    op.create_index("idx_progress_reports_team", "progress_reports", ["team_id"])

    # 33. progress_screenshots
    op.create_table(
        "progress_screenshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("progress_report_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("progress_reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("files.id", ondelete="CASCADE"), nullable=False),
        sa.Column("caption", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_screenshots_report", "progress_screenshots", ["progress_report_id"])

    # 34. submissions
    op.create_table(
        "submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("version_label", sa.String(30), nullable=True),
        sa.Column("commit_sha", sa.String(40), nullable=True),
        sa.Column("repo_url", sa.String(500), nullable=True),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("files.id", ondelete="SET NULL"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("submitted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_late", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'submitted'")),
        sa.Column("faculty_feedback", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("kind IN ('github', 'zip', 'source', 'release_package')", name="chk_submission_kind"),
        sa.CheckConstraint("status IN ('submitted', 'accepted', 'rejected')", name="chk_submission_status"),
    )
    op.create_index("idx_submissions_team", "submissions", ["team_id"])
    op.create_index("idx_submissions_user", "submissions", ["submitted_by"])

    # 35. evaluations
    op.create_table(
        "evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("review_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("reviews.id", ondelete="SET NULL"), nullable=True),
        sa.Column("stage", sa.String(20), nullable=False),
        sa.Column("total_marks", sa.Numeric(6, 2), nullable=False),
        sa.Column("grade", sa.String(10), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("evaluated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("stage IN ('review', 'final')", name="chk_evaluation_stage"),
    )
    op.create_index("idx_evaluations_team", "evaluations", ["team_id"])
    op.create_index("idx_evaluations_evaluator", "evaluations", ["evaluated_by"])

    # 36. evaluation_scores
    op.create_table(
        "evaluation_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("evaluation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("criterion_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("evaluation_criteria.id", ondelete="CASCADE"), nullable=False),
        sa.Column("marks", sa.Numeric(6, 2), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_eval_scores_eval", "evaluation_scores", ["evaluation_id"])
    op.create_index("idx_eval_scores_crit", "evaluation_scores", ["criterion_id"])

    # 37. releases
    op.create_table(
        "releases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("version", sa.String(30), nullable=False),
        sa.Column("baseline_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("baselines.id", ondelete="CASCADE"), nullable=False),
        sa.Column("commit_sha", sa.String(40), nullable=True),
        sa.Column("test_status", sa.String(20), nullable=False, server_default=sa.text("'not_run'")),
        sa.Column("doc_status", sa.String(20), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("status", sa.String(20), nullable=False, server_default=sa.text("'requested'")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("test_status IN ('not_run', 'passed', 'failed')", name="chk_release_test_status"),
        sa.CheckConstraint("doc_status IN ('pending', 'approved')", name="chk_release_doc_status"),
        sa.CheckConstraint("status IN ('requested', 'approved', 'rejected')", name="chk_release_status"),
    )
    op.create_index("idx_releases_team", "releases", ["team_id"])
    op.create_index("idx_releases_baseline", "releases", ["baseline_id"])

    # 38. notifications
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("kind", sa.String(50), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("link", sa.Text(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_notifications_user", "notifications", ["user_id"])
    op.create_index("idx_notifications_read", "notifications", ["is_read"])

    # 39. audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_role", sa.String(50), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.String(100), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("before", postgresql.JSONB(), nullable=True),
        sa.Column("after", postgresql.JSONB(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_audit_logs_at", "audit_logs", ["at"])
    op.create_index("idx_audit_logs_actor", "audit_logs", ["actor_user_id"])
    op.create_index("idx_audit_logs_action", "audit_logs", ["action"])
    op.create_index("idx_audit_logs_entity", "audit_logs", ["entity_type", "entity_id"])
    op.create_index("idx_audit_logs_proj", "audit_logs", ["project_id"])
    op.create_index("idx_audit_logs_team", "audit_logs", ["team_id"])

    # --- TRIGGERS ---
    # Trigger 1: Immutable ci_versions (cannot delete; only update status, approved_by, approved_at)
    op.execute("""
    CREATE OR REPLACE FUNCTION trg_immutable_ci_versions()
    RETURNS TRIGGER AS $$
    BEGIN
        IF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION 'Deleting CI versions is strictly prohibited (immutable).';
        ELSIF TG_OP = 'UPDATE' THEN
            IF NEW.id <> OLD.id OR
               NEW.ci_id <> OLD.ci_id OR
               NEW.major <> OLD.major OR
               NEW.minor <> OLD.minor OR
               NEW.version_label <> OLD.version_label OR
               NEW.file_id IS DISTINCT FROM OLD.file_id OR
               NEW.content_sha256 <> OLD.content_sha256 OR
               NEW.change_description <> OLD.change_description OR
               NEW.created_by <> OLD.created_by OR
               NEW.commit_sha IS DISTINCT FROM OLD.commit_sha OR
               NEW.kind <> OLD.kind OR
               NEW.rollback_of_version_id IS DISTINCT FROM OLD.rollback_of_version_id OR
               NEW.change_request_id IS DISTINCT FROM OLD.change_request_id OR
               NEW.created_at <> OLD.created_at THEN
                RAISE EXCEPTION 'Updating immutable fields of CI version is not allowed.';
            END IF;
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    DROP TRIGGER IF EXISTS trg_block_ci_versions_mutation ON ci_versions;
    CREATE TRIGGER trg_block_ci_versions_mutation
    BEFORE UPDATE OR DELETE ON ci_versions
    FOR EACH ROW EXECUTE FUNCTION trg_immutable_ci_versions();
    """)

    # Trigger 2: Append-only audit_logs (raises exception on UPDATE and DELETE)
    op.execute("""
    CREATE OR REPLACE FUNCTION trg_immutable_audit_logs()
    RETURNS TRIGGER AS $$
    BEGIN
        RAISE EXCEPTION 'audit_logs is append-only. UPDATE and DELETE operations are forbidden.';
    END;
    $$ LANGUAGE plpgsql;

    DROP TRIGGER IF EXISTS trg_block_audit_logs_mutation ON audit_logs;
    CREATE TRIGGER trg_block_audit_logs_mutation
    BEFORE UPDATE OR DELETE ON audit_logs
    FOR EACH ROW EXECUTE FUNCTION trg_immutable_audit_logs();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_block_audit_logs_mutation ON audit_logs;")
    op.execute("DROP FUNCTION IF EXISTS trg_immutable_audit_logs();")
    op.execute("DROP TRIGGER IF EXISTS trg_block_ci_versions_mutation ON ci_versions;")
    op.execute("DROP FUNCTION IF EXISTS trg_immutable_ci_versions();")

    op.drop_table("audit_logs")
    op.drop_table("notifications")
    op.drop_table("releases")
    op.drop_table("evaluation_scores")
    op.drop_table("evaluations")
    op.drop_table("submissions")
    op.drop_table("progress_screenshots")
    op.drop_table("progress_reports")
    op.drop_table("commits")
    op.drop_table("branches")
    op.drop_table("repositories")
    op.drop_table("change_transitions")
    op.drop_table("change_request_components")
    op.drop_table("change_request_items")
    op.drop_table("change_requests")
    op.drop_table("baseline_items")
    op.drop_table("baselines")
    op.drop_table("ci_versions")
    op.drop_table("ci_dependencies")
    op.drop_table("configuration_items")
    op.drop_table("files")
    op.drop_table("proposals")
    op.drop_table("team_invitations")
    op.drop_table("team_members")
    op.drop_table("review_slots")
    op.drop_table("teams")
    op.drop_table("project_students")
    op.drop_table("reviews")
    op.drop_table("evaluation_criteria")
    op.drop_table("project_deadlines")
    op.drop_table("project_ci_templates")
    op.drop_table("project_outcomes")
    op.drop_table("project_themes")
    op.drop_table("projects")
    op.drop_table("refresh_tokens")
    op.drop_table("courses")
    op.drop_table("faculty")
    op.drop_table("students")
    op.drop_table("users")
