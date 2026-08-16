import { NewsItem, Opportunity, DailyReport, UserPreferences, AgentStats } from './types';

const API_BASE = typeof window !== 'undefined' ? '' : (process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_APP_URL || 'https://tech-sentinel-chi.vercel.app');

export async function fetchNews(
  category?: string, 
  sort: 'intelligence' | 'chronological' = 'intelligence',
  allowedCategories?: string[]
): Promise<NewsItem[]> {
  try {
    const params = new URLSearchParams();
    if (category && category !== 'all') params.set('category', category);
    if (sort) params.set('sort', sort);
    if (allowedCategories && allowedCategories.length > 0) {
      params.set('categories', allowedCategories.join(','));
    }
    const qs = params.toString();
    const url = qs ? `/api/news?${qs}` : '/api/news';
    const res = await fetch(url, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const json = await res.json();
    return json.data || [];
  } catch (e) {
    console.warn('Error fetching news:', e);
    return [];
  }
}

export async function fetchNewsWithCategories(
  category?: string, 
  sort: 'intelligence' | 'chronological' = 'intelligence',
  allowedCategories?: string[]
): Promise<{ news: NewsItem[]; categories: Array<{ id: string; label: string; count: number }> }> {
  try {
    const params = new URLSearchParams();
    if (category && category !== 'all') params.set('category', category);
    if (sort) params.set('sort', sort);
    if (allowedCategories && allowedCategories.length > 0) {
      params.set('categories', allowedCategories.join(','));
    }
    const qs = params.toString();
    const url = qs ? `/api/news?${qs}` : '/api/news';
    const res = await fetch(url, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const json = await res.json();
    return {
      news: json.data || [],
      categories: json.categories || []
    };
  } catch (e) {
    console.warn('Error fetching news with categories:', e);
    return { news: [], categories: [] };
  }
}

export async function fetchCategories(): Promise<Array<{ id: string; label: string; count: number }>> {
  try {
    const res = await fetch('/api/news/categories', { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const json = await res.json();
    return json.data || [];
  } catch (e) {
    console.warn('Error fetching categories:', e);
    return [];
  }
}

export async function fetchOpportunities(type?: string, status?: string, sort: 'score' | 'expiry' | 'value' = 'score'): Promise<Opportunity[]> {
  try {
    const params = new URLSearchParams();
    if (type && type !== 'all') params.set('type', type);
    if (status && status !== 'all') params.set('status', status);
    if (sort) params.set('sort', sort);
    
    const qs = params.toString();
    const url = qs ? `/api/opportunities?${qs}` : '/api/opportunities';
    const res = await fetch(url, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const json = await res.json();
    return json.data || [];
  } catch (e) {
    console.warn('Error fetching opportunities:', e);
    return [];
  }
}

export async function fetchReports(): Promise<DailyReport[]> {
  try {
    const res = await fetch('/api/reports', { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const json = await res.json();
    return json.data || [];
  } catch (e) {
    console.warn('Error fetching reports:', e);
    return [];
  }
}

export async function fetchReportByDate(date: string): Promise<DailyReport | null> {
  try {
    const res = await fetch(`/api/reports?date=${encodeURIComponent(date)}`, { cache: 'no-store' });
    if (res.status === 404) return null;
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const json = await res.json();
    return json.data || null;
  } catch (e) {
    console.warn(`Error fetching report for ${date}:`, e);
    return null;
  }
}

export async function fetchAgentStats(): Promise<AgentStats> {
  try {
    const res = await fetch('/api/stats', { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const json = await res.json();
    return json.data || {
      status: 'ACTIVE',
      last_scan_time: 'Recently',
      sources_checked: 9,
      new_opportunities_today: 6,
      next_report_time: '9:00 PM IST',
      system_cost: '₹0.00'
    };
  } catch (e) {
    console.warn('Error fetching agent stats:', e);
    return {
      status: 'ACTIVE',
      last_scan_time: 'Recently',
      sources_checked: 9,
      new_opportunities_today: 6,
      next_report_time: '9:00 PM IST',
      system_cost: '₹0.00'
    };
  }
}

export async function fetchSavedItems(): Promise<{ news: string[]; opportunities: string[] }> {
  try {
    const res = await fetch('/api/saved', { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const json = await res.json();
    return json.data || { news: [], opportunities: [] };
  } catch {
    // Fallback to localStorage if offline
    if (typeof window !== 'undefined') {
      try {
        const stored = localStorage.getItem('sentinel_saved');
        if (stored) return JSON.parse(stored);
      } catch {}
    }
    return { news: ['news_01'], opportunities: ['opp_01', 'opp_02'] };
  }
}

export async function toggleSavedItem(type: 'news' | 'opportunity', id: string): Promise<{ news: string[]; opportunities: string[] }> {
  try {
    const res = await fetch('/api/saved', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type, id })
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const json = await res.json();
    if (typeof window !== 'undefined') {
      localStorage.setItem('sentinel_saved', JSON.stringify(json.data));
    }
    return json.data;
  } catch (e) {
    console.warn('Error toggling saved item:', e);
    // Local fallback
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('sentinel_saved');
      const data = stored ? JSON.parse(stored) : { news: [], opportunities: [] };
      const list = type === 'news' ? data.news : data.opportunities;
      const idx = list.indexOf(id);
      if (idx >= 0) list.splice(idx, 1);
      else list.push(id);
      localStorage.setItem('sentinel_saved', JSON.stringify(data));
      return data;
    }
    return { news: [], opportunities: [] };
  }
}

export async function fetchPreferences(): Promise<UserPreferences> {
  try {
    const res = await fetch('/api/preferences', { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const json = await res.json();
    return json.data || {};
  } catch (e) {
    console.warn('Error fetching preferences:', e);
    return {
      id: 'default',
      user_name: 'Balaji',
      theme: 'system',
      categories: ['ai', 'cloud', 'development', 'open_source', 'cybersecurity', 'startups'],
      keywords: ['react', 'llm', 'credits', 'internship', 'certification', 'hackathon', 'copilot'],
      opportunity_types: ['software', 'ai_credits', 'cloud', 'education', 'certification', 'competition', 'career'],
      enable_daily_brief: true,
      enable_critical_alerts: true,
      email_newsletter_enabled: false,
      newsletter_email: ''
    };
  }
}

export async function savePreferences(prefs: UserPreferences): Promise<UserPreferences> {
  try {
    const res = await fetch('/api/preferences', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(prefs)
    });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    const json = await res.json();
    return json.data;
  } catch (e) {
    console.warn('Error saving preferences:', e);
    return prefs;
  }
}
