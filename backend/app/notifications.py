from sqlalchemy.orm import Session

from .models import Notification


def notify_user(
    db: Session,
    user_id: int | None,
    type: str,
    title: str,
    link: str = "",
    body: str = "",
) -> None:
    if not user_id:
        return
    db.add(Notification(user_id=user_id, type=type, title=title, body=body, link=link))
