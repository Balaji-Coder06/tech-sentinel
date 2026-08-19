'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { Header } from '../../../components/Header';
import { DailyReport } from '../../../lib/types';
import { fetchReportByDate } from '../../../lib/api-client';
import { ArrowLeft, Sparkles, Gift, Flame, Clock, Printer, Loader2, AlertCircle } from 'lucide-react';

export default function ReportDetailPage() {
  const params = useParams();
  const date = params?.date as string;
  const [report, setReport] = useState<DailyReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    async function loadReport() {
      if (!date) return;
      setLoading(true);
      setNotFound(false);
      try {
        const data = await fetchReportByDate(date);
        if (data) {
          setReport(data);
        } else {
          setNotFound(true);
        }
      } catch {
        setNotFound(true);
      } finally {
        setLoading(false);
      }
    }
    loadReport();
  }, [date]);

  if (loading) {
    return (
      <div className="flex-1 flex flex-col min-w-0">
        <Header />
        <div className="flex-1 flex items-center justify-center min-h-[60vh]">
          <Loader2 className="w-8 h-8 text-sentinel-accent animate-spin" />
        </div>
      </div>
    );
  }

  if (notFound || !report) {
    return (
      <div className="flex-1 flex flex-col min-w-0">
        <Header />
        <main className="flex-1 max-w-2xl w-full mx-auto p-6 sm:p-12 text-center space-y-4 my-auto">
          <div className="w-12 h-12 rounded-2xl bg-amber-500/10 text-amber-500 mx-auto flex items-center justify-center">
            <AlertCircle className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold text-sentinel-text">Daily Intelligence Report Not Found</h2>
          <p className="text-xs text-sentinel-muted">
            No intelligence digest exists for date &ldquo;{date}&rdquo;. Reports are generated automatically every morning at 8:00 AM IST.
          </p>
          <div className="pt-2">
            <Link
              href="/reports"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-sentinel-accent text-white text-xs font-bold shadow-sm"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Browse Report Archives</span>
            </Link>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-w-0">
      <Header />

      <main className="flex-1 max-w-4xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-8">
        {/* Navigation Bar */}
        <div className="flex items-center justify-between">
          <Link
            href="/reports"
            className="flex items-center gap-2 text-xs font-bold text-sentinel-muted hover:text-sentinel-text transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to Archives</span>
          </Link>

          <div className="flex items-center gap-2">
            <button
              onClick={() => window.print()}
              className="p-2 rounded-xl border border-sentinel-border hover:bg-sentinel-card text-xs font-bold text-sentinel-muted flex items-center gap-1.5 transition-colors"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>Print Edition</span>
            </button>
          </div>
        </div>

        {/* Newspaper Styled Container */}
        <article className="rounded-3xl border-2 border-sentinel-border bg-sentinel-card p-6 sm:p-10 shadow-card space-y-8">
          {/* Masthead Header */}
          <div className="text-center border-b-2 border-sentinel-border pb-6 space-y-2">
            <div className="text-[11px] font-mono uppercase tracking-widest text-sentinel-muted font-bold">
              THE NIGHTLY AGENT DISPATCH
            </div>
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black tracking-tight text-sentinel-text editorial-headline uppercase">
              TECH SENTINEL
            </h1>
            <div className="flex items-center justify-center gap-4 text-xs text-sentinel-muted font-semibold pt-1">
              <span>{report.date}</span>
              <span>•</span>
              <span>Autonomous Intelligence Edition</span>
              <span>•</span>
              <span className="text-sentinel-accent font-bold">₹0 Cost Verified</span>
            </div>
          </div>

          {/* Headline & 30-Second Summary */}
          <div className="space-y-4">
            <h2 className="text-xl sm:text-2xl lg:text-3xl font-black text-sentinel-text leading-tight">
              {report.headline}
            </h2>

            <div className="p-4 rounded-2xl bg-sentinel-accent/10 border border-sentinel-accent/20 space-y-1">
              <span className="text-[10px] font-extrabold text-sentinel-accent uppercase tracking-wider block">
                30-SECOND INTELLIGENCE BRIEF
              </span>
              <p className="text-xs sm:text-sm text-sentinel-text font-medium leading-relaxed">
                {report.thirty_sec_summary}
              </p>
            </div>
          </div>

          {/* Top Stories Section */}
          {report.top_stories && report.top_stories.length > 0 && (
            <div className="space-y-3 pt-4 border-t border-sentinel-border">
              <div className="flex items-center gap-2 text-xs font-extrabold text-sentinel-accent uppercase tracking-wider">
                <Flame className="w-4 h-4" />
                <span>🔥 Top Developments</span>
              </div>
              <div className="space-y-3">
                {report.top_stories.map((story, idx) => (
                  <div key={idx} className="p-3.5 rounded-2xl bg-sentinel-border/20 border border-sentinel-border/60 space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-sentinel-text">0{idx + 1}. {story.title}</span>
                      {story.score && (
                        <span className="font-mono text-[10px] text-sentinel-accent font-bold">
                          Score {story.score}/100
                        </span>
                      )}
                    </div>
                    {story.summary && (
                      <p className="text-xs text-sentinel-muted leading-relaxed">
                        {story.summary}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Free Opportunities Section */}
          {report.free_opportunities && report.free_opportunities.length > 0 && (
            <div className="space-y-3 pt-4 border-t border-sentinel-border">
              <div className="flex items-center gap-2 text-xs font-extrabold text-sentinel-accent uppercase tracking-wider">
                <Gift className="w-4 h-4" />
                <span>🎁 Free Before It&apos;s Gone</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {report.free_opportunities.map((opp, idx) => (
                  <div key={idx} className="p-3.5 rounded-2xl bg-sentinel-card border border-sentinel-border shadow-subtle space-y-1">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="font-bold text-sentinel-text">{opp.provider || 'Provider'}</span>
                      <span className="font-bold text-sentinel-accent">{opp.value}</span>
                    </div>
                    <h4 className="font-bold text-xs text-sentinel-text line-clamp-1">{opp.title}</h4>
                    {opp.claim_url && (
                      <a
                        href={opp.claim_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[11px] font-bold text-sentinel-accent hover:underline block pt-1"
                      >
                        Claim Offer →
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Expiring Soon Watchlist */}
          {report.expiring_soon && report.expiring_soon.length > 0 && (
            <div className="space-y-3 pt-4 border-t border-sentinel-border">
              <div className="flex items-center gap-2 text-xs font-extrabold text-amber-500 uppercase tracking-wider">
                <Clock className="w-4 h-4 animate-pulse" />
                <span>⏰ Expiring Soon Watchlist</span>
              </div>
              <div className="space-y-2">
                {report.expiring_soon.map((exp, idx) => (
                  <div key={idx} className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs flex items-center justify-between">
                    <span className="font-bold text-sentinel-text">{exp.title}</span>
                    <span className="font-mono text-amber-600 dark:text-amber-400 font-bold">{exp.expires_in || exp.expires || 'Soon'}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Sentinel's Take */}
          <div className="p-5 rounded-2xl bg-sentinel-border/30 border border-sentinel-border space-y-2">
            <div className="flex items-center gap-2 text-xs font-extrabold text-sentinel-text uppercase tracking-wider">
              <Sparkles className="w-4 h-4 text-sentinel-accent" />
              <span>Sentinel&apos;s Take</span>
            </div>
            <p className="text-xs sm:text-sm text-sentinel-text/90 italic leading-relaxed">
              &ldquo;{report.sentinel_take}&rdquo;
            </p>
          </div>

          {/* Footer Signoff */}
          <div className="text-center pt-6 border-t border-sentinel-border text-xs text-sentinel-muted space-y-1">
            <p className="font-bold text-sentinel-text">You missed nothing in tech today.</p>
            <p>Generated autonomously by Tech Sentinel. Dispatched daily at 8:00 AM IST.</p>
          </div>
        </article>
      </main>
    </div>
  );
}
