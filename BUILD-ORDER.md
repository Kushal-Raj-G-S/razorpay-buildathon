# Build order — 3 days

Deadline **5 September**. Today is **2 September (late)**. So realistically **3, 4, 5 Sept**.

Ordered so that **the project is submittable at the end of every day**. If you run out of time, you
stop where you are and still have something coherent — you never end up with a half-finished
architecture and nothing to show.

**Rule: commit at every ✅. Never leave the repo in a state you can't submit.**

---

## Tonight (2 Sept) — do nothing

You have a headache. The research is done, committed and pushed. There is no decision left that
needs you tonight. Sleep.

If you genuinely can't sleep, the only zero-thought task worth doing:
`pip install fastapi uvicorn pydantic pyyaml cryptography httpx` and confirm your Razorpay **test**
keys load from `.env`. Nothing else.

---

## Day 1 (3 Sept) — the spine

Goal: **a poisoned cart gets blocked and a receipt explains why.** That single path is the whole
pitch. Everything after it is widening, not deepening.

### Morning — schemas first, no logic
- [ ] `models/` — Pydantic models for UCP `Product`, `Variant`, `Item`, `LineItem`, `Checkout`.
      Field names exactly as in [research/06 §9.1](research/06-protocols.md) — copy them, don't
      improvise. Integer minor units everywhere.
- [ ] `models/policy.py` — the policy DSL model:
      `max_order_value`, `deny_categories[]`, `max_units_per_sku`, `require_identity_tier`,
      `escalate_above`, `per_agent_daily_cap`
- [ ] `models/receipt.py` — decision receipt: `agent_identity`, `authority_presented`,
      `rules_evaluated[]` (rule name, verdict, triggering value), `cart_hash`, `decision`
      (`allow`/`block`/`escalate`), `timestamps`
- ✅ **commit:** "Add UCP, policy and receipt schemas"

### Afternoon — the deterministic evaluator (the core; no AI anywhere near it)
- [ ] `engine/evaluate.py` — pure function: `(cart, policy, agent_context) → Decision`.
      One small function per rule. Every rule returns *its own* verdict + the value that triggered
      it, so the receipt can name it. **Unknown rule type → fail closed** (AP2's rule: *"Any unknown
      Constraints MUST be treated as failing evaluation"*).
- [ ] `engine/receipt.py` — build the receipt, canonicalize (JCS-style: sorted keys, no whitespace),
      sign with Ed25519 via `cryptography`. Verify function too.
- [ ] Unit tests: clean cart allows; over-limit blocks; gift card in cart blocks; unknown rule
      fails closed.
- ✅ **commit:** "Add deterministic policy evaluator and signed decision receipts"

### Evening — the demo that matters
- [ ] `demos/poisoned_cart.py` — Unit 42 scenario: valid agent, valid authority, cart with an
      appended `gift_card` line item the buyer never saw → blocked, receipt names the line item and
      the rule.
- ✅ **commit:** "Reproduce Unit 42 cart payload poisoning, blocked with receipt"

> **End of Day 1 you can submit.** A real problem, a working core, a documented failure caught. If
> everything after this goes wrong, you still have a coherent project.

---

## Day 2 (4 Sept) — make it a real merchant surface

### Morning — the catalog (Door B)
- [ ] `catalog/ingest.py` — messy CSV/Excel/JSON → UCP `Product`/`Variant`. **This is where AI
      belongs**: attribute extraction, category mapping, variant inference ("Blue Tshirt L 499/-").
      Use whatever you already know best from Baxel — GLiNER, structured LLM output, your call.
- [ ] `api/` FastAPI: serve `/.well-known/ucp` profile, `POST /catalog/search`,
      `POST /catalog/lookup`, `POST /catalog/product`
- [ ] `POST /checkout-sessions` + `/complete` — the gate lives here: evaluate policy **before**
      anything touches Razorpay
- ✅ **commit:** "Serve UCP catalog and gated checkout for a Razorpay merchant"

### Afternoon — identity + money
- [ ] `identity/verify.py` — RFC 9421 verification: fetch JWKS from the declared `UCP-Agent`
      profile, match `keyid`→`kid`, rebuild signature base over
      `@method @authority @path ucp-agent idempotency-key content-digest`, check
      `created`/`expires`, cache nonces. Tiers: `signed` > `token` > `anonymous`.
- [ ] Razorpay **test mode**: order create + payment link, on the allow path only. REST directly, or
      their official MCP server (40+ tools) — either is fine, REST is fewer moving parts.
- [ ] Enforce the statutory bounds in code: **₹10,000** block cap, **90 days**, **one per merchant**,
      **3 retries/24h**. Comment each with its NPCI/RBI source.
- ✅ **commit:** "Verify agent identity per RFC 9421 and execute on Razorpay test mode"

### Evening — revocation (the gap nobody fills)
- [ ] `POST /agents/{id}/revoke` → next call from that agent **fails closed**; revocation lands in
      the receipt chain
- [ ] `demos/revoke_midflight.py`
- ✅ **commit:** "Add merchant-side revocation, failing closed"

---

## Day 3 (5 Sept) — evidence, then ship

**Stop building by 14:00 whatever state you're in.** The video and form take longer than you think.

### Morning — honest numbers
- [ ] `bench/run.py` — ≥50 synthetic orders: clean, over-limit, poisoned, unsigned-agent, edge cases
- [ ] Report allow/block/escalate **and false positives** — legitimate orders wrongly blocked. This
      is the number nobody demos; it's your differentiator. Print it as a table, save it to
      `bench/results.md`.
- [ ] Natural-language → policy compiler *if there's time*: merchant types a sentence, model emits
      the YAML, **human approves before it takes effect**. This is the cleanest illustration of the
      thesis. **First thing to cut if you're behind.**
- ✅ **commit:** "Add batch harness reporting allow/block/escalate and false-positive cost"

### Afternoon — the deliverables
- [ ] README: problem, architecture diagram, run instructions, the "no LLM in the decision path"
      rationale with the NIST/StakeBench numbers, and an explicit "what I did not build" section
- [ ] Record the video from [PITCH.md](PITCH.md). Read it twice, then talk. One take is fine.
- [ ] **`gh repo edit --visibility public`** ← easy to forget, breaks the submission
- [ ] Write "what broke" **from your actual log**. Do not use the pre-written candidates unless they
      really happened.
- [ ] Submit: https://forms.gle/d9r2gvxp8cmoZhon9
- ✅ **commit:** "Add README and benchmark results"

---

## Cut list, in order

If you're behind, cut from the top. Each cut leaves the project coherent.

1. NL → policy compiler *(mention it as designed-not-built; the manual YAML still proves the thesis)*
2. AI catalog ingestion → hand-write one clean UCP catalog JSON, note that normalization is the
   obvious extension
3. Razorpay live test-mode call → keep the order-payload construction, stop short of the network call
4. Revocation demo → keep the endpoint, drop the scripted scenario
5. **Never cut:** the deterministic evaluator, the signed receipt, the poisoned-cart demo, the
   false-positive number. Those four *are* the project.

---

## Stack

Your call entirely — but if you want a default that matches what's already on your resume and adds
no learning cost: **Python + FastAPI + Pydantic + PyYAML + `cryptography` (Ed25519) + httpx.**

Two notes:
- **No agent framework in the decision path.** LangGraph/CrewAI are the right tools for catalog
  normalization and the NL→policy compiler, and the wrong tool for evaluating a bound. That split
  *is* the thesis — keep the dependency boundary visible in the repo layout so a reviewer sees it.
- Keep `engine/` free of any import that can make a network call or an inference request. That's the
  clearest possible proof of the claim.
