from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import get_current_user, require_roles
from ..db import get_db
from ..erp import push_bom
from ..models import User, Version
from ..permissions import require_drawing
from ..services.bom import build_bom_csv

router = APIRouter(tags=["bom"])


@router.get("/drawings/{drawing_id}/bom")
def export_bom(drawing_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    drawing = require_drawing(db, user, drawing_id)
    version = None
    if drawing.current_version_id:
        version = db.get(Version, drawing.current_version_id)
    if version is None:
        version = db.scalar(
            select(Version).where(Version.drawing_id == drawing.id).order_by(Version.version.desc())
        )
    if version is None:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "图纸尚无版本"})

    content = build_bom_csv(drawing, version)
    filename = f"{drawing.drawing_no}-bom.csv"
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/drawings/{drawing_id}/bom/push")
def push_to_erp(
    drawing_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("designer")),
):
    drawing = require_drawing(db, user, drawing_id)
    version = None
    if drawing.current_version_id:
        version = db.get(Version, drawing.current_version_id)
    if version is None:
        version = db.scalar(
            select(Version).where(Version.drawing_id == drawing.id).order_by(Version.version.desc())
        )
    if version is None:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "图纸尚无版本"})

    content = build_bom_csv(drawing, version)
    return push_bom(drawing.drawing_no, version.version, content)
