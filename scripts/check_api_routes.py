"""Non-mutating HTTP checks against a running frontend proxy; no dependencies."""
import argparse
import sys
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


# Missing credentials/required fields intentionally prevent record creation.
PROBES = [
    ('GET', '/api/core/health', {200}),
    ('POST', '/api/auth/register', {400, 429}),
    ('POST', '/api/auth/token', {400, 429}),
    ('POST', '/api/auth/token/refresh', {403, 429}),
    ('PATCH', '/api/auth/me', {401}),
    ('POST', '/api/appointments/book', {401}),
    ('POST', '/api/prescription-reader', {401}),
    ('GET', '/api/doctors/directory', {401}),
    ('DELETE', '/api/notifications/push/subscribe', {401}),
    ('GET', '/api/documents/prescription-upload/00000000-0000-0000-0000-000000000000', {404}),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://localhost:3000')
    args = parser.parse_args()
    opener = build_opener(NoRedirects())
    failed = 0
    for method, path, expected in PROBES:
        for slash in ('', '/'):
            target = args.base_url.rstrip('/') + path + slash + '?routing_probe=1'
            req = Request(target, method=method, data=None if method == 'GET' else b'{}',
                          headers={'Content-Type': 'application/json'})
            try:
                with opener.open(req, timeout=10) as response:
                    code = response.status
            except HTTPError as exc:
                code = exc.code
                exc.close()
            except (URLError, OSError) as exc:
                print(f'FAIL {method} {path}{slash}: connection unavailable ({type(exc).__name__})')
                failed += 1
                continue
            success = code in expected
            failed += not success
            print(f'{"PASS" if success else "FAIL"} {method} {path}{slash}: {code}')
    print(f'{len(PROBES) * 2 - failed}/{len(PROBES) * 2} routing probes passed')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
