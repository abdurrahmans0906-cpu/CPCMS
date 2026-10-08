import hashlib
import os
import shutil
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import get_db
from app.config import settings
from app.models.user import User
from app.models.team import Team
from app.models.scm import ConfigurationItem, CIVersion, FileModel, ci_dependencies
from app.models.baseline import Baseline, baseline_items
from app.schemas.scm import (
    CICreate, CIUpdate, CIOut, CIVersionOut,
    CIVersionDecisionRequest, RollbackRequest,
    DependenciesUpdateRequest, VersionCompareOut, CIDependencyOut
)
from app.permissions import (
    get_current_user, require_faculty, get_team_with_access, get_project_with_access
)
from app.services.audit import record_audit
from app.services.notifications import create_notification
from app.services.locking import validate_ci_modification_allowed
from app.services.diff import generate_version_diff

router = APIRouter(tags=["Configuration Items & Versions"])


def _populate_ci_version_out(v: CIVersion) -> CIVersionOut:
    return CIVersionOut(
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
    )


def _populate_ci_out(ci: ConfigurationItem, db: Session) -> CIOut:
    versions = db.query(CIVersion).filter(CIVersion.ci_id == ci.id).order_by(CIVersion.major.desc(), CIVersion.minor.desc()).all()
    v_outs = [_populate_ci_version_out(v) for v in versions]

    latest_v = v_outs[0] if v_outs else None
    approved_versions = [v for v in v_outs if v.status == "approved"]
    latest_appr = approved_versions[0] if approved_versions else None

    # Baselines containing this CI
    baselines = (
        db.query(Baseline.code)
        .join(baseline_items, Baseline.id == baseline_items.c.baseline_id)
        .join(CIVersion, baseline_items.c.ci_version_id == CIVersion.id)
        .filter(CIVersion.ci_id == ci.id)
        .distinct()
        .all()
    )
    bl_codes = [b[0] for b in baselines]

    deps = [
        CIDependencyOut(
            id=d.id,
            ci_code=d.ci_code,
            name=d.name,
            ci_type=d.ci_type,
            is_locked=d.is_locked
        ) for d in ci.dependencies
    ]

    return CIOut(
        id=ci.id,
        team_id=ci.team_id,
        ci_code=ci.ci_code,
        name=ci.name,
        ci_type=ci.ci_type,
        owner_user_id=ci.owner_user_id,
        owner_name=ci.owner.name if ci.owner else None,
        current_version_id=ci.current_version_id,
        status=ci.status,
        is_locked=ci.is_locked,
        updated_at=ci.updated_at,
        created_at=ci.created_at,
        latest_version=latest_v,
        latest_approved_version=latest_appr,
        versions=v_outs,
        dependencies=deps,
        baseline_codes=bl_codes
    )


