# AI Hospital Management System (AIHMS)

### Intelligent Healthcare Management with AI-Powered Prescription Recognition

[![AIHMS Validation](https://github.com/Div230/ai_hospital_management/actions/workflows/ci.yml/badge.svg)](https://github.com/Div230/ai_hospital_management/actions/workflows/ci.yml)

**AI Hospital Management System (AIHMS)** is a full-stack healthcare management platform built using Django REST Framework and Next.js.

The application provides integrated portals for patients, doctors, hospital administrators, laboratory staff, and pharmacists. It supports appointment scheduling, medical records, prescriptions, laboratory operations, and hospital management.

AIHMS also includes an **AI-powered Prescription Reader** that converts printed medical prescriptions into readable digital text using local OCR, with optional vision-language model support for handwriting recognition.

**Repository:** https://github.com/Div230/ai_hospital_management

## Features

### Patient Portal

- Secure patient registration and authentication
- Personalized dashboard
- Doctor discovery and appointment booking
- Appointment management
- Medical records and prescription history
- Laboratory reports
- Notifications
- AI prescription uploads and transcription
- Prescription corrections and clinician review requests

### Doctor Portal

- Doctor profile and availability management
- Appointment scheduling
- Authorized patient record access
- Consultation management
- Digital prescriptions
- Laboratory test ordering
- Medical history access
- Prescription transcription review

### Hospital Administration

- Staff and user management
- Doctor and department management
- Appointment oversight
- Hospital-level doctor assignments
- Patient administration
- Operational dashboards
- Role-based account provisioning

### Laboratory Management

- Laboratory staff portal
- Test and diagnostic order management
- Sample and processing status tracking
- Diagnostic report management
- Authorized access to patient laboratory information

### Pharmacy Management

- Pharmacy staff portal
- Assigned prescription management
- Medication inventory operations
- Prescription processing
- Stock and order status management
- Restricted access to authorized prescriptions

## AI Prescription Reader

AIHMS includes a prescription recognition system that allows patients to upload medical prescriptions and obtain structured, readable transcriptions.

### Capabilities

- JPG, PNG, and PDF uploads
- Maximum file size of 10 MB
- PDF support up to five pages
- Local printed-text OCR using Tesseract
- Optional handwriting recognition through a configured vision model
- Image preprocessing
- Structured information extraction
- Explicit identification of unreadable or uncertain text
- Private original document storage
- Transcription history
- Copy and download functionality
- Personal correction history
- Treating-doctor review

### Processing Pipeline

```text
Prescription Upload
        |
        v
File Validation
        |
        v
Private Document Storage
        |
        v
Image Preprocessing
        |
        v
OCR / Vision Recognition
        |
        v
Structured Extraction
        |
        v
Uncertainty Handling
        |
        v
Patient Transcription
        |
        v
Optional Clinician Review
```

The system does not infer missing medication names, dosages, or instructions. All AI-extracted information is considered unverified.

Printed prescriptions can be processed locally without external AI services. External handwriting recognition requires explicit configuration and consent.

**Medical disclaimer:** AI-generated transcriptions are informational and must not be used independently for prescribing, medication substitutions, or treatment decisions.

---

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | Next.js 16, React 19, TypeScript |
| Styling | Tailwind CSS |
| Backend | Django, Django REST Framework |
| Realtime | Django Channels |
| Database | PostgreSQL 17 |
| Cache | Redis |
| Background Processing | Celery |
| OCR | Tesseract |
| Handwriting Recognition | Optional compatible Vision AI |
| Authentication | JWT, HttpOnly refresh cookies, CSRF protection |
| Email Testing | Mailpit |
| Infrastructure | Docker, Docker Compose |
| Testing | Pytest, Django Tests, Node.js Tests |
| CI/CD | GitHub Actions |

## System Architecture

```text
             Next.js Frontend
                    |
          Patient / Doctor / Admin
           Laboratory / Pharmacy
                    |
                    v
             Django REST API
                    |
        +-----------+-----------+
        |           |           |
        v           v           v
   PostgreSQL     Redis      Private
                             Documents
                    |
                    v
               Celery Worker
                    |
              OCR / Vision AI
```

The backend handles authorization, hospital operations, prescription processing requests, and medical data access. Redis and Celery support asynchronous processing, while PostgreSQL provides persistent application storage.

Original documents are stored privately and accessed through expiring, authorized links.

More information: [Architecture Documentation](docs/ARCHITECTURE.md).

---

## Quick Start — Docker (Recommended)

### Requirements

- Git
- Docker Engine
- Docker Compose
- Internet access for dependency and image installation

Ensure ports `3000`, `8000`, and `8025` are available.

### 1. Clone the Repository

```bash
git clone https://github.com/Div230/ai_hospital_management.git
cd ai_hospital_management
```

### 2. Initialize Environment

```bash
python3 scripts/init_env.py
```

This creates an ignored `.env` file containing randomly generated development secrets and demo credentials.

Never commit `.env` to version control.

### 3. Build and Start

```bash
docker compose up --build -d --wait
```

The Compose environment includes:

- Django backend
- Next.js frontend
- PostgreSQL
- Redis
- Celery worker
- Celery scheduler
- Mailpit

Database migrations are applied during backend startup.

### 4. Initialize Demo Data

```bash
docker compose exec backend python manage.py seed_demo
```

The command creates synthetic accounts and demonstration records.

### 5. Access the Application

| Service | Address |
|---|---|
| Web Application | http://localhost:3000 |
| Django Administration | http://localhost:8000/admin/ |
| API Documentation | http://localhost:8000/api/docs/ |
| Backend Health | http://localhost:8000/api/core/health/ |
| Mailpit | http://localhost:8025 |

### Demo Accounts

| Role | Email |
|---|---|
| Administrator | `admin@demo.example.test` |
| Doctor | `doctor@demo.example.test` |
| Doctor 2 | `doctor2@demo.example.test` |
| Patient | `patient@demo.example.test` |
| Patient 2 | `patient2@demo.example.test` |
| Laboratory | `lab@demo.example.test` |
| Pharmacy | `pharmacy@demo.example.test` |

The password for each account is generated during environment initialization and stored as `AIHMS_DEMO_PASSWORD` in `.env`.

Demo seeding requires `DEBUG=True` and `AIHMS_ENABLE_DEMO=True`.

To reset synthetic account passwords:

```bash
docker compose exec backend python manage.py seed_demo --reset-passwords
```

### Stop Services

```bash
docker compose down
```

This stops the application without deleting persistent database or document volumes.

---

## Manual Development Setup

Docker is recommended, but the services can also be run directly for development.

### Requirements

- Python 3.12+
- Node.js 22+
- PostgreSQL
- Redis
- Tesseract OCR
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/Div230/ai_hospital_management.git
cd ai_hospital_management
```

### 2. Create a Python Virtual Environment

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install Python Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Install Tesseract and its English language data through your operating system's package manager.

Ubuntu/Debian:

```bash
sudo apt-get install tesseract-ocr tesseract-ocr-eng
```

Ensure the Tesseract executable can be found by the application.

### 4. Configure Environment

```bash
python scripts/init_env.py
```

Configure the local PostgreSQL and Redis connection settings in `.env`.

PostgreSQL and Redis must be running and accessible before starting Django.

### 5. Initialize and Start Backend

```bash
cd backend
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 127.0.0.1:8000
```

### 6. Start Celery Worker

Open a second terminal from the repository root.

Activate the same Python virtual environment, then run:

```bash
cd backend
celery -A config worker --loglevel=WARNING
```

### 7. Start Celery Scheduler

Open a third terminal with the Python virtual environment activated:

```bash
cd backend
celery -A config beat --loglevel=WARNING
```

### 8. Start Frontend

From the repository root:

```bash
cd frontend
cp .env.local.example .env.local
npm ci
npm run dev
```

Open http://localhost:3000.

The frontend connects to the Django API through its configured proxy.

**Database note:** `USE_SQLITE=True` is available for limited local experimentation. PostgreSQL is required for transaction-safe concurrent appointment booking and the corresponding integration tests.

---

## AI Configuration

### Printed Text Recognition

Tesseract OCR processes printed prescriptions locally without external AI credentials.

The optional `TESSERACT_CMD` variable can specify a custom Tesseract executable path.

### Handwriting Recognition

Configure an OpenAI-compatible vision endpoint:

```env
VISION_BASE_URL=
VISION_MODEL=
VISION_API_KEY=
VISION_IS_EXTERNAL=False
EXTERNAL_AI_ENABLED=False
```

For external inference, the application requires HTTPS, explicit external AI enablement, and patient consent for the upload.

Without a configured handwriting recognition provider, the system reports `UNAVAILABLE` instead of returning fabricated transcription results.

See [Configuration Documentation](docs/CONFIGURATION.md).

---

## Security

AIHMS incorporates application-level safeguards including:

- Role-based access control
- Patient-level record isolation
- Patient-only public registration
- Protected staff account provisioning
- Single-use, password-bound 2FA challenges
- JWT access tokens
- Rotating HttpOnly refresh cookies
- CSRF and origin validation
- Login throttling
- Restricted document storage
- Expiring authorized document links
- Controlled clinical record modifications
- Transactional appointment booking
- Pharmacy assignment restrictions
- Private prescription processing
- Explicit consent requirements for external AI

Security controls require deployment-specific testing and review before use with real patient data.

---

## Testing

### Backend Tests

Create and activate a standard Python virtual environment as described in the manual setup section, then install dependencies.

From the repository root:

```bash
pip install -r requirements.txt pytest
PYTHONPATH=backend pytest -q backend/prescription_reader/tests/test_pure.py
python -m compileall -q backend scripts
```

Run Django checks and regression tests:

```bash
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test accounts appointments prescription_reader.tests.test_api
```

Django integration tests should use an isolated PostgreSQL test database rather than clinical or production data.

### Frontend Tests

From `frontend/`:

```bash
npm ci
npm test
npm run typecheck
npm run build
npm run test:proxy
```

### API Integration Check

With the Docker application running:

```bash
python scripts/check_api_routes.py
```

This checks API routing behavior and rejects unexpected redirects or server errors.

### GitHub Actions Validation

[![AIHMS Validation](https://github.com/Div230/ai_hospital_management/actions/workflows/ci.yml/badge.svg)](https://github.com/Div230/ai_hospital_management/actions/workflows/ci.yml)

The GitHub Actions validation workflow passed on October 25, 2026, including:

- Local OCR tests
- Django checks and migrations
- Django regression tests
- Docker Compose configuration validation
- Frontend tests
- TypeScript checking
- Next.js production build
- API proxy regression tests

[View Successful CI Run](https://github.com/Div230/ai_hospital_management/actions/runs/40200597011)

These results validate the listed automated checks. They do not constitute full end-to-end clinical or production deployment certification.

---

## Troubleshooting

### Check Running Services

```bash
docker compose ps
```

### Backend Logs

```bash
docker compose logs --tail=100 backend
```

### Frontend Logs

```bash
docker compose logs --tail=100 frontend
```

### Celery Worker Logs

```bash
docker compose logs --tail=100 worker
```

### Prescription Processing Delays

Check Redis, Celery worker, and scheduler health:

```bash
docker compose logs --tail=100 redis worker scheduler
```

### Registration or Login Returns HTTP 500

An earlier API routing issue involving Django's `APPEND_SLASH` middleware was corrected by normalizing frontend request paths and proxy behavior.

Rebuild the application and run the route checker:

```bash
docker compose up --build -d --wait
python scripts/check_api_routes.py
```

Details are available in [API Routing Fix](docs/ROUTING_FIX.md).

---

## Documentation

- [Architecture and Workflows](docs/ARCHITECTURE.md)
- [Configuration](docs/CONFIGURATION.md)
- [Deployment and Recovery](docs/DEPLOYMENT.md)
- [Implementation Report](docs/IMPLEMENTATION_REPORT.md)
- [API Routing Fix](docs/ROUTING_FIX.md)

## Known Limitations

The current application is intended for local development, demonstration, and further validation.

Areas requiring additional work before clinical deployment include:

- Clinical accuracy validation for handwriting recognition
- Full signed clinical record amendment workflows
- Complete laboratory verification and correction processes
- Production-grade infrastructure hardening
- Comprehensive backup and disaster recovery testing
- Formal security and privacy assessments
- Healthcare regulatory review

Emergency ambulance dispatch is intentionally unavailable rather than simulated as a working service.

## License

No application license has been declared in the repository. Redistribution rights for imported and third-party components should be reviewed before reuse or distribution.

## Disclaimer

AIHMS is not certified for real clinical use.

Prescription transcriptions may contain recognition errors and should be checked against original documents by qualified healthcare professionals.

AIHMS does not independently provide medical diagnoses or treatment decisions.

---

**AI Hospital Management System — Connecting Patients, Doctors, and Healthcare Services Through Intelligent Software.**
