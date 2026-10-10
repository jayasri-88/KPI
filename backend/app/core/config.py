from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"


class Settings(BaseSettings):
    app_name: str = "Retail KPI Intelligence Platform"
    app_version: str = "1.0.0"
    api_v1_str: str = "/api/v1"
    environment: str = "development"
    debug: bool = True

    # Database
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/retail_kpi",
        alias="DATABASE_URL",
    )

    # Security & JWT
    secret_key: str = Field(
        default="retail_kpi_super_secret_jwt_key_2026_change_in_production",
        alias="SECRET_KEY",
    )
    jwt_secret: str = Field(
        default="retail_kpi_super_secret_jwt_key_2026_change_in_production",
        alias="JWT_SECRET",
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # AI & Caching
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    @property
    def GEMINI_API_KEY(self) -> str:
        return self.gemini_api_key

    # CORS
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_db_url(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql://", 1)
        return v

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if not v.strip():
                return ["http://localhost:5173", "http://127.0.0.1:5173"]
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=(_ENV_FILE, ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


settings = Settings()