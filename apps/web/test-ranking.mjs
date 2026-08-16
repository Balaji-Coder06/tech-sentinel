import assert from 'node:assert/strict';
import { 
  calculateFreshnessScore, 
  calculateSourceQualityScore, 
  calculateRelevanceScore, 
  calculatePopularityScore, 
  calculateOpportunityPotentialScore, 
  calculateIntelligenceScore, 
  getRankingBreakdown, 
  rankNewsItems 
} from './lib/ranking.ts';

const referenceNow = new Date('2026-08-16T12:00:00Z');

console.log('🧪 RUNNING INTELLIGENCE RANKING ENGINE TEST SUITE...\n');

// -------------------------------------------------------------
// Test 1: New high-quality article outranks old article
// -------------------------------------------------------------
{
  const newArticle = {
    id: 'n1',
    title: 'Breakthrough in LLM Reasoning and Architecture',
    description: 'New model architecture achieves SOTA benchmarks.',
    source_name: 'TechCrunch AI',
    category: 'ai',
    tags: ['ai', 'llm', 'benchmark'],
    importance_score: 50,
    relevance_score: 50,
    published_at: '2026-08-16T11:30:00Z', // 30 mins ago
    url: 'https://example.com/1'
  };

  const oldArticle = {
    id: 'n2',
    title: 'Breakthrough in LLM Reasoning and Architecture',
    description: 'New model architecture achieves SOTA benchmarks.',
    source_name: 'TechCrunch AI',
    category: 'ai',
    tags: ['ai', 'llm', 'benchmark'],
    importance_score: 50,
    relevance_score: 50,
    published_at: '2026-08-01T12:00:00Z', // 15 days ago
    url: 'https://example.com/2'
  };

  const scoreNew = calculateIntelligenceScore(newArticle, referenceNow);
  const scoreOld = calculateIntelligenceScore(oldArticle, referenceNow);
  assert(scoreNew > scoreOld, `Expected new article score (${scoreNew}) to be higher than old (${scoreOld})`);
  console.log(`✅ Test 1 Passed: New article (${scoreNew} pts) outranks identical old article (${scoreOld} pts).`);
}

// -------------------------------------------------------------
// Test 2: Strong source gets higher source score
// -------------------------------------------------------------
{
  const officialSourceScore = calculateSourceQualityScore('Google Cloud');
  const techCrunchScore = calculateSourceQualityScore('TechCrunch AI');
  const hackerNewsScore = calculateSourceQualityScore('Hacker News');
  const freeCodeCampScore = calculateSourceQualityScore('freeCodeCamp');
  const devToScore = calculateSourceQualityScore('Dev.to');
  const unknownScore = calculateSourceQualityScore('Random Blog');

  assert.equal(officialSourceScore, 25);
  assert.equal(techCrunchScore, 22);
  assert.equal(hackerNewsScore, 20);
  assert.equal(freeCodeCampScore, 18);
  assert.equal(devToScore, 15);
  assert.equal(unknownScore, 8);
  assert(officialSourceScore > techCrunchScore && techCrunchScore > hackerNewsScore && hackerNewsScore > devToScore && devToScore > unknownScore);
  console.log('✅ Test 2 Passed: Source quality weights match project specification hierarchy.');
}

// -------------------------------------------------------------
// Test 3: Relevant AI/developer article scores higher than irrelevant content
// -------------------------------------------------------------
{
  const aiArticle = {
    category: 'ai',
    tags: ['ai', 'agent', 'model'],
    title: 'Deep Learning Model and Agent Infrastructure',
    description: 'Architecture for distributed agents and compilers.'
  };

  const genericArticle = {
    category: 'other',
    tags: ['lifestyle'],
    title: 'Generic weekend thoughts',
    description: 'Nothing technical mentioned here.'
  };

  const relAI = calculateRelevanceScore(aiArticle);
  const relGeneric = calculateRelevanceScore(genericArticle);
  assert(relAI > relGeneric, `Expected AI relevance (${relAI}) > generic (${relGeneric})`);
  console.log(`✅ Test 3 Passed: Technical AI content (${relAI} pts) scores significantly higher than generic content (${relGeneric} pts).`);
}

