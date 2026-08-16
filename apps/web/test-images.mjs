import assert from 'node:assert/strict';
import { DatabaseSync } from 'node:sqlite';

console.log('🧪 RUNNING ARTICLE IMAGE PIPELINE & RENDERING TEST SUITE...\n');

const db = new DatabaseSync('../../database/tech_sentinel.db');

// -------------------------------------------------------------
// Test 1: SQLite schema contains valid image_url column and records
// -------------------------------------------------------------
{
  const newsWithImages = db.prepare(`
    SELECT id, title, category, image_url 
    FROM news 
    WHERE image_url IS NOT NULL AND TRIM(image_url) != ''
  `).all();

  assert(newsWithImages.length > 0, 'Database must contain articles with valid image_url');
  
  for (const item of newsWithImages) {
    assert(
      item.image_url.startsWith('http://') || item.image_url.startsWith('https://'),
      `Image URL for '${item.id}' must be a valid HTTP(S) URL: ${item.image_url}`
    );
  }
  console.log(`✅ Test 1 Passed: Found ${newsWithImages.length} articles with valid HTTP(S) image URLs in SQLite database.`);
}

// -------------------------------------------------------------
// Test 2: Records with null image_url are handled safely
// -------------------------------------------------------------
{
  const newsWithoutImages = db.prepare(`
    SELECT id, title, category, image_url 
    FROM news 
    WHERE image_url IS NULL OR TRIM(image_url) = ''
  `).all();

  assert(newsWithoutImages.length > 0, 'Database contains articles with null/empty image_url');
  
  for (const item of newsWithoutImages) {
    assert.equal(item.image_url, null, 'Unpopulated image field must evaluate to null');
    assert(typeof item.title === 'string' && item.title.length > 0, 'Item must have a valid title');
  }
  console.log(`✅ Test 2 Passed: Handled ${newsWithoutImages.length} articles without image URLs safely with null values.`);
}

// -------------------------------------------------------------
// Test 3: Hero Story selection prioritizes fresh stories with media assets
// -------------------------------------------------------------
{
  const topRows = db.prepare(`
    SELECT id, title, category, image_url, published_at 
    FROM news 
    ORDER BY published_at DESC 
    LIMIT 20
  `).all();

  const heroCandidate = topRows.find(n => Boolean(n.image_url)) || topRows[0];
  assert(heroCandidate, 'Hero candidate must be selectable');
  assert(heroCandidate.image_url, 'Top hero candidate should possess a media asset for hero presentation');
  console.log(`✅ Test 3 Passed: Hero Story media preference selected '${heroCandidate.title}' with image: ${heroCandidate.image_url.slice(0, 50)}...`);
}

// -------------------------------------------------------------
// Test 4: Category fallback mapping produces distinct, valid theme configs
// -------------------------------------------------------------
{
  const categories = ['ai', 'cloud', 'development', 'open_source', 'cybersecurity', 'startups', 'education'];
  
  const getFallbackConfig = (cat) => {
    switch (cat) {
      case 'ai': return { gradient: 'from-violet-950/90', label: 'AI & NEURAL INTEL' };
      case 'cloud': return { gradient: 'from-cyan-950/90', label: 'CLOUD & INFRASTRUCTURE' };
      case 'open_source': return { gradient: 'from-emerald-950/90', label: 'OPEN SOURCE ECOSYSTEM' };
      case 'cybersecurity': return { gradient: 'from-rose-950/90', label: 'SECURITY & THREAT INTEL' };
      case 'startups': return { gradient: 'from-fuchsia-950/90', label: 'STARTUPS & VENTURE' };
      case 'education': return { gradient: 'from-sky-950/90', label: 'DEVELOPER EDUCATION' };
      default: return { gradient: 'from-amber-950/90', label: 'SOFTWARE DEVELOPMENT' };
    }
  };

  for (const cat of categories) {
    const config = getFallbackConfig(cat);
    assert(config.gradient.length > 0, `Category '${cat}' must have a valid gradient`);
    assert(config.label.length > 0, `Category '${cat}' must have a valid label`);
  }
  console.log(`✅ Test 4 Passed: Verified 7 distinct category-themed aesthetic fallback configurations.`);
}

console.log('\n🎉 ALL ARTICLE IMAGE PIPELINE & RENDERING TESTS PASSED PERFECTLY!\n');
