import type { Opportunity } from './types';

/**
 * =============================================================================
 * TECH SENTINEL - DETERMINISTIC OPPORTUNITY INTELLIGENCE ENGINE
 * =============================================================================
 * Identifies, classifies, verifies, scores, and ranks genuine developer opportunities.
 * Evaluates candidates on a normalized 0–100 score using six transparent dimensions:
 * 
 * 1. Monetary / Practical Value  (Max 20 pts) - Explicit dollar, credit, or fee waiver value
 * 2. Deadline Urgency            (Max 20 pts) - Imminent expiration countdown bonus
 * 3. Eligibility Relevance       (Max 20 pts) - Broad global developer accessibility
 * 4. Verification Confidence     (Max 20 pts) - Official provider validation & domain match
 * 5. Opportunity Strength        (Max 10 pts) - Actionable benefit classification
 * 6. Accessibility               (Max 10 pts) - Free friction-free claim path
 * =============================================================================
 */

export interface OpportunityRankingBreakdown {
  value: number;               // 0 - 20
  urgency: number;             // 0 - 20
  eligibility: number;         // 0 - 20
  verification: number;        // 0 - 20
  opportunityStrength: number; // 0 - 10
  accessibility: number;       // 0 - 10
  total: number;               // 0 - 100
}

export type OpportunityClassification = 'HIGH' | 'MEDIUM' | 'LOW' | 'NOT_AN_OPPORTUNITY';

/**
 * ANTI-PATTERNS (Negative Signals that disqualify generic articles from becoming opportunities)
 */
const NEGATIVE_SIGNALS = [
  /\b(free tutorial|free article|free guide|free opinion|interview|podcast|died on the free tier|blog post|free course review|my thoughts)\b/i,
  /\b(how to modernize|how to build|getting started with|tutorial for beginners)\b/i
];

/**
 * STRONG OPPORTUNITY POSITIVE SIGNALS
 */
const HIGH_OPP_SIGNALS = [
  /\b(credits?|\$\d+\s+credits?|100%\s*off|fee waiver|exam voucher|certification voucher|hackathon|prize pool|student pack|free forever|arm compute|24gb ram|always free|free tier compute)\b/i
];

const MEDIUM_OPP_SIGNALS = [
  /\b(developer program|free access|grant|fellowship|beta access|free tier|free plan|free trial|community edition)\b/i
];

/**
 * 1. CLASSIFY OPPORTUNITY CANDIDATES
 */
export function classifyOpportunity(
  text: string,
  title = '',
  url = ''
): OpportunityClassification {
  const combined = `${title} ${text} ${url}`.toLowerCase();

  // 1. Check for negative anti-pattern signals first
  for (const neg of NEGATIVE_SIGNALS) {
    if (neg.test(combined)) {
      return 'NOT_AN_OPPORTUNITY';
    }
  }

  // 2. High-value actionable opportunities
  for (const pos of HIGH_OPP_SIGNALS) {
    if (pos.test(combined)) {
      return 'HIGH';
    }
  }

  // 3. Medium-value developer programs & grants
  for (const med of MEDIUM_OPP_SIGNALS) {
    if (med.test(combined)) {
      return 'MEDIUM';
    }
  }

  // 4. Default: Not an actionable opportunity
  return 'NOT_AN_OPPORTUNITY';
}

/**
 * 2. MONETARY / PRACTICAL VALUE SCORE (0 - 20 points)
 */
export function calculateValueScore(opp: Pick<Opportunity, 'current_value' | 'normal_value' | 'title' | 'description'>): number {
  const combined = `${opp.current_value || ''} ${opp.normal_value || ''} ${opp.title || ''} ${opp.description || ''}`.toLowerCase();

  if (/\b(\$300|\$500|\$1000|300\s*credits?|50,000|200,000)\b/i.test(combined)) {
    return 20;
  }
  if (/\b(\$100|\$99|100%\s*off|100%\s*fee\s*waiver|exam\s*voucher)\b/i.test(combined)) {
    return 18;
  }
  if (/\b(\$50|\$25|free\s*tier\s*compute|24gb\s*ram|14,400|512mb\s*cluster)\b/i.test(combined)) {
    return 15;
  }
  if (/\b(free|free\s*forever|free\s*entry|always\s*free|free\s*plan)\b/i.test(combined)) {
    return 10;
  }

  return 5; // Unspecified or generic
}

/**
 * 3. DEADLINE URGENCY SCORE (0 - 20 points)
 */
