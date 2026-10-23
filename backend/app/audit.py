import json

from sqlalchemy.orm import Session

from .context import request_ip
from .models import AuditLog


def write_audit(
    db: Session,
    actor_id: int | None,
    action: str,
    object_type: str,
    object_id: str,
    detail: dict | None = None,
    ip: str | None = None,
) -> None:
    db.add(
        AuditLog(
            actor_id=actor_id,
            action=action,
            object_type=object_type,
            object_id=str(object_id),
            detail_json=json.dumps(detail or {}, ensure_ascii=False),
            ip=ip or request_ip.get(),
        )
    )
