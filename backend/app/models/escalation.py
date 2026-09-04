"""
Typed shape of GET /escalations/{id}/advice -- the AI Advisor tier,
same reasoning as models/digest.py: an outside admin panel needs a real
schema to render this against, not main.py's source code.
"""
from pydantic import BaseModel
from typing import Literal
from app.db.models import EscalationRow


class EscalationAdvice(BaseModel):
    recommendation: Literal["approve", "reject", "needs_human_judgment"]
    reasoning: str
    confidence: Literal["low", "medium", "high"]


class EscalationAdviceResponse(BaseModel):
    escalation_id: int
    advice: EscalationAdvice


class EscalationReviewResponse(BaseModel):
    escalation: EscalationRow
    # Present only when the escalation was approved -- Razorpay's own
    # payment-link response, left as a dict since it's an external API's
    # shape, not ours to own.
    payment: dict | None = None
