import uuid
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.scm import ConfigurationItem
from app.models.change_request import ChangeRequest, ChangeRequestItem


def validate_ci_modification_allowed(
    db: Session,
    ci: ConfigurationItem,
    change_request_id: Optional[uuid.UUID] = None
) -> Tuple[bool, Optional[ChangeRequest]]:
    """
    Checks if a CI can have a new version or rollback created.
    If CI is locked:
      - Requires an unclosed change request that is in 'approved' or 'implemented' status.
      - The change request must list this CI.
      - If change_request_id is not provided or invalid, raises 400.
    """
    if not ci.is_locked:
        return True, None

    if not change_request_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Configuration Item '{ci.ci_code}' is locked under a baseline. Modifying it requires an approved or implemented Change Request."
        )

    cr = db.query(ChangeRequest).filter(
        ChangeRequest.id == change_request_id,
        ChangeRequest.team_id == ci.team_id
    ).first()

    if not cr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Change request not found for this team."
        )

    if cr.status not in ["approved", "implemented"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Change Request '{cr.cr_code}' is in status '{cr.status}'. Only 'approved' or 'implemented' change requests allow modifying locked CIs."
        )

    # Check if cr lists this CI
    item_match = db.query(ChangeRequestItem).filter(
        ChangeRequestItem.cr_id == cr.id,
        ChangeRequestItem.ci_id == ci.id
    ).first()

    if not item_match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Change Request '{cr.cr_code}' does not include Configuration Item '{ci.ci_code}'."
        )

    return True, cr
