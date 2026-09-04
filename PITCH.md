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

> So I built the missing half. It's called Nope.ai.
>
> It does four things. It turns a merchant's messy product data — pasted text, or their real
> price-list PDF — into a UCP-shaped catalog, so they're shoppable, filling the primitive Razorpay
> doesn't have. It evaluates every agent order against rules the *merchant* wrote. It emits a signed
> receipt proving what was decided and why. And it can revoke an agent's authority mid-flight — which
> AP2, ACP, x402 and Web Bot Auth all leave undefined.
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
> The agent's identity verifies. Its authority is valid. The cart is poisoned. Nope.ai blocks it on
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

**Project name:** Nope.ai

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
> Nope.ai is that missing half: a UCP-shaped catalog so a Razorpay merchant becomes shoppable, a
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

---

## Feature log — everything built after this script was written

The script and form answers above were written early (commit `cfa5fac`) and describe four
things: catalog cleanup, rule evaluation, signed receipts, revocation. A lot has been built
since. This section exists so neither of us has to remember it from scratch when the
script gets refreshed — pull from here, don't re-derive it. Keep this updated as things
land; it's a reference list, not something to read aloud.

### Unique, differentiating features (in build order)

- **MCP server** (`b895e75`) — the whole decision engine exposed as MCP tools, the same
  protocol Razorpay's own Agent Studio (Claude Agent SDK) uses to call tools. The actual
  integration path, not just a REST API.
- **Red-team** (`203a515`, extended `0aa592e`) — a merchant can send a real autonomous AI
  at their own rules and get back a full, unscripted transcript of what it tried and why it
  failed. Every run persisted; past runs browsable and expandable in the UI, not just the
  one you just triggered.
- **Digest** (`18ae2e2`, extended `0aa592e`) — a per-agent footprint (attempts, blocked,
  which rule caught them, first/last seen) and a small set of deterministic flags (catalog
  mismatch, velocity cap hit, repeated blocks) — all fixed code, zero AI, same rule as
  checkout itself. AI only narrates already-decided flags in plain language, in a separate
  call so real numbers render before the slow AI step finishes. Every flag has a Revoke
  button right there — awareness with an action next to it, not a dead-end warning.
- **Escalation Advisor** (`fdd4f88`) — AI drafts an approve/reject recommendation with a
  confidence level for a human reviewing a large order; never decides anything itself. A
  Reviewed tab (`f5dad40`) shows every past approve/reject decision with note and timestamp
  — previously invisible the moment you acted on it.
- **Policy version history** (`595d31c`) — every save snapshotted, browsable in a sidebar,
  reloadable into the form — never auto-applied, still goes through the same
  review-then-Save path as any other change.
- **Razorpay-key auth** (`b0d3b60`) — a merchant's own real Razorpay test-mode keys become
  their Nope.ai credential directly, verified with a real live call to Razorpay, not a
  format check. No second, Nope.ai-only credential is ever minted.
- **Typed, self-describing API — now every endpoint** (`cc4be35` started it with the four
  most Digest-adjacent routes, a follow-up commit finished the rest: catalog, policy,
  checkout, receipts, escalations, revocation, red-team, merchant registration, UCP
  discovery). `/docs` and `/openapi.json` describe every route's real shape now, not "some
  JSON object" — checkable directly against `/openapi.json`, zero routes left untyped. This
  is the argument that the Next.js dashboard is a reference implementation, not the product.
- **COD governance + velocity limiting** (`afc9694`) — the India-specific gap no protocol
  (AP2, ACP, UCP, even UPI Reserve Pay) covers: agentic Cash on Delivery needs zero payment
  authorization, and order *frequency* matters as much as order size.
- **Docker, verified twice for real** (`fdd4f88`/`adca20e`, `2992606`) — one-command boot of
  both services, containers actually built and run (not just written), including a restart
  to prove SQLite data survives.
- **Catalog from a real PDF, plus a scraper that feeds it** (`369a432`, `d469969`) — a merchant
  can upload their actual price-list PDF instead of retyping it (`pypdf` extraction, same AI
  normalization as pasted text). Deliberately did *not* let a merchant paste an arbitrary URL for
  the backend to fetch — that's a live SSRF vector at request time. Instead built
  `scripts/scrape_shop_to_pdf.py`, an operator-run tool: point it at a real shop's product page,
  it scrapes the listing and writes a PDF, which then goes through the exact same
  `/catalog/from-pdf` upload path. Verified live end-to-end against a real site
  (books.toscrape.com), 20 real products scraped, normalized, and saved with correct rupee
  conversion.
