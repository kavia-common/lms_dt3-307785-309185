# CoreAPI&Services API Summary

This document summarizes the **currently implemented** backend endpoints in the `CoreAPI&Services` container (FastAPI). It focuses on route paths, request parameters/bodies, response shapes, and relevant environment variables.

## Conventions

All responses are JSON.

When an endpoint raises `fastapi.HTTPException`, the service applies a standardized error envelope via global exception handlers.

### Standard error response (for HTTPException)

**Shape**
```json
{
  "error": "http_error",
  "message": "Human readable error message",
  "details": { "status_code": 404 },
  "request_id": "optional"
}
```

**Notes**
The `request_id` field is populated from request headers `X-Request-Id` or `X-Correlation-Id` when present.

### Pagination parameters

List endpoints support query parameters:
- `skip` (integer, default `0`, minimum `0`): pagination offset.
- `limit` (integer, default `50`, minimum `1`, maximum `200`): page size.

## Health and readiness

### GET `/healthz`

**Description**
Liveness probe that confirms the process is running.

**Request**
No parameters.

**Responses**
- `200 OK`
  ```json
  {
    "status": "ok",
    "service": "coreapi"
  }
  ```

### GET `/readyz`

**Description**
Readiness probe. Currently returns `ok` without performing downstream checks.

**Request**
No parameters.

**Responses**
- `200 OK`
  ```json
  {
    "status": "ok",
    "service": "coreapi"
  }
  ```

### GET `/health/db`

**Description**
MongoDB connectivity probe. Performs a MongoDB ping (`db.command({ ping: 1 })`) and returns `ok` or `failed` along with latency and an error message when applicable.

**Request**
No parameters.

**Responses**
- `200 OK` (connectivity ok)
  ```json
  {
    "status": "ok",
    "duration_ms": 3.14,
    "error": null
  }
  ```
- `200 OK` (connectivity failed)
  ```json
  {
    "status": "failed",
    "duration_ms": 2.71,
    "error": "MongoDB is not initialized on app.state"
  }
  ```

**Environment variables affecting behavior**
- `MONGODB_URI`: when not set, MongoDB lifecycle initialization is disabled and `/health/db` will report `status=failed` with an error similar to `MongoDB is not initialized on app.state`.
- `MONGODB_DBNAME` (default `lms`)
- `MONGODB_TLS` (default `false`)

## Auth (stub)

### GET `/auth/debug`

**Description**
Debug endpoint that returns the resolved current principal.

Behavior depends on whether auth stub mode is enabled.

**Request**
No body.

Optional request headers (only used when `AUTH_STUB=true`):
- `X-Auth-Subject`: overrides the returned `subject` (defaults to `stub-user`).
- `X-Auth-Email`: sets the returned `email` (optional).
- `X-Auth-Roles`: comma-separated roles. Example: `Learner,Admin`.

**Responses**
- `200 OK` (when `AUTH_STUB=true`)
  ```json
  {
    "subject": "user-123",
    "roles": ["Learner", "Admin"],
    "email": "user@example.com"
  }
  ```
- `400 Bad Request` (when `AUTH_STUB=true` and role parsing fails)
  ```json
  {
    "error": "http_error",
    "message": "Unknown role: NotARole",
    "details": { "status_code": 400 },
    "request_id": null
  }
  ```
- `501 Not Implemented` (when `AUTH_STUB=false`)
  ```json
  {
    "error": "http_error",
    "message": "Authentication is not implemented yet.",
    "details": { "status_code": 501 },
    "request_id": null
  }
  ```

**Environment variables affecting behavior**
- `AUTH_STUB` (default `true`): when `false`, the endpoint returns `501 Not Implemented` until real OIDC validation is implemented.

## Domain routers

All domain endpoints are currently **unauthenticated** (no access control enforced in the routers yet). The routers delegate to MongoDB-backed services and use soft-delete semantics (records with `deleted_at != null` are excluded from list/get operations).

Timestamps are returned as ISO-8601 strings by FastAPI/Pydantic.

### Users

#### GET `/users`

**Description**
List users with pagination.

**Query parameters**
- `skip` (int, default 0, min 0)
- `limit` (int, default 50, min 1, max 200)

