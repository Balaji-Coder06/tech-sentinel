'use client';

import React, { useState, useEffect } from 'react';
import { Header } from '../../components/Header';
import { ArticleCard } from '../../components/ArticleCard';
import { OpportunityCard } from '../../components/OpportunityCard';
import { ArticleModal } from '../../components/ArticleModal';
import { ClaimModal } from '../../components/ClaimModal';
import { NewsItem, Opportunity } from '../../lib/types';
import { fetchNews, fetchOpportunities, fetchSavedItems, toggleSavedItem } from '../../lib/api-client';
import { Bookmark, Gift, Flame, Loader2 } from 'lucide-react';

export default function SavedPage() {
  const [activeTab, setActiveTab] = useState<'all' | 'news' | 'opportunities'>('all');
  const [allNews, setAllNews] = useState<NewsItem[]>([]);
  const [allOpps, setAllOpps] = useState<Opportunity[]>([]);
  const [savedItems, setSavedItems] = useState<{ news: string[]; opportunities: string[] }>({
    news: [],
    opportunities: []
  });
  const [loading, setLoading] = useState(true);

  const [selectedArticle, setSelectedArticle] = useState<NewsItem | null>(null);
  const [selectedOpportunity, setSelectedOpportunity] = useState<Opportunity | null>(null);

  useEffect(() => {
    async function loadSaved() {
      setLoading(true);
      try {
        const [newsData, oppsData, savedData] = await Promise.all([
          fetchNews(),
          fetchOpportunities(),
          fetchSavedItems()
        ]);
        setAllNews(newsData);
        setAllOpps(oppsData);
        setSavedItems(savedData);
      } catch (err) {
        console.error('Failed to load saved items:', err);
      } finally {
        setLoading(false);
      }
    }
    loadSaved();
  }, []);

  const savedNews = allNews.filter(n => savedItems.news.includes(n.id));
  const savedOpps = allOpps.filter(o => savedItems.opportunities.includes(o.id));

  const handleToggleSaveNews = async (id: string) => {
    const updated = await toggleSavedItem('news', id);
    setSavedItems({ ...updated });
  };

  const handleToggleSaveOpp = async (id: string) => {
    const updated = await toggleSavedItem('opportunity', id);
    setSavedItems({ ...updated });
  };

  return (
    <div className="flex-1 flex flex-col min-w-0">
      <Header userName="Balaji" />

      <main className="flex-1 max-w-5xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Bookmark className="w-5 h-5 text-sentinel-accent" />
            <h2 className="text-2xl sm:text-3xl font-black tracking-tight text-sentinel-text">
              Saved Bookmarks
            </h2>
          </div>
          <p className="text-xs sm:text-sm text-sentinel-muted">
            Your saved opportunities and high-impact technology articles for quick access.
          </p>
        </div>

        {/* Tab Filters */}
        <div className="flex gap-2 border-b border-sentinel-border pb-3">
          <button
            onClick={() => setActiveTab('all')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'all'
                ? 'bg-sentinel-accent text-white shadow-sm'
                : 'bg-sentinel-card border border-sentinel-border text-sentinel-muted hover:text-sentinel-text'
            }`}
          >
            All Saved ({savedNews.length + savedOpps.length})
          </button>
          <button
            onClick={() => setActiveTab('opportunities')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
              activeTab === 'opportunities'
                ? 'bg-sentinel-accent text-white shadow-sm'
                : 'bg-sentinel-card border border-sentinel-border text-sentinel-muted hover:text-sentinel-text'
            }`}
          >
            <Gift className="w-3.5 h-3.5" />
            <span>Opportunities ({savedOpps.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('news')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
              activeTab === 'news'
                ? 'bg-sentinel-accent text-white shadow-sm'
                : 'bg-sentinel-card border border-sentinel-border text-sentinel-muted hover:text-sentinel-text'
            }`}
          >
            <Flame className="w-3.5 h-3.5" />
            <span>Articles ({savedNews.length})</span>
          </button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-sentinel-accent animate-spin" />
          </div>
        ) : (
          <>
            {/* Saved Opportunities Section */}
            {(activeTab === 'all' || activeTab === 'opportunities') && savedOpps.length > 0 && (
              <div className="space-y-3">
                <h3 className="text-sm font-bold text-sentinel-text uppercase tracking-wider flex items-center gap-1.5">
                  <Gift className="w-4 h-4 text-sentinel-accent" />
                  <span>Bookmarked Opportunities</span>
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {savedOpps.map((opp) => (
                    <OpportunityCard
                      key={opp.id}
                      opportunity={opp}
                      onClaim={setSelectedOpportunity}
                      onToggleSave={handleToggleSaveOpp}
                      isSaved={true}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Saved News Section */}
            {(activeTab === 'all' || activeTab === 'news') && savedNews.length > 0 && (
              <div className="space-y-3 pt-4">
                <h3 className="text-sm font-bold text-sentinel-text uppercase tracking-wider flex items-center gap-1.5">
                  <Flame className="w-4 h-4 text-sentinel-accent" />
                  <span>Bookmarked Articles</span>
                </h3>
                <div className="space-y-3">
                  {savedNews.map((item) => (
                    <ArticleCard
                      key={item.id}
                      article={item}
                      onSelect={setSelectedArticle}
                      onToggleSave={handleToggleSaveNews}
                      isSaved={true}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Empty State */}
            {savedNews.length === 0 && savedOpps.length === 0 && (
              <div className="py-20 text-center space-y-3 rounded-3xl border border-sentinel-border bg-sentinel-card p-6">
                <Bookmark className="w-10 h-10 text-sentinel-muted mx-auto" />
                <h3 className="font-bold text-base text-sentinel-text">No bookmarks saved yet</h3>
                <p className="text-xs text-sentinel-muted max-w-sm mx-auto">
                  Click the bookmark icon on any article or free opportunity to save it here for later.
                </p>
              </div>
            )}
          </>
        )}
      </main>

      {/* Article Detail Modal */}
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
