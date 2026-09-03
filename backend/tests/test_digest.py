"""
Proves the digest (engine/digest.py + GET /digest): a merchant should be
able to see "what's been happening" without reading receipts one at a
time, and the flags it raises must be decided by fixed code, not by
whatever an AI model feels like saying today.

Unit tests hit compute_digest() directly -- no HTTP, no AI, no DB --
because the flag logic is the part that actually matters and must stay
deterministic. The one HTTP test proves the endpoint wires real
checkout activity into that same logic correctly, with the AI narration
step stubbed out (same reason Razorpay calls are stubbed elsewhere in
this suite: no live network dependency in the test run).
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import app.main as main_module
from app import ai_client
from app.main import app
from app.db.session import get_session
from app.engine.digest import compute_digest
from app.engine.identity import canonical_cart_bytes
from app.models.cart import CartItem


def _receipt(agent_id, decision, rules_checked, timestamp=None):
    return {
        "agent_id": agent_id,
        "decision": decision,
        "rules_checked": rules_checked,
        "cart_items": [],
        "cart_total": 10000,
        "timestamp": timestamp or datetime.now(timezone.utc),
    }


def _passed(name):
    return {"rule_name": name, "passed": True, "detail": "ok"}


def _failed(name):
    return {"rule_name": name, "passed": False, "detail": "nope"}


# ---------- compute_digest: pure unit tests ----------

def test_quiet_window_raises_no_flags():
    stats = compute_digest([_receipt("agent-a", "allow", [_passed("max_order_value")])], 0, 168)
    assert stats["totals"] == {"attempts": 1, "allowed": 1, "blocked": 0, "escalated": 0}
    assert stats["flags"] == []


def test_catalog_mismatch_block_raises_a_high_severity_flag():
    receipts = [_receipt("sneaky-agent", "block", [_failed("items_are_listed")])]
    stats = compute_digest(receipts, 0, 168)
    assert len(stats["flags"]) == 1
    flag = stats["flags"][0]
    assert flag["agent_id"] == "sneaky-agent"
    assert flag["flag_type"] == "catalog_mismatch"
    assert flag["severity"] == "high"
    assert flag["count"] == 1


def test_velocity_cap_hit_raises_a_medium_flag():
    receipts = [_receipt("fast-agent", "block", [_failed("velocity")])]
    stats = compute_digest(receipts, 0, 168)
    assert any(f["flag_type"] == "velocity_cap_hit" and f["severity"] == "medium" for f in stats["flags"])


def test_three_or_more_blocks_by_the_same_agent_raises_repeated_blocks_flag():
    receipts = [_receipt("persistent-agent", "block", [_failed("max_order_value")]) for _ in range(3)]
    stats = compute_digest(receipts, 0, 168)
    repeated = [f for f in stats["flags"] if f["flag_type"] == "repeated_blocks"]
    assert len(repeated) == 1
    assert repeated[0]["count"] == 3


def test_two_blocks_alone_do_not_trigger_repeated_blocks():
    """Below the threshold -- must not flag on 2, only 3+."""
    receipts = [_receipt("mild-agent", "block", [_failed("max_order_value")]) for _ in range(2)]
    stats = compute_digest(receipts, 0, 168)
    assert not any(f["flag_type"] == "repeated_blocks" for f in stats["flags"])


def test_flags_are_scoped_per_agent_not_merged_across_agents():
    """Two different agents each blocked twice must NOT combine into one repeated-blocks flag."""
    receipts = (
        [_receipt("agent-x", "block", [_failed("max_order_value")]) for _ in range(2)]
        + [_receipt("agent-y", "block", [_failed("max_order_value")]) for _ in range(2)]
    )
    stats = compute_digest(receipts, 0, 168)
    assert not any(f["flag_type"] == "repeated_blocks" for f in stats["flags"])
    agent_ids = {a["agent_id"] for a in stats["agents"]}
    assert agent_ids == {"agent-x", "agent-y"}
    assert all(a["blocked"] == 2 for a in stats["agents"])


def test_flags_sort_high_severity_first():
    receipts = [
        _receipt("agent-medium", "block", [_failed("velocity")]),
        _receipt("agent-high", "block", [_failed("items_are_listed")]),
    ]
    stats = compute_digest(receipts, 0, 168)
    assert stats["flags"][0]["severity"] == "high"


# ---------- GET /digest: proves real checkout activity feeds compute_digest correctly ----------

async def _fake_create_payment_link(amount_paise: int, description: str, currency: str = "INR") -> dict:
    return {"id": "plink_FAKE", "short_url": "https://rzp.io/rzp/fake", "status": "created"}


async def _fake_summarize_digest(stats: dict) -> dict:
    return {"headline": "stubbed", "summary": "stubbed", "flag_explanations": []}


@pytest.fixture()
def client(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    monkeypatch.setattr(main_module, "create_payment_link", _fake_create_payment_link)
    # Narration is a pure add-on over already-correct stats -- stub it so
    # this test doesn't depend on live network, same reasoning as
    # stubbing Razorpay elsewhere in this suite.
    monkeypatch.setattr(ai_client, "is_configured", lambda: True)
    monkeypatch.setattr(ai_client, "summarize_digest", _fake_summarize_digest)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def register_merchant(client, merchant_id):
    return client.post("/merchants/register", json={"merchant_id": merchant_id}).json()["api_key"]


def auth(key):
    return {"Authorization": f"Bearer {key}"}


def _sign(agent_id, items, client):
    key = Ed25519PrivateKey.generate()
    pub = key.public_key().public_bytes_raw().hex()
    client.post("/agents/register", json={"agent_id": agent_id, "public_key_hex": pub})
    return key.sign(canonical_cart_bytes([CartItem(**i) for i in items])).hex()


def test_digest_reflects_a_real_blocked_checkout_and_narrates_it(client):
    merchant_id = "shop_digest"
    key = register_merchant(client, merchant_id)
    client.post("/policy", headers=auth(key), json={
        "merchant_id": merchant_id, "max_order_value": 1000000, "deny_categories": [],
    })
    # No catalog uploaded on purpose in one variant would skip the check --
    # upload one so the invented item below is genuinely unlisted.
    client.post("/catalog", headers=auth(key), json={
        "merchant_id": merchant_id,
        "catalog": {"merchant_id": merchant_id, "products": [{
            "id": "real-item", "title": "Real Item",
            "variants": [{"id": "real-item", "title": "Real Item", "price": 5000, "category": "clothing"}],
        }]},
    })

    fake_items = [{"id": "invented-id", "title": "Invented", "price": 5000, "category": "clothing", "quantity": 1}]
    sig = _sign("probing-agent", fake_items, client)
    r = client.post("/checkout-sessions", json={
        "merchant_id": merchant_id, "agent_id": "probing-agent",
        "items": fake_items, "signature_hex": sig,
    })
    assert r.json()["receipt"]["decision"] == "block"

    digest = client.get("/digest", headers=auth(key), params={"merchant_id": merchant_id}).json()
    stats = digest["stats"]

    assert stats["totals"]["attempts"] == 1
    assert stats["totals"]["blocked"] == 1
    assert len(stats["flags"]) == 1
    assert stats["flags"][0]["agent_id"] == "probing-agent"
    assert stats["flags"][0]["flag_type"] == "catalog_mismatch"

    # narration is a separate call, deliberately -- GET /digest above must
    # stay fast and AI-free (see main.py's get_digest docstring); the stub
    # proves narrate_digest wires the already-computed stats through, not
    # that AI works live.
    narrated = client.post(
        "/digest/narrate", headers=auth(key), json={"merchant_id": merchant_id, "stats": stats},
    ).json()
    assert narrated["narrative"]["headline"] == "stubbed"


def test_digest_reflects_agent_revocation_status(client):
    """
    Flagging a problem is only half the point -- the merchant has to be
    able to act on it. GET /digest must tell the frontend, per agent,
    whether it's already revoked so a "Revoke" button can flip to
    "Unrevoke" without a page reload.
    """
    merchant_id = "shop_digest_revoke"
    key = register_merchant(client, merchant_id)
    client.post("/policy", headers=auth(key), json={
        "merchant_id": merchant_id, "max_order_value": 1000000, "deny_categories": [],
    })

    fake_items = [{"id": "ghost", "title": "Ghost", "price": 5000, "category": "clothing", "quantity": 1}]
    sig = _sign("watched-agent", fake_items, client)
    client.post("/checkout-sessions", json={
        "merchant_id": merchant_id, "agent_id": "watched-agent",
        "items": fake_items, "signature_hex": sig,
    })

    before = client.get("/digest", headers=auth(key), params={"merchant_id": merchant_id}).json()
    agent_before = next(a for a in before["stats"]["agents"] if a["agent_id"] == "watched-agent")
    assert agent_before["revoked"] is False

    r = client.post("/agents/watched-agent/revoke", headers=auth(key), params={"merchant_id": merchant_id})
    assert r.status_code == 200

    after = client.get("/digest", headers=auth(key), params={"merchant_id": merchant_id}).json()
    agent_after = next(a for a in after["stats"]["agents"] if a["agent_id"] == "watched-agent")
    assert agent_after["revoked"] is True


def test_digest_requires_merchant_auth(client):
    merchant_id = "shop_digest_auth"
    register_merchant(client, merchant_id)
    r = client.get("/digest", params={"merchant_id": merchant_id})
    assert r.status_code in (401, 403)
