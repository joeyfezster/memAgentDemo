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

.PHONY: bootstrap activate up up-detached down logs lint lint-backend lint-frontend test test-backend test-frontend format backend-shell frontend-shell migrate demo

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
	$(DOCKER_COMPOSE) run --rm -e TEST_DB_HOST=postgres backend pytest -m "not expensive"

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

demo:
	@echo "🎬 Setting up demo environment..."
	@echo ""
	@echo "Checking prerequisites..."
	@command -v docker >/dev/null 2>&1 || { echo "❌ Error: docker not found. Please install Docker"; exit 1; }
	@command -v corepack >/dev/null 2>&1 || { echo "❌ Error: corepack not found. Please install Node.js 20+"; exit 1; }
	@command -v pnpm >/dev/null 2>&1 || { echo "❌ Error: pnpm not found. Please run: corepack enable"; exit 1; }
	@echo "✅ Prerequisites checked"
	@echo ""
	@echo "Ensuring clean frontend build..."
	@rm -rf frontend/node_modules/.vite
	@echo ""
	@echo "Cleaning previous containers and volumes..."
	@$(MAKE) down 2>/dev/null || true
	@docker volume rm $$(docker volume ls -q | grep "$$(grep '^COMPOSE_PROJECT_NAME=' backend/clone.env 2>/dev/null | cut -d'=' -f2 || echo 'memAgentDemo')" 2>/dev/null) 2>/dev/null || true
	@echo ""
	@echo "Starting services in detached mode..."
	@$(MAKE) up-detached
	@echo ""
	@echo "Waiting for services to be ready..."
	@./scripts/wait_for_services.sh
	@echo ""
	@echo "Services are ready. Database seeding happens automatically on startup."
	@echo "Daniel persona seed data includes:"
	@echo "  - Phoenix Golf Course Path-to-Purchase Analysis (7 days ago)"
	@echo "  - Topgolf Scottsdale Outlet Prioritization (3 days ago)"
	@echo "  - Austin Golf Launch Performance Review (10 days ago)"
	@echo ""
	@echo "🎭 Running Playwright demo with video recording..."
	@echo "   Login: daniel.insights@goldtobacco.com"
	@echo "   Password: changeme123"
	@echo ""
	@FRONTEND_PORT=$$(if [ -f backend/clone.env ]; then grep '^FRONTEND_PORT=' backend/clone.env 2>/dev/null | cut -d'=' -f2; else echo '5173'; fi); \
	cd e2e && FRONTEND_PORT=$${FRONTEND_PORT:-5173} pnpm playwright test --config=playwright.config.demo.ts
	@echo ""
	@echo "✅ Demo completed!"
	@echo ""
	@echo "📹 Videos saved in: e2e/test-results/"
	@echo "📊 HTML report: e2e/playwright-report/index.html"
	@echo ""
	@echo "To view the report:"
	@echo "  open e2e/playwright-report/index.html"
	@echo ""
	@echo "To stop services:"
	@echo "  make down"

demo-no_drop:
	@echo "🎭 Running Playwright demo (no rebuild)..."
	@echo "   Login: daniel.insights@goldtobacco.com"
	@echo "   Password: changeme123"
	@echo ""
	@FRONTEND_PORT=$$(if [ -f backend/clone.env ]; then grep '^FRONTEND_PORT=' backend/clone.env 2>/dev/null | cut -d'=' -f2; else echo '5173'; fi); \
	cd e2e && FRONTEND_PORT=$${FRONTEND_PORT:-5173} pnpm playwright test --config=playwright.config.demo.ts
	@echo ""
	@echo "✅ Demo completed!"
	@echo ""
	@echo "📹 Videos saved in: e2e/test-results/"
	@echo "📊 HTML report: e2e/playwright-report/index.html"
	@echo ""
	@echo "To view the report:"
	@echo "  open e2e/playwright-report/index.html"
