"""Tech Sentinel AI Engine Package."""
from .provider import BaseAIProvider
from .gemini_provider import GeminiProvider
from .groq_provider import GroqProvider
from .local_provider import LocalProvider
from .fallback_provider import FallbackProvider
from .summarizer import AISummarizer
from .digest_generator import DailyDigestGenerator

def get_ai_provider(name: str = "fallback") -> BaseAIProvider:
    provider_map = {
        "gemini": GeminiProvider,
        "groq": GroqProvider,
        "local": LocalProvider,
        "fallback": FallbackProvider
    }
    cls = provider_map.get(name.lower(), FallbackProvider)
    return cls()

__all__ = [
    "BaseAIProvider", "GeminiProvider", "GroqProvider", "LocalProvider",
    "FallbackProvider", "AISummarizer", "DailyDigestGenerator", "get_ai_provider"
]
