# memAgent Demo - Shared Memory AI Assistant

> A location intelligence platform demonstrating persona-based shared memory across AI agents

## Overview

This project showcases a novel approach to AI agent memory where agents learn from interactions across users with similar professional personas. Users interact with "Pi", an AI assistant specialized in location analytics, which adapts based on collective experience from users in the same industry/role.

**Key Features:**

- 🧠 **Shared Memory**: Agents share learned patterns across users with same persona
- 🎭 **Persona Discovery**: Automatic identification of user industry + role through conversation
- 📊 **Location Analytics**: Integration with Placer.ai-style foot traffic data
- 🔒 **Privacy Guarantees**: PII isolated per-user, only patterns shared
- 👁️ **Memory Observability**: UI to visualize agent memory and relationships

## Quick Start

### Prerequisites

Install these if you don't have them:

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required tools
brew install python@3.12 docker docker-compose corepack

# Start Docker Desktop
open -a Docker

# Enable corepack for pnpm
corepack enable
```

### Setup Steps

1. **Clone and enter the repository:**

   ```bash
   git clone <repository-url>
   cd memAgentDemo
   ```

2. **Create Python virtual environment:**

   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   ```

3. **Bootstrap the project:**

   ```bash
   make bootstrap
   ```

   This will:

   - Install Python dependencies (poetry, pre-commit)
   - Setup pre-commit hooks
   - Copy `.env.example` files to `.env`
   - Install backend dependencies (if not using Docker)
   - Install frontend dependencies (if not using Docker)

4. **Configure environment variables:**

   The bootstrap step copies `.env.example` → `.env` for both backend and frontend. You need to add your OpenAI API key:

   **backend/.env** - Add these required variables:

   ```bash
   # Required: OpenAI API key for LLM and embeddings
   OPENAI_API_KEY=sk-your-actual-key-here

   # Optional: Letta server password (defaults to 'changeme')
   LETTA_SERVER_PASSWORD=changeme
   ```

   All other backend/.env variables have working defaults:

   ```bash
   PROJECT_NAME="memAgent Demo API"
   ENVIRONMENT=local
   DEBUG=true
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/postgres
   JWT_SECRET_KEY=change-me  # Change for production
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   PERSONA_SEED_PASSWORD=changeme123  # Demo user password
   LETTA_ENABLED=true
   LETTA_BASE_URL=http://localhost:8283
   LETTA_PROJECT_ID=  # Auto-configured
   LETTA_API_TOKEN=  # Auto-configured
   ```

   **frontend/.env** - Has working default:

   ```bash
   VITE_API_URL=http://localhost:8000
   ```

   **Quick setup:**

   ```bash
   # Add only the OpenAI key (minimum required change)
   echo "\nOPENAI_API_KEY=sk-your-actual-key-here" >> backend/.env
   ```

5. **Start the application:**

   ```bash
   make up
   ```

   This starts all 4 containers:

   - **PostgreSQL** (with pgvector extension) on port 5432
   - **Letta server** (agent orchestration) on port 8283
   - **Backend API** (FastAPI) on port 8000
   - **Frontend UI** (React + Vite) on port 5173

   Wait ~30 seconds for all services to initialize.

6. **Access the application:**

   - Open browser to **http://localhost:5173**
   - Login with demo credentials:
     - Email: `alice@example.com`
     - Password: `changeme123`
   - Other demo users: `bob@example.com`, `carol@example.com` (same password)

7. **Try it out:**
   - Ask questions like "Find QSR locations in Atlanta"
   - Switch to "Agents" tab to visualize memory blocks
   - Login as different users to see shared memory in action

## Architecture

The system is built with:

- **Frontend**: React 19 + TypeScript + Vite
- **Backend**: FastAPI (Python 3.12) + SQLAlchemy (async)
- **Database**: PostgreSQL 16 + pgvector extension
- **Agent Framework**: Letta (memory-augmented agents)
- **LLM**: OpenAI GPT-4o + text-embedding-3-small
- **Infrastructure**: Docker Compose

### Key Components

1. **Three-Tier Memory System**:

   - **Platform Memory**: Shared agent identity (read-only)
   - **User Memory**: Personal facts and preferences (private)
   - **Persona Memory**: Shared patterns across similar users (collaborative)

2. **Persona System**:

   - Format: `{industry}_{professional_role}`
   - Examples: `qsr_real_estate`, `tobacco_consumer_insights`
   - Auto-discovered through natural conversation

