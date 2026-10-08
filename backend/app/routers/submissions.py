import os
import uuid
import hashlib
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.db import get_db
from app.config import settings
from app.models.user import User
from app.models.scm import FileModel
from app.models.project import ProjectDeadline
from app.models.progress import Submission
from app.schemas.progress import (
    SubmissionCreate, SubmissionOut, SubmissionDecisionRequest
)
from app.permissions import get_current_user, require_faculty, get_team_with_access
from app.services.audit import record_audit
from app.services.notifications import create_notification

router = APIRouter(tags=["Submissions"])


def _populate_submission_out(sub: Submission) -> SubmissionOut:
    return SubmissionOut(
        id=sub.id,
        team_id=sub.team_id,
        kind=sub.kind,
        version_label=sub.version_label,
        commit_sha=sub.commit_sha,
        repo_url=sub.repo_url,
        file_id=sub.file_id,
        original_file_name=sub.file.original_name if sub.file else None,
        notes=sub.notes,
        submitted_by=sub.submitted_by,
        submitted_by_name=sub.submitter.name if sub.submitter else None,
        is_late=sub.is_late,
        status=sub.status,
        faculty_feedback=sub.faculty_feedback,
        created_at=sub.created_at
    )


@router.get("/teams/{team_id}/submissions", response_model=List[SubmissionOut])
def list_submissions(
    team_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = get_team_with_access(team_id, current_user, db)
    subs = db.query(Submission).filter(Submission.team_id == team.id).order_by(Submission.created_at.desc()).all()
    return [_populate_submission_out(s) for s in subs]


@router.post("/teams/{team_id}/submissions", response_model=SubmissionOut, status_code=status.HTTP_201_CREATED)
async def create_submission(
    team_id: uuid.UUID,
    kind: str = Form(...),  # github, zip, source, release_package
    version_label: Optional[str] = Form(None),
    commit_sha: Optional[str] = Form(None),
    repo_url: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = get_team_with_access(team_id, current_user, db)
    project = team.project
    now = datetime.now(timezone.utc)

    # Rule 25: Check deadline and late policy
    # Find relevant deadline for project (e.g. 'final' or 'srs')
    deadline = db.query(ProjectDeadline).filter(
        ProjectDeadline.project_id == project.id,
        ProjectDeadline.kind.in_(["final", "srs", "review"])
    ).order_by(ProjectDeadline.due_at.asc()).first()

    is_late = False
    if deadline and now > deadline.due_at:
        is_late = True
        if project.late_policy == "reject":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The deadline ({deadline.due_at.strftime('%Y-%m-%d %H:%M')}) has passed. Late submissions are strictly rejected per project policy."
            )

    file_model_id = None
    if file:
        content = await file.read()
        file_sha = hashlib.sha256(content).hexdigest()
        ext = file.filename.rsplit(".", 1)[-1] if "." in (file.filename or "") else "bin"
        stored_name = f"sub_{uuid.uuid4().hex}.{ext}"
        stored_path = os.path.join(settings.UPLOAD_DIR, stored_name)
        with open(stored_path, "wb") as f_out:
            f_out.write(content)

        file_obj = FileModel(
            original_name=file.filename or "submission",
            stored_path=stored_path,
            mime=file.content_type or "application/octet-stream",
            size_bytes=len(content),
            sha256=file_sha,
            uploaded_by=current_user.id
        )
        db.add(file_obj)
        db.flush()
        file_model_id = file_obj.id

    sub = Submission(
        team_id=team.id,
        kind=kind,
        version_label=version_label,
        commit_sha=commit_sha.strip() if commit_sha else None,
        repo_url=repo_url.strip() if repo_url else None,
        file_id=file_model_id,
        notes=notes.strip() if notes else None,
        submitted_by=current_user.id,
        is_late=is_late,
        status="submitted"
    )
    db.add(sub)
    db.flush()

    record_audit(
        db=db,
        action="SUBMISSION_CREATED",
        entity_type="submission",
        entity_id=sub.id,
        actor=current_user,
        project_id=team.project_id,
        team_id=team.id,
        note=f"Submitted {sub.kind} (is_late={is_late})"
    )
    db.commit()
    db.refresh(sub)
    return _populate_submission_out(sub)


@router.post("/submissions/{id}/decision", response_model=SubmissionOut)
def decide_submission(
    id: uuid.UUID,
    payload: SubmissionDecisionRequest,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    sub = db.query(Submission).filter(Submission.id == id).first()
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    team = sub.team
    if team.project.faculty_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    sub.status = payload.decision
    sub.faculty_feedback = payload.feedback

    if payload.decision == "rejected":
        for m in team.members:
            create_notification(
                db=db,
                user_id=m.student_user_id,
                kind="submission_rejected",
                message=f"Your {sub.kind} submission was rejected by faculty." + (f" Feedback: {payload.feedback}" if payload.feedback else ""),
                link=f"/projects/{team.project_id}"
            )

    record_audit(
        db=db,
        action=f"SUBMISSION_{payload.decision.upper()}",
        entity_type="submission",
        entity_id=sub.id,
        actor=current_user,
        project_id=team.project_id,
        team_id=team.id,
        note=f"Submission decision: {payload.decision}"
    )
    db.commit()
    db.refresh(sub)
    return _populate_submission_out(sub)
