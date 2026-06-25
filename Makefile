run:
	uv run uvicorn app.main:app --reload

lint:
	flake8 app
	uv run mypy app --exclude=.venv

test:
	uv run pytest -v
