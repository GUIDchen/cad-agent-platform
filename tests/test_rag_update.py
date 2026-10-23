from app.db import SessionLocal
from app.models import KnowledgeChunk

from .conftest import headers


def test_update_document_reindexes_chunks(client):
    created = client.post(
        "/api/rag/documents",
        json={"title": "旧标题", "content": "旧工艺内容。" * 30},
        headers=headers("designer"),
    ).json()

    resp = client.patch(
        "/api/rag/documents/" + str(created["id"]),
        json={"title": "新标题", "content": "新工艺内容：激光切割。" * 20},
        headers=headers("designer"),
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "新标题"

    hits = client.get("/api/rag/search", params={"q": "激光切割"}, headers=headers("designer")).json()
    assert any(hit["title"] == "新标题" for hit in hits)

    db = SessionLocal()
    chunks = db.query(KnowledgeChunk).filter(KnowledgeChunk.doc_id == created["id"]).all()
    db.close()
    assert chunks
    assert any("激光切割" in chunk.content for chunk in chunks)
