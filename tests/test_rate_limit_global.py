from .conftest import headers


def test_global_rate_limit(client, monkeypatch):
    from app import middleware

    monkeypatch.setattr(middleware, "GLOBAL_RATE_LIMIT", 1)
    client.cookies.clear()
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/drawings", headers=headers("admin")).status_code == 200
    assert client.get("/api/drawings", headers=headers("admin")).status_code == 429
