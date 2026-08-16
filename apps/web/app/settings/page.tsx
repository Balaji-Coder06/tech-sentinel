'use client';

import React, { useState, useEffect } from 'react';
import { Header } from '../../components/Header';
import { UserPreferences } from '../../lib/types';
import { fetchPreferences, savePreferences } from '../../lib/api-client';
import { Sliders, Bell, Check, Cpu, Loader2 } from 'lucide-react';

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
    ai_provider: 'fallback'
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

          {/* Section 3: AI Engine Selection */}
          <div className="p-6 rounded-3xl border border-sentinel-border bg-sentinel-card shadow-subtle space-y-4">
            <div className="space-y-0.5">
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-sentinel-accent" />
                <h3 className="font-extrabold text-sm text-sentinel-text uppercase tracking-wider">
                  AI Intelligence Engine
                </h3>
              </div>
              <p className="text-xs text-sentinel-muted">
                Choose which model provider powers your summarization & daily digest. All providers run within free-tier limits (₹0 cost).
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
              {[
                { id: 'fallback', label: 'Deterministic NLP', sub: '₹0 Cost / No API Keys' },
                { id: 'gemini', label: 'Google Gemini 2.0', sub: 'Free Tier API' },
                { id: 'groq', label: 'Groq Llama 3.3', sub: 'Ultra Fast / Free Tier' },
              ].map((p) => {
                const isSelected = prefs.ai_provider === p.id;
                return (
                  <button
                    type="button"
                    key={p.id}
                    onClick={() => setPrefs({ ...prefs, ai_provider: p.id })}
                    className={`p-4 rounded-2xl border text-left space-y-1 transition-all ${
                      isSelected
                        ? 'border-sentinel-accent bg-sentinel-accent/10 ring-2 ring-sentinel-accent/20'
                        : 'border-sentinel-border bg-sentinel-card hover:border-sentinel-border/80'
                    }`}
                  >
                    <span className="font-bold text-xs text-sentinel-text block">{p.label}</span>
                    <span className="text-[10px] text-sentinel-muted block">{p.sub}</span>
                  </button>
                );
              })}
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
                  <span className="text-xs font-bold text-sentinel-text block">Nightly Intelligence Brief</span>
                  <span className="text-[11px] text-sentinel-muted">Receive the full daily summary every night at 9:00 PM IST</span>
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
