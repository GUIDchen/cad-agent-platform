from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import require_roles
from ..db import get_db
from ..models import Drawing, User, Version
from ..permissions import accessible_project_ids
from ..schemas import PendingApprovalOut

router = APIRouter(tags=["approvals"])


@router.get("/approvals/pending", response_model=list[PendingApprovalOut])
def pending_approvals(db: Session = Depends(get_db), user: User = Depends(require_roles("reviewer"))):
    stmt = (
        select(Version, Drawing)
        .join(Drawing, Version.drawing_id == Drawing.id)
        .where(Drawing.current_version_id == Version.id, Drawing.status == "pending_review")
        .order_by(Version.created_at.desc())
    )
    ids = accessible_project_ids(db, user)
    if ids is not None:
        stmt = stmt.where(Drawing.project_id.in_(ids)) if ids else stmt.where(Drawing.project_id == -1)

    return [
        {
            "version_id": version.id,
            "drawing_id": drawing.id,
            "drawing_no": drawing.drawing_no,
            "title": drawing.title,
            "version": version.version,
            "created_at": version.created_at,
        }
        for version, drawing in db.execute(stmt).all()
    ]
