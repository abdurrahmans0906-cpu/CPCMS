import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import get_db
from app.models.user import User
from app.models.scm import ConfigurationItem, CIVersion
from app.models.baseline import Baseline, baseline_items
from app.schemas.baseline import BaselineCreate, BaselineOut
from app.schemas.scm import CIVersionOut
from app.permissions import (
    get_current_user, require_faculty, get_team_with_access
)
from app.services.audit import record_audit
from app.services.notifications import create_notification

router = APIRouter(tags=["Baselines"])


def _populate_baseline_out(bl: Baseline) -> BaselineOut:
    items_out = []
    for v in bl.ci_versions:
        items_out.append(CIVersionOut(
            id=v.id,
            ci_id=v.ci_id,
            major=v.major,
            minor=v.minor,
            version_label=v.version_label,
            file_id=v.file_id,
            original_file_name=v.file.original_name if v.file else None,
            file_size_bytes=v.file.size_bytes if v.file else 0,
            content_sha256=v.content_sha256,
            change_description=v.change_description,
            created_by=v.created_by,
            created_by_name=v.creator.name if v.creator else None,
            status=v.status,
            approved_by=v.approved_by,
            approved_by_name=v.approver.name if v.approver else None,
            approved_at=v.approved_at,
            commit_sha=v.commit_sha,
            kind=v.kind,
            rollback_of_version_id=v.rollback_of_version_id,
            change_request_id=v.change_request_id,
            created_at=v.created_at
        ))

    return BaselineOut(
        id=bl.id,
        team_id=bl.team_id,
        code=bl.code,
        name=bl.name,
        description=bl.description,
        status=bl.status,
        created_by=bl.created_by,
        created_by_name=bl.creator.name if bl.creator else None,
        approved_by=bl.approved_by,
        approved_by_name=bl.approver.name if bl.approver else None,
        locked_at=bl.locked_at,
        created_at=bl.created_at,
        items=items_out
    )


@router.get("/teams/{team_id}/baselines", response_model=List[BaselineOut])
def list_baselines(
    team_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = get_team_with_access(team_id, current_user, db)
    baselines = db.query(Baseline).filter(Baseline.team_id == team.id).order_by(Baseline.created_at.desc()).all()
    return [_populate_baseline_out(bl) for bl in baselines]


@router.post("/teams/{team_id}/baselines", response_model=BaselineOut, status_code=status.HTTP_201_CREATED)
def create_baseline(
    team_id: uuid.UUID,
    payload: BaselineCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = get_team_with_access(team_id, current_user, db)
    now = datetime.now(timezone.utc)

    # Next baseline code per team: BL-001, BL-002...
    last_bl = db.query(Baseline).filter(Baseline.team_id == team.id).order_by(Baseline.code.desc()).first()
    next_num = 1
    if last_bl and last_bl.code.startswith("BL-"):
        try:
            next_num = int(last_bl.code.split("-")[-1]) + 1
        except ValueError:
            next_num = 1

    bl_code = f"BL-{next_num:03d}"

    # Verify all versions exist and are APPROVED (Rule 18)
    versions = db.query(CIVersion).filter(CIVersion.id.in_(payload.ci_version_ids)).all()
    if len(versions) != len(payload.ci_version_ids):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more specified CI versions not found.")

    for v in versions:
        if v.ci.team_id != team.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Version {v.version_label} belongs to another team.")
        if v.status != "approved":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only approved CI versions can be baselined. Version {v.ci.ci_code} v{v.version_label} is in status '{v.status}'."
            )

    is_faculty = (current_user.role == "FACULTY")
    initial_status = "locked" if is_faculty else "proposed"
    locked_time = now if is_faculty else None
    approver_id = current_user.id if is_faculty else None

    baseline = Baseline(
        team_id=team.id,
        code=bl_code,
        name=payload.name.strip(),
        description=payload.description,
        status=initial_status,
        created_by=current_user.id,
        approved_by=approver_id,
        locked_at=locked_time
    )
    baseline.ci_versions = versions
    db.add(baseline)
    db.flush()

    # Rule 19: If baseline is locked, lock each CI in it!
    if initial_status == "locked":
        for v in versions:
            v.ci.is_locked = True
            v.ci.updated_at = now

    record_audit(
        db=db,
        action="BASELINE_LOCKED" if initial_status == "locked" else "BASELINE_PROPOSED",
        entity_type="baseline",
        entity_id=baseline.id,
        actor=current_user,
        project_id=team.project_id,
        team_id=team.id,
        note=f"{'Created and locked' if is_faculty else 'Proposed'} baseline {baseline.code}: {baseline.name} with {len(versions)} CIs"
    )
    db.commit()
    db.refresh(baseline)
    return _populate_baseline_out(baseline)


@router.post("/baselines/{id}/approve", response_model=BaselineOut)
def approve_baseline(
    id: uuid.UUID,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    baseline = db.query(Baseline).filter(Baseline.id == id).first()
    if not baseline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Baseline not found")

    team = baseline.team
    if team.project.faculty_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Baseline not found")

    if baseline.status == "locked":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Baseline is already locked.")

    now = datetime.now(timezone.utc)
    baseline.status = "locked"
    baseline.approved_by = current_user.id
    baseline.locked_at = now

    # Rule 19: Lock each CI in this baseline
    for v in baseline.ci_versions:
        v.ci.is_locked = True
        v.ci.updated_at = now

    for m in team.members:
        create_notification(
            db=db,
            user_id=m.student_user_id,
            kind="baseline_locked",
            message=f"Baseline {baseline.code} ({baseline.name}) has been approved and locked by faculty.",
            link=f"/projects/{team.project_id}"
        )

    record_audit(
        db=db,
        action="BASELINE_APPROVED_LOCKED",
        entity_type="baseline",
        entity_id=baseline.id,
        actor=current_user,
        project_id=team.project_id,
        team_id=team.id,
        note=f"Approved and locked baseline {baseline.code}: {baseline.name}"
    )
    db.commit()
    db.refresh(baseline)
    return _populate_baseline_out(baseline)
