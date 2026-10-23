
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from ..audit import write_audit
from ..auth import require_roles
from ..config import EXECUTION_MODE
from ..db import get_db
from ..models import Drawing, User, utcnow
from ..permissions import require_drawing
from ..schemas import BatchGenerateIn, GenerateIn, JobCreated
from ..queue import enqueue
from ..services.generation import create_job, run_job

router = APIRouter(tags=["generation"])


def _expire_lock(drawing: Drawing) -> None:
    if drawing.locked_by and drawing.lock_expires_at and drawing.lock_expires_at < utcnow():
        drawing.locked_by = None
        drawing.lock_expires_at = None


@router.post("/drawings/batch-generate", response_model=list[JobCreated])
def batch_generate(
    body: BatchGenerateIn,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("designer")),
):
    ids = [item.drawing_id for item in body.items]
    if len(ids) != len(set(ids)):
        raise HTTPException(status_code=400, detail={"code": "DUPLICATE", "message": "批量任务包含重复图纸"})
    drawings = []
    for item in body.items:
        drawing = require_drawing(db, user, item.drawing_id)
        _expire_lock(drawing)
        if drawing.locked_by and drawing.locked_by != user.id:
            raise HTTPException(status_code=409, detail={"code": "LOCKED", "message": f"图纸 {drawing.drawing_no} 已被他人检出"})
        if drawing.status == "generating":
            raise HTTPException(status_code=409, detail={"code": "BUSY", "message": f"图纸 {drawing.drawing_no} 正在生成"})
        drawings.append(drawing)

    results = []
    for drawing, item in zip(drawings, body.items):
        spec = item.spec.model_dump(exclude={"job_type"})
        job = create_job(db, drawing, user, spec, item.spec.job_type)
        write_audit(
            db, user.id, "generate.request", "drawing", drawing.drawing_no,
            {"job_id": job.id, "spec": spec, "job_type": item.spec.job_type, "batch": True},
        )
        db.commit()
        if EXECUTION_MODE == "inline":
            background.add_task(run_job, job.id)
        elif EXECUTION_MODE == "queue":
            enqueue(job.id)
        results.append(JobCreated(job_id=job.id, status=job.status))
    return results


@router.post("/drawings/{drawing_id}/generate", response_model=JobCreated)
def generate(
    drawing_id: int,
    body: GenerateIn,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("designer")),
):
    drawing = require_drawing(db, user, drawing_id)
    _expire_lock(drawing)
    if drawing.locked_by and drawing.locked_by != user.id:
        raise HTTPException(status_code=409, detail={"code": "LOCKED", "message": "图纸已被他人检出"})
    if drawing.status == "generating":
        raise HTTPException(status_code=409, detail={"code": "BUSY", "message": "图纸正在生成"})

    spec = body.model_dump(exclude={"job_type"})
    job = create_job(db, drawing, user, spec, body.job_type)
    write_audit(
        db, user.id, "generate.request", "drawing", drawing.drawing_no,
        {"job_id": job.id, "spec": spec, "job_type": body.job_type},
    )
    db.commit()
    if EXECUTION_MODE == "inline":
        background.add_task(run_job, job.id)
    elif EXECUTION_MODE == "queue":
        enqueue(job.id)
    return JobCreated(job_id=job.id, status=job.status)
