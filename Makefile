# pkgtk CI entry points. Deps: pip install -e .[dev]
.PHONY: ci lint test bench demo eval

ci: lint test

# Agent-eval suite (live codex runs - costs quota; deliberately NOT part of ci).
# `make eval` = 3-task smoke; `make eval-full` = all 28 tasks. OUT is timestamped
# so reruns never collide. Runs under artifacts/ sit inside the repo tree, so the
# project levers (.codex config, skills, AGENTS.md) are ACTIVE; pass
# OUT=/tmp/... for a stock-agent baseline. The report records which applied.
.PHONY: eval eval-full
EVAL_OUT = $(or $(OUT),artifacts/eval-$(shell date +%Y%m%d-%H%M%S))
eval:
	python -m evals.run_eval --out $(EVAL_OUT) --limit 1 $(EVAL_ARGS)

eval-full:
	python -m evals.run_eval --out $(EVAL_OUT) $(EVAL_ARGS)

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
