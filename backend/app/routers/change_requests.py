import uuid
from datetime import datetime, timezone
from typing import List, Set, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import get_db
from app.models.user import User
from app.models.scm import ConfigurationItem, CIVersion
from app.models.baseline import Baseline, baseline_items
from app.models.change_request import (
    ChangeRequest, ChangeRequestItem, ChangeRequestComponent, ChangeTransition
)
from app.schemas.change_request import (
    ChangeRequestCreate, ChangeRequestUpdate, ChangeRequestOut,
    CRTransitionRequest, CRImpactOut, CRItemOut, ChangeTransitionOut
)
from app.permissions import (
    get_current_user, require_faculty, get_team_with_access, is_team_leader_or_faculty
)
from app.services.audit import record_audit
from app.services.notifications import create_notification

router = APIRouter(tags=["Change Requests"])


def _populate_cr_out(cr: ChangeRequest) -> ChangeRequestOut:
    items_out = []
    for it in cr.items:
        ci = it.ci
        items_out.append(CRItemOut(
            ci_id=it.ci_id,
            ci_code=ci.ci_code if ci else "Unknown",
            ci_name=ci.name if ci else "Unknown",
            ci_type=ci.ci_type if ci else "Unknown",
            is_locked=ci.is_locked if ci else False,
            note=it.note
        ))

    comps_out = [c.component for c in cr.components]

    trans_out = []
    for t in cr.transitions:
        trans_out.append(ChangeTransitionOut(
            id=t.id,
            cr_id=t.cr_id,
            from_status=t.from_status,
            to_status=t.to_status,
            actor_id=t.actor_id,
            actor_name=t.actor.name if t.actor else "System",
            comment=t.comment,
            at=t.at
        ))

    return ChangeRequestOut(
        id=cr.id,
        team_id=cr.team_id,
        cr_code=cr.cr_code,
        title=cr.title,
        description=cr.description,
        reason=cr.reason,
        priority=cr.priority,
        status=cr.status,
        created_by=cr.created_by,
        created_by_name=cr.creator.name if cr.creator else None,
        implemented_commit_sha=cr.implemented_commit_sha,
        implemented_version_id=cr.implemented_version_id,
        components=comps_out,
        items=items_out,
        transitions=trans_out,
        created_at=cr.created_at
    )


