import assert from 'node:assert/strict';
import { DatabaseSync } from 'node:sqlite';

console.log('🧪 RUNNING CATEGORY TAXONOMY & NORMALIZATION TEST SUITE...\n');

const db = new DatabaseSync('../../database/tech_sentinel.db');

const CANONICAL_SYNONYMS = {
  'ai': 'ai',
  'artificial intelligence': 'ai',
  'artificial-intelligence': 'ai',
  'artificial_intelligence': 'ai',
  'machine learning': 'ai',
  'machine-learning': 'ai',
  'machine_learning': 'ai',
  'ml': 'ai',
  'genai': 'ai',
  'generative ai': 'ai',
  'deep learning': 'ai',
  'deep-learning': 'ai',
  'deep_learning': 'ai',
  'llm': 'ai',
  'llms': 'ai',
  'cloud': 'cloud',
  'cloud computing': 'cloud',
  'cloud-computing': 'cloud',
  'cloud_computing': 'cloud',
  'cloud infrastructure': 'cloud',
  'cloud-infrastructure': 'cloud',
  'cloud_infrastructure': 'cloud',
  'devops': 'cloud',
  'serverless': 'cloud',
  'infrastructure': 'cloud',
  'cloud & infrastructure': 'cloud',
  'cloud-native': 'cloud',
  'development': 'development',
  'software development': 'development',
  'software-development': 'development',
  'software_development': 'development',
  'software dev': 'development',
  'software-dev': 'development',
  'software_dev': 'development',
  'programming': 'development',
  'software engineering': 'development',
  'coding': 'development',
  'web development': 'development',
  'webdev': 'development',
  'frontend': 'development',
  'backend': 'development',
  'fullstack': 'development',
  'developer tools': 'development',
  'devtools': 'development',
  'open_source': 'open_source',
  'open source': 'open_source',
  'open-source': 'open_source',
  'opensource': 'open_source',
  'oss': 'open_source',
  'foss': 'open_source',
  'free and open source': 'open_source',
  'cybersecurity': 'cybersecurity',
  'cyber security': 'cybersecurity',
  'cyber-security': 'cybersecurity',
  'cyber_security': 'cybersecurity',
  'security': 'cybersecurity',
  'infosec': 'cybersecurity',
  'appsec': 'cybersecurity',
  'startups': 'startups',
  'startup': 'startups',
  'start-ups': 'startups',
  'start_ups': 'startups',
  'start-up': 'startups',
  'start_up': 'startups',
  'venture': 'startups',
  'entrepreneurship': 'startups',
  'education': 'education',
  'learning': 'education',
  'student': 'education',
  'students': 'education',
  'training': 'education',
  'tutorial': 'education',
  'tutorials': 'education',
};

function normalizeCategory(category) {
  if (!category || typeof category !== 'string') return 'development';
  const cleaned = category.trim().toLowerCase();
  const cleanedSpaces = cleaned.replace(/[\s_-]+/g, ' ').trim();
  const cleanedUnderscores = cleaned.replace(/[\s_-]+/g, '_').trim();

  if (CANONICAL_SYNONYMS[cleaned]) return CANONICAL_SYNONYMS[cleaned];
  if (CANONICAL_SYNONYMS[cleanedSpaces]) return CANONICAL_SYNONYMS[cleanedSpaces];
  if (CANONICAL_SYNONYMS[cleanedUnderscores]) return CANONICAL_SYNONYMS[cleanedUnderscores];

  const slug = cleaned.replace(/[^\w\s-]/g, '').trim().replace(/[\s-]+/g, '_');
  return slug || 'development';
}

// -------------------------------------------------------------
// Test 1: Category synonyms normalize to canonical slugs
// -------------------------------------------------------------
{
  assert.equal(normalizeCategory('AI'), 'ai');
  assert.equal(normalizeCategory('Artificial Intelligence'), 'ai');
  assert.equal(normalizeCategory('artificial-intelligence'), 'ai');
  assert.equal(normalizeCategory('machine learning'), 'ai');
  assert.equal(normalizeCategory('ML'), 'ai');

  assert.equal(normalizeCategory('Cloud Computing'), 'cloud');
  assert.equal(normalizeCategory('cloud-computing'), 'cloud');
  assert.equal(normalizeCategory('Cloud Infrastructure'), 'cloud');
  assert.equal(normalizeCategory('DevOps'), 'cloud');

  assert.equal(normalizeCategory('Software Development'), 'development');
  assert.equal(normalizeCategory('software-dev'), 'development');
  assert.equal(normalizeCategory('Programming'), 'development');
  assert.equal(normalizeCategory('Developer Tools'), 'development');

  assert.equal(normalizeCategory('Open Source'), 'open_source');
  assert.equal(normalizeCategory('OSS'), 'open_source');
  assert.equal(normalizeCategory('FOSS'), 'open_source');

  assert.equal(normalizeCategory('Cybersecurity'), 'cybersecurity');
  assert.equal(normalizeCategory('Cyber Security'), 'cybersecurity');
  assert.equal(normalizeCategory('Security'), 'cybersecurity');

  assert.equal(normalizeCategory('Startups'), 'startups');
  assert.equal(normalizeCategory('start-up'), 'startups');

  console.log('✅ Test 1 Passed: Equivalent category variations successfully normalize to canonical taxonomy slugs.');
}

// -------------------------------------------------------------
// Test 2: Unrelated categories are never improperly merged
// -------------------------------------------------------------
{
  const distinct = ['ai', 'cloud', 'development', 'open_source', 'cybersecurity', 'startups', 'education'];
  const normalized = distinct.map(c => normalizeCategory(c));
  const uniqueNormalized = new Set(normalized);
  
  assert.equal(uniqueNormalized.size, distinct.length, 'All distinct taxonomy categories must remain distinct');
  console.log(`✅ Test 2 Passed: ${distinct.length} distinct technology domains remain strictly separate without over-normalization.`);
}

// -------------------------------------------------------------
// Test 3: Active SQLite database categories are 100% canonical
// -------------------------------------------------------------
{
  const rows = db.prepare(`
    SELECT DISTINCT category 
    FROM news 
    WHERE category IS NOT NULL AND TRIM(category) != ''
  `).all();

  for (const r of rows) {
    const norm = normalizeCategory(r.category);
    assert.equal(r.category, norm, `Category in DB '${r.category}' must already be canonical (expected '${norm}')`);
  }
  console.log(`✅ Test 3 Passed: Verified all ${rows.length} distinct categories in SQLite news records match canonical taxonomy: [${rows.map(r => r.category).join(', ')}].`);
}

// -------------------------------------------------------------
// Test 4: Query filtering works transparently with raw synonym inputs
// -------------------------------------------------------------
{
  // Searching with 'Artificial Intelligence' should query canonical 'ai' records
  const normInput = normalizeCategory('Artificial Intelligence');
  const aiRecords = db.prepare('SELECT * FROM news WHERE category = ?').all(normInput);
  assert(aiRecords.length > 0, "Querying with synonym 'Artificial Intelligence' must retrieve matching AI records");

  console.log(`✅ Test 4 Passed: Query filtering with synonym 'Artificial Intelligence' seamlessly retrieved ${aiRecords.length} canonical 'ai' records.`);
}

console.log('\n🎉 ALL CATEGORY TAXONOMY & NORMALIZATION TESTS PASSED PERFECTLY!\n');