- **Typeable category picker + allow-listing** (`4aa89d4`, `3bdb2c2`) — categories in the policy
  editor are a real combobox sourced from the merchant's own catalog data, not free text. Added
  `allow_categories` alongside the existing `deny_categories` — Amazon can't deny-list every
  category it *doesn't* sell, so a whitelist mode exists for merchants with catalogs too big to
  ban item-by-item. Client-side validation blocks saving a category into both lists at once; both
  lists empty is left as a valid, unrestricted state on purpose.
- **Speak your rules instead of typing them** (`4aa89d4`, dedup fix `369a432`) — Web Speech API in
  the rules editor, no backend involvement. Found and fixed live: continuous-mode speech
  recognition re-sends already-finalized phrases on every result event, causing visible text
  duplication after a pause; fixed with `resultIndex`-based incremental extraction.

### Real bugs found and fixed — this is itself pitch material

Evidence that "tested hard" isn't a claim, it's a log. Worth a line in the pitch precisely
*because* they were found, not despite it:

- **Catalog category-spoofing** (`203a515`) — an agent could relabel a real item's category
  to dodge `deny_categories`; closed by resolving every item against the merchant's real
  catalog before any rule runs, unconditionally blocking anything that doesn't match.
- **Negative-quantity exploit** (`68407b1`) — a negative cart quantity produced a negative
  total that trivially passed every value-based rule.
- **Escalation double-approval** (`68407b1`) — double-clicking Approve could create two real
  Razorpay payment links for one order.
- **Payment-committed-before-Razorpay-succeeded ordering bug** (`fdd4f88`) — a failed
  Razorpay call used to leave an escalation permanently stuck "approved" with no payment and
  no way to retry.
- **Revoke silently no-op'd for any never-registered agent** (`0aa592e`) — the button said
  "revoked" and returned 200 OK; the agent could still check out immediately afterward.
- **Policy AI-drafter silently dropped COD and velocity instructions** (`da88d08`) — schema
  and prompt drifted apart after India-specific fields were added; now guarded by a static
  test that fails if it happens again.
- **Approving an escalation during a Razorpay rate-limit returned a bare 500** (found while
  typing every endpoint's response, fixed same day) — `create_payment_link`'s
  `raise_for_status()` wasn't caught anywhere. Now a typed 503 naming the escalation as
  untouched and safe to retry. Verified against a genuine live 429, not just a mock — the
  test account was still rate-limited from earlier same-day testing when this landed.
- **The same bare-500 bug existed in the main checkout endpoint too** — found immediately
  after fixing the escalation case, by actually running the flagship "clean cart → ALLOW"
  flow end to end against a genuinely fresh clone of the public repo, with Razorpay still
  really rate-limited. Fixed to degrade gracefully instead: the receipt is already signed
  and saved by the time payment is attempted, so a Razorpay failure now returns 200 with the
  real receipt, `payment` omitted, and an honest note — not an error hiding a decision that
  already happened.
- **Two of the Digest's own flag wordings were wrong, caught by Kushal actually reading
  them, not by testing** — `catalog_mismatch` asserted "the exact pattern of an agent trying
  to disguise what it's actually buying" as fact, when an unlisted item id is equally
  explained by a stale product reference or a bug in the agent; fixed to name both
  possibilities and stop there. `repeated_blocks` said "blocked N times" with no indication
  of what rule was actually broken, even though that data (`blocked_rules`) was already being
  computed right next to it; fixed to name the specific rule(s). Also surfaced, same
  conversation: on real demo history `Allowed` sat at 0 in every window — nothing on screen
  proved the system ever let a legitimate purchase through, only that it blocks things. Fixed
  by actually running one real, correctly-signed checkout end to end (`real-shopper-agent`)
  rather than by changing the display logic.
- **The AI escalation advisor produced a false "reject — looks like fraud" on a completely
  ordinary order** — `advise_on_escalation` embedded item prices still in paise right next
  to an order total already converted to rupees, so a Rs 5,000 order's item showed as
  `"price": 500000` beside `"Order total: Rs 5000"`. Caught live: a real NVIDIA call
  actually returned "reject, high confidence... looks like a fraud attempt" citing that
  fabricated mismatch. This is the sharpest one to have ready — it's a real instance of AI
  advice being confidently wrong for a boring, structural reason (a units bug), which is
  exactly the class of failure the whole "no AI in the decision path" argument is about. The
  human still has to click Approve/Reject either way, so no money was ever at risk from
  this one — but a merchant trusting a "high confidence" AI recommendation without checking
  would have wrongly rejected a real customer.
- **Escalations only ever showed pending orders — approve or reject one and it vanished
  with no record anywhere in the app.** The original receipt still just says "escalate"
  forever; reviewing one never touches it. A Reviewed tab now shows every past decision.

Every one of these was found by actually trying to break the thing, not by reading the code
and assuming it worked — several were found live, in a running browser, not in a test file.
