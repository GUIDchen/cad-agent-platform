from .conftest import headers


def test_agent_creates_and_generates(client):
    resp = client.post(
        "/api/ai/agent",
        json={"message": "创建图号 SW-2026-900 的安装板，180x120，4个M6孔，并生成"},
        headers=headers("designer"),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    tools = [step["tool"] for step in data["steps"]]
    assert "create_drawing" in tools
    assert "generate_drawing" in tools

    drawing = client.get("/api/drawings", headers=headers("designer")).json()
    item = next(d for d in drawing if d["drawing_no"] == "SW-2026-900")
    versions = client.get(f"/api/drawings/{item['id']}/versions", headers=headers("designer")).json()
    assert versions


def test_agent_lists_when_no_action(client):
    resp = client.post(
        "/api/ai/agent",
        json={"message": "列出图纸"},
        headers=headers("designer"),
    )
    assert resp.status_code == 200
    assert resp.json()["steps"][0]["tool"] == "list_drawings"
