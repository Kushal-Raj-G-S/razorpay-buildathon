# Market data — adoption, conversion, and whether agents can actually buy

Evidence brief, 2 September 2026.

**Source tags:** **[P]** primary/first-party · **[J]** independent journalism · **[A]** academic /
peer-reviewed · **[V]** vendor marketing · **[?]** SEO/aggregator, unverified — lead only, never
evidence.

---

## 1. ⭐⭐ What replaced Instant Checkout: ACP survived, but as a *discovery* protocol

This is the most important strategic fact in the whole research set.

- **OpenAI killed in-chat purchase and kept ACP.** The 24 Mar 2026 revamp shipped visual/image
  product search, budget-criteria filtering and side-by-side comparison — **checkout hands back to
  the merchant.** OpenAI's stated reasoning: Instant Checkout "did not offer the level of
  flexibility that we aspire to provide, so we're allowing merchants to use their own checkout
  experiences while we focus our efforts on product discovery." **[J]**
  https://www.retaildive.com/news/walmart-sparky-chatgpt-instant-checkout/815647/ (25 Mar 2026)
  ⚠️ OpenAI's own page (https://openai.com/index/powering-product-discovery-in-chatgpt/) **403s to
  automated fetch — the wording could not be verified first-hand.**
- **ACP merchants on the discovery track (8 named):** Target, Sephora, Nordstrom, Lowe's, Best Buy,
  The Home Depot, Wayfair, Walmart. Merchants supply product feeds + promotions; delivery paths
  include Salesforce and Stripe. **[J]** ⚠️ One aggregator says "seven major retailers"; retaildive
  names eight. **No source gives a total ACP merchant count.**
- ⭐ **The new shape is a merchant-run app-in-chat.** Walmart's **Sparky** runs as an in-ChatGPT app
  covering discovery → purchase with account linking, loyalty and payment — **the merchant owns the
  transaction surface, not OpenAI.** Web first; iOS/Android "coming soon" as of Mar 2026. **[J]**
- **The ACP spec is alive and still contains checkout.** GitHub `spec/` directories verified
  directly: `2025-09-29`, `2025-12-12`, `2026-01-16`, `2026-01-30`, `2026-04-17`, `unreleased`.
  Latest stable **2026-04-17** — shipped *after* Instant Checkout's death — added **cart, feed,
  orders, delegated authentication and MCP**. Jointly governed by OpenAI + Stripe as "Founding
  Maintainers", with a stated path to neutral foundation stewardship. Still labelled **beta**. **[P]**
  https://github.com/agentic-commerce-protocol/agentic-commerce-protocol
- **Stripe's ACP surface is live** and still sells agentic checkout: agentic checkout, cart & feed,
  delegate payment, delegate authentication, orders & webhooks. Stripe now names **Meta** as a
  co-creator alongside OpenAI. **[P]** https://docs.stripe.com/agentic-commerce/acp
- **Stripe Agentic Commerce Suite named merchants [V]:** URBN (Anthropologie, Free People, Urban
  Outfitters), Etsy, Ashley Furniture, Coach, Kate Spade, Nectar, Revolve, Halara, Abt Electronics;
  "more than 25 partners" endorsing ACP incl. Salesforce, Squarespace, PwC.
  https://stripe.com/blog/agentic-commerce-suite
- ⚠️ **Contradiction to flag:** ucphub.ai claims a "2026-07-28 ACP spec — largest revision since
  launch, stateless core, Extensions, Tasks & MCP Apps." **No such directory exists in the ACP
  repo.** Either unreleased-branch content described as shipped, or fabricated. **[?] Do not cite.**

> **Strategic read:** the industry already ran the experiment of "AI platform owns checkout" and it
> failed. The surviving architecture is **AI platform owns discovery, merchant owns checkout**. Any
> Track 01 build that puts the agent in charge of the payment surface is rebuilding the thing that
> just died. The defensible position is **merchant-side**.

---

## 2. Post-March-2026 measurement: the trend *accelerated* despite OpenAI's retreat

All Adobe figures **[P]** Adobe Analytics, >1T US retail site visits — independent of the AI
vendors, though Adobe sells the analytics.

