"""Build the customer message from a template. The LLM never writes these numbers."""

from .catalogue import CATALOGUE, SKU_ORDER
from .decide import Decision
from .rules import total


def describe_order(order: dict) -> str:
    """{'MANGO': 1, 'LIME': 2} -> '1 case of mango drink and 2 cases of lime soda'"""
    parts = []
    for sku in SKU_ORDER:
        if sku in order:
            qty = order[sku]
            cases = "case" if qty == 1 else "cases"
            parts.append(f"{qty} {cases} of {CATALOGUE[sku]['name'].lower()}")
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " and " + parts[-1]


def build_message(decision: Decision) -> str:
    if decision.status == "recommendation":
        main = (f"I suggest {describe_order(decision.order)}. Total ₹{total(decision.order)}, "
                f"within your ₹{decision.intent.budget} budget.")
    else:
        main = decision.reason
    return " ".join([main] + decision.notes)
