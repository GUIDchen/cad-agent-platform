from app.state import state

from .conftest import headers


def test_ai_parse_fallback(client):
    resp = client.post(
        "/api/ai/parse",
        json={"text": "180x120 安装板 4个M6孔 304"},
        headers=headers("designer"),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["source"] == "fallback"
    spec = data["spec"]
    assert spec["length"] == 180
    assert spec["width"] == 120
    assert spec["material"] == "304"
    assert len(spec["holes"]) == 4
    assert spec["holes"][0]["d"] == 6


def test_ai_image_mock(client):
    resp = client.post(
        "/api/ai/image",
        json={"prompt": "机械安装板", "width": 512, "height": 384},
        headers=headers("designer"),
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    assert resp.content.startswith(b"\x89PNG")
    assert resp.headers["X-Image-Mode"] == "mock"


def test_rate_limit_state():
    state.reset_memory()
    assert state.rate("unit", 2, 60)
    assert state.rate("unit", 2, 60)
    assert not state.rate("unit", 2, 60)
    state.reset_memory()


def test_ai_parse_requires_login(client):
    client.cookies.clear()
    assert client.post("/api/ai/parse", json={"text": "180x120"}).status_code == 401
