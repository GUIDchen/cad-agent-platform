from .conftest import headers


def test_auth_config(client):
    resp = client.get("/api/auth/config")
    assert resp.status_code == 200
    assert resp.json()["wecom_mode"] == "mock"


def test_wecom_mock_login_sets_cookie(client):
    client.cookies.clear()
    resp = client.get("/api/auth/wecom/login", params={"user": "reviewer"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "reviewer"

    me = client.get("/api/me")
    assert me.status_code == 200
    assert me.json()["name"] == "reviewer"

    client.post("/api/auth/logout")
    assert client.get("/api/me").status_code == 401


def test_dev_login_sets_cookie(client):
    client.cookies.clear()
    assert client.post("/api/auth/dev-login", json={"name": "designer"}).status_code == 200
    assert client.get("/api/me").json()["name"] == "designer"
    client.post("/api/auth/logout")


def test_header_still_wins(client):
    client.cookies.clear()
    client.post("/api/auth/dev-login", json={"name": "viewer"})
    me = client.get("/api/me", headers=headers("admin"))
    assert me.json()["name"] == "admin"
    client.post("/api/auth/logout")
