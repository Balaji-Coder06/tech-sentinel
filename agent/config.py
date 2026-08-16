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
    
    # AI Providers (Zero-cost / Free Tier first)
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "auto")  # options: auto, groq, gemini, local, fallback
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    LOCAL_AI_BASE_URL: str = os.getenv("LOCAL_AI_BASE_URL", "http://localhost:11434/v1")
    LOCAL_AI_MODEL: str = os.getenv("LOCAL_AI_MODEL", "llama3.2")
    AI_REQUEST_DELAY_SECONDS: float = float(os.getenv("AI_REQUEST_DELAY_SECONDS", "0.5"))
    AI_MAX_RETRIES: int = int(os.getenv("AI_MAX_RETRIES", "3"))
    AI_RETRY_BASE_DELAY_SECONDS: float = float(os.getenv("AI_RETRY_BASE_DELAY_SECONDS", "2.0"))
    AI_RETRY_MAX_DELAY_SECONDS: float = float(os.getenv("AI_RETRY_MAX_DELAY_SECONDS", "15.0"))
    
    # Notifications
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    
    # Web / App URL
    APP_BASE_URL: str = os.getenv("APP_BASE_URL", "http://localhost:3000")
    WEB_APP_URL: str = os.getenv("WEB_APP_URL", "")  # Optional public HTTPS URL for Telegram buttons
    
    # Ingestion Configuration
    REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "15"))
    MAX_ITEMS_PER_SOURCE: int = int(os.getenv("MAX_ITEMS_PER_SOURCE", "15"))
    USER_AGENT: str = os.getenv(
        "USER_AGENT",
        "Mozilla/5.0 (compatible; TechSentinelBot/1.0; +https://github.com/Balaji-Coder06/tech-sentinel)"
    )

settings = Settings()
