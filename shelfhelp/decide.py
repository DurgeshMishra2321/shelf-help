"""Turn an Intent into a decision. Every check here is plain code, run in order."""

from dataclasses import dataclass, field

from .catalogue import CATALOGUE
from .models import Intent
from .rules import Order
from .solver import explain_failure, solve


@dataclass
class Decision:
    status: str                      # recommendation | clarification | cannot_fulfil
    intent: Intent                   # the intent the order was checked against
    order: Order = field(default_factory=dict)
    reason: str = ""                 # why we ask / why we can't fulfil
    notes: list[str] = field(default_factory=list)   # extra lines for the message


def drink_name(sku: str) -> str:
    return CATALOGUE[sku]["name"].lower()


def decide(original: Intent) -> Decision:
    intent = original.model_copy(deep=True)   # never edit the caller's intent
    notes = []

    # 1-2. We need exactly one positive budget before we can do anything.
    if intent.budget is None or intent.budget_unclear:
        return Decision("clarification", intent,
                        reason="Could you tell me your budget as a single rupee amount?")
    if intent.budget <= 0:
        return Decision("clarification", intent,
                        reason="Your budget needs to be more than ₹0. What is your budget?")

    # 3. Out-of-stock drinks the customer asked for (today that is BERRY).
    asked_for = (intent.only or []) + intent.include + list(intent.min_qty) + list(intent.exact_qty)
    out_of_stock = [sku for sku in dict.fromkeys(asked_for) if CATALOGUE[sku]["stock"] == 0]
    if out_of_stock:
        names = " and ".join(drink_name(sku) for sku in out_of_stock)
        only_all_gone = intent.only is not None and all(sku in out_of_stock for sku in intent.only)
        if intent.no_substitutes or only_all_gone:
            return Decision("cannot_fulfil", intent,
                            reason=f"Sorry, {names} is out of stock right now.")
        # Otherwise drop them, carry on, and say so in the message.
        intent.include = [s for s in intent.include if s not in out_of_stock]
        intent.min_qty = {s: q for s, q in intent.min_qty.items() if s not in out_of_stock}
        intent.exact_qty = {s: q for s, q in intent.exact_qty.items() if s not in out_of_stock}
        if intent.only is not None:
            intent.only = [s for s in intent.only if s not in out_of_stock]
        notes.append(f"{names.capitalize()} is out of stock, so I left it out.")

    # 4. Products we don't sell. They block the order only if the customer needs them.
    if intent.unknown_products:
        names = ", ".join(intent.unknown_products)
        if intent.no_substitutes or intent.only is not None:
            return Decision("cannot_fulfil", intent,
                            reason=f"Sorry, we don't carry {names}.")
        notes.append(f"We don't carry {names}, so I left it out.")

    # Manipulation: prices and rules never change. Quantities that only make
    # sense with the injected rules (more than we stock) are ignored, and the
    # customer still gets a valid order at real prices. See DECISIONS.md.
    if intent.manipulation:
        for qty_rule in (intent.min_qty, intent.exact_qty):
            for sku in list(qty_rule):
                if qty_rule[sku] > CATALOGUE[sku]["stock"]:
                    del qty_rule[sku]
        notes.append("I can't change prices, stock or rules, but here is a valid order.")

    # 5. Let the solver find the best valid order.
    order = solve(intent)
    if order is None:
        return Decision("cannot_fulfil", intent, reason=explain_failure(intent), notes=notes)

    # 6. Recommendation.
    return Decision("recommendation", intent, order=order, notes=notes)
