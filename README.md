# STACKSENSE

STACKSENSE is an AI-powered engineering intelligence platform for understanding code, dependencies, deployments, and operational incidents. Phase 1 establishes a clean local development foundation with a React frontend, a FastAPI backend, PostgreSQL, Docker Compose, health checks, and basic tests.

## Phase 1 scope

- React + TypeScript frontend with a dashboard landing page
- FastAPI backend with health endpoints
- PostgreSQL + SQLAlchemy + Alembic foundation
- Docker Compose for local orchestration
- Basic backend tests and initial documentation

## Technology stack

- Frontend: React, TypeScript, Vite, Tailwind CSS, React Router
- Backend: Python 3.12+, FastAPI, SQLAlchemy, Alembic, Pydantic
- Database: PostgreSQL
- DevOps: Docker Compose

## Project structure

- frontend/ for the Vite app
- backend/ for the FastAPI service and tests
- docs/ for architecture notes

## Prerequisites

- Docker Desktop or Docker Engine
- Docker Compose
- Node.js 20+
- Python 3.12+

## Environment setup

1. Copy .env.example to .env.
2. Update values as needed for your local machine.

## Run locally

```bash
cp .env.example .env
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows use .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

## Run with Docker Compose

```bash
docker compose up --build
```

## Productized deployment

Set a strong `AUTH_SECRET`, non-default PostgreSQL credentials, `DATABASE_URL`, and the production frontend `VITE_API_URL` in a secret-managed `.env` file. Build the production images with `docker compose -f docker-compose.prod.yml build` and start them with `docker compose -f docker-compose.prod.yml up -d`. The backend runs migrations before serving, exposes `/api/health`, and uses a non-root container user. The frontend is served as static assets by Nginx.

Create a PostgreSQL backup with `pg_dump "$DATABASE_URL" > stacksense-$(date +%Y%m%d).sql` and restore with `psql "$DATABASE_URL" < stacksense-backup.sql`. Store backups outside the application host and test restores periodically.

Authentication uses expiring HMAC bearer tokens and scrypt password hashes. New users are viewers; the first registered user is an administrator. Mutating engineering operations require an administrator or engineer role. The CI workflow in `.github/workflows/ci.yml` runs backend tests, Python compilation, frontend builds, and production image builds.

## API endpoints

- GET /api/health
- GET /api/health/db
- POST /api/assistant/chat (local deterministic providers are the default; configure `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`, `LLM_PROVIDER`, `LLM_MODEL`, and `LLM_API_KEY` for compatible remote providers)

Index existing engineering data explicitly with `python -m app.ai.index [repository_id]`. The Phase 5 assistant combines semantic retrieval with structured evidence and dependency-aware source records. It uses portable JSON embeddings by default; pgvector acceleration is an installation-time option and is not required for local development or SQLite tests.

## Run tests

```bash
cd backend
pytest -q
```

## Current limitations

- The local providers are deterministic development fallbacks, not production-grade language or embedding models.
- The assistant requires a repository scope and only returns indexed evidence for that repository.
- PostgreSQL vector acceleration, authentication, streaming responses, and production evaluation remain future hardening work.

## Future phases

- Code intelligence
- Dependency graph analysis
- Deployment risk analysis
- Incident detection and root-cause analysis
- Vector search and RAG
- AI-powered engineering assistant
