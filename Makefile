.DEFAULT_GOAL := help
.PHONY: help install backend-install frontend-install dev-backend dev-frontend migrate checkpoint-migrate lint format-check build

UV ?= uv
NPM ?= npm

help: ## Show available commands
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z0-9_-]+:.*## / {printf "  make %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: backend-install frontend-install ## Install backend and frontend dependencies

backend-install: ## Sync Python dependencies with uv
	cd backend && $(UV) sync

frontend-install: ## Install frontend dependencies from package-lock.json
	cd frontend && $(NPM) ci

dev-backend: ## Run the FastAPI development server
	cd backend && $(UV) run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

dev-frontend: ## Run the Vite development server
	cd frontend && $(NPM) run dev

migrate: ## Apply application database migrations with Alembic
	cd backend && $(UV) run alembic upgrade head

checkpoint-migrate: ## Apply LangGraph checkpoint migrations
	cd backend && $(UV) run python -m app.migrate_checkpoints

lint: ## Run frontend ESLint
	cd frontend && $(NPM) run lint

format-check: ## Check frontend formatting with Prettier
	cd frontend && $(NPM) run format:check

build: ## Build the frontend for production
	cd frontend && $(NPM) run build
