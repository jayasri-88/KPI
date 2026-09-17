from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    app_name: str = "Retail KPI Intelligence Platform"
    environment: str = "development"
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/retail_kpi",
        alias="DATABASE_URL",
    )
    postgres_database: str = "retail_kpi"
    jwt_secret: str = Field(default="change_this_to_a_long_random_secret_12345")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    gemini_api_key: str = ""
    redis_url: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()