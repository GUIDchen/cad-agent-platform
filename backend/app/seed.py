from sqlalchemy import select

from .db import SessionLocal
from .models import Project, ProjectMember, User

DEFAULT_USERS = [
    ("admin", "admin"),
    ("designer", "designer"),
    ("designer2", "designer"),
    ("reviewer", "reviewer"),
    ("viewer", "viewer"),
]


def seed() -> None:
    db = SessionLocal()
    try:
        for name, role in DEFAULT_USERS:
            if not db.scalar(select(User).where(User.name == name)):
                db.add(User(name=name, role=role))
        db.commit()

        admin = db.scalar(select(User).where(User.name == "admin"))
        project = db.scalar(select(Project).limit(1))
        if admin and not project:
            project = Project(name="示范项目", owner_id=admin.id)
            db.add(project)
            db.commit()
            db.refresh(project)

        if project:
            existing = set(
                db.scalars(
                    select(ProjectMember.user_id).where(ProjectMember.project_id == project.id)
                ).all()
            )
            for user in db.scalars(select(User).where(User.active.is_(True))):
                if user.id not in existing:
                    db.add(
                        ProjectMember(
                            project_id=project.id,
                            user_id=user.id,
                            role="owner" if user.id == project.owner_id else "member",
                        )
                    )
            db.commit()
    finally:
        db.close()