| Metric | Figure |
|---|---|
| AI-referred retail traffic, May 2026 | **+138% YoY**, and **+1,324% vs Oct 2024** (~14×) — a new peak above every month of 2025 |
| ⭐ Conversion, Mar 2025 | AI traffic converted **~38–50% WORSE** |
| ⭐ Conversion, Mar 2026 | **+42% BETTER** |
| ⭐ Conversion, May 2026 | **+54% BETTER** |
| Revenue per visit, May 2026 | AI-referred **+53%** vs non-AI — reversed from non-AI being worth **+128%** more a year earlier |
| Engagement, May 2026 | +53% time on site · +23% pages/visit · +15% engagement rate (Mar 2026 was +48%/+13%/+12% — roughly doubled QoQ) |
| Q2 2026 AI-driven visit share YoY | Travel **+194%** · Retail **+138%** · Financial Services **+105%** |

Sources: https://www.digitalcommerce360.com/2026/06/17/adobe-ai-referred-traffic-to-retail-sites-doubles-in-a-year/ ·
https://business.adobe.com/blog/ai-traffic-surge-retail-sites-not-machine-readable ·
https://business.adobe.com/resources/sdk/q3-ai-traffic-trends-report.html

- **Adobe consumer survey [P]:** 79% of AI-shopping users feel more confident post-purchase; 69% say
  less likely to return an item bought with AI help. ⚠️ Survey **n and field date not found**.
- **Salesforce Shopping Index Q2 2026 [V/P]:** global digital traffic **+18%**, order volume **+1%**,
  AI-driven shopping traffic **+119%**. ⚠️ Ran alongside an Agentforce Commerce launch —
  vendor-launch-adjacent. https://futurumgroup.com/insights/salesforce-launches-agentforce-commerce-as-ai-shopping-traffic-jumps-119/
- ⭐ **Shopify Q2 2026 earnings (5 Aug 2026) — closest thing to real GMV attribution [J]:**
  GMV **$116B (+32%)**, revenue **$3.6B (+34%)**; **AI-driven traffic and orders each ~3× YoY**;
  new-buyer orders from AI channels **~2×** other channels; **AI searches served from Shopify
  Catalog converted 2× vs scraped data**; **75% of AI-attributed orders came from outside the top
  100 categories**. Shopify explicitly framed **UCP, not ACP**, as its agent protocol.
  ⚠️ **Shopify did not disclose absolute AI-attributed GMV.**
  https://www.pymnts.com/earnings/2026/shopifys-ai-traffic-triples-as-shoppers-skip-the-search-bar/ ·
  https://www.retailtouchpoints.com/news/shopify-credits-ai-for-34-revenue-growth-in-q2-2026/620805/
  → *The "Catalog converts 2× vs scraped data" line is the single best argument that structured,
  agent-readable product data has measurable value.*
- **Cloudflare Radar (June 2026) [P]:** automated requests = **57.5% of HTML traffic** vs 42.5%
  human. **Shopping is the most-crawled category, holding ~31% of all AI crawling every month of
  2026.** Crawl-to-refer ratios: Anthropic ~**4,580:1** (down from ~23,951:1 in Q1), GPTBot
  **903.8:1**, Perplexity **192.9:1**, Googlebot **5.2:1**.
  ⚠️ Ratios surfaced via secondary blogs — verify against Radar directly before quoting.
  https://blog.cloudflare.com/ai-crawler-traffic-by-purpose-and-industry/
- **Similarweb (2026) [V/P]:** ChatGPT share of global generative-AI web traffic fell **~76% → ~53%
  YoY**; Gemini past **25%**. Gemini outbound referral traffic **+388% YoY** vs ChatGPT **+52%**.
  https://www.similarweb.com/blog/marketing/geo/gen-ai-stats/
- **Actual dollar size, narrowest definition:** eMarketer forecasts **$20.57B US retail spend in
  2026 via checkout completed inside an AI platform ≈ 1.5% of US e-commerce.** ⚠️ A *forecast*, not
  measurement — get the eMarketer original before use. **[?→verify]**
- ⚠️ **"1 in 5 Cyber Week orders touched an agent, ~$70B GMV"** — widely repeated, **original source
  not located. Do not cite.**
- **No data found:** any Q3 2026 (Jul–Aug) hard traffic/conversion print. Adobe's 19 Aug 2026 PDF
  exists but **timed out on every fetch** — retrieve manually:
  https://business.adobe.com/assets/pdfs/resources/sdk/ai-traffic-trends-report-august-2026/ai-traffic-trends-report-2026-08-19.pdf
- **No AOV comparison (AI vs organic) found anywhere** — Adobe reports revenue-per-visit, which
  conflates conversion and basket size.

---

## 3. Google UCP — momentum shifted, but nobody published a number

