from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
    )

    discord_token: SecretStr
    database_url: str = 'sqlite:///maciota.db'


settings = Settings()
