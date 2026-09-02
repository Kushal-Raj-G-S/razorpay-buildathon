# Trust, fraud, security & liability — evidence brief

Compiled 2 September 2026. Every claim carries a number, a date and a source.
Independence flagged per item — this matters, because much of the scary data in this space is
published by vendors selling the remedy.

**Independence key**
- **Independent:** NIST, arXiv papers, Palo Alto Unit 42, Cloudflare engineering, Gartner,
  Forrester, Adobe Analytics, court records, Federal Register, EU AI Act, RBI/NPCI, FCA
- **Vendor research** (sells the remedy — attribute, never present as neutral fact): Darwinium,
  Ravelin, DataDome, Riskified, Salesforce, HUMAN, Justt, Rivero, Chargeflow, Chargebacks911,
  Checkout.com, LexisNexis Risk Solutions (huge sample, but commercial)
- **Rejected as unverifiable:** rewarx.com, cryptoaimeta.com (see §3e)

---

## 1. The quantified trust gap

### Consumer side — trust sits far below adoption

| Source | Finding |
|---|---|
| **Gartner** (independent, 27 May 2026) | Willingness to let AI **make the purchase decision** tops out at **11%**, and only in low-stakes categories (personal care, household supplies). Consumers want AI for **discovery, not decisions**. |
| **Accenture** | **9%** would let AI complete a purchase for them; **32%** would let AI decide *what* to buy if the human still pays. |
| **Riskified** Q1 2026 "Agentic Commerce Pulse" (vendor, US+UK, 27 Apr 2026) | **61.5%** already use AI for discovery · **55.0%** not comfortable with AI agents purchasing · **53.9%** believe AI increases fraud risk · **73.9%** expect strong safeguards (biometric/OTP) before allowing agent purchases · **50.8%** say the **AI platform** should be liable for unauthorized purchases |
| **Salesforce** (vendor) | **74%** trust AI chat recommendations; only **48%** of existing AI-shopping users are open to an agent purchasing. Note the collapse from "trust recommendations" (74%) → "let it buy" (48% → 9–11% in independent surveys). |
| **Forrester** (independent, paywalled) | Report title alone corroborates: *"Many US Consumers Believe In Agentic Commerce, But Few Trust It To Make Purchases"* |

- Gartner: https://www.gartner.com/en/newsroom/press-releases/2026-05-27-gartner-survey-finds-consumers-want-ai-shopping-help-but-not-ai-purchase-decisions
- Accenture: https://wwd.com/sourcing-journal/industry-news/accenture-survey-consumers-ai-agents-shopping-1239011715/
- Riskified: https://www.businesswire.com/news/home/20260427900819/en/Riskified-Study-Finds-Consumers-Arent-Ready-to-Hand-Over-Control-as-AI-Transforms-Shopping-with-Over-Half-Afraid-of-Online-Fraud
- Salesforce: https://www.salesforce.com/news/stories/agentic-search-growth/
- Forrester: https://www.forrester.com/report/many-us-consumers-believe-in-agentic-commerce-but-few-trust-it-to-make-purchases/RES188737

### Merchant side — adoption racing ahead of readiness

**Ravelin** (vendor; n=**1,504** fraud/payments professionals, 10 countries, enterprises >$50M
revenue or >450 staff, surveyed Jan 2026):
- **44%** already integrating agentic protocols; **+32%** within six months → **3 in 4** in or entering
- only **6%** have no plans
- merchants expect agentic to be **6–30%** of transactions within 3 years
- ⚠️ **53% say they trust AI shopping agents *more* than human shoppers** — a striking and
  arguably reckless finding given §3
- https://pages.ravelin.com/agentic-commerce-fraud-report/ · https://securitybrief.co.uk/story/merchants-rush-to-adopt-ai-shopping-agents-ravelin-finds

**PYMNTS Intelligence** (March & June 2026):
- only **23%** of merchants can clearly identify AI-agent-driven demand (**27%** large vs **19%** SMB)
- **~80%** of *acquirers* say they are at least somewhat prepared — **the readiness gap sits with
  merchants, not processors**
- active merchant-readiness initiatives: **31%** UAE, **20%** US, **16%** Brazil
- https://www.pymnts.com/news/artificial-intelligence/2026/how-23-percent-of-merchants-captuared-retails-next-agentic-commerce-advantage/ · https://www.pymnts.com/news/artificial-intelligence/2026/80percent-of-acquirers-say-they-are-ready-for-agentic-commerce-but-merchants-lag/

