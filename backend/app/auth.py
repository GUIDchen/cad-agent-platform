from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import ALLOW_DEV_AUTH, SESSION_COOKIE
from .db import get_db
from .models import User
from .session import verify_session


def get_current_user(
    request: Request,
    x_user: str | None = Header(default=None, alias="X-User"),
    db: Session = Depends(get_db),
) -> User:
    if x_user and ALLOW_DEV_AUTH:
        user = db.scalar(select(User).where(User.name == x_user, User.active.is_(True)))
        if not user:
            raise HTTPException(status_code=401, detail={"code": "UNAUTHENTICATED", "message": "用户不存在或已禁用"})
        return user

    token = request.cookies.get(SESSION_COOKIE)
    user_id = verify_session(token) if token else None
    if user_id:
        user = db.get(User, user_id)
        if user and user.active:
            return user

    raise HTTPException(status_code=401, detail={"code": "UNAUTHENTICATED", "message": "未登录"})


def require_roles(*roles: str):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role != "admin" and user.role not in roles:
            raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "角色不足"})
        return user

    return dependency
