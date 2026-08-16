import assert from 'node:assert/strict';
import { DatabaseSync } from 'node:sqlite';

console.log('🧪 RUNNING PERSONALIZED FEED VS GLOBAL INTELLIGENCE STREAM TEST SUITE...\n');

const db = new DatabaseSync('../../database/tech_sentinel.db');

const CANONICAL_SYNONYMS = {
  'ai': 'ai',
  'artificial intelligence': 'ai',
  'artificial-intelligence': 'ai',
  'machine learning': 'ai',
  'ml': 'ai',
  'cloud': 'cloud',
  'cloud computing': 'cloud',
  'cloud-computing': 'cloud',
  'development': 'development',
  'software development': 'development',
  'software-dev': 'development',
  'open_source': 'open_source',
  'open source': 'open_source',
  'cybersecurity': 'cybersecurity',
  'startups': 'startups',
};

function normalizeCategory(cat) {
  if (!cat || typeof cat !== 'string') return 'development';
  const cleaned = cat.trim().toLowerCase();
  if (CANONICAL_SYNONYMS[cleaned]) return CANONICAL_SYNONYMS[cleaned];
  return cleaned.replace(/[^\w\s-]/g, '').trim().replace(/[\s-]+/g, '_') || 'development';
}

function getNews(category, allowedCategories) {
  let query = "SELECT * FROM news WHERE title NOT LIKE '%{{%' AND title NOT LIKE '%${%' AND title NOT LIKE '%$(%'";
  const params = [];

  const normalizedAllowed = (allowedCategories && allowedCategories.length > 0)
    ? allowedCategories.map(c => normalizeCategory(c))
    : undefined;

  if (category && category.toLowerCase() !== 'all') {
    query += ' AND category = ?';
    params.push(normalizeCategory(category));
  } else if (normalizedAllowed && normalizedAllowed.length > 0) {
    const placeholders = normalizedAllowed.map(() => '?').join(',');
    query += ` AND category IN (${placeholders})`;
    params.push(...normalizedAllowed);
  }

  query += ' ORDER BY published_at DESC LIMIT 80';
  return db.prepare(query).all(...params);
}

// -------------------------------------------------------------
// Test A: AI Selected -> AI articles appear in personalized feed
// -------------------------------------------------------------
{
  const userAllowed = ['ai', 'cloud', 'development'];
  const personalizedFeed = getNews('all', userAllowed);
  const aiArticles = personalizedFeed.filter(item => normalizeCategory(item.category) === 'ai');

  assert(aiArticles.length > 0, 'Personalized feed must contain AI articles when AI is enabled');
  console.log(`✅ Test A Passed: AI enabled -> Found ${aiArticles.length} AI articles in Personalized News Feed.`);
}

// -------------------------------------------------------------
// Test B: AI Deselected -> AI articles do NOT appear in personalized feed
// -------------------------------------------------------------
{
  const userAllowed = ['cloud', 'development', 'open_source', 'cybersecurity', 'startups'];
  const personalizedFeed = getNews('all', userAllowed);
  const aiArticles = personalizedFeed.filter(item => normalizeCategory(item.category) === 'ai');

  assert.equal(aiArticles.length, 0, 'Personalized feed must have 0 AI articles when AI is unchecked in preferences');
  console.log('✅ Test B Passed: AI deselected -> Exactly 0 AI articles in Personalized News Feed.');
}

// -------------------------------------------------------------
// Test C: AI Deselected -> Selected categories (Cloud, Dev, OSS) still appear
// -------------------------------------------------------------
{
  const userAllowed = ['cloud', 'development', 'open_source', 'cybersecurity', 'startups'];
  const personalizedFeed = getNews('all', userAllowed);

  const cloudCount = personalizedFeed.filter(item => normalizeCategory(item.category) === 'cloud').length;
  const devCount = personalizedFeed.filter(item => normalizeCategory(item.category) === 'development').length;
  const ossCount = personalizedFeed.filter(item => normalizeCategory(item.category) === 'open_source').length;

  assert(cloudCount > 0, 'Cloud articles must appear');
  assert(devCount > 0, 'Development articles must appear');
  assert(ossCount > 0, 'Open source articles must appear');

  console.log(`✅ Test C Passed: AI deselected -> Retained ${cloudCount} Cloud, ${devCount} Dev, and ${ossCount} OSS articles.`);
}

// -------------------------------------------------------------
// Test D: Global Intelligence Stream STILL contains AI articles
// -------------------------------------------------------------
{
  // Global stream is called without allowedCategories restriction
  const globalStream = getNews('all', undefined);
  const globalAiArticles = globalStream.filter(item => normalizeCategory(item.category) === 'ai');

  assert(globalAiArticles.length > 0, 'Global Intelligence Stream must continue showing ALL categories including AI');
  console.log(`✅ Test D Passed: Global Intelligence Stream contains ${globalAiArticles.length} AI articles (bypasses preference filter).`);
}

// -------------------------------------------------------------
// Test E: Changing preferences persists in SQLite
// -------------------------------------------------------------
{
  // 1. Update preferences without AI
  db.prepare(`
    UPDATE preferences 
    SET categories = ? 
    WHERE id = 'default'
  `).run(JSON.stringify(['cloud', 'development', 'open_source']));

  // 2. Read back from a fresh query
  const row = db.prepare("SELECT categories FROM preferences WHERE id = 'default'").get();
  const savedCategories = JSON.parse(row.categories);
  assert(!savedCategories.includes('ai'), 'Preferences must persist without AI');

  // 3. Restore balanced default preferences
  db.prepare(`
    UPDATE preferences 
    SET categories = ? 
    WHERE id = 'default'
  `).run(JSON.stringify(['ai', 'cloud', 'development', 'open_source', 'cybersecurity', 'startups']));

  console.log('✅ Test E Passed: Preference updates persist cleanly in SQLite database across reloads.');
}

// -------------------------------------------------------------
// Test F: Canonical aliases work seamlessly
// -------------------------------------------------------------
{
  const aliases = ['Artificial Intelligence', 'AI', 'machine learning', 'ML', 'artificial-intelligence'];
  for (const alias of aliases) {
    assert.equal(normalizeCategory(alias), 'ai', `Alias '${alias}' must normalize to 'ai'`);
  }
  console.log('✅ Test F Passed: All canonical aliases ("Artificial Intelligence", "AI", "machine learning") resolve to "ai".');
}

console.log('\n🎉 ALL PERSONALIZED FEED & GLOBAL STREAM TESTS PASSED PERFECTLY!\n');
