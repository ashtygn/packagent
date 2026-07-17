"""Record/replay cassette for LLM calls. CI replays only and fails on cache miss.

Cassette key = stable sha256 of (model, system, messages, schema). Responses are stored
one JSON file per key under a cassette directory.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def cassette_key(model: str, system: str, messages: list, schema: dict | None) -> str:
    payload = json.dumps(
        {"model": model, "system": system, "messages": messages, "schema": schema},
        sort_keys=True, separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


class CacheMiss(KeyError):
    pass


class Cassette:
    def __init__(self, directory: str | Path):
        self.dir = Path(directory)

    def _path(self, key: str) -> Path:
        return self.dir / f"{key}.json"

    def get(self, key: str) -> dict:
        p = self._path(key)
        if not p.is_file():
            raise CacheMiss(key)
        return json.loads(p.read_text("utf-8"))

    def has(self, key: str) -> bool:
        return self._path(key).is_file()

    def put(self, key: str, response: dict) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        self._path(key).write_text(
            json.dumps(response, indent=2, sort_keys=True), "utf-8")
