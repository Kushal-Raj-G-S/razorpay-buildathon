"""
Proves the ESCALATE path -- the third possible decision, never tested
until now. An order that's too big to auto-approve but breaks no other
rule shouldn't be silently blocked OR silently allowed -- it should be
flagged for a human to look at.
"""
import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from app.engine.identity import canonical_cart_bytes

BASE = "http://127.0.0.1:8000"


def main():
    key = Ed25519PrivateKey.generate()
    public_hex = key.public_key().public_bytes_raw().hex()

    httpx.post(f"{BASE}/agents/register", json={"agent_id": "escalate-test-agent", "public_key_hex": public_hex})

    httpx.post(f"{BASE}/policy", json={
        "merchant_id": "shop_esc",
        "max_order_value": 1000000,      # Rs 10,000 hard cap
        "deny_categories": ["gift_card"],
        "max_units_per_sku": 5,
        "escalate_above": 500000,        # Rs 5,000 -- above this, ask a human
    })

    items = [{"id": "shoes", "title": "Running Shoes", "price": 700000, "category": "footwear", "quantity": 1}]

    from app.models.cart import CartItem
    cart_items = [CartItem(**i) for i in items]
    signature = key.sign(canonical_cart_bytes(cart_items)).hex()

    response = httpx.post(f"{BASE}/checkout-sessions", json={
        "merchant_id": "shop_esc",
        "agent_id": "escalate-test-agent",
        "items": items,
        "signature_hex": signature,
    })
    receipt = response.json()["receipt"]
    print(f"Cart total: Rs {receipt['cart_total'] / 100:.2f} "
          f"(above escalate_above Rs 5000, below max_order_value Rs 10000)")
    print(f"Decision: {receipt['decision'].upper()}")
    for r in receipt["rules_checked"]:
        status = "PASS" if r["passed"] else "FAIL"
        print(f"  [{status}] {r['rule_name']}: {r['detail']}")


if __name__ == "__main__":
    main()
