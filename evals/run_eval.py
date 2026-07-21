"""Run the agent-eval suite through `codex exec --json` and grade the results.

Usage:
    python -m evals.run_eval --out /tmp/eval-run [--families diagnose,fix,ecodiff]
        [--limit N] [--model SLUG] [--timeout SECS] [--ephemeral] [--dry-run]

Each task's work/ dir is the agent cwd; the prompt is work/task.md verbatim. Grading
is deterministic (evals.graders). The report lands at <out>/report.json + report.md.

NEVER wired into `make ci` - live model calls cost quota and violate the no-network
test rule. Run deliberately.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path

from evals.graders import grade
from evals.task_gen import FAMILIES, build_tasks


def _parse_events(stdout: str) -> list[dict]:
    events = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue  # non-JSON noise on stdout is not fatal
    return events


def _summarize_events(events: list[dict]) -> dict:
    summary = {
        "thread_id": None,
        "turn_status": None,
        "usage": None,
        "n_commands": 0,
        "n_failed_commands": 0,
        "n_file_changes": 0,
        "errors": [],
    }
    for ev in events:
        etype = ev.get("type")
        if etype == "thread.started":
            summary["thread_id"] = ev.get("thread_id")
        elif etype == "turn.completed":
            summary["turn_status"] = "completed"
            summary["usage"] = ev.get("usage")
        elif etype == "turn.failed":
            summary["turn_status"] = "failed"
            summary["errors"].append((ev.get("error") or {}).get("message"))
        elif etype == "error":
            summary["errors"].append(ev.get("message"))
        elif etype == "item.completed":
            item = ev.get("item") or {}
            itype = item.get("type") or item.get("item_type")
            if itype == "command_execution":
                summary["n_commands"] += 1
                if item.get("exit_code") not in (0, None):
                    summary["n_failed_commands"] += 1
            elif itype == "file_change":
                summary["n_file_changes"] += 1
    return summary


def run_task(
    task_dir: Path,
    codex_bin: str = "codex",
    model: str | None = None,
    timeout: int = 600,
    ephemeral: bool = False,
) -> dict:
    work = task_dir / "work"
    prompt = (work / "task.md").read_text("utf-8")
    cmd = [
        codex_bin, "exec",
        "--json",
        "--skip-git-repo-check",
        "--sandbox", "workspace-write",
        "-C", str(work),
    ]
    if model:
        cmd += ["-m", model]
    if ephemeral:
        cmd.append("--ephemeral")
    cmd.append(prompt)

    started = time.monotonic()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        timed_out = False
        stdout, stderr, exit_code = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as err:
        timed_out = True
        stdout = (err.stdout or b"").decode() if isinstance(err.stdout, bytes) \
            else (err.stdout or "")
        stderr = (err.stderr or b"").decode() if isinstance(err.stderr, bytes) \
            else (err.stderr or "")
        exit_code = None
    wall_secs = round(time.monotonic() - started, 1)

    events = _parse_events(stdout)
    summary = _summarize_events(events)
    graded = grade(task_dir)
    return {
        "task_id": task_dir.name,
        "passed": graded["passed"] and not timed_out,
        "grade_reasons": graded["reasons"] + (["runner timeout"] if timed_out else []),
        "exec_exit_code": exit_code,
        "timed_out": timed_out,
        "wall_secs": wall_secs,
        "stderr_tail": stderr[-2000:],
        **summary,
    }


def _render_report(rows: list[dict], header: dict) -> str:
    lines = [
        "# Agent-eval report",
        "",
        f"- codex: `{header['codex_version']}` | model: "
        f"`{header['model'] or 'harness default'}` | "
        f"passed: **{header['n_passed']}/{header['n_tasks']}**",
        "",
        "| Task | Pass | Cmds (fail) | Tokens out | Secs | First failure reason |",
        "|------|:----:|-------------|-----------|------|----------------------|",
    ]
    for r in rows:
        usage = r.get("usage") or {}
        reason = r["grade_reasons"][0] if r["grade_reasons"] else ""
        lines.append(
            f"| {r['task_id']} | {'yes' if r['passed'] else 'NO'} "
            f"| {r['n_commands']} ({r['n_failed_commands']}) "
            f"| {usage.get('output_tokens', '-')} | {r['wall_secs']} | {reason} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--families", default=",".join(FAMILIES))
    ap.add_argument("--limit", type=int, default=None,
                    help="max tasks per family")
    ap.add_argument("--model", default=None)
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--codex-bin", default="codex")
    ap.add_argument("--ephemeral", action="store_true",
                    help="do not persist codex session rollouts")
    ap.add_argument("--dry-run", action="store_true",
                    help="generate + validate tasks, skip codex runs")
    args = ap.parse_args()

    families = tuple(f for f in args.families.split(",") if f)
    task_ids = build_tasks(args.out, families=families,
                           limit_per_family=args.limit)
    print(f"generated {len(task_ids)} tasks under {args.out}")
    if args.dry_run:
        return 0

    codex_version = subprocess.run(
        [args.codex_bin, "--version"], capture_output=True, text=True
    ).stdout.strip()

    rows = []
    for task_id in task_ids:
        row = run_task(args.out / task_id, codex_bin=args.codex_bin,
                       model=args.model, timeout=args.timeout,
                       ephemeral=args.ephemeral)
        rows.append(row)
        status = "PASS" if row["passed"] else "FAIL"
        print(f"[{status}] {task_id} ({row['wall_secs']}s, "
              f"{row['n_commands']} cmds) {row['grade_reasons'][:1]}")

    header = {
        "codex_version": codex_version,
        "model": args.model,
        "families": families,
        "n_tasks": len(rows),
        "n_passed": sum(1 for r in rows if r["passed"]),
    }
    (args.out / "report.json").write_text(
        json.dumps({"header": header, "rows": rows}, indent=1), encoding="utf-8")
    (args.out / "report.md").write_text(_render_report(rows, header),
                                        encoding="utf-8")
    print(f"passed {header['n_passed']}/{header['n_tasks']}; "
          f"report at {args.out / 'report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
