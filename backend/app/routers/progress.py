import os
import uuid
import hashlib
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import get_db
from app.config import settings
from app.models.user import User
from app.models.scm import FileModel
from app.models.progress import ProgressReport, ProgressScreenshot
from app.schemas.progress import (
    ProgressReportCreate, ProgressReportOut, ProgressCommentRequest,
    ProgressScreenshotOut
)
from app.permissions import get_current_user, require_faculty, get_team_with_access
from app.services.audit import record_audit
from app.services.notifications import create_notification

router = APIRouter(tags=["Progress"])


def _populate_progress_out(pr: ProgressReport) -> ProgressReportOut:
    avg = (
        pr.requirements_pct +
        pr.design_pct +
        pr.implementation_pct +
        pr.testing_pct +
        pr.documentation_pct
    ) / 5.0

    shots = [
        ProgressScreenshotOut(
            id=s.id,
            file_id=s.file_id,
            caption=s.caption,
            created_at=s.created_at
        ) for s in pr.screenshots
    ]

    return ProgressReportOut(
        id=pr.id,
        team_id=pr.team_id,
        review_id=pr.review_id,
        review_title=pr.review.title if pr.review else None,
        seq=pr.seq,
        requirements_pct=pr.requirements_pct,
        design_pct=pr.design_pct,
        implementation_pct=pr.implementation_pct,
        testing_pct=pr.testing_pct,
        documentation_pct=pr.documentation_pct,
        overall_progress_pct=round(avg, 1),
        notes=pr.notes,
        submitted_by=pr.submitted_by,
        submitted_by_name=pr.submitter.name if pr.submitter else None,
        faculty_comment=pr.faculty_comment,
        screenshots=shots,
        created_at=pr.created_at
    )


@router.get("/teams/{team_id}/progress", response_model=List[ProgressReportOut])
def list_progress_reports(
    team_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = get_team_with_access(team_id, current_user, db)
    reports = db.query(ProgressReport).filter(ProgressReport.team_id == team.id).order_by(ProgressReport.seq.desc()).all()
    return [_populate_progress_out(pr) for pr in reports]


@router.post("/teams/{team_id}/progress", response_model=ProgressReportOut, status_code=status.HTTP_201_CREATED)
def submit_progress_report(
    team_id: uuid.UUID,
    payload: ProgressReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = get_team_with_access(team_id, current_user, db)

    # Next sequence number
    last_pr = db.query(ProgressReport).filter(ProgressReport.team_id == team.id).order_by(ProgressReport.seq.desc()).first()
    next_seq = (last_pr.seq + 1) if last_pr else 1

    pr = ProgressReport(
        team_id=team.id,
        review_id=payload.review_id,
        seq=next_seq,
        requirements_pct=payload.requirements_pct,
        design_pct=payload.design_pct,
        implementation_pct=payload.implementation_pct,
        testing_pct=payload.testing_pct,
        documentation_pct=payload.documentation_pct,
        notes=payload.notes.strip(),
        submitted_by=current_user.id
    )
    db.add(pr)
    db.flush()

    record_audit(
        db=db,
        action="PROGRESS_REPORT_SUBMITTED",
        entity_type="progress_report",
        entity_id=pr.id,
        actor=current_user,
        project_id=team.project_id,
        team_id=team.id,
        note=f"Submitted progress report #{pr.seq}"
    )
    db.commit()
    db.refresh(pr)
    return _populate_progress_out(pr)


@router.post("/progress/{id}/screenshots", response_model=ProgressReportOut)
async def upload_progress_screenshot(
    id: uuid.UUID,
    file: UploadFile = File(...),
    caption: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pr = db.query(ProgressReport).filter(ProgressReport.id == id).first()
    if not pr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Progress report not found")
    team = get_team_with_access(pr.team_id, current_user, db)

    # Validate image only
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only image files (PNG, JPG, WebP) are permitted for screenshots."
        )

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Screenshot exceeds maximum size of 10 MB.")

    file_sha = hashlib.sha256(content).hexdigest()
    ext = file.filename.rsplit(".", 1)[-1] if "." in (file.filename or "") else "png"
    stored_name = f"screenshot_{uuid.uuid4().hex}.{ext}"
    stored_path = os.path.join(settings.UPLOAD_DIR, stored_name)
    with open(stored_path, "wb") as f_out:
        f_out.write(content)

    file_obj = FileModel(
        original_name=file.filename or "screenshot.png",
        stored_path=stored_path,
        mime=file.content_type,
        size_bytes=len(content),
        sha256=file_sha,
        uploaded_by=current_user.id
    )
    db.add(file_obj)
    db.flush()

    shot = ProgressScreenshot(
        progress_report_id=pr.id,
        file_id=file_obj.id,
        caption=caption.strip() if caption else None
    )
    db.add(shot)
    db.commit()
    db.refresh(pr)
    return _populate_progress_out(pr)


@router.post("/progress/{id}/comment", response_model=ProgressReportOut)
def comment_progress_report(
    id: uuid.UUID,
    payload: ProgressCommentRequest,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    pr = db.query(ProgressReport).filter(ProgressReport.id == id).first()
    if not pr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Progress report not found")
    team = pr.team
    if team.project.faculty_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Progress report not found")

    pr.faculty_comment = payload.faculty_comment.strip()

    for m in team.members:
        create_notification(
            db=db,
            user_id=m.student_user_id,
            kind="progress_feedback",
            message=f"Faculty commented on progress report #{pr.seq}: {pr.faculty_comment}",
            link=f"/projects/{team.project_id}"
        )

    record_audit(
        db=db,
        action="PROGRESS_COMMENTED",
        entity_type="progress_report",
        entity_id=pr.id,
        actor=current_user,
        project_id=team.project_id,
        team_id=team.id,
        note=f"Added feedback on report #{pr.seq}"
    )
    db.commit()
    db.refresh(pr)
    return _populate_progress_out(pr)
