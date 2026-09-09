from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    environment: str = "development"
    database_url: str = "postgresql+psycopg://arbitra:local-only@localhost:5432/arbitra"
    frontend_url: str = "http://localhost:5173"
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    session_hours: int = 8
    pool_size: int = 5
    pool_overflow: int = 5

    @model_validator(mode="after")
    def production_safety(self):
        if self.cookie_samesite not in {"lax", "strict", "none"}:
            raise ValueError("COOKIE_SAMESITE inválido")
        if self.cookie_samesite == "none" and not self.cookie_secure:
            raise ValueError("SameSite=None exige HTTPS")
        if self.environment == "production":
            if not self.cookie_secure or not self.frontend_url.startswith("https://"):
                raise ValueError("Produção exige HTTPS e cookies seguros")
            if "local-only" in self.database_url:
                raise ValueError("Configure a credencial de produção")
        return self


@lru_cache
def settings() -> Settings:
    return Settings()
