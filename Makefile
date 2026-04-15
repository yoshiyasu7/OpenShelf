# Start localhost
run:
	python -B -m src.interfaces.main

run-dev:
	find src -type d -name '__pycache__' -exec rm -r {} + && python -B -m src.interfaces.main

test:
	PYTHONDONTWRITEBYTECODE=1 poetry run pytest


# Check formatting
.DEFAULT_GOAL := check

format:
	poetry run ruff format .
	poetry run ruff check --fix .

check:
	@echo "1/2 Running Ruff (Linting & Formatting check)..."
	poetry run ruff check .
	poetry run ruff format --check .
	@echo "2/2 Running Basedpyright (Type checking)..."
	poetry run basedpyright

clean:
	rm -rf .ruff_cache .basedpyright_cache .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