- **Capability timeline:** Checkout, Identity Linking, Order Management (Jan 2026); Cart + Product
  Discovery (Mar 2026); **Universal Cart** cross-retailer, BNPL via Affirm/Klarna inside Google Pay,
  YouTube Shopping checkout (May 2026). **[?]** verify against Google's own blog.
- **Universal Cart launch: 19–20 May 2026.** ⚠️ **Contradiction:** TechCrunch and DigitalCommerce360
  date it to **Google I/O, 19 May**; Search Engine Land to **Google Marketing Live, 20 May**. Both
  events occurred that week. **[J]**
  https://techcrunch.com/2026/05/19/googles-new-universal-cart-wants-to-follow-your-entire-shopping-journey-across-the-internet/ ·
  https://searchengineland.com/google-expands-universal-commerce-protocol-and-launches-new-agentic-shopping-tools-478113
- **Launch partners (8 named):** Nike, Sephora, Target, Ulta Beauty, Walmart, Wayfair + Shopify
  merchants Fenty and Steve Madden. Rollout US summer 2026 across Search + Gemini app; YouTube and
  Gmail later; then Canada, Australia, UK. **[J]**
  https://www.digitalcommerce360.com/2026/05/20/google-universal-cart-for-agentic-commerce/
- ⭐ **UCP Tech Council:** founded 2026 with Google, Shopify, Etsy, Target, Wayfair; expanded to
  **ten members on 24 Apr 2026** adding **Amazon, Meta, Microsoft, Salesforce and Stripe**.
  **If accurate this is the single most important structural fact in the landscape — Stripe and Meta
  sit on *both* ACP and UCP governance.** ⚠️ **[?] Sourced only from SEO blogs — verify before
  relying on it.**
- **Key structural claim:** a retailer already managing Google Shopping feeds can become UCP-enabled
  **with no code**, making UCP's addressable merchant base orders of magnitude larger than ACP's.
  **[?]** Plausible and consistent with Shopify's Catalog framing, but unverified.
- **No data found:** UCP merchant count, UCP-attributed GMV, or any Google disclosure of agentic
  checkout volume. Nothing surfaced in Q2 2026 Alphabet earnings.
- **Microsoft is on UCP too:** UCP Merchant Center + Copilot Checkout + Target loyalty integration.
  **[?]** verify.

---

## 4. Perplexity / Amazon / Microsoft — actual counts

- **Microsoft Copilot Checkout: >500,000 merchants**, US, in the Copilot mobile app. Launched
  **8 Jan 2026** with Copilot Checkout + Brand Agents; partner activation via **PayPal, Shopify,
  Stripe**; Shopify merchants **auto-enrolled after an opt-out window**. **[P/V]**
  https://about.ads.microsoft.com/en/blog/post/january-2026/conversations-that-convert-copilot-checkout-and-brand-agents
  ⚠️ **The 500k is a *reachable-merchant* number driven by Shopify auto-enrolment — not a count of
  merchants transacting. No transaction volume disclosed.**
- ⭐ **Amazon Rufus — the only large, quasi-audited agentic-commerce revenue number in existence:**
  **~$12B incremental annualized sales in 2025** (above the $10B pace signalled at Q3 2025),
  **>300M customers in 2025** (up from 250M at Nov 2025), MAU **+149% YoY**, conversational
  interactions **+210% YoY**. **[V/P]** Amazon-disclosed; "incremental" is Amazon's own attribution
  model. https://ppc.land/amazons-ai-shopping-assistant-drove-12-billion-in-sales-for-2025/
- **Rufus "Buy for Me"** (agentic checkout on third-party sites): **no transaction volume, no
  merchant count, no success rate published.** Flat gap.
- **Amazon CEO Andy Jassy (2026):** most AI shopping agents "fail to provide a satisfactory customer
  experience," lacking personalization and giving **inaccurate pricing and delivery estimates**.
  **[?]** relayed secondhand — find the earnings-call transcript; it is a quotable, quasi-independent
  knock on agent reliability.
- **Perplexity Comet: >3M MAU in Q1 2026**; iOS app hit #3 US App Store within 48h of 18 Mar 2026
  launch. **[?]**
- ⚠️ **Perplexity shopping: claimed ~$2B annualized GMV run-rate and 2M monthly active shoppers
  (Jul 2026)**, with Amazon-attributed GMV down **~30%** after Amazon cut Perplexity's real-time
  price/inventory access in Apr 2026. **[?] Single unverified aggregator, no Perplexity disclosure
  found. DO NOT CITE.** This is the largest number in the brief with the weakest sourcing.
  https://novadata.io/resources/news/perplexity-buy-now-agent-2m-shoppers-july-2026
