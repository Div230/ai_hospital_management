# AI Hospital Management System (AIHMS)

A locally hosted Django REST Framework and Next.js application with patient, doctor, hospital administrator, laboratory, and pharmacy portals. This adaptation fixes integration/security defects in the imported application and adds one feature: a prescription reader with real local OCR, optional configured vision recognition, explicit uncertainty, private originals, and clinician review.

**Validation status:** local OCR and isolated document/extraction tests run successfully. The complete Django/PostgreSQL application, Docker startup, and Next.js production build have not been verified in the current restricted environment. See [the implementation report](docs/IMPLEMENTATION_REPORT.md) for exact evidence and remaining limitations. This software has not been validated for real clinical use.

## Run with Docker

Requirements: Docker Engine with Compose, access to container/package registries, and available ports 3000, 8000, and 8025.

```bash
cd aihms  # if starting from the parent workspace
python scripts/init_env.py
docker compose up --build -d
docker compose exec backend python manage.py seed_demo
```

The first command generates unique development secrets in an ignored, mode-0600 `.env`. Never commit that file. Backend startup applies Django migrations before workers start. PostgreSQL and Redis stay on the internal Compose network. Uploaded documents live in a private Docker volume and are not exposed as public static files.

- Application: http://localhost:3000
- Django staff administration: http://localhost:8000/admin/
- API documentation: http://localhost:8000/api/docs/
- Health: http://localhost:8000/api/core/health/
- Local mailbox: http://localhost:8025

Mail delivery is disabled by default. To test it against Mailpit, set `OUTBOUND_NOTIFICATIONS_ENABLED=True` in `.env` and recreate backend/worker/scheduler containers. Mailpit captures local mail; it does not deliver email to real recipients.

The sample accounts are explicitly synthetic:

| Portal | Email |
|---|---|
| Administrator | `admin@demo.example.test` |
| Doctor | `doctor@demo.example.test` |
| Second doctor | `doctor2@demo.example.test` |
| Patient | `patient@demo.example.test` |
| Second patient | `patient2@demo.example.test` |
| Laboratory | `lab@demo.example.test` |
| Pharmacy | `pharmacy@demo.example.test` |

Their password is the generated `AIHMS_DEMO_PASSWORD` in your local `.env`. Seeding is idempotent and refuses to run unless `DEBUG=True` and `AIHMS_ENABLE_DEMO=True`. Reset **only fixture account passwords** with:

```bash
docker compose exec backend python manage.py seed_demo --reset-passwords
```

Public registration creates patient accounts only. Use Django staff administration to provision staff users and their corresponding Doctor/Laboratory/Pharmacy profiles. Doctor profiles require a real registration number in real environments and explicit verification; weekly availability is managed through the doctor profile page or Django administration. Never treat synthetic qualifications or fixture records as clinical data.

## Run directly with activate_mlenv

Start PostgreSQL and Redis locally, or run `docker compose up -d postgres redis mail` and configure their reachable hosts/ports. The Compose database and Redis services have no published ports by default; direct host development needs your own local services or a development override.

```bash
activate_mlenv
python scripts/init_env.py
pip install -r requirements.txt
# Install Tesseract English language data through your OS package manager.
# Debian/Ubuntu: sudo apt-get install tesseract-ocr tesseract-ocr-eng
# Set DB_HOST/DB_PORT and broker URLs in .env for your local services.
cd backend
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 127.0.0.1:8000
```

From separate terminals:

```bash
activate_mlenv
cd backend
celery -A config worker --loglevel=WARNING
```

```bash
activate_mlenv
cd backend
celery -A config beat --loglevel=WARNING
```

```bash
cd frontend
cp .env.local.example .env.local
npm ci
npm run dev
```

For a single-process database experiment, `USE_SQLITE=True` is an explicit development option. Use PostgreSQL for transaction-safe concurrent booking and the integration/concurrency tests. Do not deploy with SQLite.

## Prescription reader

1. Log in as a patient and open **Prescription Reader**.
2. Choose or drop a JPG/PNG/PDF up to 10 MB; PDF limit is five pages.
3. Select printed text or handwriting. Printed text uses local Tesseract and sends no data externally.
4. Submit, then watch processing status. The original remains available even if the provider fails.
5. Compare transcription and explicitly labelled fields with the original. All recognized values remain unverified; missing fields are not inferred. Unreadable text is marked accordingly.
6. Copy/download text, save a separate personal correction, or request review by a treating doctor.
7. A doctor with an authorized appointment can open **Prescription Reviews** and record an append-only review.

Personal corrections preserve the original document and machine result. They do not change the prescription or a signed clinical record. Original document links expire after 60 seconds; use **Refresh original link** to obtain a new authorized link.

Handwriting recognition is optional. Set `VISION_BASE_URL` to an OpenAI-compatible `/v1` API base, `VISION_MODEL`, and optionally `VISION_API_KEY`. For a local service, use a loopback/private endpoint and set `VISION_IS_EXTERNAL=False`. To use an external provider, HTTPS, `VISION_IS_EXTERNAL=True`, `EXTERNAL_AI_ENABLED=True`, and the patient's explicit per-upload consent are all required. No credentials means no fabricated handwriting results: the upload shows `UNAVAILABLE`.

The reader is a transcription aid. It must not be used to decide medication names, doses, substitutions, or safety. Check the original with a licensed clinician/pharmacist. Conservative label extraction intentionally leaves many unlabelled prescription fields absent.

## Verification

```bash
activate_mlenv
pip install pytest
PYTHONPATH=backend pytest -q backend/prescription_reader/tests/test_pure.py
python -m compileall -q backend scripts
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test accounts appointments prescription_reader.tests.test_api
```

Run the Django tests against isolated PostgreSQL (`USE_SQLITE=False`); the test runner creates a separate `test_` database. Never point tests at a clinical database. Test fixtures and mock providers are synthetic and confined to tests. Configure the test database user to create/drop its isolated test database.

```bash
cd frontend
npm ci
npm run typecheck
npm run build
```

A GitHub Actions workflow runs migrations, regression tests, TypeScript, and frontend build with disposable services. Its presence is not evidence that it has passed; see the report.

## Operations and boundaries

See [architecture and workflows](docs/ARCHITECTURE.md), [configuration](docs/CONFIGURATION.md), [deployment and recovery](docs/DEPLOYMENT.md), and [implementation report](docs/IMPLEMENTATION_REPORT.md).

Emergency ambulance dispatch is intentionally unavailable; the previous simulation must not be mistaken for a real ambulance service. Outbound webhooks are disabled pending endpoint/tenant security review. Existing general AI features require configuration and explicit consent; no default health score is fabricated. Pharmacy prescription discovery is restricted to already assigned orders; a new patient-directed pharmacy sharing workflow is outside this adaptation.

The initial greenfield specification was cancelled. This repository retains its Django/Next.js architecture; it is not a completed implementation of every requirement in that earlier specification.

## Troubleshooting API 500s on form submission

If backend logs mention `APPEND_SLASH` on a POST, rebuild the updated application containers:

```bash
docker compose up --build -d --wait
python scripts/check_api_routes.py
```

The checker accepts expected validation/authentication failures and rejects redirects/server errors. It submits no valid patient-creation payloads. See [routing repair and regression checks](docs/ROUTING_FIX.md). Existing database/document volumes are preserved; no reset is needed.
