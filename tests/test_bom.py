from .conftest import headers


def _new_generated_drawing(client, no: str) -> int:
    project_id = client.get("/api/projects", headers=headers("admin")).json()[0]["id"]
    drawing = client.post(
        "/api/drawings",
        json={"project_id": project_id, "drawing_no": no, "title": "BOM 测试件"},
        headers=headers("designer"),
    ).json()
    drawing_id = drawing["id"]
    payload = {
        "length": 180,
        "width": 120,
        "thickness": 6,
        "material": "304",
        "surface": "拉丝",
        "holes": [
            {"x": 20, "y": 20, "d": 6.6},
            {"x": 160, "y": 20, "d": 6.6},
        ],
    }
    gen = client.post(f"/api/drawings/{drawing_id}/generate", json=payload, headers=headers("designer"))
    assert gen.status_code == 200
    job_id = gen.json()["job_id"]
    job = client.get(f"/api/jobs/{job_id}", headers=headers("designer")).json()
    assert job["status"] == "done", job
    return drawing_id


def test_export_bom(client):
    drawing_id = _new_generated_drawing(client, "SW-2026-201")

    resp = client.get(f"/api/drawings/{drawing_id}/bom", headers=headers("designer"))
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert "attachment" in resp.headers["content-disposition"]
    assert "SW-2026-201-bom.csv" in resp.headers["content-disposition"]

    text = resp.text
    assert "图号,名称,材料,表面,长度mm,宽度mm,厚度mm,孔数,孔位" in text
    assert "SW-2026-201" in text
    assert "BOM 测试件" in text
    assert "孔数" in text


def test_export_bom_not_found(client):
    resp = client.get("/api/drawings/999999/bom", headers=headers("designer"))
    assert resp.status_code == 404
