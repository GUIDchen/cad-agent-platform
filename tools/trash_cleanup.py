import argparse
from datetime import timedelta

from sqlalchemy import delete, select

from app.db import SessionLocal
from app.models import KnowledgeChunk, KnowledgeDoc, KnowledgeDocVersion, utcnow


def cleanup_trash(days: int = 30) -> dict:
    cutoff = utcnow() - timedelta(days=days)
    db = SessionLocal()
    docs = list(
        db.scalars(
            select(KnowledgeDoc).where(
                KnowledgeDoc.deleted_at.is_not(None),
                KnowledgeDoc.deleted_at < cutoff,
            )
        )
    )
    for doc in docs:
        db.execute(delete(KnowledgeChunk).where(KnowledgeChunk.doc_id == doc.id))
        db.execute(delete(KnowledgeDocVersion).where(KnowledgeDocVersion.doc_id == doc.id))
        db.delete(doc)
    db.commit()
    db.close()
    return {"removed": len(docs), "days": days}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=30)
    args = parser.parse_args()
    print(cleanup_trash(args.days))