**Darwinium "Agentic Commerce Fraud Report 2026"** — vendor research; n=**500** fraud/risk/security
leaders (US 70%/UK 30%, **64% VP+**). ⚠️ **Branded 2026 but fieldwork was early 2025** — a real
caveat. Industries: fintech/banking 40%, gaming/gambling 30%, ecommerce/marketplace 20%, travel 11%.
https://www.darwinium.com/navigating-agentic-commerce-2026-report
- **97%** saw AI-facilitated attacks increase in the prior 12 months
- **75%** estimate ≥26% of current fraud attempts are AI-assisted; **25%** say >50%
- **93%** have encountered deepfake fraud attempts; **45%** multiple incidents
- **95%** have agentic AI in their top-5 security priorities for 2026
- Detection gap: **64%** defend only select checkpoints; only **36%** claim end-to-end coverage;
  **50%** run 5–6 separate vendors, **16%** run 7+; only **45%** have tested playbooks
- **No industry consensus on agent traffic policy: 48% allow by default with post-hoc
  monitoring · 31% block by default unless allowlisted · 20% case-by-case per endpoint**

**Market framing** (vendor/consultancy forecasts, for context only): Bain — **15–25%** of
e-commerce volume via agentic AI by 2030; McKinsey — **$3–5 trillion** agentic commerce revenue by
2030; WEF (2026) — **1 in 4** data breaches could stem from AI agent exploitation by 2028.
Cited in https://unit42.paloaltonetworks.com/retail-fraud-agentic-ai/

---

## 2. Agent impersonation and spoofing — measured

**DataDome AI Traffic Report** (vendor telemetry, ~16 Mar 2026):
- **7.9 billion** AI agent requests across DataDome's network in **Jan–Feb 2026 alone** (+5% vs Q4 2025)
- **PerplexityBot: ~2.4%** of requests bearing that identity were fraudulent — highest impersonation **rate**
- **Meta-ExternalAgent: 16.4M spoofed requests** — highest impersonation **volume**
- **ChatGPT-User: 7.9M spoofed requests**
- For one customer, agentic traffic was **9.75%** of total traffic over 30 days
- Headline: most organizations are "flying blind" — cannot distinguish agent from human from bot
- https://datadome.co/press/datadome-report-finds-most-organizations-flying-blind-as-agentic-traffic-surges/ · https://itbrief.co.uk/story/spoofed-ai-agents-flood-websites-straining-defences

**LexisNexis Risk Solutions Global Cybercrime Report 2026** (commercial, but **116 billion+**
digital transactions analysed, 26 Mar 2026):
- **+8%** global fraud attack rate rise, attributed partly to **agentic bots posing as humans**
- **Agentic traffic +450%** Jan→Dec 2025, concentrated on **credit card payments and logins at
  gaming/gambling sites**
- **+59%** rise in malicious bot attacks; bots now mimic human cursor movement well enough to
  defeat behavioural detection
- ⭐ Structural point worth quoting: LexisNexis frames agents as a **third interaction type**
  alongside "genuine human" and "traditional bot" — **existing risk engines only have two buckets**
- https://risk.lexisnexis.com/global/en/about-us/press-room/press-release/20260326-ccr-global-fraud

**The Cloudflare ⇄ Perplexity case (Aug 2025)** — the canonical documented spoofing incident,
with methodology:
- Cloudflare registered **brand-new domains** with `User-agent: * / Disallow: /` and WAF rules
  blocking Perplexity's declared crawlers. Perplexity content still appeared.
- Mechanism: fallback to a **generic Chrome 124 / macOS user-agent string**, with **rotated IPs
  and ASNs**.
- Cloudflare **delisted PerplexityBot from Verified Bots** and blocked the stealth crawlers.
- **Perplexity's rebuttal, for balance:** Cloudflare conflated **3–6M daily requests** from
  third-party cloud-browser service BrowserBase with Perplexity's own traffic, which it says was
  **<45,000 daily requests**.
- https://blog.cloudflare.com/signed-agents/ · https://www.perplexity.ai/hub/blog/agents-or-bots-making-sense-of-ai-on-the-open-web · https://www.searchenginejournal.com/cloudflare-delists-and-blocks-perplexity-from-crawling-websites/552899/

