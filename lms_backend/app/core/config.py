
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = "PAY CREST API"
    API_PREFIX: str = "/api"
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "pay_crest"

    JWT_SECRET: str = "CHANGE_ME"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24

    DEFAULT_IFSC: str = "PCIN01001"

    # Cashfree (Payment Gateway)
    CASHFREE_ENV: str = "sandbox"  # sandbox | production
    CASHFREE_CLIENT_ID: Optional[str] = None
    CASHFREE_CLIENT_SECRET: Optional[str] = None
    CASHFREE_API_VERSION: str = "2023-08-01"
    CASHFREE_RETURN_URL: str = "http://localhost:5173/customer/dashboard"
    CASHFREE_RETURN_URL_WALLET: str = "http://localhost:5173/customer/wallet"
    CASHFREE_RETURN_URL_EMI: str = "http://localhost:5173/customer/emi"
    CASHFREE_WEBHOOK_URL: str = "http://localhost:8010/api/payments/cashfree/webhook"
    CASHFREE_ORDER_PREFIX: str = "pc_emi_"
    CASHFREE_HTTP_TIMEOUT_SECONDS: int = 20

    # Idempotency
    IDEMPOTENCY_ENABLED: bool = True
    IDEMPOTENCY_TTL_HOURS: int = 24

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
