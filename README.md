# DigitalT3 LMS (Workspace) — Local Development Guide

This workspace contains the backend **Core API & Services** (FastAPI) and a separate **WebAppFrontend** (React) in a different workspace folder.

For backend endpoint details, see: [`CoreAPI&Services/API_SUMMARY.md`](CoreAPI&Services/API_SUMMARY.md).

## Repositories / workspaces in this checkout

- Backend workspace (this folder): `lms_dt3-307785-309185/`
  - Backend container: `CoreAPI&Services/` (FastAPI on port `3001`)
- Frontend workspace (separate folder at the same top-level): `lms_dt3-307785-309184/`
  - Frontend container: `WebAppFrontend/` (React dev server on port `3000`)

This README documents how to run the backend locally, and includes notes for running the frontend.

## Environment variables

### Backend (CoreAPI&Services)

Backend settings are loaded from environment variables and an optional `.env` file in `CoreAPI&Services/` (via `pydantic-settings`).

Authoritative example file: `CoreAPI&Services/.env.example`.

#### App runtime

- `APP_ENV` (default: `development`)
  - Environment name used for behavior toggles (e.g., logging format when `LOG_FORMAT=auto`).
- `HOST` (default: `0.0.0.0`)
  - Bind host for uvicorn.
- `PORT` (default: `3001`)
  - Bind port for uvicorn.
- `TRUST_PROXY` (default: `false`)
  - Placeholder flag for proxy-aware behavior. It is currently a setting only.

#### Logging

- `LOG_LEVEL` (default: `INFO`)
  - Root logging level (e.g., `DEBUG`, `INFO`, `WARNING`).
- `LOG_FORMAT` (default: `auto`)
  - `auto` selects JSON logs when `APP_ENV` is `production`/`prod`, otherwise console formatting.
  - You can force formats by setting `LOG_FORMAT=json` or `LOG_FORMAT=console`.

#### CORS

- `ALLOWED_ORIGINS` (default: `[]`)
  - List of allowed origins (e.g., `http://localhost:3000`).
- `ALLOWED_HEADERS` (default: `["Content-Type","Authorization","X-Requested-With"]`)
  - List of allowed request headers.
- `ALLOWED_METHODS` (default: `["GET","POST","PUT","DELETE","PATCH","OPTIONS"]`)
  - List of allowed HTTP methods.
- `CORS_MAX_AGE` (default: `3600`)
  - Browser preflight cache TTL, in seconds.

See “CORS configuration notes” below for parsing details.

#### MongoDB

MongoDB is optional for unit tests, but required for CRUD endpoints and seed scripts.

- `MONGODB_URI` (default: unset / `None`)
  - When unset, MongoDB initialization is disabled and MongoDB-backed endpoints will error if they require DB access.
- `MONGODB_DBNAME` (default: `lms`)
  - Database name used by the Motor client.
- `MONGODB_TLS` (default: `false`)
  - Enables TLS when connecting (passed to `AsyncIOMotorClient(..., tls=...)`).

#### Auth / OIDC scaffolding (currently stubbed)

- `AUTH_STUB` (default: `true`)
  - When `true`, the backend returns a deterministic “stub principal” for auth debug and does not perform real JWT validation.
  - When `false`, `/auth/debug` returns `501 Not Implemented` until real OIDC validation is implemented.

OIDC placeholders (not yet used for real validation):

- `OIDC_ISSUER` (default: unset)
- `OIDC_CLIENT_ID` (default: unset)
- `OIDC_AUDIENCE` (default: unset)
- `OIDC_JWKS_URI` (default: unset)

#### URLs / placeholders

These are currently optional placeholders (used for documentation and future integrations):

- `SITE_URL` (default: unset)
- `BACKEND_URL` (default: unset)
- `FRONTEND_URL` (default: unset)
- `WS_URL` (default: unset)

#### Misc

- `REQUEST_TIMEOUT_MS` (default: `30000`)
  - Placeholder timeout value for future outbound calls.
- `RATE_LIMIT_WINDOW_S` (default: `60`)
  - Placeholder rate limit window duration.
- `RATE_LIMIT_MAX` (default: `100`)
  - Placeholder max requests per window.
- `COOKIE_DOMAIN` (default: unset)
  - Placeholder cookie domain setting.

### Frontend (WebAppFrontend)

The frontend container is located at `lms_dt3-307785-309184/WebAppFrontend`.

No frontend `.env`/`.env.example` was found in the current codebase, and the current frontend entrypoint is a minimal React app. If/when the frontend adds environment variables, they will typically be declared in a file such as `.env` or `.env.example` under `WebAppFrontend/` and should be documented here.

## How to run locally

### 1) Backend: CoreAPI&Services

#### Prerequisites

- Python 3.11
- (Optional but recommended) a local MongoDB instance if you want to exercise CRUD endpoints and seed scripts

#### Install dependencies

From the backend folder:

```bash
cd lms_dt3-307785-309185/CoreAPI&Services
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### Configure environment

Copy the example env file:

```bash
cp .env.example .env
```

Then edit `.env` as needed. For local development with the frontend, the default in `.env.example` already allows `http://localhost:3000` via `ALLOWED_ORIGINS`.

If you want Mongo-backed endpoints, set:

- `MONGODB_URI=mongodb://localhost:27017` (or your connection string)

#### Run the API server

From `CoreAPI&Services/`:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload
```

Open:

- `http://localhost:3001/docs` (Swagger UI)
- `http://localhost:3001/openapi.json`

#### Seed sample data (MongoDB)

Seeding is idempotent and only affects documents tagged as seeded.

From `CoreAPI&Services/` (with `MONGODB_URI` set):

```bash
python -m app.scripts.seed
```

To clear seeded data (does not drop collections or indexes):

```bash
python -m app.scripts.clear_db
```

#### Run backend tests

From `CoreAPI&Services/`:

```bash
pytest -q
```

### 2) Frontend: WebAppFrontend (port 3000)

The frontend lives in a different workspace folder:

```bash
cd lms_dt3-307785-309184/WebAppFrontend
```

Install dependencies:

```bash
npm install
```

Run dev server (Create React App):

```bash
npm run start
```

By default, `react-scripts start` runs on `http://localhost:3000`.

If the backend is running on `http://localhost:3001`, you will typically either:
- configure a dev proxy (not currently present in `package.json`), or
- call the backend directly (and rely on backend CORS allowing `http://localhost:3000`).

## CORS configuration notes (backend)

CORS middleware is configured in `CoreAPI&Services/app/main.py` using values from settings:

- `allow_origins=settings.allowed_origins`
- `allow_methods=settings.allowed_methods`
- `allow_headers=settings.allowed_headers`
- `allow_credentials=True`
- `max_age=settings.cors_max_age`

### How `ALLOWED_ORIGINS`, `ALLOWED_HEADERS`, `ALLOWED_METHODS` are parsed

In `CoreAPI&Services/app/core/config.py`, list-like env vars use a custom parser that supports:

1) JSON arrays, for example:
```text
ALLOWED_ORIGINS=["https://example.com","http://localhost:3000"]
```

2) CSV strings, for example:
```text
ALLOWED_ORIGINS=https://example.com, http://localhost:3000
ALLOWED_HEADERS=Content-Type,Authorization,X-Requested-With
ALLOWED_METHODS=GET,POST,PUT,DELETE,PATCH,OPTIONS
```

Behavior details:
- Empty strings become an empty list.
- Whitespace is trimmed.
- If a value “looks like” a JSON array (`[...]`) but JSON decoding fails, it falls back to CSV parsing.
- If a non-string, non-list value is provided, it is stringified and treated as a single-item list.

This makes it safe to use simple `.env` CSV values while still supporting JSON arrays in more structured environments.

## Command reference

### Backend (CoreAPI&Services)

From `lms_dt3-307785-309185/CoreAPI&Services/`:

- Run server:
  - `uvicorn app.main:app --host 0.0.0.0 --port 3001 --reload`
- Run tests:
  - `pytest -q`
- Lint / format:
  - `ruff check .`
  - `black .`
- Seed / clear seeded data:
  - `python -m app.scripts.seed`
  - `python -m app.scripts.clear_db`

### Frontend (WebAppFrontend)

From `lms_dt3-307785-309184/WebAppFrontend/`:

- Run dev server:
  - `npm run start`
- Build:
  - `npm run build`
- Test:
  - `npm run test`
- Lint:
  - `npm run lint`
  - `npm run lint:fix`
- Format:
  - `npm run format`

## Troubleshooting

### Backend: `/health/db` shows `MongoDB is not initialized on app.state`

This happens when MongoDB is disabled because `MONGODB_URI` is not set. Set `MONGODB_URI` in `CoreAPI&Services/.env` and restart the server.

### Seed/clear scripts fail with “MongoDB is not configured”

The scripts `python -m app.scripts.seed` and `python -m app.scripts.clear_db` require `MONGODB_URI` to be set (and optionally `MONGODB_DBNAME`, `MONGODB_TLS`). Update `.env` and rerun.

### Changing `AUTH_STUB` does not seem to take effect

The backend settings are cached via `get_settings()` for performance. In tests, the code clears this cache explicitly.

For local development, if you change `AUTH_STUB` (or other env vars), restart uvicorn so settings are reloaded.

### Frontend cannot call the backend (CORS errors)

Confirm:
- Frontend is running on `http://localhost:3000`
- Backend `.env` includes `ALLOWED_ORIGINS=http://localhost:3000` (or includes it in the JSON array / CSV list)
- Backend was restarted after changing `.env`

Task completed: Root-level README updated with env vars, local run instructions, CORS parsing notes, command reference, and troubleshooting, linking to the API summary.
