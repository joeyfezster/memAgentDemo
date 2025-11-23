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
- Typing is required for all functions, methods input and output. Use Python's built-in typing module, create custom types when needed.

## Code Quality

- Code and tests must be written with a good-faith effort to solve the task at hand. Cop-out or 'game-the-system' solutions to make tests pass or skip tests to superficially satisfy requirements are not acceptable.
- Follow the DRY (Don't Repeat Yourself) principle to minimize code duplication. Sometimes this means creating helper functions or classes, it's important to search if they already exist for good Seiton. If there are existing functions or classes that solve the problem, use them instead of reinventing the wheel. Sometimes small changes to expand existing functionality are necessary.
- Write modular code that is easy to maintain and extend. Break down large functions or classes into smaller, reusable components.
- Ensure that your code is efficient and optimized for performance, especially in critical sections of the application.
- Write clear and descriptive variable and function names that convey their purpose and usage
- Follow SOLID principles to create maintainable and scalable code. Pay particular attention to the Single Responsibility Principle and the Open/Closed Principle.

## Testing Conventions

- Each new feature or component must be tested in a functional way. We are looking for validation of the core functionality and behaviors we expect from the code. This includes edge cases and error handling. However, this means we do NOT use mocking, stubbing, or patching unless absolutely necessary. Agents must ask for permission to use these techniques, and provide strong justification for why they are necessary.
- Write tests that are easy to read and understand.
- Use the convention of test_cases = [(test_input, expected_output), ...] and a for loop to iterate through them in order to reduce code duplication and increase readability.
- Write functional tests that cover a wide range of scenarios, including edge cases.
- Do NOT use mocking or stubbing unless absolutely necessary. Prefer testing the actual behavior of the code.
- Important: - When planning work, always consider how the work will be validated. Validation is a critical and required part of all incremental feature additions and bug fixes.

## Running Commands

- This project has a virtual environment located at `.venv/`.
- **IMPORTANT**: Activate the virtual environment in a standalone command that can be auto-approved: `source .venv/bin/activate`
- This activation command must be run separately, not chained with other commands.
- Only activate the virtual environment when the terminal complains that python is not found.

## Earned Experience

- As agents work on this project and complete tasks, they will gain experience by trying things that don't work. Agents are to request permission to update this very file to add new guidelines based on lessons learned from mistakes made during development.
