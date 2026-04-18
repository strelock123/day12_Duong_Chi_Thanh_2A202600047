from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    environment: str = "development"
    debug: bool = False

    # App
    app_name: str = "Production AI Agent"
    app_version: str = "1.0.0"

    # LLM
    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"

    # Security
    agent_api_key: str = "dev-key-change-me"
    allowed_origins: list = ["*"]

    # Rate limiting
    rate_limit_per_minute: int = 10

    # Budget
    monthly_budget_usd: float = 10.0

    # Storage
    redis_url: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()
