import json

from app.api import jobs as jobs_module
from app.db import SessionLocal
from app.models import Job, User

from .conftest import headers


def test_dead_job_list_and_requeue(client, monkeypatch):
    monkeypatch.setattr(jobs_module, "EXECUTION_MODE", "external")
    project_id = client.get("/api/projects", headers=headers("admin")).json()[0]["id"]
    drawing = client.post(
        "/api/drawings",
        json={"project_id": project_id, "drawing_no": "SW-2026-995", "title": "死信"},
        headers=headers("designer"),
    ).json()

    db = SessionLocal()
    user = db.query(User).filter(User.name == "designer").first()
    job = Job(
        id="dead-1",
        drawing_id=drawing["id"],
        type="generate_bracket",
        payload_json=json.dumps({"length": 180, "width": 120, "holes": [{"x": 20, "y": 20, "d": 6.6}]}),
        status="dead",
        attempts=3,
        error="boom",
        created_by=user.id,
    )
    db.add(job)
    db.commit()
    db.close()

    rows = client.get("/api/jobs/dead", headers=headers("admin")).json()
    assert any(row["id"] == "dead-1" for row in rows)

    resp = client.post("/api/jobs/dead-1/requeue", headers=headers("admin"))
    assert resp.status_code == 200
    assert resp.json()["status"] == "queued"

    db = SessionLocal()
    assert db.get(Job, "dead-1").attempts == 0
    db.close()

def test_clear_dead_list(client):
    from app.queue import dead_jobs
    from app.state import state

    state.reset_memory()
    state.dead_letter("x")
    assert client.delete("/api/jobs/dead", headers=headers("admin")).json()["cleared"] == 1
    assert dead_jobs() == []

