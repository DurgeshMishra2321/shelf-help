from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .catalogue import CATALOGUE


class Intent(BaseModel):
    """What the customer asked for. The LLM fills this in; it is never an order."""

    budget: int | None              # rupees; None if missing
    budget_unclear: bool            # ranges, two numbers, "not much", etc.
    include: list[str]              # SKUs the customer wants present
    exclude: list[str]              # SKUs the customer refuses
    only: list[str] | None          # "only X" -> restrict to these SKUs
    min_qty: dict[str, int]         # "at least 2 mango"
    exact_qty: dict[str, int]       # "exactly 2 lime"
    no_substitutes: bool
    unknown_products: list[str]     # names not in catalogue, e.g. "cola"
    manipulation: bool              # tries to change prices/rules/discounts

    @model_validator(mode="after")
    def clean_skus(self):
        """Uppercase every SKU. Anything not in the catalogue goes to unknown_products."""
        unknown = list(self.unknown_products)

        def keep_known(names):
            known = []
            for name in names:
                sku = name.strip().upper()
                if sku in CATALOGUE:
                    if sku not in known:
                        known.append(sku)
                elif name not in unknown:
                    unknown.append(name)
            return known

        self.include = keep_known(self.include)
        self.exclude = keep_known(self.exclude)
        if self.only is not None:
            self.only = keep_known(self.only)
        for field in ("min_qty", "exact_qty"):
            cleaned = {}
            for name, qty in getattr(self, field).items():
                sku = name.strip().upper()
                if sku in CATALOGUE:
                    cleaned[sku] = qty
                elif name not in unknown:
                    unknown.append(name)
            setattr(self, field, cleaned)
        self.unknown_products = unknown

        for field in ("min_qty", "exact_qty"):
            for sku, qty in getattr(self, field).items():
                if qty < 1:
                    raise ValueError(f"{field}[{sku}] must be at least 1, got {qty}")
        return self


class Item(BaseModel):
    sku: str
    quantity: int = Field(ge=1)


class Response(BaseModel):
    status: Literal["recommendation", "clarification", "cannot_fulfil"]
    items: list[Item]
    total: int
    message: str
