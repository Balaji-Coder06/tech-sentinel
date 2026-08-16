'use client';

import React, { useState, useEffect } from 'react';
import { NewsItem, Opportunity } from '../lib/types';
import { dbClient } from '../lib/db';
import { Search, X, Flame, Gift, ArrowRight, Loader2 } from 'lucide-react';

interface SearchModalProps {
  onClose: () => void;
  onSelectNews?: (item: NewsItem) => void;
  onSelectOpp?: (opp: Opportunity) => void;
}

export function SearchModal({ onClose, onSelectNews, onSelectOpp }: SearchModalProps) {
  const [query, setQuery] = useState('');
  const [newsResults, setNewsResults] = useState<NewsItem[]>([]);
  const [oppResults, setOppResults] = useState<Opportunity[]>([]);
  const [searching, setSearching] = useState(false);

  const suggestions = [
    'free AI tools',
    'AWS credits',
    'student certifications',
    'hackathons',
    'Claude 3.7',
    'Copilot free'
  ];

  useEffect(() => {
    if (!query.trim()) {
      setNewsResults([]);
      setOppResults([]);
      setSearching(false);
      return;
    }

    const timer = setTimeout(async () => {
      setSearching(true);
      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        if (res.ok) {
          const json = await res.json();
          if (json.data) {
            setNewsResults(json.data.news || []);
            setOppResults(json.data.opportunities || []);
            setSearching(false);
            return;
          }
        }
      } catch {
        // Fallback to local search
      }
      const { news, opportunities } = dbClient.search(query);
      setNewsResults(news);
      setOppResults(opportunities);
      setSearching(false);
    }, 200);

    return () => clearTimeout(timer);
  }, [query]);

  // Handle ESC key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center p-3 sm:p-6 pt-16 sm:pt-20 bg-black/70 backdrop-blur-sm animate-in fade-in duration-150">
      <div
        className="bg-sentinel-card border border-sentinel-border w-full max-w-2xl rounded-3xl shadow-2xl overflow-hidden flex flex-col relative animate-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input Bar */}
        <div className="p-4 border-b border-sentinel-border flex items-center gap-3 bg-sentinel-card/90">
          <Search className="w-5 h-5 text-sentinel-accent flex-shrink-0" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search technology, AI tools, cloud credits, certifications..."
            className="w-full bg-transparent text-sm sm:text-base font-medium text-sentinel-text placeholder:text-sentinel-muted focus:outline-none"
            autoFocus
          />
          {searching && <Loader2 className="w-4 h-4 text-sentinel-accent animate-spin flex-shrink-0" />}
          {query && !searching && (
            <button
              onClick={() => setQuery('')}
              className="p-1 rounded-full text-sentinel-muted hover:text-sentinel-text"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          <button
            onClick={onClose}
            className="px-2.5 py-1 rounded-lg bg-sentinel-border/50 text-xs font-semibold text-sentinel-muted hover:text-sentinel-text"
          >
            ESC
          </button>
        </div>

        {/* Suggestion Chips (when query is empty) */}
        {!query && (
          <div className="p-5 space-y-3">
            <span className="text-xs font-bold text-sentinel-muted uppercase tracking-wider block">
              Suggested Searches
            </span>
            <div className="flex flex-wrap gap-2">
              {suggestions.map((s) => (
                <button
                  key={s}
                  onClick={() => setQuery(s)}
                  className="px-3 py-1.5 rounded-full border border-sentinel-border bg-sentinel-card hover:border-sentinel-accent/40 text-xs font-medium text-sentinel-text transition-all hover:scale-105"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Search Results Area */}
        {query && (
          <div className="p-4 sm:p-5 overflow-y-auto max-h-[65vh] space-y-6">
            {/* Free Opportunities Results */}
            {oppResults.length > 0 && (
              <div className="space-y-2.5">
                <div className="flex items-center gap-2 text-xs font-extrabold text-sentinel-accent uppercase tracking-wider">
                  <Gift className="w-4 h-4" />
                  <span>Free Opportunities ({oppResults.length})</span>
                </div>
                <div className="space-y-2">
                  {oppResults.map((opp) => (
                    <div
                      key={opp.id}
                      onClick={() => {
                        if (onSelectOpp) onSelectOpp(opp);
                        onClose();
                      }}
                      className="p-3 rounded-xl border border-sentinel-border bg-sentinel-card hover:bg-sentinel-border/30 transition-all cursor-pointer flex items-center justify-between gap-3 group"
                    >
                      <div className="space-y-0.5 min-w-0">
                        <span className="text-xs font-bold text-sentinel-text group-hover:text-sentinel-accent transition-colors block truncate">
                          {opp.title}
                        </span>
                        <div className="flex items-center gap-2 text-[11px] text-sentinel-muted">
                          <span className="font-semibold text-sentinel-text">{opp.provider}</span>
                          <span>•</span>
                          <span className="text-sentinel-accent font-bold">{opp.current_value}</span>
                        </div>
                      </div>
                      <ArrowRight className="w-4 h-4 text-sentinel-muted group-hover:text-sentinel-accent group-hover:translate-x-0.5 transition-all flex-shrink-0" />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* News Items Results */}
            {newsResults.length > 0 && (
              <div className="space-y-2.5">
                <div className="flex items-center gap-2 text-xs font-extrabold text-sentinel-text uppercase tracking-wider">
                  <Flame className="w-4 h-4 text-sentinel-accent" />
                  <span>News & Updates ({newsResults.length})</span>
                </div>
                <div className="space-y-2">
                  {newsResults.map((item) => (
                    <div
                      key={item.id}
                      onClick={() => {
                        if (onSelectNews) onSelectNews(item);
                        onClose();
                      }}
                      className="p-3 rounded-xl border border-sentinel-border bg-sentinel-card hover:bg-sentinel-border/30 transition-all cursor-pointer flex items-center justify-between gap-3 group"
                    >
                      <div className="space-y-0.5 min-w-0">
                        <span className="text-xs font-bold text-sentinel-text group-hover:text-sentinel-accent transition-colors block truncate">
                          {item.title}
                        </span>
                        <div className="flex items-center gap-2 text-[11px] text-sentinel-muted">
                          <span>{item.source_name}</span>
                          <span>•</span>
                          <span className="uppercase">{item.category}</span>
                        </div>
                      </div>
                      <ArrowRight className="w-4 h-4 text-sentinel-muted group-hover:text-sentinel-accent group-hover:translate-x-0.5 transition-all flex-shrink-0" />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Empty State */}
            {!searching && newsResults.length === 0 && oppResults.length === 0 && (
              <div className="py-10 text-center space-y-2">
                <p className="text-sm font-bold text-sentinel-text">No results found for &ldquo;{query}&rdquo;</p>
                <p className="text-xs text-sentinel-muted">
                  Try searching for keywords like AI, Cloud, GitHub, Credits, or Hackathons.
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
