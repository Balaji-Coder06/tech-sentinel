import re
import time
import logging
from typing import Optional
import httpx
from ..config import settings

logger = logging.getLogger(__name__)

def parse_retry_after(response: Optional[httpx.Response], default_delay: float) -> float:
    """Extracts wait duration from Retry-After header or response error body."""
    if response is None:
        return default_delay

    # 1. Try standard Retry-After header
    try:
        retry_header = response.headers.get("Retry-After") or response.headers.get("retry-after")
        if retry_header:
            delay = float(retry_header.strip())
            return min(max(delay, 0.5), settings.AI_RETRY_MAX_DELAY_SECONDS)
    except Exception:
        pass

    # 2. Try parsing error payload message for wait advice (e.g. 'try again in 2.5s')
    try:
        data = response.json()
        error_msg = ""
        if isinstance(data, dict):
            error_msg = str(data.get("error", {}).get("message", "") or data.get("message", ""))
        match = re.search(r"try again in ([0-9]+(?:\.[0-9]+)?)s", error_msg, re.IGNORECASE)
        if match:
            delay = float(match.group(1))
            return min(max(delay, 0.5), settings.AI_RETRY_MAX_DELAY_SECONDS)
    except Exception:
        pass

    return min(max(default_delay, 0.5), settings.AI_RETRY_MAX_DELAY_SECONDS)

def apply_pacing_delay():
    """Applies a configurable pacing delay between requests to avoid RPM bursts."""
    delay = getattr(settings, "AI_REQUEST_DELAY_SECONDS", 0.5)
    if delay > 0:
        time.sleep(delay)
