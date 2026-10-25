# AIHMS web portal

Next.js App Router, strict TypeScript, Tailwind, Lucide, and Recharts. See the repository-root README for backend, environment, and account setup.

```bash
npm ci
cp .env.local.example .env.local
npm run dev
npm run typecheck
npm run build
```

HTTP API calls use a same-origin `/api` proxy configured by `API_INTERNAL_URL`. The access token lives in memory; the rotating refresh token lives in an HttpOnly cookie. `NEXT_PUBLIC_WS_URL` configures the direct Django WebSocket address and is a build-time public value. Rebuild the frontend after changing that address.

Patient prescription reader: `/dashboard/patient/prescription-reader`.
Treating-doctor review queue: `/dashboard/doctor/prescription-reader`.
