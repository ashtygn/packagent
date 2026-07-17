# pkgtk CI entry points. Deps: pip install -e .[dev]
.PHONY: ci lint test

ci: lint test

lint:
	python -m ruff check .

test:
	python -m pytest
