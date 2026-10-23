from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Drawing, Project, ProjectMember, User


def _not_found(message: str = "对象不存在") -> HTTPException:
    return HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": message})


def accessible_project_ids(db: Session, user: User) -> set[int] | None:
    if user.role == "admin":
        return None
    return set(
        db.scalars(select(ProjectMember.project_id).where(ProjectMember.user_id == user.id)).all()
    )


def require_project(db: Session, user: User, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise _not_found("项目不存在")
    if user.role == "admin":
        return project
    member = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.id,
        )
    )
    if not member:
        raise _not_found("项目不存在")
    return project


def require_drawing(db: Session, user: User, drawing_id: int) -> Drawing:
    drawing = db.get(Drawing, drawing_id)
    if not drawing:
        raise _not_found("图纸不存在")
    require_project(db, user, drawing.project_id)
    return drawing
