import argparse
import os
import shutil
import sys


def collect_checks() -> list[dict]:
    checks: list[dict] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": ok, "detail": detail})

    oda = os.getenv("ODA_FILE_CONVERTER", "")
    dwg_bin = os.getenv("DWG2DXF_BIN", "")
    add("DWG 转换", bool(oda or dwg_bin or shutil.which("dwg2dxf")), oda or dwg_bin or "未配置")

    add("SolidWorks 适配器", bool(os.getenv("CAD_ADAPTER_SOLIDWORKS")), os.getenv("CAD_ADAPTER_SOLIDWORKS", "未配置"))
    add("Altium 适配器", bool(os.getenv("CAD_ADAPTER_ALTIUM")), os.getenv("CAD_ADAPTER_ALTIUM", "未配置"))

    add(
        "ComfyUI",
        bool(os.getenv("COMFY_URL") and os.getenv("COMFY_WORKFLOW")),
        os.getenv("COMFY_URL", "未配置"),
    )
    add(
        "LLM",
        bool(os.getenv("LLM_BASE_URL") and os.getenv("LLM_API_KEY")),
        os.getenv("LLM_BASE_URL", "未配置"),
    )
    add("ERP", bool(os.getenv("ERP_WEBHOOK_URL")), os.getenv("ERP_WEBHOOK_URL", "未配置"))
    add(
        "企业微信",
        os.getenv("WECOM_MODE") == "real" and bool(os.getenv("WECOM_TOKEN")) and bool(os.getenv("WECOM_ENCODING_AES_KEY")),
        os.getenv("WECOM_MODE", "mock"),
    )
    add(
        "S3/MinIO",
        os.getenv("STORAGE_BACKEND") == "s3" and bool(os.getenv("S3_BUCKET")),
        os.getenv("STORAGE_BACKEND", "local"),
    )
    clam = os.getenv("CLAMAV_COMMAND", "clamdscan")
    add(
        "ClamAV",
        os.getenv("VIRUS_SCAN_MODE") == "command" and bool(shutil.which(clam)),
        clam,
    )
    return checks


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    checks = collect_checks()
    for item in checks:
        mark = "OK  " if item["ok"] else "MISS"
        print(f"[{mark}] {item['name']}: {item['detail']}")

    missing = [item for item in checks if not item["ok"]]
    print(f"\n{len(checks) - len(missing)}/{len(checks)} 已配置")
    if args.strict and missing:
        sys.exit(1)
