import re
import hashlib
from typing import List, Set, Dict, Any
from ..models import RawItem

class Deduplicator:
    """Deduplicates news and opportunities via canonical URL hashing and title token Jaccard similarity."""
    
    def __init__(self, similarity_threshold: float = 0.65):
        self.similarity_threshold = similarity_threshold
        self.seen_hashes: Set[str] = set()
        self.seen_titles: List[Tuple_Title] = []

    def _normalize_url(self, url: str) -> str:
        # Strip tracking query params (utm_*, ref, fbclid, etc.)
        clean_url = re.sub(r'(\?|&)(utm_[^&=]+|ref|source|fbclid|gclid)=[^&=]+', '', url)
        clean_url = clean_url.rstrip('/?&').lower()
        return clean_url

    def _get_url_hash(self, url: str) -> str:
        norm = self._normalize_url(url)
        return hashlib.sha256(norm.encode('utf-8')).hexdigest()

    def _tokenize_title(self, title: str) -> Set[str]:
        words = re.findall(r'\b\w{3,}\b', title.lower())
        stopwords = {'the', 'and', 'for', 'with', 'from', 'this', 'that', 'your', 'about', 'over', 'into', 'what', 'how', 'why', 'announces', 'launches', 'releases', 'new'}
        return {w for w in words if w not in stopwords}

    def _jaccard_similarity(self, s1: Set[str], s2: Set[str]) -> float:
        if not s1 or not s2:
            return 0.0
        intersection = len(s1.intersection(s2))
        union = len(s1.union(s2))
        return intersection / union if union > 0 else 0.0

    def is_duplicate(self, item: RawItem) -> bool:
        # 1. Direct URL check
        url_hash = self._get_url_hash(item.url)
        if url_hash in self.seen_hashes:
            return True

        # 2. Title semantic/word similarity check
        tokens = self._tokenize_title(item.title)
        if len(tokens) >= 3:
            for past_tokens, past_url in self.seen_titles:
                similarity = self._jaccard_similarity(tokens, past_tokens)
                if similarity >= self.similarity_threshold:
                    return True

        # Not a duplicate -> record it
        self.seen_hashes.add(url_hash)
        if len(tokens) >= 3:
            self.seen_titles.append((tokens, item.url))
        return False

    def filter_unique(self, items: List[RawItem]) -> List[RawItem]:
        unique_items = []
        for item in items:
            if not self.is_duplicate(item):
                unique_items.append(item)
        return unique_items

# Type alias helper
Tuple_Title = Any
