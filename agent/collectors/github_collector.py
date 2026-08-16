import logging
from datetime import datetime
from typing import List
import httpx
from .base import BaseCollector
from ..models import RawItem
from ..config import settings

logger = logging.getLogger(__name__)

class GitHubCollector(BaseCollector):
    """Collects trending open-source tools and developer pack opportunities from GitHub."""
    def fetch(self) -> List[RawItem]:
        items: List[RawItem] = []
        try:
            # We can query GitHub's public search API for recently created/trending open source AI and developer tools
            search_urls = [
                "https://api.github.com/search/repositories?q=stars:>500+created:>2026-01-01+topic:ai&sort=stars&order=desc&per_page=10",
                "https://api.github.com/search/repositories?q=topic:developer-tools+stars:>300&sort=updated&order=desc&per_page=10"
            ]
            
            headers = {
                "User-Agent": settings.USER_AGENT,
                "Accept": "application/vnd.github.v3+json"
            }
            
            with httpx.Client(timeout=settings.REQUEST_TIMEOUT_SECONDS) as client:
                for target_url in search_urls:
                    try:
                        res = client.get(target_url, headers=headers)
                        if res.status_code == 200:
                            data = res.json()
                            for repo in data.get("items", [])[:5]:
                                name = repo.get("full_name", "")
                                desc = repo.get("description") or "Open source developer tool."
                                stars = repo.get("stargazers_count", 0)
                                repo_url = repo.get("html_url", "")
                                
                                items.append(RawItem(
                                    title=f"GitHub Trending: {name} (⭐ {stars:,})",
                                    description=f"{desc} — Language: {repo.get('language', 'Various')}, License: {repo.get('license', {}).get('name', 'Open Source') if repo.get('license') else 'Open Source'}",
                                    content=f"Trending open source repository: {name}. Description: {desc}. Stargazers: {stars}. Topics: {', '.join(repo.get('topics', []))}",
                                    url=repo_url,
                                    source_id=self.source_id,
                                    source_name="GitHub Trending",
                                    category="open_source",
                                    published_at=repo.get("updated_at", datetime.utcnow().isoformat()),
                                    image_url=repo.get("owner", {}).get("avatar_url"),
                                    raw_metadata={"stars": stars, "topics": repo.get("topics", [])}
                                ))
                    except Exception as sub_e:
                        logger.debug(f"GitHub search query error: {sub_e}")
                        
            logger.info(f"GitHubCollector retrieved {len(items)} repositories.")
        except Exception as e:
            logger.error(f"Error in GitHubCollector: {e}")
        return items
