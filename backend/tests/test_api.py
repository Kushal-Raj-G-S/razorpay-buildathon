"""
Tests against the actual HTTP server (FastAPI's TestClient), not just
the internal functions. Everything in test_engine.py and
test_persistence.py tests the pieces in isolation; this file proves the
pieces are actually wired together correctly behind real endpoints --
including the auth layer, which had zero test coverage until now.

Uses a fresh in-memory database per test run via dependency override,
completely separate from the real warrant.db / Neon Postgres.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import itertools
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import app.main as main_module
from app.main import app
from app.db.session import get_session
from app.engine.identity import canonical_cart_bytes
from app.models.cart import CartItem


_fake_payment_ids = itertools.count(1)


async def _fake_create_payment_link(amount_paise: int, description: str, currency: str = "INR") -> dict:
    """
    A real call was already proven live, twice: once directly against
    Razorpay's API (research/session log) and once through the running
    server in the browser, with the payment page opened and confirmed
    genuine. Running the full test suite against the real API on every
    run got rate-limited (429 Too Many Requests) -- a real mistake, not
    a hypothetical one: tests shouldn't depend on a third party's rate
    limit to pass. This fakes only that one network boundary so the
    suite stays fast and deterministic; everything on our side of that
    boundary (the checkout logic, the receipt, the decision) is still
    exercised for real.
    """
    return {"id": f"plink_FAKE{next(_fake_payment_ids)}", "short_url": "https://rzp.io/rzp/fake",
            "status": "created", "amount": amount_paise, "description": description}


@pytest.fixture(autouse=True)
def stub_razorpay(monkeypatch):
    monkeypatch.setattr(main_module, "create_payment_link", _fake_create_payment_link)


@pytest.fixture()
def client():
    # StaticPool is required here -- without it, SQLite's in-memory
    # database gives each new connection a completely separate, empty
    # database. Every request through the TestClient would silently see
    # "no such table" because it landed on a fresh, untouched database
    # instead of the one create_all() populated below. Same class of
    # bug we hit for real in db/repo.py's timestamp issue: SQLite's
    # in-memory quirks don't show up until you actually exercise
    # multiple connections, not when you read the code.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def register_merchant(client, merchant_id="shop_test"):
    r = client.post("/merchants/register", json={"merchant_id": merchant_id})
    assert r.status_code == 200
    return r.json()["api_key"]


def auth_header(api_key):
    return {"Authorization": f"Bearer {api_key}"}


# ---------- Auth ----------

def test_saving_policy_without_a_key_is_refused(client):
    r = client.post("/policy", json={
        "merchant_id": "shop_test", "max_order_value": 1000000, "deny_categories": [],
    })
    assert r.status_code == 401


def test_saving_policy_with_wrong_key_is_refused(client):
    register_merchant(client, "shop_test")
    r = client.post("/policy", headers=auth_header("wrk_totally_wrong"), json={
        "merchant_id": "shop_test", "max_order_value": 1000000, "deny_categories": [],
    })
    assert r.status_code == 403


def test_saving_policy_with_correct_key_succeeds(client):
    key = register_merchant(client, "shop_test")
    r = client.post("/policy", headers=auth_header(key), json={
        "merchant_id": "shop_test", "max_order_value": 1000000, "deny_categories": [],
    })
    assert r.status_code == 200


def test_registering_the_same_merchant_twice_fails(client):
    register_merchant(client, "shop_dup")
    r = client.post("/merchants/register", json={"merchant_id": "shop_dup"})
    assert r.status_code == 409


def test_one_merchants_key_cannot_touch_another_merchants_policy(client):
    key_a = register_merchant(client, "shop_a")
    register_merchant(client, "shop_b")
    # shop_a's key trying to write shop_b's policy
    r = client.post("/policy", headers=auth_header(key_a), json={
        "merchant_id": "shop_b", "max_order_value": 1000000, "deny_categories": [],
    })
    assert r.status_code == 403


# ---------- Full checkout flow through real HTTP ----------

def _register_and_sign(client, agent_id, items):
    key = Ed25519PrivateKey.generate()
    pub = key.public_key().public_bytes_raw().hex()
    client.post("/agents/register", json={"agent_id": agent_id, "public_key_hex": pub})
    cart_items = [CartItem(**i) for i in items]
    return key.sign(canonical_cart_bytes(cart_items)).hex()


def test_clean_signed_cart_allows_over_http(client):
    merchant_key = register_merchant(client, "shop_http")
    client.post("/policy", headers=auth_header(merchant_key), json={
        "merchant_id": "shop_http", "max_order_value": 1000000, "deny_categories": ["gift_card"],
    })

    items = [{"id": "shirt", "title": "Shirt", "price": 45000, "category": "clothing", "quantity": 1}]
    sig = _register_and_sign(client, "http-agent", items)

    r = client.post("/checkout-sessions", json={
        "merchant_id": "shop_http", "agent_id": "http-agent", "items": items, "signature_hex": sig,
    })
    assert r.status_code == 200
    body = r.json()
    assert body["receipt"]["decision"] == "allow"
    assert "payment" in body


def test_poisoned_cart_blocks_over_http(client):
    merchant_key = register_merchant(client, "shop_http2")
    client.post("/policy", headers=auth_header(merchant_key), json={
        "merchant_id": "shop_http2", "max_order_value": 1000000, "deny_categories": ["gift_card"],
    })

    items = [
        {"id": "shirt", "title": "Shirt", "price": 45000, "category": "clothing", "quantity": 1},
        {"id": "gc", "title": "Gift Card", "price": 200000, "category": "gift_card", "quantity": 1},
    ]
    sig = _register_and_sign(client, "http-agent-2", items)

    r = client.post("/checkout-sessions", json={
        "merchant_id": "shop_http2", "agent_id": "http-agent-2", "items": items, "signature_hex": sig,
    })
    assert r.status_code == 200
    body = r.json()
    assert body["receipt"]["decision"] == "block"
    # CheckoutResponse always includes payment/order/escalation_id/note (null when
    # not applicable) now that the response has a declared schema -- a predictable
    # shape beats a key that sometimes exists and sometimes doesn't.
    assert body["payment"] is None


def test_revoked_agent_is_refused_over_http(client):
    merchant_key = register_merchant(client, "shop_http3")
    client.post("/policy", headers=auth_header(merchant_key), json={
        "merchant_id": "shop_http3", "max_order_value": 1000000, "deny_categories": [],
    })
    items = [{"id": "shirt", "title": "Shirt", "price": 45000, "category": "clothing", "quantity": 1}]
    sig = _register_and_sign(client, "revoke-me", items)

    client.post("/agents/revoke-me/revoke?merchant_id=shop_http3", headers=auth_header(merchant_key))

    r = client.post("/checkout-sessions", json={
        "merchant_id": "shop_http3", "agent_id": "revoke-me", "items": items, "signature_hex": sig,
    })
    assert r.status_code == 403


def test_idempotency_key_returns_the_same_response_twice(client):
    merchant_key = register_merchant(client, "shop_http4")
    client.post("/policy", headers=auth_header(merchant_key), json={
        "merchant_id": "shop_http4", "max_order_value": 1000000, "deny_categories": [],
    })
    items = [{"id": "shirt", "title": "Shirt", "price": 45000, "category": "clothing", "quantity": 1}]
    sig = _register_and_sign(client, "idem-agent", items)
    body = {"merchant_id": "shop_http4", "agent_id": "idem-agent", "items": items, "signature_hex": sig}

    r1 = client.post("/checkout-sessions", json=body, headers={"Idempotency-Key": "same-key-twice"})
    r2 = client.post("/checkout-sessions", json=body, headers={"Idempotency-Key": "same-key-twice"})

    assert r1.json()["payment"]["id"] == r2.json()["payment"]["id"]


def test_escalation_review_requires_the_right_merchants_key(client):
    merchant_key = register_merchant(client, "shop_http5")
    other_key = register_merchant(client, "shop_http5_other")
    client.post("/policy", headers=auth_header(merchant_key), json={
        "merchant_id": "shop_http5", "max_order_value": 1000000, "deny_categories": [],
        "escalate_above": 100,
    })
    items = [{"id": "shirt", "title": "Shirt", "price": 45000, "category": "clothing", "quantity": 1}]
    sig = _register_and_sign(client, "esc-agent", items)

    checkout = client.post("/checkout-sessions", json={
        "merchant_id": "shop_http5", "agent_id": "esc-agent", "items": items, "signature_hex": sig,
    }).json()
    assert checkout["receipt"]["decision"] == "escalate"
    esc_id = checkout["escalation_id"]

    # wrong merchant's key can't review it
    r = client.post(f"/escalations/{esc_id}/review", headers=auth_header(other_key),
                     json={"approve": True})
    assert r.status_code == 403

    # right merchant's key can
    r = client.post(f"/escalations/{esc_id}/review", headers=auth_header(merchant_key),
                     json={"approve": True})
    assert r.status_code == 200
    assert r.json()["escalation"]["status"] == "approved"
    assert "payment" in r.json()
