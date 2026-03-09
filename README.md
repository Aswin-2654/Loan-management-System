# Loan Management System (LMS)

Full-stack Loan Management System with role-based workflows for customers, verification staff, managers, and admins.

## Repository layout

```text
Loan-management-System/
  lms_frontend/   # React + TypeScript + Vite app
  lms_backend/    # FastAPI + MongoDB API
```

## Architecture at a glance

- Frontend runs on `http://localhost:5173`
- Backend API runs on `http://localhost:8010`
- Frontend API base should point to `http://localhost:8010/api`
- Backend CORS is configured for localhost Vite origins

## Prerequisites

- Node.js 18+ and npm 9+
- Python 3.10+
- MongoDB running locally (`mongodb://localhost:27017`)

## Run locally (recommended order)

### 1) Start backend

```bash
cd lms_backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8010
```

Backend health check:
- `GET http://localhost:8010/` returns `{ "status": "ok" }`

### 2) Start frontend

```bash
cd lms_frontend
npm install
npm run dev
```

Frontend URL:
- `http://localhost:5173`

## Environment variables

### Frontend (`lms_frontend/.env`)

```env
VITE_API_BASE_URL=http://localhost:8010/api
VITE_CASHFREE_ENV=sandbox
```

### Backend (`lms_backend/.env`)

Common keys used by backend config:

```env
APP_NAME=PAY CREST API
API_PREFIX=/api
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=pay_crest
JWT_SECRET=CHANGE_ME
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440
CASHFREE_ENV=sandbox
```

## Project docs

- Frontend guide: `lms_frontend/README.md`
- Frontend target structure: `lms_frontend/TARGET_STRUCTURE.md`
- Backend target structure: `lms_backend/TARGET_STRUCTURE.md`

## Key scripts

Frontend (`lms_frontend/package.json`):
- `npm run dev`
- `npm run build`
- `npm run preview`

Backend:
- `uvicorn app.main:app --reload --port 8010`

## Troubleshooting

- Port conflict:
  - Change frontend port in Vite config or run Vite with a different port.
  - Change backend port via `--port` and update `VITE_API_BASE_URL`.
- CORS errors:
  - Ensure frontend is running on `http://localhost:5173` or `http://127.0.0.1:5173`.
- API not reachable from frontend:
  - Verify backend is running and `VITE_API_BASE_URL` points to `/api` prefix.
- Mongo connection issues:
  - Confirm MongoDB service is up and `MONGODB_URI` is correct.
