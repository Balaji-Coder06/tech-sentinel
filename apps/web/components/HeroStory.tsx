'use client';

import React from 'react';
import { NewsItem } from '../lib/types';
import { formatTimeAgo } from '../lib/utils';
import { Sparkles, Clock, ArrowRight, Bookmark } from 'lucide-react';
import { SentinelImage } from './SentinelImage';

interface HeroStoryProps {
  story: NewsItem;
  onSelect: (story: NewsItem) => void;
  onToggleSave?: (id: string) => void;
  isSaved?: boolean;
}

export function HeroStory({ story, onSelect, onToggleSave, isSaved }: HeroStoryProps) {
  return (
    <div className="relative rounded-3xl overflow-hidden border border-sentinel-border bg-sentinel-card shadow-card group cursor-pointer transition-all hover:shadow-card-hover">
      {/* Background Image with Gradient Overlay */}
      <div className="relative h-64 sm:h-80 w-full overflow-hidden bg-neutral-950" onClick={() => onSelect(story)}>
        <SentinelImage
          src={story.image_url}
          alt={story.title}
          category={story.category}
          className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105 opacity-85"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/95 via-black/50 to-black/20" />
        
        {/* Floating Top Badges */}
        <div className="absolute top-4 left-4 right-4 flex items-center justify-between pointer-events-none">
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full bg-sentinel-accent text-white text-xs font-bold uppercase tracking-wider shadow-sm flex items-center gap-1">
              <Sparkles className="w-3 h-3" /> FEATURED STORY
            </span>
            <span className="px-2.5 py-1 rounded-full bg-black/60 backdrop-blur-md text-white/90 text-xs font-semibold uppercase tracking-wider">
              {story.category}
            </span>
          </div>

          {onToggleSave && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onToggleSave(story.id);
              }}
              className="pointer-events-auto p-2 rounded-full bg-black/50 backdrop-blur-md text-white hover:text-sentinel-accent transition-colors"
            >
              <Bookmark className={`w-4 h-4 ${isSaved ? 'fill-sentinel-accent text-sentinel-accent' : ''}`} />
            </button>
          )}
        </div>

        {/* Floating Bottom Content Inside Image */}
        <div className="absolute bottom-4 left-4 right-4 sm:bottom-6 sm:left-6 sm:right-6 text-white space-y-2">
          <div className="flex items-center gap-3 text-xs text-white/70 font-medium">
            <span>{story.source_name}</span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" /> {story.read_time_minutes || 3} min read
            </span>
            <span>•</span>
            <span>{formatTimeAgo(story.published_at)}</span>
          </div>

          <h2 className="text-xl sm:text-2xl lg:text-3xl font-extrabold tracking-tight text-white editorial-headline group-hover:text-orange-200 transition-colors line-clamp-2">
            {story.title}
          </h2>

          <p className="text-xs sm:text-sm text-white/80 line-clamp-2 sm:line-clamp-2 leading-relaxed max-w-3xl">
            {story.summary?.what || story.description}
          </p>
        </div>
      </div>

      {/* Sentinel Quick Summary Pill Bar */}
      <div 
        onClick={() => onSelect(story)}
        className="px-4 sm:px-6 py-3 bg-sentinel-card border-t border-sentinel-border flex items-center justify-between text-xs sm:text-sm font-medium text-sentinel-text hover:bg-sentinel-cardHover transition-colors"
      >
        <div className="flex items-center gap-2 text-sentinel-muted truncate">
          <span className="w-2 h-2 rounded-full bg-sentinel-accent flex-shrink-0" />
          <span className="font-semibold text-sentinel-text">Why it matters:</span>
          <span className="truncate">{story.summary?.why || 'Major technology development.'}</span>
        </div>
        <div className="flex items-center gap-1 text-sentinel-accent font-semibold text-xs flex-shrink-0 ml-2 group-hover:translate-x-1 transition-transform">
          <span>Read analysis</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </div>
      </div>
    </div>
  );
}
