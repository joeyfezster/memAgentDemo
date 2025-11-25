# Project General Coding Guidelines

## Agent Memory and Context

- When a user asks you to remember something, update this file to persist that memory.
- This file serves as the primary source of truth for project-specific guidelines, conventions, and accumulated knowledge.

## Workflows

- When working on a feature or bugfix, create your work plan and keep it in a local markdown file to track your progress as a todo list. Track implicit decisions you make along the way in this file. The file should be titled by the name of the feature or bugfix you are working on. Put these in /docs/agentic_work/.
- Agents will consider that human code review is a major bottleneck of the development process. strive to write minimal, high-quality code that minimizes the need for human review.
- This repo uses a local .venv for python dependencies and pip for dependency management.
- The project uses a Makefile to streamline common tasks. bootstrap is meant to ensure the system is ready to go, make up should be an idempotent and complete operation to start all the containers needed for local development.

### Docker and Container Management

- Use `make up-detached` to start services in the background (detached mode). This prevents the terminal from being blocked.
- `make up` runs in the foreground and keeps the terminal open - any further commands in that terminal will interrupt the running containers.
- The docker-compose.yml includes a `db-init` service that ensures database migrations and seeding happen idempotently before the backend starts.
- Database initialization (migrations + seeding) is handled by `backend/db_init.py` which runs once when containers start.
- To completely reset the database: `make down && docker volume rm infra_postgres_data && make up-detached`

### Alembic Migrations

- All alembic migration files should start with mxxx_description.py where xxx is a zero-padded incremental number. Check which migrations already exist before naming the new migration.

## Git

### Using Git

- Agents are not to use git, unless explicitly instructed to do so by a human operator.
- Note there are linters and pre-commit hooks set up to ensure code quality and style. These will run automatically on git commit.
- Linter-edited files must be re-staged before committing.

### Checking PR CI Status

- Use `gh pr checks <PR_NUMBER> --watch` in background mode to monitor CI checks in real-time
- **CRITICAL**: Always set `GH_PAGER` environment variable to prevent pager issues: `GH_PAGER=cat gh <command>`
- For viewing logs: `GH_PAGER=cat gh run view <RUN_ID> --log-failed`
- To get the latest failed run logs: `gh run list --branch <BRANCH> --limit 1 --json databaseId --jq '.[0].databaseId' | xargs -I {} GH_PAGER=cat gh run view {} --log-failed`
- All gh CLI commands that display output should use `GH_PAGER=cat` to avoid terminal pager blocking

### Git Commit Messages

- Follow the structure: `<Component>: <verb> <context>`
- Examples:
  - `Docs: add claude docs in md (66 files)`
  - `API: fix authentication error handling`
  - `Frontend: update chat component styles`
  - `Tests: add unit tests for persona CRUD`

### PRs and Merging

- After creating a PR, watch the results of the CI jobs and address any issues that arise.

## Code Style

- Avoid writing comments at all costs. If you see comments, refactor the code until they are not needed.
- **Exception**: Test functions should have a one-line docstring describing what they validate. This serves as living documentation.
- Typing is required for all functions, methods input and output. Use Python's built-in typing module, create custom types when needed. The idea here is to make function signatures as informative as possible.
- Return types must be explicit and descriptive. Never return collection types like`list[dict]` or `dict` - create proper dataclasses or Pydantic models that clearly communicate what the function returns.

## Code Quality

- Code and tests must be written with a good-faith effort to solve the task at hand. Cop-out or 'game-the-system' solutions to make tests pass or skip tests to superficially satisfy requirements are not acceptable.
- Follow the DRY (Don't Repeat Yourself) principle to minimize code duplication. Sometimes this means creating helper functions or classes, it's important to search if they already exist for good Seiton. If there are existing functions or classes that solve the problem, use them instead of reinventing the wheel. Sometimes small changes to expand existing functionality are necessary.
- Write modular code that is easy to maintain and extend. Break down large functions or classes into smaller, reusable components.
- Ensure that your code is efficient and optimized for performance, especially in critical sections of the application.
- Write clear and descriptive variable and function names that convey their purpose and usage
- Follow SOLID principles to create maintainable and scalable code. Pay particular attention to the Single Responsibility Principle and the Open/Closed Principle.

## Testing Conventions

- Each new feature or component must be tested in a functional way. We are looking for validation of the core functionality and behaviors we expect from the code. This includes edge cases and error handling. However, this means we do NOT use mocking, stubbing, or patching unless absolutely necessary. Agents must ask for permission to use these techniques, and provide strong justification for why they are necessary.
- Acceptable use of mocking: Testing error handling for external API failures that cannot be reliably reproduced (e.g., forcing an LLM to return a malformed response). Avoid mocking internal application logic or database interactions.
- Write tests that are easy to read and understand.
- Use the convention of test_cases = [(test_input, expected_output), ...] and a for loop to iterate through them in order to reduce code duplication and increase readability.
- Write functional tests that cover a wide range of scenarios, including edge cases.
- Do NOT use mocking or stubbing unless absolutely necessary. Prefer testing the actual behavior of the code.
- Important: - When planning work, always consider how the work will be validated. Validation is a critical and required part of all incremental feature additions and bug fixes.

### Expensive Tests (API Calls)

- Tests that make real API calls to external services (e.g., Anthropic Claude) are marked with `@pytest.mark.expensive`
- These tests are SKIPPED by default locally to avoid API credit exhaustion
- To run ALL tests including expensive ones: `pytest` (default in CI)
- To skip expensive tests locally: `pytest -m "not expensive"` (recommended for local dev)
- **When running expensive tests, use fail-fast mode to stop on first failure:** `pytest tests/test_agent_memory.py -v -x`
- **Minimize running expensive tests - only run when validating changes to agent/memory functionality**
- Files with expensive tests: `backend/tests/test_agent_tools.py` (all 7 tests make real Claude API calls), `backend/tests/test_agent_memory.py` (5 memory retrieval tests)

### Viewing E2E Test Results

- E2E test screenshots and error context are saved in `e2e/test-results/<test-name-chromium>/`
- Each failed test has a `test-failed-1.png` screenshot and `error-context.md` with page state
- HTML test report is generated in `e2e/playwright-report/index.html` - open with `open e2e/playwright-report/index.html`
- To view screenshots from terminal: Use `ls e2e/test-results/` to list test result folders, then view specific folders for artifacts

## Running Commands

- This project has a virtual environment located at `.venv/`.
- **IMPORTANT**: Activate the virtual environment in a standalone command that can be auto-approved: `source .venv/bin/activate`
- This activation command must be run separately, not chained with other commands.
- Only activate the virtual environment when the terminal complains that python is not found.
- Sometimes, you run a command and expect output but see nothing. This is very likely because of a pager issue. To fix this, try different ways to pipe the command output, for example, with `cat` or `less`. For example: `gh run view <RUN_ID> --log-failed | cat`, then update this file with any new tips learned.
- this is a good command to run the E2E playwright tests locally: `cd /Users/joeybaruch/Dropbox/0.\ consulting/demo_repos/memAgentDemo2/e2e && pnpm test:reset-db && pnpm playwright test

## Earned Experience

- As agents work on this project and complete tasks, they will gain experience by trying things that don't work. Agents are to request permission to update this very file to add new guidelines based on lessons learned from mistakes made during development.
