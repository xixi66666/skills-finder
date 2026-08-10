import pytest

from app.core.config import Settings


def test_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "mysql+asyncmy://user:pass@localhost/db")
    monkeypatch.setenv("GITHUB_TOKEN", "secret-token")
    settings = Settings(_env_file=None)
    assert settings.business_timezone == "Asia/Shanghai"
    assert settings.min_stars == 100
    assert settings.scheduler_enabled is False
    assert "secret-token" not in repr(settings)
