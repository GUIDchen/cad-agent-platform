from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db import get_db
from ..models import Notification, User
from ..schemas import NotificationOut

router = APIRouter(tags=["notifications"])


@router.get("/notifications", response_model=list[NotificationOut])
def list_notifications(
    unread_only: bool = False,
    limit: int = 30,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        stmt = stmt.where(Notification.read.is_(False))
    stmt = stmt.order_by(Notification.created_at.desc()).limit(min(max(limit, 1), 100))
    return list(db.scalars(stmt))


@router.get("/notifications/unread-count")
def unread_count(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    count = db.scalar(
        select(func.count()).select_from(Notification).where(
            Notification.user_id == user.id,
            Notification.read.is_(False),
        )
    )
    return {"count": int(count or 0)}


@router.post("/notifications/read-all")
def read_all(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = list(db.scalars(select(Notification).where(Notification.user_id == user.id, Notification.read.is_(False))))
    for row in rows:
        row.read = True
    db.commit()
    return {"updated": len(rows)}


@router.post("/notifications/{notification_id}/read", response_model=NotificationOut)
def mark_read(notification_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.get(Notification, notification_id)
    if not row or row.user_id != user.id:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "通知不存在"})
    row.read = True
    db.commit()
    db.refresh(row)
    return row
