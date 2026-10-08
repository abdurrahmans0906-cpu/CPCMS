import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.user import User
from app.models.baseline import Baseline
from app.models.release import Release
from app.schemas.release import ReleaseCreate, ReleaseOut, ReleaseDecisionRequest
from app.permissions import get_current_user, require_faculty, get_team_with_access
from app.services.audit import record_audit
from app.services.notifications import create_notification

router = APIRouter(tags=["Releases"])


def _populate_release_out(rel: Release) -> ReleaseOut:
    return ReleaseOut(
        id=rel.id,
        team_id=rel.team_id,
        code=rel.code,
        version=rel.version,
        baseline_id=rel.baseline_id,
        baseline_code=rel.baseline.code if rel.baseline else None,
        baseline_name=rel.baseline.name if rel.baseline else None,
        commit_sha=rel.commit_sha,
        test_status=rel.test_status,
        doc_status=rel.doc_status,
        status=rel.status,
        notes=rel.notes,
        requested_by=rel.requested_by,
        requested_by_name=rel.requester.name if rel.requester else None,
        approved_by=rel.approved_by,
        approved_by_name=rel.approver.name if rel.approver else None,
        created_at=rel.created_at
    )


@router.get("/teams/{team_id}/releases", response_model=List[ReleaseOut])
def list_team_releases(
    team_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = get_team_with_access(team_id, current_user, db)
    releases = db.query(Release).filter(Release.team_id == team.id).order_by(Release.created_at.desc()).all()
    return [_populate_release_out(r) for r in releases]


@router.post("/teams/{team_id}/releases", response_model=ReleaseOut, status_code=status.HTTP_201_CREATED)
def request_release(
    team_id: uuid.UUID,
    payload: ReleaseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = get_team_with_access(team_id, current_user, db)
    project = team.project

    baseline = db.query(Baseline).filter(
        Baseline.id == payload.baseline_id,
        Baseline.team_id == team.id
    ).first()
    if not baseline:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Baseline not found.")

    # Rule 24: Git commit sha mandatory if git_required
    if project.git_required and not (payload.commit_sha and payload.commit_sha.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Git commit SHA is mandatory for releases in projects where Git is required."
        )

    rel = Release(
        team_id=team.id,
        code=payload.code.strip(),
        version=payload.version.strip(),
        baseline_id=baseline.id,
        commit_sha=payload.commit_sha.strip() if payload.commit_sha else None,
        test_status="not_run",
        doc_status="pending",
        status="requested",
        notes=payload.notes.strip() if payload.notes else None,
        requested_by=current_user.id
    )
    db.add(rel)
    db.flush()

    create_notification(
        db=db,
        user_id=project.faculty_user_id,
        kind="release_requested",
        message=f"Team {team.number} requested release {rel.code} ({rel.version}) for baseline {baseline.code}.",
        link=f"/projects/{project.id}"
    )

    record_audit(
        db=db,
        action="RELEASE_REQUESTED",
        entity_type="release",
        entity_id=rel.id,
        actor=current_user,
        project_id=team.project_id,
        team_id=team.id,
        note=f"Requested release {rel.code} v{rel.version}"
    )
    db.commit()
    db.refresh(rel)
    return _populate_release_out(rel)


@router.post("/releases/{id}/decision", response_model=ReleaseOut)
def decide_release(
    id: uuid.UUID,
    payload: ReleaseDecisionRequest,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    rel = db.query(Release).filter(Release.id == id).first()
    if not rel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")

    team = rel.team
    if team.project.faculty_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Release not found")

    if payload.test_status:
        rel.test_status = payload.test_status
    if payload.doc_status:
        rel.doc_status = payload.doc_status

    if payload.decision == "approved":
        # Rule 24: Faculty approve only when:
        # 1. baseline is locked
        if rel.baseline.status != "locked":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Release approval refused: Baseline '{rel.baseline.code}' is not locked."
            )

        # 2. every CI version in it is approved
        unapproved = [v for v in rel.baseline.ci_versions if v.status != "approved"]
        if unapproved:
            bad_labels = ", ".join([f"{v.ci.ci_code} v{v.version_label}" for v in unapproved])
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Release approval refused: Baseline contains unapproved version(s): {bad_labels}."
            )

        # 3. test status is passed and documentation status is approved
        if rel.test_status != "passed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Release approval refused: Test status is '{rel.test_status}'. It must be 'passed'."
            )
        if rel.doc_status != "approved":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Release approval refused: Documentation status is '{rel.doc_status}'. It must be 'approved'."
            )

        rel.status = "approved"
        rel.approved_by = current_user.id

        # Rule 24: Approval moves the team to Released
        team.status = "Released"

    elif payload.decision == "rejected":
        rel.status = "rejected"
        rel.approved_by = current_user.id

    for m in team.members:
        create_notification(
            db=db,
            user_id=m.student_user_id,
            kind="release_decision",
            message=f"Release {rel.code} ({rel.version}) has been {payload.decision.upper()} by faculty.",
            link=f"/projects/{team.project_id}"
        )

    record_audit(
        db=db,
        action=f"RELEASE_{payload.decision.upper()}",
        entity_type="release",
        entity_id=rel.id,
        actor=current_user,
        project_id=team.project_id,
        team_id=team.id,
        note=f"Release {rel.code} {payload.decision} (tests={rel.test_status}, doc={rel.doc_status})"
    )
    db.commit()
    db.refresh(rel)
    return _populate_release_out(rel)
