"""SQLite model registry with a validated state machine and chase-email generation.

States: requested -> received -> validated -> filed -> stale. Illegal transitions
raise. `intake` runs the IBIS/Touchstone gates and advances state (a failed intake
holds at 'received' with a flag note). No LLM anywhere — jinja2 templates only.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

_MIGRATIONS = Path(__file__).parent / "migrations"
_TEMPLATES = Path(__file__).parent / "templates"

ALLOWED = {
    "requested": {"received"},
    "received": {"received", "validated"},
    "validated": {"filed"},
    "filed": {"stale", "validated"},
    "stale": {"requested", "received"},
}


class TransitionError(ValueError):
    pass


@dataclass(frozen=True)
class ModelKey:
    part: str
    rev: str
    corner: str
    model_type: str


class Registry:
    def __init__(self, db_path: str | Path = ":memory:"):
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self._migrate()

    def _migrate(self) -> None:
        for sql_file in sorted(_MIGRATIONS.glob("*.sql")):
            self.conn.executescript(sql_file.read_text("utf-8"))
        self.conn.commit()

    def add(self, key: ModelKey) -> None:
        self.conn.execute(
            "INSERT INTO models(part, rev, corner, model_type, state, updated) "
            "VALUES(?,?,?,?, 'requested', datetime('now'))",
            (key.part, key.rev, key.corner, key.model_type),
        )
        self.conn.commit()

    def _row(self, key: ModelKey) -> sqlite3.Row:
        row = self.conn.execute(
            "SELECT * FROM models WHERE part=? AND rev=? AND corner=? AND model_type=?",
            (key.part, key.rev, key.corner, key.model_type),
        ).fetchone()
        if row is None:
            raise KeyError(f"no such model: {key}")
        return row

    def state(self, key: ModelKey) -> str:
        return self._row(key)["state"]

    def transition(self, key: ModelKey, new_state: str, note: str = "") -> None:
        current = self.state(key)
        if new_state not in ALLOWED.get(current, set()):
            raise TransitionError(
                f"illegal transition {current!r} -> {new_state!r} for {key}")
        self.conn.execute(
            "UPDATE models SET state=?, note=?, updated=datetime('now') "
            "WHERE part=? AND rev=? AND corner=? AND model_type=?",
            (new_state, note, key.part, key.rev, key.corner, key.model_type),
        )
        self.conn.commit()

    def intake(self, key: ModelKey, model_path: str | Path,
               captured_ibis: str | None = None) -> dict:
        """Run the appropriate gate; advance to validated on pass, else hold."""
        from pkgtk.models.ibis_gate import parse_ibischk_output, run_ibischk
        from pkgtk.models.ts_gate import gate as ts_gate

        p = Path(model_path)
        if p.suffix.lower().startswith(".s") and p.suffix.lower().endswith("p"):
            verdict = ts_gate(p)
            decision = verdict["decision"]
        elif captured_ibis is not None:
            verdict = parse_ibischk_output(captured_ibis)
            decision = verdict["decision"]
        else:
            verdict = run_ibischk(p)
            decision = verdict["decision"]

        if self.state(key) == "requested":
            self.transition(key, "received")
        if decision == "pass":
            self.transition(key, "validated", note="intake passed")
        else:
            self.transition(key, "received", note=f"intake {decision}")
        return verdict

    def all_rows(self) -> list[dict]:
        return [dict(r) for r in self.conn.execute(
            "SELECT * FROM models ORDER BY part, rev, corner, model_type")]

    def chase_email(self, key: ModelKey) -> str:
        row = self._row(key)
        env = Environment(
            loader=FileSystemLoader(str(_TEMPLATES)),
            autoescape=select_autoescape(enabled_extensions=()),
            keep_trailing_newline=True,
        )
        tmpl = env.get_template("chase_email.j2")
        return tmpl.render(**dict(row))
