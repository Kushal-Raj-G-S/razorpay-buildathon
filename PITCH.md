# Pitch: 5-minute video script + form answers

The form asks for a 5-min pitch video (unlisted is fine). Below is a script timed to ~4:40 spoken,
leaving slack. Every number in it traces to a sourced brief in [`research/`](research/).

**Delivery notes:** screen-record the demo, voice over it. Don't show your face unless you want to.
Don't read this verbatim — read it twice, then say it in your own words. Pauses are fine.

---

## Script

### [0:00–0:35] The hook — a fact, not a vision

> Razorpay has no product catalog API.
>
> I checked their docs and their official MCP server. The Items API is an invoicing template — name,
> amount, tax code. No images, no variants, no stock, no search. Their MCP server has forty-plus
> tools and not one of them touches a product or a cart.
>
> So an AI buyer can't shop a Razorpay merchant. Razorpay's rails can *collect* money from an agent
> beautifully. They expose nothing for an agent to shop *from*.
>
> That's half the problem. The other half is worse.

### [0:35–1:20] The real problem — nobody can prove what the agent was allowed to do

> When an agent buys the wrong thing, the merchant of record eats the chargeback — even when an
> authorized agent did exactly what it was told.
>
> There is no agentic dispute reason code at Visa or Mastercard. The device fingerprint belongs to
> the agent's server, not the buyer. The dispute-recovery industry's own summary is: *"mandate
> evidence is the real gap, and no tool captures it yet."*
>
> Mastercard tells merchants — and I'm quoting — you *"must prove not just that the transaction was
> authorized, but that the agent acted within the consumer's delegated authority."*
>
> And then ships no mechanism to do it.

### [1:20–2:05] Why this is unsolved — the direction invariant

> I read nine protocols at spec level. ACP, AP2, UCP, x402, Visa TAP, Mastercard Agent Pay, Web Bot
> Auth, Shopify's UCP profile, and India's UPI primitives.
>
> Every one of them answers two questions. Is this agent who it claims to be — solved, everyone's
> converging on HTTP Message Signatures. Did a human authorize this, and within what limits — solved,
> AP2 does it well.
>
> All nine refuse the third question: *will this merchant sell this thing, to this agent, on these
> terms?*
>
> Here's why. Every limit that exists in any spec — AP2's constraints, ACP's Allowance, Visa's
> decline threshold, Reserve Pay's block — is authored by or for the **buyer**, and constrains the
> **agent**. There is no field, in any specification, whose author is the merchant and whose subject
> is the agent.
>
> UCP is explicit: merchant access policy belongs in — quote — *"out-of-band mechanisms."* Its one
> rule grammar can't express a number. There's no `maximum` keyword. "Agents may buy under five
> hundred rupees" is literally inexpressible.

### [2:05–2:40] What I built

> So I built the missing half. It's called Warrant.
>
> It does four things. It turns a merchant's messy product data into a UCP-shaped catalog, so they're
> shoppable — filling the primitive Razorpay doesn't have. It evaluates every agent order against
> rules the *merchant* wrote. It emits a signed receipt proving what was decided and why. And it can
> revoke an agent's authority mid-flight — which AP2, ACP, x402 and Web Bot Auth all leave undefined.
>
> *[show the rules editor, then a receipt]*

### [2:40–3:20] The decision I most want you to push on

> The policy engine contains no LLM. That's deliberate, and it's the choice I'd defend hardest.
>
> NIST found agent hijacking succeeds eleven percent of the time with generic attacks — and
> eighty-one percent once the attack is tailored to the specific agent. ComboShoppingBench showed
> per-criterion failure staying under seven percent while whole-task success collapses as criteria
> multiply. StakeBench ran three thousand attacked shopping runs and found no attack objective
> reliably resisted.
>
> A bound enforced by a prompt is not a bound.
>
> So: AI *authors* the rules. The merchant types "don't let agents buy gift cards, cap orders at five
> thousand" — a model compiles that to a rule file, shows it for approval, and then deterministic
> code enforces it. AI where it's fuzzy. Never in the decision path.

### [3:20–4:10] The failure — real, documented, reproduced

> Palo Alto's Unit 42 found this in production traffic. Attackers hide instructions on
> deals-aggregator sites that shopping agents crawl. The agent builds the checkout payload, and
> unauthorized gift cards get **appended to the cart** — delivered to an attacker's address. Invisible
> to the buyer until the billing statement arrives.
>
> *[run it]*
>
> The agent's identity verifies. Its authority is valid. The cart is poisoned. Warrant blocks it on
> the merchant's own rule, and the receipt names the exact line item and the exact rule that caught it.
>
> *[show revocation demo briefly]*
>
> And here's the number nobody demos. Over a batch of fifty orders: this many allowed, blocked,
> escalated — and **this many legitimate orders I wrongly blocked.** Adobe measured retailers who
> blocked AI traffic losing eighteen percent of referral traffic in a month. Sixty-two percent of
> merchants put false positives above a million dollars a year. Over-blocking is the failure mode
> everyone hides. That's mine, measured.

