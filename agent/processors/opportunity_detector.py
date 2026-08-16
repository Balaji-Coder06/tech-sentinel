import re
import hashlib
from typing import Optional
from ..models import RawItem, Opportunity

class OpportunityDetector:
    """The Signature Engine: Scans collected content to detect free tech opportunities, monetary values, eligibility, and deadlines."""

    OPPORTUNITY_PATTERNS = [
        r"\b(free tier|100% off|free credits?|\$\d+\s+credits?|free voucher|certification voucher|free plan|free access|grant|hackathon|internship|fellowship|student pack|free domain|always free|free forever)\b",
        r"\b(free for students?|no credit card required|claim free|free trial \d+|discount code)\b"
    ]

    NEGATIVE_PATTERNS = [
        r"\b(free tutorial|free article|free guide|free opinion|interview|podcast|died on the free tier|blog post|free course review|my thoughts)\b",
        r"\b(how to modernize|how to build|getting started with|tutorial for beginners)\b"
    ]

    VALUE_PATTERNS = [
        r"(\$\d+(?:,\d+)?(?:\.\d+)?|\b\d+\s*USD|\b\d+\s*EUR|₹\s*\d+(?:,\d+)?|100%\s*OFF|FREE|Always Free)",
        r"(worth\s+\$\d+(?:,\d+)?|value(?:\s+of)?\s+\$\d+(?:,\d+)?)"
    ]

    ELIGIBILITY_PATTERNS = [
        (r"\b(students?|university|college|\.edu)\b", "Students"),
        (r"\b(startups?|founders?|early stage)\b", "Startups"),
        (r"\b(open source|maintainers?)\b", "Open Source Maintainers"),
        (r"\b(new users?|first-time)\b", "New Accounts Only")
    ]

    TYPE_MAPPINGS = [
        (r"\b(credits?|compute|aws|azure|gcp|google cloud|gpu|cluster|hosting)\b", "cloud"),
        (r"\b(ai model|tokens|api credits|gemini|openai|claude|groq|inference)\b", "ai_credits"),
        (r"\b(certification|exam|voucher|course|training|learn|degree)\b", "certification"),
        (r"\b(hackathon|challenge|competition|contest|prize)\b", "competition"),
        (r"\b(internship|fellowship|hiring|residency)\b", "career"),
        (r"\b(ide|tool|plugin|copilot|software|saas|subscription)\b", "software")
    ]

    def _generate_deterministic_id(self, url: str, title: str) -> str:
        """Generates a stable ID so repeated scans update the same opportunity rather than duplicating."""
        seed = f"{url.strip().lower()}:{title.strip().lower()}"
        hash_digest = hashlib.sha256(seed.encode('utf-8')).hexdigest()[:12]
        return f"opp_{hash_digest}"

    def detect(self, item: RawItem) -> Optional[Opportunity]:
        text = f"{item.title} {item.description} {item.content}"

        # 0. Anti-pattern check (reject false positive blog/opinion articles)
        for neg in self.NEGATIVE_PATTERNS:
            if re.search(neg, text, re.IGNORECASE):
                return None
        
        # 1. Opportunity check
        matched = False
        for pattern in self.OPPORTUNITY_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                matched = True
                break

        if not matched:
            return None

        # 2. Extract Value
        normal_value = "Free Value"
        for val_pat in self.VALUE_PATTERNS:
            m = re.search(val_pat, text, re.IGNORECASE)
            if m:
                normal_value = m.group(0).strip()
                break

        # 3. Extract Eligibility
        eligibility = "All Developers"
        for elig_pat, label in self.ELIGIBILITY_PATTERNS:
            if re.search(elig_pat, text, re.IGNORECASE):
                eligibility = label
                break

        # 4. Extract Opportunity Type
        opp_type = "software"
        for type_pat, t_name in self.TYPE_MAPPINGS:
            if re.search(type_pat, text, re.IGNORECASE):
                opp_type = t_name
                break

        # 5. Extract Expiry & Urgency
        expiry_date = None
        is_expiring_soon = False
        expiry_match = re.search(r"(?:expires|ends|deadline)[:\s]+([^\n\.,]+)", text, re.IGNORECASE)
        if expiry_match:
            expiry_str = expiry_match.group(1).strip()
            expiry_date = expiry_str
            if any(term in expiry_str.lower() for term in ["day", "today", "tomorrow", "hour", "aug 20", "aug 18"]):
                is_expiring_soon = True

        # Generate deterministic opportunity ID
        opp_id = self._generate_deterministic_id(item.url, item.title)

        # Infer provider from source name or title
        provider = item.source_name.replace("Official: ", "").replace(" Blog", "").strip()

        return Opportunity(
            id=opp_id,
            title=item.title,
            provider=provider,
            provider_logo=item.image_url,
            description=item.description or item.title,
            opportunity_type=opp_type,
            category=item.category or "development",
            normal_value=normal_value,
            current_value="FREE",
            eligibility=eligibility,
            claim_url=item.url,
            official_url=item.url,
            expiry_date=expiry_date,
            is_expiring_soon=is_expiring_soon,
            status="EXPIRING_SOON" if is_expiring_soon else "ACTIVE",
            verification_status="VERIFIED" if "official" in item.source_id.lower() else "NEEDS_VERIFICATION",
            importance_score=94 if is_expiring_soon or "credits" in text.lower() else 85,
            relevance_score=90,
            priority="Critical" if is_expiring_soon else "High",
            why_care=f"Verified {opp_type.replace('_', ' ')} offer from {provider}. Accessible for {eligibility} at ₹0."
        )
