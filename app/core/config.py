"""Centralised configuration (pydantic-settings). All secrets come from env."""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "E-Commerce Backend API"
    APP_ENV: str = "dev"
    API_V1_PREFIX: str = "/api/v1"

    SECRET_KEY: str = "change-me-to-a-long-random-string-min-32-chars"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str = "postgresql+psycopg2://ecom:ecom@localhost:5432/ecom"
    REDIS_URL: str = "redis://localhost:6379/0"

    EMAIL_MODE: str = "console"
    SMTP_FROM: str = "noreply@example.com"
    FRONTEND_URL: str = "http://localhost:3000"

    FAILED_LOGIN_LIMIT: int = 5

    # --- M2: pricing / checkout ---
    TAX_RATE: float = 0.08
    SHIPPING_FLAT: float = 4.0
    FREE_SHIPPING_THRESHOLD: float = 50.0
    # --- M2: payments ---
    PAYMENT_GATEWAY: str = "mock"  # mock | stripe (stripe used only if STRIPE_API_KEY is real)
    STRIPE_API_KEY: str = "sk_test_placeholder"
    STRIPE_WEBHOOK_SECRET: str = "whsec_placeholder"
    WEBHOOK_SECRET: str = "dev-webhook-secret-change-me"
    SUPPORT_REFUND_LIMIT: float = 100.0
    # --- M2: reservation ---
    RESERVATION_TTL_MINUTES: int = 15

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
