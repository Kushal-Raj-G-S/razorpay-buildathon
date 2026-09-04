"""
Every database read/write goes through here. main.py never touches
SQLModel directly -- it calls these functions, which speak Pydantic in
and Pydantic out. Keeps the API layer and the storage layer separable,
so swapping SQLite for real Postgres later only touches this file plus
session.py's DATABASE_URL.
"""
from datetime import datetime, timezone, timedelta
from sqlmodel import Session, select
from app.db.models import (
    PolicyRow, PolicyHistoryRow, AgentRow, ReceiptRow, EscalationRow, ProductRow, SigningKeyRow,
    MerchantRow, IdempotencyRow, RedTeamRunRow,
)
from app.models.policy import Policy
from app.models.receipt import Receipt, RuleResult, Decision
from app.models.cart import CartItem
from app.models.catalog import Catalog, Product, Variant
from app.engine.signing import generate_keypair


# ---------- Signing key (generated once, reused forever) ----------

def get_or_create_signing_key(session: Session) -> tuple[bytes, bytes]:
    row = session.get(SigningKeyRow, 1)
    if row:
        return bytes.fromhex(row.private_key_hex), bytes.fromhex(row.public_key_hex)

    private_bytes, public_bytes = generate_keypair()
    row = SigningKeyRow(id=1, private_key_hex=private_bytes.hex(), public_key_hex=public_bytes.hex())
    session.add(row)
    session.commit()
    return private_bytes, public_bytes


# ---------- Merchants (auth) ----------

def merchant_exists(session: Session, merchant_id: str) -> bool:
    return session.get(MerchantRow, merchant_id) is not None


def create_merchant(session: Session, merchant_id: str, api_key_hash: str) -> None:
    session.add(MerchantRow(merchant_id=merchant_id, api_key_hash=api_key_hash))
    session.commit()


# ---------- Idempotency (stop a retried request from double-charging) ----------

def get_idempotent_response(session: Session, key: str) -> str | None:
    row = session.get(IdempotencyRow, key)
    return row.response_json if row else None


def save_idempotent_response(session: Session, key: str, merchant_id: str, response_json: str) -> None:
    session.add(IdempotencyRow(key=key, merchant_id=merchant_id, response_json=response_json))
    session.commit()


# ---------- Policy ----------

def save_policy(session: Session, policy: Policy) -> None:
    existing = session.get(PolicyRow, policy.merchant_id)
    data = policy.model_dump()
    data["updated_at"] = datetime.now(timezone.utc)
    if existing:
        for k, v in data.items():
            setattr(existing, k, v)
        session.add(existing)
    else:
        session.add(PolicyRow(**data))

    # Append-only snapshot, every save, never overwritten -- see
    # PolicyHistoryRow's docstring. Kept as a second insert in the same
    # commit rather than folded into PolicyRow so the "current" read
    # (get_policy) stays a single cheap row lookup, not a query over history.
    session.add(PolicyHistoryRow(merchant_id=policy.merchant_id, snapshot=policy.model_dump()))
    session.commit()


def list_policy_history(session: Session, merchant_id: str, limit: int = 20) -> list[PolicyHistoryRow]:
    stmt = (
        select(PolicyHistoryRow)
        .where(PolicyHistoryRow.merchant_id == merchant_id)
        .order_by(PolicyHistoryRow.id.desc())
        .limit(limit)
    )
    return session.exec(stmt).all()


def get_policy(session: Session, merchant_id: str) -> Policy | None:
    row = session.get(PolicyRow, merchant_id)
    if not row:
        return None
    return Policy(
        merchant_id=row.merchant_id,
        max_order_value=row.max_order_value,
        deny_categories=row.deny_categories,
        max_units_per_sku=row.max_units_per_sku,
        escalate_above=row.escalate_above,
        require_signed_identity=row.require_signed_identity,
        allow_cod_for_agents=row.allow_cod_for_agents,
        max_orders_per_agent_per_window=row.max_orders_per_agent_per_window,
        velocity_window_minutes=row.velocity_window_minutes,
    )


# ---------- Agents ----------

def register_agent(session: Session, agent_id: str, public_key_hex: str) -> None:
    existing = session.get(AgentRow, agent_id)
    if existing:
        existing.public_key_hex = public_key_hex
        session.add(existing)
    else:
        session.add(AgentRow(agent_id=agent_id, public_key_hex=public_key_hex))
    session.commit()


def get_agent_public_key(session: Session, agent_id: str) -> str | None:
    row = session.get(AgentRow, agent_id)
    return row.public_key_hex if row else None


def is_agent_revoked(session: Session, agent_id: str) -> bool:
    row = session.get(AgentRow, agent_id)
    return bool(row and row.revoked)


