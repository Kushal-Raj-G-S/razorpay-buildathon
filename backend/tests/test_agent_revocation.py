"""
Proves POST /agents/{id}/revoke actually stops an agent from checking
out -- including one that never called POST /agents/register first,
which is the normal case for an agent only ever seen through
/checkout-sessions.

Found live: clicking "Revoke" on the Digest page for an agent with no
prior registration returned 200 OK and the UI flipped to "Unrevoke", but
a follow-up checkout call for that same agent still succeeded --
repo.set_agent_revoked() silently did nothing because it only updated an
existing AgentRow and never created one. Fixed in db/repo.py; this test
is the regression guard.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

import app.main as main_module
from app.main import app
from app.db.session import get_session


async def _fake_create_payment_link(amount_paise: int, description: str, currency: str = "INR") -> dict:
    return {"id": "plink_FAKE", "short_url": "https://rzp.io/rzp/fake", "status": "created"}


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


def register_merchant(client, merchant_id):
    return client.post("/merchants/register", json={"merchant_id": merchant_id}).json()["api_key"]


def auth(key):
    return {"Authorization": f"Bearer {key}"}


def test_revoking_an_agent_that_never_self_registered_actually_blocks_it(client):
    """The exact bug: an agent that only ever appeared via /checkout-sessions,
    never via /agents/register, must still be revocable."""
    merchant_id = "shop_revoke_unregistered"
    key = register_merchant(client, merchant_id)
    client.post("/policy", headers=auth(key), json={
        "merchant_id": merchant_id, "max_order_value": 1000000, "deny_categories": [],
        "require_signed_identity": False,  # isolate revocation, not identity verification
    })

    items = [{"id": "anything", "title": "Anything", "price": 1000, "category": "clothing", "quantity": 1}]

    # First checkout: agent has never registered a key, never been revoked -- allowed through.
    before = client.post("/checkout-sessions", json={
        "merchant_id": merchant_id, "agent_id": "never-registered-agent", "items": items,
    })
    assert before.json()["receipt"]["decision"] == "allow"

    revoke = client.post(
        "/agents/never-registered-agent/revoke",
        params={"merchant_id": merchant_id},
        headers=auth(key),
    )
    assert revoke.status_code == 200

    after = client.post("/checkout-sessions", json={
        "merchant_id": merchant_id, "agent_id": "never-registered-agent", "items": items,
    })
    assert after.status_code == 403


def test_unrevoke_restores_access_for_a_previously_unregistered_agent(client):
    merchant_id = "shop_unrevoke_unregistered"
    key = register_merchant(client, merchant_id)
    client.post("/policy", headers=auth(key), json={
        "merchant_id": merchant_id, "max_order_value": 1000000, "deny_categories": [],
        "require_signed_identity": False,  # isolate revocation, not identity verification
    })

    client.post(
        "/agents/fresh-agent/revoke", params={"merchant_id": merchant_id}, headers=auth(key),
    )
    blocked = client.post("/checkout-sessions", json={
        "merchant_id": merchant_id, "agent_id": "fresh-agent",
        "items": [{"id": "x", "title": "X", "price": 1000, "category": "c", "quantity": 1}],
    })
    assert blocked.status_code == 403

    client.post(
        "/agents/fresh-agent/unrevoke", params={"merchant_id": merchant_id}, headers=auth(key),
    )
    allowed = client.post("/checkout-sessions", json={
        "merchant_id": merchant_id, "agent_id": "fresh-agent",
        "items": [{"id": "x", "title": "X", "price": 1000, "category": "c", "quantity": 1}],
    })
    assert allowed.json()["receipt"]["decision"] == "allow"
