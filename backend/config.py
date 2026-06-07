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
    b2_endpoint_url: str | None = None
    b2_access_key_id: str | None = None
    b2_secret_access_key: str | None = None
    b2_bucket_name: str | None = None

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
