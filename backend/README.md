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
