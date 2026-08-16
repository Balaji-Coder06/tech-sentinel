import path from 'path';
import fs from 'fs';
import { createRequire } from 'module';
import type { NewsItem, Opportunity, DailyReport, UserPreferences, AgentStats } from './types';
import { INITIAL_NEWS, INITIAL_OPPORTUNITIES, INITIAL_REPORT, INITIAL_PREFERENCES, INITIAL_AGENT_STATS } from './mock-data';
import { rankNewsItems, getRankingBreakdown, calculateIntelligenceScore } from './ranking';
import { rankOpportunities, calculateOpportunityScore, getOpportunityRankingBreakdown } from './opportunity-ranking';

const customRequire = typeof require === 'function' ? require : createRequire(import.meta.url);

let sqliteDbInstance: any = null;

function getSqliteDb(): any {
  if (sqliteDbInstance) return sqliteDbInstance;
  try {
    const { DatabaseSync } = customRequire('node:sqlite');
    const possiblePaths = [
      path.resolve(process.cwd(), '../../database/tech_sentinel.db'),
      path.resolve(process.cwd(), '../database/tech_sentinel.db'),
      path.resolve(process.cwd(), 'database/tech_sentinel.db'),
      path.resolve(process.cwd(), 'tech_sentinel.db'),
    ];

    let dbPath = possiblePaths.find(p => fs.existsSync(p));
    if (!dbPath) {
      dbPath = possiblePaths[0];
    }

    if (fs.existsSync(dbPath)) {
      sqliteDbInstance = new DatabaseSync(dbPath);
      return sqliteDbInstance;
    }
  } catch (e) {
    console.warn('node:sqlite not available or database path not found, falling back to memory/seed state:', e);
  }
  return null;
}