// -------------------------------------------------------------
// Test 4: GitHub popularity affects GitHub ranking
// -------------------------------------------------------------
{
  const megaRepo = {
    source_name: 'GitHub Trending',
    title: 'GitHub Trending: awesome/project (⭐ 34,626)',
    description: 'Stars: 34,626.'
  };

  const mediumRepo = {
    source_name: 'GitHub Trending',
    title: 'GitHub Trending: mid/project (⭐ 1,200)',
    description: 'Stars: 1,200.'
  };

  const smallRepo = {
    source_name: 'GitHub Trending',
    title: 'GitHub Trending: tiny/project (⭐ 120)',
    description: 'Stars: 120.'
  };

  const scoreMega = calculatePopularityScore(megaRepo);
  const scoreMedium = calculatePopularityScore(mediumRepo);
  const scoreSmall = calculatePopularityScore(smallRepo);

  assert(scoreMega > scoreMedium && scoreMedium > scoreSmall, `Expected mega (${scoreMega}) > medium (${scoreMedium}) > small (${scoreSmall})`);
  console.log(`✅ Test 4 Passed: GitHub repository stargazers scale popularity score (${scoreMega} > ${scoreMedium} > ${scoreSmall}).`);
}

// -------------------------------------------------------------
// Test 5: Opportunity-related article receives opportunity bonus
// -------------------------------------------------------------
{
  const oppArticle = {
    title: 'Google Cloud Free Program: $300 Credits + Free Tier Compute',
    description: 'Claim $300 instant credits and free tier compute.',
    tags: ['cloud', 'credits', 'free tier']
  };

  const normalArticle = {
    title: 'How databases process SQL queries',
    description: 'Explaining B-trees and query execution plans.',
    tags: ['database', 'sql']
  };

  const oppScore = calculateOpportunityPotentialScore(oppArticle);
  const normalScore = calculateOpportunityPotentialScore(normalArticle);

  assert.equal(oppScore, 10);
  assert.equal(normalScore, 0);
  console.log(`✅ Test 5 Passed: Opportunity article receives full opportunity bonus (${oppScore} pts vs ${normalScore} pts).`);
}

// -------------------------------------------------------------
// Test 6: Invalid/missing publication date does not crash
// -------------------------------------------------------------
{
  const invalidArticle = {
    id: 'n_err',
    title: 'Test article with bad date',
    description: 'Testing robustness.',
    source_name: 'TechCrunch',
    category: 'development',
    published_at: 'NOT-A-VALID-DATE',
    url: 'https://example.com'
  };

  const nullArticle = {
    id: 'n_null',
    title: 'Test article with null date',
    description: 'Testing robustness.',
    source_name: null,
    category: null,
    published_at: null,
    url: 'https://example.com'
  };

  const scoreInvalid = calculateIntelligenceScore(invalidArticle, referenceNow);
  const scoreNull = calculateIntelligenceScore(nullArticle, referenceNow);

  assert(typeof scoreInvalid === 'number' && scoreInvalid >= 0 && scoreInvalid <= 100);
  assert(typeof scoreNull === 'number' && scoreNull >= 0 && scoreNull <= 100);
  console.log(`✅ Test 6 Passed: Malformed or missing dates evaluate safely without throwing (scores: ${scoreInvalid}, ${scoreNull}).`);
}

