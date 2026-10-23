from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..audit import write_audit
from ..auth import get_current_user
import secrets

from ..config import CSRF_COOKIE, SESSION_COOKIE, SESSION_COOKIE_SECURE, SESSION_MAX_AGE, WECOM_MODE
from ..db import get_db
from ..models import User
from ..schemas import LoginIn, UserOut
from ..session import sign_session
from ..wecom import authorize_url, exchange_code, make_state, verify_state

router = APIRouter(tags=["auth"])


def _set_session(response, user: User):
    response.set_cookie(
        SESSION_COOKIE,
        sign_session(user.id),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=SESSION_COOKIE_SECURE,
    )
    response.set_cookie(
        CSRF_COOKIE,
        secrets.token_hex(16),
        max_age=SESSION_MAX_AGE,
        httponly=False,
        samesite="lax",
        secure=SESSION_COOKIE_SECURE,
    )
    return response


def _user_dict(user: User) -> dict:
    return {"id": user.id, "name": user.name, "role": user.role}


@router.get("/auth/config")
def auth_config() -> dict:
    return {"wecom_mode": WECOM_MODE, "dev_login": True}


@router.post("/auth/dev-login")
def dev_login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.name == body.name, User.active.is_(True)))
    if not user:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "用户不存在"})
    write_audit(db, user.id, "auth.login", "user", user.name, {"via": "dev"})
    db.commit()
    response = JSONResponse(_user_dict(user))
    return _set_session(response, user)


@router.get("/auth/wecom/login")
def wecom_login(user: str = "designer", db: Session = Depends(get_db)):
    if WECOM_MODE != "real":
        found = db.scalar(select(User).where(User.name == user, User.active.is_(True)))
        if not found:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "用户不存在"})
        write_audit(db, found.id, "auth.login", "user", found.name, {"via": "wecom-mock"})
        db.commit()
        response = JSONResponse(_user_dict(found))
        return _set_session(response, found)
    try:
        return RedirectResponse(authorize_url(make_state()))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail={"code": "WECOM_CONFIG", "message": str(exc)}) from exc


@router.get("/auth/wecom/callback")
def wecom_callback(code: str = "", state: str = "", db: Session = Depends(get_db)):
    if WECOM_MODE != "real":
        return RedirectResponse("/drawings")
    if not verify_state(state):
        raise HTTPException(status_code=400, detail={"code": "BAD_STATE", "message": "state 无效或过期"})
    try:
        userid = exchange_code(code)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail={"code": "WECOM_API", "message": str(exc)}) from exc

    user = db.scalar(select(User).where(User.name == userid))
    if not user:
        user = User(name=userid, role="viewer")
        db.add(user)
        db.commit()
        db.refresh(user)

    response = RedirectResponse("/drawings")
    return _set_session(response, user)


@router.post("/auth/logout")
def logout():
    response = JSONResponse({"ok": True})
    response.delete_cookie(SESSION_COOKIE)
    response.delete_cookie(CSRF_COOKIE)
    return response


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user
