import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.bracket import build  # noqa: E402
from app.core.preview import render  # noqa: E402

spec = json.load(sys.stdin)
dxf = build(spec, "out.dxf")
render(dxf, "out.png")
