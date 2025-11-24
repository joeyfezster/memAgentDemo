# Backend Testing Setup

## Prerequisites

### macOS Setup for testing.postgresql with pgvector

testing.postgresql requires PostgreSQL binaries (`postgres`, `initdb`) to be available in your PATH.

#### Automated Setup (Recommended)

Run the setup script from the project root:

```bash
./scripts/setup_test_env.sh
```

This script will:

- Install PostgreSQL 16 (if not present)
- Build and install pgvector extension for PostgreSQL 16
- Configure your shell PATH (~/.zshrc or ~/.bashrc)

After running the script, restart your shell or run:

```bash
source ~/.zshrc  # or ~/.bashrc for bash
```

#### Manual Setup

If you prefer manual setup or the script fails:

**1. Install PostgreSQL 16**

```bash
brew install postgresql@16
```

**2. Add PostgreSQL to PATH**

Add to your `~/.zshrc` (or `~/.bashrc` if using bash):

```bash
# PostgreSQL 16
export PATH="/usr/local/opt/postgresql@16/bin:$PATH"
```

Then reload:

```bash
source ~/.zshrc
```

**3. Build and Install pgvector**

```bash
# Download pgvector source
cd /tmp
git clone --branch v0.8.1 --depth 1 https://github.com/pgvector/pgvector.git
cd pgvector

# Build and install for postgresql@16
export PG_CONFIG=/usr/local/opt/postgresql@16/bin/pg_config
make clean
make
make install
```

**4. Verify Installation**

```bash
# Check postgres is in PATH
which postgres
# Should output: /usr/local/opt/postgresql@16/bin/postgres

# Check initdb is in PATH
which initdb
# Should output: /usr/local/opt/postgresql@16/bin/initdb

# Check pgvector extension files exist
ls -la /usr/local/opt/postgresql@16/share/postgresql@16/extension/vector.control
# Should show the file exists
```

## Running Tests

Once setup is complete, run tests with:

```bash
# Run all backend tests
pytest backend/tests/ -v

# Run specific test file
pytest backend/tests/test_health.py -v

# Run with coverage
pytest backend/tests/ --cov=app --cov-report=html
```

## Troubleshooting

### Error: "command not found: initdb"

PostgreSQL binaries are not in your PATH. Add `/usr/local/opt/postgresql@16/bin` to your PATH in your shell configuration file and restart your shell.

### Error: 'extension "vector" is not available'

pgvector extension is not installed for postgresql@16. Follow the manual setup step 3 above to build and install pgvector.

### Tests are slow

testing.postgresql creates a new database instance for each test session. This is intentional for isolation but can be slow. The test suite uses a session-scoped fixture that creates one database instance per test run to minimize overhead.

## How It Works

- `conftest.py` uses `testing.postgresql` to create an isolated PostgreSQL instance
- Each test session gets a fresh database with all migrations applied
- pgvector extension is automatically enabled during setup
- The database is destroyed after tests complete
