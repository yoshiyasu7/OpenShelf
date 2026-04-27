# Start localhost
run:
	python -B -m src.interfaces.main

run-dev:
	find src -type d -name '__pycache__' -exec rm -r {} + && python -B -m src.interfaces.main

test:
	PYTHONDONTWRITEBYTECODE=1 poetry run pytest

docker-test:
	@if [ ! -f deployment/.env ]; then \
		echo "Error: deployment/.env not found."; \
		echo "Create it manually from deployment/.env.example and set your values."; \
		exit 1; \
	fi
	docker compose -f deployment/docker-compose.yml up --build

docker-test-down:
	docker compose -f deployment/docker-compose.yml down --remove-orphans


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