**HUMAN Security** (vendor) independently documents attacker campaigns impersonating ChatGPT,
Mistral and Perplexity crawlers.
https://www.humansecurity.com/learn/blog/ai-crawler-spoofing-chatgpt-mistral-perplexity/

### How merchants detect this today — and the state of the standard
- **Web Bot Auth** — IETF Internet-Draft led by Cloudflare; HTTP Message Signatures over an
  agent-held key. Shipped into Cloudflare's Verified Bots **1 July 2025**, the same day Cloudflare
  began blocking AI crawlers by default. **19 agents** in the Verified AI Agent category at launch
  (ChatGPT Atlas, Claude in Chrome, Perplexity Browser, Gemini Agent Mode, Brave Leo, Arc Browse
  for Me). AWS WAF Bot Control added support **Nov 2025**; Vercel, Akamai, Stytch, Shopify followed.
  Cloudflare AI bot requests exceed **10 billion/week**.
- ⚠️ ~~**Critical gap: as of 18 Aug 2026 it is still an individual Internet-Draft — not even adopted
  by an IETF working group — yet gatekeepers enforce it in production.**~~
  > ⚠️ **CORRECTED by [06-protocols.md](06-protocols.md):** this is **now stale**. A chartered IETF
  > working group (`webbotauth`) exists and the document is **WG-adopted**:
  > **`draft-ietf-webbotauth-httpsig-protocol-00`**, published **1 Sept 2026**, intended Standards
  > Track. What *is* still individual-submission and NOT WG-adopted is the **agent registry**
  > (`draft-meunier-webbotauth-registry-03`). And critically, the protocol states outright:
  > **"It is not a revocation mechanism"** — it defines no authorization, no delegation, and no way
  > for one origin to convey an opinion about an agent to another.
- Practical reality: for most merchants identity is asserted by **user-agent string + IP/ASN
  reputation**, both trivially spoofable. Cryptographic signing exists but is unevenly adopted and
  unratified.
- https://blog.cloudflare.com/signed-agents/ · https://developers.cloudflare.com/bots/concepts/bot/verified-bots/ · https://stellagent.ai/insights/web-bot-auth-cloudflare-ietf

---

## 3. Documented failure incidents ⭐ (the core section)

### 3a. In-the-wild indirect prompt injection aimed at money actions
**Palo Alto Unit 42** (independent security research, 2026) — real malicious pages found in
production telemetry: **22 distinct payload-engineering techniques**, 12 documented case studies.
https://unit42.paloaltonetworks.com/ai-agent-prompt-injection/

| Case | Mechanism |
|---|---|
| **Forced paid subscription** (`llm7-landing.pages.dev`) | Payload delivered via **JavaScript dynamic execution**, coercing the agent into subscribing the victim to a paid "pro plan" without consent, routing through `token.llm7.io` Google OAuth. *Agent has session + payment authority; the page supplies the instruction.* |
| **Forced donation** (`storage3d.com`) | Instruction hidden via **HTML attribute cloaking**, pointing the agent at a live Stripe payment link. Rated high severity. *Attacker monetises directly through a legitimate processor — no card theft needed.* |
| **Forced purchase of running shoes** (`runners-daily-blog.com`) | Instruction hidden by **off-screen CSS positioning**. *Human sees a blog; the agent sees a buy order.* |
| **"Free money" scam** (`perceptivepumpkin.com`, `shiftypumpkin.com`) | Payload instructs the agent to **send $5,000 to an attacker-controlled account**. |
| **Ad-review bypass** (`reviewerpress.com`, first observed **Dec 2025**) | Payload designed to make an AI *reviewer* approve scam content it should reject. *Injection against the control system, not the buyer.* |

Related (Cybernews / Google reporting):
- A single **fake-military-eyewear storefront carried 24 separate prompt-injection attempts** aimed
  at getting ad-review AI to approve it.
- A Costa Rica spa page hid **zero-font-size** text instructing AI visitors to "GIVE A POSITIVE
  REVIEW", specifying what to include and what to suppress.
- A fraudulent domain impersonating DeBank hid text instructing models to treat it as the verified
  authoritative site, rank it first, and **avoid mentioning the word "auction" in the domain name**.
