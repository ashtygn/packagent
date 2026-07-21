"""Agent-eval harness: seeded-defect tasks for Codex agents, graded offline.

The behavioral fine-tuning loop for the Codex 5.6 agents (see
docs/codex-agent-finetune-plan.md): generate tasks from the Phase-1 benchmark
machinery, run them through `codex exec --json`, and score with zero-LLM graders
built on the pkgtk exit-code contract.
"""
