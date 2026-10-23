import xml.etree.ElementTree as ET

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import WECOM_ACTION_TOKEN, WECOM_CORP_ID, WECOM_ENCODING_AES_KEY, WECOM_TOKEN
from ..db import get_db
from ..models import User, Version
from ..permissions import require_drawing
from ..replay import seen_before
from ..schemas import WecomActionIn
from ..wecom_crypto import decrypt, verify_signature
from .versions import approve_version, reject_version

router = APIRouter(tags=["wecom"])


def _check(token: str | None) -> None:
    if token != WECOM_ACTION_TOKEN:
        raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "message": "回调令牌错误"})


@router.get("/wecom/verify")
def wecom_verify(
    signature: str,
    timestamp: str,
    nonce: str,
    echostr: str,
):
    if not WECOM_TOKEN or not WECOM_ENCODING_AES_KEY:
        raise HTTPException(status_code=500, detail={"code": "WECOM_CONFIG", "message": "回调 token/key 未配置"})
    if not verify_signature(WECOM_TOKEN, timestamp, nonce, echostr, signature):
        raise HTTPException(status_code=403, detail={"code": "BAD_SIGNATURE", "message": "签名校验失败"})
    try:
        return PlainTextResponse(decrypt(WECOM_ENCODING_AES_KEY, echostr, WECOM_CORP_ID))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"code": "BAD_ENCRYPT", "message": str(exc)}) from exc


@router.post("/wecom/event")
async def wecom_event(
    request: Request,
    msg_signature: str,
    timestamp: str,
    nonce: str,
    db: Session = Depends(get_db),
):
    if not WECOM_TOKEN or not WECOM_ENCODING_AES_KEY:
        raise HTTPException(status_code=500, detail={"code": "WECOM_CONFIG", "message": "回调 token/key 未配置"})

    raw = (await request.body()).decode("utf-8")
    try:
        outer = ET.fromstring(raw)
        encrypted = outer.findtext("Encrypt") or ""
    except ET.ParseError as exc:
        raise HTTPException(status_code=400, detail={"code": "BAD_XML", "message": "报文非法"}) from exc

    if not verify_signature(WECOM_TOKEN, timestamp, nonce, encrypted, msg_signature):
        raise HTTPException(status_code=403, detail={"code": "BAD_SIGNATURE", "message": "签名校验失败"})

    if seen_before(f"{timestamp}:{nonce}"):
        return PlainTextResponse("success")

    try:
        inner_xml = decrypt(WECOM_ENCODING_AES_KEY, encrypted, WECOM_CORP_ID)
        inner = ET.fromstring(inner_xml)
    except (ValueError, ET.ParseError):
        return PlainTextResponse("success")

    event = (inner.findtext("Event") or "").strip()
    event_key = (inner.findtext("EventKey") or "").strip()
    from_user = (inner.findtext("FromUserName") or "").strip()

    if event in ("template_card_event", "click") and ":" in event_key:
        action, version_id = event_key.split(":", 1)
        if action in ("approve", "reject") and version_id.isdigit():
            user = db.scalar(select(User).where(User.name == from_user, User.active.is_(True)))
            version = db.get(Version, int(version_id))
            if user and version:
                try:
                    require_drawing(db, user, version.drawing_id)
                except HTTPException:
                    return PlainTextResponse("success")
                if action == "approve":
                    approve_version(db, version, user, "企业微信卡片通过")
                else:
                    reject_version(db, version, user, "企业微信卡片驳回")

    return PlainTextResponse("success")


@router.post("/wecom/action")
def wecom_action(
    body: WecomActionIn,
    db: Session = Depends(get_db),
    x_wecom_token: str | None = Header(default=None, alias="X-Wecom-Token"),
):
    _check(x_wecom_token)
    version = db.get(Version, body.version_id)
    if not version:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "版本不存在"})

    if body.reviewer_id:
        user = db.get(User, body.reviewer_id)
    else:
        user = db.scalar(
            select(User)
            .where(User.role == "reviewer", User.active.is_(True))
            .order_by(User.id)
            .limit(1)
        )
    if not user or user.role not in ("admin", "reviewer"):
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "没有审批人"})

    require_drawing(db, user, version.drawing_id)

    if body.action == "approve":
        approve_version(db, version, user, body.comment)
    else:
        reject_version(db, version, user, body.comment or "企业微信卡片驳回")
    return {"ok": True, "action": body.action, "version_id": version.id}
