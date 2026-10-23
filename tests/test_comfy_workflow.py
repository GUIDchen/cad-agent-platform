import json
from pathlib import Path

from tools.comfy_workflow_check import check_workflow

ROOT = Path(__file__).resolve().parents[1]


def test_example_workflow_valid():
    report = check_workflow(ROOT / "deploy" / "comfy" / "workflow.example.json")
    assert report["ok"] is True
    assert report["errors"] == []


def test_missing_placeholder(tmp_path: Path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"1": {"class_type": "SaveImage", "inputs": {}}}), encoding="utf-8")
    report = check_workflow(path)
    assert report["ok"] is False
    assert any("PROMPT" in error for error in report["errors"])
