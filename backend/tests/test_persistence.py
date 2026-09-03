"""
Tests for the database layer. Most important test in this file:
a receipt signed, saved, and reloaded from the database must STILL
verify -- this is exactly the bug we found by hand (SQLite drops
timezone info on datetimes, which silently changed the receipt's
canonical bytes and broke every past signature after a restart).
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlmodel import SQLModel, Session, create_engine
from app.models.cart import Cart, CartItem
from app.models.policy import Policy
from app.engine.evaluate import evaluate
from app.engine.signing import sign_receipt, verify_receipt
from app.db import repo


def make_test_session() -> Session:
    """A fresh in-memory database per test, isolated from the real warrant.db file."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_receipt_survives_a_round_trip_through_the_database():
    session = make_test_session()
    policy = Policy(merchant_id="shop_x", max_order_value=1000000, deny_categories=["gift_card"])
    cart = Cart(id="c1", merchant_id="shop_x", items=[
        CartItem(id="shirt", title="Shirt", price=45000, category="clothing"),
    ])

    receipt = evaluate(cart, policy, agent_id="agent")
    private_key, public_key = repo.get_or_create_signing_key(session)
    signed = sign_receipt(receipt, private_key)

    # sanity check: it verifies before ever touching the database
    assert verify_receipt(signed, public_key) is True

    repo.save_receipt(session, signed, cart.items)

    # reload from the database, exactly like a fresh server process would
    reloaded = repo.list_receipts(session, merchant_id="shop_x")[0]

    # THIS is the assertion that would have caught the real bug
    assert verify_receipt(reloaded, public_key) is True


def test_signing_key_is_the_same_across_multiple_calls():
    """
    The old in-memory version generated a new key every server restart,
    silently invalidating every past receipt. This proves the database
    version returns the SAME key every time it's asked, not a fresh one.
    """
    session = make_test_session()
    private1, public1 = repo.get_or_create_signing_key(session)
    private2, public2 = repo.get_or_create_signing_key(session)
    assert private1 == private2
    assert public1 == public2


def test_policy_survives_a_round_trip():
    session = make_test_session()
    policy = Policy(
        merchant_id="shop_y", max_order_value=500000,
        deny_categories=["gift_card"], max_units_per_sku=3, escalate_above=200000,
    )
    repo.save_policy(session, policy)
    reloaded = repo.get_policy(session, "shop_y")
    assert reloaded.max_order_value == 500000
    assert reloaded.deny_categories == ["gift_card"]
    assert reloaded.escalate_above == 200000


def test_escalation_queue_round_trip_and_review():
    session = make_test_session()
    items = [CartItem(id="shoes", title="Shoes", price=700000, category="footwear")]

    receipt_id = repo.save_receipt(
        session,
        evaluate(
            Cart(id="c2", merchant_id="shop_z", items=items),
            Policy(merchant_id="shop_z", max_order_value=1000000, escalate_above=500000),
            agent_id="agent",
        ),
        items,
    )
    esc_id = repo.create_escalation(session, receipt_id, "shop_z", "agent", items, 700000)

    pending = repo.list_escalations(session, "shop_z", status="pending")
    assert len(pending) == 1
    assert pending[0].id == esc_id

    reviewed = repo.review_escalation(session, esc_id, approve=True, note="looks fine")
    assert reviewed.status == "approved"

    still_pending = repo.list_escalations(session, "shop_z", status="pending")
    assert len(still_pending) == 0
