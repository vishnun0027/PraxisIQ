.PHONY: install lint format type-check test check run clean

install:
	uv sync --all-groups

lint:
	uv run ruff check .

format:
	uv run ruff format .

type-check:
	uv run mypy src/ tests/

test:
	uv run pytest

check: lint type-check test  ## Run all quality checks

run:
	uv run python src/main.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +
