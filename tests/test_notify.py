from app import notify
from app.notify import approval_card, notify_job_done, retry_dead_letters, send


def test_mock_notify(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTIFY_MODE", "mock")
    monkeypatch.setenv("NOTIFY_LOG", str(tmp_path / "n.log"))
    notify_job_done("SW-2026-001", 2)
    text = (tmp_path / "n.log").read_text(encoding="utf-8")
    assert "SW-2026-001" in text
    assert "v2" in text
    send("hello")
    assert "hello" in (tmp_path / "n.log").read_text(encoding="utf-8")


def test_approval_card():
    card = approval_card("SW-2026-001", 2, 7)
    assert card["card_type"] == "text_notice"
    keys = [button["key"] for button in card["button_list"]]
    assert "approve:7" in keys
    assert "reject:7" in keys


def test_dead_letter_and_retry(tmp_path, monkeypatch):
    monkeypatch.setenv("NOTIFY_MODE", "wecom")
    monkeypatch.setenv("WECOM_WEBHOOK", "http://example.invalid/hook")
    monkeypatch.setenv("NOTIFY_DEAD_LETTER", str(tmp_path / "dead.jsonl"))

    def fail(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(notify.httpx, "post", fail)
    assert send("hello") is False
    assert (tmp_path / "dead.jsonl").exists()

    class Resp:
        status_code = 200

    monkeypatch.setattr(notify.httpx, "post", lambda *a, **k: Resp())
    assert retry_dead_letters() == (1, 0)
    assert (tmp_path / "dead.jsonl").read_text(encoding="utf-8") == ""
