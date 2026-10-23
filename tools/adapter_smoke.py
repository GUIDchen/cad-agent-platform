import argparse
import json
import shlex
import subprocess
import tempfile
from pathlib import Path

SAMPLE = {
    "drawing_no": "SW-2026-001",
    "title": "安装板",
    "length": 180,
    "width": 120,
    "thickness": 6,
    "material": "304",
    "surface": "拉丝",
    "holes": [{"x": 20, "y": 20, "d": 6.6}],
}


def run_adapter(command: str, spec: dict | None = None, timeout: int = 60) -> dict:
    workdir = Path(tempfile.mkdtemp(prefix="adapter-smoke-"))
    proc = subprocess.run(
        shlex.split(command),
        input=json.dumps(spec or SAMPLE, ensure_ascii=False),
        text=True,
        cwd=workdir,
        capture_output=True,
        timeout=timeout,
    )
    dxf = workdir / "out.dxf"
    png = workdir / "out.png"
    dxf_ok = dxf.exists() and dxf.stat().st_size > 0 and b"SECTION" in dxf.read_bytes()[:4096]
    return {
        "ok": proc.returncode == 0 and dxf_ok,
        "workdir": str(workdir),
        "returncode": proc.returncode,
        "stdout": proc.stdout[-500:],
        "stderr": proc.stderr[-1000:],
        "out_dxf": dxf.exists(),
        "out_png": png.exists(),
        "dxf_has_section": dxf_ok,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--command", required=True)
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args()
    report = run_adapter(args.command, timeout=args.timeout)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["ok"] else 1)
