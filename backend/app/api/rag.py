import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from ..auth import get_current_user, require_roles
from ..chunking import chunk_text, content_hash
from ..db import get_db
from ..embeddings import cosine, embed
from ..models import KnowledgeChunk, KnowledgeDoc, KnowledgeDocVersion, User, utcnow
from ..rerank import rerank
from ..schemas import KnowledgeHit, KnowledgeIn, KnowledgeOut, KnowledgeUpdate, KnowledgeVersionOut
from .. import vector_search

router = APIRouter(tags=["rag"])


@router.get("/rag/documents", response_model=list[KnowledgeOut])
def list_documents(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return list(
        db.scalars(
            select(KnowledgeDoc)
            .where(KnowledgeDoc.deleted_at.is_(None))
            .order_by(KnowledgeDoc.created_at.desc())
            .limit(100)
        )
    )


@router.get("/rag/trash", response_model=list[KnowledgeOut])
def list_trash(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return list(
        db.scalars(
            select(KnowledgeDoc)
            .where(KnowledgeDoc.deleted_at.is_not(None))
            .order_by(KnowledgeDoc.deleted_at.desc())
        )
    )


def _snapshot(db: Session, doc: KnowledgeDoc, user: User) -> None:
    db.add(
        KnowledgeDocVersion(
            doc_id=doc.id,
            title=doc.title,
            content=doc.content,
            content_hash=doc.content_hash,
            created_by=user.id,
        )
    )


def _index_document(db: Session, doc: KnowledgeDoc) -> int:
    db.execute(delete(KnowledgeChunk).where(KnowledgeChunk.doc_id == doc.id))
    doc.embedding_json = json.dumps(embed(doc.title + "\n" + doc.content))
    doc.content_hash = content_hash(doc.title, doc.content)
    count = 0
    for index, text in enumerate(chunk_text(doc.content)):
        db.add(
            KnowledgeChunk(
                doc_id=doc.id,
                chunk_index=index,
                content=text,
                embedding_json=json.dumps(embed(text)),
            )
        )
        count += 1
    return count


@router.post("/rag/documents", response_model=KnowledgeOut, status_code=201)
def create_document(
    body: KnowledgeIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("designer")),
):
    doc = KnowledgeDoc(
        title=body.title,
        content=body.content,
        embedding_json=json.dumps(embed(body.title + "\n" + body.content)),
        content_hash=content_hash(body.title, body.content),
        created_by=user.id,
    )
    db.add(doc)
    db.flush()
    _index_document(db, doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.get("/rag/documents/{doc_id}/versions", response_model=list[KnowledgeVersionOut])
def list_versions(
    doc_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return list(
        db.scalars(
            select(KnowledgeDocVersion)
            .where(KnowledgeDocVersion.doc_id == doc_id)
            .order_by(KnowledgeDocVersion.created_at.desc())
        )
    )


@router.post("/rag/documents/{doc_id}/versions/{version_id}/restore", response_model=KnowledgeOut)
def restore_version(
    doc_id: int,
    version_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("designer")),
):
    doc = db.get(KnowledgeDoc, doc_id)
    version = db.get(KnowledgeDocVersion, version_id)
    if not doc or not version or version.doc_id != doc_id:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "文档或版本不存在"})
    _snapshot(db, doc, user)
    doc.title = version.title
    doc.content = version.content
    _index_document(db, doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.delete("/rag/documents/{doc_id}", status_code=204)
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("designer")),
) -> None:
    doc = db.get(KnowledgeDoc, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "文档不存在"})
    doc.deleted_at = utcnow()
    db.commit()


@router.post("/rag/documents/{doc_id}/restore", response_model=KnowledgeOut)
def restore_document(
    doc_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("designer")),
):
    doc = db.get(KnowledgeDoc, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "文档不存在"})
    doc.deleted_at = None
    existing = db.scalar(select(func.count()).select_from(KnowledgeChunk).where(KnowledgeChunk.doc_id == doc.id)) or 0
    if not existing:
        _index_document(db, doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.delete("/rag/documents/{doc_id}/purge", status_code=204)
def purge_document(
    doc_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("designer")),
) -> None:
    doc = db.get(KnowledgeDoc, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "文档不存在"})
    db.execute(delete(KnowledgeChunk).where(KnowledgeChunk.doc_id == doc_id))
    db.execute(delete(KnowledgeDocVersion).where(KnowledgeDocVersion.doc_id == doc_id))
    db.delete(doc)
    db.commit()


