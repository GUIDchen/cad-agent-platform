from app import embeddings
from app import rerank as rerank_module


class Resp:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


def test_remote_embedding(monkeypatch):
    monkeypatch.setenv("EMBEDDING_API_URL", "http://embed")
    monkeypatch.setattr(embeddings.httpx, "post", lambda *a, **k: Resp({"data": [{"embedding": [1, 2]}]}))
    assert embeddings.embed("x") == [1.0, 2.0]


def test_embedding_fallback(monkeypatch):
    monkeypatch.setenv("EMBEDDING_API_URL", "http://embed")

    def fail(*args, **kwargs):
        raise RuntimeError("down")

    monkeypatch.setattr(embeddings.httpx, "post", fail)
    assert embeddings.embed("折弯") == embeddings.local_embed("折弯")


def test_remote_rerank(monkeypatch):
    monkeypatch.setenv("RERANK_API_URL", "http://rerank")
    hits = [{"id": 1, "snippet": "a"}, {"id": 2, "snippet": "b"}]
    monkeypatch.setattr(
        rerank_module.httpx,
        "post",
        lambda *a, **k: Resp({"results": [{"index": 1, "relevance_score": 0.9}, {"index": 0, "relevance_score": 0.1}]}),
    )
    ranked = rerank_module.rerank("q", hits)
    assert ranked[0]["id"] == 2


def test_rerank_fallback(monkeypatch):
    monkeypatch.setenv("RERANK_API_URL", "http://rerank")

    def fail(*args, **kwargs):
        raise RuntimeError("down")

    monkeypatch.setattr(rerank_module.httpx, "post", fail)
    hits = [{"id": 1, "snippet": "a"}]
    assert rerank_module.rerank("q", hits) == hits
