from .conftest import headers


def test_user_admin_crud(client):
    admin = headers("admin")
    created = client.post("/api/users", json={"name": "temp-user-1", "role": "viewer"}, headers=admin)
    assert created.status_code in (201, 400)
    if created.status_code == 201:
        uid = created.json()["id"]
        updated = client.patch(f"/api/users/{uid}", json={"role": "designer"}, headers=admin)
        assert updated.status_code == 200
        assert updated.json()["role"] == "designer"

    assert client.get("/api/users", headers=headers("designer")).status_code == 403


def test_user_options(client):
    resp = client.get("/api/users/options", headers=headers("designer"))
    assert resp.status_code == 200
    data = resp.json()
    assert data and all("role" not in item for item in data)


def test_duplicate_user(client):
    admin = headers("admin")
    client.post("/api/users", json={"name": "temp-user-2", "role": "viewer"}, headers=admin)
    dup = client.post("/api/users", json={"name": "temp-user-2", "role": "viewer"}, headers=admin)
    assert dup.status_code == 400


def test_cannot_disable_self(client):
    admin = headers("admin")
    me = client.get("/api/me", headers=admin).json()
    resp = client.patch(f"/api/users/{me['id']}", json={"active": False}, headers=admin)
    assert resp.status_code == 400


def test_cannot_demote_last_admin(client):
    admin = headers("admin")
    me = client.get("/api/me", headers=admin).json()
    resp = client.patch(f"/api/users/{me['id']}", json={"role": "designer"}, headers=admin)
    assert resp.status_code == 400
