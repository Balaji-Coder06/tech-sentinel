import assert from 'node:assert/strict';

console.log('🧪 RUNNING CLOUDFLARE D1 PREFERENCES PERSISTENCE TEST...\n');

const D1_API_URL = 'https://tech-sentinel-api.sbalaji06.workers.dev';

async function testD1PreferencesLifecycle() {
  // 1. Initial GET - Ensure default profile is loaded
  const initialRes = await fetch(`${D1_API_URL}/api/preferences`);
  assert.equal(initialRes.status, 200, 'GET /api/preferences should return 200');
  const initialJson = await initialRes.json();
  assert(initialJson.success, 'Response should indicate success');
  console.log('✅ Step 1 Passed: Retrieved initial preferences from Cloudflare D1.');

  // 2. Opt-in with custom email and save
  const testEmail = 'subscriber.verified@company.dev';
  const savePayload = {
    ...initialJson.data,
    email_newsletter_enabled: true,
    newsletter_email: testEmail
  };

  const saveRes = await fetch(`${D1_API_URL}/api/preferences`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(savePayload)
  });
  assert.equal(saveRes.status, 200, 'POST /api/preferences should return 200');
  const savedJson = await saveRes.json();
  assert.equal(savedJson.data.email_newsletter_enabled, true, 'email_newsletter_enabled should be true');
  assert.equal(savedJson.data.newsletter_email, testEmail, 'newsletter_email should match');
  console.log('✅ Step 2 Passed: Successfully persisted opt-in email to Cloudflare D1.');

  // 3. Simulating page navigation / refresh: GET /api/preferences
  const verifyRes = await fetch(`${D1_API_URL}/api/preferences`);
  const verifyJson = await verifyRes.json();
  assert.equal(verifyJson.data.email_newsletter_enabled, true, 'Survives navigation and re-queries true');
  assert.equal(verifyJson.data.newsletter_email, testEmail, 'Survives navigation and retains custom email');
  console.log('✅ Step 3 Passed: Verified preferences survive navigation/refresh from Cloudflare D1.');

  // 4. Verify /api/email/subscribers returns this opted-in subscriber
  // Note: /api/email/subscribers is a protected endpoint requiring ingestion secret or internal bearer
  // Let's test resetting preferences back to default clean opt-out state
  const resetPayload = {
    ...verifyJson.data,
    email_newsletter_enabled: false,
    newsletter_email: null
  };
  const resetRes = await fetch(`${D1_API_URL}/api/preferences`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(resetPayload)
  });
  const resetJson = await resetRes.json();
  assert.equal(resetJson.data.email_newsletter_enabled, false, 'email_newsletter_enabled should be reset to false');
  assert.equal(resetJson.data.newsletter_email, null, 'newsletter_email should be reset to null');
  console.log('✅ Step 4 Passed: Cleanly reset preferences to default opt-out state.');

  // 5. Final verification after reset
  const finalRes = await fetch(`${D1_API_URL}/api/preferences`);
  const finalJson = await finalRes.json();
  assert.equal(finalJson.data.email_newsletter_enabled, false);
  assert.equal(finalJson.data.newsletter_email, null);
  console.log('✅ Step 5 Passed: Verified default opt-out state is persisted.');

  console.log('\n🎉 ALL CLOUDFLARE D1 PREFERENCES PERSISTENCE TESTS PASSED PERFECTLY!\n');
}

testD1PreferencesLifecycle().catch((err) => {
  console.error('❌ Test failed:', err);
  process.exit(1);
});