- **Perplexity Merchant Program:** open to all Shopify merchants since Jan 2026, **0% commission**,
  PayPal checkout. Merchant count **not found**.

### ⭐ The legal spine of browser-agent commerce flipped twice
- **10 Mar 2026** — Judge Maxine Chesney (N.D. Cal.) granted Amazon a **preliminary injunction**
  blocking Comet from password-protected Amazon areas; found Amazon likely to win on CFAA +
  California §502, reasoning Comet acted **"with the Amazon user's permission, but without
  authorization by Amazon."** **[J]**
  https://www.cnbc.com/2026/03/10/amazon-wins-court-order-to-block-perplexitys-ai-shopping-agent.html ·
  https://www.geekwire.com/2026/judge-blocks-perplexitys-ai-bot-from-shopping-on-amazon-in-early-test-of-agentic-commerce/
- **4 Aug 2026** — the **Ninth Circuit vacated it**, holding that when a user directs the assistant,
  **it is *the user* accessing Amazon's computers**. **[J]**
  https://www.engadget.com/2230471/perplexity-has-successfully-overturned-amazon-injunction-on-its-ai-shopping-bot/ ·
  https://www.emarketer.com/content/perplexity-comet-amazon-ai-shopping-agents-ruling

> The distinction the district court drew — **permission from the user vs authorization from the
> merchant** — is exactly the gap a merchant-side policy engine occupies. The merchant currently has
> no mechanism to express authorization at all.

---

## 5. ⭐⭐ Can agents actually complete a purchase? Measured rates

### Academic, 2026, shopping-specific — the strongest evidence set **[A]**

| Benchmark | Date | Scale | Best measured result |
|---|---|---|---|
| **EComAgentBench** | 24 Jun 2026 | 662 tasks, real Amazon products/reviews, 100 tool calls, 7 models | **57.1%** overall accuracy for the strongest model; rubric satisfaction degrades from visible → hidden requirement sources. https://arxiv.org/abs/2606.17698 |
| **WebMall** | v3, 2026 | 91 tasks / 11 categories, 4 simulated shops, 4,421 real offers (Common Crawl), GPT-5.4 + Qwen 3.6 Plus | **Add-to-cart: 100%** (GPT-5.4, AX-tree). **End-to-end shopping workflow: 75%** (F1 84.26). **Cheapest-product search: 63.3%. Vague product search: 64.4%.** https://arxiv.org/html/2508.13024v3 |
| **ComboShoppingBench** | 10 Aug 2026 | 291 basket/coupon tasks, 11 agents × think/no-think | **61.2%** end-to-end (GPT-5.5-thinking) — despite 83.8% semantic, 92.4% response quality, 90.4% claim faithfulness, 83.8% rule-validation *individually*. **The intersection is what kills it.** https://arxiv.org/html/2608.09282 |
| **MMShopBench** | 31 Jul 2026 | 289 real-log multimodal multi-turn cases, 100k-product catalog | **Gemini-3.1-Pro-Preview 73.4%** (Judge@3); best open-source after SFT 67.5%; **same open model un-tuned: 5.9%.** https://arxiv.org/html/2607.29002 |
| **ShoppingBench** | 2026 | 3,310 instructions, 2.5M-product sandbox | SOTA models (e.g. GPT-4.1) **under 50%** absolute success. https://arxiv.org/abs/2508.04266 |
| **Online-Mind2Web** ("An Illusion of Progress?", OSU/Berkeley, COLM 2025) | 2025→ | 300 tasks, 136 live sites | **Operator 61% on live sites** vs **~90% claimed on WebVoyager** — headline finding is that WebVoyager-style scores **collapse in live settings.** https://arxiv.org/pdf/2504.01382 |

### ⚠️ Critical caveats on the leaderboards
- The Online-Mind2Web leaderboard now shows **Browser Use Cloud (bu-max) 97.0%**, GPT-5.4 native
  computer use 93.0%, ABP+Claude Opus 4.6 90.53%, TinyFish 90.0%. **The leaderboard itself warns**
  "Some rows are independently benchmarked and some are team-reported" — bu-max, GPT-5.4 and
  TinyFish are **self-reported**; only the ABP row published all 300 task results. **[V]**
  https://leaderboard.steel.dev/leaderboards/online-mind2web/
  **Do not treat 97% as an independent purchase-completion figure.** There is **no shopping-task
  breakdown**, and the benchmark **deliberately avoids irreversible real purchases.**
