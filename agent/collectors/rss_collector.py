import logging
from datetime import datetime, timezone
from typing import List, Optional
import feedparser
import httpx
from bs4 import BeautifulSoup
from .base import BaseCollector
from ..models import RawItem
from ..config import settings
from ..utils.validator import is_valid_title

logger = logging.getLogger(__name__)

def is_valid_article_image(url: str, img_tag=None) -> bool:
    if not url or not isinstance(url, str):
        return False
    clean = url.strip().lower()
    if not (clean.startswith("http://") or clean.startswith("https://")):
        return False
    # Reject tracking pixels, badges, logos, analytics, and icons
    reject_patterns = [
        "1x1", "pixel", "tracker", "analytics", "feedburner", "statcounter",
        "badge", "emoji", "emoticon", "spacer", "advertisement", "doubleclick",
        "favicon", ".ico", "gravatar.com/avatar/0000"
    ]
    if any(p in clean for p in reject_patterns):
        return False
    if img_tag:
        w = img_tag.get("width", "")
        h = img_tag.get("height", "")
        if str(w) in ("1", "0") or str(h) in ("1", "0"):
            return False
    return True

class RSSCollector(BaseCollector):
    def fetch(self) -> List[RawItem]:
        items: List[RawItem] = []
        try:
            headers = {"User-Agent": settings.USER_AGENT}
            with httpx.Client(timeout=settings.REQUEST_TIMEOUT_SECONDS, follow_redirects=True) as client:
                response = client.get(self.url, headers=headers)
                if response.status_code != 200:
                    logger.warning(f"Failed to fetch RSS feed {self.name}: HTTP {response.status_code}")
                    return items
                feed_content = response.text

            feed = feedparser.parse(feed_content)
            for entry in feed.entries[:settings.MAX_ITEMS_PER_SOURCE]:
                title = entry.get("title", "").strip()
                if not is_valid_title(title):
                    logger.warning(f"Rejecting entry from {self.name} with invalid/template title: '{title}'")
                    continue

                link = entry.get("link", "")
                raw_summary = entry.get("summary", "") or entry.get("description", "") or ""
                description = raw_summary
                
                # Strip HTML tags from description
                if description:
                    soup = BeautifulSoup(description, "html.parser")
                    description = soup.get_text(separator=" ", strip=True)

                content = ""
                if "content" in entry and len(entry.content) > 0:
                    soup = BeautifulSoup(entry.content[0].value, "html.parser")
                    content = soup.get_text(separator=" ", strip=True)

                # Standardize published timestamp to ISO-8601 UTC
                published_at = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    try:
                        published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()
                    except Exception:
                        pass
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    try:
                        published_at = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc).isoformat()
                    except Exception:
                        pass

                if not published_at:
                    published_at = datetime.now(timezone.utc).isoformat()

                # Extract image if present across media_content, media_thumbnail, links, or description HTML
                image_url = None
                if "media_content" in entry and len(entry.media_content) > 0:
                    cand = entry.media_content[0].get("url")
                    if is_valid_article_image(cand):
                        image_url = cand
                elif "media_thumbnail" in entry and len(entry.media_thumbnail) > 0:
                    cand = entry.media_thumbnail[0].get("url")
                    if is_valid_article_image(cand):
                        image_url = cand
                elif "links" in entry:
                    for l in entry.links:
                        if l.get("type", "").startswith("image/") or l.get("rel") == "enclosure":
                            cand = l.get("href")
                            if is_valid_article_image(cand):
                                image_url = cand
                                break
                elif "enclosures" in entry and len(entry.enclosures) > 0:
                    cand = entry.enclosures[0].get("href") or entry.enclosures[0].get("url")
                    if is_valid_article_image(cand):
                        image_url = cand

                # Fallback: check <img> tags in raw HTML description or content
                if not image_url and (raw_summary or "content" in entry):
                    try:
                        html_to_check = raw_summary or (entry.content[0].value if "content" in entry and len(entry.content) > 0 else "")
                        if "<img" in html_to_check:
                            img_soup = BeautifulSoup(html_to_check, "html.parser")
                            for img_tag in img_soup.find_all("img"):
                                src = img_tag.get("src")
                                if is_valid_article_image(src, img_tag):
                                    image_url = src
                                    break
                    except Exception:
                        pass

                items.append(RawItem(
                    title=title,
                    description=description[:1000] if description else title,
                    content=content[:3000] if content else description[:1000],
                    url=link,
                    source_id=self.source_id,
                    source_name=self.name,
                    category=self.category,
                    published_at=published_at,
                    image_url=image_url,
                    raw_metadata={"author": entry.get("author", ""), "tags": [t.get("term") for t in entry.get("tags", [])]}
                ))
            logger.info(f"Successfully collected {len(items)} items from {self.name}")
        except Exception as e:
            logger.error(f"Error fetching RSS source {self.name} ({self.url}): {e}")
        
        return items
