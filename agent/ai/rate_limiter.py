import re
import time
import logging
from typing import Optional
import httpx
from ..config import settings

logger = logging.getLogger(__name__)

_last_request_timestamp: float = 0.0

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

def apply_global_pacing(min_interval: Optional[float] = None):
    """Enforces a global minimum interval between consecutive outbound AI requests."""
    global _last_request_timestamp
    target_interval = min_interval if min_interval is not None else getattr(settings, "AI_REQUEST_DELAY_SECONDS", 2.0)

    if target_interval > 0 and _last_request_timestamp > 0:
        elapsed = time.time() - _last_request_timestamp
        remaining = target_interval - elapsed
        if remaining > 0:
            logger.debug(f"⏱️ [AI Pacing] Waiting {remaining:.2f}s before next request (target interval: {target_interval:.1f}s)...")
            time.sleep(remaining)

    _last_request_timestamp = time.time()

def record_request_completed():
    """Updates the global timestamp when a request finishes to maintain accurate pacing."""
    global _last_request_timestamp
    _last_request_timestamp = time.time()

def reset_global_pacing():
    """Resets global pacing timestamp for testing."""
    global _last_request_timestamp
    _last_request_timestamp = 0.0
