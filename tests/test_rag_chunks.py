from app.db import SessionLocal
from app.models import KnowledgeChunk

from .conftest import headers


def test_document_is_chunked(client):
    content = "折弯工艺说明。" * 120
    resp = client.post(
        "/api/rag/documents",
        json={"title": "长文档", "content": content},
        headers=headers("designer"),
    )
    assert resp.status_code == 201
    db = SessionLocal()
    chunks = db.query(KnowledgeChunk).filter(KnowledgeChunk.doc_id == resp.json()["id"]).all()
    db.close()
    assert len(chunks) > 1
    assert all(chunk.embedding_json != "[]" for chunk in chunks)
