import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.notify import retry_dead_letters  # noqa: E402

if __name__ == "__main__":
    ok, fail = retry_dead_letters()
    print(f"retried ok={ok} fail={fail}")
