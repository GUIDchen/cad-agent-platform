
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import get_current_user, require_roles
from ..config import CACHE_DIR
from ..db import get_db
from ..models import User, Version
from ..permissions import require_drawing
from ..schemas import ApproveIn, RejectIn, VersionOut
from ..services.approval import approve_version, reject_version
from ..services.upload import create_uploaded_version
from ..storage import get_storage

router = APIRouter(tags=["versions"])


def _get_version(db: Session, user: User, version_id: int) -> Version:
    version = db.get(Version, version_id)
    if not version:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "版本不存在"})
    require_drawing(db, user, version.drawing_id)
    return version


@router.get("/drawings/{drawing_id}/versions", response_model=list[VersionOut])
def list_versions(drawing_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    require_drawing(db, user, drawing_id)
    return list(
        db.scalars(
            select(Version).where(Version.drawing_id == drawing_id).order_by(Version.version.desc())
        )
    )


@router.post("/drawings/{drawing_id}/versions", response_model=VersionOut, status_code=201)
def upload_version(
    drawing_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("designer")),
):
    drawing = require_drawing(db, user, drawing_id)
    return create_uploaded_version(db, drawing, user, file)


@router.get("/versions/{version_id}/preview")
def preview(version_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    version = _get_version(db, user, version_id)
    path = get_storage().local_path(version.preview_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "预览不存在"})
    return FileResponse(path, media_type="image/png", filename=f"{path.name}")


@router.get("/versions/{version_id}/download")
def download(version_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    version = _get_version(db, user, version_id)
    path = get_storage().local_path(version.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "文件不存在"})
    return FileResponse(path, media_type="application/dxf", filename=f"v{version.version}.dxf")


@router.get("/versions/{version_id}/pdf")
def pdf(version_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    version = _get_version(db, user, version_id)
    source = get_storage().local_path(version.preview_path)
    if not source.exists():
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "预览不存在"})
    target = Path(CACHE_DIR) / f"version-{version.id}.pdf"
    if not target.exists():
        Image.open(source).convert("RGB").save(target, "PDF")
    return FileResponse(target, media_type="application/pdf", filename=f"v{version.version}.pdf")


@router.post("/versions/{version_id}/approve", response_model=VersionOut)
def approve(
    version_id: int,
    body: ApproveIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("reviewer")),
):
    version = _get_version(db, user, version_id)
    return approve_version(db, version, user, body.comment)


@router.post("/versions/{version_id}/reject", response_model=VersionOut)
def reject(
    version_id: int,
    body: RejectIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("reviewer")),
):
    version = _get_version(db, user, version_id)
    return reject_version(db, version, user, body.comment)
