import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import get_db
from app.models.user import User, Student
from app.models.project import Project, ProjectStudent
from app.models.team import Team, TeamMember, TeamInvitation
from app.schemas.team import (
    TeamCreate, TeamFacultyCreate, TeamUpdate, TeamOut,
    TeamMemberOut, TeamMemberAdd, TeamInvitationCreate,
    TeamInvitationOut, StatusTransitionRequest
)
from app.permissions import (
    get_current_user, require_faculty, require_student,
    get_project_with_access, get_team_with_access, is_team_leader_or_faculty
)
from app.services.audit import record_audit
from app.services.notifications import create_notification
from app.services.lifecycle import can_transition, check_and_update_delayed_flag, FACULTY_ALLOWED_TRANSITIONS

router = APIRouter(tags=["Teams"])


def _populate_team_out(team: Team, db: Session) -> TeamOut:
    check_and_update_delayed_flag(db, team)

    members_out = []
    for m in team.members:
        u = m.student_user
        s = u.student_profile if u else None
        members_out.append(TeamMemberOut(
            id=m.id,
            team_id=m.team_id,
            student_user_id=m.student_user_id,
            student_name=u.name if u else "Unknown",
            student_register_number=s.register_number if s else "",
            student_email=u.email if u else "",
            department=s.department if s else None,
            role=m.role,
            joined_at=m.joined_at
        ))

    # Calculate overall progress if progress reports exist
    avg_prog = 0.0
    if team.progress_reports:
        latest_pr = team.progress_reports[-1]
        avg_prog = (
            latest_pr.requirements_pct +
            latest_pr.design_pct +
            latest_pr.implementation_pct +
            latest_pr.testing_pct +
            latest_pr.documentation_pct
        ) / 5.0

    return TeamOut(
        id=team.id,
        project_id=team.project_id,
        project_name=team.project.name if team.project else None,
        number=team.number,
        title=team.title,
        status=team.status,
        formed_by=team.formed_by,
        is_delayed=team.is_delayed,
        created_at=team.created_at,
        members=members_out,
        member_count=len(members_out),
        overall_progress=avg_prog
    )


@router.get("/projects/{project_id}/teams", response_model=List[TeamOut])
def list_teams_in_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = get_project_with_access(project_id, current_user, db)
    teams = db.query(Team).filter(Team.project_id == project.id).order_by(Team.number).all()
    return [_populate_team_out(t, db) for t in teams]


@router.post("/projects/{project_id}/teams", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
def create_team(
    project_id: uuid.UUID,
    payload: TeamCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = get_project_with_access(project_id, current_user, db)
    now = datetime.now(timezone.utc)

    # Formation mode checks
    if current_user.role == "STUDENT":
        if project.team_formation_mode == "faculty":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Student team creation is disabled for this project (Faculty formation mode)."
            )
        if project.team_formation_mode == "hybrid":
            if project.team_formation_deadline and now > project.team_formation_deadline:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="The team formation deadline has passed. Only faculty can create or assign teams now."
                )

        # Check if student is already in a team for this project
        existing_mem = db.query(TeamMember).filter(
            TeamMember.project_id == project.id,
            TeamMember.student_user_id == current_user.id
        ).first()
        if existing_mem:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You are already a member of a team in this project."
            )

    # Next team number
    next_number = (db.query(func.coalesce(func.max(Team.number), 0)).filter(Team.project_id == project.id).scalar() or 0) + 1

    team = Team(
        project_id=project.id,
        number=next_number,
        title=payload.title.strip(),
        status="Team Formation",
        formed_by="student" if current_user.role == "STUDENT" else "faculty"
    )
    db.add(team)
    db.flush()

    # If student created it, add as leader
    if current_user.role == "STUDENT":
        member = TeamMember(
            team_id=team.id,
            project_id=project.id,
            student_user_id=current_user.id,
            role="leader"
        )
        db.add(member)

    record_audit(
        db=db,
        action="TEAM_CREATE",
        entity_type="team",
        entity_id=team.id,
        actor=current_user,
        project_id=project.id,
        team_id=team.id,
        note=f"Created Team {team.number}: {team.title}"
    )
    db.commit()
    db.refresh(team)
    return _populate_team_out(team, db)


