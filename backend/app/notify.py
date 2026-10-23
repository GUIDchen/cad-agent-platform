import json
import os
from pathlib import Path

import httpx

from .config import DATA_DIR


def _log_path() -> Path:
    return Path(os.getenv("NOTIFY_LOG", DATA_DIR / "notifications.log"))


def _dead_path() -> Path:
    return Path(os.getenv("NOTIFY_DEAD_LETTER", DATA_DIR / "notify_dead.jsonl"))


def _deliver(payload: dict) -> bool:
    mode = os.getenv("NOTIFY_MODE", "mock").lower()
    if mode == "mock":
        text = payload.get("text") or json.dumps(payload, ensure_ascii=False)
        path = _log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(text.replace("\n", " ") + "\n")
        return True

    webhook = os.getenv("WECOM_WEBHOOK", "")
    if not webhook:
        return False
    try:
        if payload.get("msgtype") == "template_card":
            body = {"msgtype": "template_card", "template_card": payload["template_card"]}
        else:
            body = {"msgtype": "text", "text": {"content": payload.get("text", "")}}
        resp = httpx.post(webhook, json=body, timeout=3)
        return resp.status_code < 300
    except Exception:  # noqa: BLE001
        return False


def _dead_letter(payload: dict) -> None:
    path = _dead_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False) + "\n")


def send(text: str) -> bool:
    payload = {"msgtype": "text", "text": text}
    if _deliver(payload):
        return True
    _dead_letter(payload)
    return False


def send_card(card: dict) -> bool:
    payload = {"msgtype": "template_card", "template_card": card}
    if _deliver(payload):
        return True
    _dead_letter(payload)
    return False


def retry_dead_letters() -> tuple[int, int]:
    path = _dead_path()
    if not path.exists():
        return 0, 0
    ok = fail = 0
    remaining: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if _deliver(payload):
            ok += 1
        else:
            fail += 1
            remaining.append(line)
    path.write_text("\n".join(remaining) + ("\n" if remaining else ""), encoding="utf-8")
    return ok, fail


def notify_job_done(drawing_no: str, version: int) -> None:
    send(f"[生成完成] {drawing_no} v{version} 待审批")


def notify_job_failed(drawing_no: str, error: str) -> None:
    send(f"[生成失败] {drawing_no}: {error[:200]}")


def notify_approval(drawing_no: str, version: int, status: str) -> None:
    label = "通过" if status == "approved" else "驳回"
    send(f"[审批{label}] {drawing_no} v{version}")


def approval_card(drawing_no: str, version: int, version_id: int) -> dict:
    return {
        "card_type": "text_notice",
        "main_title": {"title": "图纸待审批", "desc": f"{drawing_no} v{version}"},
        "horizontal_content_list": [
            {"keyname": "图号", "value": drawing_no},
            {"keyname": "版本", "value": f"v{version}"},
        ],
        "task_id": f"approval-{version_id}",
        "button_list": [
            {"text": "通过", "style": 1, "key": f"approve:{version_id}"},
            {"text": "驳回", "style": 2, "key": f"reject:{version_id}"},
        ],
    }


def notify_approval_card(drawing_no: str, version: int, version_id: int) -> None:
    send_card(approval_card(drawing_no, version, version_id))
