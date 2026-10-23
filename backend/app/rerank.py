import os

import httpx


def rerank(query: str, hits: list[dict]) -> list[dict]:
    if not hits:
        return hits
    url = os.getenv("RERANK_API_URL", "")
    if not url:
        return hits
    model = os.getenv("RERANK_MODEL", "bge-reranker-v2-m3")
    try:
        response = httpx.post(
            url,
            json={"model": model, "query": query, "documents": [item["snippet"] for item in hits]},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        items = data.get("results") or data.get("data") or []
        if not items:
            return hits
        ranked = []
        for item in items:
            index = int(item.get("index", 0))
            if 0 <= index < len(hits):
                row = dict(hits[index])
                row["rerank_score"] = float(item.get("relevance_score", item.get("score", 0)))
                ranked.append(row)
        if not ranked:
            return hits
        ranked.sort(key=lambda row: row["rerank_score"], reverse=True)
        return ranked
    except Exception:  # noqa: BLE001
        return hits
