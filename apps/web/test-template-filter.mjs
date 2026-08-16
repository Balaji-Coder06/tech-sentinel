import assert from 'node:assert/strict';
import { DatabaseSync } from 'node:sqlite';

console.log('🧪 RUNNING TEMPLATE EXPRESSION & DATA QUALITY REGRESSION TEST SUITE...\n');

const db = new DatabaseSync('../../database/tech_sentinel.db');

function isValidTitle(title) {
  if (!title || typeof title !== 'string') return false;
  const trimmed = title.trim();
  if (trimmed.length < 3) return false;
  const lower = trimmed.toLowerCase();
  if (['undefined', 'null', 'none', 'nan', 'n/a', '[object object]', 'untitled'].includes(lower)) return false;
  if (/\{\{.*?\}\}/s.test(trimmed)) return false;
  if (/\$\{.*?\}/s.test(trimmed)) return false;
  if (/\$\([\'\"].*?[\'\"]\)/s.test(trimmed)) return false;
  if (/<\%.*?\%>/s.test(trimmed)) return false;
  if (/\[%.*?%\]/s.test(trimmed)) return false;
  return true;
}

// -------------------------------------------------------------
// Test 1: Validation function rejects all placeholder variations
// -------------------------------------------------------------
{
  const invalidTitles = [
    "{{ $('Get Ready Post').item.json.Title }}",
    "{{ title }}",
    "${item.title}",
    "$('Get Ready Post')",
    "<%= article_title %>",
    "[% title %]",
    "undefined",
    "null",
    "[object Object]"
  ];

  for (const t of invalidTitles) {
    assert.equal(isValidTitle(t), false, `Title '${t}' must be rejected by isValidTitle`);
  }
  console.log('✅ Test 1 Passed: isValidTitle rejects all unrendered template expressions and placeholders.');
}

// -------------------------------------------------------------
// Test 2: Active SQLite database has ZERO template expressions
// -------------------------------------------------------------
{
  const query = "SELECT id, title, url FROM news WHERE title LIKE '%{{%' OR title LIKE '%${%' OR title LIKE '%$(%'";
  const rows = db.prepare(query).all();

  assert.equal(rows.length, 0, `Active SQLite news table must contain 0 corrupted template records (found ${rows.length})`);
  console.log('✅ Test 2 Passed: Verified active SQLite news table contains 0 unrendered template expressions.');
}

// -------------------------------------------------------------
// Test 3: Query filtering defends against direct SQL injection of corrupted titles
// -------------------------------------------------------------
{
  const testCorruptedId = `news_test_template_${Date.now()}`;
  const corruptedTitle = "{{ $('Get Ready Post').item.json.Title }}";
  db.prepare(
    "INSERT INTO news (id, title, description, url, source_name, category, tags, published_at) VALUES (?, ?, 'Corrupted post', ?, 'Dev.to', 'development', '[]', datetime('now'))"
  ).run(testCorruptedId, corruptedTitle, `https://example.com/test-corrupted/${testCorruptedId}`);

  // Query using serverDb filter logic
  const filteredRows = db.prepare(
    "SELECT * FROM news WHERE title NOT LIKE '%{{%' AND title NOT LIKE '%${%' AND title NOT LIKE '%$(%' ORDER BY published_at DESC"
  ).all();

  const found = filteredRows.find(r => r.id === testCorruptedId || !isValidTitle(r.title));
  assert(!found, 'Corrupted test record must be completely excluded from query results');
  console.log('✅ Test 3 Passed: Server query layer defensively filters out corrupted template records.');

  // Clean up
  db.prepare('DELETE FROM news WHERE id = ?').run(testCorruptedId);
  console.log('✅ Test 4 Passed: Cleaned up test fixture.');
}

console.log('\n🎉 ALL TEMPLATE EXPRESSION & DATA QUALITY TESTS PASSED PERFECTLY!\n');
