'use client';

import React from 'react';
import { Opportunity } from '../lib/types';
import { formatExpiry } from '../lib/utils';
import { ShieldCheck, Clock, Bookmark, ExternalLink } from 'lucide-react';

interface OpportunityCardProps {
  opportunity: Opportunity;
  onClaim: (opp: Opportunity) => void;
  onToggleSave?: (id: string) => void;
  isSaved?: boolean;
}

export function OpportunityCard({
  opportunity: opp,
  onClaim,
  onToggleSave,
  isSaved = false
}: OpportunityCardProps) {
  const expiry = formatExpiry(opp.expiry_date);

  return (
    <div className="rounded-2xl border border-sentinel-border bg-sentinel-card p-4 shadow-subtle hover:shadow-card transition-all flex flex-col justify-between space-y-3 group hover:border-sentinel-accent/30 relative">
      {/* Top Meta Row */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          {opp.provider_logo ? (
            <img
              src={opp.provider_logo}
              alt={opp.provider}
              className="w-7 h-7 rounded-lg object-contain bg-sentinel-border/30 p-1 border border-sentinel-border"
            />
          ) : (
            <div className="w-7 h-7 rounded-lg bg-sentinel-accent/10 flex items-center justify-center font-bold text-xs text-sentinel-accent">
              {opp.provider.charAt(0)}
            </div>
          )}
          <div>
            <span className="text-xs font-bold text-sentinel-text block leading-tight">
              {opp.provider}
            </span>
            <span className="text-[10px] text-sentinel-muted uppercase font-semibold">
              {opp.opportunity_type.replace('_', ' ')}
            </span>
          </div>
        </div>

        {/* Bookmark Action */}
        {onToggleSave && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onToggleSave(opp.id);
            }}
            className="p-1.5 rounded-lg text-sentinel-muted hover:text-sentinel-accent hover:bg-sentinel-border/50 transition-colors"
          >
            <Bookmark className={`w-4 h-4 ${isSaved ? 'fill-sentinel-accent text-sentinel-accent' : ''}`} />
          </button>
        )}
      </div>

      {/* Main Opportunity Content */}
      <div className="space-y-1.5">
        <h4 className="font-bold text-sm text-sentinel-text group-hover:text-sentinel-accent transition-colors line-clamp-2 leading-snug">
          {opp.title}
        </h4>
        <p className="text-xs text-sentinel-muted line-clamp-2 leading-relaxed">
          {opp.description}
        </p>
      </div>

      {/* Pricing & Eligibility Badges */}
      <div className="space-y-2 pt-2 border-t border-sentinel-border/60">
        <div className="flex items-center justify-between text-xs">
          <div className="space-y-0.5">
            <span className="text-[10px] text-sentinel-muted uppercase block">Value</span>
            <div className="flex items-baseline gap-1.5">
              <span className="font-extrabold text-sm text-sentinel-accent">
                {opp.current_value}
              </span>
              {opp.normal_value && (
                <span className="text-[11px] text-sentinel-muted line-through font-medium">
                  {opp.normal_value}
                </span>
              )}
            </div>
          </div>

          <div className="text-right space-y-0.5">
            <span className="text-[10px] text-sentinel-muted uppercase block">Eligibility</span>
            <span className="text-[11px] font-semibold text-sentinel-text bg-sentinel-border/50 px-2 py-0.5 rounded-md">
              {opp.eligibility}
            </span>
          </div>
        </div>

        {/* Expiry & Verification Indicators */}
        <div className="flex items-center justify-between text-[11px] pt-1">
          <div className="flex items-center gap-1.5">
            <Clock className={`w-3.5 h-3.5 ${expiry.urgent ? 'text-amber-500 animate-pulse' : 'text-sentinel-muted'}`} />
            <span className={`font-medium ${expiry.urgent ? 'text-amber-600 dark:text-amber-400 font-bold' : 'text-sentinel-muted'}`}>
              {expiry.text}
            </span>
          </div>

          {opp.verification_status === 'VERIFIED' && (
            <div className="flex items-center gap-1 text-sentinel-success font-semibold text-[10px]">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Verified</span>
            </div>
          )}
        </div>
      </div>

      {/* Claim Button */}
      <button
        type="button"
        onClick={() => onClaim(opp)}
        className="w-full mt-1 py-2 px-3 rounded-xl bg-sentinel-accent hover:bg-sentinel-accentHover text-white font-bold text-xs flex items-center justify-center gap-1.5 shadow-sm transition-all active:scale-98"
      >
        <span>CLAIM FREE</span>
        <ExternalLink className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}
