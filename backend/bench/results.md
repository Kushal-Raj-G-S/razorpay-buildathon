# Benchmark results

Ran 50 synthetic orders: clean, poisoned (hidden gift card), over-limit, and unsigned (impersonator) carts.

| Outcome | Count |
|---|---|
| Allowed | 30 |
| Blocked | 20 |
| Escalated | 0 |

**False positives (legitimate orders wrongly blocked): 0**

This is the number most demos hide. A system that blocks everything has a perfect block rate and a useless business. Zero false positives here means every clean, well-signed order got through.

**False negatives (bad orders wrongly allowed): 0**

This is the dangerous kind. Zero here means every scam, over-limit, and unverified-identity attempt in this batch was actually caught.
