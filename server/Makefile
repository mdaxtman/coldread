.PHONY: install dev test lint format format-check typecheck hooks-install hooks-run

install:
	uv sync --extra dev

dev:
	uv run uvicorn main:app --reload

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

typecheck:
	uv run mypy .

hooks-install:
	uv run pre-commit install

hooks-run:
	uv run pre-commit run --all-files
