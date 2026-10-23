from app import worker
from app.db import SessionLocal
from app.models import Job, User
from app.queue import ack, dead_jobs, dequeue
from app.state import state

from .conftest import headers


def test_worker_retry_then_dead_letter(client, monkeypatch):
    state.reset_memory()
    monkeypatch.setattr(worker, "JOB_MAX_ATTEMPTS", 2)

    project_id = client.get("/api/projects", headers=headers("admin")).json()[0]["id"]
    drawing = client.post(
        "/api/drawings",
        json={"project_id": project_id, "drawing_no": "SW-2026-991", "title": "重试"},
        headers=headers("designer"),
    ).json()

    db = SessionLocal()
    user = db.query(User).filter(User.name == "designer").first()
    job = Job(
        id="retry-1",
        drawing_id=drawing["id"],
        type="generate_bracket",
        payload_json="{}",
        status="failed",
        attempts=1,
        created_by=user.id,
    )
    db.add(job)
    db.commit()
    db.close()

    worker.handle_result("retry-1", "failed")
    db = SessionLocal()
    assert db.get(Job, "retry-1").status == "queued"
    db.close()
    assert dequeue(0) == "retry-1"
    ack("retry-1")

    db = SessionLocal()
    job = db.get(Job, "retry-1")
    job.attempts = 2
    job.status = "failed"
    db.commit()
    db.close()

    worker.handle_result("retry-1", "failed")
    db = SessionLocal()
    assert db.get(Job, "retry-1").status == "dead"
    db.close()
    assert "retry-1" in dead_jobs()
