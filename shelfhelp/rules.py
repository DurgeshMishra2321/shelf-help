"""Order-level rules. Each rule takes (order, intent) and returns (ok, reason).

To add a new shop rule: write one function here and add it to RULES.
"""

from .catalogue import CATALOGUE

Order = dict[str, int]   # sku -> qty (qty > 0 only)


def total(order: Order) -> int:
    return sum(CATALOGUE[sku]["price"] * qty for sku, qty in order.items())


def within_stock(order, intent):
    for sku, qty in order.items():
        if qty > CATALOGUE[sku]["stock"]:
            return False, f"only {CATALOGUE[sku]['stock']} cases of {sku} in stock"
    return True, ""


def within_budget(order, intent):
    if total(order) > intent.budget:
        return False, f"total ₹{total(order)} is over the ₹{intent.budget} budget"
    return True, ""


def in_stock_only(order, intent):
    for sku in order:
        if CATALOGUE[sku]["stock"] == 0:
            return False, f"{sku} is out of stock"
    return True, ""


def respects_exclusions(order, intent):
    for sku in order:
        if sku in intent.exclude:
            return False, f"{sku} was excluded by the customer"
    return True, ""


def respects_only(order, intent):
    if intent.only is None:
        return True, ""
    for sku in order:
        if sku not in intent.only:
            return False, f"{sku} is not in the customer's 'only' list"
    return True, ""


def respects_includes(order, intent):
    for sku in intent.include:
        if order.get(sku, 0) < 1:
            return False, f"{sku} was requested but is missing"
    return True, ""


def respects_min_qty(order, intent):
    for sku, qty in intent.min_qty.items():
        if order.get(sku, 0) < qty:
            return False, f"need at least {qty} of {sku}"
    return True, ""


def respects_exact_qty(order, intent):
    for sku, qty in intent.exact_qty.items():
        if order.get(sku, 0) != qty:
            return False, f"need exactly {qty} of {sku}"
    return True, ""


def non_empty(order, intent):
    if not order:
        return False, "order is empty"
    return True, ""


RULES = [within_stock, within_budget, in_stock_only, respects_exclusions,
         respects_only, respects_includes, respects_min_qty,
         respects_exact_qty, non_empty]
