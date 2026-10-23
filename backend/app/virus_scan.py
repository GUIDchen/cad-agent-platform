import os
import subprocess


class VirusFound(Exception):
    pass


def scan_bytes(data: bytes) -> None:
    mode = os.getenv("VIRUS_SCAN_MODE", "mock").lower()
    if mode == "mock":
        if b"EICAR" in data:
            raise VirusFound("EICAR 测试病毒")
        return

    command = os.getenv("CLAMAV_COMMAND", "clamdscan")
    try:
        result = subprocess.run(
            [command, "--no-summary", "-"],
            input=data,
            capture_output=True,
            timeout=30,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"未找到病毒扫描命令: {command}") from exc
    if result.returncode == 1:
        raise VirusFound(result.stdout.decode("utf-8", errors="ignore")[:200])
    if result.returncode not in (0, 1):
        raise RuntimeError("病毒扫描失败")
