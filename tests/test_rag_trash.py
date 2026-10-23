from app.db import SessionLocal
from app.models import KnowledgeChunk, KnowledgeDoc

from .conftest import headers


def test_document_trash_restore_purge(client):
    created = client.post(
        "/api/rag/documents",
        json={"title": "回收站", "content": "回收站测试。" * 40},
        headers=headers("designer"),
    ).json()
    doc_id = created["id"]

    assert client.delete("/api/rag/documents/" + str(doc_id), headers=headers("designer")).status_code == 204
    docs = client.get("/api/rag/documents", headers=headers("designer")).json()
    assert all(doc["id"] != doc_id for doc in docs)

    trash = client.get("/api/rag/trash", headers=headers("designer")).json()
    assert any(doc["id"] == doc_id for doc in trash)

    assert client.post("/api/rag/documents/" + str(doc_id) + "/restore", headers=headers("designer")).status_code == 200
    docs = client.get("/api/rag/documents", headers=headers("designer")).json()
    assert any(doc["id"] == doc_id for doc in docs)

    client.delete("/api/rag/documents/" + str(doc_id), headers=headers("designer"))
    assert client.delete("/api/rag/documents/" + str(doc_id) + "/purge", headers=headers("designer")).status_code == 204

    db = SessionLocal()
    assert db.get(KnowledgeDoc, doc_id) is None
    assert db.query(KnowledgeChunk).filter(KnowledgeChunk.doc_id == doc_id).count() == 0
    db.close()