**Responses**
- `200 OK`
  ```json
  {
    "items": [
      {
        "id": "507f1f77bcf86cd799439011",
        "name": "Alice Example",
        "email": "alice@example.com",
        "created_at": "2026-01-21T12:00:00+00:00",
        "updated_at": "2026-01-21T12:00:00+00:00",
        "deleted_at": null
      }
    ],
    "total": 1,
    "skip": 0,
    "limit": 50
  }
  ```

#### POST `/users`

**Description**
Create a user.

**Request body**
```json
{
  "name": "Bob Example",
  "email": "bob@example.com"
}
```

**Responses**
- `201 Created`
  ```json
  {
    "id": "507f1f77bcf86cd799439011",
    "name": "Bob Example",
    "email": "bob@example.com",
    "created_at": "2026-01-21T12:00:00+00:00",
    "updated_at": "2026-01-21T12:00:00+00:00",
    "deleted_at": null
  }
  ```
- `409 Conflict` (email already exists)
  ```json
  {
    "error": "http_error",
    "message": "A user with this email already exists.",
    "details": { "status_code": 409 },
    "request_id": null
  }
  ```

#### GET `/users/{user_id}`

**Description**
Fetch a single user by id.

**Path parameters**
- `user_id` (string): expected to be a MongoDB ObjectId string.

**Responses**
- `200 OK` (same shape as `UserRead`)
- `404 Not Found` (invalid ObjectId or missing record)
  ```json
  {
    "error": "http_error",
    "message": "User not found.",
    "details": { "status_code": 404 },
    "request_id": null
  }
  ```

#### PUT `/users/{user_id}`

**Description**
Update a user by id. Fields are optional; a no-op update returns the current record.

**Path parameters**
- `user_id` (string): MongoDB ObjectId string.

**Request body**
```json
{
  "name": "Updated Name",
  "email": "updated@example.com"
}
```
All fields are optional; omit fields you do not want to change.

**Responses**
- `200 OK` (updated `UserRead`)
- `404 Not Found` (invalid ObjectId or missing record)
- `409 Conflict` (email would collide with another user)

#### DELETE `/users/{user_id}`

**Description**
Soft-delete a user by id.

**Path parameters**
- `user_id` (string): MongoDB ObjectId string.

**Responses**
- `200 OK`
  ```json
  { "deleted": true, "id": "507f1f77bcf86cd799439011" }
  ```
- `404 Not Found` (invalid ObjectId or missing record)

### Content

#### GET `/content`

**Description**
List content items with pagination.

**Query parameters**
- `skip` (int, default 0, min 0)
- `limit` (int, default 50, min 1, max 200)

**Responses**
- `200 OK`
  ```json
  {
    "items": [
      {
        "id": "507f1f77bcf86cd799439012",
        "title": "Intro to DigitalT3",
        "slug": "intro-to-digitalt3",
        "created_at": "2026-01-21T12:00:00+00:00",
        "updated_at": "2026-01-21T12:00:00+00:00",
        "deleted_at": null
      }
    ],
    "total": 1,
    "skip": 0,
    "limit": 50
  }
  ```

#### POST `/content`

**Description**
Create a content item.

**Request body**
```json
{
  "title": "LMS Basics",
  "slug": "lms-basics"
}
```

**Key validation**
- `slug` must match the pattern `^[a-z0-9]+(?:-[a-z0-9]+)*$` (kebab-case).

**Responses**
- `201 Created` (same shape as `ContentRead`)

#### GET `/content/{content_id}`

**Description**
Fetch a single content item by id.

**Path parameters**
- `content_id` (string): expected MongoDB ObjectId string.

**Responses**
- `200 OK` (same shape as `ContentRead`)
- `404 Not Found` (invalid ObjectId or missing record)
  ```json
  {
    "error": "http_error",
    "message": "Content not found.",
    "details": { "status_code": 404 },
    "request_id": null
  }
  ```

#### PUT `/content/{content_id}`

**Description**
Update a content item by id. Fields are optional; a no-op update returns the current record.

**Path parameters**
- `content_id` (string): MongoDB ObjectId string.

**Request body**
```json
{
  "title": "Updated Title",
  "slug": "updated-slug"
}
```
All fields are optional.

**Responses**
- `200 OK` (updated `ContentRead`)
- `404 Not Found` (invalid ObjectId or missing record)

#### DELETE `/content/{content_id}`

**Description**
Soft-delete a content item by id.

**Path parameters**
- `content_id` (string): MongoDB ObjectId string.

