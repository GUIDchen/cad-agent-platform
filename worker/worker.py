"""CAD Agent Platform Worker.

Polls the API for queued jobs, generates DXF + PNG with the shared core,
and uploads the result. Runs on Windows (or any OS) with access to the API.
"""

import argparse
import os
import sys
import tempfile
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.bracket import build  # noqa: E402
from app.core.preview import render  # noqa: E402
from app.core.validate import validate  # noqa: E402

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")
WORKER_TOKEN = os.getenv("WORKER_TOKEN", "dev-worker")
POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", "2"))
HEADERS = {"X-Worker-Token": WORKER_TOKEN}


def run_once(client: httpx.Client) -> bool:
    resp = client.post(f"{API_BASE}/api/internal/jobs/claim", headers=HEADERS)
    resp.raise_for_status()
    job = resp.json().get("job_id")
    if not job:
        return False

    payload = resp.json()
    spec = dict(payload["payload"])
    spec["drawing_no"] = payload["drawing_no"]
    spec.setdefault("title", "安装板")

    with tempfile.TemporaryDirectory(prefix="cad-worker-") as tmp:
        tmp_path = Path(tmp)
        try:
            dxf = build(spec, tmp_path / "out.dxf")
            issues = validate(str(dxf), spec)
            if issues:
                raise ValueError("; ".join(issues))
            png = render(dxf, tmp_path / "out.png")
            with dxf.open("rb") as dxf_fh, png.open("rb") as png_fh:
                client.post(
                    f"{API_BASE}/api/internal/jobs/{job}/complete",
                    headers=HEADERS,
                    files={"dxf": ("out.dxf", dxf_fh), "png": ("out.png", png_fh)},
                ).raise_for_status()
        except Exception as exc:  # noqa: BLE001
            client.post(
                f"{API_BASE}/api/internal/jobs/{job}/fail",
                headers=HEADERS,
                json={"error": str(exc)},
            )
            print(f"[fail] {job}: {exc}")
        else:
            print(f"[done] {job}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="claim at most one job")
    args = parser.parse_args()

    with httpx.Client(timeout=120) as client:
        if args.once:
            run_once(client)
            return
        print(f"worker started, api={API_BASE}")
        while True:
            try:
                worked = run_once(client)
            except Exception as exc:  # noqa: BLE001
                print(f"[error] {exc}")
                worked = False
            if not worked:
                time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
