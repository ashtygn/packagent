"""Provider replay tests: cassette replay works with no network; cache miss fails."""

import pytest

from pkgtk.llm.cassette import CacheMiss
from pkgtk.llm.provider import CassetteProvider, FakeProvider
from pkgtk.schemas import schemas_dir

CASSETTES = schemas_dir().parent / "fixtures" / "synthetic" / "llm_cassettes"

MODEL = "claude-fable-5"
SYSTEM = ("You extract package design rules into Rule-IR. "
          "Respond with structured output.")
MESSAGES = [{"role": "user",
             "content": "Extract the minimum trace width rule from: "
                        "Trace width Min 25 um."}]


def test_replay_returns_recorded_response():
    provider = CassetteProvider(CASSETTES, live=False)
    resp = provider.complete(MODEL, SYSTEM, MESSAGES, None)
    assert resp["parameter"] == "trace_width_min"
    assert resp["value"]["number"] == 25


def test_cache_miss_raises_in_replay_mode():
    provider = CassetteProvider(CASSETTES, live=False)
    with pytest.raises(CacheMiss):
        provider.complete(MODEL, SYSTEM,
                          [{"role": "user", "content": "a different prompt"}], None)


def test_token_usage_logged():
    provider = CassetteProvider(CASSETTES, live=False)
    provider.complete(MODEL, SYSTEM, MESSAGES, None)
    assert provider.token_log and provider.token_log[0]["model"] == MODEL


def test_live_mode_records(tmp_path):
    fake = FakeProvider({})
    # Pre-seed the fake to answer the exact call.
    from pkgtk.llm.cassette import cassette_key
    key = cassette_key(MODEL, SYSTEM, MESSAGES, None)
    fake._responses[key] = {"ok": True}
    provider = CassetteProvider(tmp_path, live_provider=fake, live=True)
    resp = provider.complete(MODEL, SYSTEM, MESSAGES, None)
    assert resp == {"ok": True}
    # Recorded to the cassette dir; a subsequent replay finds it.
    replay = CassetteProvider(tmp_path, live=False)
    assert replay.complete(MODEL, SYSTEM, MESSAGES, None) == {"ok": True}
