import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# Resolve project root directory and load .env regardless of current working directory
_ROOT_DIR = Path(__file__).resolve().parent.parent
_ENV_FILE = _ROOT_DIR / ".env"
if _ENV_FILE.exists():
    load_dotenv(dotenv_path=_ENV_FILE, override=False)
else:
    load_dotenv(override=False)

class Settings(BaseModel):
    # Storage & DB
    BASE_DIR: Path = _ROOT_DIR
    DATABASE_PATH: str = os.getenv(
        "DATABASE_PATH",
        str(_ROOT_DIR / "database" / "tech_sentinel.db")
    )

    # Cloudflare Worker / D1 Ingestion Bridge (for GitHub Actions -> D1 production sync)
    WORKER_API_URL: str = os.getenv("WORKER_API_URL", "")  # e.g., https://tech-sentinel-api.your-subdomain.workers.dev
    INGESTION_SECRET: str = os.getenv("INGESTION_SECRET", "")  # Secret token shared between GH Actions & Worker
    
    # Notifications & Delivery
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    
    # Generic SMTP / Gmail Email Delivery
    SMTP_HOST: str = os.getenv("SMTP_HOST") or "smtp.gmail.com"
    SMTP_PORT: int = int(os.getenv("SMTP_PORT") or "587")
    SMTP_USER: str = os.getenv("SMTP_USER") or os.getenv("GMAIL_USER") or os.getenv("EMAIL_USER") or ""
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD") or os.getenv("GMAIL_APP_PASSWORD") or os.getenv("EMAIL_PASSWORD") or ""
    SMTP_USE_TLS: bool = (os.getenv("SMTP_USE_TLS") or "true").lower() in ("true", "1", "yes")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM") or os.getenv("SMTP_USER") or os.getenv("GMAIL_USER") or ""
    EMAIL_TO: str = os.getenv("EMAIL_TO") or os.getenv("NEWSLETTER_EMAIL") or ""
    
    # Web / App URL
    APP_BASE_URL: str = os.getenv("APP_BASE_URL") or "https://tech-sentinel-chi.vercel.app"
    WEB_APP_URL: str = os.getenv("WEB_APP_URL") or os.getenv("APP_BASE_URL") or "https://tech-sentinel-chi.vercel.app"  # Canonical public HTTPS URL for links & Telegram buttons
    
    # Ingestion Configuration
    REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "15"))
    MAX_ITEMS_PER_SOURCE: int = int(os.getenv("MAX_ITEMS_PER_SOURCE", "15"))
    USER_AGENT: str = os.getenv(
        "USER_AGENT",
        "Mozilla/5.0 (compatible; TechSentinelBot/1.0; +https://github.com/Balaji-Coder06/tech-sentinel)"
    )

settings = Settings()
