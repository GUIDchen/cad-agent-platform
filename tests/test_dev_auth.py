from .conftest import headers


def test_dev_auth_can_be_disabled(client, monkeypatch):
    from app import auth as auth_module

    monkeypatch.setattr(auth_module, "ALLOW_DEV_AUTH", False)
    client.cookies.clear()
    assert client.get("/api/me", headers=headers("admin")).status_code == 401

    assert client.post("/api/auth/dev-login", json={"name": "admin"}).status_code == 200
    assert client.get("/api/me").json()["name"] == "admin"
    client.post("/api/auth/logout")
