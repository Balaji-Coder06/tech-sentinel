'use client';

import React from 'react';
import Link from 'next/link';
import { Opportunity } from '../lib/types';
import { OpportunityCard } from './OpportunityCard';
import { Gift, ArrowRight } from 'lucide-react';

interface FreeBeforeItsGoneProps {
  opportunities: Opportunity[];
  onClaim: (opp: Opportunity) => void;
  onToggleSave?: (id: string) => void;
  savedIds?: string[];
}

export function FreeBeforeItsGone({
  opportunities,
  onClaim,
  onToggleSave,
  savedIds = []
}: FreeBeforeItsGoneProps) {
  return (
    <section className="space-y-4">
      {/* Header Banner */}
      <div className="flex items-center justify-between">
        <div className="space-y-0.5">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-sentinel-accent/10 flex items-center justify-center">
              <Gift className="w-3.5 h-3.5 text-sentinel-accent animate-pulse-subtle" />
            </div>
            <h3 className="text-base sm:text-lg font-black tracking-tight text-sentinel-text uppercase">
              Free Before It&apos;s Gone
            </h3>
          </div>
          <p className="text-xs text-sentinel-muted">
            High-value developer tools, cloud credits, and vouchers claimable for ₹0 right now.
          </p>
        </div>

        <Link
          href="/free"
          className="text-xs font-bold text-sentinel-accent hover:text-sentinel-accentHover flex items-center gap-1 group flex-shrink-0"
        >
          <span>See all offers</span>
          <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-0.5" />
        </Link>
      </div>

      {/* Grid of Opportunity Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {opportunities.slice(0, 3).map((opp) => (
          <OpportunityCard
            key={opp.id}
            opportunity={opp}
            onClaim={onClaim}
            onToggleSave={onToggleSave}
            isSaved={savedIds.includes(opp.id)}
          />
        ))}
      </div>
    </section>
  );
}
