"""Rule-IR deck loader.

Loads a YAML deck, validates each rule against schemas/rule_ir.schema.json (via the
RuleIR pydantic model), and reports malformed decks with cited line numbers where
available. Unknown ``parameter`` values are NOT load errors — they are handled by the
coverage reporter (honest-coverage doctrine).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import ValidationError

from pkgtk.schemas.rule_ir import RuleIR


class DeckError(ValueError):
    """A deck failed to load or a rule failed schema validation."""


@dataclass
class Deck:
    meta: dict
    rules: list[RuleIR]
    path: Path


def load_deck(path: str | Path) -> Deck:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        where = f" at line {mark.line + 1}, column {mark.column + 1}" if mark else ""
        raise DeckError(f"malformed YAML in {p.name}{where}: {exc}") from exc

    if not isinstance(data, dict) or "rules" not in data:
        raise DeckError(f"{p.name}: deck must be a mapping with a 'rules' list")
    raw_rules = data.get("rules")
    if not isinstance(raw_rules, list):
        raise DeckError(f"{p.name}: 'rules' must be a list")

    rules: list[RuleIR] = []
    for i, raw in enumerate(raw_rules):
        rid = raw.get("id", f"<index {i}>") if isinstance(raw, dict) else f"<index {i}>"
        try:
            rules.append(RuleIR.model_validate(raw))
        except ValidationError as exc:
            raise DeckError(
                f"{p.name}: rule {rid!r} failed schema validation:\n{exc}"
            ) from exc

    ids = [r.id for r in rules]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise DeckError(f"{p.name}: duplicate rule ids: {dupes}")

    return Deck(meta=data.get("meta", {}), rules=rules, path=p)
