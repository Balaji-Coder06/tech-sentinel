import { DatabaseSync } from 'node:sqlite';

const db = new DatabaseSync('../../database/tech_sentinel.db');
const rows = db.prepare('SELECT id, source_name, title, category, image_url, published_at FROM news ORDER BY published_at DESC LIMIT 15').all();

console.log('=== TRACING LATEST INTELLIGENCE STREAM CARDS ===\n');
rows.forEach((r, idx) => {
  console.log(`[Card ${idx + 1}]`);
  console.log(`  ID: ${r.id}`);
  console.log(`  Title: ${r.title}`);
  console.log(`  Source: ${r.source_name}`);
  console.log(`  Category: ${r.category}`);
  console.log(`  Image URL: ${r.image_url ? r.image_url : '(None - will render SentinelImage category-themed graphic)'}`);
  console.log(`  Render Mode: ${r.image_url ? 'Actual Source Media' : 'Tech Sentinel Fallback Graphic (' + r.category + ')'}`);
  console.log('--------------------------------------------------');
});