@router.get("/teams/{team_id}/cis", response_model=List[CIOut])
def list_cis(
    team_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = get_team_with_access(team_id, current_user, db)
    cis = db.query(ConfigurationItem).filter(ConfigurationItem.team_id == team.id).order_by(ConfigurationItem.ci_code).all()
    return [_populate_ci_out(ci, db) for ci in cis]


@router.post("/teams/{team_id}/cis", response_model=CIOut, status_code=status.HTTP_201_CREATED)
def create_ci(
    team_id: uuid.UUID,
    payload: CICreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = get_team_with_access(team_id, current_user, db)

    # Next CI code per team: CI-001, CI-002...
    last_ci = db.query(ConfigurationItem).filter(ConfigurationItem.team_id == team.id).order_by(ConfigurationItem.ci_code.desc()).first()
    next_num = 1
    if last_ci and last_ci.ci_code.startswith("CI-"):
        try:
            next_num = int(last_ci.ci_code.split("-")[-1]) + 1
        except ValueError:
            next_num = 1

    ci_code = f"CI-{next_num:03d}"

    ci = ConfigurationItem(
        team_id=team.id,
        ci_code=ci_code,
        name=payload.name.strip(),
        ci_type=payload.ci_type,
        owner_user_id=payload.owner_user_id or current_user.id,
        status="draft",
        is_locked=False,
        updated_at=datetime.now(timezone.utc)
    )
    db.add(ci)
    db.flush()

    record_audit(
        db=db,
        action="CI_CREATE",
        entity_type="configuration_item",
        entity_id=ci.id,
        actor=current_user,
        project_id=team.project_id,
        team_id=team.id,
        note=f"Created {ci.ci_code}: {ci.name} ({ci.ci_type})"
    )
    db.commit()
    db.refresh(ci)
    return _populate_ci_out(ci, db)


@router.get("/cis/{id}", response_model=CIOut)
def get_ci(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ci = db.query(ConfigurationItem).filter(ConfigurationItem.id == id).first()
    if not ci:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Configuration Item not found")
    get_team_with_access(ci.team_id, current_user, db)
    return _populate_ci_out(ci, db)


@router.patch("/cis/{id}", response_model=CIOut)
def update_ci(
    id: uuid.UUID,
    payload: CIUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ci = db.query(ConfigurationItem).filter(ConfigurationItem.id == id).first()
    if not ci:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Configuration Item not found")
    team = get_team_with_access(ci.team_id, current_user, db)

    if payload.name is not None:
        ci.name = payload.name.strip()
    if payload.owner_user_id is not None:
        ci.owner_user_id = payload.owner_user_id

    ci.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(ci)
    return _populate_ci_out(ci, db)


# --- Dependencies with Cycle Check ---

def has_cycle(start_ci_id: uuid.UUID, adj_list: dict) -> bool:
    visited = set()
    rec_stack = set()

    def dfs(node):
        visited.add(node)
        rec_stack.add(node)
        for neighbor in adj_list.get(node, []):
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True
        rec_stack.remove(node)
        return False

    return dfs(start_ci_id)


@router.put("/cis/{id}/dependencies", response_model=CIOut)
def update_ci_dependencies(
    id: uuid.UUID,
    payload: DependenciesUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ci = db.query(ConfigurationItem).filter(ConfigurationItem.id == id).first()
    if not ci:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Configuration Item not found")
    team = get_team_with_access(ci.team_id, current_user, db)

    # Cannot depend on self
    if ci.id in payload.depends_on_ci_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A configuration item cannot depend on itself."
        )

    # Build simulated adjacency graph for cycle check
    all_team_cis = db.query(ConfigurationItem).filter(ConfigurationItem.team_id == team.id).all()
    valid_ids = {c.id for c in all_team_cis}
    for did in payload.depends_on_ci_ids:
        if did not in valid_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Dependency CI '{did}' does not exist in this team."
            )

    adj = {}
    for c in all_team_cis:
        if c.id == ci.id:
            adj[c.id] = list(payload.depends_on_ci_ids)
        else:
            adj[c.id] = [d.id for d in c.dependencies]

    # Check cycles across the graph
    for c_id in adj:
        if has_cycle(c_id, adj):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cycle detected: Circular dependency between configuration items is strictly prohibited."
            )

    target_cis = db.query(ConfigurationItem).filter(ConfigurationItem.id.in_(payload.depends_on_ci_ids)).all()
    ci.dependencies = target_cis
    ci.updated_at = datetime.now(timezone.utc)

    record_audit(
        db=db,
        action="CI_DEPENDENCIES_UPDATE",
        entity_type="configuration_item",
        entity_id=ci.id,
        actor=current_user,
        project_id=team.project_id,
        team_id=team.id,
        note=f"Updated dependencies for {ci.ci_code} ({len(target_cis)} items)"
    )
    db.commit()
    db.refresh(ci)
    return _populate_ci_out(ci, db)


# --- Version Upload & Lifecycle ---

@router.post("/cis/{id}/versions", response_model=CIVersionOut, status_code=status.HTTP_201_CREATED)
async def upload_ci_version(
    id: uuid.UUID,
    file: UploadFile = File(...),
    change_description: str = Form(...),
    bump_type: str = Form("minor"),  # "major" or "minor"
    commit_sha: Optional[str] = Form(None),
    change_request_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ci = db.query(ConfigurationItem).filter(ConfigurationItem.id == id).first()
    if not ci:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Configuration Item not found")
    team = get_team_with_access(ci.team_id, current_user, db)
    project = team.project

    # Rule 19 & 22: Locking check
    cr_uuid = uuid.UUID(change_request_id) if change_request_id else None
    validate_ci_modification_allowed(db, ci, cr_uuid)

    # Validate file extension and size against project rules
    filename = file.filename or "artifact"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if project.allowed_file_exts and ext not in [e.lower() for e in project.allowed_file_exts]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '.{ext}' is not permitted. Allowed: {', '.join(project.allowed_file_exts)}."
        )

    content = await file.read()
    size_bytes = len(content)
    max_bytes = project.max_file_mb * 1024 * 1024
    if size_bytes > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size ({size_bytes / 1024 / 1024:.2f} MB) exceeds maximum allowed limit ({project.max_file_mb} MB)."
        )

    # Compute sha256
    file_sha256 = hashlib.sha256(content).hexdigest()

    # Rule 15: Reject duplicate sha256 against current version
    latest_version = db.query(CIVersion).filter(CIVersion.ci_id == ci.id).order_by(CIVersion.major.desc(), CIVersion.minor.desc()).first()
    if latest_version and latest_version.content_sha256 == file_sha256:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate file content detected. The uploaded file is identical to the current version."
        )

    # Store file under random name in UPLOAD_DIR
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}_{ext}" if ext else uuid.uuid4().hex
    stored_path = os.path.join(settings.UPLOAD_DIR, stored_name)
    with open(stored_path, "wb") as f_out:
        f_out.write(content)

    file_model = FileModel(
        original_name=filename,
        stored_path=stored_path,
        mime=file.content_type or "application/octet-stream",
        size_bytes=size_bytes,
        sha256=file_sha256,
        uploaded_by=current_user.id
    )
    db.add(file_model)
    db.flush()

    # Determine major and minor bump
    if not latest_version:
        major, minor = 1, 0
    else:
        if bump_type == "major":
            major = latest_version.major + 1
            minor = 0
        else:
            major = latest_version.major
            minor = latest_version.minor + 1

    version_label = f"{major}.{minor}"

    version = CIVersion(
        ci_id=ci.id,
        major=major,
        minor=minor,
        version_label=version_label,
        file_id=file_model.id,
        content_sha256=file_sha256,
        change_description=change_description.strip(),
        created_by=current_user.id,
        status="draft",
        commit_sha=commit_sha.strip() if commit_sha else None,
        kind="upload",
        change_request_id=cr_uuid
    )
    db.add(version)
    db.flush()

    ci.current_version_id = version.id
    ci.status = "draft"
    ci.updated_at = datetime.now(timezone.utc)

    record_audit(
        db=db,
        action="VERSION_UPLOAD",
        entity_type="ci_version",
        entity_id=version.id,
        actor=current_user,
        project_id=team.project_id,
        team_id=team.id,
        note=f"Uploaded {ci.ci_code} v{version_label} (locked override CR: {cr_uuid or 'None'})"
    )
    db.commit()
    db.refresh(version)
    return _populate_ci_version_out(version)


