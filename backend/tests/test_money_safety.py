"""
Two exploitable bugs found by auditing the system for the class of
mistake that already burned us once: a check that trivially passes
against a value nobody expected to see. Both are fixed here, and both
are proven, not just described.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from pydantic import ValidationError
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

import app.main as main_module
from app.main import app
from app.db.session import get_session
from app.models.cart import CartItem


# ---------- Negative quantity ----------

def test_negative_quantity_is_rejected_by_the_schema():
    """
    Before the fix: a cart with quantity=-9999 on a real, honestly
    priced item produced cart.total = -Rs 44,99,550 and sailed through
    every single rule as ALLOW, because every value check here works by
    asking "is this greater than the limit" -- which a negative number
    never is. Now rejected before it ever reaches the evaluator.
    """
    with pytest.raises(ValidationError):
        CartItem(id="shirt", title="Blue Shirt", price=45000, category="clothing", quantity=-9999)


def test_zero_quantity_is_rejected_too():
    with pytest.raises(ValidationError):
        CartItem(id="shirt", title="Blue Shirt", price=45000, category="clothing", quantity=0)


def test_negative_price_is_rejected():
    with pytest.raises(ValidationError):
        CartItem(id="shirt", title="Blue Shirt", price=-1, category="clothing", quantity=1)


# ---------- Double-approval on escalations ----------

async def _fake_create_payment_link(amount_paise: int, description: str, currency: str = "INR") -> dict:
    import itertools
    _fake_create_payment_link.counter = getattr(_fake_create_payment_link, "counter", 0) + 1
    return {"id": f"plink_FAKE{_fake_create_payment_link.counter}", "short_url": "https://rzp.io/rzp/fake"}


@pytest.fixture()
def client(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    monkeypatch.setattr(main_module, "create_payment_link", _fake_create_payment_link)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_approving_the_same_escalation_twice_does_not_create_a_second_payment(client):
    """
    Before the fix: review_escalation() unconditionally set the status
    and returned it -- a double-click, or a plain network retry (the
    exact failure mode Idempotency-Key exists to prevent on checkout),
    would create a SECOND real Razorpay payment link for an order
    already approved once. Now the second call gets a 409, and only one
    payment link ever exists.
    """
    key = client.post("/merchants/register", json={"merchant_id": "shop_dbl"}).json()["api_key"]
    auth = {"Authorization": f"Bearer {key}"}
    client.post("/policy", headers=auth, json={
        "merchant_id": "shop_dbl", "max_order_value": 1000000,
        "deny_categories": [], "escalate_above": 100,
    })

    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from app.engine.identity import canonical_cart_bytes
    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key().public_bytes_raw().hex()
    client.post("/agents/register", json={"agent_id": "dbl-agent", "public_key_hex": pub})
    items = [{"id": "shoes", "title": "Shoes", "price": 700000, "category": "footwear", "quantity": 1}]
    sig = priv.sign(canonical_cart_bytes([CartItem(**i) for i in items])).hex()

    checkout = client.post("/checkout-sessions", json={
        "merchant_id": "shop_dbl", "agent_id": "dbl-agent", "items": items, "signature_hex": sig,
    }).json()
    assert checkout["receipt"]["decision"] == "escalate"
    esc_id = checkout["escalation_id"]

    first = client.post(f"/escalations/{esc_id}/review", headers=auth, json={"approve": True})
    assert first.status_code == 200
    first_payment_id = first.json()["payment"]["id"]

    second = client.post(f"/escalations/{esc_id}/review", headers=auth, json={"approve": True})
    assert second.status_code == 409  # rejected outright -- no second payment attempted

    # Only the first call ever reached create_payment_link
    assert getattr(_fake_create_payment_link, "counter", 0) == 1
    assert first_payment_id == "plink_FAKE1"


def test_a_failed_payment_leaves_the_escalation_retryable_not_stuck(client, monkeypatch):
    """
    The bug this closes was found live, not by inspection: Razorpay's API
    returned 429 mid-session from earlier load testing, the payment call
    raised, but the escalation had already been committed to "approved"
    with no payment ever created -- and a retry was permanently refused
    with 409, since the endpoint believed the decision was already made.
    This proves the fix: a failed payment leaves the escalation exactly
    where it was, pending, so the same request can simply be retried once
    Razorpay stops failing.
    """
    key = client.post("/merchants/register", json={"merchant_id": "shop_retry"}).json()["api_key"]
    auth = {"Authorization": f"Bearer {key}"}
    client.post("/policy", headers=auth, json={
        "merchant_id": "shop_retry", "max_order_value": 1000000,
        "deny_categories": [], "escalate_above": 100,
    })

    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from app.engine.identity import canonical_cart_bytes
    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key().public_bytes_raw().hex()
    client.post("/agents/register", json={"agent_id": "retry-agent", "public_key_hex": pub})
    items = [{"id": "shoes", "title": "Shoes", "price": 700000, "category": "footwear", "quantity": 1}]
    sig = priv.sign(canonical_cart_bytes([CartItem(**i) for i in items])).hex()

    checkout = client.post("/checkout-sessions", json={
        "merchant_id": "shop_retry", "agent_id": "retry-agent", "items": items, "signature_hex": sig,
    }).json()
    esc_id = checkout["escalation_id"]

    async def _failing_create_payment_link(amount_paise: int, description: str, currency: str = "INR"):
        raise RuntimeError("simulated Razorpay 429 -- rate limited")

    monkeypatch.setattr(main_module, "create_payment_link", _failing_create_payment_link)

    with pytest.raises(RuntimeError):
        client.post(f"/escalations/{esc_id}/review", headers=auth, json={"approve": True})

    # Still pending -- NOT stuck as "approved with no payment"
    pending = client.get("/escalations", headers=auth, params={"merchant_id": "shop_retry"}).json()
    assert any(e["id"] == esc_id and e["status"] == "pending" for e in pending)

    # Razorpay recovers; the exact same request now succeeds
    monkeypatch.setattr(main_module, "create_payment_link", _fake_create_payment_link)
    retry = client.post(f"/escalations/{esc_id}/review", headers=auth, json={"approve": True})
    assert retry.status_code == 200
    assert retry.json()["escalation"]["status"] == "approved"
