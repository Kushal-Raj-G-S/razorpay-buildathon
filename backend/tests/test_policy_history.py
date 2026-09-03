"""
Every POST /policy save must land a snapshot in history, most-recent
first, so a merchant tweaking one number doesn't lose the ability to see
(and re-load) what the rules used to say. Direct feature request: saving
rules from scratch every time was real friction.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import get_session


@pytest.fixture()
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def register_merchant(client, merchant_id):
    return client.post("/merchants/register", json={"merchant_id": merchant_id}).json()["api_key"]


def auth(key):
    return {"Authorization": f"Bearer {key}"}


def test_every_save_appends_to_history_most_recent_first(client):
    merchant_id = "shop_policy_history"
    key = register_merchant(client, merchant_id)

    client.post("/policy", headers=auth(key), json={
        "merchant_id": merchant_id, "max_order_value": 500000, "deny_categories": [],
    })
    client.post("/policy", headers=auth(key), json={
        "merchant_id": merchant_id, "max_order_value": 1000000, "deny_categories": ["gift_card"],
    })

    history = client.get(f"/policy/{merchant_id}/history", headers=auth(key)).json()
    assert len(history) == 2
    assert history[0]["policy"]["max_order_value"] == 1000000  # most recent first
    assert history[1]["policy"]["max_order_value"] == 500000
    # The row's own timestamp, not something the client can spoof
    assert "saved_at" in history[0]


def test_current_policy_is_unaffected_by_history_bookkeeping(client):
    """get_policy must still be a single-row read -- history is additive, not a replacement."""
    merchant_id = "shop_policy_history_2"
    key = register_merchant(client, merchant_id)
    client.post("/policy", headers=auth(key), json={
        "merchant_id": merchant_id, "max_order_value": 700000, "deny_categories": [],
    })
    current = client.get(f"/policy/{merchant_id}").json()
    assert current["max_order_value"] == 700000


def test_policy_history_requires_merchant_auth(client):
    merchant_id = "shop_policy_history_auth"
    register_merchant(client, merchant_id)
    r = client.get(f"/policy/{merchant_id}/history")
    assert r.status_code in (401, 403)
