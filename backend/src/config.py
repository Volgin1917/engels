import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql://engels:engels_secure_password_change_me@localhost:5432/engels"

    # Redis/Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # Ollama
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"
    ollama_num_parallel: int = 2

    # MCP (Model Context Protocol)
    mcp_enabled: bool = False
    mcp_endpoint: Optional[str] = None

    # Security
    log_raw_data: bool = False  # Never log raw text, embeddings, or token maps

    # Application
    log_level: str = "INFO"
    environment: str = "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
