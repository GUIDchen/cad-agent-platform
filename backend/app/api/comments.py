from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..audit import write_audit
from ..auth import get_current_user
from ..db import get_db
from ..models import Comment, User
from ..permissions import require_drawing
from ..schemas import CommentIn, CommentOut

router = APIRouter(tags=["comments"])


@router.get("/drawings/{drawing_id}/comments", response_model=list[CommentOut])
def list_comments(drawing_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    require_drawing(db, user, drawing_id)
    rows = db.execute(
        select(Comment, User)
        .join(User, Comment.author_id == User.id)
        .where(Comment.drawing_id == drawing_id)
        .order_by(Comment.created_at.asc())
        .limit(200)
    ).all()
    return [
        {
            "id": comment.id,
            "drawing_id": comment.drawing_id,
            "version_id": comment.version_id,
            "author_id": comment.author_id,
            "author_name": author.name,
            "body": comment.body,
            "created_at": comment.created_at,
        }
        for comment, author in rows
    ]


@router.post("/drawings/{drawing_id}/comments", response_model=CommentOut, status_code=201)
def add_comment(
    drawing_id: int,
    body: CommentIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    drawing = require_drawing(db, user, drawing_id)
    comment = Comment(drawing_id=drawing.id, version_id=body.version_id, author_id=user.id, body=body.body)
    db.add(comment)
    write_audit(db, user.id, "comment.create", "drawing", drawing.drawing_no, {"comment_id": None})
    db.commit()
    db.refresh(comment)
    return {
        "id": comment.id,
        "drawing_id": comment.drawing_id,
        "version_id": comment.version_id,
        "author_id": comment.author_id,
        "author_name": user.name,
        "body": comment.body,
        "created_at": comment.created_at,
    }
