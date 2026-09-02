# Build decision

Written 2 September 2026. **Deadline: 5 September. Three days.** Scope is set accordingly.

Every claim below traces to a sourced brief in [`research/`](research/).

---

## 1. The problem, in one paragraph

An AI buyer cannot shop a Razorpay merchant today, because **Razorpay has no product catalog
API** — the Items API is an invoicing template with no images, variants, stock or search, and the
official MCP server's 40+ tools expose **zero** catalog or cart operations
([03](research/03-india-uap-razorpay.md)). And when an agent does buy and gets it wrong, the
**merchant of record eats the chargeback even when an authorized agent did exactly as instructed**
— there is **no agentic dispute reason code** at Visa or Mastercard, the device fingerprint belongs
to the agent's MCP server rather than the buyer, and the dispute-recovery industry's own assessment
is that *"mandate evidence is the real gap, and no tool captures it yet"*
([04](research/04-trust-fraud-liability.md)). Mastercard tells merchants they *"must prove not just
that the transaction was authorized, but that the agent acted within the consumer's delegated
authority"* — **and ships no mechanism to do it** ([06](research/06-protocols.md)).

## 2. The gap, stated precisely

Nine protocols were read at spec level ([06](research/06-protocols.md)). Every one answers two
questions and refuses a third:

| Question | Status |
|---|---|
| Is this agent who it claims to be? | **Answered** — converging on RFC 9421 / Web Bot Auth |
| Did a human authorize this, within what limits? | **Answered** — best by AP2's constraint vocabulary |
| **Will *this merchant* sell *this thing* to *this agent* on *these terms*?** | **UNANSWERED BY ALL NINE** |

**The invariant behind it: direction.** Every limit primitive in existence — AP2 `constraints`, ACP
`Allowance`, Visa `declineThreshold`, Mastercard `orderTotalAmount`, UPI Reserve Pay's block — is
authored **by or for the payer** and constrains **the agent**. **There is no field in any spec whose
author is the merchant and whose subject is the agent.**

Four protocols say so in normative prose. UCP: merchant allowlists belong in *"out-of-band
mechanisms"*. Visa: *"The Merchant may decide to block the message or use some other mechanism."*
Mastercard ships a trust table self-described as *"a recommendation table, not a schema"*. And UCP's
`request_constraints` — the only declarative rule grammar anywhere — **admits no `maximum`,
`minimum` or `pattern` keyword, so "agents may buy under ₹500" is structurally inexpressible.**

**Second uniform gap, worse than the first: revocation.** AP2 and x402 contain **zero occurrences**
of the word. ACP has expiry as its only kill switch. UCP offers key rotation and OAuth *session*
revocation, neither of which reaches a mandate. Web Bot Auth states outright *"It is not a
revocation mechanism."* Only **Visa VIC** and **UPI Reserve Pay** can kill a live authorization —
and the merchant holds neither.

## 3. Why this is not already built

From the adversarial competitor scan ([02](research/02-competitors.md)), which was tasked to
disprove the idea:

- **Catalog normalization is a commodity** — 12+ players, ~$80M+ funded; Google Merchant Center and
  Shopify give platform merchants one-click agent-readiness **for free**. → *So catalog is not the
  headline. It is included only because Razorpay genuinely lacks the primitive.*
- **"Protocol-agnostic" is taken** — Firmly Connect and Adyen Agentic say it louder. → *Dropped as a
  differentiator. Building UCP-only, justified below.*
- **Trust vendors emit a score, not a decision.** Ballerine sells governance **to PSPs**;
  HUMAN/Forter explicitly say their output is *"not a binary verify/reject"* — the merchant still
  writes the decision logic, with no tool to write it in.
- **Every catalog player has zero authorization features; every trust player has zero catalog
  features. Nobody has fused them.** A merchant-owned rules console was confirmed **absent from
  Firmly Connect's own page**.
- **India: nobody has shipped either half.** superU AI — the closest-sounding threat — is
  voice-intent-to-payment-link, not catalog or policy.

## 4. The build

> ## Warrant
> **The merchant's side of agentic commerce.**
> Makes a Razorpay merchant shoppable by an AI buyer, evaluates every agent order against rules the
> *merchant* wrote, and emits a signed receipt proving the agent acted within its delegated
> authority.

Five components. Door B (being shoppable) feeds Door A (selling more, safely) — one pipeline, not
two projects.

### 4.1 Catalog primitive — fills what Razorpay lacks
Ingest messy merchant data (CSV / Excel / JSON) → normalize → serve a **UCP-shaped** catalog:
`/.well-known/ucp` profile plus `POST /catalog/{search,lookup,product}` and the checkout-session
lifecycle.

**Why UCP and nothing else:** Shopify migrated onto it and killed Storefront MCP cart tools on
**31 Aug 2026**; the authors are an 11-member consortium including Stripe and Amazon; **AP2 merged
into it at the schema level** (AP2 = credential layer, UCP = commerce object layer); and ACP was
**demoted to a discovery protocol** in March 2026 when OpenAI handed checkout back to merchants
([05](research/05-market-data.md)). Backing one standard with a stated reason beats a shallow
adapter across four.

