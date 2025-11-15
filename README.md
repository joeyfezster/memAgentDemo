# memAgent Demo Monorepo

Scaffolded monorepo containing the frontend, backend, and infrastructure required for the memAgent platform.

## Prerequisites

Before running `make bootstrap`, ensure you have the following installed on your system:

### Required System Dependencies

- **Python 3.12**: `brew install python@3.12`
- **virtualenv**: `brew install virtualenv`
- **Node.js 25.x**: `brew install node`
- **corepack**: After installing Node.js, run `npm install -g corepack && corepack enable`

### Initial Setup

1. Create a Python virtual environment:
   ```bash
   virtualenv .venv -p python3.12
   ```
2. Run bootstrap to install all project dependencies:
   ```bash
   make bootstrap
   ```

This will:

- Install pip, pre-commit, and poetry in your virtualenv
- Configure pre-commit hooks
- Enable corepack for pnpm management
- Create `.env` files from templates
- Install backend Python dependencies via Poetry
- Install frontend Node dependencies via pnpm

## Repository layout

```
backend/    # FastAPI service, Poetry project, Alembic migrations
frontend/   # React + Vite + TypeScript web application
infra/      # Docker Compose, environment templates
common/     # Shared libraries and future cross-service assets
.github/    # GitHub Actions workflows
```

A running checklist for the scaffolding effort lives in `repo_scaffolding_build.md`.

## Quick start

```bash
make bootstrap   # install tooling and create local env files
make up          # build and start services (frontend, backend, postgres, letta)
make down        # stop services
```

Access the application at:

- Frontend: http://localhost:5173
- Backend: http://localhost:8000/healthz
- Postgres: `postgresql://postgres:postgres@localhost:5432/memagent`

## Testing & linting

```bash
make lint        # run linting for backend and frontend
make test        # run unit/component tests for both services
make format      # execute pre-commit hooks across the repo
```

## Deployment notes

- Dockerfiles are included for both services. The frontend image exposes a production `nginx` stage while the dev profile is used via Docker Compose.
- `infra/docker-compose.yml` orchestrates the local stack and includes a letta agent stub container behind an optional profile (`agents`).
- GitHub Actions workflow (`.github/workflows/ci.yml`) runs pre-commit, lint, tests, and container build smoke checks on every push/PR.

## Next steps

- Flesh out shared libraries under `common/` as cross-cutting functionality emerges.
- Implement authentication, chatbot UI, and memory-backed services on top of this scaffold.
