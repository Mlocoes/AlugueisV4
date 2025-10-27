from pydantic_settings import BaseSettings
from typing import Optional
import json
from pydantic import validator
from os import getenv

class Settings(BaseSettings):
    database_url: str = getenv("DATABASE_URL", "postgresql://alugueis_user:alugueis_password@localhost:5432/alugueis")
    # NOTE: do not leave a default secret_key for production
    secret_key: str = getenv("SECRET_KEY", None)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    allowed_origins: list[str] = ["http://localhost:8000"]

    @validator("allowed_origins", pre=True)
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # Handle comma-separated string as a fallback
                return [origin.strip() for origin in v.split(',')]
        return v
    class Config:
        env_file = ".env"
        extra = 'ignore'

settings = Settings()
# Runtime environment
APP_ENV = getenv("APP_ENV", "development").lower()

# Safety checks
insecure_secrets = (settings.secret_key is None or settings.secret_key in ("your-secret-key-here", "changeme", ""))
if APP_ENV == 'production':
    # In production fail fast on insecure configuration
    if insecure_secrets:
        raise RuntimeError("SECRET_KEY is not set or is insecure. Set SECRET_KEY environment variable before starting the application in production.")
    if not settings.allowed_origins:
        raise RuntimeError("ALLOWED_ORIGINS is not set. Configure ALLOWED_ORIGINS appropriately for production.")
else:
    # Development: warn but don't stop
    if insecure_secrets:
        print("WARNING: SECRET_KEY is not set or insecure. Set environment variable SECRET_KEY for production deployments.")