**Responses**
- `200 OK`
  ```json
  { "deleted": true, "id": "507f1f77bcf86cd799439012" }
  ```
- `404 Not Found` (invalid ObjectId or missing record)

### Assessments

#### GET `/assessments`

**Description**
List assessments with pagination.

**Query parameters**
- `skip` (int, default 0, min 0)
- `limit` (int, default 50, min 1, max 200)

**Responses**
- `200 OK`
  ```json
  {
    "items": [
      {
        "id": "507f1f77bcf86cd799439013",
        "title": "Quiz: LMS Basics",
        "course_id": "507f1f77bcf86cd799439099",
        "module_id": null,
        "created_at": "2026-01-21T12:00:00+00:00",
        "updated_at": "2026-01-21T12:00:00+00:00",
        "deleted_at": null
      }
    ],
    "total": 1,
    "skip": 0,
    "limit": 50
  }
  ```

#### POST `/assessments`

**Description**
Create an assessment.

**Request body**
```json
{
  "title": "Quiz 1",
  "course_id": "507f1f77bcf86cd799439099",
  "module_id": null
}
```

**Notes**
- `course_id` and `module_id` are optional strings (documented as “string form of ObjectId”, but not currently validated as ObjectId).

**Responses**
- `201 Created` (same shape as `AssessmentRead`)

#### GET `/assessments/{assessment_id}`

**Description**
Fetch a single assessment by id.

**Path parameters**
- `assessment_id` (string): expected MongoDB ObjectId string.

**Responses**
- `200 OK` (same shape as `AssessmentRead`)
- `404 Not Found` (invalid ObjectId or missing record)
  ```json
  {
    "error": "http_error",
    "message": "Assessment not found.",
    "details": { "status_code": 404 },
    "request_id": null
  }
  ```

#### PUT `/assessments/{assessment_id}`

**Description**
Update an assessment by id. Fields are optional; a no-op update returns the current record.

**Path parameters**
- `assessment_id` (string): MongoDB ObjectId string.

**Request body**
```json
{
  "title": "Updated Quiz Title",
  "course_id": "507f1f77bcf86cd799439099",
  "module_id": null
}
```
All fields are optional.

**Responses**
- `200 OK` (updated `AssessmentRead`)
- `404 Not Found` (invalid ObjectId or missing record)

#### DELETE `/assessments/{assessment_id}`

**Description**
Soft-delete an assessment by id.

**Path parameters**
- `assessment_id` (string): MongoDB ObjectId string.

**Responses**
- `200 OK`
  ```json
  { "deleted": true, "id": "507f1f77bcf86cd799439013" }
  ```
- `404 Not Found` (invalid ObjectId or missing record)

## Related environment variables (non-exhaustive)

These values are defined in service settings and affect runtime behavior.

### API runtime
- `HOST` (default `0.0.0.0`)
- `PORT` (default `3001`)
- `APP_ENV` (default `development`)
- `TRUST_PROXY` (default `false`)

### Logging
- `LOG_LEVEL` (default `INFO`)
- `LOG_FORMAT` (default `auto`, which uses JSON in production-like environments)

### CORS
- `ALLOWED_ORIGINS` (default `[]`)
- `ALLOWED_HEADERS` (default includes `Content-Type`, `Authorization`, `X-Requested-With`)
- `ALLOWED_METHODS` (default includes `GET`, `POST`, `PUT`, `DELETE`, `PATCH`, `OPTIONS`)
- `CORS_MAX_AGE` (default `3600`)

### MongoDB
- `MONGODB_URI` (enables MongoDB when set)
- `MONGODB_DBNAME` (default `lms`)
- `MONGODB_TLS` (default `false`)

### Auth scaffolding
- `AUTH_STUB` (default `true`)

## Quick reference

- Health:
  - `GET /healthz`
  - `GET /readyz`
  - `GET /health/db`
- Auth:
  - `GET /auth/debug`
- Domain:
  - Users: `GET /users`, `POST /users`, `GET /users/{id}`, `PUT /users/{id}`, `DELETE /users/{id}`
  - Content: `GET /content`, `POST /content`, `GET /content/{id}`, `PUT /content/{id}`, `DELETE /content/{id}`
  - Assessments: `GET /assessments`, `POST /assessments`, `GET /assessments/{id}`, `PUT /assessments/{id}`, `DELETE /assessments/{id}`