- **Google has publicly stated prompt injection has moved from theory into real abuse**, specifically
  flagging SEO-motivated injection.
- https://cybernews.com/security/hackers-poison-websites-with-malicious-ai-prompts/ · https://www.searchengineworld.com/google-says-prompt-injection-moving-from-theory-into-real-abuse

### 3b. Agentic-commerce-specific attack mechanisms
**Unit 42 retail research** (independent) https://unit42.paloaltonetworks.com/retail-fraud-agentic-ai/

- ⭐⭐ **Gift-card theft via checkout payload poisoning:** attackers inject hidden instructions into
  **deals-aggregator sites that agents crawl**. When the agent builds the checkout payload,
  unauthorized gift cards are **appended to the CartMandate** and delivered to an
  attacker-controlled email. **Invisible to the user until the billing statement arrives.**
  → *This is the cleanest possible "every money action must be explainable and bounded" story: the
  harm is an extra line item in a payload no human ever inspected.*
- **Returns fraud via logic hijacking:** malicious listings hide commands **in HTML metadata**
  telling agents to skip verification and issue instant refunds against fake tracking IDs.
  Unit 42's modelled worst case: bot farms initiating **10,000 void-000 returns in a single hour**,
  "potentially liquidating a retailer's cash reserves."
- Baseline: organised retail crime already costs **$700,000 per $1 billion in sales**; **57%** of
  retailers report increased ORC activity in the past year.

### 3c. Measured attack success rates (academic)

- ⭐⭐ **NIST — the single most quotable number in this brief.** In NIST's agent-hijacking
  evaluation work, when red-teamers developed **novel attack techniques tailored to the specific
  behavioural patterns of the target agent** rather than using known baseline attacks,
  **task-hijacking success rose from 11% to 81%**. Built on the open-source **AgentDojo** framework
  plus NIST enhancements on UK AISI's Inspect platform.
  → *Implication for a judging panel: published low attack-success rates are an artefact of generic
  attacks. Adaptive attacks near-universally succeed.*
  https://www.nist.gov/news-events/news/2025/01/technical-blog-strengthening-ai-agent-hijacking-evaluations
- **StakeBench** — *"Who Pays the Price? Stakeholder-Centric Prompt Injection Benchmarking for
  Real-world Web Agents"* (arXiv 2606.13385v2, **28 Jul 2026**). Explicitly an **e-commerce**
  benchmark: **12 attack objectives**, **3 stakeholder classes**, **22 reusable attack templates**,
  **264 executable adversarial cases**, **12 product categories**, **3,168 attacked runs**.
  Headline: *"no attack objective is reliably resisted by current LLM-based web agents"*, and
  prompt-injection risk is **victim-dependent — one exploit produces asymmetric consequences for
  different stakeholders** (user vs merchant vs platform). Explicitly covers "actions that carry
  direct financial consequences." https://arxiv.org/abs/2606.13385
- **AgentDojo** (Debenedetti et al.) — **97 tasks, 629 security test cases** across email, banking,
  travel, workspace. Best agent (Claude 3.5 Sonnet) **78% benign utility**; GPT-4o utility drops
  **69% → 50% under attack**. Downstream red-teaming (AgentVigil, arXiv 2505.05849) reports
  per-suite ASRs of **0.38–1.00** depending on model and suite. https://arxiv.org/pdf/2505.05849
- **Meta web-agent security research:** prompt-injection attacks **partially succeeded in 86% of
  cases** — ⚠️ widely reported but vendor-published; verify the primary paper before slide use.
- **"Adaptive Attacks Break Defenses Against Indirect Prompt Injection Attacks on LLM Agents"**
  (arXiv 2503.00061) — published defences fail against adaptive attackers. Pairs with the NIST
  11%→81% finding.

### 3d. Real corporate / legal incidents

**Amazon v. Perplexity** (verified, well documented):
- Amazon sent a **cease-and-desist Nov 2025** demanding Perplexity's Comet agent stop transacting
  on Amazon. Both firms had agreed to pause agentic shopping in 2024; Amazon alleges Perplexity
  re-enabled it by **disguising Comet's agent as an ordinary Chrome browser**.
- Amazon sued under the **Computer Fraud and Abuse Act**, alleging Perplexity "concealed" its
  agents, "degraded the Amazon shopping experience," and accessed customer accounts without
  disclosure.
