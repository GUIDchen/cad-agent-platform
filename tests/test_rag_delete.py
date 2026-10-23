from app.db import SessionLocal
from app.models import KnowledgeChunk, KnowledgeDoc

from .conftest import headers


def test_delete_document_moves_to_trash(client):
    created = client.post(
        "/api/rag/documents",
        json={"title": "待删除", "content": "删除测试。" * 50},
        headers=headers("designer"),
    ).json()
    doc_id = created["id"]

    resp = client.delete("/api/rag/documents/" + str(doc_id), headers=headers("designer"))
    assert resp.status_code == 204

    docs = client.get("/api/rag/documents", headers=headers("designer")).json()
    assert all(doc["id"] != doc_id for doc in docs)

    db = SessionLocal()
    assert db.get(KnowledgeDoc, doc_id).deleted_at is not None
    chunks = db.query(KnowledgeChunk).filter(KnowledgeChunk.doc_id == doc_id).all()
    db.close()
    assert chunks
