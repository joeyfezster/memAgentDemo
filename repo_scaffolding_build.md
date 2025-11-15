# Repo Scaffolding Build Tracker

- [x] Repository layout & baseline config — Directories created with shared configs (.gitignore, .editorconfig, pre-commit).
- [x] Backend scaffold (FastAPI) — FastAPI app with health check, pytest suite, Poetry + Alembic.
- [x] Frontend scaffold (React + Vite + TypeScript) — Login placeholder UI, Vitest + Testing Library.
- [x] Infrastructure tooling (docker-compose) — Compose stack for backend, frontend, Postgres, letta stub.
- [x] Makefile developer workflow — Local + docker-aware targets for linting/testing validated via `make lint USE_DOCKER=0` and `make test USE_DOCKER=0`.
- [x] CI pipeline — GitHub Actions workflow covering pre-commit, lint, tests, docker builds.
- [x] Documentation — README updated with setup instructions; service READMEs and env templates added.

## Notes
- Kickoff: 2025-02-14
- Lint run: `make lint USE_DOCKER=0`
- Test run: `make test USE_DOCKER=0`
