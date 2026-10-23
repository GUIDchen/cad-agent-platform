from datetime import timedelta

from app.db import SessionLocal
from app.models import KnowledgeDoc, utcnow
from tools.trash_cleanup import cleanup_trash

from .conftest import headers


def test_cleanup_old_trash(client):
    old = client.post(
        "/api/rag/documents",
        json={"title": "旧回收站", "content": "旧内容。" * 20},
        headers=headers("designer"),
    ).json()
    fresh = client.post(
        "/api/rag/documents",
        json={"title": "新回收站", "content": "新内容。" * 20},
        headers=headers("designer"),
    ).json()

    db = SessionLocal()
    old_doc = db.get(KnowledgeDoc, old["id"])
    old_doc.deleted_at = utcnow() - timedelta(days=40)
    fresh_doc = db.get(KnowledgeDoc, fresh["id"])
    fresh_doc.deleted_at = utcnow()
    db.commit()
    db.close()

    result = cleanup_trash(days=30)
    assert result["removed"] == 1

    db = SessionLocal()
    assert db.get(KnowledgeDoc, old["id"]) is None
    assert db.get(KnowledgeDoc, fresh["id"]) is not None
    db.close()