3. **Location Analytics Tools**:
   - 8 Placer.ai-style tools (currently mocked)
   - POI search, visit flows, audience profiles, trade areas

📄 **Full architecture documentation in [docs/deliverables/00_presentation.md](docs/deliverables/00_presentation.md)**

## Development Commands

```bash
# Container management
make up              # Start all services
make down            # Stop all services
make logs            # View logs (Ctrl+C to exit)

# Database
make migrate         # Run database migrations

# Testing & Quality
make test            # Run all tests
make test-backend    # Run backend tests only
make test-frontend   # Run frontend tests only
make lint            # Run linters
make format          # Format code (pre-commit hooks)

# Development shells
make backend-shell   # Open bash shell in backend container
make frontend-shell  # Open sh shell in frontend container

# Activation
source .venv/bin/activate  # Activate virtual environment
```

## Project Structure

```
memAgentDemo2/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # REST API endpoints
│   │   ├── core/        # Letta client, config, security
│   │   ├── crud/        # Database operations
│   │   ├── db/          # Database setup, migrations
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas
│   │   └── services/    # Business logic (persona service)
│   ├── agent/
│   │   └── tools/       # Letta agent tools
│   ├── alembic/         # Database migrations
│   └── tests/           # Backend tests
├── frontend/            # React frontend
│   └── src/
│       ├── api/         # API client
│       ├── components/  # React components
│       └── assets/      # Static assets
├── infra/               # Infrastructure
│   ├── docker-compose.yml
│   └── init-db.sql
├── docs/                # Documentation
│   ├── deliverables/    # Project deliverables
│   │   ├── 00_presentation.md
│   │   ├── 01_problem_analysis.md
│   │   └── 02_03_solution_options_and_recommended_approach.md
│   └── architecture/    # Architecture docs
│       ├── a01-system-context.md
│       ├── a02-container-diagram.md
│       ├── a03-backend-components.md
│       ├── a04-frontend-components.md
│       ├── a05-agent-architecture.md
│       └── a06-memory-architecture.md
└── Makefile            # Development commands
```

## Troubleshooting

### Port Conflicts

**Problem**: Port already in use

**Solution**: Stop conflicting services or modify ports in `infra/docker-compose.yml`:

- PostgreSQL: 5432
- Letta: 8283
- Backend: 8000
- Frontend: 5173

### Docker Not Running

**Problem**: `Cannot connect to Docker daemon`

**Solution**: Start Docker Desktop:

```bash
open -a Docker
# Wait for Docker to start, then retry
make up
```

### Missing OpenAI API Key

**Problem**: Agent responses fail or return errors

**Solution**: Add valid OpenAI API key to `backend/.env`:

```bash
echo "OPENAI_API_KEY=sk-your-actual-key-here" >> backend/.env
make down
make up
```

### Database Not Initializing

**Problem**: Backend fails to connect to database

**Solution**: Recreate containers and volumes:

```bash
make down
docker volume rm memagent_postgres memagent_letta 2>/dev/null || true
make up
```

### Frontend Build Errors

**Problem**: Frontend container fails to start

**Solution**: Clear node_modules and rebuild:

```bash
make down
rm -rf frontend/node_modules
make up
```

## Demo Scenario

**Try this to see shared memory in action:**

1. **Login as Alice** (`alice@example.com` / `changeme123`)

   - Ask: "Find QSR restaurants in Atlanta with high foot traffic"
   - Agent will identify Alice as `qsr_real_estate` persona
   - Agent learns this is a common query pattern

2. **Login as Bob** (`bob@example.com` / `changeme123`)

   - Ask: "Looking for new Taco Bell locations in Houston"
   - Agent identifies Bob as same `qsr_real_estate` persona
   - Agent benefits from pattern learned with Alice
   - Response is faster and more comprehensive

3. **View Shared Memory**:
   - Click "Agents" tab
   - See both Alice and Bob's agents connected to same `qsr_real_estate_service_experience` block
   - Click the shared block to view collaborative learnings

## Documentation

- **[Presentation](docs/deliverables/00_presentation.md)** - Executive overview with architecture diagrams
- **[Problem Analysis](docs/deliverables/01_problem_analysis.md)** - Memory system challenges
- **[Solution Options](docs/deliverables/02_03_solution_options_and_recommended_approach.md)** - Design choices and tradeoffs
- **[Architecture Docs](docs/architecture/)** - Detailed technical documentation

## License

MIT

---

**Built with ❤️ to demonstrate shared memory in AI agents**
