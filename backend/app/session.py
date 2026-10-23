import base64
import hashlib
import hmac
import json
import time

from .config import SECRET_KEY, SESSION_MAX_AGE


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _unb64(text: str) -> bytes:
    padding = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + padding)


def sign_session(user_id: int) -> str:
    body = {"uid": int(user_id), "exp": int(time.time()) + SESSION_MAX_AGE}
    raw = _b64(json.dumps(body, separators=(",", ":")).encode())
    sig = hmac.new(SECRET_KEY.encode(), raw.encode(), hashlib.sha256).hexdigest()[:32]
    return f"{raw}.{sig}"


def verify_session(token: str) -> int | None:
    try:
        raw, sig = token.split(".", 1)
        expected = hmac.new(SECRET_KEY.encode(), raw.encode(), hashlib.sha256).hexdigest()[:32]
        if not hmac.compare_digest(sig, expected):
            return None
        body = json.loads(_unb64(raw))
        if int(body.get("exp", 0)) < int(time.time()):
            return None
        return int(body["uid"])
    except Exception:  # noqa: BLE001
        return None
