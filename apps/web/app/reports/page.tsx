'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Header } from '../../components/Header';
import { DailyReport } from '../../lib/types';
import { fetchReports } from '../../lib/api-client';
import { Newspaper, Calendar, ArrowRight, Loader2 } from 'lucide-react';

export default function ReportsIndexPage() {
  const [reports, setReports] = useState<DailyReport[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadReports() {
      try {
        const data = await fetchReports();
        setReports(data);
      } catch (err) {
        console.error('Failed to load reports:', err);
      } finally {
        setLoading(false);
      }
    }
    loadReports();
  }, []);

  return (
    <div className="flex-1 flex flex-col min-w-0">
      <Header />

      <main className="flex-1 max-w-4xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Newspaper className="w-5 h-5 text-sentinel-accent" />
            <h2 className="text-2xl sm:text-3xl font-black tracking-tight text-sentinel-text">
              Daily Intelligence Archives
            </h2>
          </div>
          <p className="text-xs sm:text-sm text-sentinel-muted">
            Nightly AI digests summarizing essential technology shifts, free promotions, and developer insights.
          </p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-sentinel-accent animate-spin" />
          </div>
        ) : (
          <div className="space-y-4">
            {reports.map((report) => (
              <Link
                key={report.id}
                href={`/reports/${report.date}`}
                className="block p-5 sm:p-6 rounded-3xl border border-sentinel-border bg-sentinel-card shadow-subtle hover:shadow-card hover:border-sentinel-accent/40 transition-all group"
              >
                <div className="flex items-center justify-between gap-4">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-xs font-bold text-sentinel-accent">
                      <Calendar className="w-3.5 h-3.5" />
                      <span>{report.date}</span>
                    </div>

                    <h3 className="text-base sm:text-lg font-black text-sentinel-text group-hover:text-sentinel-accent transition-colors leading-snug">
                      {report.headline}
                    </h3>

                    <p className="text-xs sm:text-sm text-sentinel-muted line-clamp-2 leading-relaxed">
                      {report.thirty_sec_summary}
                    </p>
                  </div>

                  <div className="w-10 h-10 rounded-2xl bg-sentinel-border/40 group-hover:bg-sentinel-accent group-hover:text-white flex items-center justify-center transition-all flex-shrink-0">
                    <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
