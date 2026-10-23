from .conftest import headers


def test_document_versions_and_restore(client):
    created = client.post(
        "/api/rag/documents",
        json={"title": "版本一", "content": "第一版内容。" * 30},
        headers=headers("designer"),
    ).json()

    client.patch(
        "/api/rag/documents/" + str(created["id"]),
        json={"title": "版本二", "content": "第二版内容。" * 30},
        headers=headers("designer"),
    )

    versions = client.get(
        "/api/rag/documents/" + str(created["id"]) + "/versions",
        headers=headers("designer"),
    ).json()
    assert len(versions) == 1
    assert versions[0]["title"] == "版本一"

    restored = client.post(
        "/api/rag/documents/" + str(created["id"]) + "/versions/" + str(versions[0]["id"]) + "/restore",
        headers=headers("designer"),
    )
    assert restored.status_code == 200
    assert restored.json()["title"] == "版本一"
