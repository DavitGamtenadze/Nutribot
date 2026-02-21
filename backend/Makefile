.PHONY: lint fmt typecheck test check

lint:
	uv run ruff check app tests

fmt:
	uv run ruff format app tests

typecheck:
	uv run pyright

test:
	uv run pytest

check: lint typecheck test
