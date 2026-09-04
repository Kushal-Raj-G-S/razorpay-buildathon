"""Typed shape of POST /checkout-sessions -- the single most important
response in the whole API, and until now the least typed: a raw dict
with fields that only ever showed up conditionally on the decision. """
from pydantic import BaseModel
from app.models.receipt import Receipt


class CheckoutResponse(BaseModel):
    receipt: Receipt
    # Present only when decision == "allow" and payment_mode == "prepaid".
    # Razorpay's own payment-link response -- left as a dict rather than a
    # strict schema because it's an external API's shape, not ours to own.
    payment: dict | None = None
    # Present only when decision == "allow" and payment_mode == "cod".
    order: dict | None = None
    # Present only when decision == "escalate".
    escalation_id: int | None = None
    note: str | None = None
