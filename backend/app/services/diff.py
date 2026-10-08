import difflib
import os
from typing import Dict, Any, List, Optional
from app.models.scm import CIVersion

TEXT_EXTENSIONS = {
    "md", "txt", "py", "ts", "js", "java", "sql", "json",
    "csv", "yml", "yaml", "html", "css", "xml", "sh", "c", "cpp", "h"
}


def is_text_file(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in TEXT_EXTENSIONS


def get_file_content_lines(filepath: Optional[str]) -> List[str]:
    if not filepath or not os.path.exists(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.readlines()
    except Exception:
        return []


def generate_version_diff(v_from: CIVersion, v_to: CIVersion) -> Dict[str, Any]:
    file_from = v_from.file
    file_to = v_to.file

    meta_from = {
        "version_id": str(v_from.id),
        "version_label": v_from.version_label,
        "major": v_from.major,
        "minor": v_from.minor,
        "size_bytes": file_from.size_bytes if file_from else 0,
        "sha256": v_from.content_sha256,
        "author": v_from.creator.name if v_from.creator else "Unknown",
        "date": v_from.created_at.isoformat() if v_from.created_at else None,
        "description": v_from.change_description,
        "commit_sha": v_from.commit_sha,
        "original_name": file_from.original_name if file_from else "No file",
    }

    meta_to = {
        "version_id": str(v_to.id),
        "version_label": v_to.version_label,
        "major": v_to.major,
        "minor": v_to.minor,
        "size_bytes": file_to.size_bytes if file_to else 0,
        "sha256": v_to.content_sha256,
        "author": v_to.creator.name if v_to.creator else "Unknown",
        "date": v_to.created_at.isoformat() if v_to.created_at else None,
        "description": v_to.change_description,
        "commit_sha": v_to.commit_sha,
        "original_name": file_to.original_name if file_to else "No file",
    }

    name_from = file_from.original_name if file_from else "file_from"
    name_to = file_to.original_name if file_to else "file_to"

    is_text = is_text_file(name_from) and is_text_file(name_to)

    if not is_text or not file_from or not file_to:
        return {
            "from_metadata": meta_from,
            "to_metadata": meta_to,
            "is_text": False,
            "message": "Line diff is only available for text files (e.g. .md, .txt, .py, .ts, .json). Binary files provide metadata difference only.",
            "unified_diff": None,
            "added_count": 0,
            "removed_count": 0,
            "modified_count": 0
        }

    lines_from = get_file_content_lines(file_from.stored_path)
    lines_to = get_file_content_lines(file_to.stored_path)

    diff_lines = list(difflib.unified_diff(
        lines_from,
        lines_to,
        fromfile=f"v{v_from.version_label} ({name_from})",
        tofile=f"v{v_to.version_label} ({name_to})",
        lineterm=""
    ))

    added_count = 0
    removed_count = 0
    for line in diff_lines:
        if line.startswith("+") and not line.startswith("+++"):
            added_count += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed_count += 1

    return {
        "from_metadata": meta_from,
        "to_metadata": meta_to,
        "is_text": True,
        "message": None,
        "unified_diff": "\n".join(diff_lines),
        "added_count": added_count,
        "removed_count": removed_count,
        "modified_count": min(added_count, removed_count)
    }
