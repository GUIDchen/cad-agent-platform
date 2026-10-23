from .conftest import headers


def test_stats(client):
    resp = client.get("/api/stats", headers=headers("admin"))
    assert resp.status_code == 200
    data = resp.json()
    for key in (
        "projects",
        "drawings",
        "versions",
        "jobs",
        "jobs_by_status",
        "pending_review",
        "approved",
        "avg_job_seconds",
    ):
        assert key in data
    assert isinstance(data["jobs_by_status"], dict)
    assert data["projects"] >= 1
