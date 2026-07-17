# pkgtk CI entry points. Deps: pip install -e .[dev]
.PHONY: ci lint test bench demo

ci: lint test

demo:
	bash scripts/demo.sh

lint:
	python -m ruff check .

test:
	python -m pytest

bench:
	python -m benchmarks.run
	python -m benchmarks.lint_run
	python -m benchmarks.rollup