export function calculateUrgencyScore(
  opp: Pick<Opportunity, 'expiry_date' | 'is_expiring_soon' | 'status'>,
  now = new Date()
): number {
  if (opp.status === 'EXPIRED') return 0;

  const expiry = opp.expiry_date?.trim();
  if (!expiry || expiry.toLowerCase() === 'ongoing' || expiry.toLowerCase() === 'perpetual' || expiry.toLowerCase() === 'limited') {
    return 8; // Ongoing / perpetual benefits have reliable utility but lower immediate urgency
  }

  // Check qualitative phrases
  const lower = expiry.toLowerCase();
  if (lower.includes('today') || lower.includes('hour')) return 20;
  if (lower.includes('tomorrow') || lower.includes('1 day')) return 19;
  if (lower.includes('3 days') || lower.includes('in 3')) return 17;
  if (lower.includes('soon') || opp.is_expiring_soon) return 14;

  // Evaluate ISO or standard date strings
  try {
    const target = new Date(expiry);
    if (!isNaN(target.getTime())) {
      const diffMs = target.getTime() - now.getTime();
      const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

      if (diffDays < 0) return 0;     // Already expired
      if (diffDays <= 1) return 20;   // Expires today / tomorrow
      if (diffDays <= 3) return 17;   // Ends in 3 days
      if (diffDays <= 7) return 14;   // Ends this week
      if (diffDays <= 30) return 10;  // Active month
      return 8;                       // Long-term active
    }
  } catch {}

  return opp.is_expiring_soon ? 14 : 8;
}

/**
 * 4. ELIGIBILITY RELEVANCE SCORE (0 - 20 points)
 */
export function calculateEligibilityScore(opp: Pick<Opportunity, 'eligibility'>): number {
  const elig = (opp.eligibility || '').toLowerCase();

  if (elig.includes('all') || elig.includes('global') || elig.includes('worldwide') || elig.includes('everyone')) {
    return 20;
  }
  if (elig.includes('student')) {
    return 18;
  }
  if (elig.includes('startup') || elig.includes('founder') || elig.includes('maintainer')) {
    return 16;
  }
  if (elig.includes('new') || elig.includes('first-time')) {
    return 14;
  }

  return 12;
}

/**
 * 5. VERIFICATION CONFIDENCE SCORE (0 - 20 points)
 */
export function calculateVerificationScore(opp: Pick<Opportunity, 'verification_status' | 'status'>): number {
  if (opp.status === 'EXPIRED' || opp.verification_status === 'EXPIRED') return 0;
  if (opp.verification_status === 'VERIFIED') return 20;
  if (opp.verification_status === 'NEEDS_VERIFICATION') return 10;
  return 5;
}

/**
 * 6. OPPORTUNITY STRENGTH SCORE (0 - 10 points)
 */
/**
 * HELPER: Check whether an opportunity matches user's preferred opportunity types
 */
export function isOpportunityTypePreferred(
  opp: Pick<Opportunity, 'opportunity_type' | 'category' | 'title' | 'description'>,
  preferredTypes?: string[]
): boolean {
  if (!preferredTypes || preferredTypes.length === 0) return true;
  const normType = (opp.opportunity_type || '').toLowerCase().trim();
  const normCat = (opp.category || '').toLowerCase().trim();
  const text = `${opp.title || ''} ${opp.description || ''}`.toLowerCase();

  return preferredTypes.some(t => {
    const nt = t.toLowerCase().trim();
    if (normType === nt || normCat === nt) return true;
    if (nt === 'ai_credits' && (normType.includes('ai') || normCat.includes('ai') || text.includes('tokens') || text.includes('api credit') || text.includes('inference'))) return true;
    if (nt === 'cloud' && (normType.includes('cloud') || normCat.includes('cloud') || text.includes('aws') || text.includes('gcp') || text.includes('azure') || text.includes('oracle'))) return true;
    if (nt === 'certification' && (normType.includes('cert') || text.includes('voucher') || text.includes('exam') || text.includes('waiver'))) return true;
    if (nt === 'software' && (normType.includes('software') || text.includes('license') || text.includes('saas') || text.includes('ide'))) return true;
    if (nt === 'competition' && (normType.includes('competition') || text.includes('hackathon') || text.includes('prize'))) return true;
    if (nt === 'education' && (normType.includes('education') || text.includes('student') || text.includes('pack'))) return true;
    if (nt === 'career' && (normType.includes('career') || text.includes('internship') || text.includes('fellowship'))) return true;
    return false;
  });
}

/**
 * 6. OPPORTUNITY STRENGTH SCORE (0 - 10 points)
 */
