import { NewsItem, Opportunity, DailyReport, UserPreferences, AgentStats } from './types';
import { INITIAL_NEWS, INITIAL_OPPORTUNITIES, INITIAL_REPORT, INITIAL_PREFERENCES, INITIAL_AGENT_STATS } from './mock-data';

// Persistent memory bridge with initial state fallback
let newsStore: NewsItem[] = [...INITIAL_NEWS];
let opportunitiesStore: Opportunity[] = [...INITIAL_OPPORTUNITIES];
let reportsStore: DailyReport[] = [INITIAL_REPORT];
let preferencesStore: UserPreferences = { ...INITIAL_PREFERENCES };
let savedItemsStore: { news: string[]; opportunities: string[] } = {
  news: ['news_01'],
  opportunities: ['opp_01', 'opp_02']
};

export const dbClient = {
  // News
  getNews: (category?: string): NewsItem[] => {
    if (!category || category.toLowerCase() === 'all') return newsStore;
    return newsStore.filter(item => item.category.toLowerCase() === category.toLowerCase());
  },
  getNewsById: (id: string): NewsItem | undefined => newsStore.find(item => item.id === id),
  upsertNews: (items: NewsItem[]) => {
    for (const item of items) {
      const idx = newsStore.findIndex(n => n.url === item.url || n.id === item.id);
      if (idx >= 0) newsStore[idx] = item;
      else newsStore.unshift(item);
    }
  },

  // Opportunities
  getOpportunities: (type?: string, status?: string): Opportunity[] => {
    return opportunitiesStore.filter(opp => {
      if (type && type !== 'all' && opp.opportunity_type !== type && opp.category !== type) {
        return false;
      }
      if (status && status !== 'all' && opp.status !== status) {
        return false;
      }
      return true;
    });
  },
  getOpportunityById: (id: string): Opportunity | undefined => opportunitiesStore.find(opp => opp.id === id),
  upsertOpportunities: (opps: Opportunity[]) => {
    for (const opp of opps) {
      const idx = opportunitiesStore.findIndex(o => o.claim_url === opp.claim_url || o.id === opp.id);
      if (idx >= 0) opportunitiesStore[idx] = opp;
      else opportunitiesStore.unshift(opp);
    }
  },

  // Daily Reports
  getDailyReports: (): DailyReport[] => reportsStore,
  getLatestReport: (): DailyReport => reportsStore[0],
  getReportByDate: (date: string): DailyReport | undefined => reportsStore.find(r => r.date === date),
  upsertReport: (report: DailyReport) => {
    const idx = reportsStore.findIndex(r => r.date === report.date);
    if (idx >= 0) reportsStore[idx] = report;
    else reportsStore.unshift(report);
  },

  // User Preferences
  getPreferences: (): UserPreferences => preferencesStore,
  updatePreferences: (newPrefs: Partial<UserPreferences>): UserPreferences => {
    preferencesStore = { ...preferencesStore, ...newPrefs };
    return preferencesStore;
  },

  // Saved Bookmarks
  getSavedItems: (): { news: string[]; opportunities: string[] } => savedItemsStore,
  toggleSave: (type: 'news' | 'opportunity', id: string) => {
    const list = type === 'news' ? savedItemsStore.news : savedItemsStore.opportunities;
    const index = list.indexOf(id);
    if (index >= 0) {
      list.splice(index, 1);
    } else {
      list.push(id);
    }
    return savedItemsStore;
  },

  // Live Dynamic Stats
  getAgentStats: (): AgentStats => {
    const activeOpps = opportunitiesStore.filter(o => o.status === 'ACTIVE' || o.status === 'EXPIRING_SOON').length;
    return {
      status: 'ACTIVE',
      last_scan_time: 'Just now',
      sources_checked: 9,
      new_opportunities_today: activeOpps,
      next_report_time: '9:00 PM IST',
      system_cost: '₹0.00'
    };
  },

  // Universal Search
  search: (query: string) => {
    const q = query.toLowerCase().trim();
    if (!q) return { news: [], opportunities: [] };

    const matchingNews = newsStore.filter(n =>
      n.title.toLowerCase().includes(q) ||
      n.description.toLowerCase().includes(q) ||
      n.tags?.some(t => t.toLowerCase().includes(q))
    );

    const matchingOpps = opportunitiesStore.filter(o =>
      o.title.toLowerCase().includes(q) ||
      o.provider.toLowerCase().includes(q) ||
      o.description.toLowerCase().includes(q) ||
      o.eligibility.toLowerCase().includes(q)
    );

    return { news: matchingNews, opportunities: matchingOpps };
  }
};
