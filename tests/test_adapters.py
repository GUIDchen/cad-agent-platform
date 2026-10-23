import sys
from pathlib import Path

from .conftest import headers

ADAPTER = Path(__file__).parent / "fixtures" / "fake_adapter.py"


def _create_drawing(client, no: str) -> int:
    project_id = client.get("/api/projects", headers=headers("admin")).json()[0]["id"]
    drawing = client.post(
        "/api/drawings",
        json={"project_id": project_id, "drawing_no": no, "title": "适配器测试"},
        headers=headers("designer"),
    ).json()
    return drawing["id"]


def _payload(job_type: str) -> dict:
    return {
        "job_type": job_type,
        "length": 180,
        "width": 120,
        "thickness": 6,
        "material": "304",
        "surface": "拉丝",
        "holes": [{"x": 20, "y": 20, "d": 6.6}, {"x": 160, "y": 100, "d": 6.6}],
    }


def test_external_adapter(client, monkeypatch):
    monkeypatch.setenv("CAD_ADAPTER_SOLIDWORKS", f"{sys.executable} {ADAPTER}")
    drawing_id = _create_drawing(client, "SW-2026-301")
    gen = client.post(
        f"/api/drawings/{drawing_id}/generate",
        json=_payload("generate_solidworks"),
        headers=headers("designer"),
    )
    assert gen.status_code == 200
    job = client.get(f"/api/jobs/{gen.json()['job_id']}", headers=headers("designer")).json()
    assert job["status"] == "done", job
    versions = client.get(f"/api/drawings/{drawing_id}/versions", headers=headers("designer")).json()
    assert len(versions) == 1


def test_external_adapter_missing(client, monkeypatch):
    monkeypatch.delenv("CAD_ADAPTER_ALTIUM", raising=False)
    drawing_id = _create_drawing(client, "SW-2026-302")
    gen = client.post(
        f"/api/drawings/{drawing_id}/generate",
        json=_payload("generate_altium"),
        headers=headers("designer"),
    )
    assert gen.status_code == 200
    job = client.get(f"/api/jobs/{gen.json()['job_id']}", headers=headers("designer")).json()
    assert job["status"] == "failed"
    assert "未配置" in (job["error"] or "")
