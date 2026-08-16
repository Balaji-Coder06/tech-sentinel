'use client';

import React from 'react';
import { Opportunity } from '../lib/types';
import { formatExpiry } from '../lib/utils';
import { X, ExternalLink, ShieldCheck, Copy, Check, Sparkles, Clock, AlertCircle } from 'lucide-react';

interface ClaimModalProps {
  opportunity: Opportunity;
  onClose: () => void;
}

export function ClaimModal({ opportunity: opp, onClose }: ClaimModalProps) {
  const [copied, setCopied] = React.useState(false);
  const expiry = formatExpiry(opp.expiry_date);

  const copyCoupon = () => {
    if (opp.coupon_code) {
      navigator.clipboard.writeText(opp.coupon_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div
        className="bg-sentinel-card border border-sentinel-border w-full max-w-lg rounded-3xl shadow-2xl overflow-hidden flex flex-col relative"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="p-4 border-b border-sentinel-border flex items-center justify-between bg-sentinel-card/90">
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-1 rounded-full bg-sentinel-accent text-white text-xs font-black uppercase tracking-wider">
              {opp.current_value}
            </span>
            <span className="text-xs text-sentinel-muted font-bold">{opp.provider}</span>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-full text-sentinel-muted hover:text-sentinel-text hover:bg-sentinel-border/50 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 sm:p-6 space-y-5 overflow-y-auto max-h-[80vh]">
          <div className="space-y-1.5">
            <h3 className="text-lg sm:text-xl font-black text-sentinel-text leading-snug">
              {opp.title}
            </h3>
            <p className="text-xs sm:text-sm text-sentinel-muted leading-relaxed">
              {opp.description}
            </p>
          </div>

          {/* Quick Metrics Card */}
          <div className="grid grid-cols-2 gap-3 p-3.5 rounded-2xl bg-sentinel-border/40 border border-sentinel-border text-xs">
            <div>
              <span className="text-[10px] text-sentinel-muted uppercase block font-semibold">Standard Value</span>
              <span className="font-bold text-sentinel-text text-sm">{opp.normal_value || 'Always Free'}</span>
            </div>
            <div>
              <span className="text-[10px] text-sentinel-muted uppercase block font-semibold">Eligibility</span>
              <span className="font-bold text-sentinel-text text-sm">{opp.eligibility}</span>
            </div>
            <div>
              <span className="text-[10px] text-sentinel-muted uppercase block font-semibold">Status / Expiry</span>
              <div className="flex items-center gap-1 font-bold text-sentinel-accent">
                <Clock className="w-3.5 h-3.5" />
                <span>{expiry.text}</span>
              </div>
            </div>
            <div>
              <span className="text-[10px] text-sentinel-muted uppercase block font-semibold">Verification</span>
              <div className="flex items-center gap-1 font-bold text-sentinel-success">
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>Official Source</span>
              </div>
            </div>
          </div>

          {/* Coupon / Voucher Code If Present */}
          {opp.coupon_code && (
            <div className="p-3.5 rounded-2xl border-2 border-dashed border-sentinel-accent/50 bg-sentinel-accent/5 flex items-center justify-between">
              <div>
                <span className="text-[10px] uppercase font-bold text-sentinel-accent block">Coupon / Access Code</span>
                <span className="font-mono font-bold text-base text-sentinel-text">{opp.coupon_code}</span>
              </div>
              <button
                onClick={copyCoupon}
                className="py-1.5 px-3 rounded-lg bg-sentinel-accent text-white font-bold text-xs flex items-center gap-1 shadow-sm transition-all"
              >
                {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Copied' : 'Copy'}</span>
              </button>
            </div>
          )}

          {/* Requirements & Notes */}
          {opp.requirements && (
            <div className="space-y-1.5 text-xs">
              <span className="font-bold text-sentinel-text flex items-center gap-1">
                <AlertCircle className="w-3.5 h-3.5 text-sentinel-warning" />
                <span>Claim Instructions & Requirements:</span>
              </span>
              <p className="text-sentinel-muted leading-relaxed bg-sentinel-card p-2.5 rounded-xl border border-sentinel-border">
                {opp.requirements}
              </p>
            </div>
          )}

          {/* Why You Should Care */}
          {opp.why_care && (
            <div className="p-3 rounded-xl bg-sentinel-accent/10 border border-sentinel-accent/20 text-xs space-y-1">
              <span className="font-bold text-sentinel-accent flex items-center gap-1">
                <Sparkles className="w-3.5 h-3.5" />
                <span>Sentinel Radar Note:</span>
              </span>
              <p className="text-sentinel-text/90 leading-relaxed">
                {opp.why_care}
              </p>
            </div>
          )}
        </div>

        {/* Modal Action Footer */}
        <div className="p-4 border-t border-sentinel-border bg-sentinel-card/90 flex items-center justify-between gap-3">
          <button
            onClick={onClose}
            className="py-2.5 px-4 rounded-xl border border-sentinel-border hover:bg-sentinel-border/40 text-xs font-semibold text-sentinel-muted transition-colors"
          >
            Cancel
          </button>

          <a
            href={opp.claim_url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={onClose}
            className="py-2.5 px-6 rounded-xl bg-sentinel-accent hover:bg-sentinel-accentHover text-white font-extrabold text-xs flex items-center gap-2 shadow-glow transition-all active:scale-95 flex-1 justify-center"
          >
            <span>Proceed to Claim Official Offer</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>
    </div>
  );
}
