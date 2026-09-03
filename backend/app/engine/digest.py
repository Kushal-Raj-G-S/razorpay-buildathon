"""
Turns a window of raw receipts into merchant-facing facts: totals, a
per-agent footprint (every agent that has touched this store, not just
the one order in front of you), and a set of FLAGS -- things worth a
merchant's attention.

Why this file exists: "the merchant writes rules once and the system
enforces them" is not enough on its own. A rule only catches what it was
written for; a merchant who never looks at anything again has no way to
notice a pattern -- one agent probing the same block five different ways,
another quietly hitting a frequency cap over and over. Big companies keep
security teams to watch for exactly that. A small shop owner has nobody.
This is the closest thing this project has to give them: the footprint
of every agent that has been near their store, laid out automatically.

This file has NO AI in it, on purpose, for the same reason evaluate.py
doesn't: what counts as "worth flagging" is decided by fixed, checkable
code, not a model's judgment call, so it can't be talked out of flagging
something. ai_client.py's summarize_digest() is only allowed to turn
this file's output into plain sentences for a non-technical reader -- it
never adds, removes, or reweights a flag.
"""
from collections import defaultdict

_DECISION_KEY = {"allow": "allowed", "block": "blocked", "escalate": "escalated"}


def compute_digest(receipts: list[dict], escalation_count: int, window_hours: int) -> dict:
    """
    `receipts`: list of dicts with agent_id, decision ("allow"/"block"/
    "escalate"), rules_checked (list of {rule_name, passed, detail}),
    cart_items, cart_total, timestamp -- the raw shape stored on
    ReceiptRow (see db/repo.py's list_receipts_since).
    """
    totals = {"attempts": 0, "allowed": 0, "blocked": 0, "escalated": 0}
    agents: dict[str, dict] = {}

    for r in receipts:
        totals["attempts"] += 1
        totals[_DECISION_KEY[r["decision"]]] += 1

        agent_id = r["agent_id"]
        a = agents.setdefault(agent_id, {
            "agent_id": agent_id, "attempts": 0, "allowed": 0, "blocked": 0,
            "escalated": 0, "blocked_rules": defaultdict(int),
            "first_seen": r["timestamp"], "last_seen": r["timestamp"],
        })
        a["attempts"] += 1
        a[_DECISION_KEY[r["decision"]]] += 1
        a["first_seen"] = min(a["first_seen"], r["timestamp"])
        a["last_seen"] = max(a["last_seen"], r["timestamp"])

        if r["decision"] == "block":
            for rule in r["rules_checked"]:
                if not rule["passed"]:
                    a["blocked_rules"][rule["rule_name"]] += 1

    flags: list[dict] = []
    for agent_id, a in agents.items():
        catalog_mismatches = a["blocked_rules"].get("items_are_listed", 0)
        if catalog_mismatches > 0:
            flags.append({
                "severity": "high",
                "agent_id": agent_id,
                "flag_type": "catalog_mismatch",
                "count": catalog_mismatches,
                "detail": f"tried to check out {catalog_mismatches} item(s) that didn't match anything in "
                          f"your real catalog -- the exact pattern of an agent trying to disguise what it's "
                          f"actually buying",
            })

        velocity_hits = a["blocked_rules"].get("velocity", 0)
        if velocity_hits > 0:
            flags.append({
                "severity": "medium",
                "agent_id": agent_id,
                "flag_type": "velocity_cap_hit",
                "count": velocity_hits,
                "detail": f"hit your order-frequency limit {velocity_hits} time(s) -- tried to order faster "
                          f"than you allow",
            })

        if a["blocked"] >= 3:
            flags.append({
                "severity": "medium",
                "agent_id": agent_id,
                "flag_type": "repeated_blocks",
                "count": a["blocked"],
                "detail": f"was blocked {a['blocked']} separate times in this window and kept trying anyway",
            })

        a["blocked_rules"] = dict(a["blocked_rules"])  # defaultdict -> plain dict, JSON-safe

    severity_order = {"high": 0, "medium": 1, "low": 2}
    flags.sort(key=lambda f: severity_order[f["severity"]])

    return {
        "window_hours": window_hours,
        "totals": totals,
        "escalations_pending_or_reviewed": escalation_count,
        "agents": list(agents.values()),
        "flags": flags,
    }
