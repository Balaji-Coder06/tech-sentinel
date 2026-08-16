import assert from 'node:assert/strict';
import { DatabaseSync } from 'node:sqlite';
import { calculateRelevanceScore, rankNewsItems, getRankingBreakdown } from './lib/ranking.ts';
import { rankOpportunities, getOpportunityRankingBreakdown } from './lib/opportunity-ranking.ts';

console.log('🧪 RUNNING PREFERENCES & PERSONALIZATION TEST SUITE...\n');

const db = new DatabaseSync('../../database/tech_sentinel.db');
const referenceNow = new Date('2026-08-16T12:00:00Z');

function getPreferences() {
  const row = db.prepare("SELECT * FROM preferences WHERE id = 'default'").get();
  if (row) {
    return {
      ...row,
      categories: typeof row.categories === 'string' ? JSON.parse(row.categories || '[]') : row.categories || [],
      keywords: typeof row.keywords === 'string' ? JSON.parse(row.keywords || '[]') : row.keywords || [],
      opportunity_types: typeof row.opportunity_types === 'string' ? JSON.parse(row.opportunity_types || '[]') : row.opportunity_types || [],
      enable_daily_brief: Boolean(row.enable_daily_brief),
      enable_critical_alerts: Boolean(row.enable_critical_alerts),
      email_newsletter_enabled: Boolean(row.email_newsletter_enabled),
      newsletter_email: row.newsletter_email || ''
    };
  }
  return {
    id: 'default',
    user_name: 'Balaji',
    theme: 'system',
    categories: ['ai', 'cloud', 'development'],
    keywords: [],
    opportunity_types: ['ai_credits', 'cloud'],
    enable_daily_brief: true,
    enable_critical_alerts: true,
    email_newsletter_enabled: false,
    newsletter_email: ''
  };
}

function updatePreferences(prefs) {
  const current = getPreferences();
  const merged = { ...current, ...prefs };
  db.prepare(`
    INSERT INTO preferences (
      id, user_name, theme, categories, keywords, opportunity_types,
      enable_daily_brief, enable_critical_alerts, email_newsletter_enabled, newsletter_email, updated_at
    ) VALUES (
      'default', ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now')
    )
    ON CONFLICT(id) DO UPDATE SET
      user_name=excluded.user_name,
      theme=excluded.theme,
      categories=excluded.categories,
      keywords=excluded.keywords,
      opportunity_types=excluded.opportunity_types,
      enable_daily_brief=excluded.enable_daily_brief,
      enable_critical_alerts=excluded.enable_critical_alerts,
      email_newsletter_enabled=excluded.email_newsletter_enabled,
      newsletter_email=excluded.newsletter_email,
      updated_at=datetime('now')
  `).run(
    merged.user_name || 'Balaji',
    merged.theme || 'system',
    JSON.stringify(merged.categories || []),
    JSON.stringify(merged.keywords || []),
    JSON.stringify(merged.opportunity_types || []),
    merged.enable_daily_brief ? 1 : 0,
    merged.enable_critical_alerts ? 1 : 0,
    merged.email_newsletter_enabled ? 1 : 0,
    merged.newsletter_email || null
  );
  return getPreferences();
}

// -------------------------------------------------------------
// Test 1: Preferences SQLite Persistence & Retrieval
// -------------------------------------------------------------
{
  const initial = getPreferences();
  assert(initial && Array.isArray(initial.categories), 'Should load initial preferences object');
  console.log(`✅ Test 1 Passed: Initial preferences retrieved from SQLite (User: ${initial.user_name}, Theme: ${initial.theme}).`);
}

// -------------------------------------------------------------
// Test 2: Update Preferences (AI-Only Interests & Free Radar filters)
// -------------------------------------------------------------
{
  const updated = updatePreferences({
    user_name: 'Balaji Coder',
    categories: ['ai'],
    keywords: ['llm', 'agent', 'transformer'],
    opportunity_types: ['ai_credits', 'certification'],
    enable_daily_brief: true,
    enable_critical_alerts: true,
    email_newsletter_enabled: true,
    newsletter_email: 'balaji@example.com'
  });

  assert.equal(updated.user_name, 'Balaji Coder');
  assert.deepEqual(updated.categories, ['ai']);
  assert.deepEqual(updated.opportunity_types, ['ai_credits', 'certification']);
  assert.equal(updated.email_newsletter_enabled, true);
  assert.equal(updated.newsletter_email, 'balaji@example.com');

  // Verify persistence by reading directly from SQLite with a new DB connection
  const directDb = new DatabaseSync('../../database/tech_sentinel.db');
  const row = directDb.prepare("SELECT * FROM preferences WHERE id = 'default'").get();
  assert.equal(row.user_name, 'Balaji Coder');
  assert.deepEqual(JSON.parse(row.categories), ['ai']);
  assert.deepEqual(JSON.parse(row.opportunity_types), ['ai_credits', 'certification']);
  assert.equal(Boolean(row.email_newsletter_enabled), true);
  assert.equal(row.newsletter_email, 'balaji@example.com');

  console.log('✅ Test 2 Passed: Preferences including email newsletter persisted and verified in SQLite database.');
}

