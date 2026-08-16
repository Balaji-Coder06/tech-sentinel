from ..models import RawItem, NewsItem, UserPreferences

class Scorer:
    """Scores relevance and importance for news items and opportunities based on user interests and signals."""

    def score_news(self, item: RawItem, user_prefs: UserPreferences) -> int:
        score = 50
        text = f"{item.title} {item.description}".lower()

        # 1. User category match (+20)
        if item.category in user_prefs.categories:
            score += 20

        # 2. Keyword matches (+5 each, up to +20)
        kw_bonus = sum(5 for kw in user_prefs.keywords if kw in text)
        score += min(kw_bonus, 20)

        # 3. High-impact breaking technology keywords (+10)
        breaking_kw = ["launch", "release", "benchmark", "breakthrough", "sota", "major", "hybrid", "frontier"]
        if any(bkw in text for bkw in breaking_kw):
            score += 10

        return max(10, min(99, score))
