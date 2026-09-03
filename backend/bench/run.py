"""
THE HONEST NUMBERS.

Most demos show one cherry-picked example working. We do the opposite:
throw a batch of many different carts at the bouncer -- clean ones,
scam ones, over-limit ones, unsigned ones -- and report exactly how
many of each got allowed, blocked, or escalated.

The most important number here is FALSE POSITIVES: legitimate, honest
orders that got wrongly blocked. Real research found merchants who
over-block AI traffic lose real revenue (research/05-market-data.md).
Reporting that number honestly, instead of hiding it, is the point.
"""
import sys
import os
import random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from app.models.cart import Cart, CartItem
from app.models.policy import Policy
from app.engine.evaluate import evaluate
from app.engine.identity import canonical_cart_bytes, verify_agent_signature

random.seed(42)  # same "random" batch every run, so results are reproducible

POLICY = Policy(
    merchant_id="shop_123",
    max_order_value=1000000,     # Rs 10,000
    deny_categories=["gift_card"],
    max_units_per_sku=5,
)

REAL_KEY = Ed25519PrivateKey.generate()
REAL_PUBLIC_HEX = REAL_KEY.public_key().public_bytes_raw().hex()


class TestCase:
    def __init__(self, label: str, items: list[CartItem], signed: bool, expected: str):
        self.label = label
        self.items = items
        self.signed = signed   # was this cart signed with the REAL key?
        self.expected = expected  # what SHOULD happen -- "allow" or "block"


def build_cases() -> list[TestCase]:
    cases = []

    # 30 clearly legitimate, clean, well-signed orders -- these should ALL allow.
    products = [
        ("shirt", "Blue Shirt", 45000, "clothing"),
        ("jeans", "Denim Jeans", 129900, "clothing"),
        ("wallet", "Leather Wallet", 89900, "accessories"),
        ("shoes", "Running Shoes", 299900, "footwear"),
    ]
    for i in range(30):
        name, title, price, category = random.choice(products)
        qty = random.randint(1, 3)
        cases.append(TestCase(
            f"clean-{i}",
            [CartItem(id=name, title=title, price=price, category=category, quantity=qty)],
            signed=True,
            expected="allow",
        ))

    # 10 scam carts -- a clean item plus a smuggled gift card. Should ALL block.
    for i in range(10):
        cases.append(TestCase(
            f"poisoned-{i}",
            [
                CartItem(id="shirt", title="Blue Shirt", price=45000, category="clothing"),
                CartItem(id="giftcard", title="Gift Card", price=200000, category="gift_card"),
            ],
            signed=True,
            expected="block",
        ))

    # 5 orders that are just too expensive. Should ALL block.
    for i in range(5):
        cases.append(TestCase(
            f"over-limit-{i}",
            [CartItem(id="shoes", title="Running Shoes", price=1500000, category="footwear", quantity=2)],
            signed=True,
            expected="block",
        ))

    # 5 legitimate-looking carts but NOT actually signed by the real key
    # (an impersonator). Should ALL block, purely on identity.
    for i in range(5):
        cases.append(TestCase(
            f"unsigned-{i}",
            [CartItem(id="shirt", title="Blue Shirt", price=45000, category="clothing")],
            signed=False,
            expected="block",
        ))

    return cases


def main():
    cases = build_cases()
    counts = {"allow": 0, "block": 0, "escalate": 0}
    false_positives = []   # expected allow, but we blocked it -- the number that matters most
    false_negatives = []   # expected block, but we allowed it -- the dangerous kind

    for case in cases:
        cart_bytes = canonical_cart_bytes(case.items)
        if case.signed:
            signature = REAL_KEY.sign(cart_bytes).hex()
            identity_verified = verify_agent_signature(case.items, signature, REAL_PUBLIC_HEX)
        else:
            identity_verified = False  # impersonator has no valid signature

        cart = Cart(id=case.label, merchant_id="shop_123", items=case.items)
        receipt = evaluate(cart, POLICY, agent_id="bench-agent", identity_verified=identity_verified)

        counts[receipt.decision.value] += 1

        if case.expected == "allow" and receipt.decision.value != "allow":
            false_positives.append(case.label)
        if case.expected == "block" and receipt.decision.value == "allow":
            false_negatives.append(case.label)

    total = len(cases)
    print(f"Total orders tested: {total}")
    print(f"  Allowed:   {counts['allow']}")
    print(f"  Blocked:   {counts['block']}")
    print(f"  Escalated: {counts['escalate']}")
    print()
    print(f"False positives (legitimate orders wrongly blocked): {len(false_positives)}")
    if false_positives:
        print(f"  -> {false_positives}")
    print(f"False negatives (bad orders wrongly allowed):        {len(false_negatives)}")
    if false_negatives:
        print(f"  -> {false_negatives}")

    write_results_md(total, counts, false_positives, false_negatives)


def write_results_md(total, counts, false_positives, false_negatives):
    path = os.path.join(os.path.dirname(__file__), "results.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Benchmark results\n\n")
        f.write(f"Ran {total} synthetic orders: clean, poisoned (hidden gift card), "
                f"over-limit, and unsigned (impersonator) carts.\n\n")
        f.write("| Outcome | Count |\n|---|---|\n")
        f.write(f"| Allowed | {counts['allow']} |\n")
        f.write(f"| Blocked | {counts['block']} |\n")
        f.write(f"| Escalated | {counts['escalate']} |\n\n")
        f.write(f"**False positives (legitimate orders wrongly blocked): {len(false_positives)}**\n\n")
        f.write("This is the number most demos hide. A system that blocks everything has a perfect "
                "block rate and a useless business. Zero false positives here means every clean, "
                "well-signed order got through.\n\n")
        f.write(f"**False negatives (bad orders wrongly allowed): {len(false_negatives)}**\n\n")
        f.write("This is the dangerous kind. Zero here means every scam, over-limit, and "
                "unverified-identity attempt in this batch was actually caught.\n")
    print(f"\nWrote {path}")


if __name__ == "__main__":
    main()
