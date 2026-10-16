.DEFAULT_GOAL := help

UV ?= uv

.PHONY: backend-install dev-backend loadtest-server loadtest dev-frontend lint typecheck test check

lint: ## Check Python code with Ruff
	cd backend && $(UV) run --locked ruff check .

typecheck: ## Check backend types with mypy
	cd backend && $(UV) run --locked mypy

test: ## Run backend unit tests
	cd backend && $(UV) run --locked python -m unittest discover -s tests

check: lint typecheck test ## Run all backend checks

backend-install: ## Sync Python dependencies with uv
	cd backend && $(UV) sync


dev-backend: ## Run the FastAPI development server
	cd backend && $(UV) run uvicorn app.main:app --reload --no-access-log --host 127.0.0.1 --port 8000

loadtest-server: ## стресс тест приложения проверка выдержит ли приложение много пользователей
	cd backend && $(UV) run uvicorn loadtest.stub_server:app --no-access-log --host 127.0.0.1 --port 8100

loadtest: ## стресс тест приложения проверка выдержит ли приложение много пользователей
	cd backend && $(UV) run python -m loadtest.run --users $(or $(USERS),100) --turns $(or $(TURNS),35)

dev-frontend:
	cd frontend && python3 -m http.server 3000 --bind 127.0.0.1
