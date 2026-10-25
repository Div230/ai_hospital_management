# AIHMS implementation report

Date: 2026-10-25. Scope: adapt the requested existing application, fix identified issues, and add only the prescription reader. The earlier greenfield implementation was removed at the user's request.

## Source and identity changes

The shell could not resolve GitHub. The GitHub connector imported all 198 source files into `aihms/`; all original bytes were verified against upstream Git blob hashes before changes, including restoring two UTF-16 requirements files before verification. A fresh local Git repository contains the working copy; original Git history/remotes were not copied. This is a source snapshot import, not a full network clone.

Removed the personal biography, names/handle, personal profile links, previous deployment URLs, and previous product names from the application/documentation/configuration. Replaced product identity with AIHMS, added its own vector icon, and removed unused template logos. No replacement authorship claim was added. No application license file was present in the imported tree.

## Implemented and locally exercised

- Real Tesseract printed-document OCR via CLI or system C API, contrast/orientation normalization and bounded PDF rendering.
- Real content/type checks for JPG/PNG/PDF, file/page/dimension limits, damaged-file rejection, and rejection of recognizable active/embedded PDF content.
- Conservative field extraction from literal labels. Missing doses are not inferred; ambiguous medication text becomes unreadable; every recognized value remains explicitly unverified.
- Provider configuration/consent guards and explicit vision-service failures, tested with test-only HTTP substitution.
- Slot generation and half-open overlap calculations, including invalid schedule rejection.
- **32 pytest cases passed** under `activate_mlenv`, including a real synthetic printed prescription through OCR and structured extraction. This is not a clinical accuracy benchmark.
- Python compilation passed for backend and scripts.
- Babel's TypeScript/JSX parser accepted **44 frontend source/config files** without syntax errors. The parser was read from an existing local development tool installation. This is a syntax check, not strict TypeScript or a Next.js build.
- Docker Compose configuration validation passed (`docker compose config --quiet`). YAML and package JSON parsing also passed.
- A generated local `.env` has mode 0600, unique secrets, and is ignored by Git. No secret values are recorded here.

## Implemented, awaiting full integration verification

Prescription reader:

- Database models/migration for private originals, durable processing state, immutable personal correction history, and treating-doctor review history.
- Validated multipart upload, paginated/searchable history, detail, retry, correction, review request, clinical review, and transcription download APIs.
- Celery processing with database outbox, expiring leases, recovery scheduler, bounded attempts, stale-worker run tokens, and atomic completion notifications.
- Configurable compatible vision provider; external use requires HTTPS, operator enablement, and recorded per-upload consent. Provider absence never creates canned results.
- Patient drag/drop/preview, state polling, transcription/field comparison, uncertainty, copy/download, separate personal corrections, review requests, and doctor review queue.

Repairs to the imported application:

- Patient-only self-registration and protected verification/role fields; staff provisioning through Django administration.
- Password-bound, expiring single-use 2FA challenge; inactive-account checks and login throttling.
- Access tokens in browser memory, rotating HttpOnly refresh cookies, CSRF/origin checks for cookie operations, password-change revocation checks, and explicit server logout.
- Private expiring document capabilities with current account/workflow rechecks; removed public media routes.
- Doctor-row locking, configured-slot validation, duration snapshots, duplicate active slot constraint, atomic rescheduling/cancellation, and hospital-scoped doctor assignment.
- Prescription and clinical-note creation checks; existing records cannot be silently edited/deleted through those APIs or Django admin.
- Doctor/patient record isolation checks, pharmacy mutation permissions/assigned-order restriction, serialized stock/status transitions, and removal of cross-hospital webhook broadcasts.
- Removed shared signing/push secrets, fabricated default health score and automatic “all values normal” messages. General AI/external notifications are disabled by default; source documents are not automatically sent to external AI.
- Replaced simulated ambulance dispatch with an unavailable state and a direct emergency-call link.
- Same-origin frontend API proxy, role route redirects, mobile navigation, actual appointment slot picker, and more visible error states.
- PostgreSQL/Redis/backend/worker/scheduler/frontend/Mailpit Compose services, Dockerfiles, health checks, generated environment setup, repeatable synthetic accounts/data, setup/architecture/deployment/backup documentation, and CI configuration.

Django regression tests are authored for staff registration, cookie/CSRF behavior, 2FA bypass prevention, concurrent bookings, cancellation/rescheduling integrity, cross-patient/document isolation, reader lifecycle/idempotence, corrections/reviews, and provider unavailability. They have **not run** in this environment.

## Blocking environment evidence

| Attempt | Observed result |
|---|---|
| `git ls-remote` | Shell cannot resolve `github.com`; connector used instead. |
| Python dependency installation | Django is absent; package resolver cannot obtain it through the restricted network. |
| `python manage.py check` and Django tests | Stop at `ModuleNotFoundError: django`; no migrations or API test results claimed. |
| `npm ci --offline` | Missing cached `which-typed-array` archive. |
| Production-only offline install | Missing cached `victory-vendor` archive. |
| `npm run typecheck` | Fails on missing Next/Axios/Lucide and other dependency declarations; a full type check is not available. |
| `npm run build` | `next: command not found`. |
| `docker compose up -d --build` | Docker daemon socket access denied. No services were started. |
| Direct PostgreSQL fallback | TCP and Unix-domain socket creation are restricted. |

Therefore the application is **not represented as fully working end-to-end or deployment-ready**. Once dependency/daemon access is available, run the README verification commands, inspect migration drift, run PostgreSQL regressions and browser workflows, and fix any integration failures before use.

## Optional/unavailable integrations and limits

- Handwritten recognition needs an actual model endpoint. No real vision-provider test was possible; only its guards/failure behavior were exercised.
- External general AI, Twilio, SMTP delivery, push, and video/TURN infrastructure need operator configuration and separate validation. Webhooks are intentionally disabled.
- Original medical/laboratory modules retain clinical limitations: no complete signed-consultation amendment system, full laboratory verification/release/correction workflow, or comprehensive clinical permission audit. Existing clinical write APIs were constrained to prevent silent overwrites; a complete amendment workflow was not added.
- New pharmacy prescription sharing needs a patient-directed target/consent design. Pharmacies can only see already assigned orders; they cannot browse every patient's prescriptions.
- Private storage uses a local shared volume. S3/MinIO, encryption operations, malware scanner integration, retention/deletion workflows and disaster-recovery drills remain deployment work.
- Regex label extraction deliberately misses unlabelled fields. OCR and model output are not calibrated or clinically verified. Model prompting does not guarantee hallucination-free handwriting recognition.
- No Playwright/browser acceptance run or full frontend component suite passed in this environment. No complete patient-to-doctor-to-laboratory flow is claimed.
- Dependency ranges/images must be locked and security-reviewed after successful installation. The local Mailpit image uses a floating development tag.
- Formal security, privacy, regulatory, operational, accessibility, and clinical validation remain necessary. No legal or healthcare-compliance claim is made.

## Follow-up: confirmed trailing-slash failure

User-provided runtime logs confirmed slashless registration/login POSTs caused Django `APPEND_SLASH` errors. The shared proxy/client repair and related integration fixes are documented in [ROUTING_FIX.md](ROUTING_FIX.md). The new frontend routing/configuration tests passed (29 cases). Docker-backed proxy and Django regressions await execution in a Docker-enabled terminal; this session cannot access the running daemon.
