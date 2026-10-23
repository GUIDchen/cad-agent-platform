import json
from pathlib import Path

from tools.rag_vector_export import export_vectors

from .conftest import headers


def test_export_vectors(client, tmp_path: Path):
    client.post(
        "/api/rag/documents",
        json={"title": "导出", "content": "折弯工艺。" * 80},
        headers=headers("designer"),
    )
    out = tmp_path / "vectors.jsonl"
    report = export_vectors(out)
    assert report["chunks"] >= 1
    lines = out.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == report["chunks"]
    row = json.loads(lines[0])
    assert {"doc_id", "chunk_index", "content", "embedding"} <= set(row)
    assert row["embedding"]
