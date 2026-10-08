import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import get_db
from app.models.user import User
from app.models.team import Team, TeamMember
from app.models.project import Project, ProjectCITemplate
from app.models.proposal import Proposal
from app.models.scm import ConfigurationItem
from app.schemas.proposal import ProposalCreate, ProposalDecisionRequest, ProposalOut
from app.permissions import (
    get_current_user, require_faculty, get_team_with_access, is_team_leader_or_faculty
)
from app.services.audit import record_audit
from app.services.notifications import create_notification

router = APIRouter(tags=["Proposals"])


def _populate_proposal_out(p: Proposal) -> ProposalOut:
    return ProposalOut(
        id=p.id,
        team_id=p.team_id,
        revision_no=p.revision_no,
        title=p.title,
        abstract=p.abstract,
        problem_statement=p.problem_statement,
        objectives=p.objectives,
        theme_id=p.theme_id,
        theme_name=p.theme.name if p.theme else None,
        expected_outcome=p.expected_outcome,
        status=p.status,
        faculty_feedback=p.faculty_feedback,
        submitted_by=p.submitted_by,
        submitted_by_name=p.submitter.name if p.submitter else None,
        reviewed_by=p.reviewed_by,
        reviewed_by_name=p.reviewer.name if p.reviewer else None,
        reviewed_at=p.reviewed_at,
        created_at=p.created_at
    )


@router.get("/teams/{team_id}/proposals", response_model=List[ProposalOut])
def list_proposals(
    team_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = get_team_with_access(team_id, current_user, db)
    proposals = db.query(Proposal).filter(Proposal.team_id == team.id).order_by(Proposal.revision_no.desc()).all()
    return [_populate_proposal_out(p) for p in proposals]


@router.post("/teams/{team_id}/proposals", response_model=ProposalOut, status_code=status.HTTP_201_CREATED)
def submit_proposal(
    team_id: uuid.UUID,
    payload: ProposalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = get_team_with_access(team_id, current_user, db)
    project = team.project

    # Rule 10: Size check
    member_count = len(team.members)
    if member_count < project.min_team_size or member_count > project.max_team_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Team size ({member_count}) must be between {project.min_team_size} and {project.max_team_size} to submit a proposal."
        )

    # Rule 13: One open proposal per team
    latest_prop = db.query(Proposal).filter(Proposal.team_id == team.id).order_by(Proposal.revision_no.desc()).first()
    if latest_prop and latest_prop.status in ["submitted", "approved"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit proposal: latest revision is already '{latest_prop.status}'."
        )

    next_rev = (latest_prop.revision_no + 1) if latest_prop else 1

    proposal = Proposal(
        team_id=team.id,
        revision_no=next_rev,
        title=payload.title.strip(),
        abstract=payload.abstract.strip(),
        problem_statement=payload.problem_statement.strip(),
        objectives=payload.objectives.strip(),
        theme_id=payload.theme_id,
        expected_outcome=payload.expected_outcome.strip(),
        status="submitted",
        submitted_by=current_user.id
    )
    db.add(proposal)
    db.flush()

    # Automatic lifecycle transition
    team.status = "Proposal Submitted"

    # Notify faculty
    create_notification(
        db=db,
        user_id=project.faculty_user_id,
        kind="proposal_submitted",
        message=f"Team {team.number} submitted proposal revision {proposal.revision_no}: '{proposal.title}'.",
        link=f"/projects/{project.id}"
    )

    record_audit(
        db=db,
        action="PROPOSAL_SUBMITTED",
        entity_type="proposal",
        entity_id=proposal.id,
        actor=current_user,
        project_id=project.id,
        team_id=team.id,
        note=f"Submitted proposal rev {next_rev}: {proposal.title}"
    )
    db.commit()
    db.refresh(proposal)
    return _populate_proposal_out(proposal)


@router.post("/proposals/{id}/decision", response_model=ProposalOut)
def decide_proposal(
    id: uuid.UUID,
    payload: ProposalDecisionRequest,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    proposal = db.query(Proposal).filter(Proposal.id == id).first()
    if not proposal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")

    team = proposal.team
    project = team.project
    if project.faculty_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")

    now = datetime.now(timezone.utc)
    proposal.status = payload.decision
    proposal.faculty_feedback = payload.feedback
    proposal.reviewed_by = current_user.id
    proposal.reviewed_at = now

    # Lifecycle transition
    if payload.decision == "approved":
        team.status = "Approved"

        # Rule 13: Seed configuration items from the project CI template
        # Check if CIs are already seeded
        existing_ci_count = db.query(func.count(ConfigurationItem.id)).filter(ConfigurationItem.team_id == team.id).scalar() or 0
        if existing_ci_count == 0 and project.ci_templates:
            for idx, tmpl in enumerate(project.ci_templates, start=1):
                ci_code = f"CI-{idx:03d}"
                ci = ConfigurationItem(
                    team_id=team.id,
                    ci_code=ci_code,
                    name=tmpl.name,
                    ci_type=tmpl.ci_type,
                    status="draft",
                    is_locked=False,
                    updated_at=now
                )
                db.add(ci)

    elif payload.decision == "rejected":
        team.status = "Rejected"
    elif payload.decision == "revision_required":
        team.status = "Revision Required"

    # Notify team members
    for m in team.members:
        create_notification(
            db=db,
            user_id=m.student_user_id,
            kind="proposal_decision",
            message=f"Faculty decided {payload.decision.replace('_', ' ').upper()} on your proposal rev {proposal.revision_no}.",
            link=f"/projects/{project.id}"
        )

    record_audit(
        db=db,
        action=f"PROPOSAL_{payload.decision.upper()}",
        entity_type="proposal",
        entity_id=proposal.id,
        actor=current_user,
        project_id=project.id,
        team_id=team.id,
        note=f"Proposal decision: {payload.decision}. Feedback: {payload.feedback or 'None'}"
    )
    db.commit()
    db.refresh(proposal)
    return _populate_proposal_out(proposal)
