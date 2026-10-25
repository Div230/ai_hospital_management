/** Real standalone Next.js proxy, with a synthetic echo server instead of Django.
 * Build first: API_INTERNAL_URL=http://127.0.0.1:18080 npm run build
 * No production database, credentials, or patient records are used.
 */
import assert from 'node:assert/strict';
import { before, after, test } from 'node:test';
import { createServer } from 'node:http';
import { createHash } from 'node:crypto';
import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { setTimeout as delay } from 'node:timers/promises';

const upstreamPort = 18080;
const frontendPort = 18081;
const base = `http://127.0.0.1:${frontendPort}`;
const digest = (body) => createHash('sha256').update(body).digest('hex');
let child;
let server;
let output = '';

before(async () => {
  assert.ok(existsSync('.next/standalone/server.js'), 'Build Next.js for the synthetic proxy test endpoint first.');
  server = createServer(async (req, res) => {
    const chunks = [];
    for await (const chunk of req) chunks.push(chunk);
    const body = Buffer.concat(chunks);
    const url = new URL(req.url, `http://127.0.0.1:${upstreamPort}`);
    res.statusCode = Number(url.searchParams.get('return_status') || 200);
    res.setHeader('Content-Type', 'application/json');
    if (url.pathname.startsWith('/api/auth/')) res.setHeader('Set-Cookie', [
      'aihms_refresh=synthetic-refresh; HttpOnly; Path=/api/auth/; SameSite=Lax',
      'aihms_csrf=synthetic-csrf; Path=/; SameSite=Lax',
    ]);
    res.end(JSON.stringify({ method: req.method, pathname: url.pathname, query: [...url.searchParams],
      bodyHash: digest(body), contentType: req.headers['content-type'], csrf: req.headers['x-csrftoken'],
      authorization: req.headers.authorization, cookie: req.headers.cookie }));
  });
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(upstreamPort, '127.0.0.1', resolve); });
  child = spawn(process.execPath, ['.next/standalone/server.js'], {
    env: { ...process.env, PORT: String(frontendPort), HOSTNAME: '127.0.0.1', NODE_ENV: 'production' },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  for (const stream of [child.stdout, child.stderr]) stream.on('data', (chunk) => { output = (output + chunk).slice(-12000); });
  for (let i = 0; i < 100; i++) {
    if (child.exitCode !== null) throw new Error(`Next.js stopped: ${output}`);
    try {
      const response = await fetch(`${base}/api/core/health/`, { redirect: 'manual', signal: AbortSignal.timeout(1000) });
      if (response.status === 200) return;
    } catch { /* wait for the owned test server to become ready */ }
    await delay(100);
  }
  throw new Error(`Next.js did not become ready: ${output}`);
}, { timeout: 20000 });

after(async () => {
  if (child && child.exitCode === null) {
    const closed = new Promise((resolve) => child.once('close', resolve));
    child.kill('SIGTERM');
    await Promise.race([closed, delay(3000)]);
    if (child.exitCode === null) child.kill('SIGKILL');
  }
  if (server) { server.closeAllConnections(); await new Promise((resolve) => server.close(resolve)); }
});

const cases = [
  ['POST', '/api/auth/register'], ['POST', '/api/auth/token'], ['POST', '/api/auth/token/refresh'],
  ['POST', '/api/auth/logout'], ['POST', '/api/appointments/book'],
  ['POST', '/api/appointments/fixture/reschedule'], ['POST', '/api/prescription-reader/fixture/correction'],
  ['POST', '/api/hospital-admin/departments'], ['PATCH', '/api/auth/me'],
  ['PATCH', '/api/hospital-admin/doctors/fixture/status'], ['PATCH', '/api/pharmacy/orders/fixture'],
  ['DELETE', '/api/notifications/push/subscribe'], ['PUT', '/api/pharmacy/medicines/fixture'],
];
for (const [method, path] of cases) for (const suffix of ['', '/']) {
  test(`${method} ${path}${suffix} preserves method, body and query without redirect`, async () => {
    const body = JSON.stringify({ fixture: 'synthetic', text: 'Unicode Δ / dosage ?' });
    const response = await fetch(base + path + suffix + '?page=2&search=synthetic+patient', {
      method, body, redirect: 'manual', headers: { 'Content-Type': 'application/json' },
    });
    assert.equal(response.status, 200, output);
    assert.equal(response.headers.get('location'), null);
    const data = await response.json();
    assert.equal(data.method, method);
    assert.equal(data.pathname, path + '/');
    assert.equal(data.bodyHash, digest(body));
    assert.deepEqual(data.query, [['page', '2'], ['search', 'synthetic patient']]);
  });
}
for (const path of ['/api/prescription-reader/', '/api/patients/medical-reports/', '/api/laboratory/test-requests/fixture/upload-report/']) {
  test(`multipart upload stays intact: ${path}`, async () => {
    const boundary = 'aihms-synthetic-boundary';
    const body = Buffer.concat([Buffer.from(`--${boundary}\r\nContent-Disposition: form-data; name="file"; filename="synthetic.png"\r\nContent-Type: image/png\r\n\r\n`),
      Buffer.from([0, 255, 1, 128, 45, 10]), Buffer.from(`\r\n--${boundary}--\r\n`)]);
    const response = await fetch(base + path, { method: 'POST', body, redirect: 'manual',
      headers: { 'Content-Type': `multipart/form-data; boundary=${boundary}` } });
    assert.equal(response.status, 200);
    const data = await response.json();
    assert.equal(data.pathname, path);
    assert.equal(data.bodyHash, digest(body));
    assert.equal(data.contentType, `multipart/form-data; boundary=${boundary}`);
  });
}
test('cookie refresh preserves CSRF/auth headers and both Set-Cookie values', async () => {
  const response = await fetch(base + '/api/auth/token/refresh/', { method: 'POST', body: '{}', redirect: 'manual', headers: {
    'Content-Type': 'application/json', Cookie: 'aihms_refresh=synthetic-refresh',
    'X-CSRFToken': 'synthetic-csrf', Authorization: 'Bearer synthetic-access',
  } });
  assert.equal(response.status, 200);
  const data = await response.json();
  assert.equal(data.csrf, 'synthetic-csrf');
  assert.equal(data.cookie, 'aihms_refresh=synthetic-refresh');
  assert.equal(data.authorization, 'Bearer synthetic-access');
  assert.equal(response.headers.getSetCookie().length, 2);
});
test('signed document queries survive proxy normalization', async () => {
  const response = await fetch(base + '/api/documents/prescription-upload/fixture/?t=synthetic%2Btoken%2F%3D', { redirect: 'manual' });
  assert.equal(response.status, 200);
  const data = await response.json();
  assert.equal(data.pathname, '/api/documents/prescription-upload/fixture/');
  assert.deepEqual(data.query, [['t', 'synthetic+token/=']]);
});
test('backend validation and unavailable statuses remain unchanged', async () => {
  for (const status of [400, 401, 403, 409, 503]) {
    const response = await fetch(base + '/api/prescription-reader/?return_status=' + status, { redirect: 'manual' });
    assert.equal(response.status, status);
  }
});
