from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "电商数据分析助手"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://analytics:analytics_dev@localhost:5432/analytics_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # LLM
    LLM_API_URL: str = "http://localhost:11434/v1/chat/completions"  # Ollama default
    LLM_API_KEY: str = "ollama"
    LLM_MODEL: str = "llama2"

    # File Upload
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS: set = {".csv", ".xlsx", ".xls", ".json"}
    STORAGE_PATH: str = "storage/uploads"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
