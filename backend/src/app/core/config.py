from functools import lru_cache
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    environment: Literal["development", "test", "production"] = "development"
    database_url: str
    frontend_url: str = "http://localhost:5173"
    cookie_secure: bool = False
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    session_hours: int = Field(default=8, ge=1, le=168)
    pool_size: int = Field(default=5, ge=1, le=20)
    pool_overflow: int = Field(default=5, ge=0, le=20)
    smtp_host: str | None = None
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_starttls: bool = True

    @model_validator(mode="after")
    def production_safety(self):
        origin = urlsplit(self.frontend_url)
        if (
            origin.scheme not in {"http", "https"}
            or not origin.netloc
            or origin.username
            or origin.password
            or origin.query
            or origin.fragment
            or origin.path not in {"", "/"}
        ):
            raise ValueError("FRONTEND_URL deve conter somente a origem HTTP(S)")
        self.frontend_url = self.frontend_url.rstrip("/")
        if self.database_url.startswith("postgresql://"):
            self.database_url = self.database_url.replace(
                "postgresql://", "postgresql+psycopg://", 1
            )
        elif self.database_url.startswith("postgres://"):
            self.database_url = self.database_url.replace("postgres://", "postgresql+psycopg://", 1)
        if not self.database_url.startswith("postgresql+psycopg://"):
            raise ValueError("DATABASE_URL deve usar PostgreSQL com psycopg")
        if self.cookie_samesite == "none" and not self.cookie_secure:
            raise ValueError("SameSite=None exige HTTPS")
        if self.environment == "production":
            if not self.cookie_secure or origin.scheme != "https":
                raise ValueError("Produção exige HTTPS e cookies seguros")
            if "local-only" in self.database_url:
                raise ValueError("Configure a credencial de produção")
            if not all((self.smtp_host, self.smtp_from)):
                raise ValueError("Produção exige SMTP")
            if not self.smtp_starttls:
                raise ValueError("Produção exige SMTP_STARTTLS=true")
        return self


@lru_cache
def settings() -> Settings:
    return Settings()
