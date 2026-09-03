"""
THE BOUNCER.

This file has no AI in it on purpose. It takes a cart and a policy
and checks the cart against every rule, one by one, like a checklist.

Why no AI here: real research (NIST) found that AI can be tricked into
ignoring its own instructions once someone specifically targets it.
So the actual "allow or block" decision has to be plain code that
always behaves the same way, every time, no exceptions.
"""
from app.models.cart import Cart
from app.models.policy import Policy
from app.models.receipt import Receipt, RuleResult, Decision
from datetime import datetime, timezone


def check_max_order_value(cart: Cart, policy: Policy) -> RuleResult:
    if cart.total > policy.max_order_value:
        return RuleResult(
            rule_name="max_order_value",
            passed=False,
            detail=f"cart total {cart.total} paise exceeds limit {policy.max_order_value} paise",
        )
    return RuleResult(rule_name="max_order_value", passed=True, detail="within limit")


def check_deny_categories(cart: Cart, policy: Policy) -> RuleResult:
    for item in cart.items:
        if item.category in policy.deny_categories:
            return RuleResult(
                rule_name="deny_categories",
                passed=False,
                detail=f"item '{item.title}' has banned category '{item.category}'",
            )
    return RuleResult(rule_name="deny_categories", passed=True, detail="no banned categories found")


def check_max_units_per_sku(cart: Cart, policy: Policy) -> RuleResult:
    for item in cart.items:
        if item.quantity > policy.max_units_per_sku:
            return RuleResult(
                rule_name="max_units_per_sku",
                passed=False,
                detail=f"item '{item.title}' quantity {item.quantity} exceeds max {policy.max_units_per_sku}",
            )
    return RuleResult(rule_name="max_units_per_sku", passed=True, detail="quantities within limit")


def check_identity_verified(policy: Policy, identity_verified: bool) -> RuleResult:
    """
    The identity check (see engine/identity.py). If the shop owner
    requires proof of identity and the agent didn't provide a valid
    signature, the whole cart is blocked -- no matter what else is in it.
    """
    if policy.require_signed_identity and not identity_verified:
        return RuleResult(
            rule_name="identity_verified",
            passed=False,
            detail="agent did not present a valid signature -- cannot confirm who this really is",
        )
    return RuleResult(rule_name="identity_verified", passed=True, detail="identity confirmed or not required")


# Every rule function goes in this list. Adding a new rule later = write
# one function above, add its name here. Nothing else changes.
ALL_CHECKS = [
    check_max_order_value,
    check_deny_categories,
    check_max_units_per_sku,
]


def evaluate(cart: Cart, policy: Policy, agent_id: str, identity_verified: bool = True) -> Receipt:
    """
    Run every check. If even ONE fails, the whole cart is blocked.
    This matches AP2's own rule: an unknown or failing check always
    means "fail closed", never "let it through and hope for the best".
    """
    results = [check(cart, policy) for check in ALL_CHECKS]
    results.append(check_identity_verified(policy, identity_verified))

    if any(not r.passed for r in results):
        decision = Decision.BLOCK
    elif policy.escalate_above is not None and cart.total > policy.escalate_above:
        decision = Decision.ESCALATE
    else:
        decision = Decision.ALLOW

    return Receipt(
        cart_id=cart.id,
        merchant_id=cart.merchant_id,
        agent_id=agent_id,
        decision=decision,
        rules_checked=results,
        cart_total=cart.total,
        timestamp=datetime.now(timezone.utc),
    )
