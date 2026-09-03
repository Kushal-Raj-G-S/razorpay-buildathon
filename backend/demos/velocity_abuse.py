"""
Every other check in this project looks at ONE cart at a time. This is
the one with memory.

UPI Reserve Pay itself caps failed-debit retries at 3 in 24 hours (see
research/03-india-uap-razorpay.md) -- the regulator's own design already
treats how OFTEN an agent transacts as the primary threat, not just how
MUCH any single order costs. A single Rs 400 order is nothing. Forty
Rs 400 orders in ten minutes from the same agent is a very different
story, and a rule engine that only checks cart totals will never catch
it, because no individual cart ever breaks a limit.

This runs the same clean, well-signed, perfectly legal-looking cart
through the bouncer repeatedly and shows exactly where it starts getting
caught -- purely on frequency, nothing else about the order changes.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.models.cart import Cart, CartItem
from app.models.policy import Policy
from app.engine.evaluate import evaluate


def main():
    policy = Policy(
        merchant_id="shop_velocity",
        max_order_value=1000000,
        deny_categories=["gift_card"],
        max_orders_per_agent_per_window=5,
        velocity_window_minutes=60,
    )

    items = [CartItem(id="socks", title="Pack of Socks", price=40000, category="clothing")]

    print(f"Policy: max {policy.max_orders_per_agent_per_window} orders per agent "
          f"per {policy.velocity_window_minutes} minutes\n")

    for attempt in range(1, 9):
        cart = Cart(id=f"velocity_cart_{attempt}", merchant_id="shop_velocity", items=items)
        # recent_order_count simulates "this agent has already placed
        # (attempt - 1) orders in this window" -- in the real server this
        # number comes from db/repo.py's count_recent_orders() against
        # actual receipt history, not a hand-fed counter like here.
        receipt = evaluate(cart, policy, agent_id="rapid-fire-agent", recent_order_count=attempt - 1)
        velocity_result = next(r for r in receipt.rules_checked if r.rule_name == "velocity")
        status = "PASS" if velocity_result.passed else "FAIL"
        print(f"Order #{attempt}: DECISION={receipt.decision.value.upper():9s} "
              f"velocity=[{status}] {velocity_result.detail}")


if __name__ == "__main__":
    main()