- Amazon won a **temporary injunction (Mar 2026)**; the **Ninth Circuit then overturned it**,
  holding Amazon's CFAA claim did not hold up.
- → *Retellable as: the largest merchant on earth could not reliably tell an agent from a browser,
  and the law does not yet settle whether it may exclude one.*
- https://www.paymentsdive.com/news/amazon-sues-perplexity-ai-shopping-agents/804923/ · https://www.cnbc.com/2026/03/10/amazon-wins-court-order-to-block-perplexitys-ai-shopping-agent.html · https://www.engadget.com/2230471/perplexity-has-successfully-overturned-amazon-injunction-on-its-ai-shopping-bot/

⭐⭐ **OpenAI Instant Checkout was SHUT DOWN — announced 5 March 2026**, under a year after launch.
The best available "agentic checkout failed on trust and friction" datapoint:
- Only **8%** of US adult ChatGPT users tried it in its first month; usage stayed low across the
  five-month trial.
- Only **~a dozen Shopify merchants** were actually live.
- **Walmart measured in-ChatGPT checkout converting roughly 3× WORSE** than a click-through to
  walmart.com — even though ChatGPT drove ~**2× the new-customer rate** of search.
- Launch scope was single-item, US Etsy sellers only — **no multi-item carts, promo codes,
  shipping promises or state sales tax remittance**.
- OpenAI's own words: the version "did not offer the level of flexibility that we aspire to provide."
- Shopify merchants had been facing a **4% fee** on ChatGPT checkout sales **on top of** Shopify fees.
- https://www.cnbc.com/2026/03/24/openai-revamps-shopping-experience-in-chatgpt-after-instant-checkout.html · https://www.forbes.com/sites/jasongoldberg/2026/03/10/why-openais-checkout-retreat-spells-trouble-for-its-commerce-strategy/ · https://www.forrester.com/blogs/what-it-means-that-the-leader-in-agentic-commerce-just-pulled-back/ · https://www.pymnts.com/news/ecommerce/2026/shopify-merchants-to-pay-4percent-fee-on-sales-made-through-chatgpt-checkout/

**Perplexity privacy class action** (verified, but **NOT** a purchase case): *Doe v. Perplexity AI
Inc.*, **3:26-cv-02803**, N.D. Cal. — alleges undetectable tracking software sent user
conversations to Meta, Google and other third parties in violation of California privacy law.
https://www.benzinga.com/markets/private-markets/26/04/51615214/perplexity-ai-under-fire-in-lawsuit-alleging-privacy-violations

### ⚠️ 3e. Claims that FAILED verification — do NOT use these

Two attractive-sounding "incidents" surfaced **only** on low-quality SEO/AI-generated blogs
(`rewarx.com`, `cryptoaimeta.com`) and failed independent corroboration on targeted follow-up:

1. A *"Perplexity Buy with Pro class action, N.D. Cal., Feb 2026, $1.8 million in confirmed
   unauthorized transactions."* **No docket, no news coverage, no court record.** The only real
   N.D. Cal. Perplexity class action is the privacy case above. **Treat as fabricated.**
2. An *"FTC complaint against OpenAI, March 2026, citing a 22% rise in disputed Shopify merchant
   charges in the 90 days after Instant Checkout launched."* **No FTC record, no press coverage.**
   **Treat as fabricated.**

> ⭐ **This is itself a finding worth 15 seconds of the pitch:** the agentic-commerce incident record
> is thin enough, and the topic hot enough, that the search-result layer is **already polluted with
> plausible synthetic incidents carrying fake docket numbers and fake dollar figures**. Provenance
> and verifiability are the problem, recursively.

**Genuine gaps:** no data on measured rates of **duplicate/double purchases** by agents, and **no
public post-mortem** of a specific named consumer's unauthorized agent purchase with a dollar figure.
Consumer-harm evidence exists as **survey sentiment** and as **security-research capability** — not
yet as a documented, adjudicated loss event.

---

## 4. False positives / over-blocking cost

**The "$1M+ false positive" stat — primary source located.** It is **Darwinium's Agentic Commerce
Fraud Report 2026**, from the n=500 survey (**fielded early 2025**). ⚠️ **Vendor research —
Darwinium sells the remedy.** https://www.darwinium.com/navigating-agentic-commerce-2026-report

