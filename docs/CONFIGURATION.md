# Configuration

Copying a template is insufficient for secrets: run `python scripts/init_env.py`. It creates random values only when `.env` does not exist. Docker environment variables override file configuration. For direct Django commands python-decouple finds the root `.env`.

| Variables | Purpose |
|---|---|
| `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` | Django signing and deployment boundary. No default signing secret. |
| `DB_*`, `DATABASE_URL`, `USE_SQLITE`, `DB_SSL_REQUIRE` | PostgreSQL connection; URL chosen when SQLite is explicitly disabled. Require TLS for remote production DB connections. |
| `CORS_ALLOWED_ORIGINS` | Exact permitted browser HTTP and WebSocket origins. |
| `USE_REDIS_CHANNEL_LAYER`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | Shared channel/cache/broker infrastructure. Redis is required in Compose. |
| `AIHMS_ENABLE_DEMO`, `AIHMS_DEMO_PASSWORD` | Development-only fixture enablement and operator-generated password. |
| `API_INTERNAL_URL` | Next.js HTTP proxy backend address; evaluated during build for production rewrites. |
| `NEXT_PUBLIC_WS_URL` | Browser-reachable WebSocket server URL, public at frontend build time. |
| `TESSERACT_CMD` | Tesseract executable. Uses public library API if CLI is absent and system library/language data are installed. |
| `VISION_BASE_URL`, `VISION_MODEL`, `VISION_API_KEY` | Compatible `/v1` vision service. Empty values yield an explicit unavailable state for handwriting. |
| `VISION_IS_EXTERNAL`, `EXTERNAL_AI_ENABLED` | Privacy boundary. External vision requires both operator enablement and patient consent recorded for that upload. |
| `GEMINI_API_KEY`, `GROQ_API_KEY`, `GROQ_MODEL` | Optional pre-existing general AI integrations; disabled by `EXTERNAL_AI_ENABLED=False`. |
| `OUTBOUND_NOTIFICATIONS_ENABLED`, `EMAIL_*`, `DEFAULT_FROM_EMAIL` | Optional outbound messaging; use Mailpit for synthetic development. In-app notifications persist without delivery credentials. |
| `VAPID_*`, `TWILIO_*` | Optional push/SMS/WhatsApp credentials; no shared keys are supplied. |

Do not point external AI at real patient data until privacy authorization, provider contracts, retention, jurisdiction, and clinical review are assessed. Existing general AI HTTP requests require `X-AI-Consent: true`; the patient AI screen explicitly asks for consent. Report uploads run local OCR and do not automatically send clinical records to an LLM.

Private uploaded files are local volume storage in this adaptation. S3/MinIO, encryption key management, malware scanning, external notification retries, and formal consent management require additional work before any real deployment. The reader's format/resource checks are not a substitute for a dedicated malware scanner.
