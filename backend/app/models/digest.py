"""
The typed shape of GET /digest and POST /digest/narrate.

Why this file exists at all: engine/digest.py and ai_client.py both
build and return plain dicts, which worked fine for our own frontend
(it just JSON.parses whatever comes back) but means the auto-generated
OpenAPI schema at /docs shows nothing useful -- an integrator building
their own admin panel against this API (the actual point of framing
this as a Razorpay feature, not a standalone product with its own
required frontend) would have to read main.py's source to know what
GET /digest returns. Declaring these as the routes' response_model
makes FastAPI validate the real response against this shape and publish
an accurate schema, with zero change to engine/digest.py's own logic --
it keeps returning plain dicts internally, FastAPI does the rest.
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Literal


class DigestTotals(BaseModel):
    attempts: int
    allowed: int
    blocked: int
    escalated: int


class DigestFlag(BaseModel):
    severity: Literal["high", "medium", "low"]
    agent_id: str
    flag_type: Literal["catalog_mismatch", "velocity_cap_hit", "repeated_blocks"]
    count: int
    detail: str


class AgentFootprint(BaseModel):
    agent_id: str
    attempts: int
    allowed: int
    blocked: int
    escalated: int
    blocked_rules: dict[str, int]
    first_seen: datetime
    last_seen: datetime
    revoked: bool


class DigestStats(BaseModel):
    window_hours: int
    totals: DigestTotals
    escalations_pending_or_reviewed: int
    agents: list[AgentFootprint]
    flags: list[DigestFlag]


class DigestResponse(BaseModel):
    stats: DigestStats


class DigestFlagExplanation(BaseModel):
    agent_id: str
    plain_english: str


class DigestNarrative(BaseModel):
    headline: str
    summary: str
    flag_explanations: list[DigestFlagExplanation]


class DigestNarrateResponse(BaseModel):
    narrative: DigestNarrative
