"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration using pydantic-settings.

    Values are loaded from environment variables or a .env file.
    """

    # Database
    database_url: str = (
        "postgresql://erpdsl:erpdsl@localhost:5432/erpdsl"
    )

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480  # 8 hours

    # App
    app_name: str = "AutoSystem"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = {"env_prefix": "ERP_", "env_file": ".env"}


settings = Settings()
