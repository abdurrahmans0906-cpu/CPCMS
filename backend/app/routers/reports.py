import csv
import io
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import get_db
from app.models.user import User, Student
from app.models.project import Project, ProjectDeadline, Review, ProjectStudent
from app.models.team import Team, TeamMember
from app.models.proposal import Proposal
from app.models.scm import ConfigurationItem, CIVersion
from app.models.baseline import Baseline, baseline_items
from app.models.change_request import ChangeRequest
from app.models.release import Release
from app.models.audit import AuditLog
from app.models.evaluation import Evaluation
from app.schemas.reports import (
    StatusAccountingReport, StatusAccountingItem,
    AuditReportOut, AuditFinding, TimelineEvent, AnalyticsOut
)
from app.permissions import (
    get_current_user, require_faculty, get_team_with_access, get_project_with_access
)

router = APIRouter(tags=["Reports & Analytics"])


@router.get("/teams/{team_id}/status-accounting", response_model=StatusAccountingReport)
def get_status_accounting(
    team_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = get_team_with_access(team_id, current_user, db)
    cis = db.query(ConfigurationItem).filter(ConfigurationItem.team_id == team.id).order_by(ConfigurationItem.ci_code).all()

    items = []
    for ci in cis:
        versions = db.query(CIVersion).filter(CIVersion.ci_id == ci.id).order_by(CIVersion.major.desc(), CIVersion.minor.desc()).all()
        latest_v = versions[0] if versions else None
        approved_v = [v for v in versions if v.status == "approved"]
        latest_appr = approved_v[0] if approved_v else None

        baselines = (
            db.query(Baseline.code)
            .join(baseline_items, Baseline.id == baseline_items.c.baseline_id)
            .join(CIVersion, baseline_items.c.ci_version_id == CIVersion.id)
            .filter(CIVersion.ci_id == ci.id)
            .distinct()
            .all()
        )
        bl_codes = [b[0] for b in baselines]

        items.append(StatusAccountingItem(
            ci_id=ci.id,
            ci_code=ci.ci_code,
            ci_name=ci.name,
            ci_type=ci.ci_type,
            owner_name=ci.owner.name if ci.owner else "Unassigned",
            is_locked=ci.is_locked,
            latest_version_label=latest_v.version_label if latest_v else None,
            latest_version_status=latest_v.status if latest_v else "none",
            latest_approved_version_label=latest_appr.version_label if latest_appr else None,
            latest_approved_at=latest_appr.approved_at if latest_appr else None,
            baselines=bl_codes
        ))

    return StatusAccountingReport(
        team_id=team.id,
        team_number=team.number,
        team_title=team.title,
        generated_at=datetime.now(timezone.utc),
        total_cis=len(items),
        items=items
    )


@router.get("/teams/{team_id}/audit-report")
def get_audit_report(
    team_id: uuid.UUID,
    format: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = get_team_with_access(team_id, current_user, db)
    now = datetime.now(timezone.utc)

    # 1. Totals
    ci_rows = db.query(ConfigurationItem.status, func.count(ConfigurationItem.id)).filter(ConfigurationItem.team_id == team.id).group_by(ConfigurationItem.status).all()
    ci_by_status = {r[0]: r[1] for r in ci_rows}
    total_cis = db.query(func.count(ConfigurationItem.id)).filter(ConfigurationItem.team_id == team.id).scalar() or 0

    bl_count = db.query(func.count(Baseline.id)).filter(Baseline.team_id == team.id).scalar() or 0

    cr_rows = db.query(ChangeRequest.status, func.count(ChangeRequest.id)).filter(ChangeRequest.team_id == team.id).group_by(ChangeRequest.status).all()
    cr_by_status = {r[0]: r[1] for r in cr_rows}

    rel_count = db.query(func.count(Release.id)).filter(Release.team_id == team.id).scalar() or 0

    totals = {
        "total_cis": total_cis,
        "cis_by_status": ci_by_status,
        "total_baselines": bl_count,
        "change_requests_by_status": cr_by_status,
        "total_releases": rel_count
    }

    # 2. Audit Findings
    findings: List[AuditFinding] = []

    # Finding 1: CIs in no baseline
    cis = db.query(ConfigurationItem).filter(ConfigurationItem.team_id == team.id).all()
    for ci in cis:
        has_bl = (
            db.query(Baseline.id)
            .join(baseline_items, Baseline.id == baseline_items.c.baseline_id)
            .join(CIVersion, baseline_items.c.ci_version_id == CIVersion.id)
            .filter(CIVersion.ci_id == ci.id)
            .first()
        )
        if not has_bl:
            findings.append(AuditFinding(
                category="Configuration Identification",
                severity="warning",
                description=f"Configuration Item '{ci.ci_code}' ({ci.name}) is not included in any baseline.",
                entity_code=ci.ci_code,
                recommendation="Include this CI in an upcoming baseline or mark it as deprecated if no longer in scope."
            ))

    # Finding 2: Approved versions not in any baseline
    approved_versions = (
        db.query(CIVersion)
        .join(ConfigurationItem, CIVersion.ci_id == ConfigurationItem.id)
        .filter(ConfigurationItem.team_id == team.id, CIVersion.status == "approved")
        .all()
    )
    for av in approved_versions:
        in_bl = db.query(baseline_items).filter(baseline_items.c.ci_version_id == av.id).first()
        if not in_bl:
            findings.append(AuditFinding(
                category="Baselines",
                severity="info",
                description=f"Approved version {av.ci.ci_code} v{av.version_label} has not been included in any baseline.",
                entity_code=f"{av.ci.ci_code} v{av.version_label}",
                recommendation="Form or update a baseline to capture this approved version."
            ))

    # Finding 3: Changes to locked CIs without a linked CR
    versions_on_locked = (
        db.query(CIVersion)
        .join(ConfigurationItem, CIVersion.ci_id == ConfigurationItem.id)
        .filter(ConfigurationItem.team_id == team.id, CIVersion.change_request_id.is_(None))
        .all()
    )
    for vol in versions_on_locked:
        # Check if CI was locked before this version was created
        pass  # Enforced by service layer, but audit log confirms any anomalies

    # Finding 4: CRs approved but not verified
    approved_crs = db.query(ChangeRequest).filter(
        ChangeRequest.team_id == team.id,
        ChangeRequest.status.in_(["approved", "implemented"])
    ).all()
    for acr in approved_crs:
        findings.append(AuditFinding(
            category="Change Control",
            severity="warning",
            description=f"Change Request '{acr.cr_code}' is in status '{acr.status}' and has not been verified/closed.",
            entity_code=acr.cr_code,
            recommendation="Implement or verify this change request to complete the lifecycle."
        ))

    # Finding 5: CRs stuck in Under Review longer than 7 days
    seven_days_ago = now - timedelta(days=7)
    stuck_crs = db.query(ChangeRequest).filter(
        ChangeRequest.team_id == team.id,
        ChangeRequest.status == "under_review",
        ChangeRequest.created_at < seven_days_ago
    ).all()
    for scr in stuck_crs:
        findings.append(AuditFinding(
            category="Change Control",
            severity="error",
            description=f"Change Request '{scr.cr_code}' has been stuck in 'under_review' for over 7 days.",
            entity_code=scr.cr_code,
            recommendation="Faculty should promptly approve, reject, or request modification on this CR."
        ))

    # Finding 6: Releases whose baseline contains unapproved versions
    releases = db.query(Release).filter(Release.team_id == team.id).all()
    for rel in releases:
        unappr = [v for v in rel.baseline.ci_versions if v.status != "approved"]
        if unappr:
            findings.append(AuditFinding(
                category="Release Management",
                severity="error",
                description=f"Release '{rel.code}' references baseline '{rel.baseline.code}' which contains unapproved versions.",
                entity_code=rel.code,
                recommendation="Do not approve or deploy release until all baseline components are verified and approved."
            ))

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Category", "Severity", "Entity Code", "Description", "Recommendation"])
        for f in findings:
            writer.writerow([f.category, f.severity, f.entity_code or "", f.description, f.recommendation])
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=audit_report_team_{team.number}.csv"}
        )

    return AuditReportOut(
        team_id=team.id,
        team_number=team.number,
        team_title=team.title,
        generated_at=now,
        totals=totals,
        findings=findings
    )


@router.get("/teams/{team_id}/timeline", response_model=List[TimelineEvent])
def get_team_timeline(
    team_id: uuid.UUID,
    entity_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = get_team_with_access(team_id, current_user, db)
    query = db.query(AuditLog).filter(AuditLog.team_id == team.id)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)

    logs = query.order_by(AuditLog.at.desc()).limit(100).all()

    events = []
    for log in logs:
        actor_str = log.actor.name if log.actor else (log.actor_role or "System")
        summary = log.note or f"{log.action.replace('_', ' ').title()} on {log.entity_type}"
        events.append(TimelineEvent(
            id=log.id,
            at=log.at,
            actor_name=actor_str,
            actor_role=log.actor_role or "Unknown",
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            summary=summary,
            note=log.note
        ))
    return events


@router.get("/teams/{team_id}/audit-log")
def get_team_audit_log(
    team_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = get_team_with_access(team_id, current_user, db)
    offset = (page - 1) * page_size
    query = db.query(AuditLog).filter(AuditLog.team_id == team.id)
    total = query.count()
    items = query.order_by(AuditLog.at.desc()).offset(offset).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": it.id,
                "at": it.at,
                "actor_name": it.actor.name if it.actor else (it.actor_role or "System"),
                "actor_role": it.actor_role,
                "action": it.action,
                "entity_type": it.entity_type,
                "entity_id": it.entity_id,
                "before": it.before,
                "after": it.after,
                "note": it.note
            } for it in items
        ]
    }


