import assert from 'node:assert/strict';
import { 
  classifyOpportunity,
  calculateValueScore,
  calculateUrgencyScore,
  calculateEligibilityScore,
  calculateVerificationScore,
  calculateStrengthScore,
  calculateAccessibilityScore,
  calculateOpportunityScore,
  getOpportunityRankingBreakdown,
  rankOpportunities
} from './lib/opportunity-ranking.ts';

const referenceNow = new Date('2026-08-16T12:00:00Z');

console.log('🧪 RUNNING OPPORTUNITY INTELLIGENCE ENGINE TEST SUITE...\n');

// -------------------------------------------------------------
// Test 1: Genuine cloud-credit opportunity classified correctly
// -------------------------------------------------------------
{
  const text = 'Google Cloud provides $300 in free credits and compute for all developers.';
  const classification = classifyOpportunity(text, 'Google Cloud Free Program: $300 Credits', 'https://cloud.google.com/free');
  assert.equal(classification, 'HIGH');
  console.log('✅ Test 1 Passed: Genuine cloud-credit offer classified as HIGH opportunity.');
}

// -------------------------------------------------------------
// Test 2: Certification voucher classified correctly
// -------------------------------------------------------------
{
  const text = 'Complete the challenge to receive a 100% exam fee waiver certification voucher.';
  const classification = classifyOpportunity(text, 'Microsoft Azure AI Certification Voucher (100% Fee Waiver)', 'https://learn.microsoft.com');
  assert.equal(classification, 'HIGH');
  console.log('✅ Test 2 Passed: 100% fee waiver exam voucher classified as HIGH opportunity.');
}

// -------------------------------------------------------------
// Test 3: Hackathon classified correctly
// -------------------------------------------------------------
{
  const text = 'Build serverless apps on AWS. $50,000 prize pool and $100 instant credits for participants.';
  const classification = classifyOpportunity(text, 'AWS Summer Hackathon ($50,000 Prize Pool)', 'https://aws.amazon.com/events');
  assert.equal(classification, 'HIGH');
  console.log('✅ Test 3 Passed: Hackathon with prize pool & credits classified as HIGH opportunity.');
}

// -------------------------------------------------------------
// Test 4: Generic "free tutorial" is NOT an opportunity
// -------------------------------------------------------------
{
  const text = 'Check out this free tutorial on building web apps with React.';
  const classification = classifyOpportunity(text, 'Free Tutorial: React 19 for Beginners', 'https://example.com/blog/tutorial');
  assert.equal(classification, 'NOT_AN_OPPORTUNITY');
  console.log('✅ Test 4 Passed: "Free tutorial" correctly rejected as NOT_AN_OPPORTUNITY.');
}

// -------------------------------------------------------------
// Test 5: Generic news containing "free" is NOT an opportunity
// -------------------------------------------------------------
{
  const text = 'I tested n8n and Zapier and one died on the free tier during workflow execution.';
  const classification = classifyOpportunity(text, 'I built the same automation in n8n and Make — one died on the free tier', 'https://dev.to/post/died-on-the-free-tier');
  assert.equal(classification, 'NOT_AN_OPPORTUNITY');
  console.log('✅ Test 5 Passed: Opinion/comparison article containing "free" correctly rejected.');
}

// -------------------------------------------------------------
// Test 6: Verified opportunity ranks above unverified equivalent
// -------------------------------------------------------------
{
  const verifiedOpp = {
    id: 'opp_ver',
    title: 'Cloudflare Free Plan: Unlimited Edge CDN',
    provider: 'Cloudflare',
    current_value: 'FREE',
    eligibility: 'All Developers',
    claim_url: 'https://cloudflare.com/free',
    verification_status: 'VERIFIED',
    status: 'ACTIVE',
    importance_score: 85,
    relevance_score: 85,
    priority: 'High',
    opportunity_type: 'cloud',
    category: 'cloud'
  };

  const unverifiedOpp = {
    id: 'opp_unver',
    title: 'Cloudflare Free Plan: Unlimited Edge CDN',
    provider: 'Cloudflare',
    current_value: 'FREE',
    eligibility: 'All Developers',
    claim_url: 'https://cloudflare.com/free',
    verification_status: 'NEEDS_VERIFICATION',
    status: 'ACTIVE',
    importance_score: 85,
    relevance_score: 85,
    priority: 'High',
    opportunity_type: 'cloud',
    category: 'cloud'
  };

  const scoreVerified = calculateOpportunityScore(verifiedOpp, referenceNow);
  const scoreUnverified = calculateOpportunityScore(unverifiedOpp, referenceNow);
  assert(scoreVerified > scoreUnverified, `Verified score (${scoreVerified}) should exceed unverified (${scoreUnverified})`);
  console.log(`✅ Test 6 Passed: Verified opportunity (${scoreVerified} pts) outranks unverified opportunity (${scoreUnverified} pts).`);
}

