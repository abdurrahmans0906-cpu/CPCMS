import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union
from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.models.user import User


def _serialize_value(val: Any) -> Any:
    if isinstance(val, (datetime,)):
        return val.isoformat()
    if isinstance(val, (uuid.UUID,)):
        return str(val)
    if isinstance(val, dict):
        return {k: _serialize_value(v) for k, v in val.items()}
    if isinstance(val, list):
        return [_serialize_value(v) for v in val]
    return val


def record_audit(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: Union[str, uuid.UUID],
    actor: Optional[User] = None,
    project_id: Optional[uuid.UUID] = None,
    team_id: Optional[uuid.UUID] = None,
    before: Optional[Dict[str, Any]] = None,
    after: Optional[Dict[str, Any]] = None,
    note: Optional[str] = None
) -> AuditLog:
    clean_before = _serialize_value(before) if before else None
    clean_after = _serialize_value(after) if after else None

    actor_id = actor.id if actor else None
    actor_role = actor.role if actor else "SYSTEM"

    audit_entry = AuditLog(
        at=datetime.now(timezone.utc),
        actor_user_id=actor_id,
        actor_role=actor_role,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        project_id=project_id,
        team_id=team_id,
        before=clean_before,
        after=clean_after,
        note=note
    )
    db.add(audit_entry)
    db.flush()
    return audit_entry
