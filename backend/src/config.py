from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = "postgresql://engels:engels_secure_password_change_me@localhost:5432/engels"

    # PostgreSQL (for Docker Compose)
    postgres_user: str = "engels"
    postgres_password: str = "engels_secure_password_change_me"
    postgres_db: str = "engels"

    # Redis/Celery
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    redis_url: str = "redis://localhost:6379/0"

    # Ollama
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"
    ollama_num_parallel: int = 2
    ollama_keep_alive: str = "5m"

    # Strapi
    strapi_jwt_secret: str = "strapi_jwt_secret_change_me"
    strapi_api_token_salt: str = "strapi_api_token_salt_change_me"
    strapi_admin_jwt_secret: str = "strapi_admin_jwt_secret_change_me"

    # MCP (Model Context Protocol)
    mcp_enabled: bool = False
    mcp_endpoint: str | None = None

    # Security
    log_raw_data: bool = False  # Never log raw text, embeddings, or token maps

    # Application
    log_level: str = "INFO"
    environment: str = "development"
    node_env: str = "development"
    api_url: str = "http://localhost:1337"

    # Frontend
    vite_api_url: str = "http://localhost:1337"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields from .env file


settings = Settings()
