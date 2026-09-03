"""
Proves the signing actually protects the receipt.

We sign a real receipt, verify it (should pass), then secretly edit it
(like someone trying to fake a different decision) and verify again
(should fail).
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.models.cart import Cart, CartItem
from app.models.policy import Policy
from app.engine.evaluate import evaluate
from app.engine.signing import generate_keypair, sign_receipt, verify_receipt


def main():
    private_key, public_key = generate_keypair()

    policy = Policy(merchant_id="shop_123", max_order_value=1000000, deny_categories=["gift_card"])
    cart = Cart(
        id="cart_xyz", merchant_id="shop_123",
        items=[CartItem(id="shirt", title="Blue Shirt", price=45000, category="clothing")],
    )

    receipt = evaluate(cart, policy, agent_id="agent-007")
    signed = sign_receipt(receipt, private_key)

    print("Original signed receipt, decision:", signed.decision.value)
    print("Verify original ->", verify_receipt(signed, public_key))

    # Someone tries to sneakily change the cart total after the fact
    tampered = signed.model_copy(update={"cart_total": 1})
    print("\nTampered receipt, cart_total forged to:", tampered.cart_total)
    print("Verify tampered ->", verify_receipt(tampered, public_key))


if __name__ == "__main__":
    main()
