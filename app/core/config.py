from pydantic_settings import BaseSettings
from typing import Optional

from os import getenv

class Settings(BaseSettings):
    database_url: str = getenv("DATABASE_URL", "postgresql://alugueis_user:alugueis_password@localhost:5432/alugueis")
    secret_key: str = getenv("SECRET_KEY", "your-secret-key-here")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    allowed_origins: list[str] = ["*"]

    class Config:
        env_file = ".env"
        extra = 'ignore'

settings = Settings()