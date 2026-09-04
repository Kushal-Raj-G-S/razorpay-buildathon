"""
The receipt we print after every single check. This is the proof
that gets shown if anyone ever asks "why did/didn't this go through?"
"""
from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class Decision(str, Enum):
    ALLOW = "allow"
    BLOCK = "block"
    ESCALATE = "escalate"     # too close to call, a human should look


class RuleResult(BaseModel):
    rule_name: str          # e.g. "max_order_value"
    passed: bool
    detail: str              # plain-English reason, e.g. "cart total 6000 exceeds limit 5000"


class Receipt(BaseModel):
    cart_id: str
    merchant_id: str
    agent_id: str
    decision: Decision
    rules_checked: list[RuleResult]
    cart_total: int
    timestamp: datetime

    # filled in later once we sign it (step 4 from our chat)
    signature: str | None = None


class ReceiptItem(BaseModel):
    id: str
    title: str
    price: int
    category: str | None = None
    quantity: int
    listed: bool = True


class ReceiptWithItems(Receipt):
    """
    GET /receipts's real response shape -- Receipt itself deliberately
    doesn't carry items (its shape is also what gets signed), but a
    merchant looking at "what was actually allowed/blocked" needs the
    real products, not just a total in rupees. A prior version declared
    response_model=list[Receipt] on that route, which silently stripped
    this field from every response even though repo.list_receipts_with_items
    returned it -- found by clicking through the Digest page's own
    "Allowed" drilldown and noticing the expand arrow never appeared.
    """
    cart_items: list[ReceiptItem] = []
