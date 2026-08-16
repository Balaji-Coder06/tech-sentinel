'use client';

import React, { useState, useEffect } from 'react';
import { Header } from '../../components/Header';
import { OpportunityCard } from '../../components/OpportunityCard';
import { ClaimModal } from '../../components/ClaimModal';
import { Opportunity } from '../../lib/types';
import { fetchOpportunities, fetchSavedItems, toggleSavedItem } from '../../lib/api-client';
import { Gift, SlidersHorizontal, ShieldCheck, Loader2 } from 'lucide-react';

import { rankOpportunities } from '../../lib/opportunity-ranking';

export default function FreeRadarPage() {
  const [activeType, setActiveType] = useState('all');
  const [activeStatus, setActiveStatus] = useState('all');
  const [sortBy, setSortBy] = useState<'score' | 'expiry' | 'value'>('score');
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [savedItems, setSavedItems] = useState<{ news: string[]; opportunities: string[] }>({
    news: [],
    opportunities: []
  });
  const [loading, setLoading] = useState(true);
  const [selectedOpp, setSelectedOpp] = useState<Opportunity | null>(null);

  const typeFilters = [
    { id: 'all', label: 'All Opportunities' },
    { id: 'ai_credits', label: 'AI Credits' },
    { id: 'cloud', label: 'Cloud Credits' },
    { id: 'certification', label: 'Certifications' },
    { id: 'software', label: 'Free Software' },
    { id: 'competition', label: 'Hackathons' },
    { id: 'education', label: 'Student Programs' },
  ];

  useEffect(() => {
    async function loadOpps() {
      setLoading(true);
      try {
        const [oppsData, savedData] = await Promise.all([
          fetchOpportunities(activeType, activeStatus, sortBy),
          fetchSavedItems()
        ]);
        setOpportunities(oppsData);
        setSavedItems(savedData);
      } catch (err) {
        console.error('Failed to load opportunities:', err);
      } finally {
        setLoading(false);
      }
    }
    loadOpps();
  }, [activeType, activeStatus, sortBy]);

  const sortedOpps = rankOpportunities(opportunities, sortBy);

  const handleToggleSave = async (id: string) => {
    const updated = await toggleSavedItem('opportunity', id);
    setSavedItems({ ...updated });
  };

  return (
    <div className="flex-1 flex flex-col min-w-0">
      <Header userName="Balaji" />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        {/* Page Banner */}
        <div className="rounded-3xl border border-sentinel-border bg-gradient-to-r from-sentinel-card via-sentinel-card to-orange-500/10 p-6 sm:p-8 shadow-card flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="space-y-1.5 max-w-2xl">
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 rounded-full bg-sentinel-accent text-white font-extrabold text-xs uppercase tracking-wider flex items-center gap-1.5 shadow-sm">
                <Gift className="w-3.5 h-3.5" /> FREE RADAR
              </span>
              <span className="flex items-center gap-1 text-xs text-sentinel-success font-bold">
                <ShieldCheck className="w-4 h-4" /> 100% Official Verified
              </span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-black tracking-tight text-sentinel-text">
              Free Tech Opportunities & Promotions
            </h2>
            <p className="text-xs sm:text-sm text-sentinel-muted leading-relaxed">
              Every active developer deal, student credit pack, free exam voucher, and cloud trial that you can claim at ₹0 right now.
            </p>
          </div>

          <div className="px-4 py-3 rounded-2xl bg-sentinel-card border border-sentinel-border text-center shadow-subtle flex-shrink-0">
            <span className="text-[10px] uppercase font-bold text-sentinel-muted block">Monetary Value Tracked</span>
            <span className="font-extrabold text-xl text-sentinel-accent font-mono">$200,500+</span>
          </div>
        </div>

        {/* Filter & Sort Controls */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          {/* Type Filter Pills */}
          <div className="flex gap-2 overflow-x-auto pb-1 no-scrollbar w-full sm:w-auto">
            {typeFilters.map((t) => (
              <button
                key={t.id}
                onClick={() => setActiveType(t.id)}
                className={`px-3.5 py-1.5 rounded-full text-xs font-bold whitespace-nowrap transition-all ${
                  activeType === t.id
                    ? 'bg-sentinel-accent text-white shadow-sm'
                    : 'border border-sentinel-border bg-sentinel-card text-sentinel-muted hover:text-sentinel-text hover:border-sentinel-accent/40'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* Sort Dropdown */}
          <div className="flex items-center gap-2 flex-shrink-0 self-end sm:self-auto">
            <SlidersHorizontal className="w-4 h-4 text-sentinel-muted" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="bg-sentinel-card border border-sentinel-border rounded-xl px-3 py-1.5 text-xs font-semibold text-sentinel-text focus:outline-none focus:border-sentinel-accent cursor-pointer"
            >
              <option value="score">Highest Priority</option>
              <option value="expiry">Expiring Soonest</option>
              <option value="value">Most Valuable</option>
            </select>
          </div>
        </div>

        {/* Opportunities Grid */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-sentinel-accent animate-spin" />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {sortedOpps.map((opp) => (
              <OpportunityCard
                key={opp.id}
                opportunity={opp}
                onClaim={setSelectedOpp}
                onToggleSave={handleToggleSave}
                isSaved={savedItems.opportunities.includes(opp.id)}
              />
            ))}
          </div>
        )}
      </main>

      {/* Claim Modal */}
      {selectedOpp && (
        <ClaimModal
          opportunity={selectedOpp}
          onClose={() => setSelectedOpp(null)}
        />
      )}
    </div>
  );
}