@router.get("/teams/{id}", response_model=TeamOut)
def get_team(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = get_team_with_access(id, current_user, db)
    return _populate_team_out(team, db)


@router.patch("/teams/{id}", response_model=TeamOut)
def update_team(
    id: uuid.UUID,
    payload: TeamUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = get_team_with_access(id, current_user, db)
    if not is_team_leader_or_faculty(team, current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only team leader or faculty can edit team details.")

    if payload.title is not None:
        team.title = payload.title.strip()
    if payload.is_delayed is not None and current_user.role == "FACULTY":
        team.is_delayed = payload.is_delayed

    record_audit(
        db=db,
        action="TEAM_UPDATE",
        entity_type="team",
        entity_id=team.id,
        actor=current_user,
        project_id=team.project_id,
        team_id=team.id,
        note="Updated team details"
    )
    db.commit()
    db.refresh(team)
    return _populate_team_out(team, db)


# --- Invitations ---

@router.post("/teams/{id}/invitations", response_model=TeamInvitationOut, status_code=status.HTTP_201_CREATED)
def invite_student_to_team(
    id: uuid.UUID,
    payload: TeamInvitationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = get_team_with_access(id, current_user, db)
    project = team.project
    now = datetime.now(timezone.utc)

    # Hybrid check: cannot invite if deadline passed
    if project.team_formation_mode == "hybrid" and project.team_formation_deadline and now > project.team_formation_deadline:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The team formation deadline has passed. Invitations are disabled."
        )

    # Check team capacity
    if len(team.members) >= project.max_team_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Team is already at maximum capacity ({project.max_team_size} members)."
        )

    # Target student must be enrolled in this project
    reg_clean = payload.invitee_register_number.strip().upper()
    enrolled = db.query(ProjectStudent).filter(
        ProjectStudent.project_id == project.id,
        ProjectStudent.register_number == reg_clean
    ).first()
    if not enrolled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student '{reg_clean}' is not enrolled in this project."
        )

    # Must be registered
    student_record = db.query(Student).filter(Student.register_number == reg_clean).first()
    if not student_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Student '{reg_clean}' has not registered an account yet."
        )

    target_user_id = student_record.user_id

    # Check if target already in a team in this project
    if db.query(TeamMember).filter(TeamMember.project_id == project.id, TeamMember.student_user_id == target_user_id).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Student '{reg_clean}' already belongs to a team in this project."
        )

    # Check existing pending invitation
    existing_inv = db.query(TeamInvitation).filter(
        TeamInvitation.team_id == team.id,
        TeamInvitation.invitee_user_id == target_user_id,
        TeamInvitation.status == "pending"
    ).first()
    if existing_inv:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A pending invitation has already been sent to this student."
        )

    inv = TeamInvitation(
        team_id=team.id,
        invited_by=current_user.id,
        invitee_user_id=target_user_id,
        status="pending"
    )
    db.add(inv)
    db.flush()

    # Notify student
    create_notification(
        db=db,
        user_id=target_user_id,
        kind="team_invitation",
        message=f"You received an invitation to join Team {team.number} ({team.title}) for {project.name}.",
        link=f"/projects/{project.id}"
    )

    record_audit(
        db=db,
        action="TEAM_INVITATION_SENT",
        entity_type="team_invitation",
        entity_id=inv.id,
        actor=current_user,
        project_id=project.id,
        team_id=team.id,
        note=f"Invited {reg_clean} to Team {team.number}"
    )
    db.commit()
    db.refresh(inv)

    return TeamInvitationOut(
        id=inv.id,
        team_id=inv.team_id,
        team_number=team.number,
        team_title=team.title,
        project_id=project.id,
        project_name=project.name,
        invited_by=inv.invited_by,
        invited_by_name=current_user.name,
        invitee_user_id=inv.invitee_user_id,
        invitee_name=student_record.user.name,
        invitee_register_number=reg_clean,
        status=inv.status,
        responded_at=inv.responded_at,
        created_at=inv.created_at
    )


