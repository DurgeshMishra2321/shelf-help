"""run.py end to end, with a fake LLM (no API key needed)."""

import json
import sys

import run
from shelfhelp import llm

from test_extract import GOOD, fake_llm


def test_respond_gives_a_valid_recommendation(monkeypatch):
    fake_llm(monkeypatch, [GOOD])
    response = run.respond("₹900, I want mango")
    assert response["status"] == "recommendation"
    assert response["total"] == 900


def test_respond_falls_back_when_extraction_fails(monkeypatch):
    fake_llm(monkeypatch, ["junk", "junk", "junk"])
    response = run.respond("₹900, I want mango")
    assert response["status"] == "clarification" and response["items"] == []


def test_batch_keeps_order_and_survives_bad_requests(monkeypatch, tmp_path, capsys):
    fake_llm(monkeypatch, [GOOD, GOOD])
    monkeypatch.setattr(llm, "check_config", lambda: None)
    path = tmp_path / "requests.json"
    path.write_text(json.dumps([
        {"id": "a", "text": "₹900 mango"},
        {"id": "b"},                       # missing text
        "not an object",
        {"id": "c", "text": "₹900 mango"},
    ]), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["run.py", str(path)])
    run.main()
    results = json.loads(capsys.readouterr().out)   # stdout must be pure JSON
    assert [r["id"] for r in results] == ["a", "b", None, "c"]
    assert results[1]["response"]["status"] == "clarification"
    assert results[3]["response"]["status"] == "recommendation"
