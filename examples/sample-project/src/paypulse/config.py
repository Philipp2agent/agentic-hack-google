import os
from dataclasses import dataclass

@dataclass
class Settings:
    environment: str = os.getenv("PAYPULSE_ENV", "development")
    port: int = int(os.getenv("PORT", "8000"))
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    stripe_webhook_secret: str = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_sample_secret_key")
    idempotency_ttl_seconds: int = int(os.getenv("IDEMPOTENCY_TTL_SECONDS", "172800"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))

settings = Settings()
