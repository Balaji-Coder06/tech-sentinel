'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { Header } from '../../components/Header';
import { ArticleCard } from '../../components/ArticleCard';
import { ArticleModal } from '../../components/ArticleModal';
import { NewsItem } from '../../lib/types';
import { fetchNewsWithCategories, fetchSavedItems, fetchPreferences, toggleSavedItem } from '../../lib/api-client';
import { Flame, Sparkles, Loader2 } from 'lucide-react';

interface CategoryItem {
  id: string;
  label: string;
  count: number;
}

function NewsFeedContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const categoryParam = searchParams.get('category')?.toLowerCase().trim() || 'all';

  const [activeCategory, setActiveCategory] = useState(categoryParam);
  const [categories, setCategories] = useState<CategoryItem[]>([]);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [savedItems, setSavedItems] = useState<{ news: string[]; opportunities: string[] }>({
    news: [],
    opportunities: []
  });
  const [loading, setLoading] = useState(true);
  const [selectedArticle, setSelectedArticle] = useState<NewsItem | null>(null);

  // Synchronize activeCategory if query param changes externally
  useEffect(() => {
    if (categoryParam !== activeCategory) {
      setActiveCategory(categoryParam);
    }
  }, [categoryParam]);

  useEffect(() => {
    async function loadNewsData() {
      setLoading(true);
      try {
        const [prefsData, savedData] = await Promise.all([
          fetchPreferences(),
          fetchSavedItems()
        ]);
        setSavedItems(savedData);

        const userSelectedCategories = prefsData?.categories && prefsData.categories.length > 0
          ? prefsData.categories
          : undefined;

        const { news: newsData, categories: catData } = await fetchNewsWithCategories(
          activeCategory,
          'intelligence',
          userSelectedCategories
        );

        setNews(newsData);
        if (catData && catData.length > 0) {
          setCategories(catData);
        }
      } catch (err) {
        console.error('Failed to load news:', err);
      } finally {
        setLoading(false);
      }
    }
    loadNewsData();
  }, [activeCategory]);

  const handleCategoryChange = (catId: string) => {
    setActiveCategory(catId);
    if (catId === 'all') {
      router.replace('/news');
    } else {
      router.replace(`/news?category=${encodeURIComponent(catId)}`);
    }
  };

  const handleToggleSave = async (id: string) => {
    const updated = await toggleSavedItem('news', id);
    setSavedItems({ ...updated });
  };

  // Dynamically compute total news records across all categories
  const totalNewsCount = categories.reduce((acc, c) => acc + c.count, 0);
  const dynamicTabs = [
    { id: 'all', label: 'All News', count: totalNewsCount },
    ...categories
  ];

  return (
    <div className="flex-1 flex flex-col min-w-0">
      <Header />

      <main className="flex-1 max-w-5xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        {/* Page Header */}
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Flame className="w-5 h-5 text-sentinel-accent" />
            <h2 className="text-2xl sm:text-3xl font-black tracking-tight text-sentinel-text">
              Technology News Intelligence
            </h2>
          </div>
          <p className="text-xs sm:text-sm text-sentinel-muted">
            Curated, verified, and AI-summarized developments across the global technology ecosystem.
          </p>
        </div>

        {/* Dynamic Data-Driven Category Filter Tabs */}
        <div className="flex gap-2 overflow-x-auto pb-2 no-scrollbar">
          {dynamicTabs.map((cat) => (
            <button
              key={cat.id}
              onClick={() => handleCategoryChange(cat.id)}
              className={`px-4 py-2 rounded-full text-xs font-bold whitespace-nowrap transition-all flex items-center gap-1.5 ${
                activeCategory === cat.id
                  ? 'bg-sentinel-accent text-white shadow-sm'
                  : 'border border-sentinel-border bg-sentinel-card text-sentinel-muted hover:text-sentinel-text hover:border-sentinel-accent/40'
              }`}
            >
              <span>{cat.label}</span>
              {cat.count > 0 && (
                <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono font-normal ${
                  activeCategory === cat.id ? 'bg-white/25 text-white' : 'bg-sentinel-border/70 text-sentinel-muted'
                }`}>
                  {cat.count}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Articles Feed */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-sentinel-accent animate-spin" />
          </div>
        ) : (
          <div className="space-y-4">
            {news.length > 0 ? (
              news.map((item) => (
                <ArticleCard
                  key={item.id}
                  article={item}
                  onSelect={setSelectedArticle}
                  onToggleSave={handleToggleSave}
                  isSaved={savedItems.news.includes(item.id)}
                />
              ))
            ) : (
              <div className="py-16 text-center space-y-2 rounded-3xl border border-sentinel-border bg-sentinel-card p-6">
                <Sparkles className="w-8 h-8 text-sentinel-accent mx-auto animate-pulse" />
                <h3 className="font-bold text-sm text-sentinel-text">No articles found in this category</h3>
                <p className="text-xs text-sentinel-muted">Try selecting &ldquo;All News&rdquo; to explore other categories.</p>
              </div>
            )}
          </div>
        )}
      </main>

      {selectedArticle && (
        <ArticleModal
          article={selectedArticle}
          onClose={() => setSelectedArticle(null)}
          onToggleSave={handleToggleSave}
          isSaved={savedItems.news.includes(selectedArticle.id)}
        />
      )}
    </div>
  );
}

export default function NewsPage() {
  return (
    <Suspense fallback={
      <div className="flex-1 flex flex-col min-w-0">
        <Header />
        <div className="flex-1 flex items-center justify-center min-h-[60vh]">
          <Loader2 className="w-8 h-8 text-sentinel-accent animate-spin" />
        </div>
      </div>
    }>
      <NewsFeedContent />
    </Suspense>
  );
}
