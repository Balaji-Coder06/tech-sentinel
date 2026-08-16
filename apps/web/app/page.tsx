'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Header } from '../components/Header';
import { HeroStory } from '../components/HeroStory';
import { ForYouCarousel } from '../components/ForYouCarousel';
import { FreeBeforeItsGone } from '../components/FreeBeforeItsGone';
import { ArticleCard } from '../components/ArticleCard';
import { ArticleModal } from '../components/ArticleModal';
import { ClaimModal } from '../components/ClaimModal';
import { DailyBriefCard } from '../components/DailyBriefCard';
import { AgentStatusWidget } from '../components/AgentStatusWidget';
import { NewsItem, Opportunity, DailyReport, AgentStats, UserPreferences } from '../lib/types';
import { calculateFreshnessScore, calculateIntelligenceScore, rankNewsItems } from '../lib/ranking';
import { rankOpportunities, calculateUrgencyScore } from '../lib/opportunity-ranking';
import { 
  fetchNews, 
  fetchOpportunities, 
  fetchReports, 
  fetchAgentStats, 
  fetchSavedItems, 
  fetchPreferences,
  toggleSavedItem 
} from '../lib/api-client';
import { Flame, Clock, ArrowRight, Zap, Loader2, Sparkles } from 'lucide-react';

