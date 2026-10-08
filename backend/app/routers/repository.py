import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.user import User
from app.models.git import Repository, Branch, Commit
from app.schemas.git import RepositoryCreate, RepositoryOut, BranchOut, CommitOut
from app.permissions import get_current_user, get_team_with_access
from app.services.github import parse_github_url, sync_github_repository
from app.services.audit import record_audit

router = APIRouter(tags=["Repository"])


def _populate_repo_out(repo: Repository, db: Session) -> RepositoryOut:
    branches = db.query(Branch).filter(Branch.repo_id == repo.id).order_by(Branch.name).all()
    commits = db.query(Commit).filter(Commit.repo_id == repo.id).order_by(Commit.committed_at.desc()).limit(30).all()

    return RepositoryOut(
        id=repo.id,
        team_id=repo.team_id,
        url=repo.url,
        owner=repo.owner,
        name=repo.name,
        default_branch=repo.default_branch,
        last_synced_at=repo.last_synced_at,
        last_sync_error=repo.last_sync_error,
        branches=[BranchOut.model_validate(b) for b in branches],
        commits=[CommitOut.model_validate(c) for c in commits],
        created_at=repo.created_at
    )


@router.get("/teams/{team_id}/repository", response_model=RepositoryOut)
def get_team_repository(
    team_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = get_team_with_access(team_id, current_user, db)
    repo = db.query(Repository).filter(Repository.team_id == team.id).first()
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No GitHub repository linked to this team.")
    return _populate_repo_out(repo, db)


@router.put("/teams/{team_id}/repository", response_model=RepositoryOut)
async def set_team_repository(
    team_id: uuid.UUID,
    payload: RepositoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = get_team_with_access(team_id, current_user, db)
    owner, name = parse_github_url(payload.url)
    if not owner or not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid GitHub repository URL. Expected format: https://github.com/owner/repository"
        )

    repo = db.query(Repository).filter(Repository.team_id == team.id).first()
    if not repo:
        repo = Repository(
            team_id=team.id,
            url=payload.url.strip(),
            owner=owner,
            name=name
        )
        db.add(repo)
        db.flush()
    else:
        repo.url = payload.url.strip()
        repo.owner = owner
        repo.name = name

    # Run initial sync
    await sync_github_repository(db, repo, team.project)

    record_audit(
        db=db,
        action="REPO_LINKED",
        entity_type="repository",
        entity_id=repo.id,
        actor=current_user,
        project_id=team.project_id,
        team_id=team.id,
        note=f"Linked GitHub repo: {owner}/{name}"
    )
    db.commit()
    db.refresh(repo)
    return _populate_repo_out(repo, db)


@router.post("/teams/{team_id}/repository/sync", response_model=RepositoryOut)
async def sync_repository_now(
    team_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = get_team_with_access(team_id, current_user, db)
    repo = db.query(Repository).filter(Repository.team_id == team.id).first()
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No repository linked to this team.")

    success, error = await sync_github_repository(db, repo, team.project)
    db.commit()
    db.refresh(repo)
    return _populate_repo_out(repo, db)


@router.get("/teams/{team_id}/repository/branches", response_model=List[BranchOut])
def get_branches(
    team_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = get_team_with_access(team_id, current_user, db)
    repo = db.query(Repository).filter(Repository.team_id == team.id).first()
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No repository linked.")
    branches = db.query(Branch).filter(Branch.repo_id == repo.id).order_by(Branch.name).all()
    return [BranchOut.model_validate(b) for b in branches]


@router.get("/teams/{team_id}/repository/commits", response_model=List[CommitOut])
def get_commits(
    team_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    team = get_team_with_access(team_id, current_user, db)
    repo = db.query(Repository).filter(Repository.team_id == team.id).first()
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No repository linked.")
    commits = db.query(Commit).filter(Commit.repo_id == repo.id).order_by(Commit.committed_at.desc()).limit(50).all()
    return [CommitOut.model_validate(c) for c in commits]
