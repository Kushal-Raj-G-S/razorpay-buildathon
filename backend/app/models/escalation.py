"""
Typed shape of GET /escalations/{id}/advice -- the AI Advisor tier,
same reasoning as models/digest.py: an outside admin panel needs a real
schema to render this against, not main.py's source code.
"""
from pydantic import BaseModel
from typing import Literal


class EscalationAdvice(BaseModel):
    recommendation: Literal["approve", "reject", "needs_human_judgment"]
    reasoning: str
    confidence: Literal["low", "medium", "high"]


class EscalationAdviceResponse(BaseModel):
    escalation_id: int
    advice: EscalationAdvice
