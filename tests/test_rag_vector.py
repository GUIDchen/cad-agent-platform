from app.embeddings import cosine, local_embed


def test_local_embedding_similarity():
    left = local_embed("折弯工艺")
    right = local_embed("折弯工艺 304")
    other = local_embed("电路板布线")
    assert cosine(left, right) > cosine(left, other)


def test_rag_vector_search(client):
    from .conftest import headers

    client.post(
        "/api/rag/documents",
        json={"title": "折弯工艺", "content": "304 不锈钢折弯半径建议不小于板厚。"},
        headers=headers("designer"),
    )
    hits = client.get("/api/rag/search", params={"q": "折弯"}, headers=headers("designer")).json()
    assert hits
    assert hits[0]["title"] == "折弯工艺"
    assert hits[0]["score"] > 0
