'use client';

import React from 'react';
import { AgentStats } from '../lib/types';
import { formatTimeAgo } from '../lib/utils';
import { ShieldCheck, RefreshCw } from 'lucide-react';

interface AgentStatusWidgetProps {
  stats: AgentStats;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export function AgentStatusWidget({ stats, onRefresh, isRefreshing }: AgentStatusWidgetProps) {
  const formattedLastScan = stats.last_scan_time?.includes('T') || stats.last_scan_time?.includes('-')
    ? formatTimeAgo(stats.last_scan_time)
    : (stats.last_scan_time || 'Just now');

  return (
    <div className="rounded-3xl border border-sentinel-border bg-sentinel-card p-4 sm:p-5 shadow-subtle space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-sentinel-success radar-active" />
          <h4 className="font-extrabold text-xs text-sentinel-text uppercase tracking-wider">
            Sentinel Radar
          </h4>
        </div>

        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="p-1.5 rounded-lg text-sentinel-muted hover:text-sentinel-text hover:bg-sentinel-border/50 transition-all disabled:opacity-50"
            title="Scan Sources Now"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin text-sentinel-accent' : ''}`} />
          </button>
        )}
      </div>

      {/* Grid of Key Metrics */}
      <div className="grid grid-cols-2 gap-2.5 text-xs">
        <div className="p-2.5 rounded-xl bg-sentinel-border/30 border border-sentinel-border/50 space-y-0.5">
          <span className="text-[10px] text-sentinel-muted uppercase font-semibold block">Last Scan</span>
          <span className="font-bold text-sentinel-text">{formattedLastScan}</span>
        </div>

        <div className="p-2.5 rounded-xl bg-sentinel-border/30 border border-sentinel-border/50 space-y-0.5">
          <span className="text-[10px] text-sentinel-muted uppercase font-semibold block">Sources Checked</span>
          <span className="font-bold text-sentinel-text">{stats.sources_checked || 9} active</span>
        </div>

        <div className="p-2.5 rounded-xl bg-sentinel-border/30 border border-sentinel-border/50 space-y-0.5">
          <span className="text-[10px] text-sentinel-muted uppercase font-semibold block">New Today</span>
          <span className="font-bold text-sentinel-accent">+{stats.new_opportunities_today || 0} offers</span>
        </div>

        <div className="p-2.5 rounded-xl bg-sentinel-border/30 border border-sentinel-border/50 space-y-0.5">
          <span className="text-[10px] text-sentinel-muted uppercase font-semibold block">Next Digest</span>
          <span className="font-bold text-sentinel-text">{stats.next_report_time || '9:00 PM IST'}</span>
        </div>
      </div>

      {/* Zero Cost Assurance Footer */}
      <div className="flex items-center justify-between text-[11px] pt-1 text-sentinel-muted">
        <div className="flex items-center gap-1 font-medium">
          <ShieldCheck className="w-3.5 h-3.5 text-sentinel-success" />
          <span>Automated Verification</span>
        </div>
        <span className="font-mono font-bold text-sentinel-accent">{stats.system_cost || '₹0.00'} Infra Cost</span>
      </div>
    </div>
  );
}
