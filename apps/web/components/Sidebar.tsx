'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  Home, 
  Flame, 
  Gift, 
  Bookmark, 
  Newspaper, 
  Sliders, 
  Sparkles
} from 'lucide-react';
import { cn } from '../lib/utils';

export function Sidebar() {
  const pathname = usePathname();

  const navItems = [
    { label: 'Home', href: '/', icon: Home },
    { label: 'News Feed', href: '/news', icon: Flame },
    { label: 'Free Radar', href: '/free', icon: Gift, badge: '🔥 HOT' },
    { label: 'Daily Reports', href: '/reports', icon: Newspaper },
    { label: 'Saved Items', href: '/saved', icon: Bookmark },
  ];

  const secondaryItems = [
    { label: 'Preferences', href: '/settings', icon: Sliders },
  ];

  return (
    <aside className="hidden lg:flex flex-col w-64 border-r border-sentinel-border bg-sentinel-card/40 backdrop-blur-md h-screen sticky top-0 px-5 py-6 justify-between select-none">
      <div className="space-y-7">
        {/* Brand Header */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-sentinel-accent to-orange-400 flex items-center justify-center shadow-glow transition-transform group-hover:scale-105">
            <Sparkles className="w-5 h-5 text-white animate-pulse-subtle" />
          </div>
          <div>
            <span className="font-bold text-lg tracking-tight flex items-center gap-1.5 text-sentinel-text">
              TECH SENTINEL
            </span>
            <p className="text-[11px] font-medium text-sentinel-muted tracking-wider uppercase">
              Opportunity Intelligence
            </p>
          </div>
        </Link>

        {/* Primary Navigation */}
        <nav className="space-y-1.5">
          <div className="text-[11px] font-semibold tracking-wider text-sentinel-muted uppercase px-3 mb-2">
            Intelligence
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center justify-between px-3.5 py-2.5 rounded-xl font-medium text-sm transition-all group',
                  isActive
                    ? 'bg-sentinel-accent text-white shadow-sm font-semibold'
                    : 'text-sentinel-muted hover:text-sentinel-text hover:bg-sentinel-border/50'
                )}
              >
                <div className="flex items-center gap-3">
                  <Icon className={cn('w-4 h-4 transition-transform group-hover:scale-110', isActive ? 'text-white' : 'text-sentinel-muted')} />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className={cn(
                    'text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider',
                    isActive ? 'bg-white/20 text-white' : 'bg-sentinel-accent/10 text-sentinel-accent'
                  )}>
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Customization */}
        <div className="space-y-1.5">
          <div className="text-[11px] font-semibold tracking-wider text-sentinel-muted uppercase px-3 mb-2">
            Personalize
          </div>
          {secondaryItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-medium text-sm transition-all group',
                  isActive
                    ? 'bg-sentinel-accent text-white font-semibold'
                    : 'text-sentinel-muted hover:text-sentinel-text hover:bg-sentinel-border/50'
                )}
              >
                <Icon className={cn('w-4 h-4 transition-transform group-hover:scale-110', isActive ? 'text-white' : 'text-sentinel-muted')} />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Sentinel Active Status Badge */}
      <div className="px-3.5 py-2.5 rounded-2xl border border-sentinel-border bg-sentinel-card shadow-subtle flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
          </span>
          <span className="text-xs font-bold text-sentinel-text">Sentinel Active</span>
        </div>
      </div>
    </aside>
  );
}
