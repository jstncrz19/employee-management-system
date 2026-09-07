# Employee Management System

A full-stack employee management system for tracking employees, attendance, leave requests, leave balances, audit logs, and role-based admin/employee dashboards.

The backend is a FastAPI REST API backed by PostgreSQL. The frontend is a React (Vite) single-page application.

## CI

[![Backend CI](https://github.com/jstncrz19/employee-management-system/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/jstncrz19/employee-management-system/actions/workflows/backend-ci.yml)
[![Frontend CI](https://github.com/jstncrz19/employee-management-system/actions/workflows/frontend-ci.yml/badge.svg)](https://github.com/jstncrz19/employee-management-system/actions/workflows/frontend-ci.yml)

## Features

### Authentication & Roles

- JWT-based authentication with Argon2 password hashing
- Role-based authorization (`admin` vs `employee`)
- Self-service registration creates an employee account, linked employee profile, and default leave balances
- No public route allows registering an admin account; the initial admin is created with a CLI script (see [Admin Account Setup](#admin-account-setup))

### Employees

- Admin CRUD for employees (create, update, deactivate)
- Employee account provisioning (email + password) for employees without an account
- Self-service employee profile endpoints
- Search, status/department filters, sorting, and pagination
- Prevents duplicate employee numbers/emails (HTTP 409)

### Attendance

- Employee check-in / check-out (one record per employee per day)
- Check-in is blocked while the employee is on approved leave
- Employee attendance history
- Admin attendance list with employee/date-range filters, search, and pagination

### Leave Management

- Employee leave request creation (vacation, sick, emergency, other)
- Admin approval and rejection; employee cancellation
- Overlapping leave requests are rejected
- Approving consumes the leave balance; cancellation restores it; rejection does not change the balance
- Approving a leave that overlaps an existing attendance record is rejected
- Leave balances per type with admin management (total days cannot drop below used days)
- Leave list filtering (status, employee, type, date range, search), sorting, and pagination

### Dashboards

- Admin dashboard: total/active employees, present/absent employees, employees on leave, pending leave requests
- Employee dashboard: today's attendance, leave balances, pending leaves, upcoming approved leaves, recent attendance

### Audit Logging

- Every significant action (create, update, approve, reject, cancel, check-in/out, register, deactivate) is written to an audit log
- Admin-only audit log viewer with user/employee/action/entity filters, sorting, and pagination

### API Quality

- Pydantic request/response validation (422 on invalid input)
- Consistent error semantics: 400 (invalid business logic), 401 (unauthenticated), 403 (forbidden), 404 (not found), 409 (conflict)
- Filtering, sorting, and pagination across list endpoints
- Automatic OpenAPI documentation
- 228 automated API tests run in CI

## Tech Stack

### Backend

- Python 3.10
- FastAPI
- SQLAlchemy 2.0 (ORM)
- Pydantic v2 (validation / schemas)
- Alembic (database migrations)
- PostgreSQL
- JWT (PyJWT) + Argon2 (pwdlib) authentication
- pytest (test suite)

### Frontend

- React 19
- Vite
- React Router
- Axios

### Infrastructure

- Docker / Docker Compose
- GitHub Actions (Backend CI + Frontend CI)

## Architecture

```text
                 +-------------------+
                 |   React SPA       |
                 |   (Vite, /:5173)  |
                 +---------+---------+
                           |  HTTP / JSON (JWT in Authorization header)
                           v
                 +-------------------+
                 |   FastAPI API     |
                 |   (uvicorn, /:8000)|
                 +---------+---------+
                           |
              +------------+------------+
              |                         |
        +-----v------+           +------v------+
        |  Routers   |           | Auth/RBAC   |
        |  Schemas   |           | Security    |
        +-----+------+           +------+------+
              |                         |
              +------------+------------+
                           |
              +------------v------------+
              |      SQLAlchemy ORM      |
              |  + Audit logging hooks   |
              +------------+------------+
                           |
              +------------v------------+
              |      PostgreSQL          |
              +-------------------------+
```

- **Routers** (`backend/app/routers/`) — HTTP layer: auth, users, employees, attendance, leaves, dashboard, audit-logs
- **Schemas** (`backend/app/schemas/`) — Pydantic request/response models
- **Models** (`backend/app/models/`) — SQLAlchemy ORM models
- **Core** (`backend/app/core/`) — security (JWT, password hashing, dependency guards), audit logging, timezone-aware `now()`
- **Config** (`backend/config.py`) — environment-driven configuration
- **Migrations** (`backend/alembic/`) — versioned database migrations

## Database

Tables (managed by Alembic):

- `users` — accounts with email, Argon2 password hash, role
- `employees` — employee profiles linked to users (optional for admins)
- `attendance` — one record per employee per day
- `leaves` — leave requests
- `leave_balances` — per-employee, per-type balances
- `audit_logs` — audit trail
- `alembic_version` — migration bookkeeping

## Authentication & Authorization

### How it works

1. `POST /auth/login` with email + password returns a signed JWT access token (default 30-minute expiry, configurable).
2. The frontend stores the token and sends it as `Authorization: Bearer <token>`.
3. A token can be created for any account; `GET /users/me` returns the current account's id, email, and role.

### Roles

| Role | What it can do |
| --- | --- |
| `admin` | Everything: employee management, approve/reject leaves, admin attendance, dashboards, audit logs, leave balances. Admins do not need an employee profile. |
| `employee` | Self-service only: own attendance, own leaves, own balances, own dashboard. |

### Error semantics

- `401` — missing, invalid, or expired token, or bad login credentials
- `403` — authenticated but not authorized for the endpoint (e.g., employee calling an admin endpoint)
- `422` — request body/query failed Pydantic validation

### Registering accounts

- `POST /auth/register` — creates an **employee** account plus linked profile and default leave balances (vacation 15, sick 15, emergency 5, other 0). It never creates admin accounts.
- Admins can provision an employee account via `POST /employees/{employee_id}/account` (email + password).

## Key Workflows

### Leave workflow

1. Employee submits a leave request (type, start date, end date, reason). Overlapping requests are rejected.
2. Admin approves or rejects: approving consumes `used_days` from the balance and is blocked if insufficient days remain or if the leave overlaps an attendance record; rejection leaves the balance unchanged.
3. The employee can cancel a request. Cancelling an approved request restores the deducted days; pending requests have no balance impact.
4. Each step (create, approve, reject, cancel) is recorded in the audit log.

### Attendance workflow

1. Employee checks in (once per day). Check-in is blocked while on approved leave.
2. Employee checks out.
3. Employees see their own history; admins see all records with filters and search.

### Audit logging

- `app/core/audit.py` centralizes log creation.
- Every audited action records the acting user, action, entity type/id, details, and timestamp.
- Admins review logs via `GET /audit-logs`.

### Search / filter / sort / pagination

- List endpoints (`/employees`, `/attendance`, `/leaves`, `/audit-logs`) support a consistent pattern:
  - **Search** — text match on relevant fields (`search`)
  - **Filters** — optional query parameters (status, department, date ranges, entity/action, ...)
  - **Sorting** — `sort_by` + `sort_order` on whitelisted fields
  - **Pagination** — `page` + `limit`, with total count and page metadata in the response

## API Reference

All routers are tagged, so the full interactive documentation is generated automatically:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

Click **Authorize** in Swagger UI and paste the `access_token` from `POST /auth/login` (used as a bearer token), or send `Authorization: Bearer <token>` on any protected endpoint. Unauthenticated requests return `401`; an employee calling an admin-only endpoint (or an admin using an employee-only endpoint) returns `403`. Each endpoint's role requirement and real response codes are documented inline, so the interactive docs are the source of truth.

### Endpoint summary

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| GET | `/` | Public | API banner |
| GET | `/health` | Public | Health check |
| POST | `/auth/register` | Public | Register an employee account + profile + balances |
| POST | `/auth/login` | Public | Exchange credentials for a JWT |
| GET | `/users/me` | Authenticated | Current account (id, email, role) |
| POST | `/employees` | Admin | Create employee |
| POST | `/employees/{employee_id}/account` | Admin | Provision an account for an employee |
| GET | `/employees` | Admin | List with search/filter/sort/pagination |
| GET | `/employees/{employee_id}` | Admin | Get one employee |
| PATCH | `/employees/{employee_id}` | Admin | Update employee |
| DELETE | `/employees/{employee_id}` | Admin | Deactivate employee |
| GET | `/employees/me` | Employee | Own employee profile |
| PATCH | `/employees/me` | Employee | Update own profile |
| POST | `/attendance/check-in` | Employee | Check in |
| POST | `/attendance/check-out` | Employee | Check out |
| GET | `/attendance/me` | Employee | Own attendance history |
| GET | `/attendance` | Admin | All attendance with filters/search/pagination |
| POST | `/leaves` | Employee | Create leave request |
| GET | `/leaves/me` | Employee | Own leave requests |
| GET | `/leaves` | Admin | All leave requests with filters/sort/pagination |
| GET | `/leaves/balance/me` | Employee | Own leave balances |
| GET | `/leaves/balance/{employee_id}` | Admin | An employee's leave balances |
| PATCH | `/leaves/balance/{employee_id}/{leave_type}` | Admin | Update a balance's total days |
| PATCH | `/leaves/{leave_id}/cancel` | Employee | Cancel own request |
| PATCH | `/leaves/{leave_id}/approve` | Admin | Approve request |
| PATCH | `/leaves/{leave_id}/reject` | Admin | Reject request |
| GET | `/dashboard/me` | Employee | Employee dashboard data |
| GET | `/dashboard/summary` | Admin | Admin dashboard summary |
| GET | `/audit-logs` | Admin | View audit logs |

## Project Structure

```text
employee-management-system/
├── backend/
│   ├── app/
│   │   ├── core/          # security, audit, permissions, time
│   │   ├── models/        # SQLAlchemy models
│   │   ├── routers/       # FastAPI route handlers
│   │   └── schemas/       # Pydantic models
│   ├── alembic/           # database migrations
│   ├── scripts/           # admin bootstrap CLI
│   ├── tests/             # pytest suite
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/    # shared UI (Navbar, guards, states, badges)
│   │   ├── context/       # auth state
│   │   ├── hooks/         # useAuth
│   │   ├── pages/         # Login, dashboards, tables, forms
│   │   ├── services/      # API client, token helpers
│   │   └── utils/         # error message helpers
│   ├── index.html
│   └── package.json
├── .github/workflows/     # CI pipelines
├── docker-compose.yml
├── LICENSE
└── README.md
```

## Getting Started

### Prerequisites

Only two tools are required:

- [Docker](https://docs.docker.com/get-docker/) (with Docker Compose)
- Git

Python, Node.js, and PostgreSQL are **not** needed for the Docker workflow — they run inside containers. Node.js is only needed if you prefer to run the frontend outside Docker (see [Frontend Setup](#frontend-setup)).

### 1. Environment variables

Copy the example environment file into place:

```bash
cp .env.example .env
```

Edit `.env` and set at least:

```dotenv
POSTGRES_PASSWORD=change-this-password
JWT_SECRET_KEY=change-this-to-a-long-random-secret
```

`docker compose` reads this `.env` automatically. Never commit it (`.env` is git-ignored).

### 2. Start the backend and database

```bash
docker compose up -d
```

This starts:

- `backend` — the FastAPI app on `http://localhost:8000`
- `postgres` — the database

Check the containers:

```bash
docker compose ps
```

### 3. Apply database migrations

```bash
docker compose exec backend alembic upgrade head
```

### 4. Create the initial admin account

Registration only creates **employee** accounts, so a fresh installation has no admin. Create one now (this script only works until the first admin exists):

```bash
docker compose exec backend python -m scripts.create_admin \
  --email admin@example.com \
  --password 'choose-a-strong-password'
```

Naming the `--password` argument is not required; the script prompts interactively if it is omitted:

```bash
docker compose exec backend python -m scripts.create_admin --email admin@example.com
```

The script uses the standard password-hashing and authentication system. It refuses to run a second time (once an admin exists) and refuses emails already in use.

#### Admin account with a linked employee profile

An admin can also act as an employee, for example using the self-service "My Leaves" features. To have the script create the linked employee profile when the admin account is created, provide the employee information explicitly (it is never inferred from the email address; the admin's email is reused as the employee email and default leave balances are seeded):

```bash
docker compose exec backend python -m scripts.create_admin \
  --email admin@example.com \
  --password 'choose-a-strong-password' \
  --employee-number 10000 \
  --first-name Jane \
  --last-name Doe \
  --department Administration \
  --position Administrator \
  --date-hired 2026-09-01
```

#### Linking a profile to an existing admin account

If an admin was created earlier without a profile (for example in an existing deployment), link a profile to that admin without creating a new user account.

To fix an existing production admin (whose account lives in the Supabase database), run a one-off container and temporarily point `DATABASE_URL` at the Supabase Session Pooler connection string. Fill in the `USER`/`PASSWORD`/`HOST` placeholders locally — the actual Supabase password and host belong only on your command line, never in the repository:

```bash
docker compose run --rm \
  -e DATABASE_URL="postgresql+psycopg://USER:PASSWORD@HOST:5432/postgres?sslmode=require" \
  backend python -m scripts.create_admin \
  --link-existing \
  --email admin@example.com \
  --employee-number 10000 \
  --first-name Jane \
  --last-name Doe \
  --department Administration \
  --position Administrator \
  --date-hired 2026-09-01
```

Only `DATABASE_URL` must point at the Supabase database; the rest of the container environment is taken from the local `.env` and is not used for this operation. The command runs against the production database, so only run it when you intend to modify production. For the local Docker database, omit the `-e DATABASE_URL=...` override and use `docker compose exec backend` instead.

`--link-existing` never modifies the user account, its password, or its role; it only creates the employee profile and leave balances. It does not require or use `--password` in this mode. It refuses to run if the user is not an admin, already has a linked profile, or if the employee number/email is already in use.

### 5. Run the frontend

See [Frontend Setup](#frontend-setup). With the API running on port 8000, the frontend on port 5173 can be started with:

```bash
cd frontend
npm install
npm run dev
```

Then open `http://localhost:5173`. Log in as the admin created in step 4, or register a new employee account from the login page.

### 6. Verify it works

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health check: `http://localhost:8000/health`

## Frontend Setup

The frontend is a React SPA in `frontend/` that talks to the FastAPI backend over HTTP with a bearer token.

```bash
cd frontend
npm install
npm run dev        # development server on http://localhost:5173
npm run lint       # ESLint
npm run build      # production build to frontend/dist
```

### Frontend environment

```dotenv
VITE_API_BASE_URL=http://localhost:8000
```

Set it in `frontend/.env` (see `frontend/.env.example`) only if the API is not at `http://localhost:8000`.

### Frontend routes

| Path | Access | Page |
| --- | --- | --- |
| `/login` | Public | Login / register |
| `/admin` | Admin | Admin dashboard |
| `/employees` | Admin | Employee management |
| `/admin/attendance` | Admin | Attendance records |
| `/admin/leaves` | Admin | Leave requests (approve/reject) |
| `/admin/audit-logs` | Admin | Audit log viewer |
| `/dashboard` | Employee | Employee dashboard |
| `/leaves` | Admin + Employee | My leaves / leave balances |

## Backend Setup Without Docker

Optional — only needed if you want the backend on your host instead of in Docker.

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate     Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then edit DATABASE_URL / JWT_SECRET_KEY
alembic upgrade head
uvicorn main:app --reload
```

The backend `.env` (for local runs) uses a `DATABASE_URL` such as `postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/employee_management`.

## Environment Variables

### Root `.env` (used by Docker Compose)

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `POSTGRES_DB` | — | `employee_management` | PostgreSQL database name |
| `POSTGRES_USER` | — | `postgres` | PostgreSQL user |
| `POSTGRES_PASSWORD` | Yes | — | PostgreSQL password |
| `JWT_SECRET_KEY` | Yes | — | Secret used to sign/verify JWTs (use a long random value) |
| `JWT_ALGORITHM` | — | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | — | `30` | Access token lifetime in minutes |
| `CORS_ORIGINS` | — | `http://localhost:5173` | Comma-separated allowed CORS origins |

### Backend `.env` (only for running backend outside Docker)

| Variable | Required | Description |
| --- | --- | --- |
| `DATABASE_URL` | Yes | SQLAlchemy connection string |
| `JWT_SECRET_KEY` | Yes | JWT signing secret |
| `JWT_ALGORITHM` | No | Default `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Default `30` |
| `CORS_ORIGINS` | No | Default `http://localhost:5173` |

### Frontend `.env`

| Variable | Default | Description |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `http://localhost:8000` | Base URL of the FastAPI backend |

## Deployment

### Production architecture

```text
React/Vite  →  Render Static Site  →  Render FastAPI Docker Web Service  →  Supabase PostgreSQL
```

### Backend production environment variables

Configure these in the Render Web Service environment:

| Variable | Required | Description |
| --- | --- | --- |
| `DATABASE_URL` | Yes | SQLAlchemy connection string for Supabase PostgreSQL |
| `JWT_SECRET_KEY` | Yes | Secret used to sign/verify JWTs (use a long random value) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Defaults to `30` |
| `CORS_ORIGINS` | No | Comma-separated allowed origins; set to the Render frontend URL |

`DATABASE_URL` uses the SQLAlchemy psycopg format:

```text
postgresql+psycopg://USER:PASSWORD@HOST:5432/postgres?sslmode=require
```

If the database password contains URL-reserved characters, it must be URL-encoded.

### Frontend production environment variable

| Variable | Description |
| --- | --- |
| `VITE_API_BASE_URL` | URL of the deployed backend (embedded into the build) |

### Deployment sequence

1. Create/configure the Supabase PostgreSQL project.
2. Configure the Render backend environment variables.
3. Deploy the backend.
4. Run `alembic upgrade head` against the production Supabase database.
5. Verify `/health` and `/docs`.
6. Configure `CORS_ORIGINS` with the actual Render frontend URL.
7. Deploy the React frontend as a Render Static Site.
8. Set `VITE_API_BASE_URL` to the deployed backend URL.
9. Verify login and core application flows.

Secrets must be configured through Render environment variables and must never be committed to Git.

## Testing

The backend has **228 passing tests** covering authentication, authorization, validation, business logic, defensive branches, and the admin bootstrap script. CI runs the suite against a real PostgreSQL service on every push and pull request.

```bash
docker compose exec backend pytest -q
```

### What the suite covers

- Authentication and registration (including conflict/validation branches)
- Authorization regression matrix: unauthenticated → 401, employee → admin endpoint 403, admin → employee endpoint 403
- Employee CRUD, lifecycle, account provisioning, duplicate protection, filtering/sorting/pagination
- Attendance check-in/out, duplicate rejection, approved-leave blocking, filters/pagination
- Leave create/approve/reject/cancel, balance consumption & restoration, overlap & date validation, insufficient-balance rejection
- Dashboards (admin + employee)
- Audit log endpoints and audit trail generation
- `GET /users/me` (including invalid/expired tokens)
- Admin bootstrap script safeguards

## Docker Development Workflow

```bash
docker compose up -d                       # start backend + postgres
docker compose exec backend alembic upgrade head
docker compose logs -f backend             # follow backend logs
docker compose ps                          # container status
docker compose down                        # stop (data persists in the volume)
docker compose down -v                     # stop AND delete the database volume
```

> `docker compose down -v` deletes all data. Use with care.

### Rebuilding after code changes

```bash
docker compose build backend
docker compose up -d backend
```

## Notes

- `.env` files are git-ignored; the repository only tracks `.env.example` templates.
- Application timezone is set to `Asia/Manila` in `backend/config.py`.
- Access tokens expire (default 30 minutes) and the frontend redirects to `/login` on a 401.