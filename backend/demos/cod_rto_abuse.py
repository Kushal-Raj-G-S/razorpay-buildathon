"""
THE REAL DISASTER, NOT THE EXOTIC ONE.

Every agentic commerce protocol we researched -- AP2, ACP, UCP, even UPI
Reserve Pay -- only ever authorizes PREPAID money. None of them touch
Cash on Delivery. That's a blind spot for the US/global teams that built
them, because COD barely exists there.

In India, COD is 50-70% of real D2C order volume, and RTO on COD orders
already runs 20-40% BEFORE agents ever entered the picture (see
research/03-india-uap-razorpay.md). A COD order needs ZERO payment
authorization to place -- no card, no UPI mandate, nothing. So an AI
agent that misunderstands an instruction, gets manipulated, or is just
buggy, can place dozens of COD orders in minutes and NOTHING in any
protocol stops it, because none of them were built with COD in mind at
all.

This is the scenario a merchant actually loses sleep over -- not a
cryptographically signed mandate exploit, but an agent quietly placing
30 COD orders for a customer who never asked for 30 of anything, and
finding out only when the RTO bills arrive.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.models.cart import Cart, CartItem
from app.models.policy import Policy
from app.engine.evaluate import evaluate


def main():
    # Default policy: agents are NOT allowed to place COD orders unless
    # the merchant explicitly says so. That's the whole fix.
    policy = Policy(
        merchant_id="shop_india",
        max_order_value=1000000,
        deny_categories=["gift_card"],
        allow_cod_for_agents=False,   # <-- the default that actually matters here
    )

    cart = Cart(
        id="cod_cart_1",
        merchant_id="shop_india",
        payment_mode="cod",           # the agent is trying to place this as Cash on Delivery
        items=[
            CartItem(id="jeans", title="Denim Jeans", price=129900, category="clothing", quantity=1),
        ],
    )

    receipt = evaluate(cart, policy, agent_id="rto-risk-agent")

    print(f"Payment mode: {cart.payment_mode}")
    print(f"DECISION: {receipt.decision.value.upper()}\n")
    for r in receipt.rules_checked:
        status = "PASS" if r.passed else "FAIL"
        print(f"  [{status}] {r.rule_name}: {r.detail}")

    print("\n--- Now the merchant explicitly opts a specific trusted agent into COD ---")
    policy_opted_in = policy.model_copy(update={"allow_cod_for_agents": True})
    receipt2 = evaluate(cart, policy_opted_in, agent_id="rto-risk-agent")
    print(f"DECISION: {receipt2.decision.value.upper()} (merchant's own choice, not an unnoticed default)")


if __name__ == "__main__":
    main()
