import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.config import STORAGE_BACKEND  # noqa: E402
from app.storage import get_storage  # noqa: E402

if __name__ == "__main__":
    store = get_storage()
    ok = store.health()
    print(f"storage={STORAGE_BACKEND} type={type(store).__name__} healthy={ok}")
    raise SystemExit(0 if ok else 1)
