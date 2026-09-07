# Project Decisions

## Purpose

A full-stack employee leave and attendance management system covering employee records, daily check-in/check-out, leave requests and leave balances, role-based dashboards, and an audit trail.

## Technology Stack

| Area | Choice |
| --- | --- |
| Backend | Python 3.10, FastAPI, SQLAlchemy 2.0, Alembic |
| Database | PostgreSQL |
| Frontend | React 19 (Vite 8), plain CSS — no TypeScript, no UI framework |
| Authentication | JWT (HS256) bearer tokens via FastAPI OAuth2 password flow |
| Password hashing | Argon2 (pwdlib) |
| Testing | pytest (backend), ESLint + production build (frontend) |
| Infrastructure | Docker Compose (backend + PostgreSQL), GitHub Actions CI, GitHub-hosted repo |

## Domain decisions

- An employee profile links to at most one user account. Employees self-register their login account; admins are created exclusively by the CLI bootstrap script.
- Leave balances are seeded per employee: vacation 15, sick 15, emergency 5, other 0 days.
- Approving a leave request deducts the requested days from the balance; cancelling an approved request restores them; rejecting does not change the balance.
- Approval is rejected when the requested dates overlap an existing attendance record, when the employee is inactive, or when the balance is insufficient.
- Check-in/check-out is blocked while the employee is on approved leave.
- Deactivating an employee is a soft delete (status becomes `inactive`).
- No dedicated departments table: `department` is a field on the employee record.
- Every significant action is written to the audit log.
- Local development stays Docker Compose-based; the production deployment targets Render with Supabase PostgreSQL (see "Production Deployment" below).

## Production Deployment

- React frontend deployed as a Render Static Site.
- FastAPI backend deployed as a Render Docker Web Service.
- PostgreSQL hosted on Supabase.
- The Supabase Session Pooler is used for the Render backend because Render's environment is IPv4-oriented.
- The database schema is created using the existing Alembic migrations.
- Production frontend/backend URLs are configured through environment variables.
- No cloud deployment existed before this deployment work.

## Development Approach

REST API and database first, then the React frontend, then Docker and CI. Features are built on short-lived branches and merged into `main`, which is always stable.

## Git Workflow

- `main` is the stable branch.
- Features are developed on `feature/*` branches.
- Commit messages follow conventional-commit style.