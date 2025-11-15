# memAgentDemo

A demo project with strict coding standards enforced through automated linting and pre-commit hooks.

## Development Setup

### Install Dependencies

```bash
pip install -r requirements-dev.txt
```

### Set Up Pre-commit Hooks

Install the pre-commit hooks to automatically check code quality before each commit:

```bash
pre-commit install
```

### Linting

Run the linter manually on all files:

```bash
ruff check .
```

Auto-fix issues where possible:

```bash
ruff check --fix .
```

Format code:

```bash
ruff format .
```

### Pre-commit Hooks

The pre-commit hooks will automatically run on staged files before each commit. They include:

- **Ruff linter**: Enforces code quality rules (no commented code, naming conventions, bug detection)
- **Ruff formatter**: Ensures consistent code formatting
- **File checks**: Trailing whitespace, end-of-file fixes, YAML/JSON/TOML validation
- **Security checks**: Detects accidentally committed private keys

To run hooks manually on all files:

```bash
pre-commit run --all-files
```

## Coding Standards

This project enforces strict coding standards:

- **No comments**: Code should be self-documenting through clear naming and structure
- **DRY principle**: Minimize code duplication through abstraction and reuse
- **SOLID principles**: Especially Single Responsibility and Open/Closed principles
- **Modular design**: Break down large functions into smaller, reusable components
- **Performance optimization**: Efficient code in critical sections
- **Clear naming**: Descriptive variable and function names

The linter configuration in `pyproject.toml` enforces these standards and will detect:
- Code style violations
- Potential bugs and anti-patterns
- Commented-out code (ERA rules)
- Code complexity issues
- Performance problems
- Import sorting and organization