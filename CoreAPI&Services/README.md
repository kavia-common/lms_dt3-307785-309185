# CoreAPI&Services (LMS Backend)

Production-ready backend scaffold for the DigitalT3 LMS using **FastAPI**.

## Features included
- REST API-ready FastAPI application structure
- Health probes:
  - `GET /healthz`
  - `GET /readyz`
- Centralized settings loaded from environment variables (supports `.env`)
- Standardized JSON error responses
- CORS configuration (env-driven)
- Structured logging (JSON in production; readable logs in development)
- Tooling:
  - `ruff` (lint)
  - `black` (format)
  - `pytest` (tests)
- Containerization:
  - `Dockerfile`
  - `.dockerignore`

## Project structure

- `app/`
  - `main.py` (FastAPI entrypoint)
  - `api/routers/` (route modules)
  - `core/config.py` (settings)
  - `core/logging.py` (logging setup)
  - `core/errors.py` (error handling + response models)
  - `core/security/` (placeholder for future auth/RBAC)
  - `services/` (business logic modules; placeholder)
  - `schemas/` (Pydantic models; placeholder)
  - `tests/` (pytest)

## Environment variables

See `.env.example` for the full list.

Notes:
- This container already has a `.env` managed by the platform/orchestrator. Do not commit secrets.
- For CORS, set `ALLOWED_ORIGINS` (comma-separated).

## Local development

### 1) Install dependencies
The platform's init scripts install dependencies into `/opt/venv` using `requirements.txt`.

If running locally yourself:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Run the API
Using uvicorn:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload
```

Open:
- `http://localhost:3001/docs`
- `http://localhost:3001/openapi.json`

### 3) Lint/format
```bash
ruff check .
black .
```

### 4) Run tests
```bash
pytest -q
```

## Docker

Build:
```bash
docker build -t lms-coreapi .
```

Run:
```bash
docker run --rm -p 3001:3001 --env-file .env lms-coreapi
```

## Roadmap / TODO
- TODO(auth): Microsoft Entra ID token validation
- TODO(rbac): role-based authorization policies
- TODO(db): MongoDB integration (connection pooling, repositories)
- TODO(observability): metrics/tracing (OpenTelemetry)
