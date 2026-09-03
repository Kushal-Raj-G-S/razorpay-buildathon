"""
The real database tables. Everything here survives a server restart --
unlike app/storage.py's in-memory dicts, which were fine for a first
demo but wipe on every restart. This is the production-grade version.

Uses SQLModel (SQLAlchemy + Pydantic in one) so these classes work both
as database tables AND as the API request/response shapes, no duplicate
definitions.
"""
from sqlmodel import SQLModel, Field, Column, JSON
from datetime import datetime, timezone
from typing import Optional


def _now() -> datetime:
    return datetime.now(timezone.utc)


class PolicyRow(SQLModel, table=True):
    __tablename__ = "policies"

    merchant_id: str = Field(primary_key=True)
    max_order_value: int
    deny_categories: list[str] = Field(sa_column=Column(JSON), default_factory=list)
    max_units_per_sku: int = 10
    escalate_above: Optional[int] = None
    require_signed_identity: bool = True
    allow_cod_for_agents: bool = False
    max_orders_per_agent_per_window: Optional[int] = None
    velocity_window_minutes: int = 60
    updated_at: datetime = Field(default_factory=_now)


class AgentRow(SQLModel, table=True):
    __tablename__ = "agents"

    agent_id: str = Field(primary_key=True)
    public_key_hex: str
    revoked: bool = False
    registered_at: datetime = Field(default_factory=_now)


class ReceiptRow(SQLModel, table=True):
    __tablename__ = "receipts"

    id: Optional[int] = Field(default=None, primary_key=True)
    cart_id: str
    merchant_id: str
    agent_id: str
    decision: str  # "allow" | "block" | "escalate"
    rules_checked: list = Field(sa_column=Column(JSON))  # list of RuleResult dicts
    cart_items: list = Field(sa_column=Column(JSON))     # snapshot of what was in the cart
    cart_total: int
    timestamp: datetime = Field(default_factory=_now)
    signature: Optional[str] = None


class EscalationRow(SQLModel, table=True):
    """
    A cart that passed every rule but was too big to auto-approve.
    Sits here until a human clicks approve or reject.
    """
    __tablename__ = "escalations"

    id: Optional[int] = Field(default=None, primary_key=True)
    receipt_id: int = Field(foreign_key="receipts.id")
    merchant_id: str
    agent_id: str
    cart_items: list = Field(sa_column=Column(JSON))
    cart_total: int
    status: str = "pending"  # "pending" | "approved" | "rejected"
    reviewer_note: Optional[str] = None
    created_at: datetime = Field(default_factory=_now)
    reviewed_at: Optional[datetime] = None


class ProductRow(SQLModel, table=True):
    """One row per catalog product, after AI normalization."""
    __tablename__ = "products"

    id: str = Field(primary_key=True)          # composite in practice: f"{merchant_id}:{product_id}"
    merchant_id: str = Field(index=True)
    title: str
    description: Optional[str] = None
    variants: list = Field(sa_column=Column(JSON))  # list of {id, title, price, category, available, sku}


class MerchantRow(SQLModel, table=True):
    """
    A shop owner's account. The api_key_hash is a SHA-256 hash -- the
    real key is shown to the merchant exactly once, at registration, and
    never stored or logged anywhere in plain text.
    """
    __tablename__ = "merchants"

    merchant_id: str = Field(primary_key=True)
    api_key_hash: str
    created_at: datetime = Field(default_factory=_now)


class IdempotencyRow(SQLModel, table=True):
    """
    If an AI agent's network hiccups and it retries the exact same
    checkout request, this stops us from creating a second order (and a
    second real payment link) for something that already happened once.
    Real protocols (ACP, UCP -- see research/06-protocols.md) require an
    Idempotency-Key header for exactly this reason.
    """
    __tablename__ = "idempotency_keys"

    key: str = Field(primary_key=True)          # the Idempotency-Key header value
    merchant_id: str
    response_json: str                          # the exact response we sent the first time
    created_at: datetime = Field(default_factory=_now)


class SigningKeyRow(SQLModel, table=True):
    """
    The shop's Ed25519 keypair for signing receipts. Generated once,
    then reused forever -- so a receipt signed last week still verifies
    today, even after a hundred restarts. (Storing this in memory, like
    the first version did, meant every restart silently invalidated every
    past receipt's signature -- a real bug we're fixing here.)
    """
    __tablename__ = "signing_key"

    id: int = Field(default=1, primary_key=True)
    private_key_hex: str
    public_key_hex: str
