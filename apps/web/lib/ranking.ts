import type { NewsItem } from './types';

/**
 * =============================================================================
 * TECH SENTINEL - DETERMINISTIC INTELLIGENCE RANKING ENGINE
 * =============================================================================
 * Scores news and intelligence items on a normalized 0–100 scale using five
 * transparent, deterministic factors:
 * 
 * 1. FRESHNESS               (Max 30 pts) - Recency decay based on ISO-8601 UTC
 * 2. SOURCE QUALITY          (Max 25 pts) - Mapped to active first-party & curated feeds
 * 3. RELEVANCE               (Max 20 pts) - Category signal + technical domain keywords
 * 4. POPULARITY / SIGNAL     (Max 15 pts) - Real GitHub stargazers / neutral editorial signal
 * 5. OPPORTUNITY POTENTIAL   (Max 10 pts) - Actionable tool, voucher, or credit indicators
 * =============================================================================
 */

export interface RankingBreakdown {
  freshness: number;            // 0 - 30
  sourceQuality: number;        // 0 - 25
  relevance: number;            // 0 - 20
  popularity: number;           // 0 - 15
  opportunityPotential: number; // 0 - 10
  total: number;                // 0 - 100
}

/**
 * SOURCE QUALITY WEIGHTS (Max 25 pts)
 * Mapped strictly to sources present in the Tech Sentinel collectors.
 */
const SOURCE_QUALITY_MAP: Record<string, number> = {
  // Official first-party partner/cloud feeds
  'official': 25,
  'google cloud': 25,
  'microsoft learn': 25,
  'github education': 25,
  'oracle cloud': 25,
  'cloudflare': 25,
  'groq': 25,
  'aws': 25,

  // Primary technology publications & editorial feeds
  'techcrunch ai': 22,
  'techcrunch': 22,
  'hacker news': 20,
  'hackernews': 20,
  'freecodecamp': 18,
  'freecodecamp news': 18,
  'dev.to': 15,
  'devto': 15,
  'github trending': 15,
  'github': 15
};

/**
 * HIGH-SIGNAL TECHNICAL DOMAIN TOPICS (Max +10 bonus for Relevance)
 */
const TECHNICAL_SIGNALS = [
  'llm', 'agent', 'model', 'framework', 'compiler', 'architecture',
  'infrastructure', 'security', 'cybersecurity', 'database', 'api',
  'open source', 'python', 'rust', 'typescript', 'benchmark',
  'reasoning', 'deep learning', 'distributed', 'kubernetes', 'cloud'
];

/**
 * OPPORTUNITY IDENTIFIERS (Max +10 bonus for Opportunity Potential)
 */
const HIGH_OPPORTUNITY_KEYWORDS = [
  'credits', 'certification', 'voucher', 'hackathon', 'free tier',
  'grant', 'fellowship', 'student pack', 'waived', 'scholarship',
  '$300', '$100', '100% off', 'free forever'
];

const MODERATE_OPPORTUNITY_KEYWORDS = [
  'free tool', 'open access', 'giveaway', 'community edition', 'developer pack', 'free plan'
];

/**
 * 1. FRESHNESS SCORE (0 - 30 points)
 * Evaluates the time delta between item publication and target reference time.
 */
export function calculateFreshnessScore(publishedAt?: string | null, now: Date = new Date()): number {
  if (!publishedAt) return 2;

  try {
    const pubDate = new Date(publishedAt);
    if (isNaN(pubDate.getTime())) return 2;

    const diffMs = now.getTime() - pubDate.getTime();
    const diffHours = diffMs / (1000 * 60 * 60);

    // Negative diff (small clock skew) or published within the last hour
    if (diffHours < 1) return 30;
    if (diffHours < 6) return 26;
    if (diffHours < 12) return 22;
    if (diffHours < 24) return 18;
    if (diffHours < 48) return 12; // < 2 days
    if (diffHours < 168) return 6;  // < 7 days
    return 2;                       // > 7 days
  } catch {
    return 2;
  }
}

/**
 * 2. SOURCE QUALITY SCORE (0 - 25 points)
 * Evaluates the authoritative standing of the originating collector.
 */
export function calculateSourceQualityScore(sourceName?: string | null): number {
  if (!sourceName) return 8;

  const normalized = sourceName.toLowerCase().trim();
  for (const [srcKey, weight] of Object.entries(SOURCE_QUALITY_MAP)) {
    if (normalized.includes(srcKey)) {
      return weight;
    }
  }
  return 8; // Standard baseline for unknown feeds
}

/**
 * 3. RELEVANCE SCORE (0 - 20 points)
 * Evaluates category alignment and depth of technical signals.
 */
/**
 * 3. RELEVANCE SCORE (0 - 20 points)
 * Evaluates category alignment, technical domain signals, and personalized user preferences.
 */
