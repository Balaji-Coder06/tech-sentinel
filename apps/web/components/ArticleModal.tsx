'use client';

import React from 'react';
import { NewsItem } from '../lib/types';
import { formatTimeAgo } from '../lib/utils';
import { X, ExternalLink, Bookmark, Sparkles, CheckCircle2, Clock, Share2 } from 'lucide-react';
import { SentinelImage } from './SentinelImage';

interface ArticleModalProps {
  article: NewsItem;
  onClose: () => void;
  onToggleSave?: (id: string) => void;
  isSaved?: boolean;
}

export function ArticleModal({
  article,
  onClose,
  onToggleSave,
  isSaved = false
}: ArticleModalProps) {
  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: article.title,
        text: article.description,
        url: article.url
      }).catch(() => {});
    } else {
      navigator.clipboard.writeText(article.url);
      alert('Link copied to clipboard!');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div 
        className="bg-sentinel-card border border-sentinel-border w-full max-w-2xl max-h-[90vh] rounded-3xl shadow-2xl overflow-hidden flex flex-col relative"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header Actions */}
        <div className="p-4 border-b border-sentinel-border flex items-center justify-between bg-sentinel-card/80 backdrop-blur-md sticky top-0 z-10">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-1 rounded-full bg-sentinel-accent/10 text-sentinel-accent text-xs font-bold uppercase tracking-wider">
              {article.category}
            </span>
            <span className="text-xs text-sentinel-muted">{article.source_name}</span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleShare}
              className="p-2 rounded-full text-sentinel-muted hover:text-sentinel-text hover:bg-sentinel-border/50 transition-colors"
              title="Share"
            >
              <Share2 className="w-4 h-4" />
            </button>

            {onToggleSave && (
              <button
                onClick={() => onToggleSave(article.id)}
                className="p-2 rounded-full text-sentinel-muted hover:text-sentinel-accent hover:bg-sentinel-border/50 transition-colors"
                title="Bookmark"
              >
                <Bookmark className={`w-4 h-4 ${isSaved ? 'fill-sentinel-accent text-sentinel-accent' : ''}`} />
              </button>
            )}

            <button
              onClick={onClose}
              className="p-2 rounded-full text-sentinel-muted hover:text-sentinel-text hover:bg-sentinel-border/50 transition-colors"
              title="Close"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Scrollable Content */}
        <div className="p-5 sm:p-7 overflow-y-auto space-y-6">
          {/* Headline & Metadata */}
          <div className="space-y-3">
            <h2 className="text-xl sm:text-2xl font-black text-sentinel-text leading-tight editorial-headline">
              {article.title}
            </h2>

            <div className="flex items-center gap-3 text-xs text-sentinel-muted font-medium">
              <span className="flex items-center gap-1">
                <Clock className="w-3.5 h-3.5" /> {article.read_time_minutes || 3} min read
              </span>
              <span>•</span>
              <span>{formatTimeAgo(article.published_at)}</span>
            </div>
          </div>

          {/* Article Banner Image */}
          <div className="w-full h-56 sm:h-72 rounded-2xl overflow-hidden bg-neutral-950 border border-sentinel-border/50 shadow-subtle">
            <SentinelImage
              src={article.image_url}
              alt={article.title}
              category={article.category}
              className="w-full h-full object-cover"
            />
          </div>

          {/* Signature Sentinel AI Summary Box */}
          <div className="rounded-2xl border-2 border-sentinel-accent/30 bg-sentinel-accent/5 p-4 sm:p-5 space-y-4">
            <div className="flex items-center gap-2 text-sentinel-accent font-bold text-sm uppercase tracking-wide">
              <Sparkles className="w-4 h-4" />
              <span>SENTINEL AI INTELLIGENCE</span>
            </div>

            <div className="space-y-3 text-xs sm:text-sm">
              <div>
                <span className="font-extrabold text-sentinel-text block mb-0.5">What happened:</span>
                <p className="text-sentinel-muted leading-relaxed">
                  {article.summary?.what || article.description}
                </p>
              </div>

              <div>
                <span className="font-extrabold text-sentinel-text block mb-0.5">Why it matters:</span>
                <p className="text-sentinel-muted leading-relaxed">
                  {article.summary?.why || "Key development impacting the ecosystem."}
                </p>
              </div>

              <div>
                <span className="font-extrabold text-sentinel-text block mb-0.5">What you can do:</span>
                <p className="text-sentinel-muted leading-relaxed">
                  {article.summary?.action || "Evaluate on the official documentation."}
                </p>
              </div>
            </div>
          </div>

          {/* Key Takeaways */}
          {article.summary?.key_points && article.summary.key_points.length > 0 && (
            <div className="space-y-2.5">
              <h4 className="font-bold text-sm text-sentinel-text">Key Takeaways</h4>
              <ul className="space-y-2 text-xs sm:text-sm text-sentinel-muted">
                {article.summary.key_points.map((point, idx) => (
                  <li key={idx} className="flex items-start gap-2">
                    <CheckCircle2 className="w-4 h-4 text-sentinel-success flex-shrink-0 mt-0.5" />
                    <span>{point}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Full Body / Description */}
          {article.content && (
            <div className="space-y-2 pt-2 border-t border-sentinel-border text-xs sm:text-sm text-sentinel-text leading-relaxed">
              <p>{article.content}</p>
            </div>
          )}
        </div>

        {/* Footer Link Out */}
        <div className="p-4 border-t border-sentinel-border bg-sentinel-card/80 backdrop-blur-md flex items-center justify-between gap-3">
          <div className="text-xs text-sentinel-muted truncate">
            Source: <span className="font-semibold text-sentinel-text">{article.source_name}</span>
          </div>

          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="py-2.5 px-5 rounded-xl bg-sentinel-accent hover:bg-sentinel-accentHover text-white font-bold text-xs flex items-center gap-1.5 shadow-sm transition-all active:scale-95 flex-shrink-0"
          >
            <span>Read Original Article</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>
    </div>
  );
}
