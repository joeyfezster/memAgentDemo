SHELL := /bin/bash
DOCKER_COMPOSE := docker compose -f infra/docker-compose.yml
HAS_DOCKER := $(shell command -v docker >/dev/null 2>&1 && echo 1 || echo 0)
USE_DOCKER ?= $(HAS_DOCKER)
ROOT_DIR := $(shell pwd)
VENV_PATH := .venv
PYTHON := $(VENV_PATH)/bin/python
PIP := $(VENV_PATH)/bin/pip
POETRY := $(ROOT_DIR)/$(VENV_PATH)/bin/poetry
PRECOMMIT := $(ROOT_DIR)/$(VENV_PATH)/bin/pre-commit

.PHONY: bootstrap activate up down logs lint lint-backend lint-frontend test test-backend test-frontend format backend-shell frontend-shell migrate test-letta

bootstrap:
	@if [ ! -d "$(VENV_PATH)" ]; then \
		echo "Error: Virtual environment not found at $(VENV_PATH)"; \
		echo "Please create one first by running:"; \
		echo "  virtualenv .venv -p python3.12"; \
		exit 1; \
	fi
	@$(PIP) install --upgrade pip
	@$(PIP) install pre-commit poetry==1.8.4
	@"$(PRECOMMIT)" install
	@corepack enable
	@[ -f backend/.env ] || cp backend/.env.example backend/.env
	@[ -f frontend/.env ] || cp frontend/.env.example frontend/.env
	@if [ "$(USE_DOCKER)" != "1" ]; then \
		cd backend && "$(POETRY)" install --with dev; \
	fi
	@if [ "$(USE_DOCKER)" != "1" ]; then \
		cd frontend && pnpm install; \
	fi
	@echo "Bootstrap complete."

activate:
	@if [ ! -d "$(VENV_PATH)" ]; then \
		echo "Error: Virtual environment not found at $(VENV_PATH)"; \
		echo "Please create one first by running:"; \
		echo "  virtualenv .venv -p python3.12"; \
		exit 1; \
	fi
	@echo "To activate the virtual environment, run:"
	@echo "  source $(VENV_PATH)/bin/activate"

up:
	$(DOCKER_COMPOSE) up --build

down:
	$(DOCKER_COMPOSE) down --remove-orphans

logs:
	$(DOCKER_COMPOSE) logs -f

define run_backend
	@if [ "$(USE_DOCKER)" = "1" ]; then \
	$(DOCKER_COMPOSE) run --rm backend $(1); \
	else \
	cd backend && $(1); \
	fi
endef

define run_frontend
	@if [ "$(USE_DOCKER)" = "1" ]; then \
	$(DOCKER_COMPOSE) run --rm frontend $(1); \
	else \
	cd frontend && $(1); \
	fi
endef

lint: lint-backend lint-frontend

lint-backend:
	$(call run_backend,"$(POETRY)" run ruff check app tests)

lint-frontend:
	$(call run_frontend,pnpm lint)

test: test-backend test-frontend

test-backend:
	$(call run_backend,poetry run pytest tests/unit/)

test-frontend:
	$(call run_frontend,pnpm test -- --run)

format:
	pre-commit run --all-files

backend-shell:
	$(DOCKER_COMPOSE) run --rm backend bash

frontend-shell:
	$(DOCKER_COMPOSE) run --rm frontend sh

migrate:
	$(call run_backend,poetry run alembic upgrade head)

db-seed:
	@echo "Seeding database..."
	@if [ "$(USE_DOCKER)" = "1" ]; then \
		docker exec infra-backend-1 python -c "from app.db.session import get_db; from app.db.seed import seed_database; import asyncio; asyncio.run(next(get_db().__aiter__()).__anext__().then(lambda db: seed_database(db)))"; \
	else \
		cd backend && poetry run python -c "from app.db.session import get_db; from app.db.seed import seed_database; import asyncio; async def run(): async for db in get_db(): await seed_database(db); break; asyncio.run(run())"; \
	fi

test-letta:
	@cd backend && ../.venv/bin/poetry run pytest tests/letta/ -v
