# Initial landscape scan — protocols, players, gaps

First-pass research, 2 September 2026. Every claim carries a source.
Deeper evidence briefs (market data, India/UAP, protocol specs, competitors, trust/fraud)
land in subsequent files in this folder.

---

## 1. The protocol race (the "rails")

### AP2 — Agent Payments Protocol (Google)
- Announced **16 September 2025** with **60+ launch partners** incl. Mastercard, PayPal,
  Coinbase, American Express, Salesforce.
- Core abstraction: the **Mandate** — a digitally signed statement from the consumer defining
  exactly what the agent may spend, on what, with what limits, for how long.
  > ⚠️ **CORRECTED by [06-protocols.md](06-protocols.md):** the mandate types recorded here
  > ("Intent / Cart / Payment") are **stale**. The shipped SDK has `CheckoutMandate` /
  > `OpenCheckoutMandate` / `PaymentMandate` / `OpenPaymentMandate`; **`IntentMandate` no longer
  > exists**. Mandates are **SD-JWT VCs (RFC 9901)**, not W3C VC-JSON-LD. Also: **AP2 and UCP have
  > merged at the schema level** — AP2 is the credential layer, UCP the commerce object layer.
- The mandate **travels with the transaction**, so networks and merchants can verify the agent
  had real authorization rather than merely possessing credentials.
- **Payment-method agnostic** — extension points for card networks, ACH/bank transfer,
  real-time rails (FedNow, **UPI**, Pix), and stablecoins.
- **Governance shift:** Google is **donating AP2 to the FIDO Alliance** to keep it
  platform-agnostic and community-led.
- By **Q1 2026**: 60+ partner orgs, with **Adyen and Worldpay** endorsing; commercial pilots
  running on payment networks.

Sources: https://cloud.google.com/blog/products/ai-machine-learning/announcing-agents-to-payments-ap2-protocol · https://ap2-protocol.org/ · https://blog.google/products-and-platforms/platforms/google-pay/agent-payments-protocol-fido-alliance/ · https://www.everestgrp.com/googles-agent-payments-protocol-ap2-a-new-chapter-in-agentic-commerce-blog/

### ACP — Agentic Commerce Protocol (OpenAI + Stripe, + Meta)
- Open standard maintained by **OpenAI and Stripe**; defines how agents interact with
  businesses to complete purchases for a buyer.
- Building blocks: **agentic checkout** (cart management, fulfillment options, payment),
  **cart and feed** (catalog browsing), **secure payment token delegation**.
  > ⚠️ **CORRECTED by [06-protocols.md](06-protocols.md):** **there is no OAuth 2.0 in the released
  > ACP spec** — `delegate_authentication` is *"3D Secure 2 (3DS2) authentication only"*. Stripe's
  > marketing page claims OAuth; the spec does not contain it. The scoping object is named
  > **`Allowance`**, not "shared payment token". And ACP was **demoted to a discovery protocol** in
  > March 2026 — see [05-market-data.md](05-market-data.md).
- **Already live in production**: powers **Instant Checkout in ChatGPT** — US users buying
  from US **Etsy** sellers and **1M+ Shopify** merchants (Glossier, Vuori, Spanx, SKIMS).
- Payment mechanism: **Shared Payment Token (SPT)** — lets ChatGPT initiate payment without
  exposing buyer credentials; **scoped to a specific merchant and cart total**.
- Existing Stripe merchants can enable agentic payments in **~one line of code**.
- **Salesforce announced support** (14 Oct 2025).
- Adoptable even by non-Stripe merchants — Stripe's is just the first reference impl.

Sources: https://docs.stripe.com/agentic-commerce/acp · https://github.com/agentic-commerce-protocol/agentic-commerce-protocol · https://openai.com/index/buy-it-in-chatgpt/ · https://stripe.com/newsroom/news/stripe-openai-instant-checkout · https://www.salesforce.com/news/press-releases/2025/10/14/stripe-openai-agentic-commerce-protocol-announcement/

### x402 (Coinbase)
- Whitepaper released **6 May 2025** by Coinbase Developer Platform.
- Uses the **HTTP 402 Payment Required** status code: agent requests a paid resource → server
  returns 402 with payment instructions → agent signs a **stablecoin (USDC)** transaction,
  attaches proof, retries → server verifies and serves. Cycle takes **seconds, no login**,
  settles onchain.
- **x402 Foundation** launched by Coinbase + Cloudflare; core members now include **Google,
  Visa, AWS, Circle, Anthropic, Vercel**.
