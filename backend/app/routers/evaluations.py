import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import get_db
from app.models.user import User
from app.models.project import EvaluationCriteria
from app.models.team import Team
from app.models.evaluation import Evaluation, EvaluationScore
from app.schemas.evaluation import EvaluationCreate, EvaluationOut, EvaluationScoreOut
from app.permissions import get_current_user, require_faculty, get_team_with_access
from app.services.audit import record_audit
from app.services.notifications import create_notification

router = APIRouter(tags=["Evaluations"])


def _calculate_grade(total_marks: float, grade_bands: list) -> str:
    for band in grade_bands:
        if band.get("min", 0) <= total_marks <= band.get("max", 100):
            return band.get("grade", "F")
    return "F"


def _populate_evaluation_out(ev: Evaluation) -> EvaluationOut:
    scores_out = []
    for s in ev.scores:
        crit = s.criterion
        scores_out.append(EvaluationScoreOut(
            id=s.id,
            criterion_id=s.criterion_id,
            criterion_name=crit.name if crit else "Unknown",
            max_marks=crit.max_marks if crit else 0,
            marks=float(s.marks),
            comment=s.comment,
            created_at=s.created_at
        ))

    return EvaluationOut(
        id=ev.id,
        team_id=ev.team_id,
        review_id=ev.review_id,
        review_title=ev.review.title if ev.review else None,
        stage=ev.stage,
        total_marks=float(ev.total_marks),
        grade=ev.grade,
        feedback=ev.feedback,
        evaluated_by=ev.evaluated_by,
        evaluated_by_name=ev.evaluator.name if ev.evaluator else None,
        scores=scores_out,
        created_at=ev.created_at
    )


@router.get("/teams/{team_id}/evaluations", response_model=List[EvaluationOut])
def list_team_evaluations(
    team_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = get_team_with_access(team_id, current_user, db)
    evals = db.query(Evaluation).filter(Evaluation.team_id == team.id).order_by(Evaluation.created_at.desc()).all()
    return [_populate_evaluation_out(ev) for ev in evals]


@router.post("/teams/{team_id}/evaluations", response_model=EvaluationOut, status_code=status.HTTP_201_CREATED)
def record_evaluation(
    team_id: uuid.UUID,
    payload: EvaluationCreate,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    team = get_team_with_access(team_id, current_user, db)
    project = team.project

    # Rule 27: Verify criteria sum equals project's total_marks
    total_criteria_sum = (
        db.query(func.coalesce(func.sum(EvaluationCriteria.max_marks), 0))
        .filter(EvaluationCriteria.project_id == project.id)
        .scalar()
    )
    if total_criteria_sum != project.total_marks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The sum of evaluation criteria ({total_criteria_sum}) must equal total marks ({project.total_marks}) before any evaluation can be saved."
        )

    # Validate each score against criterion max_marks
    criteria_map = {c.id: c for c in project.evaluation_criteria}
    total_awarded = 0.0

    for sc in payload.scores:
        if sc.criterion_id not in criteria_map:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Criterion '{sc.criterion_id}' not found.")
        crit = criteria_map[sc.criterion_id]
        if sc.marks > crit.max_marks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Marks for '{crit.name}' ({sc.marks}) exceed maximum allowed ({crit.max_marks})."
            )
        total_awarded += sc.marks

    grade = _calculate_grade(total_awarded, project.grade_bands or [])

    ev = Evaluation(
        team_id=team.id,
        review_id=payload.review_id,
        stage=payload.stage,
        total_marks=total_awarded,
        grade=grade,
        feedback=payload.feedback,
        evaluated_by=current_user.id
    )
    db.add(ev)
    db.flush()

    for sc in payload.scores:
        ev_score = EvaluationScore(
            evaluation_id=ev.id,
            criterion_id=sc.criterion_id,
            marks=sc.marks,
            comment=sc.comment
        )
        db.add(ev_score)

    for m in team.members:
        create_notification(
            db=db,
            user_id=m.student_user_id,
            kind="evaluation_published",
            message=f"Evaluation published for stage '{ev.stage}'. Score: {total_awarded}/{project.total_marks} (Grade: {grade}).",
            link=f"/projects/{project.id}"
        )

    record_audit(
        db=db,
        action="EVALUATION_RECORDED",
        entity_type="evaluation",
        entity_id=ev.id,
        actor=current_user,
        project_id=project.id,
        team_id=team.id,
        note=f"Recorded {ev.stage} evaluation: {total_awarded} marks, grade {grade}"
    )
    db.commit()
    db.refresh(ev)
    return _populate_evaluation_out(ev)
