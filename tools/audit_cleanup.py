import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.audit_cleanup import cleanup_before  # noqa: E402
from app.db import SessionLocal  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=180)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cutoff = datetime.utcnow() - timedelta(days=args.days)
    db = SessionLocal()
    try:
        count = cleanup_before(db, cutoff, dry_run=args.dry_run)
        print(f"cutoff={cutoff.isoformat()} matched={count} dry_run={args.dry_run}")
    finally:
        db.close()
