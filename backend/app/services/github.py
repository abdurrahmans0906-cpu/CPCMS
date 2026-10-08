import re
from datetime import datetime, timezone
from typing import Tuple, Optional, List, Dict, Any
import httpx
from sqlalchemy.orm import Session
from app.config import settings
from app.models.git import Repository, Branch, Commit
from app.models.project import Project


def parse_github_url(url: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parses owner and repo name from GitHub URL.
    Supports formats:
    - https://github.com/owner/repo
    - https://github.com/owner/repo.git
    - git@github.com:owner/repo.git
    """
    url = url.strip()
    match = re.search(r"github\.com[:/]([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)", url)
    if match:
        owner = match.group(1)
        repo = match.group(2)
        if repo.endswith(".git"):
            repo = repo[:-4]
        return owner, repo
    return None, None


def is_gitflow_lite_branch(branch_name: str) -> bool:
    """
    GitFlow Lite policy:
    Allowed branches: main, master, develop, feature/*, release/*, hotfix/*
    """
    name = branch_name.strip()
    if name in ["main", "master", "develop"]:
        return True
    if name.startswith("feature/") or name.startswith("release/") or name.startswith("hotfix/"):
        return True
    return False


async def sync_github_repository(db: Session, repo: Repository, project: Project) -> Tuple[bool, Optional[str]]:
    owner = repo.owner
    name = repo.name

    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "CPCMS-Sync/1.0"
    }
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            # 1. Fetch Repo info to get default branch
            repo_res = await client.get(f"https://api.github.com/repos/{owner}/{name}", headers=headers)
            if repo_res.status_code == 404:
                err = f"Repository '{owner}/{name}' not found. Please verify the URL or ensure it is public."
                repo.last_sync_error = err
                repo.last_synced_at = datetime.now(timezone.utc)
                db.flush()
                return False, err
            elif repo_res.status_code == 403:
                err = "GitHub API rate limit exceeded or access forbidden. Check GITHUB_TOKEN."
                repo.last_sync_error = err
                repo.last_synced_at = datetime.now(timezone.utc)
                db.flush()
                return False, err
            elif repo_res.status_code != 200:
                err = f"GitHub API returned HTTP {repo_res.status_code}: {repo_res.text[:200]}"
                repo.last_sync_error = err
                repo.last_synced_at = datetime.now(timezone.utc)
                db.flush()
                return False, err

            repo_data = repo_res.json()
            repo.default_branch = repo_data.get("default_branch", "main")

            # 2. Fetch Branches
            branches_res = await client.get(f"https://api.github.com/repos/{owner}/{name}/branches?per_page=50", headers=headers)
            if branches_res.status_code == 200:
                branches_data = branches_res.json()
                # Clear existing branches or update
                db.query(Branch).filter(Branch.repo_id == repo.id).delete()
                for b in branches_data:
                    b_name = b["name"]
                    commit_sha = b["commit"]["sha"]
                    follows = True
                    if project.branching_policy == "gitflow_lite":
                        follows = is_gitflow_lite_branch(b_name)

                    branch_obj = Branch(
                        repo_id=repo.id,
                        name=b_name,
                        head_sha=commit_sha,
                        follows_policy=follows
                    )
                    db.add(branch_obj)

            # 3. Fetch Recent Commits (up to 30)
            commits_res = await client.get(f"https://api.github.com/repos/{owner}/{name}/commits?per_page=30", headers=headers)
            if commits_res.status_code == 200:
                commits_data = commits_res.json()
                db.query(Commit).filter(Commit.repo_id == repo.id).delete()
                for c in commits_data:
                    sha = c["sha"]
                    c_info = c.get("commit", {})
                    author_info = c_info.get("author", {})
                    author_login = c.get("author", {}).get("login") if c.get("author") else None
                    author_name = author_info.get("name", "Unknown")
                    message = c_info.get("message", "")
                    date_str = author_info.get("date")

                    try:
                        committed_at = datetime.fromisoformat(date_str.replace("Z", "+00:00")) if date_str else datetime.now(timezone.utc)
                    except Exception:
                        committed_at = datetime.now(timezone.utc)

                    commit_obj = Commit(
                        repo_id=repo.id,
                        sha=sha,
                        branch=repo.default_branch,
                        author_name=author_name,
                        author_login=author_login,
                        message=message,
                        committed_at=committed_at
                    )
                    db.add(commit_obj)

            repo.last_synced_at = datetime.now(timezone.utc)
            repo.last_sync_error = None
            db.flush()
            return True, None

        except httpx.RequestError as exc:
            err = f"Network error communicating with GitHub: {str(exc)}"
            repo.last_sync_error = err
            repo.last_synced_at = datetime.now(timezone.utc)
            db.flush()
            return False, err
        except Exception as exc:
            err = f"Unexpected error during sync: {str(exc)}"
            repo.last_sync_error = err
            repo.last_synced_at = datetime.now(timezone.utc)
            db.flush()
            return False, err
