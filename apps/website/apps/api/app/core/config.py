from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_SECRET_KEYS = {"change-me", "change-me-in-env", "replace-me-for-production"}


class Settings(BaseSettings):
    app_name: str = "AiMO API"
    app_env: str = "development"
    secret_key: str = "change-me-in-env"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    database_url: str = "postgresql+psycopg://aimo:aimo@db:5432/aimo"
    sql_echo: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def reject_default_secret_outside_development(self) -> "Settings":
        if self.app_env != "development" and self.secret_key in INSECURE_SECRET_KEYS:
            raise ValueError("SECRET_KEY must be unique when APP_ENV is not 'development'")
        return self

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