// -------------------------------------------------------------
// Test 7: Expiring opportunity gets urgency boost
// -------------------------------------------------------------
{
  const urgentOpp = {
    id: 'opp_urgent',
    title: 'Azure Certification Voucher',
    provider: 'Microsoft',
    current_value: '100% OFF',
    eligibility: 'All Developers',
    claim_url: 'https://learn.microsoft.com',
    verification_status: 'VERIFIED',
    status: 'EXPIRING_SOON',
    expiry_date: '2026-08-17T12:00:00Z', // 1 day remaining
    is_expiring_soon: true,
    importance_score: 90,
    relevance_score: 90,
    priority: 'Critical',
    opportunity_type: 'certification',
    category: 'cloud'
  };

  const ongoingOpp = {
    id: 'opp_ongoing',
    title: 'Azure Certification Voucher',
    provider: 'Microsoft',
    current_value: '100% OFF',
    eligibility: 'All Developers',
    claim_url: 'https://learn.microsoft.com',
    verification_status: 'VERIFIED',
    status: 'ACTIVE',
    expiry_date: 'Ongoing',
    is_expiring_soon: false,
    importance_score: 90,
    relevance_score: 90,
    priority: 'High',
    opportunity_type: 'certification',
    category: 'cloud'
  };

  const urgencyScore = calculateUrgencyScore(urgentOpp, referenceNow);
  const ongoingUrgency = calculateUrgencyScore(ongoingOpp, referenceNow);
  assert(urgencyScore > ongoingUrgency, `Urgent score (${urgencyScore}) should exceed ongoing (${ongoingUrgency})`);
  console.log(`✅ Test 7 Passed: Expiring offer receives urgency boost (${urgencyScore} pts vs ${ongoingUrgency} pts).`);
}

// -------------------------------------------------------------
// Test 8: Expired opportunity is excluded from active radar
// -------------------------------------------------------------
{
  const activeOpp = {
    id: 'opp_act',
    title: 'Active Deal',
    provider: 'Provider',
    current_value: 'FREE',
    eligibility: 'All Developers',
    claim_url: 'https://example.com/act',
    verification_status: 'VERIFIED',
    status: 'ACTIVE'
  };

  const expiredOpp = {
    id: 'opp_exp',
    title: 'Expired Deal',
    provider: 'Provider',
    current_value: 'FREE',
    eligibility: 'All Developers',
    claim_url: 'https://example.com/exp',
    verification_status: 'EXPIRED',
    status: 'EXPIRED'
  };

  const ranked = rankOpportunities([activeOpp, expiredOpp], 'score', referenceNow);
  assert.equal(ranked.length, 1);
  assert.equal(ranked[0].id, 'opp_act');
  console.log('✅ Test 8 Passed: Expired opportunities automatically excluded from active radar output.');
}

// -------------------------------------------------------------
// Test 9: Unknown deadline does not crash
// -------------------------------------------------------------
{
  const nullExpiryOpp = {
    id: 'opp_null',
    title: 'Free MongoDB Cluster',
    provider: 'MongoDB',
    current_value: 'FREE',
    eligibility: 'All Developers',
    claim_url: 'https://mongodb.com',
    verification_status: 'VERIFIED',
    status: 'ACTIVE',
    expiry_date: null
  };

  const score = calculateOpportunityScore(nullExpiryOpp, referenceNow);
  assert(typeof score === 'number' && score >= 0 && score <= 100);
  console.log(`✅ Test 9 Passed: Null/missing deadline handled safely without error (Score: ${score} pts).`);
}

// -------------------------------------------------------------
// Test 10: Ranking is deterministic
// -------------------------------------------------------------
{
  const list = [
    { id: 'opp_1', title: 'A', provider: 'P1', current_value: 'FREE', eligibility: 'All Developers', claim_url: 'https://p1.com', verification_status: 'VERIFIED', status: 'ACTIVE' },
    { id: 'opp_2', title: 'B', provider: 'P2', current_value: '$300 CREDITS', eligibility: 'All Developers', claim_url: 'https://p2.com', verification_status: 'VERIFIED', status: 'ACTIVE' },
    { id: 'opp_3', title: 'C', provider: 'P3', current_value: '100% OFF', eligibility: 'Students', claim_url: 'https://p3.com', verification_status: 'VERIFIED', status: 'EXPIRING_SOON', expiry_date: '2026-08-17T00:00:00Z' }
  ];

  const r1 = rankOpportunities(list, 'score', referenceNow).map(o => o.id);
  const r2 = rankOpportunities(list, 'score', referenceNow).map(o => o.id);
  const r3 = rankOpportunities(list, 'score', referenceNow).map(o => o.id);

  assert.deepEqual(r1, r2);
  assert.deepEqual(r2, r3);
  console.log(`✅ Test 10 Passed: Opportunity ranking is 100% deterministic: [${r1.join(', ')}].`);
}

// -------------------------------------------------------------
// Test 11: Claim URL remains authentic
// -------------------------------------------------------------
{
  const opp = {
    id: 'opp_url_check',
    title: 'Oracle Cloud Free Tier',
    provider: 'Oracle',
    current_value: 'FREE',
    eligibility: 'All Developers',
    claim_url: 'https://www.oracle.com/cloud/free/',
    verification_status: 'VERIFIED',
    status: 'ACTIVE'
  };

  const ranked = rankOpportunities([opp], 'score', referenceNow);
  assert.equal(ranked[0].claim_url, 'https://www.oracle.com/cloud/free/');
  console.log('✅ Test 11 Passed: Direct claim URL preserved with zero alteration.');
}

console.log('\n🎉 ALL 11 OPPORTUNITY INTELLIGENCE TESTS PASSED PERFECTLY!\n');
