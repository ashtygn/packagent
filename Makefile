# pkgtk CI entry points. Deps: pip install -e .[dev]
.PHONY: ci lint test bench

ci: lint test

lint:
	python -m ruff check .

test:
	python -m pytest

bench:
	python -m benchmarks.run
