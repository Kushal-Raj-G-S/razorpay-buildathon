"""
The shop owner's rulebook. This is what they write, in plain settings,
not code. We turn it into this shape (by hand for now, later maybe
an AI helps translate their English into this).
"""
from pydantic import BaseModel


class Policy(BaseModel):
    merchant_id: str

    max_order_value: int              # in paise. e.g. 500000 = Rs 5000 max per order
    deny_categories: list[str] = []   # e.g. ["gift_card", "clearance"]
    max_units_per_sku: int = 10       # can't buy more than this of one item
    escalate_above: int | None = None # orders above this get flagged for human review instead of auto-blocked
    require_signed_identity: bool = True  # if True, agent MUST prove identity (step 1 from our chat)
