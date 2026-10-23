from datetime import datetime, timedelta, timezone

from .conftest import headers


def test_audit_filter_and_csv(client):
    admin = headers("admin")
    client.post("/api/projects", json={"name": "审计项目"}, headers=admin)

    rows = client.get("/api/audit", params={"action": "project.create", "limit": 10}, headers=admin).json()
    assert rows
    assert all(item["action"] == "project.create" for item in rows)

    resp = client.get("/api/audit", params={"fmt": "csv", "limit": 5}, headers=admin)
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "action" in resp.text
    assert "project.create" in resp.text

    now = datetime.now(timezone.utc)
    start = (now - timedelta(hours=1)).isoformat()
    end = (now + timedelta(hours=1)).isoformat()
    ranged = client.get("/api/audit", params={"start": start, "end": end}, headers=admin).json()
    assert ranged

    future = (now + timedelta(days=1)).isoformat()
    assert client.get("/api/audit", params={"start": future}, headers=admin).json() == []
    assert client.get("/api/audit", params={"start": "not-a-time"}, headers=admin).status_code == 400


def test_audit_requires_admin(client):
    assert client.get("/api/audit", headers=headers("designer")).status_code == 403
