# pkgtk CI entry points. Deps: pip install -e .[dev]
.PHONY: ci lint test bench demo eval

ci: lint test

# Agent-eval suite (live codex runs - costs quota; deliberately NOT part of ci).
# Usage: make eval [OUT=/path/to/run] [EVAL_ARGS="--families diagnose --limit 3"]
eval:
	python -m evals.run_eval --out $(or $(OUT),artifacts/eval-run) $(EVAL_ARGS)

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
