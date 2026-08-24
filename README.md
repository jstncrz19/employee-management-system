# Employee Management System

A backend REST API for managing employees, attendance, leave requests, leave balances, authentication, dashboards, and audit logs.

Built with FastAPI, PostgreSQL, SQLAlchemy, Alembic, JWT authentication, and Docker.

## Features

- JWT-based authentication
- Role-based authorization
- Employee management
- Employee account provisioning
- Employee profile management
- Attendance check-in and check-out
- Attendance history
- Leave request management
- Leave approval and rejection
- Leave cancellation
- Leave balance tracking
- Admin leave balance management
- Admin dashboard
- Employee dashboard
- Audit logging
- Filtering, sorting, and pagination
- Employee account lifecycle protection
- Dockerized development environment
- Automated API testing with pytest

## Tech Stack

- Python 3.10
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Pydantic
- JWT
- Argon2 password hashing
- pytest
- Docker
- Docker Compose

## Project Structure

```text
employee-management-system/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   ├── models/
│   │   ├── routers/
│   │   └── schemas/
│   ├── alembic/
│   │   └── versions/
│   ├── tests/
│   ├── .dockerignore
│   ├── .env.example
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   └── requirements.txt
├── docker-compose.yml
├── PROJECT_DECISIONS.md
├── .gitignore
└── README.md
```

## Requirements

For the Docker setup, you only need:

- Git
- Docker Desktop
- VS Code

Python and PostgreSQL do not need to be installed separately when using the Docker workflow.

## Environment Variables

Create a `.env` file inside `backend/`.

You can use `.env.example` as a template:

```text
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/employee_management
JWT_SECRET_KEY=change-this-to-a-random-secret
```

The `.env` file is intentionally excluded from Git.

## Running with Docker

Clone the repository:

```bash
git clone <repository-url>
cd employee-management-system
```

Start the application and PostgreSQL:

```bash
docker compose up -d
```

Check the containers:

```bash
docker compose ps
```

Run the database migrations:

```bash
docker compose exec backend alembic upgrade head
```

Check the current migration:

```bash
docker compose exec backend alembic current
```

The API will be available at:

```text
http://localhost:8000
```

Swagger API documentation:

```text
http://localhost:8000/docs
```

ReDoc:

```text
http://localhost:8000/redoc
```

## Stopping the Application

Stop the containers:

```bash
docker compose down
```

The PostgreSQL data is stored in a Docker volume and will remain available when the containers are started again.

```bash
docker compose up -d
```

To remove the containers and PostgreSQL volume:

```bash
docker compose down -v
```

> Warning: `docker compose down -v` deletes the Docker PostgreSQL database volume.

## Database Migrations

Create a new migration after changing database models:

```bash
docker compose exec backend alembic revision --autogenerate -m "description"
```

Apply migrations:

```bash
docker compose exec backend alembic upgrade head
```

Check the current migration:

```bash
docker compose exec backend alembic current
```

## Running Tests

The project uses pytest for automated API testing.

The current test suite covers:

- Authentication
- Employee management
- Attendance
- Leave management
- Leave balances
- Dashboard
- Audit logs
- Root endpoint
- Authorization
- Validation
- Employee account lifecycle

Run the test suite:

```bash
pytest
```

The current test suite contains 134 passing tests.

## API Modules

### Authentication

- Register
- Login
- JWT access tokens
- Password hashing
- Active/inactive employee validation
- Employee profile validation

### Employees

- Create employee
- Update employee
- Patch employee
- Delete/deactivate employee
- Get employee
- Get current employee profile
- Update current employee profile
- Employee filtering
- Search
- Sorting
- Pagination
- Employee account provisioning

### Attendance

- Check-in
- Check-out
- Personal attendance history
- Admin attendance records
- Attendance filtering
- Pagination
- Approved-leave validation

### Leave Management

- Create leave request
- View leave requests
- Approve leave
- Reject leave
- Cancel leave
- Leave overlap validation
- Date validation
- Leave balance validation
- Leave balance consumption
- Leave balance restoration
- Leave filtering
- Sorting
- Pagination

### Dashboard

Admin dashboard provides:

- Total employees
- Active employees
- Present employees
- Absent employees
- Employees on leave
- Pending leave requests

Employee dashboard provides:

- Today's attendance
- Leave balances
- Pending leaves
- Upcoming approved leaves
- Recent attendance

### Audit Logs

Administrators can view audit logs with:

- User information
- Employee information
- Action
- Entity type
- Entity ID
- Details
- Date filtering
- Action filtering
- Entity filtering
- Sorting
- Pagination

## Architecture

```text
Client
  │
  ▼
FastAPI
  │
  ├── Authentication / Authorization
  ├── Routers
  ├── Pydantic Schemas
  ├── SQLAlchemy Models
  ├── Audit Logging
  └── Database Access
        │
        ▼
    PostgreSQL
```

When running with Docker:

```text
                 Docker Compose
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
     FastAPI                 PostgreSQL
     Container                Container
          │                       │
          └──── Docker Network ───┘
                    │
              PostgreSQL
                 Volume
```

## Development Workflow

Create a feature branch:

```bash
git checkout main
git pull
git checkout -b feature/<feature-name>
```

Run the application:

```bash
docker compose up -d
```

Apply migrations:

```bash
docker compose exec backend alembic upgrade head
```

Run tests:

```bash
pytest
```

After changes are verified:

```bash
git add .
git commit -m "Description of changes"
git push origin feature/<feature-name>
```

## Docker Workflow

The Docker environment provides:

- FastAPI application container
- PostgreSQL database container
- Docker network for service communication
- Persistent PostgreSQL volume
- Reproducible Python dependencies
- Database migrations through Alembic

The backend connects to PostgreSQL using the Docker service name:

```text
postgres
```

rather than:

```text
localhost
```

This allows the application and database to communicate correctly inside the Docker network.

## Current Database Tables

- `users`
- `employees`
- `attendance`
- `leaves`
- `leave_balances`
- `audit_logs`
- `alembic_version`

## Testing Status

The backend currently has:

```text
134 passed
```

across the complete pytest suite.

## Notes

The repository does not contain the actual `.env` file or local Python virtual environment.

These are intentionally excluded from version control.

Docker provides the reproducible application and PostgreSQL environment for development and deployment.