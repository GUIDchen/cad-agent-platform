import json

from app.db import SessionLocal
from app.models import Job, User

from .conftest import headers


def test_cancel_and_retry_job(client):
    project_id = client.get("/api/projects", headers=headers("admin")).json()[0]["id"]
    drawing = client.post(
        "/api/drawings",
        json={"project_id": project_id, "drawing_no": "SW-2026-981", "title": "取消"},
        headers=headers("designer"),
    ).json()

    db = SessionLocal()
    user = db.query(User).filter(User.name == "designer").first()
    job = Job(
        id="cancel-test",
        drawing_id=drawing["id"],
        type="generate_bracket",
        payload_json=json.dumps({"length": 180, "width": 120, "holes": [{"x": 20, "y": 20, "d": 6.6}]}),
        status="queued",
        created_by=user.id,
    )
    db.add(job)
    db.commit()
    db.close()

    resp = client.post("/api/jobs/cancel-test/cancel", headers=headers("designer"))
    assert resp.status_code == 200
    assert resp.json()["status"] == "canceled"

    retry = client.post("/api/jobs/cancel-test/retry", headers=headers("designer"))
    assert retry.status_code == 200
    assert retry.json()["job_id"] != "cancel-test"
