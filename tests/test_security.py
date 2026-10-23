import pytest

from app import security


def test_production_requires_strong_secret(monkeypatch):
    monkeypatch.setattr(security, "APP_ENV", "production")
    monkeypatch.setattr(security, "SECRET_KEY", "dev-secret-change-me")
    monkeypatch.setattr(security, "ALLOW_DEV_AUTH", False)
    monkeypatch.setattr(security, "WECOM_MODE", "mock")
    with pytest.raises(RuntimeError):
        security.validate_config()

    monkeypatch.setattr(security, "SECRET_KEY", "a-very-long-random-secret")
    security.validate_config()


def test_production_requires_dev_auth_off(monkeypatch):
    monkeypatch.setattr(security, "APP_ENV", "production")
    monkeypatch.setattr(security, "SECRET_KEY", "a-very-long-random-secret")
    monkeypatch.setattr(security, "ALLOW_DEV_AUTH", True)
    monkeypatch.setattr(security, "WECOM_MODE", "mock")
    with pytest.raises(RuntimeError):
        security.validate_config()
