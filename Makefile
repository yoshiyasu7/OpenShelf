# Start localhost
run:
	python -B -m src.interfaces.main

run-dev:
	find src -type d -name '__pycache__' -exec rm -r {} + && python -B -m src.interfaces.main


# Check formatting
black:
	isort --profile black .
	black -l75 .

check: black
	poetry run flake8 .
	poetry run ruff check .
	poetry run mypy .
	poetry run pylint .
