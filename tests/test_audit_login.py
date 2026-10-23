from .conftest import headers


def test_login_writes_audit(client):
    client.cookies.clear()
    assert client.post("/api/auth/dev-login", json={"name": "designer"}).status_code == 200
    rows = client.get("/api/audit", params={"action": "auth.login"}, headers=headers("admin")).json()
    assert rows
    assert rows[0]["object_id"] == "designer"
    assert rows[0]["ip"] == "testclient"
