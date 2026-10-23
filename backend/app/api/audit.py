import csv
import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import require_roles
from ..db import get_db
from ..models import AuditLog, User
from ..schemas import AuditOut

router = APIRouter(tags=["audit"])


def _parse_dt(value: str) -> datetime:
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"code": "BAD_TIME", "message": "时间格式应为 ISO8601"}) from exc
    if dt.tzinfo:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


@router.get("/audit")
def list_audit(
    object_id: str | None = None,
    action: str | None = None,
    actor_id: int | None = None,
    start: str | None = None,
    end: str | None = None,
    offset: int = 0,
    limit: int = 50,
    fmt: str = "json",
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    stmt = select(AuditLog)
    if object_id:
        stmt = stmt.where(AuditLog.object_id == object_id)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if actor_id:
        stmt = stmt.where(AuditLog.actor_id == actor_id)
    if start:
        stmt = stmt.where(AuditLog.created_at >= _parse_dt(start))
    if end:
        stmt = stmt.where(AuditLog.created_at <= _parse_dt(end))

    stmt = stmt.order_by(AuditLog.id.desc())
    size = min(max(limit, 1), 5000)

    if fmt == "csv":
        rows = list(db.scalars(stmt.limit(size)))
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["id", "actor_id", "action", "object_type", "object_id", "detail_json", "created_at"])
        for row in rows:
            writer.writerow(
                [
                    row.id,
                    row.actor_id or "",
                    row.action,
                    row.object_type,
                    row.object_id,
                    row.detail_json,
                    row.created_at.isoformat() if row.created_at else "",
                ]
            )
        return Response(
            content="\ufeff" + buffer.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="audit.csv"'},
        )

    rows = list(db.scalars(stmt.offset(max(offset, 0)).limit(min(size, 200))))
    return [AuditOut.model_validate(row).model_dump() for row in rows]
