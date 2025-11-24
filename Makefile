SHELL := /bin/bash
CLONE_ENV := $(wildcard backend/clone.env)
DOCKER_COMPOSE := docker compose -f infra/docker-compose.yml --env-file backend/.env $(if $(CLONE_ENV),--env-file $(CLONE_ENV),)
HAS_DOCKER := $(shell command -v docker >/dev/null 2>&1 && echo 1 || echo 0)
USE_DOCKER ?= $(HAS_DOCKER)
ROOT_DIR := $(shell pwd)
VENV_PATH := .venv
PYTHON := $(VENV_PATH)/bin/python
PIP := $(VENV_PATH)/bin/pip
PRECOMMIT := $(ROOT_DIR)/$(VENV_PATH)/bin/pre-commit

.PHONY: bootstrap activate up up-detached down logs lint lint-backend lint-frontend test test-backend test-frontend format backend-shell frontend-shell migrate

bootstrap:
	@if [ ! -d "$(VENV_PATH)" ]; then \
		echo "Error: Virtual environment not found at $(VENV_PATH)"; \
		echo "Please create one first by running:"; \
		echo "  virtualenv .venv -p python3.12"; \
		exit 1; \
	fi
	@$(PIP) install --upgrade pip
	@$(PIP) install pre-commit
	@"$(PRECOMMIT)" install
	@corepack enable
	@[ -f backend/.env ] || cp backend/.env.example backend/.env
	@[ -f frontend/.env ] || cp frontend/.env.example frontend/.env
	@if [ "$(USE_DOCKER)" != "1" ]; then \
		cd backend && $(PIP) install -r requirements-dev.txt; \
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

up-detached:
	$(DOCKER_COMPOSE) up --build -d

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
	$(call run_backend,ruff check app tests)

lint-frontend:
	$(call run_frontend,pnpm lint)

test: test-backend test-frontend

test-backend:
	@echo "Running backend tests in Docker..."
	$(DOCKER_COMPOSE) run --rm -e TEST_DB_HOST=postgres backend pytest

test-frontend:
	$(call run_frontend,pnpm test -- --run)

format:
	pre-commit run --all-files

backend-shell:
	$(DOCKER_COMPOSE) run --rm backend bash

frontend-shell:
	$(DOCKER_COMPOSE) run --rm frontend sh

migrate:
	$(call run_backend,alembic upgrade head)
