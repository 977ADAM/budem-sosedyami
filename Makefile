.DEFAULT_GOAL := help

UV ?= uv

backend-install: ## Sync Python dependencies with uv
	cd backend && $(UV) sync


dev-backend: ## Run the FastAPI development server
	cd backend && $(UV) run uvicorn app.main:app --reload --no-access-log --host 127.0.0.1 --port 8000

loadtest-server: ## Run the backend with a fake model on :8100 for load tests
	cd backend && $(UV) run uvicorn loadtest.stub_server:app --no-access-log --host 127.0.0.1 --port 8100

loadtest: ## Load test :8100 (USERS=100 TURNS=35); run several in parallel above ~200 users
	cd backend && $(UV) run python -m loadtest.run --users $(or $(USERS),100) --turns $(or $(TURNS),35)

dev-frontend: ## Serve the static chat frontend on the CORS-allowed 127.0.0.1:3000
	cd frontend && python3 -m http.server 3000 --bind 127.0.0.1
