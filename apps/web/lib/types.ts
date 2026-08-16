export type Category = 'ai' | 'cloud' | 'development' | 'open_source' | 'cybersecurity' | 'startups';

export type OpportunityType = 
  | 'software' 
  | 'ai_credits' 
  | 'cloud' 
  | 'education' 
  | 'certification' 
  | 'competition' 
  | 'career' 
  | 'resource';

export type VerificationStatus = 'VERIFIED' | 'NEEDS_VERIFICATION' | 'EXPIRED';
export type OpportunityStatus = 'ACTIVE' | 'EXPIRING_SOON' | 'EXPIRED';
export type PriorityLevel = 'Critical' | 'High' | 'Medium' | 'Low';

export interface SentinelSummary {
  what: string;
  why: string;
  action: string;
  key_points?: string[];
}

export interface NewsItem {
  id: string;
  title: string;
  description: string;
  content?: string;
  url: string;
  canonical_url?: string;
  image_url?: string;
  source_id?: string;
  source_name: string;
  category: Category | string;
  tags?: string[];
  read_time_minutes?: number;
  
  summary?: SentinelSummary;
  summary_what?: string;
  summary_why?: string;
  summary_action?: string;
  key_points?: string | string[];

  importance_score: number;
  relevance_score: number;
  is_featured?: boolean;
  is_trending?: boolean;
  published_at: string;
  discovered_at?: string;
}

export interface Opportunity {
  id: string;
  title: string;
  provider: string;
  provider_logo?: string;
  description: string;
  opportunity_type: OpportunityType;
  category: Category | string;
  
  normal_value?: string;
  current_value: string;
  eligibility: string;
  claim_url: string;
  official_url?: string;
  requirements?: string;
  coupon_code?: string;
  
  start_date?: string;
  expiry_date?: string;
  is_expiring_soon?: boolean;
  status: OpportunityStatus;
  
  verification_status: VerificationStatus;
  last_verified_at?: string;
  verification_notes?: string;
  
  importance_score: number;
  relevance_score: number;
  priority: PriorityLevel;
  why_care?: string;
  
  discovered_at?: string;
}

export interface DailyReport {
  id: string;
  date: string;
  title: string;
  headline: string;
  thirty_sec_summary: string;
  top_stories: Array<{
    id: string;
    title: string;
    category?: string;
    score?: number;
    summary?: string;
  }>;
  free_opportunities: Array<{
    id: string;
    title: string;
    provider?: string;
    value?: string;
    claim_url?: string;
    eligibility?: string;
  }>;
  student_opportunities?: Array<{
    id: string;
    title: string;
    value?: string;
  }>;
  open_source_highlights?: Array<{
    title: string;
    url?: string;
    category?: string;
  }>;
  expiring_soon?: Array<{
    id: string;
    title: string;
    expires?: string;
    expires_in?: string;
  }>;
  sentinel_take: string;
  stats?: {
    total_scanned?: number;
    new_news?: number;
    new_opportunities?: number;
    verified_active?: number;
    expiring_count?: number;
  };
  published_at?: string;
}

export interface UserPreferences {
  id: string;
  user_name: string;
  theme: 'light' | 'dark' | 'system';
  categories: string[];
  keywords: string[];
  opportunity_types: string[];
  enable_daily_brief: boolean;
  enable_critical_alerts: boolean;
  telegram_chat_id?: string;
}

export interface AgentStats {
  status: 'ACTIVE' | 'IDLE' | 'SCANNING';
  last_scan_time: string;
  sources_checked: number;
  new_opportunities_today: number;
  next_report_time: string;
  system_cost: string;
  trending_topics?: Array<{ tag: string; count: number }>;
}