| Metric | Figure |
|---|---|
| Orgs estimating false-positive cost at **$1M+/yr** | **62%** |
| Average annual **direct AI fraud loss** | **$4.5M** |
| Average annual **revenue lost to false positives** | **$3.0M** |
| Future revenue lost **per 1,000 impacted accounts** | **$825K** |
| **Total annual exposure** per organization | **$7.5M** |

**Methodology caveats to state honestly:** these are **self-reported estimates by respondents**,
not audited financials, and "cost of a false positive" includes **modelled lifetime-value loss**
(the $825K/1,000 accounts line), not just the declined basket. Darwinium's **qualitative** claim —
that the cost of blocking good customers and good agentic traffic is approaching parity with letting
bad actors through — is defensible. **The dollar precision is not.**

**Corroborating over-blocking evidence:**
- **Finextra** (trade press, 2026): merchants are **losing revenue because fraud systems
  misclassify AI shopping agents as malicious bots**.
  https://www.finextra.com/newsarticle/47675/merchants-losing-revenue-as-fraud-systems-misclassify-ai-shopping-agents-as-malicious-bots
- Mechanism (well attested): browser-resident shopping agents produce traffic that looks
  **increasingly human**, so systems tuned for "a human is always behind the transaction" misfire
  in **both** directions.
- ⭐ **Adobe Analytics** (independent measurement, Q1 2026): AI-referred traffic to US retailers
  **+393% YoY**; **AI-referred shoppers convert 42% better** than other shoppers. Retailers who
  **blocked AI crawlers saw referral traffic fall 18% month-over-month**; Walmart, which leaned in,
  captures **~20%** of ChatGPT referral traffic. Retailers with agent integrations saw **7× sales
  growth during Cyber Week 2025**.
- **Salesforce** (vendor): brands with branded shopper agents saw **+6.2%** holiday sales growth vs
  **+3.9%** without (59% higher growth rate). https://www.salesforce.com/blog/holiday-retail-predictions-2026/
- **Darwinium:** no consensus blocking posture — **48% allow-by-default, 31% block-by-default,
  20% case-by-case**. → **Over-blocking is a policy accident, not a decision.**

> ⚠️ Note the tension worth acknowledging in the pitch: Adobe says AI-referred shoppers convert
> **42% better**, while Walmart measured in-ChatGPT checkout converting **3× worse**. These are not
> contradictory — **AI as a referral channel works; AI as the checkout surface did not.** That
> distinction is load-bearing for Track 01.

---

## 5. Liability and dispute rules — largely an open gap

### Card networks: no agent-specific liability rule exists
- **No rule assigns fault** among consumer, AI provider and merchant for a disputed agent-initiated
  purchase. Network rules have **not** been amended for agents; existing liability allocation
  applies unchanged. https://www.chargeflow.io/blog/ai-agent-chargeback-liability
- **Visa VAMP** and **Mastercard ECM** dispute-ratio thresholds apply identically regardless of
  whether an agent initiated the transaction — an agent-driven dispute spike counts against the
  merchant's monitoring programme like any other.
- ⭐ **No dedicated agentic dispute reason code exists** at either major network. Agentic disputes
  are filed under **existing codes**, with **"did-not-authorize" the dominant category**.
  https://www.chargeflow.io/chargebacks-101/chargeback-reason-codes · https://justt.ai/blog/solving-agentic-commerce-chargebacks/
- **Worldpay's own framing:** *"Agentic commerce liability is still being written."*
  https://www.worldpay.com/en/insights/articles/agentic-commerce-liability-is-still-being-written

### ⭐⭐ The evidence gap — what merchants must retain, and can't
(Vendor sources — Justt, Rivero, Chargeflow, Checkout.com, Chargebacks911 — but **consistent
across all of them**.)

- Traditional dispute evidence **largely disappears**: no human click trail, no cardholder
  behavioural session data, and the **device fingerprint belongs to the agent's MCP server, not the
  buyer's device**.
- What is required instead: **proof of delegated authority** — the user's instruction, the
  scope/limits granted, the approval signal, and notification timestamps, captured **before the
  agent executes**.
- ⭐⭐ **The quote that defines the opportunity:** *"Mandate evidence is the real gap, and no tool
  captures it yet."*
