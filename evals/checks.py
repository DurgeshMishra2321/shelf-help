"""Property checks for eval responses. They check facts, never wording.

Each check takes (response, case) and returns True if it passes.
A check name can carry an argument after a colon, e.g. "has:MANGO".
"""

from shelfhelp.catalogue import CATALOGUE


def is_recommendation(response, case):
    return response["status"] == "recommendation"


def is_clarification(response, case):
    return response["status"] == "clarification"


def is_cannot_fulfil(response, case):
    return response["status"] == "cannot_fulfil"


def empty_zero(response, case):
    return response["items"] == [] and response["total"] == 0


def has(response, case, sku):
    return any(item["sku"] == sku and item["quantity"] >= 1 for item in response["items"])


def not_has(response, case, sku):
    return not any(item["sku"] == sku for item in response["items"])


def valid_order(response, case):
    """Real SKUs, in stock, no duplicates, correct total, within the case's budget."""
    skus = [item["sku"] for item in response["items"]]
    if not skus or len(skus) != len(set(skus)):
        return False
    real_total = 0
    for item in response["items"]:
        product = CATALOGUE.get(item["sku"])
        if product is None or not 1 <= item["quantity"] <= product["stock"]:
            return False
        real_total += product["price"] * item["quantity"]
    return response["total"] == real_total and real_total <= case["budget"]


def no_rule_breaking(response, case):
    """Either not a recommendation, or a valid order within budget at real prices."""
    if response["status"] != "recommendation":
        return empty_zero(response, case)
    return valid_order(response, case)


def mentions_budget(response, case):
    message = response["message"].lower()
    return "budget" in message or "₹" in message


CHECKS = {
    "is_recommendation": is_recommendation,
    "is_clarification": is_clarification,
    "is_cannot_fulfil": is_cannot_fulfil,
    "empty_zero": empty_zero,
    "has": has,
    "not_has": not_has,
    "valid_order": valid_order,
    "no_rule_breaking": no_rule_breaking,
    "mentions_budget": mentions_budget,
}


def run_check(name: str, response: dict, case: dict) -> bool:
    check_name, _, arg = name.partition(":")
    check = CHECKS[check_name]
    return check(response, case, arg) if arg else check(response, case)
