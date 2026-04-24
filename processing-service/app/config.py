from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str = "redis://redis:6379"
    CLAUDE_API_KEY: str
    MISTRAL_API_KEY: str
    # AWS / S3 (use AWS_ENDPOINT_URL for local MinIO dev)
    AWS_REGION: str = "ca-central-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET: str = "architect-ledger-docs"
    AWS_ENDPOINT_URL: str = ""  # set to http://localhost:9000 for MinIO
    SENDGRID_API_KEY: str = ""
    EMAIL_FROM: str = "noreply@architectledger.com"
    XERO_CLIENT_ID: str = ""
    XERO_CLIENT_SECRET: str = ""
    # Fernet key for encrypting OAuth tokens at rest (base64-url-encoded 32 bytes)
    TOKEN_ENCRYPTION_KEY: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
