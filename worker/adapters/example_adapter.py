import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.bracket import build  # noqa: E402
from app.core.preview import render  # noqa: E402


def main() -> None:
    spec = json.load(sys.stdin)
    spec.setdefault("holes", [{"x": 20, "y": 20, "d": 6.6}])
    dxf = build(spec, Path("out.dxf"))
    render(dxf, Path("out.png"))
    print(json.dumps({"ok": True, "dxf": str(dxf), "png": "out.png"}))


if __name__ == "__main__":
    main()