- Use cases: pay-per-call API access, metered data feeds, per-call AI inference, and
  **agent-to-agent commerce** (one agent buying another's output, settled in USDC).
- Also has a **Google AP2 + x402 joint integration** ("agents can now actually pay each other").

Sources: https://www.coinbase.com/developer-platform/discover/launches/x402 · https://www.coinbase.com/developer-platform/discover/launches/google_x402 · https://www.allium.so/blog/x402-explained-the-internet-native-payments-standard-for-apis-data-and-agent-commerce/ · https://solana.com/x402/what-is-x402

### UAP — Unified Agent Protocol (NPCI, India) ← **the one the track name-drops**
- NPCI-led framework to let **AI agents transact over UPI** on a user's behalf **without
  altering existing payments infrastructure**.
- Authenticates and authorises AI agents, defines transaction permissions, preserves UPI
  interoperability.
- Key technical mechanism: **one-time, consent-based authentication set up in advance, with
  per-merchant spending limits**, letting an agent transact **without entering a PIN or OTP
  each time**.
- Expected unveiling at **Global Fintech Fest, Mumbai**; **requires RBI approval before
  launch**.
- First use cases: **low-value, frequent purchases** such as groceries.
- Would place India among the first countries with **national infrastructure for agentic
  payments**.

Sources: https://www.business-standard.com/finance/news/india-may-allow-agentic-ai-led-upi-transactions-under-new-npci-protocol-126070801343_1.html · https://www.outlookbusiness.com/news/india-plans-ai-powered-upi-payments-framework-through-unified-agent-protocol · https://www.brecorder.com/news/40437409/india-preparing-rollout-of-agentic-payments-on-upi-sources-say · https://stellagent.ai/insights/india-npci-unified-agent-protocol-upi

### Card networks
- **Mastercard Agent Pay** — network-level framework on **Agentic Tokens** + **Verifiable
  Intent** artifacts proving the agent acted within user-granted authority. Citi and US Bank
  cardholders in pilot **Sept 2025**; rollout completed to **all US Mastercard cardholders by
  Nov 2025**. Optimised for **minimal merchant integration lift**.
- **Visa Intelligent Commerce** + **Trusted Agent Protocol (TAP)** — defines how agents
  **identify themselves to merchants** and how merchants **verify** them. Uses
  **per-transaction signed intents** — each purchase carries a fresh, scoped mandate signed by
  the cardholder/wallet. Favours **discrete, higher-value purchases** with tighter control.
  Introduces new acceptance surface but richer agent metadata.
- **PayPal Agent Toolkit** — in Q4 2025 integrated with **ChatGPT, Perplexity and Mastercard
  Agent Pay simultaneously**, positioning as the payment layer *regardless of which AI
  platform wins*.

Sources: https://risingwave.com/blog/mastercard-agent-pay-vs-visa-vs-stripe-agentic-commerce/ · https://eco.com/support/en/articles/15192003-mastercard-agent-pay-vs-visa-trusted-agent-2026-compared · https://www.pymnts.com/news/artificial-intelligence/2025/visa-mastercard-paypal-fuel-agentic-ai-commerce-boom/ · https://www.emarketer.com/content/agentic-ai-hype-builds-visa-affirm-paypal-launches

---

## 2. What Razorpay itself has already shipped ⚠️ (critical for scoping)

- **Agentic payments pilot with NPCI on Anthropic's Claude** — announced at the **India AI
  Impact Summit, 20 February 2026**. Users order food/groceries/essentials from **Zomato,
  Swiggy, Zepto** without leaving the Claude conversation. Covers **discovery → checkout in a
  single conversational exchange**, removing app-switching and repeated payment approvals.
  Currently **pilot phase, select users**.
- **Razorpay Agent Studio** — launched at **FTX'26**, billed as the *world's first AI-native
  Agent Studio for payments*, **built on Anthropic's Claude Agent SDK**. A **B2B agent
  marketplace + builder platform** for payments and business banking.
  - **No-code agent builder** — describe the task in plain English, select systems to access.
  - Integrations: **Shopify, WhatsApp, Shiprocket, Slack, QuickBooks** and more.
  - **Pre-built agents already shipping: dispute management, cart recovery, subscription
    retry, cashflow forecasting, RTO reduction.**
- **Agentic Integration** — AI-native way for partners/merchants/devs to integrate Razorpay
  in **under 10 minutes**, working across **Claude Code**, Replit, Emergent.
- **Razorpay Agentic Experience Platform** — also built on the Claude Agent SDK.
- Other pilots: **Sarvam AI** (Indus app, agent-powered payments, Mar 2026), **superU AI**
  agentic payment system.
- Note: independent coverage has raised **dark-pattern and price-discrimination questions**
  about Agent Studio — worth knowing, since "explainable and gated" is the track's bar.

Sources: https://razorpay.com/newsroom/razorpay-launches-the-worlds-first-ai-native-agent-studio-for-payments-at-ftx26-powered-by-anthropics-claude/ · https://razorpay.com/blog/agentic-payments-and-npci/ · https://thepaypers.com/payments/news/razorpay-and-npci-launch-agentic-payments-on-claude · https://thepaypers.com/payments/news/razorpay-launches-ai-agent-studio-and-agentic-experience-platform · https://razorpay.com/agentic-payments/ · https://www.medianama.com/2026/03/223-razorpay-sarvam-ai-ai-agent-payments-indus-app/ · https://www.medianama.com/2026/03/223-razorpay-launches-ai-agent-studio-questions-loom-dark-patterns-price-discrimination/ · https://www.superu.ai/blogs/agentic-commerce-stack-superu-ai-razorpay-integration

**Implication:** Tracks 03/04 (cart recovery, subscription retry, disputes, forecasting) are
*already Razorpay products*. Building there competes with their own shipping stack. Track 01's
catalog/AI-buyer-readiness/trust surface is the least occupied.

---

## 3. Where the market is actually stuck (the gap)

### Trust is the #1 barrier — ahead of every technical concern
- **61.5%** of consumers have used AI for **product discovery**, yet **55.0%** are **not
  comfortable letting AI agents buy on their behalf**, and **50.8%** assign responsibility for
  unauthorized purchases to the **AI platform** (not themselves).
- Trust was identified as the **number-one barrier** to agentic commerce deployment, ahead of
  all technical concerns.

### Merchants are adopting faster than they can safely manage
- **3 in 4 merchants** are integrating or about to integrate agentic protocols: **44% already
  integrating**, a further **32% within six months**.
- Enterprise merchants are racing in "at unprecedented speed… faster than they can safely
  manage."

### Agent impersonation is already happening at scale
- **PerplexityBot: 2.4% impersonation rate.**
- **Meta-ExternalAgent: 16M+ spoofed requests in the first two months of 2026 alone.**

### The risk decomposes into four buckets
1. **Authorization** — did the user actually approve?
2. **Identity** — is this a real agent or a scraper?
3. **Fraud** — who owns the chargeback?
4. **Merchant discovery** — algorithmic ranking can collapse organic channels.

### Over-blocking is expensive
- **62% of merchants estimate false-positive costs at $1M+ annually.** The bind: "block too
  much and lose revenue, or allow too much and absorb fraud risk."

### Forward risk
- A **2026 World Economic Forum Annual Meeting** estimate: by **2028, 1 in 4 data breaches**
  could result from **AI agent exploitation**.

Sources: https://www.darwinium.com/navigating-agentic-commerce-2026-report · https://nhimg.org/articles/ai-shopping-agents-expose-a-trust-gap-in-autonomous-commerce/ · https://nhimg.org/community/identity-beyond-iam/agentic-commerce-trust-gap-what-merchants-and-iam-teams-need-to-know/ · https://www.ravelin.com/blog/the-agentic-commerce-gold-rush-risk · https://datadome.co/agent-trust-management/the-rise-of-agentic-fraud/ · https://unit42.paloaltonetworks.com/retail-fraud-agentic-ai/ · https://eco.com/support/en/articles/14839400-what-is-agentic-commerce-the-2026-guide

> ⚠️ Caveat: several of these figures come from **fraud-prevention vendors** (Darwinium,
> Ravelin, DataDome) who sell into this fear. Treat as directional; independent verification
> tracked in the trust/fraud deep-dive brief.

### Protocol fragmentation
AP2 (mandates) vs ACP (SPT + feed) vs x402 (HTTP 402 + USDC) vs UAP (UPI consent + per-merchant
caps) vs Visa TAP vs Mastercard Agentic Tokens are all **different shapes**. A small Indian
merchant has **no single cheap path to being "agent-ready" across all of them**. Big brands get
white-glove ACP/Shopify integration; **the long tail does not**.

---

## 4. Working hypothesis for the build

> Merchants shouldn't have to bet on a winning protocol. A **trust-and-catalog layer** that
> makes any merchant instantly agent-ready **across protocols**, where **every agent action is
> independently auditable**.

Pipeline: messy merchant product data → **normalized agent-readable catalog** (protocol-agnostic)
→ wrapped in a **signed, scoped authorization gate** (bounded spend, scoped SKUs, TTL) →
**conversational growth/upsell/checkout agent** that can *only* act through that gate → every
action emits an auditable proof object.

Direct transfer from prior work: Varinth's Proof Objects / Critic–Verifier–Judge verification
swarm, Roast's self-evaluating trust layer, Baxel's hierarchical multi-agent + structured
generation.

**Open questions to resolve before committing** (tracked in later briefs):
1. Does Razorpay's test-mode API even expose a **product/catalog** primitive? If not, what is
   the closest surface (orders / payment links / invoices / subscriptions)?
2. Is a **lossless** multi-protocol catalog+mandate translation actually feasible, or does it
   break at the auth model?
3. Is the multi-protocol adapter angle **already occupied** (Cloudflare, superU AI, Stripe,
   feed/PIM vendors)?
4. What **RBI constraints** bound an agent-initiated UPI payment demo?
5. What **documented failure incident** should the "one failure handled gracefully" demo
   reproduce?
