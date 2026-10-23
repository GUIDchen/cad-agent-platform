import json
import shutil
import tempfile
from datetime import timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..config import WORKER_TOKEN
from ..db import get_db
from ..services.generation import finalize
from ..models import Drawing, Job, utcnow

router = APIRouter(tags=["internal"])


def _check_token(x_worker_token: str | None) -> None:
    if x_worker_token != WORKER_TOKEN:
        raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED", "message": "Worker 令牌错误"})


@router.post("/internal/jobs/claim")
def claim(
    db: Session = Depends(get_db),
    x_worker_token: str | None = Header(default=None, alias="X-Worker-Token"),
):
    _check_token(x_worker_token)
    stale = utcnow() - timedelta(minutes=15)
    db.execute(
        update(Job)
        .where(Job.status == "running", Job.started_at < stale)
        .values(status="queued")
    )
    db.commit()
    job = db.scalar(select(Job).where(Job.status == "queued").order_by(Job.created_at).limit(1))
    if not job:
        return {"job": None}
    drawing = db.get(Drawing, job.drawing_id)
    job.status = "running"
    job.started_at = utcnow()
    job.attempts += 1
    if drawing:
        drawing.status = "generating"
    db.commit()
    return {
        "job_id": job.id,
        "drawing_no": drawing.drawing_no if drawing else None,
        "payload": json.loads(job.payload_json),
    }


@router.post("/internal/jobs/{job_id}/fail")
def fail(
    job_id: str,
    body: dict,
    db: Session = Depends(get_db),
    x_worker_token: str | None = Header(default=None, alias="X-Worker-Token"),
):
    _check_token(x_worker_token)
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "任务不存在"})
    job.status = "failed"
    job.error = str(body.get("error", "worker failed"))
    job.finished_at = utcnow()
    drawing = db.get(Drawing, job.drawing_id)
    if drawing:
        drawing.status = "draft"
    db.commit()
    return {"status": "failed"}


@router.post("/internal/jobs/{job_id}/complete")
def complete(
    job_id: str,
    dxf: UploadFile = File(...),
    png: UploadFile = File(...),
    db: Session = Depends(get_db),
    x_worker_token: str | None = Header(default=None, alias="X-Worker-Token"),
):
    _check_token(x_worker_token)
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "任务不存在"})
    tmp = Path(tempfile.mkdtemp(prefix=f"job-{job_id}-"))
    try:
        dxf_path = tmp / "out.dxf"
        png_path = tmp / "out.png"
        with dxf_path.open("wb") as fh:
            shutil.copyfileobj(dxf.file, fh)
        with png_path.open("wb") as fh:
            shutil.copyfileobj(png.file, fh)
        version = finalize(db, job, dxf_path, png_path)
        return {"status": "done", "version_id": version.id, "version": version.version}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)