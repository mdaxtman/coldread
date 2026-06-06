.PHONY: check check-backend check-frontend

# Run all checks that CI runs — lint, type-check, and tests for both backend and frontend.
# Use this before pushing to catch failures locally instead of in CI.
check: check-backend check-frontend

check-backend:
	cd server && uv run ruff check . && uv run ruff format --check . && uv run mypy . && uv run pytest

check-frontend:
	cd client && npx tsc --noEmit && npx eslint . && npx vite build && npx vitest run
