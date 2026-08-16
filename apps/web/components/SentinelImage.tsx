'use client';

import React, { useState } from 'react';
import { 
  Sparkles, 
  Cpu, 
  Cloud, 
  Code2, 
  GitBranch, 
  ShieldCheck, 
  Rocket, 
  GraduationCap, 
  Zap
} from 'lucide-react';

interface SentinelImageProps {
  src?: string | null;
  alt: string;
  category?: string;
  className?: string;
}

export function SentinelImage({
  src,
  alt,
  category = 'development',
  className = 'w-full h-full object-cover transition-transform duration-500 group-hover:scale-105',
}: SentinelImageProps) {
  const [hasError, setHasError] = useState(false);

  const cleanSrc = (src && typeof src === 'string' && src.trim().length > 5) ? src.trim() : null;
  const showImage = cleanSrc && !hasError;

  const catLower = (category || 'development').toLowerCase().replace(/[\s_-]+/g, '_');

  // Category-specific aesthetic fallback configuration
  const getFallbackConfig = (cat: string) => {
    switch (cat) {
      case 'ai':
        return {
          gradient: 'from-violet-950/90 via-indigo-950/70 to-neutral-900',
          icon: Cpu,
          label: 'AI & NEURAL INTEL',
          pattern: 'radial-gradient(circle at 75% 25%, rgba(139, 92, 246, 0.25) 0%, transparent 60%)'
        };
      case 'cloud':
        return {
          gradient: 'from-cyan-950/90 via-blue-950/70 to-neutral-900',
          icon: Cloud,
          label: 'CLOUD & INFRASTRUCTURE',
          pattern: 'radial-gradient(circle at 75% 25%, rgba(6, 182, 212, 0.25) 0%, transparent 60%)'
        };
      case 'open_source':
        return {
          gradient: 'from-emerald-950/90 via-teal-950/70 to-neutral-900',
          icon: GitBranch,
          label: 'OPEN SOURCE ECOSYSTEM',
          pattern: 'radial-gradient(circle at 75% 25%, rgba(16, 185, 129, 0.25) 0%, transparent 60%)'
        };
      case 'cybersecurity':
        return {
          gradient: 'from-rose-950/90 via-red-950/70 to-neutral-900',
          icon: ShieldCheck,
          label: 'SECURITY & THREAT INTEL',
          pattern: 'radial-gradient(circle at 75% 25%, rgba(244, 63, 94, 0.25) 0%, transparent 60%)'
        };
      case 'startups':
        return {
          gradient: 'from-fuchsia-950/90 via-pink-950/70 to-neutral-900',
          icon: Rocket,
          label: 'STARTUPS & VENTURE',
          pattern: 'radial-gradient(circle at 75% 25%, rgba(217, 70, 239, 0.25) 0%, transparent 60%)'
        };
      case 'education':
        return {
          gradient: 'from-sky-950/90 via-blue-950/70 to-neutral-900',
          icon: GraduationCap,
          label: 'DEVELOPER EDUCATION',
          pattern: 'radial-gradient(circle at 75% 25%, rgba(14, 165, 233, 0.25) 0%, transparent 60%)'
        };
      case 'development':
      default:
        return {
          gradient: 'from-amber-950/90 via-orange-950/70 to-neutral-900',
          icon: Code2,
          label: 'SOFTWARE DEVELOPMENT',
          pattern: 'radial-gradient(circle at 75% 25%, rgba(245, 158, 11, 0.25) 0%, transparent 60%)'
        };
    }
  };

  const theme = getFallbackConfig(catLower);
  const IconComponent = theme.icon;

  if (showImage) {
    return (
      <img
        src={cleanSrc}
        alt={alt}
        className={className}
        onError={() => setHasError(true)}
        loading="lazy"
      />
    );
  }

  // Polished Tech Sentinel Category-Themed Fallback
  return (
    <div 
      className="w-full h-full relative overflow-hidden flex flex-col justify-between p-3 select-none transition-transform duration-500 group-hover:scale-105"
      style={{ 
        background: `linear-gradient(135deg, ${theme.gradient})`,
        backgroundImage: theme.pattern
      }}
    >
      {/* Subtle Background Circuit Mesh */}
      <div className="absolute inset-0 opacity-15 bg-[radial-gradient(#ffffff20_1px,transparent_1px)] [background-size:12px_12px] pointer-events-none" />

      {/* Top Tag */}
      <div className="relative z-10 flex items-center justify-between">
        <div className="flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-black/50 backdrop-blur-md border border-white/10 text-[9px] font-mono font-bold tracking-wider uppercase text-white/90">
          <Zap className="w-2.5 h-2.5 text-sentinel-accent fill-sentinel-accent" />
          <span>SENTINEL</span>
        </div>
      </div>

      {/* Central Watermark Icon */}
      <div className="absolute -right-3 -bottom-3 opacity-20 pointer-events-none">
        <IconComponent className="w-24 h-24 text-white stroke-[1.2]" />
      </div>

      {/* Bottom Information */}
      <div className="relative z-10">
        <span className="text-[10px] font-extrabold tracking-wider font-mono text-white/80 flex items-center gap-1">
          <IconComponent className="w-3 h-3 text-sentinel-accent flex-shrink-0" />
          <span className="truncate">{theme.label}</span>
        </span>
      </div>
    </div>
  );
}
