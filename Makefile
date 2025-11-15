.PHONY: help bootstrap up down restart logs clean test lint format backend-shell frontend-shell db-shell migrate build

# Color output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

# Docker Compose files
COMPOSE_FILE := infra/docker-compose.yml
COMPOSE_DEV_FILE := infra/docker-compose.dev.yml

help: ## Show this help message
	@echo "$(GREEN)Memory Agent Development Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

bootstrap: ## Initialize development environment
	@echo "$(GREEN)Bootstrapping development environment...$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)Creating .env from .env.example...$(NC)"; \
		cp .env.example .env; \
	else \
		echo "$(YELLOW).env already exists, skipping...$(NC)"; \
	fi
	@if [ ! -f backend/.env ]; then \
		echo "$(YELLOW)Creating backend/.env from backend/.env.example...$(NC)"; \
		cp backend/.env.example backend/.env; \
	else \
		echo "$(YELLOW)backend/.env already exists, skipping...$(NC)"; \
	fi
	@if [ ! -f frontend/.env ]; then \
		echo "$(YELLOW)Creating frontend/.env from frontend/.env.example...$(NC)"; \
		cp frontend/.env.example frontend/.env; \
	else \
		echo "$(YELLOW)frontend/.env already exists, skipping...$(NC)"; \
	fi
	@if command -v pre-commit >/dev/null 2>&1; then \
		echo "$(GREEN)Installing pre-commit hooks...$(NC)"; \
		pre-commit install; \
	else \
		echo "$(YELLOW)pre-commit not installed. Install with: pip install pre-commit$(NC)"; \
	fi
	@echo "$(GREEN)Bootstrap complete!$(NC)"
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. Edit .env files with your configuration"
	@echo "  2. Run 'make up' to start all services"

up: ## Start all services
	@echo "$(GREEN)Starting all services...$(NC)"
	docker-compose -f $(COMPOSE_FILE) up -d
	@echo "$(GREEN)Services started!$(NC)"
	@echo "$(YELLOW)Frontend:$(NC) http://localhost:5173"
	@echo "$(YELLOW)Backend:$(NC) http://localhost:8000"
	@echo "$(YELLOW)Letta:$(NC) http://localhost:8080"

up-dev: ## Start all services in development mode
	@echo "$(GREEN)Starting services in development mode...$(NC)"
	docker-compose -f $(COMPOSE_FILE) -f $(COMPOSE_DEV_FILE) up -d
	@echo "$(GREEN)Services started!$(NC)"
	@echo "$(YELLOW)Frontend:$(NC) http://localhost:5173"
	@echo "$(YELLOW)Backend:$(NC) http://localhost:8000"
	@echo "$(YELLOW)Letta:$(NC) http://localhost:8080"
	@echo "$(YELLOW)PGAdmin:$(NC) http://localhost:5050"

down: ## Stop all services
	@echo "$(RED)Stopping all services...$(NC)"
	docker-compose -f $(COMPOSE_FILE) -f $(COMPOSE_DEV_FILE) down

restart: down up ## Restart all services

logs: ## View logs from all services
	docker-compose -f $(COMPOSE_FILE) logs -f

logs-backend: ## View backend logs
	docker-compose -f $(COMPOSE_FILE) logs -f backend

logs-frontend: ## View frontend logs
	docker-compose -f $(COMPOSE_FILE) logs -f frontend

logs-letta: ## View Letta agent logs
	docker-compose -f $(COMPOSE_FILE) logs -f letta

build: ## Build all Docker images
	@echo "$(GREEN)Building all Docker images...$(NC)"
	docker-compose -f $(COMPOSE_FILE) build

build-backend: ## Build backend Docker image
	@echo "$(GREEN)Building backend Docker image...$(NC)"
	docker-compose -f $(COMPOSE_FILE) build backend

build-frontend: ## Build frontend Docker image
	@echo "$(GREEN)Building frontend Docker image...$(NC)"
	docker-compose -f $(COMPOSE_FILE) build frontend

test: ## Run all tests
	@echo "$(GREEN)Running all tests...$(NC)"
	@$(MAKE) test-backend
	@$(MAKE) test-frontend

test-backend: ## Run backend tests
	@echo "$(GREEN)Running backend tests...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec backend pytest

test-frontend: ## Run frontend tests
	@echo "$(GREEN)Running frontend tests...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec frontend npm test

test-coverage: ## Run tests with coverage
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec backend pytest --cov
	docker-compose -f $(COMPOSE_FILE) exec frontend npm run test:coverage

lint: ## Run linters for all services
	@echo "$(GREEN)Running linters...$(NC)"
	@$(MAKE) lint-backend
	@$(MAKE) lint-frontend

lint-backend: ## Run backend linter
	@echo "$(GREEN)Running backend linter...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec backend ruff check app/
	docker-compose -f $(COMPOSE_FILE) exec backend mypy app/

lint-frontend: ## Run frontend linter
	@echo "$(GREEN)Running frontend linter...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec frontend npm run lint

format: ## Format code for all services
	@echo "$(GREEN)Formatting code...$(NC)"
	@$(MAKE) format-backend
	@$(MAKE) format-frontend

format-backend: ## Format backend code
	@echo "$(GREEN)Formatting backend code...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec backend black app/ tests/
	docker-compose -f $(COMPOSE_FILE) exec backend isort app/ tests/
	docker-compose -f $(COMPOSE_FILE) exec backend ruff check --fix app/ tests/

format-frontend: ## Format frontend code
	@echo "$(GREEN)Formatting frontend code...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec frontend npm run format

backend-shell: ## Open a shell in the backend container
	@echo "$(GREEN)Opening backend shell...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec backend /bin/bash

frontend-shell: ## Open a shell in the frontend container
	@echo "$(GREEN)Opening frontend shell...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec frontend /bin/sh

db-shell: ## Open a PostgreSQL shell
	@echo "$(GREEN)Opening database shell...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec postgres psql -U postgres -d memagent

migrate: ## Run database migrations
	@echo "$(GREEN)Running database migrations...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec backend alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MSG="description")
	@echo "$(GREEN)Creating new migration...$(NC)"
	@if [ -z "$(MSG)" ]; then \
		echo "$(RED)Error: MSG is required. Usage: make migrate-create MSG='description'$(NC)"; \
		exit 1; \
	fi
	docker-compose -f $(COMPOSE_FILE) exec backend alembic revision --autogenerate -m "$(MSG)"

migrate-down: ## Rollback last migration
	@echo "$(YELLOW)Rolling back last migration...$(NC)"
	docker-compose -f $(COMPOSE_FILE) exec backend alembic downgrade -1

clean: ## Clean up containers, volumes, and build artifacts
	@echo "$(RED)Cleaning up...$(NC)"
	docker-compose -f $(COMPOSE_FILE) -f $(COMPOSE_DEV_FILE) down -v
	@echo "$(YELLOW)Removing build artifacts...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "coverage" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)Clean complete!$(NC)"

ps: ## Show running containers
	docker-compose -f $(COMPOSE_FILE) ps

health: ## Check health of all services
	@echo "$(GREEN)Checking service health...$(NC)"
	@docker-compose -f $(COMPOSE_FILE) ps --format json | jq -r '.[] | "\(.Name): \(.Health)"' || docker-compose -f $(COMPOSE_FILE) ps
