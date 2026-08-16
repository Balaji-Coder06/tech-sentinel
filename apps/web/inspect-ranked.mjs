import { DatabaseSync } from 'node:sqlite';
import { rankNewsItems, getRankingBreakdown } from './lib/ranking.ts';

const db = new DatabaseSync('../../database/tech_sentinel.db');
const rows = db.prepare('SELECT * FROM news ORDER BY published_at DESC LIMIT 80').all().map(r => ({
  ...r,
  tags: typeof r.tags === 'string' ? JSON.parse(r.tags || '[]') : r.tags || []
}));

const ranked = rankNewsItems(rows);
console.log(`\n--- TOP 8 INTELLIGENCE RANKED NEWS (Total Ingested: ${rows.length}) ---`);

ranked.slice(0, 8).forEach((item, i) => {
  const b = getRankingBreakdown(item);
  console.log(`[#${i + 1}] Score: ${b.total} pts | Source: ${item.source_name} | Category: ${item.category}`);
  console.log(`     Title: ${item.title}`);
  console.log(`     Published: ${item.published_at}`);
  console.log(`     Breakdown: Freshness=${b.freshness}/30, SourceQuality=${b.sourceQuality}/25, Relevance=${b.relevance}/20, Popularity=${b.popularity}/15, OppBonus=${b.opportunityPotential}/10\n`);
});
