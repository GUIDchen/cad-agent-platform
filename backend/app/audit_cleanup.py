from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from .models import AuditLog


def cleanup_before(db: Session, cutoff: datetime, dry_run: bool = False) -> int:
    count = db.scalar(
        select(func.count()).select_from(AuditLog).where(AuditLog.created_at < cutoff)
    ) or 0
    if count and not dry_run:
        db.execute(delete(AuditLog).where(AuditLog.created_at < cutoff))
        db.commit()
    return int(count)
