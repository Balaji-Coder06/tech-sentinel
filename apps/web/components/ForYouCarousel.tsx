'use client';

import React from 'react';
import Link from 'next/link';
import { NewsItem } from '../lib/types';
import { formatTimeAgo } from '../lib/utils';
import { Sparkles, ArrowRight } from 'lucide-react';
import { SentinelImage } from './SentinelImage';

interface ForYouCarouselProps {
  items: NewsItem[];
  onSelect: (item: NewsItem) => void;
}

export function ForYouCarousel({ items, onSelect }: ForYouCarouselProps) {
  return (
    <section className="space-y-3.5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-sentinel-accent" />
          <h3 className="text-base sm:text-lg font-bold tracking-tight text-sentinel-text">
            For You
          </h3>
        </div>
        <Link
          href="/news"
          className="text-xs font-semibold text-sentinel-accent hover:text-sentinel-accentHover flex items-center gap-1 group"
        >
          <span>See all</span>
          <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-0.5" />
        </Link>
      </div>

      <div className="flex gap-4 overflow-x-auto pb-2 no-scrollbar scroll-smooth snap-x">
        {items.map((item) => (
          <div
            key={item.id}
            onClick={() => onSelect(item)}
            className="flex-shrink-0 w-72 sm:w-80 rounded-2xl border border-sentinel-border bg-sentinel-card p-3.5 shadow-subtle hover:shadow-card transition-all cursor-pointer group snap-start space-y-3"
          >
            {/* Image Container */}
            <div className="relative h-36 w-full rounded-xl overflow-hidden bg-neutral-950 border border-sentinel-border/50">
              <SentinelImage
                src={item.image_url}
                alt={item.title}
                category={item.category}
                className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
              />
              <div className="absolute top-2.5 left-2.5 z-10">
                <span className="px-2 py-0.5 rounded-md bg-black/70 backdrop-blur-md text-[10px] font-bold text-white uppercase tracking-wider border border-white/10 shadow-sm">
                  {item.category}
                </span>
              </div>
            </div>

            {/* Content */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-[11px] text-sentinel-muted font-medium">
                <span>{item.source_name}</span>
                <span>{formatTimeAgo(item.published_at)}</span>
              </div>

              <h4 className="font-bold text-sm text-sentinel-text group-hover:text-sentinel-accent transition-colors line-clamp-2 leading-snug">
                {item.title}
              </h4>

              <p className="text-xs text-sentinel-muted line-clamp-2 leading-relaxed">
                {item.summary?.what || item.description}
              </p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
