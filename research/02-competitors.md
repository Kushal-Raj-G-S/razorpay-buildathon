# Competitor landscape — adversarial scan

Research brief, 2 September 2026. This agent was explicitly tasked to **try to prove our idea
is already taken**, so we don't walk into occupied ground.

## Verdict up front

**The original idea is largely taken.** Both halves ship today — from funded startups *and*
from Adyen, Google and Shopify.

- **Part (a)** — messy merchant data → multi-protocol agent-readable catalog — is the **most
  crowded space in agentic commerce right now**: ≥12 credible players, ~**$80M+ funded** in the
  last 15 months.
- **Part (b)** — merchant-side trust/authorization gate — is less crowded, but owned by
  well-capitalised fraud/risk incumbents plus one exact-fit startup.
- The **"protocol-agnostic across ACP+AP2+x402"** differentiation claim is **already the
  explicit marketing line of at least three players**, one of which is **Adyen**.

### Closest three competitors

1. **Firmly Connect** — protocol-agnostic merchant onboarding across UCP, ACP, AP2, TAP, MCP,
   KYA, no-code. *This is our pitch, live and funded* ($5.2M — FJ Labs, Ark, MC Start Path).
   https://www.firmly.ai/connect
2. **Adyen Agentic** (16 June 2026) — three-layer API: Agentic Feed + Agentic Cart + Agentic
   Payments across UCP/ACP/AP2, with cross-protocol coverage as the *stated* differentiator.
   https://www.digitalapplied.com/blog/adyen-agentic-commerce-integration-layer-2026-merchant-guide
3. **Octogen AI** — catalog standardization + enrichment, monitors how each AI agent interprets
   the catalog, "automatically maintains compatibility as platforms change", readiness score,
   zero feed export. https://www.octogen.ai/

---

## Player map

### (a) Catalog normalization / agent-readable feeds

