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


def check_cod_allowed(cart: Cart, policy: Policy) -> RuleResult:
    """
    No protocol we researched -- AP2, ACP, UCP, UPI Reserve Pay -- gates
    Cash on Delivery. They only ever authorize prepaid money. But COD is
    50-70% of real Indian D2C orders (research/03), and it needs ZERO
    payment authorization to place: an agent can put in dozens of COD
    orders and nothing anywhere stops it. Unless the merchant explicitly
    opted in, an agent-initiated COD order is blocked by default.
    """
    if cart.payment_mode == "cod" and not policy.allow_cod_for_agents:
        return RuleResult(
            rule_name="cod_allowed",
            passed=False,
            detail="agent tried to place a Cash on Delivery order, but this merchant "
                   "requires agent orders to be prepaid (COD needs no payment authorization "
                   "at all -- see policy.allow_cod_for_agents)",
        )
    return RuleResult(rule_name="cod_allowed", passed=True, detail="prepaid order, or COD explicitly allowed")


def check_velocity(policy: Policy, recent_order_count: int) -> RuleResult:
    """
    UPI Reserve Pay itself caps retries at 3 in 24 hours (research/03) --
    the regulator already treats ORDER FREQUENCY, not just order size,
    as the primary threat. Every other check here only ever looks at one
    cart in isolation; this is the one check with memory of what this
    agent has already done. `recent_order_count` is computed by the
    caller (see db/repo.py) before evaluate() runs, so this function
    itself stays a pure, stateless check like every other rule.
    """
    if policy.max_orders_per_agent_per_window is None:
        return RuleResult(rule_name="velocity", passed=True, detail="no velocity limit set")

    if recent_order_count >= policy.max_orders_per_agent_per_window:
        return RuleResult(
            rule_name="velocity",
            passed=False,
            detail=f"agent has already placed {recent_order_count} orders in the last "
                   f"{policy.velocity_window_minutes} minutes, at or above the limit of "
                   f"{policy.max_orders_per_agent_per_window}",
        )
    return RuleResult(rule_name="velocity", passed=True,
                       detail=f"{recent_order_count} orders in window, within limit")


# Every rule function goes in this list. Adding a new rule later = write
# one function above, add its name here. Nothing else changes.
ALL_CHECKS = [
    check_max_order_value,
    check_deny_categories,
    check_max_units_per_sku,
    check_cod_allowed,
]


def evaluate(cart: Cart, policy: Policy, agent_id: str, identity_verified: bool = True,
             recent_order_count: int = 0) -> Receipt:
    """
    Run every check. If even ONE fails, the whole cart is blocked.
    This matches AP2's own rule: an unknown or failing check always
    means "fail closed", never "let it through and hope for the best".
    """
    results = [check(cart, policy) for check in ALL_CHECKS]
    results.append(check_identity_verified(policy, identity_verified))
    results.append(check_velocity(policy, recent_order_count))

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
