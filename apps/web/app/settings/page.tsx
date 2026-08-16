'use client';

import React, { useState, useEffect } from 'react';
import { Header } from '../../components/Header';
import { UserPreferences } from '../../lib/types';
import { fetchPreferences, savePreferences } from '../../lib/api-client';
import { Sliders, Bell, Check, Cpu, Loader2, Mail } from 'lucide-react';

export default function SettingsPage() {
  const [prefs, setPrefs] = useState<UserPreferences>({
    id: 'default',
    user_name: 'Balaji',
    theme: 'system',
    categories: ['ai', 'cloud', 'development', 'open_source', 'cybersecurity', 'startups'],
    keywords: ['react', 'llm', 'credits', 'internship', 'certification', 'hackathon'],
    opportunity_types: ['software', 'ai_credits', 'cloud', 'education', 'certification', 'competition', 'career'],
    enable_daily_brief: true,
    enable_critical_alerts: true,
    email_newsletter_enabled: false,
    newsletter_email: ''
  });
  const [loading, setLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    async function loadPrefs() {
      try {
        const data = await fetchPreferences();
        if (data && data.categories) {
          setPrefs(data);
        }
      } catch (err) {
        console.warn('Failed to load preferences:', err);
      } finally {
        setLoading(false);
      }
    }
    loadPrefs();
  }, []);

  const availableCategories = [
    { id: 'ai', label: 'Artificial Intelligence' },
    { id: 'cloud', label: 'Cloud Computing' },
    { id: 'development', label: 'Software Development' },
    { id: 'open_source', label: 'Open Source' },
    { id: 'cybersecurity', label: 'Cybersecurity' },
    { id: 'startups', label: 'Startups & Tools' },
  ];

  const availableOpportunities = [
    { id: 'ai_credits', label: 'Free AI Credits & API Keys' },
    { id: 'cloud', label: 'Cloud Credits (AWS / GCP / Azure)' },
    { id: 'certification', label: '100% Free Cert Exam Vouchers' },
    { id: 'software', label: 'Free SaaS & IDE Licenses' },
    { id: 'competition', label: 'Hackathons & Coding Contests' },
    { id: 'education', label: 'Student Developer Benefits' },
    { id: 'career', label: 'Internships & Fellowship Programs' },
  ];

  const toggleCategory = (catId: string) => {
    const list = [...prefs.categories];
    const index = list.indexOf(catId);
    if (index >= 0) list.splice(index, 1);
    else list.push(catId);
    setPrefs({ ...prefs, categories: list });
  };

  const toggleOppType = (typeId: string) => {
    const list = [...prefs.opportunity_types];
    const index = list.indexOf(typeId);
    if (index >= 0) list.splice(index, 1);
    else list.push(typeId);
    setPrefs({ ...prefs, opportunity_types: list });
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setErrorMessage(null);
    try {
      const updated = await savePreferences(prefs);
      if (updated && updated.categories) {
        setPrefs(updated);
      }
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch (err: any) {
      setErrorMessage('Failed to save preferences. Please try again.');
      setTimeout(() => setErrorMessage(null), 4000);
    } finally {
      setIsSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex flex-col min-w-0">
        <Header userName="Balaji" />
        <div className="flex-1 flex items-center justify-center min-h-[60vh]">
          <Loader2 className="w-8 h-8 text-sentinel-accent animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-w-0">
      <Header userName={prefs.user_name || 'Balaji'} />

      <main className="flex-1 max-w-4xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Sliders className="w-5 h-5 text-sentinel-accent" />
            <h2 className="text-2xl sm:text-3xl font-black tracking-tight text-sentinel-text">
              Preferences & Intelligence Radar Settings
            </h2>
          </div>
          <p className="text-xs sm:text-sm text-sentinel-muted">
            Configure your technical interests, opportunity notifications, and autonomous AI engine preferences.
          </p>
        </div>

        <form onSubmit={handleSave} className="space-y-6">
          {/* Section 1: Tracked Categories */}
          <div className="p-6 rounded-3xl border border-sentinel-border bg-sentinel-card shadow-subtle space-y-4">
            <div className="space-y-0.5">
              <h3 className="font-extrabold text-sm text-sentinel-text uppercase tracking-wider">
                Technology Interests
              </h3>
              <p className="text-xs text-sentinel-muted">
                Sentinel prioritizes news and analysis matching your selected categories.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
              {availableCategories.map((cat) => {
                const isChecked = prefs.categories.includes(cat.id);
                return (
                  <button
                    type="button"
                    key={cat.id}
                    onClick={() => toggleCategory(cat.id)}
                    className={`p-3 rounded-2xl border text-xs font-bold text-left flex items-center justify-between transition-all ${
                      isChecked
                        ? 'border-sentinel-accent bg-sentinel-accent/10 text-sentinel-text'
                        : 'border-sentinel-border bg-sentinel-card text-sentinel-muted hover:border-sentinel-border/80'
                    }`}
                  >
                    <span>{cat.label}</span>
                    <div className={`w-5 h-5 rounded-lg flex items-center justify-center border ${isChecked ? 'bg-sentinel-accent border-sentinel-accent text-white' : 'border-sentinel-border'}`}>
                      {isChecked && <Check className="w-3.5 h-3.5" />}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Section 2: Opportunity Types */}
          <div className="p-6 rounded-3xl border border-sentinel-border bg-sentinel-card shadow-subtle space-y-4">
            <div className="space-y-0.5">
              <h3 className="font-extrabold text-sm text-sentinel-text uppercase tracking-wider">
                Free Radar Preferences
              </h3>
              <p className="text-xs text-sentinel-muted">
                Select which types of free deals and promotions to monitor.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
              {availableOpportunities.map((opp) => {
                const isChecked = prefs.opportunity_types.includes(opp.id);
                return (
                  <button
                    type="button"
                    key={opp.id}
                    onClick={() => toggleOppType(opp.id)}
                    className={`p-3 rounded-2xl border text-xs font-bold text-left flex items-center justify-between transition-all ${
                      isChecked
                        ? 'border-sentinel-accent bg-sentinel-accent/10 text-sentinel-text'
                        : 'border-sentinel-border bg-sentinel-card text-sentinel-muted hover:border-sentinel-border/80'
                    }`}
                  >
                    <span>{opp.label}</span>
                    <div className={`w-5 h-5 rounded-lg flex items-center justify-center border ${isChecked ? 'bg-sentinel-accent border-sentinel-accent text-white' : 'border-sentinel-border'}`}>
                      {isChecked && <Check className="w-3.5 h-3.5" />}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Section 3: Processing Engine */}
          <div className="p-6 rounded-3xl border border-sentinel-border bg-sentinel-card shadow-subtle space-y-4">
            <div className="space-y-0.5">
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-sentinel-accent" />
                <h3 className="font-extrabold text-sm text-sentinel-text uppercase tracking-wider">
                  Intelligence Processing Engine
                </h3>
              </div>
              <p className="text-xs text-sentinel-muted">
                Tech Sentinel runs 100% locally with high-performance deterministic NLP heuristics (₹0 cost / zero external API dependencies).
              </p>
            </div>

            <div className="grid grid-cols-1 gap-3 pt-2">
              <div className="p-4 rounded-2xl border border-sentinel-accent bg-sentinel-accent/10 ring-2 ring-sentinel-accent/20 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-xs text-sentinel-text block">Local Deterministic NLP</span>
                  <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 font-bold">Active</span>
                </div>
                <span className="text-[10px] text-sentinel-muted block">Instantaneous offline extraction, scoring, and nightly intelligence reports</span>
              </div>
            </div>
          </div>

          {/* Section 4: Notifications */}
          <div className="p-6 rounded-3xl border border-sentinel-border bg-sentinel-card shadow-subtle space-y-4">
            <div className="space-y-0.5">
              <div className="flex items-center gap-2">
                <Bell className="w-4 h-4 text-sentinel-accent" />
                <h3 className="font-extrabold text-sm text-sentinel-text uppercase tracking-wider">
                  Notification Delivery
                </h3>
              </div>
              <p className="text-xs text-sentinel-muted">
                Autonomous Telegram delivery for nightly reports and urgent expiring alerts.
              </p>
            </div>

            <div className="space-y-3 pt-2">
              <label className="flex items-center justify-between p-3 rounded-2xl border border-sentinel-border bg-sentinel-card cursor-pointer">
                <div>
                  <span className="text-xs font-bold text-sentinel-text block">Nightly Telegram Brief</span>
                  <span className="text-[11px] text-sentinel-muted">Receive the full daily summary via Telegram every night at 9:30 PM IST</span>
                </div>
                <input
                  type="checkbox"
                  checked={prefs.enable_daily_brief}
                  onChange={(e) => setPrefs({ ...prefs, enable_daily_brief: e.target.checked })}
                  className="w-4 h-4 accent-sentinel-accent rounded"
                />
              </label>

              <label className="flex items-center justify-between p-3 rounded-2xl border border-sentinel-border bg-sentinel-card cursor-pointer">
                <div>
                  <span className="text-xs font-bold text-sentinel-text block">Critical Expiring Offers Alert</span>
                  <span className="text-[11px] text-sentinel-muted">Instant alert when a verified &gt;$50 offer has &lt;24 hours left</span>
                </div>
                <input
                  type="checkbox"
                  checked={prefs.enable_critical_alerts}
                  onChange={(e) => setPrefs({ ...prefs, enable_critical_alerts: e.target.checked })}
                  className="w-4 h-4 accent-sentinel-accent rounded"
                />
              </label>

              <div className="p-3.5 rounded-2xl border border-sentinel-border bg-sentinel-card space-y-2.5">
                <label className="flex items-center justify-between cursor-pointer">
                  <div className="flex items-center gap-2">
                    <Mail className="w-4 h-4 text-sentinel-accent" />
                    <div>
                      <span className="text-xs font-bold text-sentinel-text block">Gmail / Email Newsletter</span>
                      <span className="text-[11px] text-sentinel-muted">Receive the Nightly Intelligence Brief in your inbox at 9:30 PM IST</span>
                    </div>
                  </div>
                  <input
                    type="checkbox"
                    checked={prefs.email_newsletter_enabled}
                    onChange={(e) => setPrefs({ ...prefs, email_newsletter_enabled: e.target.checked })}
                    className="w-4 h-4 accent-sentinel-accent rounded"
                  />
                </label>

                {prefs.email_newsletter_enabled && (
                  <div className="pt-2 border-t border-sentinel-border/50">
                    <label className="block text-[11px] font-bold text-sentinel-muted mb-1">
                      Newsletter Recipient Email
                    </label>
                    <input
                      type="email"
                      placeholder="e.g. balaji@example.com"
                      value={prefs.newsletter_email || ''}
                      onChange={(e) => setPrefs({ ...prefs, newsletter_email: e.target.value })}
                      className="w-full px-3.5 py-2 text-xs rounded-xl bg-sentinel-bg border border-sentinel-border text-sentinel-text focus:outline-none focus:border-sentinel-accent transition-colors"
                    />
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Save Button & Feedback */}
          <div className="flex flex-col sm:flex-row items-end sm:items-center justify-end gap-3 pt-2">
            {errorMessage && (
              <span className="text-xs font-bold text-sentinel-danger flex items-center gap-1 animate-in fade-in">
                {errorMessage}
              </span>
            )}
            {savedSuccess && (
              <span className="text-xs font-bold text-sentinel-success flex items-center gap-1 animate-in fade-in">
                <Check className="w-4 h-4" /> Preferences saved!
              </span>
            )}
            <button
              type="submit"
              disabled={isSaving}
              className="py-3 px-8 rounded-2xl bg-sentinel-accent hover:bg-sentinel-accentHover disabled:opacity-50 text-white font-extrabold text-xs shadow-glow transition-all active:scale-95 flex items-center gap-2"
            >
              {isSaving ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Saving...</span>
                </>
              ) : (
                <span>Save Preferences</span>
              )}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
