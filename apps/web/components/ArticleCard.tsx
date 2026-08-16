'use client';

import React from 'react';
import { NewsItem } from '../lib/types';
import { formatTimeAgo } from '../lib/utils';
import { Clock, Bookmark, Sparkles } from 'lucide-react';
import { SentinelImage } from './SentinelImage';

interface ArticleCardProps {
  article: NewsItem;
  onSelect: (article: NewsItem) => void;
  onToggleSave?: (id: string) => void;
  isSaved?: boolean;
}

export function ArticleCard({
  article,
  onSelect,
  onToggleSave,
  isSaved = false
}: ArticleCardProps) {
  return (
    <article
      onClick={() => onSelect(article)}
      className="p-4 sm:p-5 rounded-2xl border border-sentinel-border bg-sentinel-card shadow-subtle hover:shadow-card hover:border-sentinel-accent/30 transition-all cursor-pointer group flex flex-col sm:flex-row gap-4 items-start justify-between overflow-hidden"
    >
      {/* Left Column: Text Info */}
      <div className="space-y-2 flex-1 min-w-0 w-full">
        <div className="flex items-center gap-2 text-xs text-sentinel-muted flex-wrap">
          <span className="px-2 py-0.5 rounded-md bg-sentinel-border/60 text-sentinel-text font-bold uppercase text-[10px] tracking-wider flex-shrink-0">
            {article.category}
          </span>
          <span className="truncate max-w-[180px] font-medium">{article.source_name}</span>
          <span>•</span>
          <span className="whitespace-nowrap flex-shrink-0">{formatTimeAgo(article.published_at)}</span>
        </div>

        <h3 className="font-bold text-base sm:text-lg text-sentinel-text group-hover:text-sentinel-accent transition-colors leading-snug line-clamp-2">
          {article.title}
        </h3>

        <p className="text-xs sm:text-sm text-sentinel-muted line-clamp-2 leading-relaxed">
          {article.summary?.what || article.description}
        </p>

        {/* Sentinel AI "Why this matters" teaser */}
        {article.summary?.why && (
          <div className="pt-1 flex items-center gap-2 text-xs text-sentinel-muted min-w-0">
            <Sparkles className="w-3.5 h-3.5 text-sentinel-accent flex-shrink-0" />
            <span className="font-semibold text-sentinel-text flex-shrink-0">Why it matters:</span>
            <span className="truncate">{article.summary.why}</span>
          </div>
        )}
      </div>

      {/* Right Column: Dedicated Thumbnail & Bookmark Action */}
      <div className="flex sm:flex-col items-center sm:items-end justify-between sm:justify-start gap-2.5 w-full sm:w-auto flex-shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-sentinel-border/40">
        <div className="w-24 sm:w-32 h-16 sm:h-20 rounded-xl overflow-hidden bg-neutral-950 border border-sentinel-border/40 flex-shrink-0 relative">
          <SentinelImage
            src={article.image_url}
            alt={article.title}
            category={article.category}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          />
        </div>

        {onToggleSave && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onToggleSave(article.id);
            }}
            className="p-1.5 rounded-lg text-sentinel-muted hover:text-sentinel-accent hover:bg-sentinel-border/50 transition-colors flex-shrink-0"
            title="Bookmark article"
          >
            <Bookmark className={`w-4 h-4 ${isSaved ? 'fill-sentinel-accent text-sentinel-accent' : ''}`} />
          </button>
        )}
      </div>
    </article>
  );
}
