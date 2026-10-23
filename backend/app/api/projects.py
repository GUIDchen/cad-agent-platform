from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..audit import write_audit
from ..auth import get_current_user, require_roles
from ..db import get_db
from ..models import Project, ProjectMember, User
from ..notify import send
from ..permissions import accessible_project_ids, require_project
from ..schemas import ProjectCreate, ProjectMemberCreate, ProjectMemberOut, ProjectMemberUpdate, ProjectOut

router = APIRouter(tags=["projects"])


@router.get("/projects", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = select(Project).order_by(Project.id)
    ids = accessible_project_ids(db, user)
    if ids is not None:
        stmt = stmt.where(Project.id.in_(ids)) if ids else stmt.where(Project.id == -1)
    return list(db.scalars(stmt))


@router.post("/projects", response_model=ProjectOut, status_code=201)
def create_project(
    body: ProjectCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("designer")),
):
    project = Project(name=body.name, owner_id=user.id)
    db.add(project)
    db.flush()
    db.add(ProjectMember(project_id=project.id, user_id=user.id, role="owner"))
    write_audit(db, user.id, "project.create", "project", project.id, {"name": project.name})
    db.commit()
    db.refresh(project)
    return project


@router.get("/projects/{project_id}/members", response_model=list[ProjectMemberOut])
def list_members(
    project_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_project(db, user, project_id)
    members = list(
        db.scalars(select(ProjectMember).where(ProjectMember.project_id == project_id).order_by(ProjectMember.id))
    )
    names = {u.id: u.name for u in db.scalars(select(User).where(User.id.in_([m.user_id for m in members])))}
    return [
        {
            "id": m.id,
            "project_id": m.project_id,
            "user_id": m.user_id,
            "role": m.role,
            "user_name": names.get(m.user_id),
        }
        for m in members
    ]


@router.post("/projects/{project_id}/members", response_model=ProjectMemberOut, status_code=201)
def add_member(
    project_id: int,
    body: ProjectMemberCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = require_project(db, user, project_id)
    if user.role != "admin" and project.owner_id != user.id:
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "只有管理员或项目负责人可加成员"})
    target = db.get(User, body.user_id)
    if not target:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "用户不存在"})
    existing = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == body.user_id,
        )
    )
    if existing:
        return existing
    member = ProjectMember(project_id=project_id, user_id=body.user_id, role=body.role)
    db.add(member)
    write_audit(db, user.id, "project.member.add", "project", project_id, {"user_id": body.user_id})
    db.commit()
    db.refresh(member)
    send(f"[项目成员] {project.name} 添加 {target.name}（{body.role}）")
    return member


@router.patch("/projects/{project_id}/members/{user_id}", response_model=ProjectMemberOut)
def update_member_role(
    project_id: int,
    user_id: int,
    body: ProjectMemberUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = require_project(db, user, project_id)
    if user.role != "admin" and project.owner_id != user.id:
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "只有管理员或项目负责人可改角色"})
    if user_id == project.owner_id and body.role != "owner":
        raise HTTPException(status_code=400, detail={"code": "OWNER", "message": "不能降级项目负责人"})
    member = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )
    if not member:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "成员不存在"})
    member.role = body.role
    write_audit(db, user.id, "project.member.role", "project", project_id, {"user_id": user_id, "role": body.role})
    db.commit()
    db.refresh(member)
    target = db.get(User, user_id)
    send(f"[项目成员] 项目 {project.name} 将 {target.name if target else user_id} 设为 {body.role}")
    return {
        "id": member.id,
        "project_id": member.project_id,
        "user_id": member.user_id,
        "role": member.role,
        "user_name": target.name if target else None,
    }


@router.delete("/projects/{project_id}/members/{user_id}", status_code=204)
def remove_member(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = require_project(db, user, project_id)
    if user.role != "admin" and project.owner_id != user.id:
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "只有管理员或项目负责人可移除成员"})
    if user_id == project.owner_id:
        raise HTTPException(status_code=400, detail={"code": "OWNER", "message": "不能移除项目负责人"})
    member = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )
    if not member:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "成员不存在"})
    db.delete(member)
    write_audit(db, user.id, "project.member.remove", "project", project_id, {"user_id": user_id})
    db.commit()
    send(f"[项目成员] 项目 {project.name} 移除用户 {user_id}")
    return Response(status_code=204)
