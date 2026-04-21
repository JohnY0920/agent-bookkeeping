from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str = "redis://redis:6379"
    CLAUDE_API_KEY: str
    MISTRAL_API_KEY: str
    GCS_BUCKET: str = "architect-ledger-docs"
    GCS_PROJECT_ID: str = ""
    SENDGRID_API_KEY: str = ""
    EMAIL_FROM: str = "noreply@architectledger.com"
    XERO_CLIENT_ID: str = ""
    XERO_CLIENT_SECRET: str = ""

    model_config = {"env_file": ".env"}


settings = Settings()