@router.get("/invitations", response_model=List[TeamInvitationOut])
def list_my_invitations(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    invitations = db.query(TeamInvitation).filter(
        TeamInvitation.invitee_user_id == current_user.id,
        TeamInvitation.status == "pending"
    ).order_by(TeamInvitation.created_at.desc()).all()

    results = []
    for inv in invitations:
        team = inv.team
        results.append(TeamInvitationOut(
            id=inv.id,
            team_id=inv.team_id,
            team_number=team.number if team else None,
            team_title=team.title if team else None,
            project_id=team.project_id if team else None,
            project_name=team.project.name if team and team.project else None,
            invited_by=inv.invited_by,
            invited_by_name=inv.inviter.name if inv.inviter else "Unknown",
            invitee_user_id=inv.invitee_user_id,
            invitee_name=current_user.name,
            invitee_register_number=current_user.student_profile.register_number if current_user.student_profile else "",
            status=inv.status,
            responded_at=inv.responded_at,
            created_at=inv.created_at
        ))
    return results


@router.post("/invitations/{id}/accept", response_model=Dict[str, Any])
def accept_invitation(
    id: uuid.UUID,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    inv = db.query(TeamInvitation).filter(TeamInvitation.id == id).first()
    if not inv or inv.invitee_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found.")

    if inv.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invitation already {inv.status}.")

    team = inv.team
    project = team.project
    now = datetime.now(timezone.utc)

    # Check formation deadline
    if project.team_formation_deadline and now > project.team_formation_deadline:
        inv.status = "expired"
        inv.responded_at = now
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation expired as formation deadline has passed.")

    # Check team capacity
    if len(team.members) >= project.max_team_size:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Team is already full.")

    # Check student not in another team
    if db.query(TeamMember).filter(TeamMember.project_id == project.id, TeamMember.student_user_id == current_user.id).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You already joined another team in this project.")

    inv.status = "accepted"
    inv.responded_at = now

    member = TeamMember(
        team_id=team.id,
        project_id=project.id,
        student_user_id=current_user.id,
        role="member"
    )
    db.add(member)

    # Cancel other pending invitations for this user in this project
    other_invs = (
        db.query(TeamInvitation)
        .join(Team, TeamInvitation.team_id == Team.id)
        .filter(
            Team.project_id == project.id,
            TeamInvitation.invitee_user_id == current_user.id,
            TeamInvitation.status == "pending"
        )
        .all()
    )
    for oi in other_invs:
        oi.status = "cancelled"

    record_audit(
        db=db,
        action="TEAM_INVITATION_ACCEPTED",
        entity_type="team",
        entity_id=team.id,
        actor=current_user,
        project_id=project.id,
        team_id=team.id,
        note=f"{current_user.name} accepted invitation to Team {team.number}"
    )
    db.commit()
    return {"message": f"Successfully joined Team {team.number}.", "team_id": team.id}


@router.post("/invitations/{id}/reject", response_model=Dict[str, Any])
def reject_invitation(
    id: uuid.UUID,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    inv = db.query(TeamInvitation).filter(TeamInvitation.id == id).first()
    if not inv or inv.invitee_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found.")

    if inv.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invitation already {inv.status}.")

    inv.status = "rejected"
    inv.responded_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Invitation rejected."}


# --- Status Transitions ---

@router.post("/teams/{id}/status", response_model=TeamOut)
def update_team_status(
    id: uuid.UUID,
    payload: StatusTransitionRequest,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    team = get_team_with_access(id, current_user, db)
    target = payload.target_status.strip()

    if target not in FACULTY_ALLOWED_TRANSITIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Faculty cannot transition to status '{target}' manually."
        )

    if not can_transition(team.status, target):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transition from '{team.status}' to '{target}' is not allowed."
        )

    before_status = team.status
    team.status = target

    record_audit(
        db=db,
        action="TEAM_STATUS_TRANSITION",
        entity_type="team",
        entity_id=team.id,
        actor=current_user,
        project_id=team.project_id,
        team_id=team.id,
        before={"status": before_status},
        after={"status": target},
        note=payload.comment or f"Moved team status to {target}"
    )
    db.commit()
    db.refresh(team)
    return _populate_team_out(team, db)
