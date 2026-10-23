from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..audit import write_audit
from ..auth import get_current_user, require_roles
from ..db import get_db
from ..models import Drawing, User, utcnow
from ..permissions import accessible_project_ids, require_drawing, require_project
from ..schemas import DrawingCreate, DrawingOut

router = APIRouter(tags=["drawings"])


def _expire_lock(drawing: Drawing) -> None:
    if drawing.locked_by and drawing.lock_expires_at and drawing.lock_expires_at < utcnow():
        drawing.locked_by = None
        drawing.lock_expires_at = None


@router.get("/drawings", response_model=list[DrawingOut])
def list_drawings(
    project_id: int | None = None,
    status: str | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
    response: Response = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Drawing).order_by(Drawing.id.desc())
    ids = accessible_project_ids(db, user)
    if ids is not None:
        stmt = stmt.where(Drawing.project_id.in_(ids)) if ids else stmt.where(Drawing.project_id == -1)
    if project_id:
        require_project(db, user, project_id)
        stmt = stmt.where(Drawing.project_id == project_id)
    if status:
        stmt = stmt.where(Drawing.status == status)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Drawing.drawing_no.ilike(like), Drawing.title.ilike(like)))
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    if response is not None:
        response.headers["X-Total-Count"] = str(total)
    stmt = stmt.offset(max(0, offset)).limit(min(max(1, limit), 200))
    return list(db.scalars(stmt))


@router.post("/drawings", response_model=DrawingOut, status_code=201)
def create_drawing(
    body: DrawingCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("designer")),
):
    require_project(db, user, body.project_id)
    if db.scalar(select(Drawing).where(Drawing.drawing_no == body.drawing_no)):
        raise HTTPException(status_code=400, detail={"code": "DUPLICATE", "message": "图号已存在"})
    drawing = Drawing(project_id=body.project_id, drawing_no=body.drawing_no, title=body.title)
    db.add(drawing)
    db.flush()
    write_audit(db, user.id, "drawing.create", "drawing", drawing.drawing_no, {"title": drawing.title})
    db.commit()
    db.refresh(drawing)
    return drawing


@router.get("/drawings/{drawing_id}", response_model=DrawingOut)
def get_drawing(drawing_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return require_drawing(db, user, drawing_id)


@router.post("/drawings/{drawing_id}/checkout", response_model=DrawingOut)
def checkout(drawing_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("designer"))):
    drawing = require_drawing(db, user, drawing_id)
    _expire_lock(drawing)
    if drawing.locked_by and drawing.locked_by != user.id:
        raise HTTPException(status_code=409, detail={"code": "LOCKED", "message": "图纸已被他人检出"})
    drawing.locked_by = user.id
    drawing.lock_expires_at = utcnow() + timedelta(minutes=30)
    write_audit(db, user.id, "drawing.checkout", "drawing", drawing.drawing_no)
    db.commit()
    db.refresh(drawing)
    return drawing


@router.post("/drawings/{drawing_id}/checkin", response_model=DrawingOut)
def checkin(drawing_id: int, db: Session = Depends(get_db), user: User = Depends(require_roles("designer"))):
    drawing = require_drawing(db, user, drawing_id)
    if drawing.locked_by and drawing.locked_by != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "只能检入自己锁定的图纸"})
    drawing.locked_by = None
    drawing.lock_expires_at = None
    write_audit(db, user.id, "drawing.checkin", "drawing", drawing.drawing_no)
    db.commit()
    db.refresh(drawing)
    return drawing
