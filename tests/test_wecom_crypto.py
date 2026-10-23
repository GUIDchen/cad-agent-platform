import pytest

from app import wecom_crypto
from app.api import wecom as wecom_api

KEY = "A" * 43
CORP = "corp"


def test_roundtrip():
    encrypted = wecom_crypto.encrypt(KEY, "hello-wecom", CORP, random16=b"0" * 16)
    assert wecom_crypto.decrypt(KEY, encrypted, CORP) == "hello-wecom"


def test_wrong_receive_id():
    encrypted = wecom_crypto.encrypt(KEY, "hello", CORP, random16=b"1" * 16)
    with pytest.raises(ValueError):
        wecom_crypto.decrypt(KEY, encrypted, "other")


def test_signature():
    sig = wecom_crypto.signature("tok", "1700000000", "nonce", "abc")
    assert wecom_crypto.verify_signature("tok", "1700000000", "nonce", "abc", sig)
    assert not wecom_crypto.verify_signature("tok", "1700000000", "nonce", "abc", "bad")


def test_verify_endpoint(client, monkeypatch):
    monkeypatch.setattr(wecom_api, "WECOM_TOKEN", "tok")
    monkeypatch.setattr(wecom_api, "WECOM_ENCODING_AES_KEY", KEY)
    monkeypatch.setattr(wecom_api, "WECOM_CORP_ID", CORP)

    echo = wecom_crypto.encrypt(KEY, "12345", CORP)
    ts = "1700000000"
    nonce = "n"
    sig = wecom_crypto.signature("tok", ts, nonce, echo)
    resp = client.get(
        "/api/wecom/verify",
        params={"signature": sig, "timestamp": ts, "nonce": nonce, "echostr": echo},
    )
    assert resp.status_code == 200
    assert resp.text == "12345"

    bad = client.get(
        "/api/wecom/verify",
        params={"signature": "bad", "timestamp": ts, "nonce": nonce, "echostr": echo},
    )
    assert bad.status_code == 403
