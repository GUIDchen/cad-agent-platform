import json
import shutil
import uuid
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..audit import write_audit
from ..config import DATA_DIR
from ..core.adapters import run_external
from ..core.bracket import build
from ..core.preview import render
from ..core.validate import validate
from ..db import SessionLocal
from ..models import Drawing, Job, User, Version, utcnow
from ..notifications import notify_user
from ..notify import notify_approval_card, notify_job_done, notify_job_failed
from ..storage import get_storage, sha256_file, version_keys


def create_job(db: Session, drawing: Drawing, user: User, spec: dict, job_type: str = "generate_bracket") -> Job:
    job = Job(
        id=uuid.uuid4().hex,
        drawing_id=drawing.id,
        type=job_type,
        payload_json=json.dumps(spec, ensure_ascii=False),
        status="queued",
        created_by=user.id,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def _next_version(db: Session, drawing_id: int) -> int:
    current = db.scalar(select(func.max(Version.version)).where(Version.drawing_id == drawing_id))
    return int(current or 0) + 1


def finalize(db: Session, job: Job, dxf_path: Path, png_path: Path) -> Version:
    drawing = db.get(Drawing, job.drawing_id)
    if drawing is None:
        raise RuntimeError("图纸不存在")
    version_no = _next_version(db, drawing.id)
    key_dxf, key_png = version_keys(drawing.drawing_no, version_no)
    store = get_storage()
    store.save(dxf_path, key_dxf)
    store.save(png_path, key_png)

    version = Version(
        drawing_id=drawing.id,
        version=version_no,
        file_path=key_dxf,
        preview_path=key_png,
        sha256=sha256_file(dxf_path),
        params_json=job.payload_json,
        created_by=job.created_by,
    )
    db.add(version)
    db.flush()

    drawing.current_version_id = version.id
    drawing.status = "pending_review"
    job.status = "done"
    job.finished_at = utcnow()
    write_audit(
        db,
        actor_id=job.created_by,
        action="generate.done",
        object_type="drawing",
        object_id=drawing.drawing_no,
        detail={"version": version_no, "job_id": job.id},
    )
    notify_user(
        db, job.created_by, "job",
        f"{drawing.drawing_no} v{version_no} 生成完成",
        f"/drawings/{drawing.id}",
    )
    db.commit()
    db.refresh(version)
    notify_job_done(drawing.drawing_no, version_no)
    notify_approval_card(drawing.drawing_no, version_no, version.id)
    return version


def run_job(job_id: str) -> str:
    db = SessionLocal()
    job = db.get(Job, job_id)
    if job is None or job.status not in ("queued", "running"):
        db.close()
        return "skipped"
    drawing = db.get(Drawing, job.drawing_id)
    if drawing is None:
        job.status = "failed"
        job.error = "图纸不存在"
        db.commit()
        db.close()
        return "failed"

    job.status = "running"
    job.started_at = utcnow()
    job.attempts += 1
    drawing.status = "generating"
    db.commit()

    spec = json.loads(job.payload_json)
    spec["drawing_no"] = drawing.drawing_no
    spec["title"] = drawing.title
    tmp_dir = DATA_DIR / "tmp" / job.id
    tmp_dir.mkdir(parents=True, exist_ok=True)
    try:
        if job.type == "generate_bracket":
            dxf = build(spec, tmp_dir / "out.dxf")
            issues = validate(str(dxf), spec)
            if issues:
                raise ValueError("; ".join(issues))
            png = render(dxf, tmp_dir / "out.png")
        elif job.type.startswith("generate_"):
            kind = job.type.removeprefix("generate_")
            dxf, png = run_external(kind, spec, tmp_dir)
            issues = validate(str(dxf), spec)
            if issues:
                raise ValueError("; ".join(issues))
        else:
            raise ValueError(f"不支持的任务类型: {job.type}")
        db.expire_all()
        current = db.get(Job, job.id)
        if current and current.status == "canceled":
            drawing.status = "draft"
            db.commit()
            return "canceled"
        finalize(db, job, dxf, png)
        return "done"
    except Exception as exc:  # noqa: BLE001
        job.status = "failed"
        job.error = str(exc)
        job.finished_at = utcnow()
        drawing.status = "draft"
        write_audit(
            db,
            actor_id=job.created_by,
            action="generate.failed",
            object_type="drawing",
            object_id=drawing.drawing_no,
            detail={"job_id": job.id, "error": str(exc)},
        )
        db.commit()
        notify_job_failed(drawing.drawing_no, str(exc))
        return "failed"
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        db.close()