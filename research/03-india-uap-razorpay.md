# India: UAP, RBI constraints, Razorpay surface, merchant pain

Research brief, 2 September 2026.

**Reliability legend:** 🟢 primary/official · 🟡 credible press · 🟠 vendor marketing ·
🔴 SEO/low-confidence — treat as uniteable

---

## 1. NPCI Unified Agent Protocol (UAP)

### ⚠️ UAP does not publicly exist yet

- **No NPCI circular or spec for UAP exists on npci.org.in.** The circulars index was searched
  directly — nothing. 🟢 (negative finding) https://www.npci.org.in/circulars/upi
- Every account of UAP traces to **press reporting from unnamed sources**.
- **Unveiling expected at Global Fintech Fest 2026, Mumbai, 9–11 September 2026** — i.e. **four
  days AFTER the buildathon deadline of 5 Sept.** Reuters, 1 Sept 2026. 🟡
  https://www.thestar.com.my/tech/tech-news/2026/09/01/india-preparing-rollout-of-agentic-payments-on-upi-sources-say
- **RBI approval NOT obtained.** Launch "is likely to require a regulatory nod from RBI." NPCI
  declined to comment to Reuters. 🟡
- **Banks/PSPs in pilot: no data found. GA timeline: no data found.**

> **Design consequence:** you cannot build against a UAP spec — it isn't published. Cite it as
> the *why now*, but build on the primitives that actually exist today (below). Saying this out
> loud in the pitch is itself a signal of judgment.

### Architecture as reported
UAP adds **no new rails**. It is a registration/authentication/authorisation layer for AI agents
riding **existing UPI Circle (delegation) + UPI Reserve Pay (fund blocking)**. Stated goals:
agent identity verification, transaction permissions, spending limits, **audit trails**,
preserved interoperability, and NPCI validating payment genuineness *without* visibility into
purchase contents. 🟡 https://www.outlookbusiness.com/news/india-plans-ai-powered-upi-payments-framework-through-unified-agent-protocol

Consent model = **"rule-based instructions"**: user sets rules for when and how much the agent
may pay; one-time authorisation, then no per-transaction PIN. First use cases: low-value,
high-frequency — groceries, dairy, daily essentials; **q-commerce** the early beneficiary.

NPCI has been at this since **GFF 2025**, where it demoed an agentic UPI framework branded
"intelligent commerce". 🟡 https://inc42.com/buzz/npci-to-launch-agentic-payments-on-upi-report/

### 🔑 The one hard spec that exists today: UPI Reserve Pay

This is the real substrate under **both** Razorpay's Claude pilot and Pine Labs' P3P.

