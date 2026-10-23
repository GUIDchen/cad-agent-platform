import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.dwg import convert  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("src")
    parser.add_argument("dst")
    args = parser.parse_args()
    print(convert(Path(args.src), Path(args.dst)))