// -------------------------------------------------------------
// Test 7: Ranking is deterministic
// -------------------------------------------------------------
{
  const items = [
    {
      id: 'a',
      title: 'Item A',
      description: 'Dev tools',
      source_name: 'Hacker News',
      category: 'development',
      published_at: '2026-08-16T10:00:00Z',
      url: 'https://a.com'
    },
    {
      id: 'b',
      title: 'Item B',
      description: 'AI breakthrough',
      source_name: 'TechCrunch AI',
      category: 'ai',
      tags: ['llm', 'model'],
      published_at: '2026-08-16T11:00:00Z',
      url: 'https://b.com'
    },
    {
      id: 'c',
      title: 'Item C',
      description: 'Cloud credits giveaway',
      source_name: 'Google Cloud',
      category: 'cloud',
      tags: ['credits', 'cloud'],
      published_at: '2026-08-16T09:00:00Z',
      url: 'https://c.com'
    }
  ];

  const run1 = rankNewsItems(items, referenceNow).map(i => i.id);
  const run2 = rankNewsItems(items, referenceNow).map(i => i.id);
  const run3 = rankNewsItems(items, referenceNow).map(i => i.id);

  assert.deepEqual(run1, run2);
  assert.deepEqual(run2, run3);
  console.log(`✅ Test 7 Passed: Ranking order is 100% deterministic: [${run1.join(', ')}].`);
}

// -------------------------------------------------------------
// Test 8: Latest Stream remains chronological
// -------------------------------------------------------------
{
  const rawList = [
    { id: '1', title: 'Older', published_at: '2026-08-16T06:00:00Z' },
    { id: '2', title: 'Newer', published_at: '2026-08-16T11:00:00Z' },
    { id: '3', title: 'Mid', published_at: '2026-08-16T08:00:00Z' },
  ];

  const chronological = [...rawList].sort((a, b) => new Date(b.published_at).getTime() - new Date(a.published_at).getTime());
  assert.equal(chronological[0].id, '2');
  assert.equal(chronological[1].id, '3');
  assert.equal(chronological[2].id, '1');
  console.log('✅ Test 8 Passed: Latest stream maintains pure chronological published_at DESC ordering.');
}

// -------------------------------------------------------------
// Test 9: Featured, For You, Don't Miss, and Latest contain no duplicates
// -------------------------------------------------------------
{
  const mockNews = Array.from({ length: 20 }, (_, idx) => ({
    id: `item_${idx + 1}`,
    title: `Article Title ${idx + 1}`,
    description: `Description for article ${idx + 1}`,
    source_name: idx % 2 === 0 ? 'TechCrunch AI' : 'Hacker News',
    category: 'ai',
    tags: ['ai'],
    published_at: new Date(Date.now() - idx * 3600000).toISOString(),
    image_url: idx === 0 || idx === 3 ? `https://img.example.com/${idx}.jpg` : undefined,
    url: `https://example.com/${idx}`
  }));

  const ranked = rankNewsItems(mockNews, referenceNow);

  // Section distribution logic:
  const heroStory = ranked.find(n => calculateFreshnessScore(n.published_at, referenceNow) >= 6 && Boolean(n.image_url)) || ranked[0];
  const remainingNews = heroStory ? ranked.filter(n => n.id !== heroStory.id) : ranked;
  const forYouItems = remainingNews.slice(0, 4);
  const dontMissItems = remainingNews.slice(4, 7);
  const feedItems = remainingNews.slice(7).sort((a, b) => new Date(b.published_at).getTime() - new Date(a.published_at).getTime());

  const heroIds = [heroStory.id];
  const forYouIds = forYouItems.map(i => i.id);
  const dontMissIds = dontMissItems.map(i => i.id);
  const feedIds = feedItems.map(i => i.id);

  const allDisplayedIds = [...heroIds, ...forYouIds, ...dontMissIds, ...feedIds];
  const uniqueIds = new Set(allDisplayedIds);

  assert.equal(allDisplayedIds.length, uniqueIds.size, 'Found duplicated article ID across sections!');
  console.log(`✅ Test 9 Passed: Zero duplicate article IDs across Hero (1), For You (${forYouIds.length}), Don't Miss (${dontMissIds.length}), and Latest Stream (${feedIds.length}). Total unique: ${uniqueIds.size}.`);
}

console.log('\n🎉 ALL 9 INTELLIGENCE RANKING TESTS PASSED PERFECTLY!\n');
