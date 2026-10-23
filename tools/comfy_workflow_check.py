import argparse
import json
from pathlib import Path


def check_workflow(path: Path) -> dict:
    errors: list[str] = []
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "errors": [f"JSON 无法读取: {exc}"], "nodes": 0}

    if not isinstance(data, dict) or not data:
        return {"ok": False, "errors": ["工作流必须是非空对象"], "nodes": 0}

    text = json.dumps(data, ensure_ascii=False)
    for placeholder in ("{{PROMPT}}", "{{NEGATIVE}}", "{{WIDTH}}", "{{HEIGHT}}", "{{SEED}}"):
        if placeholder not in text:
            errors.append(f"缺少占位符 {placeholder}")

    class_types = [node.get("class_type", "") for node in data.values() if isinstance(node, dict)]
    if "SaveImage" not in class_types:
        errors.append("缺少 SaveImage 节点")
    if "KSampler" not in class_types:
        errors.append("缺少 KSampler 节点")
    if "CheckpointLoaderSimple" not in class_types:
        errors.append("缺少 CheckpointLoaderSimple 节点")

    return {"ok": not errors, "errors": errors, "nodes": len(data)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()
    report = check_workflow(Path(args.path))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["ok"] else 1)