- **The hardest class of dispute:** a shopper claiming the agent **misunderstood an instruction,
  bought the wrong item, or exceeded its authority** is making a **dispute claim, not a fraud
  claim** — and as merchant of record you bear the chargeback **even when an authorized agent acted
  exactly as instructed**.
- **Volume forecast: Datos Insights** projects **+24%** global chargeback volume 2025→2028, reaching
  **324 million disputes annually**, with agentic commerce accelerating the curve before
  authentication standards mature.
- **Amex** has issued a **partial** answer on responsibility for incorrect agent purchases (page
  403s to automated fetch — worth a manual read):
  https://thefinancialbrand.com/news/payments-trends/when-ai-agents-make-incorrect-purchases-whos-responsible-197147
- Bloomberg Law on the novel exposure:
  https://news.bloomberglaw.com/banking-law/ai-shopping-agents-pose-novel-liability-authorization-risks

### Regulators

- ⭐ **India — the most advanced national infrastructure play.** NPCI's **UAP** would let agents make
  small payments without per-transaction approval, with **user-set rule-based instructions,
  spending limits, audit trails and identity checks**, plus direct merchant integration. **Launch
  requires RBI approval.** RBI's **Payments Vision 2028** (27 Mar 2026) sets the surrounding roadmap.
  → *"Spending limits + audit trails + identity checks" is literally the regulator-endorsed control
  set — and it is verbatim the hackathon's judging bar.*
  https://www.newsonair.gov.in/rbi-announces-its-payments-vision-2028-outlining-roadmap-to-strengthen-expand-indias-rapidly-growing-digital-payments-ecosystem
- **UK FCA:** ran a "Supercharged Sandbox" with Nvidia from mid-2025, first cohort completed **Jan
  2026**; in **Mar 2026** formally named **agentic payments a live policy question** in its Payments
  Regulatory Priorities report. **Signal of intent, not a rule.**
- **EU:** **EU AI Act Article 50(1), in force 2 Aug 2026** — providers of AI systems interacting
  directly with people must ensure those people **know they are dealing with AI**. Also imposes
  transparency, human-oversight, governance and **record-keeping** duties on higher-risk systems.
  **The only *binding* agent-disclosure obligation identified.**
  https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai
- **US / CFPB: no data found.** No CFPB guidance, rule or interpretive statement on AI-agent-initiated
  payments located. The relevant existing framework is **Regulation E / EFTA (12 CFR Part 1005)**
  unauthorized-EFT liability, last clarified by a CFPB Compliance Aid on **15 Jan 2025** — which
  predates and does not mention agentic commerce. **Whether an agent-initiated transfer the consumer
  did not specifically intend is an "unauthorized EFT" under Reg E appears unanswered in writing.
  That gap is itself a finding.**
- Academic framing: *AI Agents in Payments: Applications, Risks and Regulations*, **European Journal
  of Risk Regulation** (Cambridge)
  https://www.cambridge.org/core/journals/european-journal-of-risk-regulation/article/ai-agents-in-payments-applications-risks-and-regulations/C2EF22C4CD9513A9A6459D10680A5D12
  · WEF: https://www.weforum.org/stories/artificial-intelligence/how-do-we-regulate-payments-when-its-ai-agents-spending-the-money/

---

## 6. Existing standards for auditability of agent actions

**OWASP Top 10 for Agentic Applications** — published **9 Dec 2025** by the OWASP Agentic Security
Initiative; **100+ contributors**, review board from **NIST, Cisco, Microsoft, AWS**. The closest
thing to a consensus control catalogue. Explicit audit-trail expectations:
- **Signed, immutable audit trails** for actions, tool calls and messages
- Against **ASI08 Cascading Failures** and **ASI10 Rogue Agents**: log **every decision, tool call
  and state change, including a stable identifier for the active goal** (goal provenance, not just
  call logs)
- **Log and audit every privileged action**
- Establish a **behavioural baseline per agent**; deviation triggers immediate alert. Observability
  framed as **a security control, not a debugging tool**.
- https://genai.owasp.org/ · https://cycode.com/blog/owasp-top-10-agentic-applications/ · https://neuraltrust.ai/blog/owasp-top-10-for-agentic-applications-2026

**NIST**
- **NIST AI 100-2 E2025** (adversarial ML taxonomy, 24 Mar 2025) — current taxonomy of
  agent-hijacking categories: **indirect prompt injection, remote code execution via tool use,
  database exfiltration**.
