import logging
from urllib.parse import urlsplit
from datetime import datetime, timezone
from typing import Optional
import httpx
from ..models import Opportunity
from ..config import settings

logger = logging.getLogger(__name__)

class Verifier:
    """Verifies URLs and checks official provider status for discovered opportunities."""
    
    TRUSTED_DOMAINS = [
        "google.com", "microsoft.com", "github.com", "amazon.com", "aws.amazon.com",
        "oracle.com", "cloudflare.com", "anthropic.com", "openai.com", "meta.com",
        "huggingface.co", "groq.com", "mongodb.com", "vercel.com", "supabase.com",
        "freecodecamp.org", "education.github.com"
    ]

    def _is_trusted_domain(self, url: str) -> bool:
        """Securely verifies whether the URL hostname is an exact match or subdomain of trusted providers."""
        try:
            parsed = urlsplit(url)
            hostname = parsed.hostname
            if not hostname:
                return False
            hostname = hostname.lower()
            
            for trusted in self.TRUSTED_DOMAINS:
                if hostname == trusted or hostname.endswith("." + trusted):
                    return True
            return False
        except Exception:
            return False

    def verify(self, opp: Opportunity) -> Opportunity:
        opp.last_verified_at = datetime.now(timezone.utc).isoformat()
        is_official = self._is_trusted_domain(opp.claim_url)

        if is_official:
            opp.verification_status = "VERIFIED"
            opp.verification_notes = "Official source verified on official provider domain."
            return opp

        try:
            # Probe link liveness via HEAD/GET
            headers = {"User-Agent": settings.USER_AGENT}
            with httpx.Client(timeout=6.0, follow_redirects=True) as client:
                res = client.head(opp.claim_url, headers=headers)
                if res.status_code in (405, 403):
                    # Fallback to GET for sites that block HEAD
                    res = client.get(opp.claim_url, headers=headers)

                if res.status_code in (200, 301, 302, 307, 308):
                    # Verify if redirected to official domain
                    final_url = str(res.url)
                    if self._is_trusted_domain(final_url):
                        opp.verification_status = "VERIFIED"
                        opp.verification_notes = f"Verified redirect to official provider ({urlsplit(final_url).hostname})."
                    else:
                        # Link is active, but origin is secondary/community
                        opp.verification_status = "NEEDS_VERIFICATION"
                        opp.verification_notes = f"Endpoint is active (HTTP {res.status_code}); community source verification recommended."
                elif res.status_code in (404, 410):
                    opp.verification_status = "EXPIRED"
                    opp.status = "EXPIRED"
                    opp.verification_notes = f"Offer link returned HTTP {res.status_code} (Expired/Removed)."
                else:
                    opp.verification_status = "NEEDS_VERIFICATION"
                    opp.verification_notes = f"Returned HTTP {res.status_code}."
        except Exception as e:
            logger.debug(f"Verification probe failed for {opp.claim_url}: {e}")
            opp.verification_status = "NEEDS_VERIFICATION"
            opp.verification_notes = "Verification probe timed out; manual confirmation recommended."

        return opp