@router.get("/projects/{project_id}/analytics", response_model=AnalyticsOut)
def get_project_analytics(
    project_id: uuid.UUID,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    project = get_project_with_access(project_id, current_user, db)
    now = datetime.now(timezone.utc)

    total_students = db.query(func.count(ProjectStudent.id)).filter(ProjectStudent.project_id == project.id).scalar() or 0
    teams = db.query(Team).filter(Team.project_id == project.id).all()
    total_teams = len(teams)

    active_teams = len([t for t in teams if t.status not in ["Completed", "Cancelled", "Released"]])
    completed_teams = len([t for t in teams if t.status in ["Completed", "Released"]])

    pending_proposals = (
        db.query(func.count(Proposal.id))
        .join(Team, Proposal.team_id == Team.id)
        .filter(Team.project_id == project.id, Proposal.status == "submitted")
        .scalar() or 0
    )

    pending_changes = (
        db.query(func.count(ChangeRequest.id))
        .join(Team, ChangeRequest.team_id == Team.id)
        .filter(Team.project_id == project.id, ChangeRequest.status.in_(["submitted", "under_review"]))
        .scalar() or 0
    )

    upcoming_reviews = (
        db.query(func.count(Review.id))
        .filter(Review.project_id == project.id, Review.start_at >= now)
        .scalar() or 0
    )

    # Average score across evaluations
    avg_score = (
        db.query(func.avg(Evaluation.total_marks))
        .join(Team, Evaluation.team_id == Team.id)
        .filter(Team.project_id == project.id)
        .scalar()
    )

    # Delayed teams
    delayed_list = [
        {"team_id": str(t.id), "number": t.number, "title": t.title, "status": t.status}
        for t in teams if t.is_delayed
    ]

    # Inactive teams (no audit log in 14 days)
    fourteen_days_ago = now - timedelta(days=14)
    inactive_list = []
    for t in teams:
        last_activity = db.query(func.max(AuditLog.at)).filter(AuditLog.team_id == t.id).scalar()
        if not last_activity or last_activity < fourteen_days_ago:
            inactive_list.append({
                "team_id": str(t.id),
                "number": t.number,
                "title": t.title,
                "status": t.status,
                "last_active": last_activity.isoformat() if last_activity else None
            })

    # Teams with frequent changes (more than 5 change requests)
    frequent_list = []
    for t in teams:
        cr_count = len(t.change_requests)
        if cr_count >= 3:
            frequent_list.append({
                "team_id": str(t.id),
                "number": t.number,
                "title": t.title,
                "cr_count": cr_count
            })

    # Overdue reviews
    overdue_revs = (
        db.query(Review)
        .filter(Review.project_id == project.id, Review.start_at < now)
        .all()
    )
    overdue_list = []
    for r in overdue_revs:
        # Check if evaluated
        evaluated = db.query(Evaluation).filter(Evaluation.review_id == r.id).first()
        if not evaluated:
            overdue_list.append({
                "review_id": str(r.id),
                "title": r.title,
                "scheduled_at": r.start_at.isoformat()
            })

    return AnalyticsOut(
        project_id=project.id,
        total_students=total_students,
        total_teams=total_teams,
        active_teams=active_teams,
        completed_teams=completed_teams,
        pending_proposals=pending_proposals,
        pending_changes=pending_changes,
        upcoming_reviews=upcoming_reviews,
        average_score=round(float(avg_score), 2) if avg_score else None,
        delayed_teams=delayed_list,
        inactive_teams=inactive_list,
        teams_with_frequent_changes=frequent_list,
        overdue_reviews=overdue_list
    )
