.PHONY: install install-dev dev-backend dev-frontend dev db-up db-down db-upgrade test lint format fmt typecheck check clean

# ── UV-based Backend ──────────────────────────────────────────────

install:
	cd backend && uv sync

install-dev:
	cd backend && uv sync --extra dev

dev-backend:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

test:
	cd backend && uv run pytest -q

lint:
	cd backend && uv run ruff check .

format:
	cd backend && uv run ruff format .

fmt: format

typecheck:
	cd backend && uv run pyright

check: lint typecheck test

db-upgrade:
	cd backend && uv run alembic upgrade head

# ── Frontend ──────────────────────────────────────────────────────

frontend-install:
	cd frontend && npm install

dev-frontend:
	cd frontend && npm run dev

# ── Convenience ───────────────────────────────────────────────────

dev: ## Start backend + frontend (run in separate terminals)
	@echo "Run in two terminals:"
	@echo "  make dev-backend"
	@echo "  make dev-frontend"

db-up: ## Start PostgreSQL via docker
	docker compose up -d db

db-down:
	docker compose down

clean:
	rm -rf backend/.venv backend/__pycache__ backend/.pytest_cache
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