def set_agent_revoked(session: Session, agent_id: str, revoked: bool) -> None:
    """
    Real bug, caught live by actually clicking the Revoke button in a
    browser and then checking with a raw checkout call whether it did
    anything: most agents in real traffic never call POST /agents/register
    first (that's only needed for identity-signature verification, not to
    exist) -- they just show up via /checkout-sessions. This function used
    to silently no-op for any agent with no AgentRow yet, so revoking one
    of them returned 200 OK and did NOTHING; the agent could still check
    out immediately afterward. Now it creates the row if it doesn't exist,
    same as any real "block this identity" action must be able to target
    an identity it has never seen register anything.
    """
    row = session.get(AgentRow, agent_id)
    if row:
        row.revoked = revoked
    else:
        row = AgentRow(agent_id=agent_id, public_key_hex="", revoked=revoked)
    session.add(row)
    session.commit()


# ---------- Receipts ----------

def save_receipt(session: Session, receipt: Receipt, cart_items: list[CartItem]) -> int:
    row = ReceiptRow(
        cart_id=receipt.cart_id,
        merchant_id=receipt.merchant_id,
        agent_id=receipt.agent_id,
        decision=receipt.decision.value,
        rules_checked=[r.model_dump() for r in receipt.rules_checked],
        cart_items=[i.model_dump() for i in cart_items],
        cart_total=receipt.cart_total,
        timestamp=receipt.timestamp,
        signature=receipt.signature,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row.id


def _row_to_receipt(row: ReceiptRow) -> Receipt:
    # SQLite silently drops timezone info on datetime columns -- the
    # value we stored was always UTC (see models.py's _now()), it just
    # comes back "naive". Re-attach the marker explicitly, otherwise the
    # receipt's canonical bytes (see engine/signing.py) come out
    # different from what was originally signed, and a completely
    # untampered receipt fails its own signature check. Real bug, caught
    # by testing a restart, not something we'd have found by reading the
    # code.
    timestamp = row.timestamp
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    return Receipt(
        cart_id=row.cart_id,
        merchant_id=row.merchant_id,
        agent_id=row.agent_id,
        decision=Decision(row.decision),
        rules_checked=[RuleResult(**r) for r in row.rules_checked],
        cart_total=row.cart_total,
        timestamp=timestamp,
        signature=row.signature,
    )


def list_receipts(session: Session, merchant_id: str | None = None) -> list[Receipt]:
    stmt = select(ReceiptRow)
    if merchant_id:
        stmt = stmt.where(ReceiptRow.merchant_id == merchant_id)
    stmt = stmt.order_by(ReceiptRow.id)
    return [_row_to_receipt(r) for r in session.exec(stmt).all()]


def list_receipts_with_items(session: Session, merchant_id: str) -> list[dict]:
    """
    Same rows as list_receipts(), plus the cart_items snapshot -- Receipt
    itself deliberately doesn't carry items (see models/receipt.py), but
    a merchant looking at "what was actually allowed" needs to see the
    real products, not just a total in rupees. Returned as plain dicts,
    not Receipt objects, since Receipt's shape is also what gets signed
    and verified -- this stays a display-only superset, not a change to
    that contract.
    """
    stmt = (
        select(ReceiptRow)
        .where(ReceiptRow.merchant_id == merchant_id)
        .order_by(ReceiptRow.id)
    )
    rows = session.exec(stmt).all()
    result = []
    for r in rows:
        receipt = _row_to_receipt(r)
        result.append({**receipt.model_dump(mode="json"), "cart_items": r.cart_items})
    return result


def count_recent_orders(session: Session, merchant_id: str, agent_id: str, window_minutes: int) -> int:
    """
    How many times has this agent tried to check out with this merchant
    in the last `window_minutes`? Feeds the velocity check (see
    engine/evaluate.py's check_velocity) -- the one rule with memory of
    what an agent already did, mirroring how UPI Reserve Pay itself caps
    retries per day rather than only capping amount per order.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
    stmt = select(ReceiptRow).where(
        ReceiptRow.merchant_id == merchant_id,
        ReceiptRow.agent_id == agent_id,
        ReceiptRow.timestamp >= cutoff,
    )
    return len(session.exec(stmt).all())


def list_receipts_since(session: Session, merchant_id: str, since: datetime) -> list[ReceiptRow]:
    """
    Raw receipt ROWS (not the Receipt pydantic model) in a time window --
    feeds the digest (engine/digest.py). Returns the ORM rows directly
    because the digest needs cart_items, the agent-claimed snapshot of
    what was in the cart, which Receipt itself deliberately doesn't
    carry (see models/receipt.py).
    """
    stmt = (
        select(ReceiptRow)
        .where(ReceiptRow.merchant_id == merchant_id, ReceiptRow.timestamp >= since)
        .order_by(ReceiptRow.id)
    )
    return session.exec(stmt).all()


def list_escalations_since(session: Session, merchant_id: str, since: datetime):
    stmt = (
        select(EscalationRow)
        .where(EscalationRow.merchant_id == merchant_id, EscalationRow.created_at >= since)
        .order_by(EscalationRow.id)
    )
    return session.exec(stmt).all()


def summarize_agent_history(session: Session, merchant_id: str, agent_id: str, limit: int = 5) -> str:
    """
    A short, human-readable line per recent decision for this agent
    with this merchant -- feeds the escalation advisor (ai_client.py's
    advise_on_escalation) so its recommendation is informed by whether
    this agent has a track record here, not just the one order in front
    of it.
    """
    stmt = (
        select(ReceiptRow)
        .where(ReceiptRow.merchant_id == merchant_id, ReceiptRow.agent_id == agent_id)
        .order_by(ReceiptRow.id.desc())
        .limit(limit)
    )
    rows = session.exec(stmt).all()
    if not rows:
        return ""
    return "; ".join(f"{r.decision} (Rs {r.cart_total/100:.0f})" for r in rows)


# ---------- Escalations (the human-review queue) ----------

def create_escalation(session: Session, receipt_id: int, merchant_id: str, agent_id: str,
                       cart_items: list[CartItem], cart_total: int) -> int:
    row = EscalationRow(
        receipt_id=receipt_id,
        merchant_id=merchant_id,
        agent_id=agent_id,
        cart_items=[i.model_dump() for i in cart_items],
        cart_total=cart_total,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row.id


def list_escalations(session: Session, merchant_id: str | None = None, status: str | None = "pending"):
    stmt = select(EscalationRow)
    if merchant_id:
        stmt = stmt.where(EscalationRow.merchant_id == merchant_id)
    if status:
        stmt = stmt.where(EscalationRow.status == status)
    stmt = stmt.order_by(EscalationRow.id)
    return session.exec(stmt).all()


class AlreadyReviewedError(Exception):
    """Raised when a caller tries to review an escalation a second time.

    Without this guard, double-clicking Approve -- or a plain network
    retry, the same failure mode Idempotency-Key exists to prevent on
    checkout -- would create a SECOND real Razorpay payment link for an
    order that was already approved once. Caught this by re-reading the
    checkout endpoint's own idempotency handling and asking whether the
    same class of bug existed anywhere else money moves. It did, here.
    """


def review_escalation(session: Session, escalation_id: int, approve: bool, note: str | None) -> EscalationRow | None:
    row = session.get(EscalationRow, escalation_id)
    if not row:
        return None
    if row.status != "pending":
        raise AlreadyReviewedError(
            f"escalation {escalation_id} was already {row.status} at {row.reviewed_at}"
        )
    row.status = "approved" if approve else "rejected"
    row.reviewer_note = note
    row.reviewed_at = datetime.now(timezone.utc)
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def get_escalation(session: Session, escalation_id: int) -> EscalationRow | None:
    return session.get(EscalationRow, escalation_id)


# ---------- Catalog ----------

def save_catalog(session: Session, catalog: Catalog) -> None:
    # replace-all semantics: clear this merchant's products, insert the fresh set
    existing = session.exec(select(ProductRow).where(ProductRow.merchant_id == catalog.merchant_id)).all()
    for row in existing:
        session.delete(row)

    for product in catalog.products:
        session.add(ProductRow(
            id=f"{catalog.merchant_id}:{product.id}",
            merchant_id=catalog.merchant_id,
            title=product.title,
            description=product.description,
            variants=[v.model_dump() for v in product.variants],
        ))
    session.commit()


def save_red_team_run(session: Session, merchant_id: str, goal: str, rounds: list[dict], outcome: str) -> int:
    row = RedTeamRunRow(merchant_id=merchant_id, goal=goal, rounds=rounds, outcome=outcome)
    session.add(row)
    session.commit()
    session.refresh(row)
    return row.id


def list_red_team_runs(session: Session, merchant_id: str) -> list[RedTeamRunRow]:
    stmt = select(RedTeamRunRow).where(RedTeamRunRow.merchant_id == merchant_id).order_by(RedTeamRunRow.id.desc())
    return session.exec(stmt).all()


def get_catalog(session: Session, merchant_id: str) -> Catalog | None:
    rows = session.exec(select(ProductRow).where(ProductRow.merchant_id == merchant_id)).all()
    if not rows:
        return None
    products = [
        Product(id=r.id.split(":", 1)[1], title=r.title, description=r.description,
                 variants=[Variant(**v) for v in r.variants])
        for r in rows
    ]
    return Catalog(merchant_id=merchant_id, products=products)
