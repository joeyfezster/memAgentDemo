# Memory Agent

AI-powered memory management system built with FastAPI, React, and Letta.

## Architecture

This project follows a **monorepo** architecture with shared tooling:

```
memAgentDemo/
├── frontend/          # React + TypeScript + Vite
├── backend/           # Python FastAPI service
├── infra/             # Docker Compose & infrastructure
├── common/            # Shared schemas and contracts
└── .github/           # CI/CD workflows
```

### Services

- **Frontend**: React 18 + TypeScript + Vite for fast development
- **Backend**: FastAPI (Python 3.12) with async support
- **Database**: PostgreSQL 16 for persistent storage
- **Letta Agent**: Containerized AI agent service
- **Alembic**: Database migration management

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Make (optional, for convenient commands)
- Python 3.12+ (for local development)
- Node 20+ (for local development)

### Initial Setup

1. **Bootstrap the environment**:
   ```bash
   make bootstrap
   ```
   This will:
   - Create `.env` files from templates
   - Install pre-commit hooks (if available)

2. **Configure environment variables**:
   Edit the `.env` file in the root directory and service-specific `.env` files:
   - `OPENAI_API_KEY` - Your OpenAI API key
   - `POSTGRES_PASSWORD` - Database password
   - Other service configurations as needed

3. **Start all services**:
   ```bash
   make up
   ```

4. **Access the application**:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Letta Agent: http://localhost:8080

## Development Workflow

### Common Commands

```bash
# Start all services
make up

# Start in development mode (with hot reload)
make up-dev

# Stop all services
make down

# View logs
make logs                # All services
make logs-backend        # Backend only
make logs-frontend       # Frontend only

# Run tests
make test                # All tests
make test-backend        # Backend tests only
make test-frontend       # Frontend tests only

# Lint code
make lint                # All services
make lint-backend        # Backend only
make lint-frontend       # Frontend only

# Format code
make format              # All services
make format-backend      # Backend only
make format-frontend     # Frontend only

# Access service shells
make backend-shell       # Backend container shell
make frontend-shell      # Frontend container shell
make db-shell           # PostgreSQL shell

# Database migrations
make migrate            # Run migrations
make migrate-create MSG="description"  # Create new migration
make migrate-down       # Rollback last migration

# Clean up
make clean              # Remove containers, volumes, and artifacts
```

### Project Structure

#### Backend (`/backend`)

```
backend/
├── app/
│   ├── api/           # API routes
│   ├── db/            # Database configuration
│   ├── models/        # SQLAlchemy models
│   └── schemas/       # Pydantic schemas
├── tests/             # Test files
├── alembic/           # Database migrations
├── Dockerfile
└── pyproject.toml     # Python dependencies
```

**Key technologies**:
- FastAPI for async API endpoints
- SQLAlchemy 2.0 with async support
- Alembic for migrations
- Pytest for testing
- Ruff, Black, isort for linting/formatting

#### Frontend (`/frontend`)

```
frontend/
├── src/
│   ├── components/    # React components
│   ├── pages/         # Page components
│   ├── api/           # API client
│   ├── types/         # TypeScript types
│   └── test/          # Test files
├── Dockerfile
├── nginx.conf         # Production nginx config
└── package.json
```

**Key technologies**:
- React 18 with TypeScript
- Vite for build tooling
- Vitest + React Testing Library
- ESLint + Prettier for linting/formatting

#### Common (`/common`)

Shared assets across services:
- JSON schemas for data validation
- OpenAPI specifications
- Agent tool contracts

#### Infrastructure (`/infra`)

Docker Compose configurations:
- `docker-compose.yml` - Production configuration
- `docker-compose.dev.yml` - Development overrides

## Testing

### Backend Tests

```bash
# Run all backend tests
make test-backend

# Run with coverage
docker-compose -f infra/docker-compose.yml exec backend pytest --cov

# Run specific test file
docker-compose -f infra/docker-compose.yml exec backend pytest tests/test_health.py
```

### Frontend Tests

```bash
# Run all frontend tests
make test-frontend

# Run with UI
docker-compose -f infra/docker-compose.yml exec frontend npm run test:ui

# Run with coverage
docker-compose -f infra/docker-compose.yml exec frontend npm run test:coverage
```

## Database Migrations

### Creating Migrations

```bash
# Auto-generate migration from model changes
make migrate-create MSG="add user table"

# The migration file will be created in backend/alembic/versions/
```

### Running Migrations

```bash
# Apply all pending migrations
make migrate

# Rollback last migration
make migrate-down
```

## CI/CD

### GitHub Actions Workflows

- **CI Pipeline** (`.github/workflows/ci.yml`):
  - Runs on PRs and pushes to main/develop
  - Lint checks for backend and frontend
  - Unit tests with coverage
  - Docker build validation
  - Path-based filtering to run only affected jobs

- **Publish Pipeline** (`.github/workflows/publish.yml`):
  - Runs on pushes to main and version tags
  - Builds and pushes Docker images to GitHub Container Registry
  - Tags images with version, branch, and SHA

### Pre-commit Hooks

Install pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
```

Hooks configured:
- Python: Ruff, Black, isort, MyPy
- TypeScript: ESLint, Prettier
- General: trailing whitespace, file endings, YAML/JSON validation
- Docker: Hadolint for Dockerfile linting

## Environment Variables

### Root `.env`
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`
- `BACKEND_PORT`, `FRONTEND_PORT`, `LETTA_PORT`
- `OPENAI_API_KEY`, `LETTA_API_KEY`

### Backend `.env`
- `DATABASE_URL` - PostgreSQL connection string
- `LETTA_AGENT_URL` - Letta service URL
- `CORS_ORIGINS` - Allowed CORS origins

### Frontend `.env`
- `VITE_API_BASE_URL` - Backend API URL

## Deployment

### Container Registry

Images are automatically published to GitHub Container Registry:
- `ghcr.io/<username>/memagent-backend:latest`
- `ghcr.io/<username>/memagent-frontend:latest`

### Heroku Deployment (Example)

```bash
# Login to Heroku Container Registry
heroku container:login

# Build and push
docker build -t registry.heroku.com/<app-name>/web ./backend
docker push registry.heroku.com/<app-name>/web

# Release
heroku container:release web -a <app-name>
```

## API Documentation

Interactive API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

OpenAPI specification: `/common/clients/openapi-spec.yaml`

## Troubleshooting

### Services won't start
```bash
# Check service logs
make logs

# Restart services
make restart

# Clean and restart
make clean
make up
```

### Database connection issues
```bash
# Check PostgreSQL is running
docker-compose -f infra/docker-compose.yml ps postgres

# Access database shell
make db-shell
```

### Frontend can't connect to backend
- Verify `VITE_API_BASE_URL` in `frontend/.env`
- Check CORS settings in `backend/app/config.py`
- Ensure backend is running: `make logs-backend`

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests: `make test`
4. Run linters: `make lint`
5. Commit (pre-commit hooks will run automatically)
6. Push and create a PR

## License

[Add your license here]

## Support

For issues and questions, please open an issue on GitHub.