export function calculateRelevanceScore(
  item: Pick<NewsItem, 'category' | 'tags' | 'title' | 'description'>,
  userPreferences?: { categories?: string[]; keywords?: string[] }
): number {
  let baseCategoryScore = 4;
  const category = (item.category || '').toLowerCase().trim();

  if (userPreferences?.categories && userPreferences.categories.length > 0) {
    // Personalized category weighting: elevate selected interests without excluding others
    const normSelected = userPreferences.categories.map(c => c.toLowerCase().trim());
    if (normSelected.includes(category)) {
      baseCategoryScore = 10;
    } else {
      baseCategoryScore = 3;
    }
  } else {
    // Default objective category baseline
    if (category === 'ai') baseCategoryScore = 10;
    else if (['cloud', 'development', 'open_source'].includes(category)) baseCategoryScore = 8;
    else if (category === 'cybersecurity') baseCategoryScore = 7;
    else if (category === 'startups') baseCategoryScore = 6;
  }

  const text = `${item.title || ''} ${item.description || ''} ${(item.tags || []).join(' ')}`.toLowerCase();
  
  let signalMatches = 0;
  for (const sig of TECHNICAL_SIGNALS) {
    if (text.includes(sig)) {
      signalMatches++;
    }
  }

  // Also check user's customized keywords
  if (userPreferences?.keywords && userPreferences.keywords.length > 0) {
    for (const kw of userPreferences.keywords) {
      if (kw && text.includes(kw.toLowerCase().trim())) {
        signalMatches += 2;
      }
    }
  }

  const signalBonus = Math.min(10, signalMatches * 2);
  return Math.min(20, baseCategoryScore + signalBonus);
}

/**
 * 4. POPULARITY / SIGNAL SCORE (0 - 15 points)
 * Evaluates GitHub engagement metrics or assigns neutral editorial baselines.
 */
export function calculatePopularityScore(
  item: Pick<NewsItem, 'source_name' | 'title' | 'description'>
): number {
  const source = (item.source_name || '').toLowerCase();
  const text = `${item.title || ''} ${item.description || ''}`;

  // Evaluate GitHub repository stargazers
  if (source.includes('github') || text.includes('⭐') || text.includes('stars:')) {
    const starMatch = text.match(/⭐\s*([\d,]+)/) || text.match(/stars:\s*([\d,]+)/i);
    if (starMatch) {
      const starCount = parseInt(starMatch[1].replace(/,/g, ''), 10);
      if (!isNaN(starCount)) {
        if (starCount >= 10000) return 15;
        if (starCount >= 2500) return 13;
        if (starCount >= 500) return 10;
        return 8;
      }
    }
    return 8;
  }

  // Curated editorial sources receive a reliable neutral baseline
  if (
    source.includes('techcrunch') ||
    source.includes('hacker news') ||
    source.includes('freecodecamp') ||
    source.includes('dev.to') ||
    source.includes('official')
  ) {
    return 9;
  }

  return 7;
}

/**
 * 5. OPPORTUNITY POTENTIAL SCORE (0 - 10 points)
 * Evaluates whether an item contains actionable developer promotions or credits.
 */
export function calculateOpportunityPotentialScore(
  item: Pick<NewsItem, 'title' | 'description' | 'tags'>
): number {
  const text = `${item.title || ''} ${item.description || ''} ${(item.tags || []).join(' ')}`.toLowerCase();

  for (const kw of HIGH_OPPORTUNITY_KEYWORDS) {
    if (text.includes(kw)) {
      return 10;
    }
  }

  for (const kw of MODERATE_OPPORTUNITY_KEYWORDS) {
    if (text.includes(kw)) {
      return 5;
    }
  }

  return 0;
}

/**
 * FULL RANKING BREAKDOWN HELPER
 * Returns exact component weights for introspection, debugging, and tuning.
 */
export function getRankingBreakdown(
  item: NewsItem,
  now: Date = new Date(),
  userPreferences?: { categories?: string[]; keywords?: string[] }
): RankingBreakdown {
  const freshness = calculateFreshnessScore(item.published_at, now);
  const sourceQuality = calculateSourceQualityScore(item.source_name);
  const relevance = calculateRelevanceScore(item, userPreferences);
  const popularity = calculatePopularityScore(item);
  const opportunityPotential = calculateOpportunityPotentialScore(item);

  const rawTotal = freshness + sourceQuality + relevance + popularity + opportunityPotential;
  const total = Math.max(0, Math.min(100, Math.round(rawTotal)));

  return {
    freshness,
    sourceQuality,
    relevance,
    popularity,
    opportunityPotential,
    total
  };
}

/**
 * CALCULATE INTELLIGENCE SCORE (0–100)
 */
export function calculateIntelligenceScore(
  item: NewsItem,
  now: Date = new Date(),
  userPreferences?: { categories?: string[]; keywords?: string[] }
): number {
  return getRankingBreakdown(item, now, userPreferences).total;
}

/**
 * RANK NEWS ITEMS
 * Sorts an array of news items in descending order of their intelligence score.
 * Ties are broken deterministically by recency (published_at DESC).
 */
export function rankNewsItems(
  items: NewsItem[],
  now: Date = new Date(),
  userPreferences?: { categories?: string[]; keywords?: string[] }
): NewsItem[] {
  return [...items].sort((a, b) => {
    const scoreA = calculateIntelligenceScore(a, now, userPreferences);
    const scoreB = calculateIntelligenceScore(b, now, userPreferences);

    if (scoreB !== scoreA) {
      return scoreB - scoreA;
    }

    // Deterministic tie-breaking by publication timestamp
    const timeA = new Date(a.published_at || 0).getTime();
    const timeB = new Date(b.published_at || 0).getTime();
    return timeB - timeA;
  });
}