export default function HomePage() {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [report, setReport] = useState<DailyReport | null>(null);
  const [prefs, setPrefs] = useState<UserPreferences | null>(null);
  const [stats, setStats] = useState<AgentStats>({
    status: 'ACTIVE',
    last_scan_time: 'Just now',
    sources_checked: 9,
    new_opportunities_today: 4,
    next_report_time: '9:00 PM IST',
    system_cost: '₹0.00'
  });
  const [savedItems, setSavedItems] = useState<{ news: string[]; opportunities: string[] }>({
    news: [],
    opportunities: []
  });

  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedArticle, setSelectedArticle] = useState<NewsItem | null>(null);
  const [selectedOpportunity, setSelectedOpportunity] = useState<Opportunity | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [newsData, oppsData, reportsData, statsData, savedData, prefsData] = await Promise.all([
          fetchNews(undefined, 'intelligence'),
          fetchOpportunities(undefined, undefined, 'score'),
          fetchReports(),
          fetchAgentStats(),
          fetchSavedItems(),
          fetchPreferences()
        ]);
        setNews(newsData);
        setOpportunities(oppsData);
        if (reportsData.length > 0) setReport(reportsData[0]);
        setStats(statsData);
        setSavedItems(savedData);
        if (prefsData) setPrefs(prefsData);
      } catch (err) {
        console.error('Failed to load initial data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  // -------------------------------------------------------------
  // Dynamic Intelligence-Ranked & Personalized Distribution
  // -------------------------------------------------------------
  const userPrefConfig = prefs ? { categories: prefs.categories, keywords: prefs.keywords } : undefined;

  // 1. Featured Hero: Select highest-ranked fresh candidate (within 7d), preferring media assets
  const topCandidates = rankNewsItems(news.slice(0, 15), undefined, userPrefConfig);
  const heroStory = topCandidates.find(n => calculateFreshnessScore(n.published_at) >= 6 && Boolean(n.image_url)) ||
                    topCandidates.find(n => calculateFreshnessScore(n.published_at) >= 6) ||
                    news[0];

  const remainingNews = heroStory ? news.filter(n => n.id !== heroStory.id) : news;

  // 2. For You Carousel: Personalized intelligence strictly filtered & ranked by user preferences
  const userAllowedCategories = (prefs?.categories && prefs.categories.length > 0)
    ? prefs.categories.map(c => c.toLowerCase().trim())
    : undefined;

  const forYouCandidatePool = userAllowedCategories
    ? remainingNews.filter(n => userAllowedCategories.includes((n.category || '').toLowerCase().trim()))
    : remainingNews;

  const personalizedRemaining = rankNewsItems(forYouCandidatePool, undefined, userPrefConfig);
  const forYouItems = personalizedRemaining.slice(0, 4);

  // Distinct pool for subsequent sections (ensures 100% zero overlap)
  const nonForYouRemaining = remainingNews.filter(n => !forYouItems.some(f => f.id === n.id));

  // 3. Don't Miss: Next 3 high-value distinct items
  const dontMissItems = nonForYouRemaining.slice(0, 3);

  // 4. Latest Intelligence Stream (Global): Explicitly bypasses preference filtering to show ALL categories chronologically
  const feedItems = nonForYouRemaining.slice(3).sort((a, b) => {
    const timeA = new Date(a.published_at || 0).getTime();
    const timeB = new Date(b.published_at || 0).getTime();
    return timeB - timeA;
  });

  // 5. Active Verified Opportunities: Ranked with user's Free Radar preferences
  const activeOpportunities = rankOpportunities(
    opportunities,
    'score',
    undefined,
    prefs?.opportunity_types
  );

  // 6. Expiring Soon watchlist (Strictly active offers with urgent deadlines, sorted nearest first)
  const expiringItems = opportunities
    .filter(o => {
      if (o.status === 'EXPIRED') return false;
      if (o.is_expiring_soon || o.status === 'EXPIRING_SOON') return true;
      if (o.expiry_date) {
        const lower = o.expiry_date.toLowerCase();
        if (lower === 'ongoing' || lower === 'perpetual') return false;
        return lower.includes('day') || lower.includes('hour') || lower.includes('soon') || lower.includes('ends');
      }
      return false;
    })
    .sort((a, b) => calculateUrgencyScore(b) - calculateUrgencyScore(a));

  // 7. Dynamic Trending Topics
  const trendingTopics = stats.trending_topics && stats.trending_topics.length > 0
    ? stats.trending_topics
    : [
        { tag: 'AI & LLMs', count: 18 },
        { tag: 'Software Dev', count: 15 },
        { tag: 'Cloud Computing', count: 12 },
        { tag: 'Open Source', count: 9 },
        { tag: 'Cybersecurity', count: 6 },
        { tag: 'Developer Tools', count: 5 }
      ];

  const handleToggleSaveNews = async (id: string) => {
    const updated = await toggleSavedItem('news', id);
    setSavedItems({ ...updated });
  };

  const handleToggleSaveOpp = async (id: string) => {
    const updated = await toggleSavedItem('opportunity', id);
    setSavedItems({ ...updated });
  };

  const handleRefreshRadar = async () => {
    setIsRefreshing(true);
    try {
      const [newStats, latestNews, latestOpps, reportsData] = await Promise.all([
        fetchAgentStats(),
        fetchNews(),
        fetchOpportunities(),
        fetchReports()
      ]);
      setStats(newStats);
      setNews(latestNews);
      setOpportunities(latestOpps);
      if (reportsData.length > 0) setReport(reportsData[0]);
    } catch (err) {
      console.warn('Radar refresh warning:', err);
    } finally {
      setIsRefreshing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex flex-col min-w-0">
        <Header userName="Balaji" />
        <div className="flex-1 flex items-center justify-center min-h-[60vh]">
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="w-8 h-8 text-sentinel-accent animate-spin" />
            <p className="text-xs font-bold text-sentinel-muted tracking-wider uppercase">
              Loading Tech Sentinel Intelligence...
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-w-0">
      <Header userName="Balaji" />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        {/* 3-Column Layout (Main 70% + Right Rail 30%) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Main Content Stream (8 Cols) */}
          <div className="lg:col-span-8 space-y-8">
            
            {/* 1. Hero Editorial Story */}
            {heroStory ? (
              <HeroStory
                story={heroStory}
                onSelect={setSelectedArticle}
                onToggleSave={handleToggleSaveNews}
                isSaved={savedItems.news.includes(heroStory.id)}
              />
            ) : (
              <div className="p-8 rounded-3xl border border-sentinel-border bg-sentinel-card text-center space-y-2">
                <Sparkles className="w-8 h-8 text-sentinel-accent mx-auto animate-pulse" />
                <h3 className="font-bold text-sm text-sentinel-text">No articles ingested yet</h3>
                <p className="text-xs text-sentinel-muted">Run collection pipeline to ingest live intelligence feeds.</p>
              </div>
            )}

            {/* 2. Signature "Free Before It's Gone" Section */}
            {activeOpportunities.length > 0 && (
              <FreeBeforeItsGone
                opportunities={activeOpportunities}
                onClaim={setSelectedOpportunity}
                onToggleSave={handleToggleSaveOpp}
                savedIds={savedItems.opportunities}
              />
            )}

            {/* 3. For You Horizontal Carousel */}
            {forYouItems.length > 0 && (
              <ForYouCarousel
                items={forYouItems}
                onSelect={setSelectedArticle}
              />
            )}

            {/* 4. Don't Miss Today (Fast Bullet Scanning - Zero Duplication) */}
            {dontMissItems.length > 0 && (
              <section className="p-5 rounded-3xl border border-sentinel-border bg-sentinel-card shadow-subtle space-y-3">
                <div className="flex items-center gap-2 text-sentinel-accent font-extrabold text-sm uppercase tracking-wide">
                  <Zap className="w-4 h-4 fill-sentinel-accent" />
                  <span>Don&apos;t Miss — Rapid Intelligence</span>
                </div>
                <ul className="space-y-2.5 text-xs sm:text-sm text-sentinel-text divide-y divide-sentinel-border/50">
                  {dontMissItems.map((item, idx) => (
                    <li
                      key={item.id}
                      onClick={() => setSelectedArticle(item)}
                      className="pt-2 first:pt-0 flex items-center justify-between gap-3 cursor-pointer group hover:text-sentinel-accent transition-colors"
                    >
                      <div className="flex items-center gap-2.5 truncate">
                        <span className="font-mono text-sentinel-muted font-bold text-xs">0{idx + 1}</span>
                        <span className="truncate font-semibold">{item.title}</span>
                      </div>
                      <ArrowRight className="w-3.5 h-3.5 text-sentinel-muted group-hover:text-sentinel-accent group-hover:translate-x-1 transition-all flex-shrink-0" />
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {/* 5. Latest News Feed List */}
            <section className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Flame className="w-4 h-4 text-sentinel-accent" />
                  <h3 className="text-base sm:text-lg font-bold tracking-tight text-sentinel-text">
                    Latest Intelligence Stream
                  </h3>
                </div>
                <Link
                  href="/news"
                  className="text-xs font-semibold text-sentinel-accent hover:text-sentinel-accentHover flex items-center gap-1 group"
                >
                  <span>View full feed</span>
                  <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-0.5" />
                </Link>
              </div>

              <div className="space-y-3.5">
                {feedItems.length > 0 ? (
                  feedItems.map((item) => (
                    <ArticleCard
                      key={item.id}
                      article={item}
                      onSelect={setSelectedArticle}
                      onToggleSave={handleToggleSaveNews}
                      isSaved={savedItems.news.includes(item.id)}
                    />
                  ))
                ) : (
                  <p className="text-xs text-sentinel-muted py-4 text-center">
                    All latest intelligence is highlighted in the sections above.
                  </p>
                )}
              </div>
            </section>
          </div>

          {/* Right Rail (4 Cols) */}
          <aside className="lg:col-span-4 space-y-6">
            {/* Sentinel Radar Live Widget */}
            <AgentStatusWidget
              stats={stats}
              onRefresh={handleRefreshRadar}
              isRefreshing={isRefreshing}
            />

            {/* Daily Brief Column */}
            {report && <DailyBriefCard report={report} />}

            {/* Expiring Soon Watchlist */}
            <div className="rounded-3xl border border-sentinel-border bg-sentinel-card p-5 shadow-subtle space-y-3.5">
              <div className="flex items-center justify-between border-b border-sentinel-border pb-2.5">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-amber-500 animate-pulse" />
                  <h4 className="font-extrabold text-xs text-sentinel-text uppercase tracking-wider">
                    Expiring Soon
                  </h4>
                </div>
                <span className="text-[10px] font-bold text-amber-600 dark:text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded-full">
                  Action Required
                </span>
              </div>

              <div className="space-y-2.5">
                {expiringItems.length > 0 ? (
                  expiringItems.map((opp) => (
                    <div
                      key={opp.id}
                      onClick={() => setSelectedOpportunity(opp)}
                      className="p-3 rounded-2xl border border-sentinel-border/80 bg-sentinel-border/20 hover:bg-sentinel-border/40 transition-all cursor-pointer space-y-1 group"
                    >
                      <div className="flex items-center justify-between text-[10px]">
                        <span className="font-bold text-sentinel-accent">{opp.provider}</span>
                        <span className="font-mono text-amber-600 dark:text-amber-400 font-bold">
                          {opp.expiry_date ? 'Ends Soon' : 'Limited'}
                        </span>
                      </div>
                      <h5 className="font-bold text-xs text-sentinel-text group-hover:text-sentinel-accent transition-colors line-clamp-1">
                        {opp.title}
                      </h5>
                      <span className="text-[11px] font-extrabold text-sentinel-success block">
                        {opp.current_value} ({opp.normal_value})
                      </span>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-sentinel-muted text-center py-3">
                    No offers currently in critical countdown.
                  </p>
                )}
              </div>
            </div>

            {/* Trending Topics (Dynamic Aggregation from SQLite) */}
            <div className="rounded-3xl border border-sentinel-border bg-sentinel-card p-5 shadow-subtle space-y-3">
              <h4 className="font-extrabold text-xs text-sentinel-text uppercase tracking-wider">
                Trending Topics
              </h4>
              <div className="flex flex-wrap gap-2">
                {trendingTopics.map((t) => (
                  <Link
                    key={t.tag}
                    href={`/news?category=${encodeURIComponent(t.tag.toLowerCase().replace(/\s+/g, '_'))}`}
                    className="px-3 py-1.5 rounded-full border border-sentinel-border bg-sentinel-border/20 hover:border-sentinel-accent/40 text-xs font-medium text-sentinel-text transition-all hover:scale-105 flex items-center gap-1.5"
                  >
                    <span>{t.tag}</span>
                    <span className="text-[10px] text-sentinel-muted font-mono">{t.count}</span>
                  </Link>
                ))}
              </div>
            </div>
          </aside>
        </div>
      </main>

      {/* Article Detail Reading Modal */}
      {selectedArticle && (
        <ArticleModal
          article={selectedArticle}
          onClose={() => setSelectedArticle(null)}
          onToggleSave={handleToggleSaveNews}
          isSaved={savedItems.news.includes(selectedArticle.id)}
        />
      )}

      {/* Opportunity Claim Modal */}
      {selectedOpportunity && (
        <ClaimModal
          opportunity={selectedOpportunity}
          onClose={() => setSelectedOpportunity(null)}
        />
      )}
    </div>
  );
}