**Circular NPCI/UPI/OC-228/2025-26, dated 8 October 2025** — "Enhancement in UPI Single Block
Multiple Debits (UPI Reserve Pay)". 🟢
https://www.npci.org.in/uploads/UPI_OC_No_228_FY_2025_26_Enhancement_in_UPI_Single_Block_Multiple_Debits_UPI_Reserve_Pay_a9095c181d.pdf
(npci.org.in blocks automated fetch — open in browser. Contents extracted via 🟡
https://complinity.com/legal-update/npci-issues-enhancements-in-upi-single-block-multiple-debits-upi-reserve-pay--20722/)

| Constraint | Value |
|---|---|
| Block cap | **₹10,000** |
| Validity | up to **90 days** |
| Blocks per merchant per customer | **one** |
| Funding sources | savings, current, overdraft, RuPay credit card, pre-sanctioned credit line |
| Merchant eligibility | initially **verified online merchants, low-ticket high-frequency** only |
| Failed-debit retries | **max 3 in 24 hours**; only successful debits count as payment |

Reuters confirms banks cap Reserve Pay at ₹10,000/90 days and that **"this limit and its
validity may be revisited for agentic use"** — treat ₹10,000 as current but movable. 🟡

### UPI Circle (delegation primitive)
- **Full delegation:** monthly cap up to **₹15,000**; **per-payment cap ₹5,000**; max **5
  secondary users** per primary. 🟡 https://paytm.com/blog/payments/upi/what-is-upi-circle-transaction-limits/
- **Partial delegation:** every payment needs the primary's push approval, **5-minute timer**. 🟡

### Competing protocol already live in India — Pine Labs P3P
Launched **11 June 2026**, "India's first agentic payment protocol on UPI". Stack = Reserve Pay +
One Time Mandate + an identity/delegation layer called **Grantex** + **HTTP 402** machine-readable
payment requests. Live: **Gullak** (digital gold; rule = "buy ₹500 gold if price < ₹16,000/g").
PoC: Vijay Sales. 🟠 https://www.pinelabs.com/media-analyst/the-ai-agent-can-now-pay-pine-labs-launches-p3p-indias-first-agentic-payment-protocol-built-on-upi
· 🟡 https://thepaypers.com/payments/news/pine-labs-launches-p3p-agentic-payment-protocol-on-upi

**Mastercard completed its first authenticated agentic transaction in New Delhi, June 2026.** 🟡

---

## 2. RBI constraints — the legally defined bounds ⭐

**This section is the single most valuable input to the build.** The track asks for money actions
that are *bounded and gated*. In India the bounds are not a design preference — they are law.

### RBI (Authentication Mechanisms for Digital Payment Transactions) Directions, 2025
Issued **25 Sept 2025**, compliance deadline **1 April 2026**. 🟢
https://rbidocs.rbi.org.in/rdocs/PressRelease/PDFs/PR1165D250AB0389BE4D3D9E006CECD26F928E.PDF
(CAPTCHA-walled to automated fetch) · 🟡
https://www.business-standard.com/markets/capital-market-news/rbi-issues-directions-on-framework-on-authentication-mechanisms-for-digital-payment-transactions-125092501090_1.html

- **Two factors mandatory** for all digital payments; for **non-card-present**, at least one
  factor must be **dynamic**.
- Technology-neutral: OTP, PIN, biometrics, hardware/software tokens, FIDO2 all permitted.
- **This is THE binding constraint on agentic payments. An agent is not a dynamic factor.**
  Everything agentic in India today works by moving the AFA to a **one-time upfront event**
  (mandate/block registration) rather than eliminating it.

### RBI Digital Payments – E-Mandate Framework, 2026
**RBI/DPSS/2026-27/396**, ref **CO.DPSS.POLC.No.S56/02.14.003/2026-27**, dated **21 April 2026**,
effective immediately. Repeals/consolidates **8 circulars (Aug 2019 – Aug 2024)**. Scope:
recurring domestic **and cross-border**, on cards, PPIs and UPI. 🟡
https://kpmg.com/in/en/insights/2026/06/reserve-bank-of-india-rbi-digital-payments-e-mandate-framework-2026.html
· https://www.lexorbis.com/rbis-digital-payments-e-mandate-framework-2026-consolidated-directions-for-recurring-digital-transactions/

| Rule | Value |
|---|---|
| AFA-free recurring debit ceiling | **₹15,000 / transaction** (above → AFA per txn) |
| Higher ceiling (insurance, MF subscriptions, credit-card bills only) | **₹1,00,000** |
| Registration | one-time **with AFA**; modification/withdrawal also require AFA |
| Pre-debit notification | **≥ 24 hours** before debit, carrying merchant name, amount, date/time, e-mandate reference, reason |
| Exemptions from pre-debit notice | FASTag, NCMC auto-replenishment |

Issuers must let customers change validity, withdraw at will, choose notification channel, and
set a max transaction value for variable mandates.

> **⚠️ Notable gap: no agent/AI/delegated-payment provision appears anywhere in the 2026 e-mandate
> framework. The directions do not contemplate a non-human initiator.**

### Net hard constraints for any build
1. Two factors, one dynamic, for every payment unless exempt.
2. Agentic autonomy is legally achievable **only** via e-mandate (≤₹15,000/txn AFA-free) or
   Reserve Pay block (≤₹10,000, ≤90 days, one per merchant).
3. **The 24-hour pre-debit notice kills same-session agentic checkout via the e-mandate route** —
   which is precisely why **Reserve Pay, not e-mandate, is the primitive everyone chose.**
4. Instant revocation and audit trail are non-negotiable.

- **2026 RBI guidance specifically on AI/agentic payments: no data found.** Nothing published.
- **RBI tokenisation: no 2026 update found.** Treat CoFT rules as unchanged.

---

## 3. Razorpay — numbers and product surface

### Numbers (🟠 company-stated; no audited figure found)
- **Annualised TPV ~$180 billion**; target **~$400B by 2030** (stated Feb 2025). 🟡
  https://www.business-standard.com/companies/news/razorpay-marks-10-years-targets-about-400-billion-in-tpv-by-2030-125020900388_1.html
- **>5 million businesses**, **>200 million end consumers**.
  ⚠️ Aggregators quote "12 million merchants" 🔴 — conflicts with Razorpay's own 5M. **Use 5M.**
- **~50 brands currently experimenting with agentic commerce** with Razorpay (CEO Harshil
  Mathur). 🟡 https://inc42.com/features/can-razorpay-turn-chatgpt-into-indias-next-commerce-channel/

### NPCI + Claude pilot — 20 Feb 2026, India AI Impact Summit
- Live merchants **Zomato, Swiggy, Zepto**; **closed pilot, select users**. 🟠
  https://razorpay.com/blog/agentic-payments-and-npci/
- Mechanism: **UPI Reserve Pay** — one-time consent, **per-merchant spending limit**, then no
  repeat PIN/OTP; instant revocation.
- **No transaction limits, cap values, pilot user counts, geography or conversion metrics
  disclosed** — confirmed absent from Razorpay's own post.
- Same summit: voice-first payments with **Gnani.ai, SuperU, Zomato Nugget**; in-app agent
  commerce with **Vodafone Idea**; **Replit** partnership bringing UPI to an AI dev platform.

### Agent Studio + Agentic Experience Platform — FTX'26, 12 March 2026, Bengaluru
🟠 official newsroom: https://razorpay.com/newsroom/razorpay-launches-the-worlds-first-ai-native-agent-studio-for-payments-at-ftx26-powered-by-anthropics-claude/

**Agent Studio — 5 shipped agents:** Abandoned Cart Conversion (voice-led) · Dispute Responder ·
Subscription Recovery (voice-led, with ElevenLabs) · Cashflow Forecaster · **"Build Your Agent"**
no-code plain-English builder.

**Agentic Experience Platform — 3 components:** **Agentic Onboarding** (30–45 min → **5 min**,
PAN + website) · **Agentic Dashboard** (natural-language ops, e.g. reconcile an uploaded bank
statement against settlements) · **Agentic Integration** (stack auto-detection, integrate in
**<10 min** via Claude Code, Replit, Emergent).

Integrations: Shopify, Shiprocket, WhatsApp, ElevenLabs, Slack, Tally, QuickBooks.
In-app commerce partners: Zomato, Swiggy, PVR Inox, Vodafone Idea, Bluestone, Honasa.

> "Razorpay Vulcan" payments foundation model (~4B payments, Aug 2026) appears in a **single
> low-quality source** 🔴 with no official confirmation. **Do not cite.**

### Developer surface / test mode
- **Razorpay MCP Server** — official, open source, **40+ tools** (README-verified). 🟢
  https://github.com/razorpay/razorpay-mcp-server · docs https://razorpay.com/docs/mcp-server/remote/
  - Confirmed tool categories: **Payments** (capture, fetch, update, initiate, OTP resend/submit,
    card details) · **Payment Links** (standard + UPI-specific, send via SMS/email) · **Orders**
    (create, fetch, update, fetch payments) · **Refunds** (fetch/update — `create_refund` **not
    available on remote**) · **QR Codes** · **Settlements & Payouts** (incl. recon report, instant
    settlement) · **Tokens** (saved methods by customer, revoke) · **Integration helpers**
    (detect language/framework, generate checkout code).
- **~400+ documented REST endpoints; `llms.txt` published** in developer docs for AI tools. 🟠
- **Test mode:** same base URL `https://api.razorpay.com/v1/`, swap to test keys. 🟢
  https://razorpay.com/docs/api/sandbox-setup/
- **Subscriptions test mode:** dashboard **"Charge this now"** simulates a due charge and fires
  all events without waiting. 🟢 https://razorpay.com/docs/subscriptions/test-guide/

### ⭐⭐ Catalog API gap check — CONFIRMED GAP

**Razorpay has no product catalog API.** This is the most important technical finding in the
whole research set.

- The closest surface is the **Items API**, which is an **invoicing template**, not a catalog:
  fields are name, description, amount/unit amount, currency, quantity, plus HSN (8-digit) /
  SAC (6-digit) tax codes. Items exist to populate an invoice dropdown; a **Line Item** is created
  when an Item is used as a template on an invoice; **max 50 line items per invoice**. 🟢
  https://razorpay.com/docs/api/payments/items/ · https://razorpay.com/docs/payments/invoices/items/
- **No images, no variants/SKUs, no stock/inventory, no categories, no search, no availability.**
- **The MCP server exposes ZERO catalog/product/item/cart tools** — README-verified. Also **no
  subscriptions tools**.
- "Product Configuration APIs" are a false friend — "product" there means *Razorpay products*
  activated for a sub-merchant, not merchandise.
  https://razorpay.com/docs/api/partners/product-configuration/

> **Implication:** a merchant on Razorpay literally **cannot** be browsed by an AI buyer today —
> there is no product primitive to browse. Razorpay's rails can *collect* money from an agent
> (payment links, orders, Reserve Pay) but expose **nothing for an agent to shop from**. That is
> the hole between Razorpay's stack and agentic commerce.

---

## 4. Merchant pain data

> ⚠️ **Handle with care.** Indian cart-abandonment and RTO numbers circulating in 2026 are heavily
> contaminated by SEO content citing itself. Only what survives scrutiny is below.

### RTO — the best-sourced number here
**Unicommerce India D2C Report 2026** (April 2026), built on **410+ million shipments** 🟡
https://unicommerce.com/india-d2c-report-2026-april/
- National RTO **39.2%** at the Nov 2025 festive peak → **25.6%** by Jan 2026 → **21.0%** by
  March 2026 among optimised brands. Improvement was **metro-driven**.
- **COD vs prepaid:** FY26 festive quarter — **58% of COD orders came back vs <15% prepaid**.
  FY23 baseline: COD 20.9% vs prepaid 5.8% — a **3.6× gap**.
- Independent cross-check: Shipway "ShipNotes" found **26% RTO on COD orders** nationally. 🟡
  https://mediabrief.com/shipnotes-reveals-26-rto-rate-on-cod-orders-across-india/

### COD share
**50–70% of D2C transactions; 60–70% in Tier 2/3.** 🟡 Unicommerce-derived. Note the wide range —
**there is no single authoritative national COD-share figure.**

### Market size — Bain & Flipkart, "How India Shops Online 2026"
🟢 PDF: https://storage.googleapis.com/flipkart-stories-media/How_India_Shops_Online_2026_060094273e/How_India_Shops_Online_2026_060094273e.pdf
- **E-retail GMV ~$65–66B in 2025**, growing **19–21%**; forecast **$170–180B by 2030**. 🟡
- **Online shopper base 290–300M in 2025**, doubled in 5 years; seller ecosystem **3×**. 🟡
- **Q-commerce = 16–17% of e-commerce GMV**, ahead of China; lower COD reliance. 🟡
- Grocery + beauty + general merchandise = **>75% of incremental GMV growth 2020–2025**. 🟡

### UPI failure rates — official, usable
- **Technical Decline 0.7–0.8%**, down from 8–10% in 2016. **NPCI Circular OC-149 (June 2022)**
  requires banks to hold **TD < 1%** and **Business Decline < 5%**. 🟡
  https://paytm.com/blog/payments/upi/upi-decline-rate-drops-to-0-8-global-expansion/
- **UPI scale, Aug 2026: 24.51 billion transactions worth ₹29.82 lakh crore** — record month.
  **+3.6% MoM**, **+22% YoY**. **Daily average 791 million txns, ~₹96,205 crore/day.** 🟡
  https://www.freepressjournal.in/india/upi-transactions-hit-record-2451-billion-in-august-festive-demand-drives-growth

### Cart abandonment — ⚠️ WEAK EVIDENCE
- Only defensible figure: **global average 70.22% (2026)** from **Baymard**, a genuine independent
  research shop. 🟡 https://baymard.com/lists/cart-abandonment-rate
- The India-specific claims in circulation — **"85% mobile cart abandonment in India"**, "26% of
  drop-offs from forced account creation", "UPI Intent ~98% success vs Collect flow", "<65% is a
  good D2C benchmark" — **all originate from Razorpay's own SEO blog pages** with no dataset
  disclosed. 🔴/🟠 **Do not present 85% as research.**
- **No independent India cart-abandonment measurement exists.**
- **Average step-by-step checkout drop-off (India): no data found.**

---

## 5. Long-tail merchant / catalog / vernacular

- **MSME base: 63.4 million units.** 🟡 https://www.ibef.org/industry/msme
- **Formal registrations (Mar 2026): 79 million** — 47.2M Udyam + 32.1M Udyam Assist. 🟡
  https://www.policycircle.org/industry/msme-procurement-ecommerce-boom/
- **Kirana universe: 14 million stores, 75–80% of FMCG sales.** Government **DigiDukaan** push:
  Hyderabad pilot onboarded **10,000+ retailers, 35 brands**; Jaipur launch June 2026. 🟡
  https://www.newkerala.com/news/a/india-prepares-digidukaan-expansion-digitise-14-crore-kirana-350.htm
- **Total count of Indian D2C brands: no data found.** No credible absolute number exists.
- **Platform mix: WEAK/folklore.** The claim "~80% of India D2C brands at ₹1–100 Cr GMV run on
  Shopify" comes from an agency blog with no methodology 🔴. **Shopify publishes no India merchant
  count.**
- **Structured product feed / Google Merchant Center adoption in India: NO DATA FOUND.** Google
  publishes no India GMC merchant count; no industry report covers it. **A genuine measurement
  void.**
- **Best proxy for structured catalogs — ONDC:** **~370,000 sellers across 800+ cities** (July
  2026), **100+ buyer apps**, **500M+ cumulative transactions** crossed July 2026, **~218M
  transactions in FY26**, monthly retail purchases **3.6M in March** (6× in six months). 🟡
  https://ondc.org/sellers/ · https://www.ondc.org/blog/ondc-monthly-retail-purchases-surge-sixfold-in-six-months-reaching-3-6-million-in-march/
- **Vernacular/voice — all Google-sourced and dated (largely pre-2023), cite with care:** voice
  searches in India **+270% YoY** 🟠; **~75%** of India's internet base are vernacular speakers;
  **88%** more likely to respond to an ad in their own language; **9 of 10 new internet users** are
  Indian-language users 🟠. **40% of rural India relies on voice search**; one-third have used a
  voice assistant to shop 🔴 — underlying study is the WATConsult/Recogn voice-commerce report 🟡
  https://www.watconsult.com/wp-content/themes/watconsult/VoiceCommerce-DigitalCommerceResearch-RecognWATConsult-C1.pdf
- **No 2026 India voice-commerce measurement found.**

---

## Gaps to close before relying on this

1. **UAP spec does not exist publicly.** GFF runs 9–11 Sept 2026 — check
   npci.org.in/circulars/upi immediately after. (Deadline is 5 Sept, so the build must not
   depend on it.)
2. **Bain/Flipkart 2026 PDF** needs manual reading for the real COD/prepaid split and payment mix.
3. **npci.org.in and rbi.org.in both block automated fetch** (403/CAPTCHA) — the Reserve Pay
   circular and RBI authentication directions must be opened in a browser.
4. **Every India cart-abandonment number in circulation is Razorpay marketing.** No independent
   benchmark exists.
5. **Razorpay merchant count is contradictory** (5M official vs 12M aggregator). Use 5M.