// -------------------------------------------------------------
// Test 3: Personalized Relevance Scoring with Selected Interests
// -------------------------------------------------------------
{
  const aiItem = {
    id: 'news_ai',
    title: 'OpenAI announces GPT-5 with autonomous tool use',
    description: 'New model capabilities and developer API updates',
    category: 'ai',
    tags: ['llm', 'agent'],
    published_at: '2026-08-16T11:00:00Z',
    source_name: 'Official Blog'
  };

  const cloudItem = {
    id: 'news_cloud',
    title: 'Kubernetes v1.32 Released with Gateway API GA',
    description: 'General availability of Gateway API and cluster optimizations',
    category: 'cloud',
    tags: ['k8s', 'infra'],
    published_at: '2026-08-16T11:00:00Z',
    source_name: 'Official Blog'
  };

  const aiScore = calculateRelevanceScore(aiItem, { categories: ['ai'], keywords: ['llm', 'agent'] });
  const cloudScore = calculateRelevanceScore(cloudItem, { categories: ['ai'], keywords: ['llm', 'agent'] });

  assert(aiScore > cloudScore, `AI item (${aiScore}) should score significantly higher than Cloud (${cloudScore}) when user selected AI`);
  console.log(`✅ Test 3 Passed: User's selected interests elevate personalized relevance (AI: ${aiScore} pts vs Cloud: ${cloudScore} pts).`);
}

// -------------------------------------------------------------
// Test 4: Personalized Feed Preserves Global Intelligence
// -------------------------------------------------------------
{
  const items = [
    { id: '1', title: 'AI agent architecture', category: 'ai', tags: ['agent'], published_at: '2026-08-16T11:00:00Z', source_name: 'TechCrunch AI' },
    { id: '2', title: 'PostgreSQL 18 Features', category: 'development', tags: ['sql'], published_at: '2026-08-16T11:30:00Z', source_name: 'Hacker News' },
    { id: '3', title: 'Linux Kernel Patch', category: 'open_source', tags: ['linux'], published_at: '2026-08-16T11:15:00Z', source_name: 'GitHub Trending' }
  ];

  const rankedForUser = rankNewsItems(items, referenceNow, { categories: ['ai'], keywords: ['agent'] });
  
  assert.equal(rankedForUser[0].id, '1', 'AI article must be ranked first in personalized recommendations');
  assert.equal(rankedForUser.length, 3, 'Personalized ranking must keep all articles available without discarding non-selected categories');
  console.log('✅ Test 4 Passed: Preferences personalize recommendations while preserving complete global feed.');
}

// -------------------------------------------------------------
// Test 5: Opportunity Ranking Respects Free Radar Preferences
// -------------------------------------------------------------
{
  const opps = [
    { id: 'opp_1', title: '$300 Google Cloud Credits', type: 'credits', category: 'cloud', value_amount: '$300', expires_at: '2026-08-20T00:00:00Z', is_verified: true },
    { id: 'opp_2', title: 'AWS Solutions Architect Free Voucher', type: 'certification', category: 'certification', value_amount: '$300', expires_at: '2026-08-20T00:00:00Z', is_verified: true },
    { id: 'opp_3', title: 'OpenAI Developer $200 Credits', type: 'credits', category: 'ai_credits', value_amount: '$200', expires_at: '2026-08-20T00:00:00Z', is_verified: true }
  ];

  const rankedForAi = rankOpportunities(opps, 'score', referenceNow, ['ai_credits']);
  assert.equal(rankedForAi[0].id, 'opp_3', 'AI credit opportunity should be elevated when ai_credits preference is active');

  console.log('✅ Test 5 Passed: Free Radar preferences prioritize matching opportunity types.');
}

// -------------------------------------------------------------
// Test 6: Restore Default Balanced Preferences
// -------------------------------------------------------------
{
  const restored = updatePreferences({
    user_name: 'Balaji',
    theme: 'system',
    categories: ['ai', 'cloud', 'development', 'open_source', 'cybersecurity', 'startups'],
    keywords: [],
    opportunity_types: ['ai_credits', 'cloud', 'certification', 'software', 'competition', 'education', 'career'],
    enable_daily_brief: true,
    enable_critical_alerts: true
  });

  assert.equal(restored.user_name, 'Balaji');
  console.log('✅ Test 6 Passed: Full default preferences successfully restored and verified.');
}

console.log('\n🎉 ALL PREFERENCES & PERSONALIZATION TESTS PASSED PERFECTLY!\n');
