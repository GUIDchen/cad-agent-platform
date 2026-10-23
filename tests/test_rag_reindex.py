from app.db import SessionLocal
from app.models import KnowledgeChunk

from .conftest import headers


def test_reindex_documents(client):
    client.post(
        "/api/rag/documents",
        json={"title": "重建", "content": "折弯工艺。" * 80},
        headers=headers("designer"),
    )
    db = SessionLocal()
    db.query(KnowledgeChunk).delete()
    db.commit()
    db.close()

    resp = client.post("/api/rag/reindex", headers=headers("designer"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["documents"] >= 1
    assert body["chunks"] >= 1

    stats = client.get("/api/rag/stats", headers=headers("admin")).json()
    assert stats["chunks"] >= 1
