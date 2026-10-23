import hashlib
import hmac
import time
from urllib.parse import quote

import httpx

from .config import SECRET_KEY, WECOM_CORP_ID, WECOM_REDIRECT_URI, WECOM_SECRET


def make_state() -> str:
    ts = str(int(time.time()))
    sig = hmac.new(SECRET_KEY.encode(), ts.encode(), hashlib.sha256).hexdigest()[:16]
    return f"{ts}.{sig}"


def verify_state(state: str) -> bool:
    try:
        ts, sig = state.split(".", 1)
        expected = hmac.new(SECRET_KEY.encode(), ts.encode(), hashlib.sha256).hexdigest()[:16]
        return hmac.compare_digest(sig, expected) and int(time.time()) - int(ts) < 600
    except Exception:  # noqa: BLE001
        return False


def authorize_url(state: str) -> str:
    if not WECOM_CORP_ID:
        raise RuntimeError("WECOM_CORP_ID 未配置")
    redirect = quote(WECOM_REDIRECT_URI, safe="")
    return (
        "https://open.weixin.qq.com/connect/oauth2/authorize"
        f"?appid={WECOM_CORP_ID}&redirect_uri={redirect}"
        f"&response_type=code&scope=snsapi_base&state={state}#wechat_redirect"
    )


def exchange_code(code: str) -> str:
    if not WECOM_CORP_ID or not WECOM_SECRET:
        raise RuntimeError("企业微信 corp_id/secret 未配置")
    with httpx.Client(timeout=10) as client:
        token_resp = client.get(
            "https://qyapi.weixin.qq.com/cgi-bin/gettoken",
            params={"corpid": WECOM_CORP_ID, "corpsecret": WECOM_SECRET},
        ).json()
        if token_resp.get("errcode") != 0:
            raise RuntimeError(f"gettoken 失败: {token_resp}")
        access_token = token_resp["access_token"]
        info = client.get(
            "https://qyapi.weixin.qq.com/cgi-bin/auth/getuserinfo",
            params={"access_token": access_token, "code": code},
        ).json()
        if info.get("errcode") != 0 or not info.get("userid"):
            raise RuntimeError(f"getuserinfo 失败: {info}")
        return str(info["userid"])
