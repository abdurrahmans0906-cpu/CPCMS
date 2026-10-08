from typing import Dict, List, Set, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.team import Team
from app.models.project import ProjectDeadline
from app.models.progress import Submission


# Standard sequential flow
LIFECYCLE_STAGES: List[str] = [
    "Created",
    "Team Formation",
    "Proposal Submitted",
    "Under Review",
    "Approved",
    "Development",
    "Review 1",
    "Review 2",
    "Testing",
    "Final Submission",
    "Final Review",
    "Released",
    "Completed"
]

SIDE_STATES: Set[str] = {
    "Rejected",
    "Revision Required",
    "On Hold",
    "Cancelled"
}

# Allowed transitions map: from_status -> set of allowed target statuses
ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
    "Created": {"Team Formation", "Cancelled"},
    "Team Formation": {"Proposal Submitted", "Cancelled"},
    "Proposal Submitted": {"Under Review", "Cancelled"},
    "Under Review": {"Approved", "Rejected", "Revision Required", "Cancelled"},
    "Revision Required": {"Proposal Submitted", "Cancelled"},
    "Rejected": {"Cancelled"},  # Terminal unless overridden
    "Approved": {"Development", "On Hold", "Cancelled"},
    "Development": {"Review 1", "Testing", "On Hold", "Cancelled"},
    "Review 1": {"Development", "Review 2", "Testing", "On Hold", "Cancelled"},
    "Review 2": {"Development", "Testing", "Final Submission", "On Hold", "Cancelled"},
    "Testing": {"Final Submission", "Final Review", "Development", "On Hold", "Cancelled"},
    "Final Submission": {"Final Review", "On Hold", "Cancelled"},
    "Final Review": {"Released", "Testing", "On Hold", "Cancelled"},
    "Released": {"Completed", "On Hold", "Cancelled"},
    "Completed": set(),
    "On Hold": {"Development", "Review 1", "Review 2", "Testing", "Final Submission", "Final Review", "Released", "Cancelled"},
    "Cancelled": set(),
}

# Faculty can manually transition between development and review stages
FACULTY_ALLOWED_TRANSITIONS: Set[str] = {
    "Development", "Review 1", "Review 2", "Testing", "Final Submission", "Final Review", "Completed", "On Hold", "Cancelled"
}


def can_transition(current_status: str, target_status: str) -> bool:
    allowed = ALLOWED_TRANSITIONS.get(current_status, set())
    return target_status in allowed


def check_and_update_delayed_flag(db: Session, team: Team) -> bool:
    """
    Computes is_delayed flag:
    A team is delayed if an active project deadline has passed without a matching submission/proposal.
    """
    now = datetime.now(timezone.utc)
    # Check deadlines for the team's project
    deadlines = db.query(ProjectDeadline).filter(
        ProjectDeadline.project_id == team.project_id,
        ProjectDeadline.due_at < now
    ).all()

    delayed = False
    for dl in deadlines:
        if dl.kind == "proposal":
            has_approved_or_submitted = any(
                p.status in ["submitted", "approved", "under_review"] for p in team.proposals
            )
            if not has_approved_or_submitted:
                delayed = True
                break
        elif dl.kind in ["srs", "review", "final"]:
            has_submission = any(
                s.created_at <= dl.due_at for s in team.submissions
            )
            if not has_submission and team.status in ["Development", "Review 1", "Review 2", "Testing"]:
                delayed = True
                break

    if team.is_delayed != delayed:
        team.is_delayed = delayed
        db.flush()

    return delayed
