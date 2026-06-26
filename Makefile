.PHONY: install run test lint fmt typecheck docker

install:
	uv sync

run:
	uv run uvicorn app.main:app --reload

test:
	uv run pytest -m "not live" -v

test-coverage:
	uv run pytest -m "not live" --cov=app --cov-report=term-missing

lint:
	uv run ruff check .

fmt:
	uv run ruff format .
	uv run ruff check --fix .

typecheck:
	uv run mypy app

docker-build:
	docker build -t market-research-multiagent:latest .

docker-run:
	docker compose up

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f api