export function calculateStrengthScore(
  opp: Pick<Opportunity, 'title' | 'description' | 'claim_url' | 'opportunity_type' | 'category'>,
  preferredTypes?: string[]
): number {
  const classification = classifyOpportunity(opp.description || '', opp.title || '', opp.claim_url || '');
  let base = 0;
  if (classification === 'HIGH') base = 10;
  else if (classification === 'MEDIUM') base = 7;
  else if (classification === 'LOW') base = 4;

  if (preferredTypes && preferredTypes.length > 0) {
    const isPreferred = isOpportunityTypePreferred(opp, preferredTypes);
    if (!isPreferred) {
      // De-prioritize non-selected opportunity types
      return 0;
    }
  }

  return base;
}

/**
 * 7. ACCESSIBILITY SCORE (0 - 10 points)
 */
export function calculateAccessibilityScore(opp: Pick<Opportunity, 'claim_url' | 'description' | 'eligibility'>): number {
  const text = `${opp.claim_url || ''} ${opp.description || ''} ${opp.eligibility || ''}`.toLowerCase();
  
  if (text.includes('no credit card') || text.includes('instant') || text.includes('direct')) {
    return 10;
  }
  if (opp.claim_url && opp.claim_url.startsWith('http')) {
    return 8; // Standard web claim
  }
  return 5;
}

/**
 * FULL OPPORTUNITY RANKING BREAKDOWN
 */
export function getOpportunityRankingBreakdown(
  opp: Opportunity,
  now: Date = new Date(),
  preferredTypes?: string[]
): OpportunityRankingBreakdown {
  const value = calculateValueScore(opp);
  const urgency = calculateUrgencyScore(opp, now);
  const eligibility = calculateEligibilityScore(opp);
  const verification = calculateVerificationScore(opp);
  const opportunityStrength = calculateStrengthScore(opp, preferredTypes);
  const accessibility = calculateAccessibilityScore(opp);

  const rawTotal = value + urgency + eligibility + verification + opportunityStrength + accessibility;
  const total = Math.max(0, Math.min(100, Math.round(rawTotal)));

  return {
    value,
    urgency,
    eligibility,
    verification,
    opportunityStrength,
    accessibility,
    total
  };
}

/**
 * CALCULATE OPPORTUNITY SCORE (0–100)
 */
export function calculateOpportunityScore(
  opp: Opportunity,
  now: Date = new Date(),
  preferredTypes?: string[]
): number {
  return getOpportunityRankingBreakdown(opp, now, preferredTypes).total;
}

/**
 * RANK OPPORTUNITIES
 * Sorts opportunities for display on Free Radar and Home widgets.
 * Automatically excludes expired deals from the active list.
 */
export function rankOpportunities(
  opps: Opportunity[],
  sortBy: 'score' | 'expiry' | 'value' = 'score',
  now: Date = new Date(),
  preferredTypes?: string[]
): Opportunity[] {
  // Exclude expired deals from active radar
  const activeOpps = opps.filter(o => o.status !== 'EXPIRED' && o.verification_status !== 'EXPIRED');

  return [...activeOpps].sort((a, b) => {
    // When personalized by preferredTypes, prioritize matching opportunity categories
    if (preferredTypes && preferredTypes.length > 0) {
      const matchA = isOpportunityTypePreferred(a, preferredTypes);
      const matchB = isOpportunityTypePreferred(b, preferredTypes);
      if (matchA && !matchB) return -1;
      if (matchB && !matchA) return 1;
    }

    if (sortBy === 'expiry') {
      const urgencyA = calculateUrgencyScore(a, now);
      const urgencyB = calculateUrgencyScore(b, now);
      if (urgencyB !== urgencyA) return urgencyB - urgencyA;
    } else if (sortBy === 'value') {
      const valA = calculateValueScore(a);
      const valB = calculateValueScore(b);
      if (valB !== valA) return valB - valA;
    }

    // Default: Overall Opportunity Score (incorporating user opportunity preferences)
    const scoreA = calculateOpportunityScore(a, now, preferredTypes);
    const scoreB = calculateOpportunityScore(b, now, preferredTypes);
    if (scoreB !== scoreA) return scoreB - scoreA;

    // Tie breaker: Verification status then ID
    if (a.verification_status === 'VERIFIED' && b.verification_status !== 'VERIFIED') return -1;
    if (b.verification_status === 'VERIFIED' && a.verification_status !== 'VERIFIED') return 1;

    return a.id.localeCompare(b.id);
  });
}
