from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy import func, select, text

from ..config import APP_ENV, APP_VERSION, STORAGE_BACKEND
from ..db import get_db
from ..models import Drawing, Job
from ..state import state
from ..storage import get_storage

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/version")
def version() -> dict:
    return {"version": APP_VERSION, "env": APP_ENV, "storage": STORAGE_BACKEND}


@router.get("/ready")
def ready(db=Depends(get_db)):
    db.execute(text("SELECT 1"))
    storage_ok = get_storage().health()
    redis_ok = state.healthy()
    ok = storage_ok and redis_ok
    body = {
        "status": "ok" if ok else "degraded",
        "database": "ok",
        "storage": STORAGE_BACKEND,
        "storage_ok": storage_ok,
        "redis_ok": redis_ok,
    }
    return JSONResponse(status_code=200 if ok else 503, content=body)


@router.get("/metrics")
def metrics(db=Depends(get_db)):
    requests = state.request_metrics()
    count, total = state.duration_metrics()

    lines = ["# TYPE cad_requests_total counter"]
    for field, value in sorted(requests.items()):
        method, path, status = field.split("|", 2)
        lines.append(f'cad_requests_total{{method="{method}",path="{path}",status="{status}"}} {value}')
    lines.append("# TYPE cad_request_duration_seconds summary")
    lines.append(f"cad_request_duration_seconds_count {count}")
    lines.append(f"cad_request_duration_seconds_sum {total:.6f}")
    lines.append("# TYPE cad_drawings_total gauge")
    lines.append(f"cad_drawings_total {db.scalar(select(func.count()).select_from(Drawing)) or 0}")
    lines.append("# TYPE cad_jobs_total gauge")
    lines.append(f"cad_jobs_total {db.scalar(select(func.count()).select_from(Job)) or 0}")
    lines.append("# TYPE cad_jobs_queued gauge")
    lines.append(f"cad_jobs_queued {db.scalar(select(func.count()).select_from(Job).where(Job.status == 'queued')) or 0}")
    return PlainTextResponse("\n".join(lines) + "\n")
