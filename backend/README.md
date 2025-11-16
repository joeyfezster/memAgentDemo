# Backend Service

FastAPI-based backend for the memAgent demo platform.

## Local development

```bash
poetry install
poetry run uvicorn app.main:app --reload
```

The application reads configuration from environment variables or a `.env` file. Copy
`./.env.example` to `.env` to start with sensible defaults.

| Variable | Description |
| --- | --- |
| `DATABASE_URL` | Database connection string (PostgreSQL in production, SQLite for tests). |
| `JWT_SECRET_KEY` | Symmetric key for signing bearer tokens. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Minutes before issued tokens expire. |
| `PERSONA_SEED_PASSWORD` | Plaintext password applied to seeded personas from `/docs/product/personas`. |

## Testing

```bash
poetry run pytest
```

## Agent orchestration

Set `LETTA_ENABLED=true` along with `LETTA_API_TOKEN`, `LETTA_PROJECT_ID`, and optionally `LETTA_BASE_URL` to connect the backend to a running Letta deployment. When these variables are not set the system falls back to a simulation backend so the FastAPI application and tests remain deterministic. The agents live under `app/agents` and can be exercised interactively via `agent_work/notebooks/agent_playground.ipynb`.