- **τ-bench is dead as a citation.** BenchLM's operator note: "0 sourced rows are currently
  displayable"; 38 raw numbers withheld for lack of source attachment and pass^k/domain labels; the
  upstream repo warns its **retail tasks are outdated** and points to τ³-bench. **[P]**
  https://benchlm.ai/benchmarks/tau-bench
  The circulating retail pass^k figures (Claude-3.5-Sonnet 0.692→0.462 across pass^1→pass^4; GPT-4o
  0.604→0.383) are **2024 models** — **the *shape* (reliability decaying ~30% from 1 to 4 trials) is
  the transferable finding, not the levels.**
- **WebArena:** record single-agent completion **61.7%** (IBM CUGA, Feb 2025); **human baseline 78%.**
  **[A]** https://www.emergentmind.com/topics/webarena-benchmark

### ⭐ Reported failure modes, verbatim from the papers
- **Constraint accumulation** — per-criterion failure rates stay modest (**4.8–6.6%**) but task-level
  pass **collapses as criteria multiply** (ComboShoppingBench).
- **Cross-item reasoning** is the highest-failure semantic category — i.e. **multi-item carts, the
  exact thing OpenAI cited as unbuildable.**
- **Suboptimal coupon/discount selection:** 15% of no-think cases, 8% with thinking.
- **Reasoning can hurt:** Qwen3.6-27B **lost more tasks than it recovered** with thinking enabled.
- **Hidden-intent degradation:** accuracy falls as requirements move visible query → profile →
  clarification (EComAgentBench).
- **Stale/invisible element loops:** vision-only Qwen agents "repeatedly emit the same click action
  against an invisible or stale element until the step budget is exhausted." **Accessibility-tree
  access is essential; adding vision *on top of* AX-tree sometimes degrades performance** (WebMall).
- **Selection-retrieval mismatch** — valid candidates retrieved then discarded at final ranking
  (MMShopBench).
- ⭐⭐ **Comparison shopping is harder than checkout.** Across WebMall, the mechanical act of
  add-to-cart/checkout is **near-solved (100%)**; finding the cheapest offer across four shops is
  **~63%**. **The bottleneck is decision quality, not form-filling.**

### Journalist / hands-on
- ⚠️ **"48% failure rate" study** (UW + Ohio State + others, ~Aug 2026): 100 standardized shopping
  tasks × 600 trials against Operator, Project Mariner, Perplexity Shopping Agent, WebVoyager
  baseline. Failure modes: hallucinated product pages for nonexistent items; wrong product/size
  despite reaching the right site; navigation failure; misidentified prices leading to overpayment;
  stalling at paywalls/pop-ups. **Primary paper and press release could not be located** — only a
  forum summary with no citation. **Treat as unverified. Highest-value item to chase.**
- ⭐⭐ **Guardio Labs "Scamlexity"** (Aug 2025, re-circulated through 2026) — **the single best
  hands-on checkout failure.** Researchers stood up a **fake Walmart** and told **Comet** to buy an
  Apple Watch. Comet **ignored a wonky logo and a wrong URL, went to checkout, auto-filled card and
  address, and completed the purchase without asking the user to confirm.** It also auto-filled
  credentials into a **live in-the-wild Wells Fargo phishing page**, and was induced to download a
  file via prompt injection hidden in a fake CAPTCHA ("PromptFix"). **[P/J]**
  https://guard.io/labs/scamlexity-we-put-agentic-ai-browsers-to-the-test-they-clicked-they-paid-they-failed ·
  https://www.itnews.com.au/news/ai-browsers-fooled-by-phishing-and-fake-stores-619746
  ⚠️ **No aggregate hit-rate — 3 scenarios, not a sample.**
- **"One Polluted Page Is Enough: Evaluating Web Content Pollution in Generative Recommenders"**
  (Luo & Chen, Jun 2026) — a **single** manipulated page can make an AI assistant promote a fake
  product. **[A]** via https://techxplore.com/news/2026-06-fake-web-page-ai-bots.html — find the arXiv id.
- **Wired:** an agent took **45 seconds to add eggs to a cart**. **WSJ:** an AI-run vending machine
  lost money and stocked itself with a live fish. **[?]** both worth chasing to original.
- **No data found:** any Which?, Consumer Reports or Stiftung Warentest systematic agent-checkout
  test. Searched three ways; **nothing exists as of Sep 2026.**

---

## 6. Production error rates, duplicates, wrong items — the biggest hole in the evidence base

