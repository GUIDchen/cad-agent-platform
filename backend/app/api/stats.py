from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db import get_db
from ..models import Drawing, Job, Project, User, Version

router = APIRouter(tags=["stats"])


@router.get("/stats")
def get_stats(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    jobs_by_status = dict(
        db.execute(select(Job.status, func.count()).group_by(Job.status)).all()
    )
    done_jobs = list(
        db.scalars(
            select(Job).where(
                Job.status == "done",
                Job.started_at.is_not(None),
                Job.finished_at.is_not(None),
            )
        )
    )
    durations = [
        (job.finished_at - job.started_at).total_seconds()
        for job in done_jobs
        if job.finished_at and job.started_at
    ]
    return {
        "projects": db.scalar(select(func.count()).select_from(Project)) or 0,
        "drawings": db.scalar(select(func.count()).select_from(Drawing)) or 0,
        "versions": db.scalar(select(func.count()).select_from(Version)) or 0,
        "jobs": db.scalar(select(func.count()).select_from(Job)) or 0,
        "jobs_by_status": jobs_by_status,
        "pending_review": db.scalar(
            select(func.count()).select_from(Drawing).where(Drawing.status == "pending_review")
        )
        or 0,
        "approved": db.scalar(
            select(func.count()).select_from(Drawing).where(Drawing.status == "approved")
        )
        or 0,
        "avg_job_seconds": round(sum(durations) / len(durations), 3) if durations else 0.0,
    }
