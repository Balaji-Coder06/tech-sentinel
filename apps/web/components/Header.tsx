'use client';

import React, { useState } from 'react';
import { Search, Bell, Moon, Sun, Sparkles } from 'lucide-react';
import { SearchModal } from './SearchModal';

export function Header() {
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isDark, setIsDark] = useState(false);

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour >= 5 && hour < 12) return 'Good morning';
    if (hour >= 12 && hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  const toggleTheme = () => {
    const root = document.documentElement;
    if (root.classList.contains('dark')) {
      root.classList.remove('dark');
      setIsDark(false);
    } else {
      root.classList.add('dark');
      setIsDark(true);
    }
  };

  return (
    <>
      <header className="sticky top-0 z-30 glass-panel border-b border-sentinel-border px-4 sm:px-8 py-3.5 flex items-center justify-between gap-4">
        {/* Dynamic Greeting */}
        <div>
          <h1 className="text-base sm:text-lg font-bold tracking-tight text-sentinel-text flex items-center gap-1.5">
            {getGreeting()} <span className="animate-bounce">👋</span>
          </h1>
          <p className="text-xs text-sentinel-muted hidden sm:block">
            Here is what you missed in tech & what you can claim today.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2.5 sm:gap-3">
          {/* Universal Search Bar Trigger */}
          <button
            onClick={() => setIsSearchOpen(true)}
            className="flex items-center gap-2.5 px-3.5 py-2 rounded-full border border-sentinel-border bg-sentinel-card hover:border-sentinel-accent/40 shadow-subtle text-xs sm:text-sm text-sentinel-muted transition-all hover:shadow-card w-40 sm:w-64 justify-between"
          >
            <div className="flex items-center gap-2">
              <Search className="w-4 h-4 text-sentinel-accent" />
              <span className="truncate">Search opportunities...</span>
            </div>
            <kbd className="hidden sm:inline-block px-1.5 py-0.5 rounded bg-sentinel-border/50 text-[10px] font-mono text-sentinel-muted">
              ⌘K
            </kbd>
          </button>

          {/* Theme Toggle */}
          <button
            onClick={toggleTheme}
            className="p-2.5 rounded-full border border-sentinel-border bg-sentinel-card hover:bg-sentinel-border/40 text-sentinel-text shadow-subtle transition-transform active:scale-95"
            aria-label="Toggle theme"
          >
            {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-sentinel-muted" />}
          </button>

          {/* Notification Button */}
          <button
            onClick={() => alert('All active opportunity alerts are enabled & synced with Telegram.')}
            className="p-2.5 rounded-full border border-sentinel-border bg-sentinel-card hover:bg-sentinel-border/40 text-sentinel-text shadow-subtle relative transition-transform active:scale-95"
            aria-label="Notifications"
          >
            <Bell className="w-4 h-4 text-sentinel-muted" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-sentinel-accent ring-2 ring-sentinel-card" />
          </button>
        </div>
      </header>

      {/* Interactive Search Modal */}
      {isSearchOpen && <SearchModal onClose={() => setIsSearchOpen(false)} />}
    </>
  );
}
