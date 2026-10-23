import argparse
import json
from pathlib import Path

from sqlalchemy import select

from app.db import SessionLocal
from app.models import KnowledgeChunk, KnowledgeDoc


def export_vectors(out: Path) -> dict:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    db = SessionLocal()
    rows = db.execute(
        select(KnowledgeChunk, KnowledgeDoc)
        .join(KnowledgeDoc, KnowledgeChunk.doc_id == KnowledgeDoc.id)
        .where(KnowledgeDoc.deleted_at.is_(None))
        .order_by(KnowledgeDoc.id, KnowledgeChunk.chunk_index)
    ).all()
    db.close()

    dim = 0
    count = 0
    with out.open("w", encoding="utf-8") as fh:
        for chunk, doc in rows:
            try:
                embedding = json.loads(chunk.embedding_json or "[]")
            except json.JSONDecodeError:
                embedding = []
            if not embedding:
                continue
            dim = len(embedding)
            fh.write(
                json.dumps(
                    {
                        "doc_id": doc.id,
                        "title": doc.title,
                        "chunk_index": chunk.chunk_index,
                        "content": chunk.content,
                        "embedding": embedding,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            count += 1
    return {"chunks": count, "dim": dim, "path": str(out)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="data/rag_vectors.jsonl")
    args = parser.parse_args()
    print(export_vectors(Path(args.out)))