@router.get("/versions/{id}/download")
def download_ci_version(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    version = db.query(CIVersion).filter(CIVersion.id == id).first()
    if not version or not version.file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version or file not found")

    ci = version.ci
    get_team_with_access(ci.team_id, current_user, db)

    if not os.path.exists(version.file.stored_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored file missing on server disk")

    return FileResponse(
        path=version.file.stored_path,
        filename=version.file.original_name,
        media_type=version.file.mime
    )


@router.post("/versions/{id}/submit", response_model=CIVersionOut)
def submit_version_for_review(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    version = db.query(CIVersion).filter(CIVersion.id == id).first()
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")

    ci = version.ci
    team = get_team_with_access(ci.team_id, current_user, db)

    if version.status != "draft":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Version is already in status '{version.status}'.")

    version.status = "submitted"
    ci.status = "under_review"
    ci.updated_at = datetime.now(timezone.utc)

    create_notification(
        db=db,
        user_id=team.project.faculty_user_id,
        kind="version_submitted",
        message=f"Team {team.number} submitted {ci.ci_code} v{version.version_label} for review.",
        link=f"/projects/{team.project_id}"
    )

    record_audit(
        db=db,
        action="VERSION_SUBMITTED",
        entity_type="ci_version",
        entity_id=version.id,
        actor=current_user,
        project_id=team.project_id,
        team_id=team.id,
        note=f"Submitted {ci.ci_code} v{version.version_label} for faculty review"
    )
    db.commit()
    db.refresh(version)
    return _populate_ci_version_out(version)


@router.post("/versions/{id}/decision", response_model=CIVersionOut)
def decide_ci_version(
    id: uuid.UUID,
    payload: CIVersionDecisionRequest,
    current_user: User = Depends(require_faculty),
    db: Session = Depends(get_db)
):
    version = db.query(CIVersion).filter(CIVersion.id == id).first()
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")

    ci = version.ci
    team = version.ci.team
    if team.project.faculty_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")

    now = datetime.now(timezone.utc)
    version.status = payload.decision
    if payload.decision == "approved":
        version.approved_by = current_user.id
        version.approved_at = now
        ci.status = "approved"
    else:
        ci.status = "rejected"

    ci.updated_at = now

    for m in team.members:
        create_notification(
            db=db,
            user_id=m.student_user_id,
            kind="version_decision",
            message=f"Faculty {payload.decision.upper()} {ci.ci_code} v{version.version_label}." + (f" Note: {payload.comment}" if payload.comment else ""),
            link=f"/projects/{team.project_id}"
        )

    record_audit(
        db=db,
        action=f"VERSION_{payload.decision.upper()}",
        entity_type="ci_version",
        entity_id=version.id,
        actor=current_user,
        project_id=team.project_id,
        team_id=team.id,
        note=f"{payload.decision.title()} {ci.ci_code} v{version.version_label}. Comment: {payload.comment or 'None'}"
    )
    db.commit()
    db.refresh(version)
    return _populate_ci_version_out(version)


# --- Version Comparison ---

@router.get("/cis/{id}/compare", response_model=VersionCompareOut)
def compare_ci_versions(
    id: uuid.UUID,
    from_version_id: uuid.UUID = Query(..., alias="from"),
    to_version_id: uuid.UUID = Query(..., alias="to"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ci = db.query(ConfigurationItem).filter(ConfigurationItem.id == id).first()
    if not ci:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Configuration Item not found")
    get_team_with_access(ci.team_id, current_user, db)

    v_from = db.query(CIVersion).filter(CIVersion.id == from_version_id, CIVersion.ci_id == ci.id).first()
    v_to = db.query(CIVersion).filter(CIVersion.id == to_version_id, CIVersion.ci_id == ci.id).first()
    if not v_from or not v_to:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or both versions not found for this CI.")

    diff_data = generate_version_diff(v_from, v_to)
    return VersionCompareOut(**diff_data)


# --- Rollback ---

@router.post("/cis/{id}/rollback", response_model=CIVersionOut, status_code=status.HTTP_201_CREATED)
def rollback_ci_version(
    id: uuid.UUID,
    payload: RollbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ci = db.query(ConfigurationItem).filter(ConfigurationItem.id == id).first()
    if not ci:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Configuration Item not found")
    team = get_team_with_access(ci.team_id, current_user, db)

    # Rule 19 & 22: Locking check
    validate_ci_modification_allowed(db, ci, payload.change_request_id)

    target_version = db.query(CIVersion).filter(
        CIVersion.id == payload.target_version_id,
        CIVersion.ci_id == ci.id
    ).first()
    if not target_version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target version to rollback to not found.")

    latest_version = db.query(CIVersion).filter(CIVersion.ci_id == ci.id).order_by(CIVersion.major.desc(), CIVersion.minor.desc()).first()

    if payload.bump_type == "major":
        major = latest_version.major + 1
        minor = 0
    else:
        major = latest_version.major
        minor = latest_version.minor + 1

    version_label = f"{major}.{minor} (rollback to {target_version.version_label})"

    new_version = CIVersion(
        ci_id=ci.id,
        major=major,
        minor=minor,
        version_label=version_label,
        file_id=target_version.file_id,
        content_sha256=target_version.content_sha256,
        change_description=f"Rollback to v{target_version.version_label}: {payload.reason.strip()}",
        created_by=current_user.id,
        status="draft",
        kind="rollback",
        rollback_of_version_id=target_version.id,
        change_request_id=payload.change_request_id
    )
    db.add(new_version)
    db.flush()

    ci.current_version_id = new_version.id
    ci.status = "draft"
    ci.updated_at = datetime.now(timezone.utc)

    record_audit(
        db=db,
        action="VERSION_ROLLBACK",
        entity_type="ci_version",
        entity_id=new_version.id,
        actor=current_user,
        project_id=team.project_id,
        team_id=team.id,
        note=f"Rolled back {ci.ci_code} to v{target_version.version_label}. Reason: {payload.reason}"
    )
    db.commit()
    db.refresh(new_version)
    return _populate_ci_version_out(new_version)
