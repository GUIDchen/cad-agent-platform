from app.db import SessionLocal
from app.models import KnowledgeDoc

from .conftest import headers


def test_incremental_reindex(client):
    created = client.post(
        "/api/rag/documents",
        json={"title": "增量", "content": "折弯工艺。" * 80},
        headers=headers("designer"),
    ).json()

    first = client.post("/api/rag/reindex", headers=headers("designer")).json()
    assert first["documents"] == 0

    db = SessionLocal()
    doc = db.get(KnowledgeDoc, created["id"])
    doc.content = doc.content + "新增内容"
    db.commit()
    db.close()

    second = client.post("/api/rag/reindex", headers=headers("designer")).json()
    assert second["documents"] == 1
    assert second["chunks"] >= 1
