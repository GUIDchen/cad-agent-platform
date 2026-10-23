from .conftest import headers


def test_rag_documents_and_search(client):
    created = client.post(
        "/api/rag/documents",
        json={"title": "折弯工艺", "content": "304 不锈钢折弯半径建议不小于板厚，拉丝表面需保护膜。"},
        headers=headers("designer"),
    )
    assert created.status_code == 201

    hits = client.get("/api/rag/search", params={"q": "折弯"}, headers=headers("designer")).json()
    assert hits
    assert hits[0]["title"] == "折弯工艺"
    assert "折弯" in hits[0]["snippet"]

    assert client.post(
        "/api/rag/documents",
        json={"title": "x", "content": "y"},
        headers=headers("viewer"),
    ).status_code == 403
