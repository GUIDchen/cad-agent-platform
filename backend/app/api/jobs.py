import json
import time

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..audit import write_audit
from ..auth import get_current_user, require_roles
from ..config import EXECUTION_MODE
from ..db import SessionLocal, get_db
from ..models import Drawing, Job, User, utcnow
from ..permissions import require_drawing
from ..queue import clear_dead, enqueue, remove_dead
from ..schemas import DeadJobOut, JobCreated, JobOut
from ..services.generation import create_job, run_job

router = APIRouter(tags=["jobs"])


@router.get("/jobs/dead", response_model=list[DeadJobOut])
def list_dead_jobs(db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    jobs = list(db.scalars(select(Job).where(Job.status == "dead").order_by(Job.created_at.desc()).limit(100)))
    drawings = {}
    for job in jobs:
        drawing = db.get(Drawing, job.drawing_id)
        if drawing:
            drawings[job.drawing_id] = drawing
    return [
        {
            "id": job.id,
            "drawing_id": job.drawing_id,
            "drawing_no": drawings[job.drawing_id].drawing_no if job.drawing_id in drawings else "-",
            "title": drawings[job.drawing_id].title if job.drawing_id in drawings else "-",
            "type": job.type,
            "attempts": job.attempts,
            "error": job.error,
            "created_at": job.created_at,
        }
        for job in jobs
    ]


@router.delete("/jobs/dead")
def clear_dead_jobs(user: User = Depends(require_roles("admin"))):
    return {"cleared": clear_dead()}


@router.post("/jobs/{job_id}/requeue", response_model=JobCreated)
def requeue_dead_job(
    job_id: str,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "任务不存在"})
    if job.status != "dead":
        raise HTTPException(status_code=400, detail={"code": "NOT_DEAD", "message": "只有死信任务可重排"})
    job.status = "queued"
    job.attempts = 0
    job.error = None
    write_audit(db, user.id, "job.requeue", "job", job.id, {"drawing_id": job.drawing_id})
    db.commit()
    remove_dead(job.id)
    if EXECUTION_MODE == "inline":
        background.add_task(run_job, job.id)
    elif EXECUTION_MODE == "queue":
        enqueue(job.id)
    return JobCreated(job_id=job.id, status=job.status)


@router.get("/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "任务不存在"})
    require_drawing(db, user, job.drawing_id)
    return job


@router.post("/jobs/{job_id}/cancel", response_model=JobOut)
def cancel_job(job_id: str, db: Session = Depends(get_db), user: User = Depends(require_roles("designer"))):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "任务不存在"})
    drawing = require_drawing(db, user, job.drawing_id)
    if job.status in ("done", "failed", "canceled"):
        raise HTTPException(status_code=400, detail={"code": "TERMINAL", "message": "任务已结束"})
    job.status = "canceled"
    job.error = "canceled by user"
    job.finished_at = utcnow()
    drawing.status = "draft"
    write_audit(db, user.id, "job.cancel", "drawing", drawing.drawing_no, {"job_id": job.id})
    db.commit()
    db.refresh(job)
    return job


@router.post("/jobs/{job_id}/retry", response_model=JobCreated)
def retry_job(
    job_id: str,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("designer")),
):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "任务不存在"})
    drawing = require_drawing(db, user, job.drawing_id)
    if job.status not in ("failed", "canceled"):
        raise HTTPException(status_code=400, detail={"code": "NOT_RETRYABLE", "message": "只有失败/取消的任务可重试"})
    new_job = create_job(db, drawing, user, json.loads(job.payload_json), job.type)
    write_audit(db, user.id, "job.retry", "drawing", drawing.drawing_no, {"job_id": new_job.id, "from": job.id})
    db.commit()
    if EXECUTION_MODE == "inline":
        background.add_task(run_job, new_job.id)
    elif EXECUTION_MODE == "queue":
        enqueue(new_job.id)
    return JobCreated(job_id=new_job.id, status=new_job.status)


@router.get("/jobs/{job_id}/events")
def job_events(job_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "任务不存在"})
    require_drawing(db, user, job.drawing_id)

    def stream():
        session = SessionLocal()
        last = None
        try:
            for _ in range(1200):
                session.expire_all()
                current = session.get(Job, job_id)
                if not current:
                    break
                payload = {"status": current.status, "error": current.error}
                if payload != last:
                    yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                    last = payload
                if current.status in ("done", "failed", "canceled"):
                    break
                time.sleep(0.5)
        finally:
            session.close()

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
