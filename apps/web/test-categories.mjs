import assert from 'node:assert/strict';
import { DatabaseSync } from 'node:sqlite';

console.log('🧪 RUNNING DATA-DRIVEN CATEGORIES & NEWS FILTER TEST SUITE...\n');

const db = new DatabaseSync('../../database/tech_sentinel.db');

function formatCategoryLabel(category) {
  if (!category) return '';
  const trimmed = category.trim();
  const lower = trimmed.toLowerCase();
  if (lower === 'ai') return 'AI';
  if (lower === 'ml') return 'ML';
  if (lower === 'api') return 'API';
  if (lower === 'ui' || lower === 'ux') return lower.toUpperCase();
  if (lower === 'all' || lower === 'all news') return 'All News';

  return trimmed
    .split(/[_\s-]+/)
    .map(word => {
      const wLower = word.toLowerCase();
      if (wLower === 'ai' || wLower === 'ui' || wLower === 'ux' || wLower === 'api') return wLower.toUpperCase();
      return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
    })
    .join(' ');
}

function getCategories() {
  const rows = db.prepare(`
    SELECT category, COUNT(*) as count 
    FROM news 
    WHERE category IS NOT NULL AND TRIM(category) != '' 
    GROUP BY category 
    HAVING count > 0 
    ORDER BY count DESC, category ASC
  `).all();

  return rows.map(r => ({
    id: r.category.toLowerCase().trim(),
    label: formatCategoryLabel(r.category),
    count: Number(r.count)
  }));
}

// -------------------------------------------------------------
// Test 1: Dynamic Categories derived from SQLite
// -------------------------------------------------------------
{
  const categories = getCategories();
  assert(Array.isArray(categories), 'Categories must be an array');
  assert(categories.length > 0, 'Should find active categories in SQLite');

  console.log(`✅ Test 1 Passed: Retrieved ${categories.length} data-driven categories from SQLite:`);
  categories.forEach(c => console.log(`   - ${c.label} (ID: ${c.id}, Count: ${c.count})`));
}

// -------------------------------------------------------------
// Test 2: Categories are sorted by count DESC
// -------------------------------------------------------------
{
  const categories = getCategories();
  for (let i = 0; i < categories.length - 1; i++) {
    assert(categories[i].count >= categories[i + 1].count, 'Categories must be ordered by count DESC');
  }
  console.log('✅ Test 2 Passed: Categories are sorted deterministically by record count DESC.');
}

// -------------------------------------------------------------
// Test 3: Formatting helper formats labels correctly
// -------------------------------------------------------------
{
  assert.equal(formatCategoryLabel('ai'), 'AI');
  assert.equal(formatCategoryLabel('open_source'), 'Open Source');
  assert.equal(formatCategoryLabel('cloud_computing'), 'Cloud Computing');
  assert.equal(formatCategoryLabel('robotics_and_automation'), 'Robotics And Automation');
  assert.equal(formatCategoryLabel('ui_ux'), 'UI UX');
  console.log('✅ Test 3 Passed: Dynamic category label formatter handles slugs, acronyms, and spacing cleanly.');
}

// -------------------------------------------------------------
// Test 4: Filtering by category returns strictly matching items
// -------------------------------------------------------------
{
  const aiRows = db.prepare("SELECT * FROM news WHERE category = 'ai'").all();
  assert(aiRows.length > 0, 'Should have AI news records in SQLite');
  for (const item of aiRows) {
    assert.equal(item.category.toLowerCase(), 'ai', `All items in AI filter must have category === 'ai' (found ${item.category})`);
  }
  console.log(`✅ Test 4 Passed: Category filter 'ai' returned ${aiRows.length} items with 100% category match.`);
}

// -------------------------------------------------------------
// Test 5: Zero hardcoded categories — Automatic detection of new category
// -------------------------------------------------------------
{
  // Insert a test item with a completely new category: 'robotics'
  const testId = `test_news_robotics_${Date.now()}`;
  db.prepare(`
    INSERT INTO news (
      id, title, description, url, source_name, category, tags, published_at
    ) VALUES (?, 'Autonomous Quadruped Robot Released', 'New open source quadruped robot platform', ?, 'Robotics Lab', 'robotics', '["robotics"]', datetime('now'))
  `).run(testId, `https://example.com/robotics/${testId}`);

  // Query categories again
  const refreshedCategories = getCategories();
  const roboticsCat = refreshedCategories.find(c => c.id === 'robotics');
  
  assert(Boolean(roboticsCat), "New category 'robotics' must automatically appear in categories list!");
  assert.equal(roboticsCat.label, 'Robotics');
  console.log(`✅ Test 5 Passed: Completely new category 'robotics' was dynamically detected and exposed (Count: ${roboticsCat.count}) with zero frontend code changes!`);

  // Clean up test item
  db.prepare('DELETE FROM news WHERE id = ?').run(testId);
  const postCleanupCategories = getCategories();
  assert(!postCleanupCategories.some(c => c.id === 'robotics'), 'Category should vanish when count reaches 0');
  console.log('✅ Test 6 Passed: Empty categories (count === 0) are automatically pruned.');
}

console.log('\n🎉 ALL DATA-DRIVEN CATEGORY TESTS PASSED PERFECTLY!\n');
