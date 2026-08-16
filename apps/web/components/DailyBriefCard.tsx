'use client';

import React from 'react';
import Link from 'next/link';
import { DailyReport } from '../lib/types';
import { Newspaper, ArrowRight, Sparkles } from 'lucide-react';

interface DailyBriefCardProps {
  report: DailyReport;
}

export function DailyBriefCard({ report }: DailyBriefCardProps) {
  return (
    <div className="rounded-3xl border border-sentinel-border bg-gradient-to-br from-sentinel-card via-sentinel-card to-orange-500/5 p-5 sm:p-6 shadow-subtle hover:shadow-card transition-all space-y-4">
      <div className="flex items-center justify-between border-b border-sentinel-border pb-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-sentinel-accent/10 flex items-center justify-center">
            <Newspaper className="w-4 h-4 text-sentinel-accent" />
          </div>
          <div>
            <h3 className="font-extrabold text-sm text-sentinel-text uppercase tracking-tight">
              Daily Intelligence
            </h3>
            <span className="text-[11px] text-sentinel-muted">{report.date}</span>
          </div>
        </div>

        <Link
          href={`/reports/${report.date}`}
          className="text-xs font-bold text-sentinel-accent hover:text-sentinel-accentHover flex items-center gap-1 group"
        >
          <span>Read newspaper</span>
          <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-0.5" />
        </Link>
      </div>

      <div className="space-y-2">
        <h4 className="font-extrabold text-base text-sentinel-text leading-snug">
          {report.headline}
        </h4>
        <p className="text-xs text-sentinel-muted leading-relaxed">
          {report.thirty_sec_summary}
        </p>
      </div>

      {/* Sentinel Take snippet */}
      <div className="p-3 rounded-2xl bg-sentinel-border/30 border border-sentinel-border/50 text-xs flex items-start gap-2.5">
        <Sparkles className="w-4 h-4 text-sentinel-accent flex-shrink-0 mt-0.5" />
        <p className="text-sentinel-text/90 italic leading-snug">
          &ldquo;{report.sentinel_take}&rdquo;
        </p>
      </div>
    </div>
  );
}
