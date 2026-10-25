# API routing and integration regression repair

The supplied Docker logs confirmed `POST /api/auth/register` and `POST /api/auth/token` reached Django without their required trailing slashes. Django's `APPEND_SLASH` middleware cannot redirect these requests while preserving POST data and raises a development-mode 500.

Root cause: Next.js normally redirects a slash-terminated URL to its slashless form. The frontend requests already contained slashes, but the shared proxy path did not preserve Django's convention.

Repair:

- Disable Next's automatic slash redirects with `skipTrailingSlashRedirect`.
- Match both API URL forms and rewrite each directly to the slash-terminated Django endpoint. Do not redirect unsafe methods or disable Django's URL conventions.
- Canonicalize Axios request paths centrally, preserving exact query/fragment text. This also protects direct-backend configuration and future calls that omit a slash.
- Preserve signed document links through the shared proxy, including their query strings.
- Catch SimpleJWT `TokenError` during cookie refresh and return a 401 for malformed/expired/blacklisted refresh credentials instead of a generic 500.
- Let the browser/Axios supply multipart boundaries for existing medical/lab uploads.
- Remove the settings screen's request to a deliberately disabled account-deletion endpoint, explain retention review, and load the actual server-side 2FA state.

Next behavior references: [trailing-slash defaults](https://nextjs.org/docs/app/api-reference/config/next-config-js/trailingSlash) and [skipTrailingSlashRedirect](https://nextjs.org/docs/app/api-reference/config/next-config-js/skipTrailingSlashRedirect).

## Verification evidence

- `cd frontend && npm test`: **29 tests passed** (27 path/query/idempotence cases, two Next configuration contracts).
- Backend Python compilation and frontend syntax checks passed. Frontend count is now 48 TS/TSX/MJS files.
- A real standalone Next.js HTTP proxy regression suite is added, covering POST/PATCH/PUT/DELETE, both slash forms, exact body hashes, multipart binary payloads, query strings, signed links, auth/CSRF headers, Set-Cookie forwarding, and upstream error statuses. It is wired into CI but could not run locally because the Next.js dependencies/build are absent and Docker access is denied.
- Added Django registration/login and invalid/blacklisted refresh regressions. These require the Docker/Python runtime and remain unexecuted in this restricted session.

## Apply to the running application

From the repository root:

```bash
sudo docker compose up --build -d --wait
python scripts/check_api_routes.py
sudo docker compose exec -T backend python manage.py test accounts
```

The HTTP smoke checker needs only Python's standard library. It sends empty, unauthenticated synthetic requests to existing endpoints; no patient data or valid creation payloads are submitted. Expected validation/authentication responses are accepted; redirects and server errors fail the check. Both slash forms are tested. It does not prove all business workflows pass.

The rebuild replaces application containers and preserves existing database/document volumes. Do not run `down -v` or reseed/reset data to resolve this routing issue.

To run the isolated real Next.js proxy suite on a development/CI machine with npm dependencies:

```bash
cd frontend
npm ci
npm test
API_INTERNAL_URL=http://127.0.0.1:18080 npm run build
npm run test:proxy
```

The fixture uses only local test ports 18080/18081 and an echo server; it never contacts the hospital database. Rebuild with the normal backend address before using that development build against the application. Docker Compose's build supplies `http://backend:8000` automatically.