### [4:10–4:40] Bounds from law, and what I didn't build

> One more thing. The limits here aren't invented. UPI Reserve Pay caps a block at ten thousand
> rupees, ninety days, one block per merchant, three retries in twenty-four hours. RBI requires two
> factors with one dynamic. Reserve Pay is the only primitive in this entire landscape whose limit is
> enforced by the payer's *bank* — everything else enforces limits in software held by whoever
> benefits from ignoring them.
>
> And what I didn't build: UAP. There's no published NPCI circular, no RBI approval, and the
> unveiling is at Global Fintech Fest on the ninth — four days after this deadline. It's why this
> matters. It's not something you can build against yet.
>
> Thanks.

---

## Form answers (12 fields)

**About you** — self-explanatory: full name, college (BMS Institute of Technology and Management),
graduation year (2027), in-person from September (your call), 6 or 12 months (your call), resume.

**Track:** 01 — AI Growth & Agentic Commerce

**Project name:** Warrant

**What it solves** (fits a short box):

> An AI buyer can't shop a Razorpay merchant — there's no catalog API; the Items API is an invoicing
> template and the official MCP server has zero catalog or cart tools. And when an agent buys wrong,
> the merchant of record eats the chargeback with no way to prove the agent stayed within its
> delegated authority — no agentic dispute reason code exists at either network.
>
> I read nine agentic-commerce protocols at spec level. Every one lets the *buyer* bound the agent.
> None lets the *merchant* declare what it will accept, or prove what it decided. There is no field
> in any spec whose author is the merchant and whose subject is the agent.
>
> Warrant is that missing half: a UCP-shaped catalog so a Razorpay merchant becomes shoppable, a
> deterministic policy engine enforcing rules the merchant wrote, signed decision receipts that hold
> up in a dispute, and merchant-side revocation — which AP2, ACP, x402 and Web Bot Auth all leave
> undefined. AI authors the rules; deterministic code enforces them, because NIST measured agent
> hijacking rising from 11% to 81% under tailored attacks and a bound enforced by a prompt is not a
> bound.

**GitHub repo URL:** https://github.com/Kushal-Raj-G-S/razorpay-buildathon
→ ⚠️ **must be flipped to public before submitting.** One command: `gh repo edit --visibility public`

**Pitch video:** unlisted YouTube link

**What broke, and how you got out** — *they say they read this first.*
Write it from the real log, the day it happens. Do not pre-write it. Candidates already visible in
the research, any of which will probably actually bite you:

- **The RFC 9421 profile incompatibility.** One signature cannot satisfy both Visa's
  `("@authority" "@path")` + `agent-payer-auth` profile and UCP's nine-component + `web-bot-auth`
  profile — different covered components, different tags, different key-discovery paths, Ed25519 vs
  ECDSA P-256. The way out is choosing to verify one profile correctly instead of three badly, and
  saying why.
- **UCP's `signing_keys` → `keys` rename** between the `2026-04-08` and `2026-08-25` releases, where
  Google's own published example still emits the old field name. A spec-drift bug that only appears
  at runtime.
- **AP2's `Item` is a four-field stub** — `id`, `title`, `price`, `image_url` — and `price` carries
  no currency, which lives on the enclosing checkout. So a mandate-signed cart signs a drastically
  reduced view of the cart, forcing the receipt to hash the full cart separately.

---

## Numbers to have in your head

| Fact | Number |
|---|---|
| Consumers willing to let AI make the purchase decision (Gartner) | **11%** |
| Would drop an agent after **one** mistake (ACI, UK) | **6 in 10** |
| Agent hijacking: generic → adaptive attacks (NIST) | **11% → 81%** |
| Add-to-cart vs cheapest-offer search (WebMall) | **100% vs 63%** |
| AI-referred conversion vs organic, May 2026 (Adobe) | **+54% better** |
| …the same measure in March 2025 | **38–50% worse** |
| Shopify Catalog-served AI search vs scraped data | **converts 2×** |
| Merchants estimating $1M+/yr false-positive cost | **62%** |
| Public production agent purchase-error rate | **doesn't exist** |
| Agentic chargeback reason codes at Visa/Mastercard | **zero** |
| Reserve Pay block cap / validity | **₹10,000 / 90 days** |
