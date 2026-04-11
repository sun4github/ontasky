from functools import cached_property

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    DB_HOST: str
    DB_PORT: int = 5432
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str

    # Application
    APP_TITLE: str = "Ontasky"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # JWT
    JWT_SECRET_KEY: str = "dev-only-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    JWT_AUDIENCE: str | None = None
    JWT_ISSUER: str | None = None
    JWT_ALLOW_NON_EXPIRING_AGENT_TOKENS: bool = False

    @cached_property
    def db_conninfo(self) -> str:
        return (
            f"host={self.DB_HOST} "
            f"port={self.DB_PORT} "
            f"dbname={self.DB_NAME} "
            f"user={self.DB_USER} "
            f"password={self.DB_PASSWORD}"
        )


settings = Settings()
