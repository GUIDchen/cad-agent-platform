from datetime import datetime

from app.audit_cleanup import cleanup_before
from app.db import SessionLocal
from app.models import AuditLog


def test_cleanup_old_audit_rows():
    db = SessionLocal()
    old = AuditLog(
        actor_id=None,
        action="test.cleanup",
        object_type="test",
        object_id="old",
        detail_json="{}",
        created_at=datetime(2000, 1, 1),
    )
    db.add(old)
    db.commit()
    db.refresh(old)

    cutoff = datetime(2001, 1, 1)
    assert cleanup_before(db, cutoff, dry_run=True) >= 1
    assert db.get(AuditLog, old.id) is not None

    assert cleanup_before(db, cutoff) >= 1
    assert db.get(AuditLog, old.id) is None
    db.close()
