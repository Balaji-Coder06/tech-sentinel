from datetime import datetime, timezone
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class RawItem(BaseModel):
    title: str
    description: Optional[str] = ""
    content: Optional[str] = ""
    url: str
    source_id: str
    source_name: str
    category: Optional[str] = "development"
    published_at: Optional[str] = None
    image_url: Optional[str] = None
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)

class SentinelSummary(BaseModel):
    what: str
    why: str
    action: str
    key_points: List[str] = Field(default_factory=list)

class NewsItem(BaseModel):
    id: str
    title: str
    description: str
    content: Optional[str] = ""
    url: str
    canonical_url: Optional[str] = None
    image_url: Optional[str] = None
    source_id: Optional[str] = None
    source_name: str
    category: str
    tags: List[str] = Field(default_factory=list)
    read_time_minutes: int = 3
    
    summary: Optional[SentinelSummary] = None
    importance_score: int = 50
    relevance_score: int = 50
    is_featured: bool = False
    is_trending: bool = False
    
    published_at: str
    discovered_at: str = Field(default_factory=utc_now_iso)

class Opportunity(BaseModel):
    id: str
    title: str
    provider: str
    provider_logo: Optional[str] = None
    description: str
    opportunity_type: Literal[
        'software', 'ai_credits', 'cloud', 'education', 
        'certification', 'competition', 'career', 'resource'
    ] = 'software'
    category: str = 'development'
    
    normal_value: Optional[str] = None
    current_value: str = 'FREE'
    eligibility: str = 'All Developers'
    claim_url: str
    official_url: Optional[str] = None
    requirements: Optional[str] = None
    coupon_code: Optional[str] = None
    
    start_date: Optional[str] = None
    expiry_date: Optional[str] = None
    is_expiring_soon: bool = False
    status: Literal['ACTIVE', 'EXPIRING_SOON', 'EXPIRED'] = 'ACTIVE'
    
    verification_status: Literal['VERIFIED', 'NEEDS_VERIFICATION', 'EXPIRED'] = 'NEEDS_VERIFICATION'
    last_verified_at: Optional[str] = None
    verification_notes: Optional[str] = None
    
    importance_score: int = 80
    relevance_score: int = 80
    priority: Literal['Critical', 'High', 'Medium', 'Low'] = 'High'
    why_care: Optional[str] = None
    
    discovered_at: str = Field(default_factory=utc_now_iso)

class DailyReport(BaseModel):
    id: str
    date: str  # YYYY-MM-DD
    title: str
    headline: str
    thirty_sec_summary: str
    top_stories: List[Dict[str, Any]]
    free_opportunities: List[Dict[str, Any]]
    student_opportunities: List[Dict[str, Any]] = Field(default_factory=list)
    open_source_highlights: List[Dict[str, Any]] = Field(default_factory=list)
    expiring_soon: List[Dict[str, Any]] = Field(default_factory=list)
    sentinel_take: str
    stats: Dict[str, Any] = Field(default_factory=dict)
    published_at: str = Field(default_factory=utc_now_iso)
    telegram_message_id: Optional[str] = None

class UserPreferences(BaseModel):
    id: str = "default"
    user_name: str = "Balaji"
    theme: str = "system"
    categories: List[str] = Field(default_factory=lambda: ["ai", "cloud", "development", "open_source", "cybersecurity", "startups"])
    keywords: List[str] = Field(default_factory=lambda: ["react", "llm", "credits", "internship", "certification", "hackathon"])
    opportunity_types: List[str] = Field(default_factory=lambda: ["software", "ai_credits", "cloud", "education", "certification", "competition", "career"])
    enable_daily_brief: bool = True
    enable_critical_alerts: bool = True
    telegram_chat_id: Optional[str] = None
    ai_provider: str = "fallback"

class SystemStatus(BaseModel):
    id: str = "current"
    status: str = "ACTIVE"
    last_scan_time: str = Field(default_factory=utc_now_iso)
    sources_checked: int = 0
    new_opportunities_today: int = 0
    next_report_time: str = "9:00 PM IST"
    last_run_duration_sec: float = 0.0
    last_error: Optional[str] = None
