from functools import lru_cache
from pydantic import BaseSettings


class Settings(BaseSettings):
  # App
  APP_NAME: str = "TTS Backend"
  API_PREFIX: str = "/api"
  ENV: str = "dev"
  DEBUG: bool = True

  # Security
  SECRET_KEY: str = "change-me"
  JWT_ALGORITHM: str = "HS256"
  ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
  REFRESH_TOKEN_EXPIRE_DAYS: int = 7

  # Database
  DATABASE_URL: str = "sqlite:///./data/app.db"

  # Redis (optional, not required now)
  REDIS_HOST: str = "localhost"
  REDIS_PORT: int = 6379
  REDIS_DB: int = 0
  REDIS_PASSWORD: str | None = None

  # OSS (optional, placeholder)
  OSS_ACCESS_KEY_ID: str | None = None
  OSS_ACCESS_KEY_SECRET: str | None = None
  OSS_BUCKET_NAME: str | None = None
  OSS_ENDPOINT: str | None = None

  class Config:
    env_file = ".env"
    case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
  return Settings()


settings = get_settings()
