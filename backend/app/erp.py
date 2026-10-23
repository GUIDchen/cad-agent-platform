import json
from datetime import datetime, timezone

import httpx

from .config import DATA_DIR, ERP_WEBHOOK_TOKEN, ERP_WEBHOOK_URL


def push_bom(drawing_no: str, version: int, csv_text: str) -> dict:
    payload = {"drawing_no": drawing_no, "version": version, "bom_csv": csv_text}
    if ERP_WEBHOOK_URL:
        response = httpx.post(
            ERP_WEBHOOK_URL,
            headers={"Authorization": f"Bearer {ERP_WEBHOOK_TOKEN}"} if ERP_WEBHOOK_TOKEN else {},
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        return {"mode": "webhook", "status": response.status_code}

    outbox = DATA_DIR / "erp_outbox.jsonl"
    outbox.parent.mkdir(parents=True, exist_ok=True)
    record = {**payload, "created_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat()}
    with outbox.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return {"mode": "mock", "file": str(outbox)}
