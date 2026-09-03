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
