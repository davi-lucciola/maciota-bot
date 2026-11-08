from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
    )

    discord_token: SecretStr
    database_url: str = 'sqlite:///data/maciota.db'
    openrouter_api_url: str = 'https://openrouter.ai/api/v1'
    openrouter_api_key: SecretStr = SecretStr('')
    llm_model: str = 'openai/gpt-4o-mini'
    llm_light_model: str = 'openai/gpt-4o-mini'
    checkpoint_path: str = 'data/checkpoints.db'
    log_level: LogLevel = 'INFO'


settings = Settings()
