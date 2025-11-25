# E2E Tests

End-to-end tests using Playwright to validate the application's functionality.

## Setup

```bash
cd e2e
pnpm install
pnpm exec playwright install chromium
```

## Running Tests

```bash
# Run all tests
pnpm test

# Run tests in headed mode (see browser)
pnpm test:headed

# Run tests in UI mode (interactive)
pnpm test:ui

# Debug tests
pnpm test:debug
```

## Prerequisites

The application must be running before executing the tests:

```bash
# From the root directory
make up
```

The tests expect:

- Frontend running at http://localhost:5173
- Backend running at http://localhost:8000
- Database seeded with test user: sarah@chickfilb.com / changeme123
