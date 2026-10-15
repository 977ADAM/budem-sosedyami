.DEFAULT_GOAL := help

UV ?= uv

backend-install: ## Sync Python dependencies with uv
	cd backend && $(UV) sync


dev-backend: ## Run the FastAPI development server
	cd backend && $(UV) run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

migrate: ## Apply application database migrations with Alembic
	cd backend && $(UV) run alembic upgrade head

checkpoint-migrate: ## Apply LangGraph checkpoint migrations
	cd backend && $(UV) run python -m app.migrate_checkpoints

dev-frontend: ## Serve the static chat frontend on the CORS-allowed 127.0.0.1:3000
	cd frontend && python3 -m http.server 3000 --bind 127.0.0.1

frontend-test: ## Run frontend unit tests with the Node test runner
	cd frontend && node --test
