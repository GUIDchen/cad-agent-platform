from app import comfy


class Resp:
    def __init__(self, payload=None, content=b""):
        self._payload = payload or {}
        self.content = content

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_prepare_workflow_nested():
    template = {"1": {"inputs": {"text": "{{PROMPT}}", "width": "{{WIDTH}}", "height": "{{HEIGHT}}"}}}
    result = comfy.prepare_workflow(template, "机械板", 512, 384)
    assert result["1"]["inputs"] == {"text": "机械板", "width": "512", "height": "384"}


def test_comfy_generate(monkeypatch):
    monkeypatch.setattr(comfy, "COMFY_URL", "http://comfy:8188")
    monkeypatch.setattr(comfy, "COMFY_WORKFLOW", "unused.json")
    monkeypatch.setattr(
        comfy, "_load_workflow", lambda: {"1": {"inputs": {"text": "{{PROMPT}}"}}}
    )

    captured = {}

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["prompt"] = json["prompt"]
        return Resp({"prompt_id": "p1"})

    def fake_get(url, params=None, timeout=10):
        if "/history/" in url:
            return Resp({"p1": {"outputs": {"9": {"images": [{"filename": "a.png"}]}}}})
        return Resp(content=b"PNG-BYTES")

    monkeypatch.setattr(comfy.httpx, "post", fake_post)
    monkeypatch.setattr(comfy.httpx, "get", fake_get)

    assert comfy.generate("机械板", 512, 384) == b"PNG-BYTES"
    assert captured["prompt"]["1"]["inputs"]["text"] == "机械板"


def test_prepare_workflow_negative_seed():
    template = {"neg": "{{NEGATIVE}}", "seed": "{{SEED}}"}
    result = comfy.prepare_workflow(template, "机械板", 512, 384, "低质量", 42)
    assert result == {"neg": "低质量", "seed": "42"}


def test_load_workflow_rejects_invalid(monkeypatch, tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(comfy, "COMFY_WORKFLOW", str(path))
    try:
        comfy._load_workflow()
    except RuntimeError as exc:
        assert "工作流" in str(exc)
    else:
        raise AssertionError("应当拒绝空工作流")
