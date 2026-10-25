import assert from 'node:assert/strict';
import test from 'node:test';
import { withApiTrailingSlash } from '../src/lib/api-path.ts';

const routes = [
  '/auth/register', '/auth/token', '/auth/token/refresh', '/auth/logout',
  '/auth/me', '/auth/2fa/setup', '/auth/2fa/enable', '/auth/2fa/login-verify',
  '/appointments/book', '/appointments/fixture/cancel', '/appointments/fixture/reschedule',
  '/appointments/prescriptions', '/doctors/fixture/slots',
  '/hospital-admin/doctors/fixture/status', '/hospital-admin/departments',
  '/patients/medical-reports', '/laboratory/test-requests/fixture/upload-report',
  '/pharmacy/orders/fixture', '/notifications/push/subscribe',
  '/prescription-reader', '/prescription-reader/fixture/retry',
  '/prescription-reader/fixture/correction', '/prescription-reader/fixture/request-review',
  '/prescription-reader/fixture/review', '/prescription-reader/fixture/download',
];
for (const route of routes) {
  test(`canonical Django route: ${route}`, () => {
    assert.equal(withApiTrailingSlash(route), route + '/');
    assert.equal(withApiTrailingSlash(route + '/'), route + '/');
    assert.equal(withApiTrailingSlash(withApiTrailingSlash(route)), route + '/');
  });
}
test('preserves exact signed query strings and fragments', () => {
  const query = '?t=synthetic%2Btoken%2Fvalue%3D&search=a+b&page=2#preview';
  assert.equal(withApiTrailingSlash('/api/documents/fixture' + query), '/api/documents/fixture/' + query);
  assert.equal(withApiTrailingSlash('/api/documents/fixture/' + query), '/api/documents/fixture/' + query);
});
test('supports direct backend URLs and empty optional URLs', () => {
  assert.equal(withApiTrailingSlash('https://api.example.test/api/auth/token?next=%2F'), 'https://api.example.test/api/auth/token/?next=%2F');
  assert.equal(withApiTrailingSlash(''), '');
});