### 4.2 Policy engine — the missing schema, and the core of the project
A declarative merchant-authored rule set (YAML), expressing exactly what no protocol can:

```yaml
agent_policy:
  max_order_value: 5000            # INR
  deny_categories: [gift_card, clearance]
  max_units_per_sku: 3
  require_identity_tier: signed    # RFC 9421 verified, not bearer-token
  escalate_above: 2000
  per_agent_daily_cap: 25000
```

**Evaluation is deterministic. No LLM in the decision path.** This is a deliberate choice with
evidence behind it:
- **NIST:** agent task-hijacking success rises from **11% → 81%** once attacks are tailored to the
  target agent rather than drawn from generic baselines.
- **ComboShoppingBench:** *constraint accumulation* — per-criterion failure stays at 4.8–6.6% while
  **task-level success collapses as criteria multiply**.
- **StakeBench** (3,168 attacked runs on e-commerce objectives): *"no attack objective is reliably
  resisted by current LLM-based web agents."*

→ A model asked to respect bounds will violate them under adaptive pressure. **Bounds get evaluated
outside the model or they are not bounds.**

### 4.3 Agent identity — consume, never reimplement
Verify **RFC 9421 HTTP Message Signatures** with Web Bot Auth profile: fetch the JWKS from the
declared profile, match `keyid` to a `kid`, rebuild the signature base, check `created`/`expires`
freshness, cache nonces.

Cloudflare, Visa, Mastercard, Shopify and the IETF WG already own this layer — rebuilding it is how
you lose. **Worth surfacing in the pitch:** the profiles are **mutually incompatible** — `tag` is
`web-bot-auth` (IETF MUST) vs `agent-browser-auth`/`agent-payer-auth` (Visa) vs `Agent-pay-auth`
(Mastercard, capital A, case-sensitive); Visa signs only `("@authority" "@path")` while UCP requires
`@method` plus up to eight components; keys live at three different well-known paths; Ed25519 (IETF,
Visa) vs **ECDSA P-256** (Shopify). **One signature cannot satisfy Visa and Shopify simultaneously.**

### 4.4 Decision receipt — the dispute artifact nobody captures
Every agent order emits a **signed (Ed25519), human-readable** receipt containing:

1. Agent identity as a distinct non-human principal, cryptographically attested
2. The delegated authority presented (scope, limits, TTL) — captured **before execution**
3. **Every rule evaluated, with its verdict and the value that triggered it**
4. The cart **as executed**, hashed — *so an appended line item is detectable*
5. Timestamps and the final decision: `allow` / `block` / `escalate`

This is the conformance checklist synthesized from OWASP Top 10 for Agentic Applications (9 Dec
2025), NIST's four control areas, and AP2's dispute-evidence algorithm
([04 §6](research/04-trust-fraud-liability.md)). Directly reuses the **Proof Object** pattern from
Varinth.

### 4.5 Revocation — the gap nobody fills
A merchant-side kill switch that invalidates an agent's authority mid-flight, fails closed on the
next call, and records the revocation in the receipt chain. Since **UPI Reserve Pay is the only
primitive in the landscape whose limit is bank-enforced against a blocked balance** (`action:
"CANCEL"` releases unused funds), the design maps onto a real rail rather than an invented one.

## 5. Bounds come from Indian law, not from taste

The track asks for money actions that are *bounded and gated*. In India the bounds are **statutory,
with numbers** ([03](research/03-india-uap-razorpay.md)):

| Constraint | Value | Source |
|---|---|---|
| Reserve Pay block cap | **₹10,000** | NPCI OC-228, 8 Oct 2025 |
| Block validity | **90 days** | ” |
| Blocks per merchant per customer | **one** | ” |
| Failed-debit retries | **max 3 / 24h** | ” |
| Authentication | two factors, **one dynamic** | RBI Directions 2025 |
| E-mandate AFA-free ceiling | **₹15,000 / txn** | RBI e-mandate framework 2026 |

Demonstrating limits that a regulator already wrote is far stronger than demonstrating limits you
invented.

## 6. Where AI is used — and where it is deliberately not

The judging criterion is *"the right tool in the right place, **and where you chose not to use
one**."* Answer it explicitly:

| Component | AI? | Why |
|---|---|---|
| Catalog normalization from messy data | **Yes** — entity extraction, attribute inference, category mapping | Genuinely fuzzy: "Blue Tshirt L 499/-" → structured variant. LLM/GLiNER is correct here |
| **Natural-language → policy compiler** | **Yes** | Merchant types *"don't let agents buy gift cards, cap orders at ₹5k"* → compiles to the YAML DSL and **shows it for human approval before it takes effect** |
| **Policy evaluation** | **NO — deliberately** | NIST 11%→81%; constraint accumulation; StakeBench. A bound enforced by a prompt is not a bound |
| Receipt signing / identity verification | **NO** | Cryptography, not inference |
| Escalation summary for the merchant | **Yes** | Explaining *why* something was blocked, in plain language |

