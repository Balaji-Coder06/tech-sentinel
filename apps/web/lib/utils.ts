import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatTimeAgo(isoOrDateString?: string | null): string {
  if (!isoOrDateString) return 'Recently';

  try {
    const date = new Date(isoOrDateString);
    if (isNaN(date.getTime())) return 'Recently';

    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    
    // Future / clock skew safeguard
    if (diffMs < 60000) {
      return 'Just now';
    }

    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 60) {
      return `${diffMins}m ago`;
    }
    if (diffHours < 24) {
      return `${diffHours}h ago`;
    }
    if (diffDays === 1) {
      return 'Yesterday';
    }
    if (diffDays < 7) {
      return `${diffDays}d ago`;
    }
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  } catch {
    return 'Recently';
  }
}

export function formatExpiry(isoOrString?: string): { text: string; urgent: boolean } {
  if (!isoOrString) return { text: 'Ongoing', urgent: false };
  
  const lower = isoOrString.toLowerCase();
  if (lower.includes('day') || lower.includes('hour') || lower.includes('soon') || lower.includes('ends')) {
    return { text: isoOrString, urgent: true };
  }

  try {
    const target = new Date(isoOrString);
    if (isNaN(target.getTime())) return { text: isoOrString, urgent: false };

    const now = new Date();
    const diffDays = Math.ceil((target.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

    if (diffDays <= 0) return { text: 'Expires Today', urgent: true };
    if (diffDays === 1) return { text: 'Ends Tomorrow', urgent: true };
    if (diffDays <= 3) return { text: `Ends in ${diffDays} days`, urgent: true };
    if (diffDays <= 7) return { text: `Ends in ${diffDays} days`, urgent: false };
    
    return {
      text: `Expires ${target.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`,
      urgent: false
    };
  } catch {
    return { text: isoOrString, urgent: false };
  }
}
