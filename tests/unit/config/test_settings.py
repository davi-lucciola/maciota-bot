import pytest
from pydantic import ValidationError

from maciota_bot.config import Settings


def test_settings_reads_discord_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('DISCORD_TOKEN', 'abc')

    settings = Settings()

    assert settings.discord_token.get_secret_value() == 'abc'


def test_settings_rejects_a_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv('DISCORD_TOKEN', raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)
