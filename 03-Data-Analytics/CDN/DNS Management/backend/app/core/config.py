from functools import lru_cache

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    app_name: str = Field(default="CDN/DNS Management API", alias="APP_NAME")
    api_v1_prefix: str = Field(default="/api", alias="API_V1_PREFIX")
    project_env: str = Field(default="local", alias="PROJECT_ENV")
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/cdn_dns",
        alias="DATABASE_URL",
    )
    redis_url: str | None = Field(default=None, alias="REDIS_URL")
    secret_key: str = Field(default="local-secret-key", alias="SECRET_KEY")
    scheduler_timezone: str = Field(default="UTC", alias="SCHEDULER_TIMEZONE")

    godaddy_api_key: str | None = Field(default=None, alias="GODADDY_API_KEY")
    godaddy_api_secret: str | None = Field(default=None, alias="GODADDY_API_SECRET")
    godaddy_env: str = Field(default="production", alias="GODADDY_ENV")

    namecheap_api_user: str | None = Field(default=None, alias="NAMECHEAP_API_USER")
    namecheap_api_key: str | None = Field(default=None, alias="NAMECHEAP_API_KEY")
    namecheap_api_ip: str | None = Field(default=None, alias="NAMECHEAP_API_IP")
    namecheap_env: str = Field(default="sandbox", alias="NAMECHEAP_ENV")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
