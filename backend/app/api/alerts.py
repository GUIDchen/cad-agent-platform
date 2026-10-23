from fastapi import APIRouter, Header, HTTPException

from ..config import ALERT_WEBHOOK_TOKEN
from ..notify import send

router = APIRouter(tags=["alerts"])


@router.post("/alerts")
def alert_webhook(
    body: dict,
    x_alert_token: str | None = Header(default=None, alias="X-Alert-Token"),
):
    if x_alert_token != ALERT_WEBHOOK_TOKEN:
        raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "message": "告警令牌错误"})

    count = 0
    for alert in body.get("alerts", []) or []:
        labels = alert.get("labels", {}) or {}
        annotations = alert.get("annotations", {}) or {}
        name = labels.get("alertname", "unknown")
        severity = labels.get("severity", "")
        status = alert.get("status", "firing")
        summary = annotations.get("summary", "")
        prefix = "[告警恢复]" if status == "resolved" else "[告警]"
        send(f"{prefix} {name} ({severity}) {summary}")
        count += 1
    return {"ok": True, "count": count}