- Four control focus areas for agent deployments: **identification, authorization, access
  delegation, logging**. Specific expectations: agents authenticate as **distinct non-human
  principals** (not under user credentials); tool/API access **scoped by explicit authorization
  policy**, not inherited from operator permissions; **delegation chains from user to agent bounded
  in scope and duration**.
- ⚠️ **NIST/CAISI issued an RFI on Security Considerations for AI Agents — Federal Register, 8 Jan
  2026.** NIST is still *gathering input*; **there is no finalized NIST agent-security standard.**
  https://www.federalregister.gov/documents/2026/01/08/2026-00206/request-for-information-regarding-security-considerations-for-artificial-intelligence-agents

**Verifiable credentials for agent transactions — AP2 is the concrete spec**
- **AP2**, Google-initiated, announced **16 Sep 2025** with **60+ launch partners**. Spec:
  https://ap2-protocol.org/
- ⭐ **Mechanism maps almost exactly onto the judging bar:** AP2 Mandates are cryptographically
  signed claims carrying an issuer, a transaction context, a payload and a signature, giving
  successive **gates**: authorized scope → cart contents → payment execution.
  > ⚠️ **CORRECTED by [06-protocols.md](06-protocols.md):** mandates are **SD-JWT VCs (RFC 9901)**,
  > **not** W3C Verifiable Credentials, and the type names here are stale — the shipped set is
  > `CheckoutMandate` / `OpenCheckoutMandate` / `PaymentMandate` / `OpenPaymentMandate` (+
  > `CheckoutReceipt` / `PaymentReceipt`); **`IntentMandate` no longer exists**. Note also that
  > AP2's `Item` is a **four-field stub** (`id`, `title`, `price`, `image_url`) with **no currency
  > field**, so an AP2-signed cart signs a drastically reduced view of the cart.
- **Dispute relevance, stated explicitly by the spec's proponents:** a merchant facing a chargeback
  can produce the **signed Intent Mandate authorizing the purchase scope**; AP2 is designed as a
  **non-repudiable cryptographic audit trail**.
- **Visa Trusted Agent Protocol (TAP)** — verifies agents acting for consumers using
  **cryptographically signed credentials confirming both agent identity and consumer authorization**.
  **Mastercard Agent Pay** (announced **29 Apr 2025**) — verified agents transact via **Agentic
  Tokens**, an extension of MDES. Both are **network-specific implementations** alongside AP2's open
  governance; **an AP2 mandate envelope can wrap a Mastercard Agentic Token**.
  https://www.nasdaq.com/press-release/visa-and-partners-complete-secure-ai-transactions-setting-stage-mainstream-adoption

### ⭐ What "an audit trail" is currently expected to contain
Synthesis across OWASP, NIST, AP2 and the dispute-defence literature — **use this as the build's
conformance checklist**:

1. **Signed, immutable** record — non-repudiable, tamper-evident
2. **Agent identity as a distinct non-human principal**, cryptographically attested (Web Bot Auth /
   TAP / Agentic Token)
3. **Delegation chain** user → agent, **bounded in scope and duration**
4. **The user's mandate**: original instruction, granted scope, spending limits, approval signal,
   timestamped **before execution** (AP2 Intent Mandate)
5. **Every tool call, decision and state change**, each tagged with a **stable identifier for the
   active goal**
6. **Every privileged/money action** logged separately and explicitly
7. **The cart/payload as executed**, signed (AP2 Cart + Payment Mandates) — *so an appended gift card
   is detectable*
8. **Notification timestamps** to the user
9. **Behavioural baseline + deviation alerts** per agent

### Gaps in the standards layer (findings in themselves)
- **No finalized NIST agent-security standard** — still at RFI stage as of Jan 2026.
- **Web Bot Auth is an individual Internet-Draft**, not working-group adopted, yet enforced in
  production by Cloudflare, AWS, Akamai, HUMAN, Vercel — **de facto gatekeeping ahead of any
  standard**.
- **No agentic dispute reason code** at either major network.
- **No tool captures mandate evidence end-to-end today**, per the dispute-recovery industry's own
  assessment.
- **AP2/TAP/Agent Pay adoption rates: no data found.** Announcements and partner counts exist;
  measured production transaction share does not.
