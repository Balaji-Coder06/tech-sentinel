import { DatabaseSync } from 'node:sqlite';
import { rankOpportunities, getOpportunityRankingBreakdown } from './lib/opportunity-ranking.ts';

const db = new DatabaseSync('../../database/tech_sentinel.db');
const rows = db.prepare('SELECT * FROM opportunities').all().map(r => ({
  ...r,
  is_expiring_soon: Boolean(r.is_expiring_soon)
}));

const ranked = rankOpportunities(rows, 'score');
console.log(`\n--- TOP RANKED OPPORTUNITIES (Total Active: ${ranked.length}) ---`);

ranked.forEach((opp, i) => {
  const b = getOpportunityRankingBreakdown(opp);
  console.log(`[#${i + 1}] Score: ${b.total} pts | Provider: ${opp.provider} | Status: ${opp.status} | Value: ${opp.current_value}`);
  console.log(`     Title: ${opp.title}`);
  console.log(`     Claim: ${opp.claim_url}`);
  console.log(`     Breakdown: Value=${b.value}/20, Urgency=${b.urgency}/20, Elig=${b.eligibility}/20, Verif=${b.verification}/20, Strength=${b.opportunityStrength}/10, Access=${b.accessibility}/10\n`);
});
