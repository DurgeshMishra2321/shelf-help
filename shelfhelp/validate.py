"""Final check of every response before it is printed, plus the safe fallback."""

from pydantic import ValidationError

from .catalogue import CATALOGUE
from .models import Intent, Response
from .rules import RULES, total

FALLBACK = {
    "status": "clarification",
    "items": [],
    "total": 0,
    "message": "Sorry, I couldn't process that. Could you tell me your budget and which drinks you want?",
}


def fallback_response() -> dict:
    return dict(FALLBACK, items=[])


def problems(response: dict, intent: Intent | None) -> list[str]:
    """Return everything wrong with the response. An empty list means it is valid."""
    try:
        parsed = Response.model_validate(response)
    except ValidationError as e:
        return [f"schema: {e}"]

    found = []
    order = {}
    for item in parsed.items:
        if item.sku not in CATALOGUE:
            found.append(f"{item.sku} is not in the catalogue")
            continue
        if item.sku in order:
            found.append(f"{item.sku} appears twice")
        if not 1 <= item.quantity <= CATALOGUE[item.sku]["stock"]:
            found.append(f"{item.sku} quantity {item.quantity} is outside 1..stock")
        order[item.sku] = item.quantity
    if found:
        return found

    if parsed.total != total(order):
        found.append(f"total {parsed.total} does not match the real sum {total(order)}")

    if parsed.status == "recommendation":
        if intent is None or intent.budget is None:
            found.append("recommendation without a budget")
        else:
            for rule in RULES:
                ok, reason = rule(order, intent)
                if not ok:
                    found.append(f"{rule.__name__}: {reason}")
    elif parsed.items or parsed.total != 0:
        found.append(f"{parsed.status} must have no items and total 0")
    return found