@router.get("/teams/{team_id}/change-requests", response_model=List[ChangeRequestOut])
def list_change_requests(
    team_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = get_team_with_access(team_id, current_user, db)
    crs = db.query(ChangeRequest).filter(ChangeRequest.team_id == team.id).order_by(ChangeRequest.created_at.desc()).all()
    return [_populate_cr_out(cr) for cr in crs]


@router.post("/teams/{team_id}/change-requests", response_model=ChangeRequestOut, status_code=status.HTTP_201_CREATED)
def create_change_request(
    team_id: uuid.UUID,
    payload: ChangeRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = get_team_with_access(team_id, current_user, db)
    now = datetime.now(timezone.utc)
    current_year = now.year

    # Sequence per year per team: CR-2026-001
    prefix = f"CR-{current_year}-"
    last_cr = db.query(ChangeRequest).filter(
        ChangeRequest.team_id == team.id,
        ChangeRequest.cr_code.like(f"{prefix}%")
    ).order_by(ChangeRequest.cr_code.desc()).first()

    next_seq = 1
    if last_cr:
        try:
            next_seq = int(last_cr.cr_code.split("-")[-1]) + 1
        except ValueError:
            next_seq = 1

    cr_code = f"{prefix}{next_seq:03d}"

    cr = ChangeRequest(
        team_id=team.id,
        cr_code=cr_code,
        title=payload.title.strip(),
        description=payload.description.strip(),
        reason=payload.reason.strip(),
        priority=payload.priority,
        status="draft",
        created_by=current_user.id
    )
    db.add(cr)
    db.flush()

    # Affected CIs
    for ci_id in set(payload.affected_ci_ids):
        db.add(ChangeRequestItem(cr_id=cr.id, ci_id=ci_id))

    # Affected components
    for comp in set(payload.components):
        db.add(ChangeRequestComponent(cr_id=cr.id, component=comp))

    # Initial transition: to draft
    db.add(ChangeTransition(
        cr_id=cr.id,
        from_status="none",
        to_status="draft",
        actor_id=current_user.id,
        comment="Created initial change request draft",
        at=now
    ))

    record_audit(
        db=db,
        action="CR_CREATE",
        entity_type="change_request",
        entity_id=cr.id,
        actor=current_user,
        project_id=team.project_id,
        team_id=team.id,
        note=f"Created {cr.cr_code}: {cr.title} ({cr.priority})"
    )
    db.commit()
    db.refresh(cr)
    return _populate_cr_out(cr)


@router.get("/change-requests/{id}", response_model=ChangeRequestOut)
def get_change_request(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cr = db.query(ChangeRequest).filter(ChangeRequest.id == id).first()
    if not cr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change Request not found")
    get_team_with_access(cr.team_id, current_user, db)
    return _populate_cr_out(cr)


@router.patch("/change-requests/{id}", response_model=ChangeRequestOut)
def update_change_request(
    id: uuid.UUID,
    payload: ChangeRequestUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cr = db.query(ChangeRequest).filter(ChangeRequest.id == id).first()
    if not cr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change Request not found")
    get_team_with_access(cr.team_id, current_user, db)

    if cr.status not in ["draft", "submitted"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot edit Change Request while in status '{cr.status}'."
        )

    if payload.title is not None:
        cr.title = payload.title.strip()
    if payload.description is not None:
        cr.description = payload.description.strip()
    if payload.reason is not None:
        cr.reason = payload.reason.strip()
    if payload.priority is not None:
        cr.priority = payload.priority

    if payload.affected_ci_ids is not None:
        db.query(ChangeRequestItem).filter(ChangeRequestItem.cr_id == cr.id).delete()
        for ci_id in set(payload.affected_ci_ids):
            db.add(ChangeRequestItem(cr_id=cr.id, ci_id=ci_id))

    if payload.components is not None:
        db.query(ChangeRequestComponent).filter(ChangeRequestComponent.cr_id == cr.id).delete()
        for comp in set(payload.components):
            db.add(ChangeRequestComponent(cr_id=cr.id, component=comp))

    db.commit()
    db.refresh(cr)
    return _populate_cr_out(cr)


@router.post("/change-requests/{id}/transition", response_model=ChangeRequestOut)
def transition_change_request(
    id: uuid.UUID,
    payload: CRTransitionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cr = db.query(ChangeRequest).filter(ChangeRequest.id == id).first()
    if not cr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change Request not found")

    team = cr.team
    project = team.project
    get_team_with_access(team.id, current_user, db)
    now = datetime.now(timezone.utc)

    from_st = cr.status
    to_st = payload.to_status

    # Rule 20: Validate allowed transitions and permissions
    # 1. Draft to Submitted (team)
    if from_st == "draft" and to_st == "submitted":
        if current_user.role != "STUDENT" and current_user.id != project.faculty_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")

    # 2. Submitted to Under Review (faculty)
    elif from_st == "submitted" and to_st == "under_review":
        if current_user.role != "FACULTY":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only faculty can review change requests.")

    # 3. Under Review to Approved/Rejected (faculty, comment required on reject)
    elif from_st == "under_review" and to_st in ["approved", "rejected"]:
        if current_user.role != "FACULTY":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only faculty can approve/reject change requests.")
        if to_st == "rejected" and not (payload.comment and payload.comment.strip()):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A comment is required when rejecting a change request.")

    # 4. Approved to Implemented (team, with a new CI version and/or commit SHA attached)
    elif from_st == "approved" and to_st == "implemented":
        if not payload.implemented_commit_sha and not payload.implemented_version_id and not cr.implemented_commit_sha and not cr.implemented_version_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A new CI version or commit SHA must be attached when marking a change request as implemented."
            )
        if payload.implemented_commit_sha:
            cr.implemented_commit_sha = payload.implemented_commit_sha.strip()
        if payload.implemented_version_id:
            cr.implemented_version_id = payload.implemented_version_id

    # 5. Implemented to Verified (faculty)
    elif from_st == "implemented" and to_st == "verified":
        if current_user.role != "FACULTY":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only faculty can verify change requests.")

    # 6. Verified to Closed (faculty)
    elif from_st == "verified" and to_st == "closed":
        if current_user.role != "FACULTY":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only faculty can close change requests.")

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Illegal transition from '{from_st}' to '{to_st}'."
        )

    cr.status = to_st

    # Record transition
    trans = ChangeTransition(
        cr_id=cr.id,
        from_status=from_st,
        to_status=to_st,
        actor_id=current_user.id,
        comment=payload.comment,
        at=now
    )
    db.add(trans)

    # Notifications
    if to_st == "submitted":
        create_notification(
            db=db,
            user_id=project.faculty_user_id,
            kind="cr_submitted",
            message=f"Team {team.number} submitted Change Request {cr.cr_code}: '{cr.title}'.",
            link=f"/projects/{project.id}"
        )
    elif to_st in ["approved", "rejected", "verified", "closed"]:
        for m in team.members:
            create_notification(
                db=db,
                user_id=m.student_user_id,
                kind=f"cr_{to_st}",
                message=f"Change Request {cr.cr_code} transitioned to {to_st.upper()} by faculty." + (f" Note: {payload.comment}" if payload.comment else ""),
                link=f"/projects/{project.id}"
            )

    record_audit(
        db=db,
        action=f"CR_TRANSITION_{to_st.upper()}",
        entity_type="change_request",
        entity_id=cr.id,
        actor=current_user,
        project_id=project.id,
        team_id=team.id,
        before={"status": from_st},
        after={"status": to_st},
        note=payload.comment or f"Moved CR to {to_st}"
    )
    db.commit()
    db.refresh(cr)
    return _populate_cr_out(cr)


@router.get("/change-requests/{id}/impact", response_model=CRImpactOut)
def get_impact_analysis(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cr = db.query(ChangeRequest).filter(ChangeRequest.id == id).first()
    if not cr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Change Request not found")
    team = get_team_with_access(cr.team_id, current_user, db)

    # Rule 21: Directly affected CIs, reachable CIs through ci_dependencies graph traversal,
    # which of them are locked, which baselines contain them, and components ticked.
    directly_affected_ids = [it.ci_id for it in cr.items]
    direct_cis = db.query(ConfigurationItem).filter(ConfigurationItem.id.in_(directly_affected_ids)).all()

    # Graph traversal to find all reachable CIs
    all_team_cis = db.query(ConfigurationItem).filter(ConfigurationItem.team_id == team.id).all()
    dep_graph: Dict[uuid.UUID, List[ConfigurationItem]] = {c.id: c.depended_on_by for c in all_team_cis}

    reachable_ids: Set[uuid.UUID] = set()
    queue = list(directly_affected_ids)
    visited = set(directly_affected_ids)

    while queue:
        curr = queue.pop(0)
        # Find which CIs depend on curr (i.e. if curr changes, what items are impacted!)
        for dependent_ci in dep_graph.get(curr, []):
            if dependent_ci.id not in visited:
                visited.add(dependent_ci.id)
                reachable_ids.add(dependent_ci.id)
                queue.append(dependent_ci.id)

    indirect_cis = [c for c in all_team_cis if c.id in reachable_ids]

    all_affected_cis = direct_cis + indirect_cis
    all_affected_ids = [c.id for c in all_affected_cis]

    locked_list = [{"id": str(c.id), "ci_code": c.ci_code, "name": c.name} for c in all_affected_cis if c.is_locked]

    # Baselines containing any of these CIs
    affected_baselines = (
        db.query(Baseline)
        .join(baseline_items, Baseline.id == baseline_items.c.baseline_id)
        .join(CIVersion, baseline_items.c.ci_version_id == CIVersion.id)
        .filter(CIVersion.ci_id.in_(all_affected_ids))
        .distinct()
        .all()
    )

    baseline_info = [
        {"id": str(b.id), "code": b.code, "name": b.name, "status": b.status}
        for b in affected_baselines
    ]

    return CRImpactOut(
        cr_id=cr.id,
        cr_code=cr.cr_code,
        components=[c.component for c in cr.components],
        directly_affected_cis=[{"id": str(c.id), "ci_code": c.ci_code, "name": c.name, "is_locked": c.is_locked} for c in direct_cis],
        indirectly_affected_cis=[{"id": str(c.id), "ci_code": c.ci_code, "name": c.name, "is_locked": c.is_locked} for c in indirect_cis],
        locked_cis=locked_list,
        affected_baselines=baseline_info
    )
