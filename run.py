"""The one command:  python run.py requests.json > responses.json

stdout gets ONLY the JSON results. Logs go to stderr and logs/run.jsonl.
"""

import json
import sys
import time

from shelfhelp import llm
from shelfhelp.decide import decide
from shelfhelp.extract import ExtractionFailed, extract
from shelfhelp.log import log
from shelfhelp.message import build_message
from shelfhelp.rules import total
from shelfhelp.validate import fallback_response, problems


def respond(text: str, request_id=None) -> dict:
    """Run one request through the whole pipeline. Never raises."""
    started = time.monotonic()
    attempts, intent, decision, issues, fallback_reason = [], None, None, [], None
    try:
        intent = extract(text, attempts)                      # 1. LLM -> Intent
        decision = decide(intent)                             # 2-3. status + order
        response = {                                          # 4. message from template
            "status": decision.status,
            "items": [{"sku": sku, "quantity": qty} for sku, qty in decision.order.items()],
            "total": total(decision.order),
            "message": build_message(decision),
        }
        issues = problems(response, decision.intent)          # 5. final check
        if issues:
            fallback_reason = "validation failed"
    except ExtractionFailed as e:
        fallback_reason = f"extraction failed: {e}"
    except Exception as e:                                    # never crash the batch
        fallback_reason = f"unexpected error: {type(e).__name__}: {e}"

    if fallback_reason:                                       # 6. safe fallback
        response = fallback_response()

    log("request", id=request_id, text=text, attempts=attempts,
        intent=intent.model_dump() if intent else None,
        decision=decision.status if decision else None,
        validator=issues or "ok", fallback_reason=fallback_reason,
        latency_ms=round((time.monotonic() - started) * 1000))
    return response


def load_requests(path: str) -> list:
    try:
        with open(path, encoding="utf-8-sig") as f:
            data = json.load(f)
    except FileNotFoundError:
        sys.exit(f"error: file not found: {path}")
    except json.JSONDecodeError as e:
        sys.exit(f"error: {path} is not valid JSON: {e}")
    if not isinstance(data, list):
        sys.exit(f"error: {path} must contain a JSON list of {{id, text}} objects")
    return data


def main() -> None:
    # Windows consoles default to a non-UTF-8 encoding; ₹ must print correctly.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    if len(sys.argv) != 2:
        sys.exit("usage: python run.py requests.json > responses.json")

    requests = load_requests(sys.argv[1])
    llm.check_config()

    results = []
    for request in requests:                                  # keep the input order
        if not isinstance(request, dict) or "id" not in request \
                or not isinstance(request.get("text"), str):
            log("bad_request", request=request, fallback_reason="missing id or text")
            request_id = request.get("id") if isinstance(request, dict) else None
            results.append({"id": request_id, "response": fallback_response()})
            continue
        results.append({"id": request["id"], "response": respond(request["text"], request["id"])})

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
