import uuid

from app import wecom_crypto
from app.api import wecom as wecom_api
from app.replay import reset, seen_before

from .conftest import headers

TOKEN = "tok"
KEY = "A" * 43
CORP = "corp"


def test_replay_cache():
    reset()
    assert not seen_before("event-1")
    assert seen_before("event-1")
    reset()


def _generated_version(client, no: str) -> tuple[int, int]:
    project_id = client.get("/api/projects", headers=headers("admin")).json()[0]["id"]
    drawing = client.post(
        "/api/drawings",
        json={"project_id": project_id, "drawing_no": no, "title": "事件审批"},
        headers=headers("designer"),
    ).json()
    gen = client.post(
        f"/api/drawings/{drawing['id']}/generate",
        json={"length": 180, "width": 120, "holes": [{"x": 20, "y": 20, "d": 6.6}]},
        headers=headers("designer"),
    ).json()
    assert client.get(f"/api/jobs/{gen['job_id']}", headers=headers("designer")).json()["status"] == "done"
    version_id = client.get(
        f"/api/drawings/{drawing['id']}/versions", headers=headers("designer")
    ).json()[0]["id"]
    return drawing["id"], version_id


def _build_event(inner_xml: str):
    encrypted = wecom_crypto.encrypt(KEY, inner_xml, CORP)
    body = f"<xml><Encrypt><![CDATA[{encrypted}]]></Encrypt></xml>"
    timestamp = "1700000000"
    nonce = uuid.uuid4().hex
    signature = wecom_crypto.signature(TOKEN, timestamp, nonce, encrypted)
    params = {
        "msg_signature": signature,
        "timestamp": timestamp,
        "nonce": nonce,
    }
    return body, params


def test_event_approve_and_replay(client, monkeypatch):
    monkeypatch.setattr(wecom_api, "WECOM_TOKEN", TOKEN)
    monkeypatch.setattr(wecom_api, "WECOM_ENCODING_AES_KEY", KEY)
    monkeypatch.setattr(wecom_api, "WECOM_CORP_ID", CORP)

    drawing_id, version_id = _generated_version(client, "SW-2026-601")
    inner = (
        "<xml><FromUserName>reviewer</FromUserName>"
        "<Event>template_card_event</Event>"
        f"<EventKey>approve:{version_id}</EventKey></xml>"
    )
    body, params = _build_event(inner)

    first = client.post("/api/wecom/event", params=params, content=body)
    assert first.status_code == 200
    assert first.text == "success"
    assert client.get(f"/api/drawings/{drawing_id}", headers=headers("reviewer")).json()["status"] == "approved"

    second = client.post("/api/wecom/event", params=params, content=body)
    assert second.status_code == 200
    assert client.get(f"/api/drawings/{drawing_id}", headers=headers("reviewer")).json()["status"] == "approved"


def test_event_reject_and_bad_signature(client, monkeypatch):
    monkeypatch.setattr(wecom_api, "WECOM_TOKEN", TOKEN)
    monkeypatch.setattr(wecom_api, "WECOM_ENCODING_AES_KEY", KEY)
    monkeypatch.setattr(wecom_api, "WECOM_CORP_ID", CORP)

    drawing_id, version_id = _generated_version(client, "SW-2026-602")
    inner = (
        "<xml><FromUserName>reviewer</FromUserName>"
        "<Event>template_card_event</Event>"
        f"<EventKey>reject:{version_id}</EventKey></xml>"
    )
    body, params = _build_event(inner)
    assert client.post("/api/wecom/event", params=params, content=body).status_code == 200
    assert client.get(f"/api/drawings/{drawing_id}", headers=headers("reviewer")).json()["status"] == "rejected"

    bad_params = dict(params)
    bad_params["msg_signature"] = "bad"
    assert client.post("/api/wecom/event", params=bad_params, content=body).status_code == 403
