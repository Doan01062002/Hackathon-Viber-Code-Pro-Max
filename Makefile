.PHONY: install run run-fe test test-ai test-be lint format boundaries check clean

install:
	pip install -r requirements.txt
	cd frontend && npm install

# --- chạy ---
run:
	uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

run-fe:
	cd frontend && npm run dev

# --- test theo module ---
test: test-ai test-be

test-ai:
	cd ai && pytest tests/ -v

test-be:
	cd backend && pytest tests/ -v

# --- chất lượng ---
lint:
	ruff check ai/ backend/
	cd frontend && npm run lint

format:
	ruff format ai/ backend/

boundaries:
	bash scripts/check_boundaries.sh

check: lint boundaries test

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +
