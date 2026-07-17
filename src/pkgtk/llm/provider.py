"""LLM provider abstraction. Only this module may touch the Anthropic SDK.

Structured outputs are constrained to a JSON Schema; temperature 0; bounded retries.
Tests inject a fake or replay from cassettes. CI is replay-only (PKGTK_LLM_LIVE unset)
and fails on cache miss; live mode records new cassettes.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol

from pkgtk.llm.cassette import CacheMiss, Cassette, cassette_key

DEFAULT_MODEL = "claude-fable-5"


class Provider(Protocol):
    def complete(self, model: str, system: str, messages: list,
                 schema: dict | None = None) -> dict:
        ...


class FakeProvider:
    """Deterministic provider for unit tests: keyed canned responses."""

    def __init__(self, responses: dict[str, dict], usage_log: list | None = None):
        self._responses = responses
        self.calls: list = []

    def complete(self, model, system, messages, schema=None) -> dict:
        key = cassette_key(model, system, messages, schema)
        self.calls.append(key)
        if key not in self._responses:
            raise CacheMiss(key)
        return self._responses[key]


class CassetteProvider:
    """Replay from / record to a cassette dir. Wraps a live provider in record mode."""

    def __init__(self, cassette_dir: str | Path, live_provider: Provider | None = None,
                 live: bool | None = None):
        self.cassette = Cassette(cassette_dir)
        self.live_provider = live_provider
        self.live = (os.environ.get("PKGTK_LLM_LIVE") == "1") if live is None else live
        self.token_log: list[dict] = []

    def complete(self, model, system, messages, schema=None) -> dict:
        key = cassette_key(model, system, messages, schema)
        if not self.live:
            resp = self.cassette.get(key)  # raises CacheMiss -> CI fails loudly
            self._log(model, key, resp)
            return resp
        if self.live_provider is None:
            raise RuntimeError("live mode requires a live_provider")
        resp = self.live_provider.complete(model, system, messages, schema)
        self.cassette.put(key, resp)
        self._log(model, key, resp)
        return resp

    def _log(self, model, key, resp):
        self.token_log.append({"model": model, "key": key,
                               "usage": resp.get("_usage")})


class AnthropicProvider:
    """Real Anthropic provider (imported lazily; used only in live mode)."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

    def complete(self, model, system, messages, schema=None) -> dict:
        import anthropic  # lazy: never imported in replay CI

        client = anthropic.Anthropic(api_key=self.api_key)
        tools = None
        tool_choice = None
        if schema is not None:
            tools = [{"name": "emit", "description": "emit structured result",
                      "input_schema": schema}]
            tool_choice = {"type": "tool", "name": "emit"}
        resp = client.messages.create(
            model=model, system=system, messages=messages, temperature=0,
            max_tokens=4096, tools=tools, tool_choice=tool_choice,
        )
        out = {}
        for block in resp.content:
            if getattr(block, "type", None) == "tool_use":
                out = block.input
        out["_usage"] = {"input_tokens": resp.usage.input_tokens,
                         "output_tokens": resp.usage.output_tokens}
        return out
