# ShiftSync: A Shift Handover Management System with NLP for Automated Task Categorisation and Priority Detection

ShiftSync is a full-stack web application designed for small and medium-sized shift-based organisations to formalise the transfer of responsibilities between outgoing and incoming workers through structured task records, automated Hugging Face Transformer NLP classification, mandatory handover acknowledgment, persistent audit trails, and supervisory oversight.

---

## 1. Technology Stack

- **Frontend**: React 18, TypeScript, Vite, React Router v6, Axios (in-memory JWT access token + `HttpOnly` refresh cookie), Lucide Icons, responsive CSS design system.
- **Backend**: Python 3.13, Django 6.1, Django REST Framework (DRF), SimpleJWT, `drf-spectacular` (OpenAPI 3.0 / Swagger), `django-cors-headers`, `django-filter`.
- **Database**: PostgreSQL 18 (`shiftsync_db`) with relational migrations, foreign key `PROTECT` audit constraints, and composite indexes.
- **NLP Engine**: Hugging Face Transformers (`BertForSequenceClassification` fine-tuned from `prajjwal1/bert-tiny` with `AutoTokenizer`) + calibrated Scikit-Learn TF-IDF/LogisticRegression fallback provider + graceful manual fallback mode.
- **Testing & CI**: `pytest` + `pytest-django` (Backend & NLP), `Vitest` + React Testing Library (Frontend), `Playwright` (End-to-End browser tests), and GitHub Actions CI (`.github/workflows/ci.yml`).

---

## 2. Quick Start Instructions

### Step 1: Configure Environment & PostgreSQL

Copy `.env.example` to `.env` and set your PostgreSQL credentials:

```ini
POSTGRES_DB=shiftsync_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<your_postgres_password>
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5433
DJANGO_SECRET_KEY=shiftsync-dev-secret-key-2026-academic-project-secure-987654321
DJANGO_DEBUG=True
```

### Step 2: Install Backend Dependencies, Migrate & Seed Demo Data

```powershell
# Install Python dependencies into the virtual environment
.\.venv\Scripts\pip.exe install -r requirements.txt

# Apply PostgreSQL migrations and seed demonstration records
cd backend
..\.venv\Scripts\python.exe manage.py migrate
..\.venv\Scripts\python.exe manage.py seed_demo_data

# (Optional) Create an interactive superuser/administrator
..\.venv\Scripts\python.exe manage.py createsuperuser

# (Optional) Re-run Hugging Face Transformer fine-tuning & evaluation
..\.venv\Scripts\python.exe nlp_service/train_transformer.py

# Start the Django REST API server on http://127.0.0.1:8000
..\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

### Step 3: Install & Start React Frontend

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Open `http://127.0.0.1:5173` in your browser.

---

## 3. Seeded Demonstration Accounts (Development Only)

All demonstration accounts use password: **`ShiftSync@2026!`**

| Role | Email | Organisational Scope |
| :--- | :--- | :--- |
| **Outgoing Worker** | `outgoing@shiftsync.ac.ke` | Kenya Airways Line Maintenance (`KQ-MRO`) |
| **Incoming Worker** | `incoming@shiftsync.ac.ke` | Kenya Airways Line Maintenance (`KQ-MRO`) |
| **Supervisor** | `supervisor@shiftsync.ac.ke` | Kenya Airways Line Maintenance (`KQ-MRO`) |
| **System Administrator** | `admin@shiftsync.ac.ke` | Kenya Airways Line Maintenance (`KQ-MRO`) |
| **External Org Worker** | `external@mombasaport.co.ke` | Mombasa Terminal Logistics (`MPA-OPS` — isolated) |

---

## 4. Running Automated Test Suites

### Backend & NLP Tests (`pytest`)
```powershell
cd backend
..\.venv\Scripts\pytest.exe -v
```

### Frontend Component & Security Tests (`Vitest` + React Testing Library)
```powershell
cd frontend
npm.cmd run test
```

### End-to-End Lifecycle Tests (`Playwright`)
With the backend (`127.0.0.1:8000`) and frontend (`127.0.0.1:5173`) running:
```powershell
cd frontend
npm.cmd run test:e2e
```

---

## 5. Documentation Index

- [Database Schema Documentation](docs/DATABASE_SCHEMA.md)
- [REST API Documentation](docs/API_DOCUMENTATION.md) (Live Swagger UI at `http://127.0.0.1:8000/api/docs/`)
- [NLP Model Evaluation Report](docs/nlp_model_evaluation.md)
- [Ubuntu + Nginx + Gunicorn Deployment Guide](docs/DEPLOYMENT_GUIDE_UBUNTU_NGINX_GUNICORN.md)
- [User Guide for Workers, Supervisors & Administrators](docs/USER_GUIDE.md)
