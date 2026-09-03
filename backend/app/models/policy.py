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

    # ---- India-specific, research-driven ----
    # No agentic commerce protocol we researched (AP2, ACP, UCP, UPI
    # Reserve Pay) governs Cash on Delivery -- they only ever authorize
    # prepaid money. But COD is 50-70% of real Indian D2C volume, and
    # RTO on COD already runs 20-40% (research/03-india-uap-razorpay.md).
    # An agent can place a COD order with ZERO payment authorization --
    # nothing anywhere gates that today. Defaulting this to False means
    # an agent-initiated order needs the merchant's explicit opt-in to
    # even attempt COD; the safe default is "agents pay upfront."
    allow_cod_for_agents: bool = False

    # Reserve Pay's own design caps retries at 3 in 24 hours -- the
    # regulator already treats ORDER VELOCITY, not just order size, as
    # the primary threat model for agentic abuse. Our rules before this
    # only ever looked at one cart at a time and had no memory of what
    # an agent did five minutes ago. This closes that: how many orders
    # one agent may place in a rolling time window.
    max_orders_per_agent_per_window: int | None = None
    velocity_window_minutes: int = 60
