import assert from 'node:assert/strict';
import test from 'node:test';
import config from '../next.config.ts';

test('Django API requests bypass Next trailing-slash redirects', () => {
  assert.equal(config.skipTrailingSlashRedirect, true);
});
test('both slash forms proxy directly to Django slash-terminated routes', async () => {
  const rules = await config.rewrites();
  for (const source of ['/api/:path*/', '/api/:path*']) {
    const rule = rules.find((item) => item.source === source);
    assert.ok(rule, `Missing rewrite for ${source}`);
    assert.ok(rule.destination.endsWith('/api/:path*/'));
    assert.ok(!rule.destination.includes('//api/'));
  }
});
