from tools.check_integrations import collect_checks


def test_collect_checks_reports_all(monkeypatch):
    for key in (
        "ODA_FILE_CONVERTER",
        "DWG2DXF_BIN",
        "CAD_ADAPTER_SOLIDWORKS",
        "CAD_ADAPTER_ALTIUM",
        "COMFY_URL",
        "COMFY_WORKFLOW",
        "LLM_BASE_URL",
        "LLM_API_KEY",
        "ERP_WEBHOOK_URL",
        "WECOM_MODE",
        "WECOM_TOKEN",
        "WECOM_ENCODING_AES_KEY",
        "STORAGE_BACKEND",
        "S3_BUCKET",
        "VIRUS_SCAN_MODE",
    ):
        monkeypatch.delenv(key, raising=False)

    checks = collect_checks()
    names = {item["name"] for item in checks}
    assert "DWG 转换" in names
    assert "ComfyUI" in names
    assert "企业微信" in names
    assert any(not item["ok"] for item in checks)
