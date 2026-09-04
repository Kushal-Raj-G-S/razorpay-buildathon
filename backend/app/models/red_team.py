"""Typed shapes for the red-team endpoints -- one of the headline
features, so it deserves a real schema as much as Digest does."""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.models.cart import CartItem


class RedTeamRound(BaseModel):
    round: int
    reasoning: str
    items: list[CartItem]                       # what the agent CLAIMED
    resolved_items: list[CartItem] | None = None  # what it actually was (absent on a give_up round)
    decision: str                                 # "allow" | "block" | "escalate" | "gave_up"
    rules_failed: list[str]


class RedTeamRunResult(BaseModel):
    """POST /red-team/run's response -- the run just triggered."""
    run_id: int
    goal: str
    outcome: str  # "held" | "breached" | "agent_gave_up" | "max_rounds_reached"
    rounds: list[RedTeamRound]


class RedTeamRunRecord(BaseModel):
    """GET /red-team/runs's response -- a persisted run read back later,
    same shape as RedTeamRunResult plus its id and when it happened."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    merchant_id: str
    goal: str
    rounds: list[RedTeamRound]
    outcome: str
    created_at: datetime