export function isValidTitle(title?: string | null): boolean {
  if (!title || typeof title !== 'string') return false;
  const trimmed = title.trim();
  if (trimmed.length < 3) return false;
  const lower = trimmed.toLowerCase();
  if (['undefined', 'null', 'none', 'nan', 'n/a', '[object object]', 'untitled'].includes(lower)) return false;
  if (/\{\{[\s\S]*?\}\}/.test(trimmed)) return false;
  if (/\$\{[\s\S]*?\}/.test(trimmed)) return false;
  if (/\$\([\'\"][\s\S]*?[\'\"]\)/.test(trimmed)) return false;
  if (/<\%[\s\S]*?\%>/.test(trimmed)) return false;
  if (/\[%[\s\S]*?%\]/.test(trimmed)) return false;
  return true;
}

export const CANONICAL_SYNONYMS: Record<string, string> = {
  'ai': 'ai',
  'artificial intelligence': 'ai',
  'artificial-intelligence': 'ai',
  'artificial_intelligence': 'ai',
  'machine learning': 'ai',
  'machine-learning': 'ai',
  'machine_learning': 'ai',
  'ml': 'ai',
  'genai': 'ai',
  'generative ai': 'ai',
  'deep learning': 'ai',
  'deep-learning': 'ai',
  'deep_learning': 'ai',
  'llm': 'ai',
  'llms': 'ai',
  'cloud': 'cloud',
  'cloud computing': 'cloud',
  'cloud-computing': 'cloud',
  'cloud_computing': 'cloud',
  'cloud infrastructure': 'cloud',
  'cloud-infrastructure': 'cloud',
  'cloud_infrastructure': 'cloud',
  'devops': 'cloud',
  'serverless': 'cloud',
  'infrastructure': 'cloud',
  'cloud & infrastructure': 'cloud',
  'cloud-native': 'cloud',
  'development': 'development',
  'software development': 'development',
  'software-development': 'development',
  'software_development': 'development',
  'software dev': 'development',
  'software-dev': 'development',
  'software_dev': 'development',
  'programming': 'development',
  'software engineering': 'development',
  'coding': 'development',
  'web development': 'development',
  'webdev': 'development',
  'frontend': 'development',
  'backend': 'development',
  'fullstack': 'development',
  'developer tools': 'development',
  'devtools': 'development',
  'open_source': 'open_source',
  'open source': 'open_source',
  'open-source': 'open_source',
  'opensource': 'open_source',
  'oss': 'open_source',
  'foss': 'open_source',
  'free and open source': 'open_source',
  'cybersecurity': 'cybersecurity',
  'cyber security': 'cybersecurity',
  'cyber-security': 'cybersecurity',
  'cyber_security': 'cybersecurity',
  'security': 'cybersecurity',
  'infosec': 'cybersecurity',
  'appsec': 'cybersecurity',
  'startups': 'startups',
  'startup': 'startups',
  'start-ups': 'startups',
  'start_ups': 'startups',
  'start-up': 'startups',
  'start_up': 'startups',
  'venture': 'startups',
  'entrepreneurship': 'startups',
  'education': 'education',
  'learning': 'education',
  'student': 'education',
  'students': 'education',
  'training': 'education',
  'tutorial': 'education',
  'tutorials': 'education',
};

export function normalizeCategory(category?: string | null): string {
  if (!category || typeof category !== 'string') return 'development';
  const cleaned = category.trim().toLowerCase();
  const cleanedSpaces = cleaned.replace(/[\s_-]+/g, ' ').trim();
  const cleanedUnderscores = cleaned.replace(/[\s_-]+/g, '_').trim();

  if (CANONICAL_SYNONYMS[cleaned]) return CANONICAL_SYNONYMS[cleaned];
  if (CANONICAL_SYNONYMS[cleanedSpaces]) return CANONICAL_SYNONYMS[cleanedSpaces];
  if (CANONICAL_SYNONYMS[cleanedUnderscores]) return CANONICAL_SYNONYMS[cleanedUnderscores];

  const slug = cleaned.replace(/[^\w\s-]/g, '').trim().replace(/[\s-]+/g, '_');
  return slug || 'development';
}

export const serverDb = {
  // -------------------------------------------------------------
  // News
  // -------------------------------------------------------------
  getNews: (
    category?: string, 
    sortMode: 'intelligence' | 'chronological' = 'intelligence',
    allowedCategories?: string[]
  ): NewsItem[] => {
    const db = getSqliteDb();
    const normalizedAllowed = (allowedCategories && allowedCategories.length > 0)
      ? allowedCategories.map(c => normalizeCategory(c))
      : undefined;

    if (db) {
      try {
        let query = "SELECT * FROM news WHERE title NOT LIKE '%{{%' AND title NOT LIKE '%${%' AND title NOT LIKE '%$(%'";
        const params: any[] = [];
        
        if (category && category.toLowerCase() !== 'all') {
          const normCat = normalizeCategory(category);
          query += ' AND category = ?';
          params.push(normCat);
        } else if (normalizedAllowed && normalizedAllowed.length > 0) {
          const placeholders = normalizedAllowed.map(() => '?').join(',');
          query += ` AND category IN (${placeholders})`;
          params.push(...normalizedAllowed);
        }
        
        query += ' ORDER BY published_at DESC LIMIT 80';
        const stmt = db.prepare(query);
        const rows = stmt.all(...params);
        if (rows && rows.length > 0) {
          const items: NewsItem[] = rows
            .filter((r: any) => isValidTitle(r.title))
            .map((r: any) => ({
              ...r,
              tags: typeof r.tags === 'string' ? JSON.parse(r.tags || '[]') : r.tags || [],
              is_featured: Boolean(r.is_featured),
              is_trending: Boolean(r.is_trending),
              summary: {
                what: r.summary_what || r.description,
                why: r.summary_why || '',
                action: r.summary_action || '',
                key_points: typeof r.key_points === 'string' ? JSON.parse(r.key_points || '[]') : r.key_points || []
              }
            }));

          if (sortMode === 'intelligence') {
            return rankNewsItems(items);
          }
          return items;
        }
      } catch (err) {
        console.warn('Error reading news from SQLite:', err);
      }
    }
    // Fallback
    let fallback = (!category || category.toLowerCase() === 'all')
      ? INITIAL_NEWS
      : INITIAL_NEWS.filter(item => normalizeCategory(item.category) === normalizeCategory(category));

    if (normalizedAllowed && normalizedAllowed.length > 0 && (!category || category.toLowerCase() === 'all')) {
      fallback = fallback.filter(item => normalizedAllowed.includes(normalizeCategory(item.category)));
    }

    if (sortMode === 'intelligence') {
      return rankNewsItems(fallback);
    }
    return fallback;
  },

  // -------------------------------------------------------------
  // Dynamic Categories (Derived from SQLite news records)
  // -------------------------------------------------------------
  getCategories: (allowedCategories?: string[]): Array<{ id: string; label: string; count: number }> => {
    const db = getSqliteDb();
    const normalizedAllowed = (allowedCategories && allowedCategories.length > 0)
      ? allowedCategories.map(c => normalizeCategory(c))
      : undefined;

    if (db) {
      try {
        let query = "SELECT category, COUNT(*) as count FROM news WHERE category IS NOT NULL AND TRIM(category) != '' AND title NOT LIKE '%{{%' AND title NOT LIKE '%${%' AND title NOT LIKE '%$(%'";
        const params: any[] = [];

        if (normalizedAllowed && normalizedAllowed.length > 0) {
          const placeholders = normalizedAllowed.map(() => '?').join(',');
          query += ` AND category IN (${placeholders})`;
          params.push(...normalizedAllowed);
        }

        query += " GROUP BY category HAVING count > 0 ORDER BY count DESC, category ASC";
        const rows = db.prepare(query).all(...params);

        if (rows && rows.length > 0) {
          return rows.map((r: any) => ({
            id: r.category.toLowerCase().trim(),
            label: serverDb.formatCategoryLabel(r.category),
            count: Number(r.count)
          }));
        }
      } catch (err) {
        console.warn('Error querying categories from SQLite:', err);
      }
    }
    // Fallback from INITIAL_NEWS
    const counts: Record<string, number> = {};
    for (const item of INITIAL_NEWS) {
      if (item.category) {
        const cat = normalizeCategory(item.category);
        if (!normalizedAllowed || normalizedAllowed.includes(cat)) {
          counts[cat] = (counts[cat] || 0) + 1;
        }
      }
    }
    return Object.entries(counts)
      .map(([id, count]) => ({
        id,
        label: serverDb.formatCategoryLabel(id),
        count
      }))
      .sort((a, b) => b.count - a.count);
  },

  formatCategoryLabel: (category: string): string => {
    if (!category) return '';
    const trimmed = category.trim();
    const lower = trimmed.toLowerCase();
    if (lower === 'ai') return 'AI';
    if (lower === 'ml') return 'ML';
    if (lower === 'api') return 'API';
    if (lower === 'ui' || lower === 'ux') return lower.toUpperCase();
    if (lower === 'all' || lower === 'all news') return 'All News';

    return trimmed
      .split(/[_\s-]+/)
      .map(word => {
        const wLower = word.toLowerCase();
        if (wLower === 'ai' || wLower === 'ui' || wLower === 'ux' || wLower === 'api') return wLower.toUpperCase();
        return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
      })
      .join(' ');
  },

  getRankingBreakdown: (item: NewsItem) => {
    return getRankingBreakdown(item);
  },

  getNewsById: (id: string): NewsItem | undefined => {
    const db = getSqliteDb();
    if (db) {
      try {
        const stmt = db.prepare('SELECT * FROM news WHERE id = ? LIMIT 1');
        const r = stmt.get(id);
        if (r) {
          return {
            ...r,
            tags: typeof r.tags === 'string' ? JSON.parse(r.tags || '[]') : r.tags || [],
            is_featured: Boolean(r.is_featured),
            is_trending: Boolean(r.is_trending),
            summary: {
              what: r.summary_what || r.description,
              why: r.summary_why || '',
              action: r.summary_action || '',
              key_points: typeof r.key_points === 'string' ? JSON.parse(r.key_points || '[]') : r.key_points || []
            }
          };
        }
      } catch (err) {
        console.warn('Error reading news by id from SQLite:', err);
      }
    }
    return INITIAL_NEWS.find(item => item.id === id);
  },

  // -------------------------------------------------------------
  // Opportunities (Opportunity Intelligence Engine)
  // -------------------------------------------------------------
  getOpportunities: (type?: string, status?: string, sortBy: 'score' | 'expiry' | 'value' = 'score'): Opportunity[] => {
    const db = getSqliteDb();
    if (db) {
      try {
        let query = 'SELECT * FROM opportunities WHERE 1=1';
        const params: any[] = [];
        if (status && status !== 'all' && status !== 'ALL') {
          query += ' AND status = ?';
          params.push(status);
        }
        if (type && type !== 'all') {
          query += ' AND (opportunity_type = ? OR category = ?)';
          params.push(type, type);
        }
        const stmt = db.prepare(query);
        const rows = stmt.all(...params);
        if (rows && rows.length > 0) {
          const items: Opportunity[] = rows.map((r: any) => ({
            ...r,
            is_expiring_soon: Boolean(r.is_expiring_soon)
          }));
          return rankOpportunities(items, sortBy);
        }
      } catch (err) {
        console.warn('Error reading opportunities from SQLite:', err);
      }
    }
    const fallback = INITIAL_OPPORTUNITIES.filter(opp => {
      if (type && type !== 'all' && opp.opportunity_type !== type && opp.category !== type) return false;
      if (status && status !== 'all' && opp.status !== status) return false;
      return true;
    });
    return rankOpportunities(fallback, sortBy);
  },

  getOpportunityRankingBreakdown: (opp: Opportunity) => {
    return getOpportunityRankingBreakdown(opp);
  },

  getOpportunityById: (id: string): Opportunity | undefined => {
    const db = getSqliteDb();
    if (db) {
      try {
        const stmt = db.prepare('SELECT * FROM opportunities WHERE id = ? LIMIT 1');
        const r = stmt.get(id);
        if (r) {
          return {
            ...r,
            is_expiring_soon: Boolean(r.is_expiring_soon)
          };
        }
      } catch (err) {
        console.warn('Error reading opportunity by id from SQLite:', err);
      }
    }
    return INITIAL_OPPORTUNITIES.find(opp => opp.id === id);
  },

  // -------------------------------------------------------------
  // Reports
  // -------------------------------------------------------------
  getDailyReports: (): DailyReport[] => {
    const db = getSqliteDb();
    if (db) {
      try {
        const stmt = db.prepare('SELECT * FROM daily_reports ORDER BY date DESC, published_at DESC LIMIT 20');
        const rows = stmt.all();
        if (rows && rows.length > 0) {
          return rows.map((r: any) => ({
            ...r,
            top_stories: typeof r.top_stories === 'string' ? JSON.parse(r.top_stories || '[]') : r.top_stories || [],
            free_opportunities: typeof r.free_opportunities === 'string' ? JSON.parse(r.free_opportunities || '[]') : r.free_opportunities || [],
            student_opportunities: typeof r.student_opportunities === 'string' ? JSON.parse(r.student_opportunities || '[]') : r.student_opportunities || [],
            open_source_highlights: typeof r.open_source_highlights === 'string' ? JSON.parse(r.open_source_highlights || '[]') : r.open_source_highlights || [],
            expiring_soon: typeof r.expiring_soon === 'string' ? JSON.parse(r.expiring_soon || '[]') : r.expiring_soon || [],
            stats: typeof r.stats_json === 'string' ? JSON.parse(r.stats_json || '{}') : r.stats_json || {}
          }));
        }
      } catch (err) {
        console.warn('Error reading daily reports from SQLite:', err);
      }
    }
    return [INITIAL_REPORT];
  },

  getReportByDate: (date: string): DailyReport | undefined => {
    const db = getSqliteDb();
    if (db) {
      try {
        const stmt = db.prepare('SELECT * FROM daily_reports WHERE date = ? LIMIT 1');
        const r = stmt.get(date);
        if (r) {
          return {
            ...r,
            top_stories: typeof r.top_stories === 'string' ? JSON.parse(r.top_stories || '[]') : r.top_stories || [],
            free_opportunities: typeof r.free_opportunities === 'string' ? JSON.parse(r.free_opportunities || '[]') : r.free_opportunities || [],
            student_opportunities: typeof r.student_opportunities === 'string' ? JSON.parse(r.student_opportunities || '[]') : r.student_opportunities || [],
            open_source_highlights: typeof r.open_source_highlights === 'string' ? JSON.parse(r.open_source_highlights || '[]') : r.open_source_highlights || [],
            expiring_soon: typeof r.expiring_soon === 'string' ? JSON.parse(r.expiring_soon || '[]') : r.expiring_soon || [],
            stats: typeof r.stats_json === 'string' ? JSON.parse(r.stats_json || '{}') : r.stats_json || {}
          };
        }
      } catch (err) {
        console.warn('Error reading daily report by date from SQLite:', err);
      }
    }
    if (INITIAL_REPORT.date === date) return INITIAL_REPORT;
    return undefined;
  },

  // -------------------------------------------------------------
  // Trending Topics (Dynamic Aggregation from SQLite data)
  // -------------------------------------------------------------
  getTrendingTopics: (): Array<{ tag: string; count: number }> => {
    const db = getSqliteDb();
    if (db) {
      try {
        const rows = db.prepare('SELECT tags, category, title FROM news ORDER BY published_at DESC LIMIT 100').all();
        const countMap: Record<string, number> = {};
        
        for (const r of rows) {
          if (r.tags) {
            const tags = typeof r.tags === 'string' ? JSON.parse(r.tags) : r.tags;
            if (Array.isArray(tags)) {
              for (const t of tags) {
                if (t && typeof t === 'string' && t.trim().length > 1) {
                  const norm = t.trim();
                  countMap[norm] = (countMap[norm] || 0) + 1;
                }
              }
            }
          }
          // Also tally categories as fallback topics if tags are sparse
          if (r.category && typeof r.category === 'string') {
            const catLabel = r.category.toUpperCase().replace('_', ' ');
            countMap[catLabel] = (countMap[catLabel] || 0) + 1;
          }
        }

        const sorted = Object.entries(countMap)
          .map(([tag, count]) => ({ tag, count }))
          .sort((a, b) => b.count - a.count)
          .slice(0, 6);

        if (sorted.length > 0) return sorted;
      } catch (err) {
        console.warn('Error extracting trending topics from SQLite:', err);
      }
    }
    return [
      { tag: 'AI & LLMs', count: 18 },
      { tag: 'Software Dev', count: 15 },
      { tag: 'Cloud Computing', count: 12 },
      { tag: 'Open Source', count: 9 },
      { tag: 'Cybersecurity', count: 6 },
      { tag: 'Developer Tools', count: 5 }
    ];
  },

  // -------------------------------------------------------------
  // Live Agent Stats
  // -------------------------------------------------------------
  getAgentStats: (): AgentStats => {
    const db = getSqliteDb();
    const trending = serverDb.getTrendingTopics();

    if (db) {
      try {
        const statusRow = db.prepare("SELECT * FROM system_status WHERE id = 'current' LIMIT 1").get();
        const oppsCountRow = db.prepare("SELECT COUNT(*) as count FROM opportunities WHERE status IN ('ACTIVE', 'EXPIRING_SOON')").get();
        const sourcesCountRow = db.prepare("SELECT COUNT(*) as count FROM sources WHERE enabled = 1").get();

        const activeOpps = oppsCountRow ? oppsCountRow.count : 4;
        const totalSources = sourcesCountRow ? sourcesCountRow.count : 9;

        if (statusRow) {
          return {
            status: statusRow.status || 'ACTIVE',
            last_scan_time: statusRow.last_scan_time || 'Just now',
            sources_checked: statusRow.sources_checked || totalSources,
            new_opportunities_today: activeOpps,
            next_report_time: statusRow.next_report_time || '9:00 PM IST',
            system_cost: '₹0.00',
            trending_topics: trending
          };
        }
      } catch (err) {
        console.warn('Error reading agent stats from SQLite:', err);
      }
    }
    return {
      ...INITIAL_AGENT_STATS,
      trending_topics: trending
    };
  },

  // -------------------------------------------------------------
  // Saved Bookmarks
  // -------------------------------------------------------------
  getSavedItems: (): { news: string[]; opportunities: string[] } => {
    const db = getSqliteDb();
    if (db) {
      try {
        const rows = db.prepare('SELECT item_type, item_id FROM saved_items ORDER BY saved_at DESC').all();
        if (rows) {
          const news = rows.filter((r: any) => r.item_type === 'news').map((r: any) => r.item_id);
          const opportunities = rows.filter((r: any) => r.item_type === 'opportunity').map((r: any) => r.item_id);
          return { news, opportunities };
        }
      } catch (err) {
        console.warn('Error reading saved items from SQLite:', err);
      }
    }
    return { news: ['news_01'], opportunities: ['opp_01', 'opp_02'] };
  },

  toggleSave: (type: 'news' | 'opportunity', id: string) => {
    const db = getSqliteDb();
    if (db) {
      try {
        const existing = db.prepare('SELECT id FROM saved_items WHERE item_type = ? AND item_id = ?').get(type, id);
        if (existing) {
          db.prepare('DELETE FROM saved_items WHERE item_type = ? AND item_id = ?').run(type, id);
        } else {
          const saveId = `save_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
          db.prepare('INSERT INTO saved_items (id, item_type, item_id) VALUES (?, ?, ?)').run(saveId, type, id);
        }
        return serverDb.getSavedItems();
      } catch (err) {
        console.warn('Error toggling saved item in SQLite:', err);
      }
    }
    return { news: [], opportunities: [] };
  },

  // -------------------------------------------------------------
  // Preferences
  // -------------------------------------------------------------
  getPreferences: (): UserPreferences => {
    const db = getSqliteDb();
    if (db) {
      try {
        const row = db.prepare("SELECT * FROM preferences WHERE id = 'default' LIMIT 1").get();
        if (row) {
          return {
            ...row,
            categories: typeof row.categories === 'string' ? JSON.parse(row.categories || '[]') : row.categories || [],
            keywords: typeof row.keywords === 'string' ? JSON.parse(row.keywords || '[]') : row.keywords || [],
            opportunity_types: typeof row.opportunity_types === 'string' ? JSON.parse(row.opportunity_types || '[]') : row.opportunity_types || [],
            enable_daily_brief: Boolean(row.enable_daily_brief),
            enable_critical_alerts: Boolean(row.enable_critical_alerts)
          };
        }
      } catch (err) {
        console.warn('Error reading preferences from SQLite:', err);
      }
    }
    return INITIAL_PREFERENCES;
  },

  updatePreferences: (newPrefs: Partial<UserPreferences>): UserPreferences => {
    const db = getSqliteDb();
    if (db) {
      try {
        const categories = JSON.stringify(newPrefs.categories || []);
        const keywords = JSON.stringify(newPrefs.keywords || []);
        const opportunityTypes = JSON.stringify(newPrefs.opportunity_types || []);

        db.prepare(`
          INSERT INTO preferences (
            id, user_name, theme, categories, keywords, opportunity_types,
            enable_daily_brief, enable_critical_alerts, ai_provider, updated_at
          ) VALUES ('default', ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
          ON CONFLICT(id) DO UPDATE SET
            user_name=excluded.user_name,
            theme=excluded.theme,
            categories=excluded.categories,
            keywords=excluded.keywords,
            opportunity_types=excluded.opportunity_types,
            enable_daily_brief=excluded.enable_daily_brief,
            enable_critical_alerts=excluded.enable_critical_alerts,
            ai_provider=excluded.ai_provider,
            updated_at=datetime('now')
        `).run(
          newPrefs.user_name || 'Balaji',
          newPrefs.theme || 'system',
          categories,
          keywords,
          opportunityTypes,
          newPrefs.enable_daily_brief ? 1 : 0,
          newPrefs.enable_critical_alerts ? 1 : 0,
          newPrefs.ai_provider || 'fallback'
        );
        return serverDb.getPreferences();
      } catch (err) {
        console.warn('Error updating preferences in SQLite:', err);
      }
    }
    return { ...INITIAL_PREFERENCES, ...newPrefs };
  },

  // -------------------------------------------------------------
  // Universal Search
  // -------------------------------------------------------------
  search: (query: string) => {
    const q = query.toLowerCase().trim();
    if (!q) return { news: [], opportunities: [] };

    const db = getSqliteDb();
    if (db) {
      try {
        const pattern = `%${q}%`;
        const newsRows = db.prepare('SELECT * FROM news WHERE title LIKE ? OR description LIKE ? OR tags LIKE ? LIMIT 15').all(pattern, pattern, pattern);
        const oppsRows = db.prepare('SELECT * FROM opportunities WHERE title LIKE ? OR provider LIKE ? OR description LIKE ? LIMIT 15').all(pattern, pattern, pattern);

        const news = newsRows.map((r: any) => ({
          ...r,
          tags: typeof r.tags === 'string' ? JSON.parse(r.tags || '[]') : r.tags || [],
          summary: {
            what: r.summary_what || r.description,
            why: r.summary_why || '',
            action: r.summary_action || '',
            key_points: typeof r.key_points === 'string' ? JSON.parse(r.key_points || '[]') : r.key_points || []
          }
        }));

        const opportunities = oppsRows.map((r: any) => ({
          ...r,
          is_expiring_soon: Boolean(r.is_expiring_soon)
        }));

        return { news, opportunities };
      } catch (err) {
        console.warn('Error executing search in SQLite:', err);
      }
    }

    const matchingNews = INITIAL_NEWS.filter(n =>
      n.title.toLowerCase().includes(q) ||
      n.description.toLowerCase().includes(q) ||
      n.tags?.some(t => t.toLowerCase().includes(q))
    );

    const matchingOpps = INITIAL_OPPORTUNITIES.filter(o =>
      o.title.toLowerCase().includes(q) ||
      o.provider.toLowerCase().includes(q) ||
      o.description.toLowerCase().includes(q) ||
      o.eligibility.toLowerCase().includes(q)
    );

    return { news: matchingNews, opportunities: matchingOpps };
  }
};
