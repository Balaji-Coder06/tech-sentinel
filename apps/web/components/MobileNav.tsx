'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, Flame, Gift, Bookmark, Sliders } from 'lucide-react';
import { cn } from '../lib/utils';

export function MobileNav() {
  const pathname = usePathname();

  const navItems = [
    { label: 'Home', href: '/', icon: Home },
    { label: 'News', href: '/news', icon: Flame },
    { label: 'Free', href: '/free', icon: Gift, isHighlight: true },
    { label: 'Saved', href: '/saved', icon: Bookmark },
    { label: 'Settings', href: '/settings', icon: Sliders },
  ];

  return (
    <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-50 glass-panel border-t border-sentinel-border px-3 py-2 flex items-center justify-around">
      {navItems.map((item) => {
        const Icon = item.icon;
        const isActive = pathname === item.href;

        if (item.isHighlight) {
          return (
            <Link
              key={item.href}
              href={item.href}
              className="flex flex-col items-center justify-center relative -top-3"
            >
              <div className={cn(
                'w-12 h-12 rounded-full flex items-center justify-center shadow-lg transition-transform active:scale-95',
                isActive
                  ? 'bg-sentinel-accent text-white ring-4 ring-sentinel-accent/20'
                  : 'bg-gradient-to-tr from-sentinel-accent to-orange-400 text-white'
              )}>
                <Icon className="w-5 h-5 animate-pulse-subtle" />
              </div>
              <span className="text-[10px] font-bold mt-1 text-sentinel-accent">
                {item.label}
              </span>
            </Link>
          );
        }

        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              'flex flex-col items-center gap-1 py-1 px-3 rounded-lg transition-colors',
              isActive ? 'text-sentinel-accent font-semibold' : 'text-sentinel-muted'
            )}
          >
            <Icon className="w-5 h-5" />
            <span className="text-[10px] font-medium">{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
