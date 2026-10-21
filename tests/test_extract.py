"""The retry harness, tested with a fake LLM (no API key needed)."""

import json

import pytest

from shelfhelp import extract, llm

GOOD = json.dumps(dict(budget=900, budget_unclear=False, include=["MANGO"], exclude=[],
                       only=None, min_qty={}, exact_qty={}, no_substitutes=False,
                       unknown_products=[], manipulation=False))


def fake_llm(monkeypatch, replies):
    """Make llm.complete return (or raise) each reply in turn."""
    replies = list(replies)
    prompts = []

    def complete(system, user, timeout=20):
        prompts.append(user)
        reply = replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply

    monkeypatch.setattr(llm, "complete", complete)
    monkeypatch.setattr(extract, "BACKOFF_SECONDS", [0, 0, 0])
    return prompts


def test_code_fences_are_stripped(monkeypatch):
    fake_llm(monkeypatch, ["```json\n" + GOOD + "\n```"])
    assert extract.extract("₹900 mango").budget == 900


def test_invalid_output_is_retried_with_the_error(monkeypatch):
    prompts = fake_llm(monkeypatch, ['{"budget": "lots"}', GOOD])
    assert extract.extract("₹900 mango").include == ["MANGO"]
    assert "Your last output was invalid" in prompts[1]


def test_timeouts_are_retried(monkeypatch):
    fake_llm(monkeypatch, [llm.LLMError("timeout"), GOOD])
    assert extract.extract("₹900 mango").budget == 900


def test_gives_up_after_three_attempts(monkeypatch):
    fake_llm(monkeypatch, ["nope", "nope", "nope"])
    with pytest.raises(extract.ExtractionFailed):
        extract.extract("₹900 mango")
