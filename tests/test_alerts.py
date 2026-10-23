def test_alert_webhook(client, tmp_path, monkeypatch):
    monkeypatch.setenv("NOTIFY_MODE", "mock")
    monkeypatch.setenv("NOTIFY_LOG", str(tmp_path / "alerts.log"))
    payload = {
        "alerts": [
            {
                "status": "firing",
                "labels": {"alertname": "CadApiDown", "severity": "critical"},
                "annotations": {"summary": "api down"},
            }
        ]
    }
    resp = client.post(
        "/api/alerts", json=payload, headers={"X-Alert-Token": "dev-alert-token"}
    )
    assert resp.status_code == 200
    assert resp.json()["count"] == 1
    text = (tmp_path / "alerts.log").read_text(encoding="utf-8")
    assert "CadApiDown" in text
    assert "api down" in text

    resolved = {
        "alerts": [
            {
                "status": "resolved",
                "labels": {"alertname": "CadApiDown", "severity": "critical"},
                "annotations": {"summary": "api up"},
            }
        ]
    }
    assert (
        client.post(
            "/api/alerts", json=resolved, headers={"X-Alert-Token": "dev-alert-token"}
        ).status_code
        == 200
    )
    assert "告警恢复" in (tmp_path / "alerts.log").read_text(encoding="utf-8")

    assert (
        client.post("/api/alerts", json=payload, headers={"X-Alert-Token": "bad"}).status_code
        == 401
    )
