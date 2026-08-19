from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
    
    # Required. The app refuses to start without it.
    database_url: str
    
    # Optional. Only the test suite needs it
    test_database_url: str | None = None
    
    # The expiring-soon window: its default and its cap.
    default_expiry_window_days: int = 30
    max_expiry_window_days: int = 365
    
    @field_validator("database_url", "test_database_url")
    @classmethod
    def use_psycopg_driver(cls, v: str | None) -> str | None:
        """Neon hands out 'postgresql://'. SQLAlchemy then picks
        psycopg2, which is not installed. Force psycopg v3."""
        if v is None:
            return v
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+psycopg://", 1)
        return v
        
settings = Settings()