| Player | What it actually ships | Overlap |
|---|---|---|
| [Firmly Connect](https://www.firmly.ai/connect) | No-code merchant onboarding; abstracts UCP/ACP/AP2/TAP/MCP; partial-catalog control, real-time inventory/pricing; merchant stays MoR. $5.2M | **Direct** |
| [Adyen Agentic](https://www.digitalapplied.com/blog/adyen-agentic-commerce-integration-layer-2026-merchant-guide) | Agentic Feed / Cart / Payments across UCP+ACP+AP2 | **Direct** |
| [Octogen AI](https://www.octogen.ai/) | Catalog standardization + enrichment + per-agent interpretation monitoring + auto-maintained compatibility | **Direct** |
| [Lemrock](https://www.eu-startups.com/2026/03/paris-based-lemrock-raises-e6-million-to-help-brands-sell-within-ai-agents-like-chatgpt-and-claude/) | Single access point to ChatGPT/Claude/Perplexity: catalog integration, real-time availability, transactions, analytics. 10M+ live products; Fnac Darty, Cdiscount, Maisons du Monde. €6M seed | **Direct** |
| [Channel3](https://siliconangle.com/2025/12/10/channel3-raises-6m-make-every-single-product-sold-web-discoverable-ai-agents/) | Multimodal product matching across retailers, attribute extraction, variant linking, schemas maintained as standards evolve. $6M seed | **Direct** |
| [Feedonomics ACE](https://www.commerce.com/press/feedonomics-unlocks-agentic-discovery-with-agentic-catalog-exports/) (27 Apr 2026) | Data transformation + enrichment + syndication to OpenAI, Gemini, Copilot, PayPal, Stripe, Perplexity, Amazon. Enterprise-only today; self-serve "planned" | **Direct** |
| Productsup / Salsify / Syndigo / Akeneo | OpenAI Connect channels, ACP-compliant feeds, MCP servers, GEO products ([tracker](https://www.productsup.com/agentic-commerce-tracker/)) | **Direct** (enterprise PIM tier) |
| [Google Merchant Center UCP](https://developers.google.com/merchant/ucp) | Simplified UCP onboarding (Mar 2026), UCP manifest centralised in GMC, feed becomes checkout-ready data layer + real-time Catalog capability | **Direct — and free** |
| [Shopify Agentic Storefronts](https://shopify.dev/docs/apps/build/storefront-mcp/servers/storefront) | One-click UCP enable from admin: auto-generates manifest, maps schema, broadcasts. Storefront MCP + Catalog MCP + Global Catalog feed | **Direct — and free** |
| ReFiBuy ($13.6M seed, [May 2026](https://retailtechinnovationhub.com/home/2026/5/5/agentic-commerce-specialist-refibuy-raises-136-million-seed-round-led-by-newroad-capital-partners)), Wildcard, Sitefire, Cernel, Netcore Unbxd, Swap Commerce, AgentPort, ShopAgentic (€1.9M) | Agentic commerce optimization / GEO / MCP-ification of catalogs | Direct → partial |

### (b) Trust / authorization / verification

| Player | What it actually ships | Overlap |
|---|---|---|
| [Ballerine](https://ballerine.com/agentic-commerce) (15 Jan 2026) | Trusted Agentic Commerce Governance: merchant eligibility evaluation, **agent-specific policy controls**, readiness profiles, continuous monitoring of catalog drift + behavioural anomalies, remediation workflows. **Sold to PSPs/PayFacs** | **Direct on part (b)** |
| [HUMAN AgenticTrust](https://www.humansecurity.com/newsroom/riskified-human-trusted-ai-shopping-agent-commerce/) | Identifies agent intent, validates agent identity, **enforces policies on what agents may do**; Riskified consumes signals for chargeback guarantee | **Direct** |
| Forter | Identity Monitoring for Agentic Commerce, Agentic Orchestration Suite, [VGS partnership](https://www.forter.com/blog/forter-and-vgs-expand-partnership-to-power-trusted-agentic-commerce/) | Direct |
| [Cloudflare Web Bot Auth / signed agents](https://blog.cloudflare.com/secure-agentic-commerce/) | Cryptographic HTTP-signature agent verification; surfaced in Bot Management + AI Audit; adopted into Mastercard Agent Pay and Amex | **Partial** — identity, not purchase policy |
| Visa TAP / Mastercard Agent Pay + Verifiable Intent | Agent authentication handled **processor-side** for merchants on Stripe/Adyen/Nuvei/Worldpay; Verifiable Intent creates auditable consent trail | **Partial → commoditizing** |
| [Stytch Agent Ready](https://stytch.com/ai-agent-ready) / [WorkOS](https://workos.com/blog/how-to-secure-agentic-commerce) | Per-agent tokens, custom scopes, RAR fine-grained mandates ("one flight SFO→JFK, ≤$500"), org allowlists | **Direct on the bounding primitive** |
| AP2 signed mandates | Rejects out-of-mandate spend before the processor. Protocol-level, **free** | Direct — at protocol layer |
| DataDome, Kasada, Akamai, Signifyd, Chargebacks911 | Bot/fraud detection adapted to agent traffic | Partial |

### (c) India

| Player | What it actually ships | Overlap |
|---|---|---|
| [Razorpay × superU AI](https://thepaypers.com/payments/news/razorpay-and-superu-ai-launch-agentic-payment-system) | **Not our idea.** Voice/conversational agent detects payment intent mid-dialogue → Razorpay auto-fires a payment link. No catalog normalization, no protocol adapter, no merchant authorization gate. Voice-commerce *collections* | **No / weak partial** |
| Razorpay / Cashfree / PayU | LLM-native UPI payments shipped Feb 2026 ([analysis](https://stellagent.ai/insights/india-agentic-commerce-fintech-payment)) | Partial (payments only) |
| Shiprocket (SHIVIR 2026), Unicommerce, Flipkart/BigBasket AI storefronts | Positioning + AI storefronts; enablement narrative, no published multi-protocol adapter | Partial / no |
| [PadUp Ventures × Unicity Labs](https://stellagent.ai/insights/india-agentic-commerce-fintech-payment) | Agentic commerce infra accelerator for Indian startups | No (funder) |

> **superU was the feared threat and isn't one** — it's voice-AI-to-payment-link. The real India
> finding: **nobody in India has shipped catalog normalization or a protocol adapter.**

---

## Already solved — do NOT rebuild

- **Multi-protocol adapter (ACP/UCP/AP2/TAP/MCP)** — Firmly Connect, Adyen Agentic, Spreedly.
  "Connect once, stay current" is verbatim their line.
- **Catalog → agent-readable schema** — Feedonomics ACE, Octogen, Channel3, Lemrock,
  Productsup, Syndigo, Salsify.
- **One-click agent-readiness for platform merchants** — Google Merchant Center + Shopify admin,
  **free**. Any Shopify/GMC merchant is a non-customer.
- **Agent identity verification** — Cloudflare Web Bot Auth, now inside Visa TAP / Mastercard
  Agent Pay / Amex, and handled processor-side by Stripe/Adyen/Worldpay/Nuvei.
- **Mandate / spend bounding** — AP2 signed mandates (free, protocol-level), Stytch/WorkOS RAR
  scopes, Nekuda Agentic Mandates SDK, virtual-card MCC/limit locks (Lithic, Marqeta).
- **Agent trust scoring for merchants** — HUMAN AgenticTrust + Riskified, Forter.

## Genuine white space

1. **Merchant-side policy authoring, not PSP-side.** Ballerine sells governance *to PSPs*;
   HUMAN/Forter emit a *trust score* and explicitly say it is "not a binary verify/reject" — the
   merchant still writes the decision logic. **There is no merchant-owned rules console**
   ("agents may buy ≤₹5k, not clearance SKUs, not gift cards, not >3 units, escalate above X").
   Confirmed absent from Firmly Connect's own page.
2. **Protocol-agnostic + trust fused in one product.** Every catalog player has **zero**
   authorization features; every trust player has **zero** catalog features. Nobody has fused
   them — **the one unclaimed seam**.
3. **Explainability / dispute-defensible reasoning.** Consensus-unsolved: [no clear liability
   standard](https://www.chargeflow.io/blog/agentic-commerce-regulation-what-merchants-need-to-know);
   the new failure mode "**the agent bought the wrong thing**" fits **no existing chargeback
   reason code**; merchants need a record of *what was authorized vs. what actually happened*.
   AP2 mandates and Mastercard Verifiable Intent cover **consent**, not **merchant-side rule
   evaluation explanation**.
4. **Long-tail / non-platform, non-English merchants.** Every solved path assumes Shopify admin,
   GMC, or an enterprise PIM contract. Feedonomics ACE is enterprise-only, self-serve merely
   "planned". Truly messy data (**WhatsApp catalogs, Excel, WooCommerce, regional
   marketplaces**) is unserved — and **completely unserved in India**.
5. **Protocol-drift regression testing.** Only Octogen claims per-agent interpretation
   monitoring. Nobody offers "your catalog broke under UCP v-next" as a contract.

## Funding signal — where investors think the gap is

Money is concentrated in **payments/identity** (Basis Theory $33M B; Skyfire $9.5M; Nekuda $5M)
and **merchant optimization/discovery** (FERMÀT $45M B; ReFiBuy $13.6M seed; Rye $14M), with a
fresh **catalog-middleware seed wave** (Lemrock €6M, Channel3 $6M, New Generation $4.5M,
ShopAgentic €1.9M).

Notably [Rye's own landscape](https://rye.com/blog/agentic-commerce-startups) flags **checkout
execution** as the underfunded layer — *not* catalog. Read: investors already funded part (a) at
seed and consider it contested.

---

## Recommendation carried forward

**Drop** "agent-readable catalog" as the headline — commodity, two free incumbents.
**Drop** "protocol-agnostic" as the differentiator — Firmly and Adyen say it louder.

**Keep** white-space **#1 + #3 fused**: a **merchant-owned policy engine** that evaluates each
agent order against merchant-authored bounds and emits a **signed, human-readable decision
receipt usable in a dispute**.

- **Consume** Web Bot Auth / AP2 mandates / AgenticTrust-style scores as *inputs* rather than
  reimplementing them.
- **Target** long-tail, non-Shopify, non-English **Indian** merchants, where nobody has shipped
  anything.

This maps cleanly onto the track's bar — *every money action explainable, bounded and gated;
show the audit trail* — and onto prior work (Varinth's Proof Objects and Critic–Verifier–Judge
verdict synthesis are the same primitive as a signed decision receipt).

Further sources: [ACP/UCP provider directory](https://www.acpready.com/)
