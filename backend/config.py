from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    media_root: str
    storage_backend: str = "disk"
    redis_url: str
    whisper_model: str = "base"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
