from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..audit import write_audit
from ..auth import get_current_user, require_roles
from ..db import get_db
from ..models import User
from ..schemas import UserCreate, UserOut, UserUpdate

router = APIRouter(tags=["users"])


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), user: User = Depends(require_roles())):
    return list(db.scalars(select(User).order_by(User.id)))


@router.get("/users/options")
def user_options(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return [
        {"id": u.id, "name": u.name}
        for u in db.scalars(select(User).where(User.active.is_(True)).order_by(User.id))
    ]


@router.post("/users", response_model=UserOut, status_code=201)
def create_user(
    body: UserCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    if db.scalar(select(User).where(User.name == body.name)):
        raise HTTPException(status_code=400, detail={"code": "DUPLICATE", "message": "用户已存在"})
    target = User(name=body.name, role=body.role)
    db.add(target)
    db.flush()
    write_audit(db, user.id, "user.create", "user", target.id, {"name": target.name, "role": target.role})
    db.commit()
    db.refresh(target)
    return target


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    body: UserUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles()),
):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "用户不存在"})

    if body.active is False and target.id == user.id:
        raise HTTPException(status_code=400, detail={"code": "SELF", "message": "不能禁用自己"})

    if body.role is not None and target.role == "admin" and body.role != "admin":
        admins = db.scalar(
            select(func.count()).select_from(User).where(User.role == "admin", User.active.is_(True))
        )
        if (admins or 0) <= 1:
            raise HTTPException(status_code=400, detail={"code": "LAST_ADMIN", "message": "不能降级最后一个管理员"})

    if body.role is not None:
        target.role = body.role
    if body.active is not None:
        target.active = body.active

    write_audit(
        db,
        user.id,
        "user.update",
        "user",
        target.id,
        {"role": target.role, "active": target.active},
    )
    db.commit()
    db.refresh(target)
    return target
