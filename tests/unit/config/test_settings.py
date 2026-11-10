import pytest
from pydantic import ValidationError

from maciota_bot.config import Settings


def test_settings_reads_discord_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('DISCORD_TOKEN', 'abc')

    settings = Settings()

    assert settings.discord_token.get_secret_value() == 'abc'


def test_settings_defaults_log_level_to_info(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv('DISCORD_TOKEN', 'abc')
    monkeypatch.delenv('LOG_LEVEL', raising=False)

    settings = Settings(_env_file=None)

    assert settings.log_level == 'INFO'


def test_settings_reads_log_level(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('DISCORD_TOKEN', 'abc')
    monkeypatch.setenv('LOG_LEVEL', 'DEBUG')

    settings = Settings(_env_file=None)

    assert settings.log_level == 'DEBUG'


def test_settings_ignores_unknown_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('DISCORD_TOKEN', 'abc')
    monkeypatch.setenv('LANGSMITH_TRACING', 'true')

    settings = Settings(_env_file=None)

    assert settings.discord_token.get_secret_value() == 'abc'


def test_settings_rejects_a_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv('DISCORD_TOKEN', raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)
