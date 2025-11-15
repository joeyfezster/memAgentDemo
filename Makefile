SHELL := /bin/bash
DOCKER_COMPOSE := docker compose -f infra/docker-compose.yml
HAS_DOCKER := $(shell command -v docker >/dev/null 2>&1 && echo 1 || echo 0)
USE_DOCKER ?= $(HAS_DOCKER)

.PHONY: bootstrap up down logs lint lint-backend lint-frontend test test-backend test-frontend format backend-shell frontend-shell migrate

bootstrap:
	@python3 -m pip install --upgrade pip
	@python3 -m pip install pre-commit poetry==1.8.4
	@pre-commit install
	@corepack enable
	@[ -f backend/.env ] || cp backend/.env.example backend/.env
	@[ -f frontend/.env ] || cp frontend/.env.example frontend/.env
	@if [ "$(USE_DOCKER)" != "1" ]; then \
		cd backend && poetry install --with dev; \
	fi
	@if [ "$(USE_DOCKER)" != "1" ]; then \
		cd frontend && pnpm install; \
	fi
	@echo "Bootstrap complete."

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
	$(call run_backend,poetry run ruff check app tests)
	$(call run_backend,poetry run black --check app tests)
	$(call run_backend,poetry run isort --check-only app tests)

lint-frontend:
	$(call run_frontend,pnpm lint)
	$(call run_frontend,pnpm format)

test: test-backend test-frontend

test-backend:
	$(call run_backend,poetry run pytest)

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
