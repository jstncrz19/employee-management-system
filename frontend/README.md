# Employee Management System — Frontend

The frontend is a single-page application built with **React** and **Vite**. It provides the user interface for the Employee Management System's FastAPI backend: login, role-based navigation, dashboards, employee management, attendance, and leave management.

## Tech Stack

- React 19
- Vite 8 (build tool + development server)
- React Router (client-side routing)
- Axios (HTTP client, JWT via Authorization header)
- Plain CSS (no UI framework — no runtime CSS libraries)

## How It Talks to the Backend

- All API calls go through `src/services/api.js`, an Axios instance.
- The base URL comes from `VITE_API_BASE_URL` and defaults to `http://localhost:8000`.
- On login, the JWT is stored as `access_token` (localStorage).
- A request interceptor attaches `Authorization: Bearer <token>` to every request.
- A response interceptor clears the token and redirects to `/login` on any `401`.
- `GET /users/me` resolves the current account (id, email, role) on app load; this drives the navigation and route guards.

## Getting Started

Requires Node.js (18+).

```bash
cd frontend
npm install
npm run dev
```

The development server runs at `http://localhost:5173`. Make sure the backend is running on `http://localhost:8000` (see the root README).

## Environment Configuration

Copy the example file if the API is not reachable at the default URL:

```bash
cp .env.example .env
```

| Variable | Default | Description |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `http://localhost:8000` | Base URL of the FastAPI backend |

## Routes

Routes are role-protected by `src/components/ProtectedRoute.jsx`. Unauthenticated users are redirected to `/login`.

### Public

| Path | Page |
| --- | --- |
| `/login` | Login and employee self-registration |

### Admin only

| Path | Page |
| --- | --- |
| `/admin` | Admin dashboard (company overview) |
| `/employees` | Employee management (create, edit, deactivate, provision accounts, manage balances) |
| `/admin/attendance` | All attendance records with filters |
| `/admin/leaves` | Leave requests (approve / reject) |
| `/admin/audit-logs` | Audit log viewer |

### Employee (and admin) self-service

| Path | Page |
| --- | --- |
| `/dashboard` | Employee dashboard (check-in/out, balances, leave status) |
| `/leaves` | My leaves and leave balances |

## Production Build

```bash
npm run build
```

Outputs the optimized bundle to `frontend/dist`. Vite statically serves it; any reverse proxy should rewrite all non-asset routes to `index.html` so client-side routing works.

## Scripts

| Command | Description |
| --- | --- |
| `npm run dev` | Start the development server |
| `npm run build` | Create the production build in `dist/` |
| `npm run lint` | Run ESLint |
| `npm run preview` | Preview the production build locally |