@router.patch("/rag/documents/{doc_id}", response_model=KnowledgeOut)
def update_document(
    doc_id: int,
    body: KnowledgeUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("designer")),
):
    doc = db.get(KnowledgeDoc, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "文档不存在"})
    data = body.model_dump(exclude_unset=True)
    changed = ("title" in data and data["title"] != doc.title) or (
        "content" in data and data["content"] != doc.content
    )
    if changed:
        _snapshot(db, doc, user)
    if "title" in data:
        doc.title = data["title"]
    if "content" in data:
        doc.content = data["content"]
    _index_document(db, doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.get("/rag/stats")
def stats(db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    return {
        "documents": db.scalar(
            select(func.count()).select_from(KnowledgeDoc).where(KnowledgeDoc.deleted_at.is_(None))
        )
        or 0,
        "chunks": db.scalar(select(func.count()).select_from(KnowledgeChunk)) or 0,
    }


@router.post("/rag/reindex")
def reindex(
    force: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("designer")),
):
    docs = list(db.scalars(select(KnowledgeDoc).where(KnowledgeDoc.deleted_at.is_(None))))
    rebuilt = 0
    chunks = 0
    for doc in docs:
        digest = content_hash(doc.title, doc.content)
        existing = db.scalar(
            select(func.count()).select_from(KnowledgeChunk).where(KnowledgeChunk.doc_id == doc.id)
        ) or 0
        if not force and doc.content_hash == digest and existing:
            continue
        db.execute(delete(KnowledgeChunk).where(KnowledgeChunk.doc_id == doc.id))
        doc.embedding_json = json.dumps(embed(doc.title + "\n" + doc.content))
        doc.content_hash = digest
        for index, text in enumerate(chunk_text(doc.content)):
            db.add(
                KnowledgeChunk(
                    doc_id=doc.id,
                    chunk_index=index,
                    content=text,
                    embedding_json=json.dumps(embed(text)),
                )
            )
            chunks += 1
        rebuilt += 1
    db.commit()
    return {"documents": rebuilt, "chunks": chunks}


@router.get("/rag/search", response_model=list[KnowledgeHit])
def search(q: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    terms = [item.lower() for item in q.split() if item.strip()]
    if not terms:
        return []
    query_vec = embed(q)
    external = vector_search.search(query_vec, 5)
    if external is not None:
        hits: list[dict] = []
        for result in external:
            doc = db.get(KnowledgeDoc, int(result.get("doc_id", 0)))
            if not doc or doc.deleted_at is not None:
                continue
            chunk = db.scalar(
                select(KnowledgeChunk).where(
                    KnowledgeChunk.doc_id == doc.id,
                    KnowledgeChunk.chunk_index == int(result.get("chunk_index", 0)),
                )
            )
            hits.append(
                {
                    "id": doc.id,
                    "title": doc.title,
                    "snippet": (chunk.content if chunk else doc.content)[:240],
                    "score": round(float(result.get("score", 0)), 3),
                }
            )
        return rerank(q, hits[:5])

    hits: dict[int, dict] = {}

    rows = db.execute(
        select(KnowledgeChunk, KnowledgeDoc)
        .join(KnowledgeDoc, KnowledgeChunk.doc_id == KnowledgeDoc.id)
        .where(KnowledgeDoc.deleted_at.is_(None))
    ).all()
    chunk_docs = set()
    for chunk, doc in rows:
        chunk_docs.add(doc.id)
        haystack = (doc.title + "\n" + chunk.content).lower()
        keyword = sum(haystack.count(term) for term in terms)
        try:
            chunk_vec = json.loads(chunk.embedding_json or "[]")
        except json.JSONDecodeError:
            chunk_vec = []
        score = max(cosine(query_vec, chunk_vec) if chunk_vec else 0.0, min(keyword, 10) / 10)
        if score < 0.12 and not keyword:
            continue
        current = hits.get(doc.id)
        if current is None or score > current["score"]:
            hits[doc.id] = {
                "id": doc.id,
                "title": doc.title,
                "snippet": chunk.content[:240],
                "score": round(score, 3),
            }

    docs = list(
        db.scalars(
            select(KnowledgeDoc)
            .where(KnowledgeDoc.deleted_at.is_(None))
            .order_by(KnowledgeDoc.created_at.desc())
            .limit(200)
        )
    )
    for doc in docs:
        if doc.id in chunk_docs:
            continue
        haystack = (doc.title + "\n" + doc.content).lower()
        keyword = sum(haystack.count(term) for term in terms)
        try:
            doc_vec = json.loads(doc.embedding_json or "[]")
        except json.JSONDecodeError:
            doc_vec = []
        score = max(cosine(query_vec, doc_vec) if doc_vec else 0.0, min(keyword, 10) / 10)
        if score < 0.12 and not keyword:
            continue
        hits[doc.id] = {"id": doc.id, "title": doc.title, "snippet": doc.content[:240], "score": round(score, 3)}

    ranked = sorted(hits.values(), key=lambda item: item["score"], reverse=True)
    return rerank(q, ranked[:5])
