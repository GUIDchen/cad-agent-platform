from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..audit import write_audit
from ..models import Approval, Drawing, User, Version
from ..notifications import notify_user
from ..notify import notify_approval


def _current_drawing(db: Session, version: Version) -> Drawing:
    drawing = db.get(Drawing, version.drawing_id)
    if not drawing or drawing.current_version_id != version.id:
        raise HTTPException(status_code=400, detail={"code": "STALE", "message": "只能审批当前版本"})
    return drawing


def approve_version(db: Session, version: Version, user: User, comment: str = "") -> Version:
    drawing = _current_drawing(db, version)
    db.add(Approval(version_id=version.id, reviewer_id=user.id, status="approved", comment=comment))
    drawing.status = "approved"
    write_audit(db, user.id, "version.approve", "drawing", drawing.drawing_no, {"version": version.version})
    notify_user(
        db, version.created_by, "approval",
        f"{drawing.drawing_no} v{version.version} 已通过",
        f"/drawings/{drawing.id}",
    )
    db.commit()
    notify_approval(drawing.drawing_no, version.version, "approved")
    return version


def reject_version(db: Session, version: Version, user: User, comment: str) -> Version:
    drawing = _current_drawing(db, version)
    db.add(Approval(version_id=version.id, reviewer_id=user.id, status="rejected", comment=comment))
    drawing.status = "rejected"
    write_audit(
        db, user.id, "version.reject", "drawing", drawing.drawing_no,
        {"version": version.version, "comment": comment},
    )
    notify_user(
        db, version.created_by, "approval",
        f"{drawing.drawing_no} v{version.version} 已驳回",
        f"/drawings/{drawing.id}",
        comment,
    )
    db.commit()
    notify_approval(drawing.drawing_no, version.version, "rejected")
    return version
