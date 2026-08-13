# Project Decisions

## Project

Employee Leave & Attendance Management System

## Purpose

This project is a full-stack employee management system designed to simulate a real-world enterprise application.

The system will manage:

- Employees
- Departments
- Attendance
- Leave requests
- Leave balances
- User roles and permissions

## Technology Stack

### Backend

- Python
- FastAPI
- SQLAlchemy

### Database

- PostgreSQL

### Frontend

- React
- TypeScript

### Authentication

- JWT

### Testing

- pytest

### DevOps

- Git
- GitHub
- Docker
- GitHub Actions

### Cloud

- AWS

## Development Approach

The project will be developed incrementally.

Core application functionality will be implemented before introducing additional infrastructure such as Docker, CI/CD, and cloud deployment.

## Git Workflow

The `main` branch represents stable code.

New features will be developed using feature branches.

Example:

`feature/authentication`

Changes will be committed using conventional commit-style messages.