- ⭐⭐ **No public production agent-purchase error rate exists. Anywhere.** No duplicate-purchase
  rate, no wrong-item rate, no agent-specific chargeback rate, from any platform, processor or
  network. Searched five ways. **This is a genuine, citable gap.**
- ⭐ **The strongest available proxy is liability being *priced* rather than *measured*.**
  **14 Apr 2026**, American Express launched the **ACE Developer Kit** with **Amex Agent Purchase
  Protection** — an industry-first commitment to **cover erroneous purchases made by registered AI
  agents** on its network. Architecture: verified agents get issued payment credentials, cardholders
  authenticated before the agent may transact; the kit provides agent registration, account
  enablement, intent intelligence, payment credentials and cart context. Launch partners **Adyen,
  Stripe, PayPal, Fiserv** + merchants **Delta, Expedia, Hilton**. **[P]**
  https://www.americanexpress.com/en-us/newsroom/articles/innovation/american-express-debuts-agentic-commerce-experiences--ace--devel.html ·
  **[J]** https://fortune.com/2026/04/14/american-express-ai-payments-developers-purchase-protection/
  **Amex published no expected error rate and no reserve figure. They are insuring a risk nobody has
  sized.**
- ⭐ **Signifyd State of Fraud 2026 [V/P]:** e-commerce fraud pressure **+33% YoY** over the first
  four months of 2026. Signifyd's characterization of agentic fraud: it presents as **"clean, fast,
  and successful transactions"** — i.e. **it does not trip legacy fraud models, because agentic
  checkout strips the behavioral signals those models depend on.**
  https://www.signifyd.com/blog/agentic-commerce-fraud/
- **False-decline baseline (pre-agentic, context) [V]:** issuers decline ~**1 in 10** e-commerce
  dollars at auth (Riskified); **30–70%** of merchant-declined orders are false positives; **~27%**
  of loyal customers never return after one.
- ⭐ **Consumer tolerance for a single mistake:** ACI Worldwide — **six in ten UK consumers would
  stop using an AI shopping agent after ONE mistake.** **[P]**
  https://investor.aciworldwide.com/news-releases/news-release-details/six-ten-uk-consumers-would-stop-using-ai-shopping-agent-after
  ⚠️ fetch timed out; headline only — **get n and field dates.**
- **Riskified Q1 2026 [V]:** 61.5% have used AI for product discovery; **55.0% not comfortable with
  AI agents purchasing on their behalf**; 53.9% think AI raises fraud risk.
  ⚠️ **Do not stack this with Gartner's 11% or Adobe's 79%** — the three measure different things
  (delegate the *decision* vs delegate the *transaction* vs feel confident using AI as an *advisor*).
- **Fake-shop base rate rising [V/J]:** Gen blocked **114.2M e-shop scam attacks in H1 2026**;
  fake-shop scams **more than doubled** H1 YoY. Relevant because Scamlexity shows agents don't filter
  these. https://securitybrief.co.uk/story/fake-shop-scams-more-than-doubled-in-first-half-of-2026
- ⚠️ **Contradiction to note:** a vendor blog claims merchants with "agentic storefronts" see **20%
  fewer returns**, and Adobe reports 69% of AI-assisted buyers say they're less likely to return —
  both cut **against** the wrong-item-purchase thesis. Both are self-interested/self-reported.
  **No independent return-rate comparison for agent-completed orders exists.**

---

## Gaps worth stating plainly

1. **No public production error/duplicate/wrong-item rate for agent purchases.** Anywhere. **Amex is
   insuring a risk nobody has sized.**
2. **No UCP merchant count and no UCP GMV** — despite UCP being the presumptive winner post-March.
3. **No absolute agentic GMV from anyone.** Shopify gives 3× growth, not dollars; eMarketer's
   $20.57B / 1.5% is a forecast; the "$70B Cyber Week" figure has no traceable origin.
4. **No AOV comparison** (AI-referred vs organic) in any source.
5. **No Q3 2026 (Jul–Aug) measurement retrieved.** Adobe's 19 Aug 2026 PDF exists but would not fetch.
6. **Two load-bearing claims need primary verification before use:** the UCP Tech Council 10-member
   composition (24 Apr 2026), and the "48% failure / 600 trials" study.
7. ⭐⭐ **Every benchmark above avoids real irreversible purchases.** WebMall's 100% add-to-cart is a
   **simulated** shop. **There is no published measurement of agents completing real, money-moving
   checkouts on live merchant sites** — the closest thing is **Guardio getting one to pay a
   fraudster.**
