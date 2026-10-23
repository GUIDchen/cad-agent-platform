import json
import os
import shlex
import subprocess
from pathlib import Path


def run_external(kind: str, spec: dict, work_dir: Path) -> tuple[Path, Path]:
    """Run an external CAD adapter command.

    The command reads a JSON spec from stdin and must write out.dxf / out.png
    into the working directory.
    """
    env_key = f"CAD_ADAPTER_{kind.upper()}"
    command = os.getenv(env_key)
    if not command:
        raise RuntimeError(f"{kind} 适配器未配置（{env_key}）")

    timeout = int(os.getenv("CAD_ADAPTER_TIMEOUT", "300"))
    proc = subprocess.run(
        shlex.split(command),
        input=json.dumps(spec, ensure_ascii=False),
        text=True,
        cwd=work_dir,
        capture_output=True,
        timeout=timeout,
    )
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "")[-500:]
        raise RuntimeError(f"{kind} 适配器失败（{proc.returncode}）: {tail}")

    dxf = work_dir / "out.dxf"
    png = work_dir / "out.png"
    if not dxf.exists() or not png.exists():
        raise RuntimeError(f"{kind} 适配器未生成 out.dxf/out.png")
    return dxf, png
