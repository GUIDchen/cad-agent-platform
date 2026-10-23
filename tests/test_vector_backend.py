from app import vector_search

from .conftest import headers


class Resp:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_external_vector_search(client, monkeypatch):
    created = client.post(
        "/api/rag/documents",
        json={"title": "外部向量", "content": "完全无关的文本内容。" * 20},
        headers=headers("designer"),
    ).json()
    monkeypatch.setenv("VECTOR_SEARCH_URL", "http://vector/search")
    monkeypatch.setattr(
        vector_search.httpx,
        "post",
        lambda *a, **k: Resp({"results": [{"doc_id": created["id"], "chunk_index": 0, "score": 0.99}]}),
    )
    hits = client.get("/api/rag/search", params={"q": "zzz"}, headers=headers("designer")).json()
    assert hits
    assert hits[0]["title"] == "外部向量"


def test_external_vector_failure_falls_back(client, monkeypatch):
    client.post(
        "/api/rag/documents",
        json={"title": "回退", "content": "折弯工艺。" * 20},
        headers=headers("designer"),
    )
    monkeypatch.setenv("VECTOR_SEARCH_URL", "http://vector/search")

    def fail(*args, **kwargs):
        raise RuntimeError("down")

    monkeypatch.setattr(vector_search.httpx, "post", fail)
    hits = client.get("/api/rag/search", params={"q": "折弯"}, headers=headers("designer")).json()
    assert hits
