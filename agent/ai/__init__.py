"""Tech Sentinel AI Engine Package."""
import logging
from .provider import BaseAIProvider
from .gemini_provider import GeminiProvider
from .groq_provider import GroqProvider
from .local_provider import LocalProvider
from .fallback_provider import FallbackProvider
from .summarizer import AISummarizer
from .digest_generator import DailyDigestGenerator
from ..config import settings

logger = logging.getLogger(__name__)

def get_ai_provider(name: str = None) -> BaseAIProvider:
    """Instantiates AI provider with clean cascading strategy:
    GROQ (Primary) -> Gemini (Fallback) -> Local Heuristics (Safety Net).
    """
    provider_name = (name or settings.AI_PROVIDER or "auto").strip().lower()

    fallback = FallbackProvider()
    gemini = GeminiProvider(fallback=fallback)
    groq = GroqProvider(fallback=gemini if settings.GEMINI_API_KEY else fallback)

    if provider_name in ("groq", "auto", "hybrid", "default"):
        if settings.GROQ_API_KEY:
            logger.info("🤖 [AI Strategy] Primary: Groq (Llama 3.3 70B) | Fallback: Gemini (2.5 Flash)")
            return groq
        elif settings.GEMINI_API_KEY:
            logger.info("🤖 [AI Strategy] Primary: Gemini (2.5 Flash) | Fallback: Deterministic NLP")
            return gemini
        logger.info("🤖 [AI Strategy] Using Deterministic Offline NLP (No API keys found)")
        return fallback
    elif provider_name == "gemini":
        gemini_with_groq = GeminiProvider(fallback=groq if settings.GROQ_API_KEY else fallback)
        if settings.GEMINI_API_KEY:
            logger.info("🤖 [AI Strategy] Primary: Gemini (2.5 Flash) | Fallback: Groq (Llama 3.3 70B)")
            return gemini_with_groq
        elif settings.GROQ_API_KEY:
            logger.info("🤖 [AI Strategy] Primary: Groq (Llama 3.3 70B) | Fallback: Deterministic NLP")
            return groq
        return fallback
    elif provider_name == "local":
        return LocalProvider()
    elif provider_name == "fallback":
        logger.info("🤖 [AI Strategy] Using Deterministic Offline NLP (Explicitly configured)")
        return fallback
    else:
        if settings.GROQ_API_KEY:
            return groq
        elif settings.GEMINI_API_KEY:
            return gemini
        return fallback

__all__ = [
    "BaseAIProvider", "GeminiProvider", "GroqProvider", "LocalProvider",
    "FallbackProvider", "AISummarizer", "DailyDigestGenerator", "get_ai_provider"
]