**AI authors the rules. Deterministic code enforces them.** That sentence is the project's thesis.

## 7. Demo: two real, documented failures handled gracefully

**Failure 1 — cart payload poisoning (the primary).** Palo Alto **Unit 42** documented, in
production telemetry, attackers injecting hidden instructions into aggregator sites that agents
crawl, causing **unauthorized gift cards to be appended to the CartMandate**, delivered to an
attacker-controlled address, **invisible to the user until the billing statement arrives**.
→ Agent presents *valid* authority. Cart contains an appended gift card. Warrant blocks on
`deny_categories: [gift_card]` and emits a receipt naming the offending line item and the rule.
*The harm was an extra line item in a payload no human inspected — exactly what the bar defends
against.*

**Failure 2 — revocation mid-session.** Merchant revokes the agent's authority while a checkout is
in flight; the next call fails closed; the receipt chain records the revocation and the reason.
*Fills the gap that AP2, ACP, x402 and Web Bot Auth all leave open.*

**Honest metrics, not one cherry-picked pass.** Run a batch (≥50 synthetic orders, mixed clean /
over-limit / poisoned / unsigned-agent) and report: allow / block / escalate counts, **plus the
false-positive cost** — legitimate orders wrongly blocked. Adobe measured retailers who blocked AI
crawlers losing **18% of referral traffic month-over-month**, and 62% of merchants estimate
false-positive costs at $1M+/yr — **over-blocking is the failure mode nobody demos.** Reporting it
is the differentiator.

## 8. Scope for three days

**Build:**
- Messy-input → UCP catalog, served with `/.well-known/ucp` + catalog + checkout-session endpoints
- Policy DSL + deterministic evaluator
- NL → policy compiler with human approval step
- RFC 9421 / Web Bot Auth signature verification
- Ed25519-signed decision receipts with full rule trace
- Merchant-side revocation, failing closed
- Razorpay **test-mode** order + payment link (REST or official MCP server, 40+ tools)
- Batch harness reporting honest metrics incl. false-positive cost
- Two failure demos above

**Deliberately cut — and say so in the pitch, because scoping is judgment:**
- Multi-protocol adapter across ACP/AP2/x402 → **UCP only**, for the reasons in §4.1
- x402 → no dispute model exists in it at all (zero occurrences of chargeback/refund/revocation);
  irrelevant to an Indian merchant
- **Live UAP integration** → the spec **does not exist publicly**; no NPCI circular, no RBI
  approval, and the Global Fintech Fest unveiling is **9–11 September, four days after this
  deadline**. Cited as *why now*, not built against. **Saying this out loud demonstrates having
  checked.**
- Real bank Reserve Pay flow → requires PSP/bank enablement; simulated against the documented
  statutory constraints, with the limits enforced for real in code
- Polished UI → a clean receipt view and a rules editor, nothing more

## 9. The form answers

**Project name:** Warrant

**What it solves:** *An AI buyer can't shop a Razorpay merchant — there's no catalog API. And when
an agent buys wrong, the merchant eats the chargeback with no evidence it acted within authority; no
agentic dispute reason code exists. Every protocol lets the buyer bound the agent. None lets the
merchant say what it will accept, or prove what it decided. Warrant is that missing half: a
UCP-shaped catalog so the merchant is shoppable, a deterministic policy engine enforcing rules the
merchant wrote, and a signed decision receipt that stands up in a dispute.*

**What broke, and how you got out** — *the field they say they read first.* Write it the day it
happens, from the real log. Strong candidates, all genuine:
- The **RFC 9421 profile incompatibility** — discovering one signature cannot satisfy both Visa's
  `("@authority" "@path")` + `agent-payer-auth` and UCP's nine-component + `web-bot-auth` profile,
  and choosing to verify one profile properly rather than three badly
- **UCP's `signing_keys` → `keys` rename** between `2026-04-08` and `2026-08-25`, with Google's own
  published example still emitting the old field — a spec-drift bug that only surfaces at runtime
- Discovering **AP2's `Item` is a four-field stub with no currency field**, so a mandate-signed cart
  signs a drastically reduced view — forcing the receipt to hash the full cart separately

Do **not** invent one. The log will supply it.

---

## Appendix: the numbers worth memorizing for the video

| Fact | Number |
|---|---|
| Consumers willing to let AI make the purchase decision (Gartner) | **11%** |
| Consumers who'd drop an agent after **one** mistake (ACI, UK) | **6 in 10** |
| Agent hijacking success: generic → adaptive attacks (NIST) | **11% → 81%** |
| Add-to-cart vs cheapest-offer-search success (WebMall) | **100% vs 63%** |
| AI-referred conversion vs organic, May 2026 (Adobe) | **+54% better** |
| …having been, March 2025 | **38–50% worse** |
| Shopify Catalog-served AI search vs scraped data | **converts 2×** |
| Merchants estimating $1M+/yr false-positive cost (Darwinium) | **62%** |
| Public production agent purchase-error rate | **does not exist** |
| Agentic chargeback reason codes at Visa/Mastercard | **zero** |
