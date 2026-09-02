# Protocols — implementation-level technical brief

As of 2 September 2026. Every claim sourced from the shipped specs. **Silences flagged
explicitly** — a spec's refusal to define something is a finding, not a gap in the research.

---

## 0. ⚠️ Corrections to our earlier baseline

Four facts recorded in [01-landscape-initial.md](01-landscape-initial.md) and
[04-trust-fraud-liability.md](04-trust-fraud-liability.md) are **stale against the shipped
specs**. These supersede them.

| What we recorded earlier | Actual, as of today |
|---|---|
| "AP2 Mandates are W3C Verifiable Credentials with issuer/subject/payload/signature" | AP2 mandates are **SD-JWT VCs (RFC 9901)**, *not* W3C VC-JSON-LD. Claims are `vct`, `constraints`, `cnf`, `iat`, `exp`, `_sd_alg`. Key binding is RFC 7800 `cnf`. |
| "Three types: Intent, Cart, Payment" | The shipped SDK has **`CheckoutMandate` / `OpenCheckoutMandate` / `PaymentMandate` / `OpenPaymentMandate`** plus `CheckoutReceipt` / `PaymentReceipt`. `vct` values: `mandate.checkout.1`, `mandate.checkout.open.1`, `mandate.payment.1`, `mandate.payment.open.1`. **`IntentMandate` no longer exists** — grep of UCP and AP2 returns zero hits. "Cart" → "Checkout". |
| "ACP uses Shared Payment Tokens plus OAuth 2.0 delegation" | The scoping object is named **`Allowance`**. And `delegate_authentication` is **3-D Secure 2, browser channel only** — *"This specification covers: 3D Secure 2 (3DS2) authentication only"* (`rfcs/rfc.delegate_authentication.md:19`). **There is no OAuth 2.0 in the released ACP spec.** Stripe's marketing page claims OAuth; the spec does not contain it. |
| (implied) "UCP is Google's spec" | UCP is **not Google's**. It lives at `github.com/Universal-Commerce-Protocol/ucp` (Apache-2.0, "UCP Authors": Google, Amazon, Etsy, Meta, Microsoft, Salesforce, **Shopify, Stripe**, Target, Walmart, Wayfair). `developers.google.com/merchant/ucp` is one narrower Google-surface *profile* of it, pinned a release behind. |

### ⭐⭐ And the structural fact that reshapes the field: AP2 and UCP have merged at the schema level

- The AP2 Python SDK ships `code/sdk/schemas/ucp/types/{checkout,line_item,buyer,total,link,message}.json`.
- `ap2/types/item.json` is annotated *"Matches UCP types/item.json (2026-04-08)"*.
- `ucp/types/checkout.json` says *"UCP Checkout object (dev.ucp.shopping.checkout 2026-04-08). The
  merchant field is an AP2 extension for mandate binding."*
- UCP carries AP2 as an optional negotiated capability `dev.ucp.common.payment.ap2_mandate`.

**→ AP2 is the credential layer; UCP is the commerce object layer.** They are not competitors.

**Shopify has migrated onto UCP and deprecated Storefront MCP cart tools — legacy support ended
31 August 2026, two days before this brief.**

So the real field is **not five peers**. It is:

| Camp | Composition |
|---|---|
| **UCP + AP2** | Google, Shopify, Stripe, Amazon, Meta, Microsoft, Salesforce, Etsy, Target, Walmart, Wayfair |
| **ACP** | OpenAI, Stripe, Meta |
| **x402** | crypto-native, Coinbase |
| **Card-network agent auth** | Visa, Mastercard — **no commerce objects at all** |

…with all four converging on **RFC 9421 HTTP Message Signatures** as the agent-identity primitive.

---

## 1. ACP — Agentic Commerce Protocol (OpenAI / Stripe / Meta)

Spec version **`2026-04-17`**.
`github.com/agentic-commerce-protocol/agentic-commerce-protocol/tree/main/spec/2026-04-17`

### 1.1 What the merchant must expose

Discovery at **`/.well-known/acp.json`** at origin root, unauthenticated
(`rfcs/rfc.discovery.md:96-99`). Returns `DiscoveryResponse`:
- required `protocol` (`{name:"acp", version, supported_versions[], documentation_url}`),
  `api_base_url`, `transports[]` (`rest`|`mcp`), `capabilities`
- `capabilities.services[]` is a **closed enum**: `checkout`, `orders`, `delegate_payment`, `carts`
- optional `capabilities.extensions[]`, `intervention_types[]`
  (`3ds`|`biometric`|`address_verification`), `supported_currencies[]`, `supported_locales[]`

| Service | Operations |
|---|---|
| Checkout | `POST /checkout_sessions`, `GET\|POST /checkout_sessions/{id}`, `POST /checkout_sessions/{id}/complete`, `POST /checkout_sessions/{id}/cancel` |
| Cart | `POST /carts`, `GET /carts/{id}`, `POST /carts/{id}` (update), `POST /carts/{id}/cancel` |
| Feed | `POST /feeds`, `GET /feeds/{id}`, `GET /feeds/{id}/products`, `PATCH /feeds/{id}/products` |
| Delegate payment | `POST /agentic_commerce/delegate_payment` |
| Delegate auth (3DS) | `POST /delegate_authentication`, `POST /delegate_authentication/{id}/authenticate`, `GET /delegate_authentication/{id}` |

**Required headers on every call:** `Authorization: Bearer`, `Content-Type`, `API-Version`
(YYYY-MM-DD), and `Idempotency-Key` on all POSTs — *"MUST be present on all POST requests. Opaque
string, max 255 characters. UUID v4 recommended. Scoped to authenticated identity + endpoint."*
Optional: `Accept-Language`, `User-Agent` (example: `ChatGPT/2.0 (Mac OS X 15.0.1; arm64; build 0)`),
`Request-Id`, `Signature`, `Timestamp`.

**⭐ Product feed schema (`schema.feed.json`) — ACP is the only protocol here with a real,
dedicated catalog schema:**
- `Product`: **required** `id`, `variants[]`; optional `title`, `description`, `url`, `media[]`
- `Variant`: **required** `id`, `title`; optional `description`, `url`, `barcodes[]`, `price`,
  `list_price`, `unit_price`, `availability`, `categories[]`, `condition`, `variant_options[]`,
  `media[]`, `seller`, `marketplace`
- `Price`: **required** `amount` (integer minor units), `currency`
- `Availability`: `available` (bool), `status` (open string; *"Known values include in_stock,
  limited_stock, backorder, preorder, out_of_stock, and discontinued"*)
- `Media`: **required** `type`, `url`; optional `alt_text`, `width`, `height`
- `Barcode`: **required** `type`, `value` (*"such as GTIN, UPC, or EAN"*)
- `Category`: **required** `value`; optional `taxonomy` (*"such as google_product_category,
  shopify, or merchant"*)
- `UnitPrice`: **required** `amount`, `currency`, `measure{value,unit}`, `reference{value,unit}` —
  EU unit-pricing compliance
- `Seller`: `name`, `links[]`; `Link.type` *"such as privacy_policy, terms_of_service,
  refund_policy, shipping_policy, or faq"*
- `FeedMetadata`: **required** `id`; optional `target_country`, `updated_at`

Offline ingestion: **`metadata.json`** + **`products.jsonl`** (one Product per line). *"File
ingestion replaces the full product set. Partial updates are only supported through
`PATCH /feeds/{id}/products`."*

**Webhook (merchant → agent), required:** `POST /agentic_checkout/webhooks/order_events`. Header
**`Merchant-Signature`** is `required: true`, pattern `^t=\d+,v1=[a-fA-F0-9]{64}$`, described as
*"HMAC-SHA256(timestamp + "." + raw_body, secret). Return 401 if invalid."* Event `type`:
`order_create`, `order_update`. *"The `data` field MUST contain the full Order object (not
incremental deltas)."*

### 1.2 Authorization model

`Allowance` (`schema.delegate_payment.json`) — **all six fields required**:

```
reason: "one_time"   (enum, single value)
max_amount: integer
currency: string
checkout_session_id: string
merchant_id: string
expires_at: string
```

**That is the entire scope-and-limit vocabulary:** one amount cap, one merchant, one session, one
expiry, single-use. `DelegatePaymentRequest` requires `payment_method`, `allowance`,
`risk_signals[]`, `metadata`. `PaymentMethodCard` carries `card_number_type` (`fpan`|`network_token`),
`cryptogram`, `eci_value`, `checks_performed[]` (`avs`|`cvv`|`ani`|`auth0`),
`display_card_funding_type`.

**Revocation: not defined.** No revoke endpoint, no status transition for a delegated token.
**Expiry is the only kill switch.** `rfc.delegate_payment.md:17` out of scope: *"PSP-specific
authorization/capture, multi-use tokens beyond allowance, refund semantics."*

### 1.3 Agent identity verification

**Bearer token only.** `security: bearerAuth`, `Authorization: Bearer api_key_123`. **No signed
requests, no key discovery, no agent registry, no RFC 9421.** `User-Agent` is `required: false` and
purely descriptive. **Agent identity in ACP is a pre-shared API key — a bilateral business
relationship, not a protocol.**

### 1.4 Dispute / liability / audit

Refunds and disputes are **reportable state, not operations**. `Adjustment` (required `id`, `type`,
`occurred_at`, `status`): *"Defined values: 'refund', 'credit', 'return', 'exchange',
'price_adjustment', 'cancellation', 'dispute'… **'dispute' covers chargebacks**."* `Total.type`
gained `amount_refunded`. Changelog records the decision: *"merge `chargeback` into `dispute`"* and
*"removed `refunds[]` in favor of `adjustments[]`"*.

**There is no refund endpoint, no dispute endpoint, no evidence-retention requirement, and no
liability allocation anywhere in ACP.** `rfc.agentic_checkout.md:24` out of scope: *"PSP
authorization/capture semantics, returns/exchanges workflows, tax configuration, fraud modeling
details."*

The only audit primitive is `IntentTrace` (**unreleased**), required `reason_code` from enum
`price_sensitivity`, `shipping_cost`, `shipping_speed`, `product_fit`, `trust_security`,
`returns_policy`, `payment_options`, `comparison`, `timing_deferred`, `other` — **abandonment
telemetry, not dispute evidence**.

---

## 2. AP2 — Agent Payments Protocol (Google)

`github.com/google-agentic-commerce/AP2`, `docs/ap2/*.md`, `code/sdk/python/ap2/`.
Schemas dated **2026-04-28**.

### 2.1 What the merchant must expose

**Nothing.** AP2 defines no endpoints, no catalog API, no cart lifecycle. It is a credential format
plus verification rules, transported over A2A / MCP / x402 or embedded in UCP. The merchant's
obligation is a **verification duty**, not a surface: *"The Merchant MUST receive an appropriate
Checkout Mandate from a Shopping Agent before completing the Checkout"* (`specification.md`).

The commerce objects AP2 binds to are **UCP's**: `Checkout` (required `id`, `line_items`, `status`,
`currency`, `totals`, `links`), `LineItem` (required `id`, `item`, `quantity`, `totals`), and `Item`
— required `id`, `title`, `price`; optional `image_url`. ⚠️ **That is the entire AP2/UCP-shared
product shape at mandate level: four fields.**

### 2.2 ⭐ Authorization model — the richest of any protocol

Mandates are **SD-JWT VCs**, two-state:
- **Open** — user-signed, unbound, carries `constraints[]` + `cnf` (RFC 7800 PoP key endorsing the agent)
- **Closed** — bound to one transaction via Key Binding JWT and `sd_hash`

`CheckoutMandate`: `vct="mandate.checkout.1"`, `checkout_jwt` (base64url merchant-signed JWT, marked
`x-selectively-disclosable-field`), `checkout_hash`, `iat`, `exp`.
`PaymentMandate`: `vct="mandate.payment.1"`, `transaction_id` (= hash of `checkout_jwt`, **the
cross-layer binding**), `payee`, `pisp`, `payment_amount`, `payment_instrument`, `execution_date`,
`risk_data`, `iat`, `exp`.

**Constraint vocabulary** (`open_payment_mandate.json`, `open_checkout_mandate.json`) — every entry
has a `type` discriminator:

| `type` | Fields |
|---|---|
| `payment.amount_range` | `currency`, `max` (req), `min` |
| `payment.allowed_payees` | `allowed[]` of `Merchant{id,name,website}` |
| `payment.allowed_payment_instruments` | `allowed[]` |
| `payment.allowed_pisps` | `allowed[]` |
| `payment.agent_recurrence` | `frequency` (`ON_DEMAND`\|`DAILY`\|`WEEKLY`\|`BIWEEKLY`\|`MONTHLY`\|`QUARTERLY`\|`ANNUALLY`), `max_occurrences` |
| `payment.budget` | `max`, `currency` — cumulative cap across recurrences |
| `payment.execution_date` | `not_before`, `not_after` |
| `payment.reference` | `conditional_transaction_id` |
| `checkout.allowed_merchants` | `allowed[]` |
| `checkout.line_items` | `items[]` of `LineItemRequirements{id, acceptable_items[], quantity}` |

⭐ Constraints are **extensible with a fail-closed rule**: *"Any unknown Constraints MUST be treated
as failing evaluation."* Reference evaluators ship in `ap2/sdk/constraints.py` (555 LOC, one class
per constraint type). Selective disclosure hides constraint contents — `allowed[]` arrays are
`x-selectively-disclosable-array`, so an agent reveals only the merchant it is actually using.

**Revocation: AP2 contains ZERO occurrences of "revoke" or "revocation"** across all docs and SDK
files (grepped). The substitute is a `MandateReceipt` (Verifier-signed JWT: `iss`, `result` ∈
`{success,error}`, `reference`, `error`, `error_description`) plus a self-policing rule: *"The agent
reduces the scope of the open mandate based on the receipt, often preventing future presentations
entirely."* ⚠️ **That is agent-side honesty, not verifier-enforced revocation. A stolen open mandate
remains valid until `exp`.** Error codes: `invalid_credential`, `unresolved_constraint`,
`invalid_mandate`, `mandates_not_supported`.

### 2.3 Agent identity verification

Two models (`agent_authorization.md`):
1. **User Credential** — pre-issued VC, presented via **OpenID4VP**
2. **Trusted Agent Provider** — no pre-issued credential; the Agent Provider signs from a "Trusted
   Surface" and *"MUST ensure that the Agent is not able to access the Agent Provider signing key,
   or use it without the Trusted Surface"*

Agent identity is proven by **possession of the `cnf` key the user endorsed**, not by a registry or
attestation. **No AP2 agent directory. No RFC 9421** — AP2 is transport-agnostic and lives in the body.

### 2.4 Dispute / liability / audit — most developed of any protocol, and still incomplete

`specification.md` §"Dispute Evidence": *"the Checkout Mandate and Receipt, and Payment Mandate and
Receipt can be brought together to provide a non-repudiable picture of the transaction."* Named
holders: Shopping Agent, Merchant (checkout side); Shopping Agent, Credential Provider, Network,
Merchant Payment Processor (payment side).

A normative **five-step dispute verification algorithm** exists (recompute `checkout_jwt` hash;
Checkout Receipt `reference` MUST match hash of closed Checkout Mandate; same for payment; then
*"the information contained in the Checkout Mandate and Payment Mandate is able to be used as
evidence as to what the user, and each role saw"*).

But the surrounding machinery is explicitly deferred: *"Specific details of how this is used for
dispute resolution, **retention, and retrieval requirements are outside the scope of this
specification**."* And an admitted gap: *"Providing an automated method to retrieve the Checkout
Mandate… would provide substantial utility to the ecosystem. The exact details are outside the scope
of the current version, but would be done by using the Payment Mandate `transaction_id` as the
key."*

⚠️ **No retention period, no retrieval API, no liability allocation.** Agent-to-agent delegation is
also *"outside the scope of the current specification."*

---

## 3. UCP — Universal Commerce Protocol (consortium; Shopify's chosen path)

Releases `v2026-01-11`, `v2026-01-23`, `v2026-04-08`, **`v2026-08-25`** (current). Google is pinned
to `2026-04-08`.

### 3.1 What the merchant must expose

**Profile at `/.well-known/ucp`** (no extension), *"must be publicly accessible and not require any
authentication"*. Top level requires `ucp`; optional `keys`.

`ucp` requires **`version`**, **`services`**, **`payment_handlers`**; optional `capabilities`,
`supported_versions`, `map_order`, `status`. All three maps keyed by reverse-DNS (`dev.ucp.shopping`,
`dev.ucp.shopping.checkout`, `com.google.pay`). Shared entity base: `version` (always required),
`spec`, `schema`, `id`, `config`. `service` requires `transport` ∈ `rest`|`mcp`|`a2a`|`embedded`
plus `endpoint`.

⚠️ **Breaking rename Google's docs have not caught up to:** the key field was **`signing_keys`** in
`2026-04-08` (`source/discovery/profile_schema.json`), renamed to **`keys`** in `2026-08-25`
(`source/schemas/profile.json`), RSA dropped, `OKP`/Ed25519 added. **Google's published example
still emits `signing_keys`.**

`keys[]` items require `kid`, `kty` (`EC`|`OKP`, open vocabulary); `crv`/`x`/`y` conditional; *"For
keys used in dual-audience (Web Bot Auth) signatures, the kid MUST be the key's JWK SHA-256
Thumbprint (RFC 7638)"*. Private members schema-forbidden.

Normative caching: *"MUST include a `Cache-Control` header with `public` and `max-age` of at least
60 seconds, and MUST NOT be served with `private`, `no-store`, or `no-cache`"*. And: *"Profiles MUST
NOT contain per-transaction or per-session configuration."*

**13 REST operations**, identical names over MCP:
`POST /checkout-sessions`, `GET|PUT /checkout-sessions/{id}`,
`POST /checkout-sessions/{id}/{complete,cancel}`; `POST /carts`, `GET|PUT /carts/{id}`,
`POST /carts/{id}/cancel`; `POST /catalog/{search,lookup,product}`; `GET /orders/{id}`. Plus
`POST /locations/{search,lookup}`.

⭐ **Required headers: `UCP-Agent`, `Idempotency-Key`, `Request-Id`.** Critically,
**`Signature`/`Signature-Input`/`Content-Digest` are `required: false`** — **signing is opt-in while
agent self-declaration is mandatory.**

**Catalog schema (`shopping/types/product.json`) — richest of any protocol:**
- `Product` required: `id` (*"Global ID (GID)"*), `title`, `description`, `price_range`, `variants[]`
  (minItems 1). Optional: `handle`, `url`, `categories[]`, `list_price_range`, `media[]`, `options[]`,
  `rating`, `tags[]`, `metadata`
- `Variant` required: `id` (*"Used as `item.id` in checkout"*), `title`, `description`, `price`.
  Optional: `sku`, `barcodes[]`, `handle`, `url`, `categories`, `quantity_unit`, `list_price`,
  `unit_price`, `availability`, `options[]`, `media`, `rating`, `tags`, `metadata`, `seller`
- `Item` (checkout-time) required `id`, `title`, `price` — but with **direction annotations**:
  `title`, `price`, `unit_price`, `image_url` are `ucp_request: "omit"`. **Only `id` is
  agent-supplied.**

⭐ UCP's directional mechanism is a custom annotation **`ucp_request` / `ucp_response`** ∈
`"omit"`|`"optional"`|`"required"`, or an object keyed `create`/`update`/`complete`. A field can be
**required in a response and forbidden in a request**. No counterpart in ACP.

Cart: `line_items` *"Full replacement on update"* (PUT semantics). Checkout `status` enum:
`incomplete`, `requires_escalation`, `ready_for_complete`, `complete_in_progress`, `completed`,
`canceled`. `expires_at`: *"Default TTL is 6 hours from creation if not sent."* `links` is
*"Mandatory for legal compliance."*

Orders are read-only over HTTP; updates flow **outbound** via merchant→platform webhook
(`webhook_url` required in the platform schema), standardwebhooks.com headers
`Webhook-Timestamp`/`Webhook-Id`, and *"Webhook notifications MUST be signed."*

⚠️ **No product feed schema, no schema.org mapping, no `gtin`, no Merchant Center attributes in the
open spec.** The only taxonomy hook is `Category.taxonomy` (open string; well-known
`google_product_category`|`shopify`|`merchant`). Google's feed tie-in
(`native_commerce(checkout_eligibility)`, `merchant_item_id`, `consumer_notice`) lives **outside
UCP**, in Merchant Center.

### 3.2 Authorization model — two axes, neither mandatory

**(a) Baseline: buyer intent is not cryptographically proven at all.** `buyer.json` is
`{first_name, last_name, email, phone_number}` with **no required fields and no proof**. No intent
token, no scope, no limit, no TTL at the buyer layer. `signals.json` is explicitly *not* proof:
*"Values MUST NOT be buyer-asserted claims."*

**(b) Optional `dev.ucp.common.payment.ap2_mandate`:**

| Field | Format |
|---|---|
| `ap2.merchant_authorization` | **JWS Detached Content** (RFC 7515 App. F), `^[A-Za-z0-9_-]+\.\.[A-Za-z0-9_-]+$`, `alg` ES256/384/512 + `kid`, signing the JCS-canonicalized checkout excluding `ap2` |
| `ap2.checkout_mandate` | **SD-JWT+kb**, `complete: "required"` |
| `payment.instruments[*].credential.token` | SD-JWT-VC `payment_mandate` |

Nested binding: *"the platform's signature covers the business's signature."* Canonicalization is
**JCS (RFC 8785)** for mandates, raw bytes for `Content-Digest`.

UCP defines **placement only**: *"The mandate credential structure (claims, selective disclosure,
key binding) is defined by the AP2 Protocol Specification."* Consequently **there is no
`max_amount`, no `allowed_categories`, no `valid_until` in any UCP schema.** Errors:
`mandate_required`, `agent_missing_key`, `mandate_invalid_signature`, `mandate_expired`,
`mandate_scope_mismatch`, `merchant_authorization_invalid`, `merchant_authorization_missing`.
⚠️ Note `mandate_scope_mismatch` means *"bound to a different checkout"* — **"scope" means resource
binding, not spend authority.**

**Revocation:** nothing at the mandate layer. Two substitutes: **key rotation** (*"Key rotation…
provides the mechanism for invalidating old signatures"*; 90-day SHOULD, ≥7-day grace, *"A key still
listed in `keys[]` continues to verify"*), and **OAuth RFC 7009 revocation** for identity-linked
sessions (`revocation_endpoint` MUST; *"Businesses MUST reject subsequent requests that present
revoked tokens"*; does not propagate across the IdP chain).

**Replay protection is not at the signature layer:** *"UCP handles replay protection at the business
layer through idempotency keys, not at the signature layer."* `Idempotency-Key` ≥128 bits, ≥24h
storage, mismatched payload → 409, storage failure → **fail closed with 503**. RFC 9421 `created` is
OPTIONAL for default UCP signatures.

### 3.3 ⭐ Agent identity verification — the most complete of any commerce protocol

**RFC 9421 + profile-published JWKS. No registry, no attestation, no trust list.**

`UCP-Agent` (RFC 8941 Dictionary) always required; key `profile` REQUIRED, quoted HTTPS URL, *"For
business profiles, URL MUST point to `/.well-known/ucp`; platform profile URLs are not
path-constrained"*. Verifier fetches that profile and matches `Signature-Input`'s `keyid` to a `kid`
in `keys[]`.

Signed components: `@method`, `@authority` (*"prevents cross-host relay"*), `@path` required; then
conditionally `@query`, `ucp-agent`, `signature-agent`, `idempotency-key`, `content-digest`,
`content-type`. `Content-Digest` MUST use `sha-256`.

**Web Bot Auth dual-audience signature** — one key, one signing operation, one signature satisfying
both a UCP verifier (via `UCP-Agent`) and a WBA verifier (via `Signature-Agent`). Opt-in requires:
carry `Signature-Agent` *alongside* `UCP-Agent`, sign the `signature-agent` component, use RFC 7638
thumbprint as `keyid`, add `created`, `expires`, `tag="web-bot-auth"`. `Signature-Agent`'s `type`
param selects `jwks_uri`|`cimd`|`directory`. *"The `tag` is a hint, not a gate."* Request-scoped only.

Spec-verbatim wire example:

```
UCP-Agent: profile="https://platform.example/.well-known/ucp"
Signature-Agent: sig1="https://platform.example/.well-known/ucp";type=jwks_uri
Signature-Input: sig1=("@method" "@authority" "@path" "signature-agent";key="sig1" "ucp-agent" "idempotency-key" "content-digest" "content-type");keyid="poqkLGiymh_W0uP6PZFw-dvez3QJT5SolqXBCW38r0U";created=1738617600;expires=1738621200;tag="web-bot-auth"
```

Alternatives are co-equal: *"HTTP Message Signatures are the only mechanism that enables
permissionless interaction"* — OAuth 2.0, API keys, mTLS all listed as pre-established equivalents.
`User-Agent` is `required: false`.

### 3.4 Dispute / liability / audit

⭐ **Liability is assigned in exactly one sentence, then abandoned.** Glossary: *"**Business** — The
entity selling goods or services. In UCP, they act as the **Merchant of Record (MoR)**, retaining
financial liability and ownership of the order."*

`order.adjustments[]` is the only refund/dispute structure and is **read-only reporting**. Required
`id`, `type`, `occurred_at`, `status` (`pending`|`completed`|`failed`). ⚠️ **`type` is an open string
with no enum:** *"Typically money-related like: `refund`, `return`, `credit`, `price_adjustment`,
`dispute`, `cancellation`. Can be any value that makes sense for the merchant's business."*
`totals[]` negative for money returned. `policies[]` (required `type`, `description`; well-known
`dev.ucp.shopping.policy.return`, `.warranty`; `applies_to[]` are RFC 9535 JSONPaths) are captured on
the order as *"a durable record"*.

**Explicit silences:** no refund/dispute/chargeback endpoint (none of the 13 operations mutates an
adjustment); **no evidence-retention requirement anywhere** — the only retention MUST in the whole
spec is a *privacy* one about location data; no representment format, no evidence-package schema, no
liability-shift rules, no allocation of loss between platform and merchant. Only durability numbers
in the spec: idempotency ≥24h, key-rotation grace ≥7 days. A `feat/policy-return-extension` branch
exists — **in flight, not released.**

---

## 4. x402 (Coinbase)

Spec **v2** (`specs/x402-specification-v2.md`); v1 is legacy.

### 4.1 What the merchant must expose

No catalog, no cart, no order, no product schema — ⚠️ **x402 has no commerce object model
whatsoever.** It is a paywall on an HTTP resource. Server returns `402` with header
**`PAYMENT-REQUIRED`** (v2 renamed from v1's `X-PAYMENT`), client replies with
**`PAYMENT-SIGNATURE`**, server returns **`PAYMENT-RESPONSE`** — all base64-encoded JSON.
*"Response bodies are a server implementation concern. All x402 protocol information is communicated
through headers."*

- `PaymentRequired`: required `x402Version` (must be 2), `resource`, `accepts[]`; optional `error`,
  `extensions`
- `PaymentRequirements`: required `scheme`, `network` (CAIP-2), `amount` (atomic units, string),
  `asset`, `payTo`, `maxTimeoutSeconds`; optional `extra`
- `ResourceInfo`: required `url`; optional `description`, `mimeType`. ⚠️ **`ResourceInfo` is the
  entire "catalog": a URL, a sentence, and a MIME type.**
- `PaymentPayload`: required `x402Version`, `accepted`, `payload`; optional `resource`, `extensions`
- `exact`/EVM `payload`: `signature` (EIP-712) + `authorization{from, to, value, validAfter,
  validBefore, nonce}` (EIP-3009)
- `SettleResponse`: required `success`, `transaction`, `network`; optional `errorReason`, `payer`,
  `amount`, `extensions`. `VerifyResponse`: required `isValid`; optional `invalidReason`, `payer`
- Facilitator: `POST /verify`, `POST /settle` (plus `/supported`)

### 4.2 Authorization model

`validAfter`/`validBefore` are the TTL; `value` is the amount; `nonce` (32 bytes) is replay
protection. The **`upto` scheme** adds a variable cap: *"authorizes a transfer of up to a maximum
amount… The settled `amount` MUST be `<=` the authorized maximum"*, with `amount` being
**phase-dependent** (max at verify, actual at settle).

**Complete scope vocabulary: one amount ceiling, one recipient address, one time window.** No
merchant identity beyond `payTo`, no category, no recurrence, no budget.

### 4.3 Agent identity verification

Core protocol: **none** — identity is a wallet address. The optional `http-message-signatures`
extension adds RFC 9421: `registrationUrl` (required), `signatureSchemes` (required, e.g.
`["ed25519","ecdsa-p256-sha256","rsa-pss-sha512"]`), `tags` (e.g.
`["web-bot-auth","agent-browser-auth"]`). Client MUST *"Host their public keys at
`/.well-known/http-message-signatures-directory`"* and register with the network. **Same convergence
point as UCP/Visa/Mastercard.**

### 4.4 ⭐ Dispute / liability — our prior finding CONFIRMED, and slightly worse than stated

Grepped v1 spec, v2 spec, all three v2 transports, both schemes, the facilitator/402/client-server
docs, and the FAQ:

| Term | Occurrences |
|---|---|
| `chargeback` | **0** |
| `revocation` / `revoke` | **0** |
| `liabilit` | **0** |
| `reversal` | **0** |
| `arbitrat` | **0** |
| `refund` | **2** — both in the FAQ, none in any spec |
| `dispute` | **2** — both in the optional offer-receipt extension |

The FAQ is the only statement: *"The current `exact` scheme is a push payment—irreversible once
executed."* Options given: *"Business-logic refunds: Seller sends a new USDC transfer back to the
buyer"* and *"Escrow schemes: **Future spec could add** conditional transfers (e.g., HTLCs or hold
invoices)."*

The only evidence machinery is the optional `offer-and-receipt` extension (`format` ∈ `eip712`|`jws`;
Offer payload `version`, `resourceUrl`, `scheme`, `network`, `asset`, `payTo`, `amount`,
`validUntil`; Receipt payload `version`, `network`, `resourceUrl`, `payer`, `issuedAt`,
`transaction`), which claims to support *"dispute evidence and auditability"* — but **defines no
dispute process, no retention, no adjudicator.**

⭐ **Characterization of the gap: this is not an oversight, it is architectural.** x402 settles
on-chain, irreversibly, with no issuer, no acquirer and no scheme rules. **There is no party with
authority to reverse a settled payment, so there is nothing for a refund or chargeback clause to
bind.** Every consumer-protection concept in card commerce — reversal, representment, liability
shift, cardholder dispute rights — is **unrepresentable in the protocol**. Any recourse must be built
above it, and the spec explicitly declines: `Out of Scope: … Client-side budget management; Session
handling mechanisms.`

---

## 5. Card networks: Visa TAP and Mastercard Agent Pay

Both are **agent-authentication + credential-issuance protocols. Neither defines any product catalog
or cart schema at the merchant boundary.**

### 5.1 Visa Trusted Agent Protocol — merchant spec fully public, no login

`developer.visa.com/capabilities/trusted-agent-protocol/trusted-agent-protocol-specifications`;
samples `github.com/visa/trusted-agent-protocol`.

**No merchant API.** TAP is verification applied to the merchant's existing HTTP surface at two
hardcoded points: **product detail page and checkout page**. Merchant work: read two headers, fetch a
key, rebuild a signature base, optionally parse two body objects. *"Verification can be performed
independently by the Merchant or by a Site Protection Provider on behalf of the Merchant."*

**RFC 9421**, *"aligned with web-bot-auth"* (their spelling: "RCF 9421"). Only `Signature-Input` +
`Signature` (label `sig2`). Required params: `@authority`, `@path`, `created`, `expires`, `keyId`,
`alg`, `nonce`, `tag`. ⚠️ Covered components are **only `("@authority" "@path")`** — **method and
body are not signed.** Algorithms `Ed25519`, `PS256`.

⭐ **`tag` is the intent discriminator:** `agent-browser-auth` (browse) vs `agent-payer-auth`
(checkout). *"If the header does not contain a message signature with a `Signature-Input` field
containing a tag of either `agent-browser-auth` or `agent-payer-auth`, the message has not been
signed by a trusted agent."* Freshness: `created`↔`expires` *"should not be more than 8 minutes
apart"*; nonce cache 8 minutes.

Key discovery: **`https://mcp.visa.com/.well-known/jwks` is live, HTTP 200** — but currently serves a
single RSA key from "Visa Sandbox Issuing CA" for CN `vic-oauth-jwe.visa.com`. ⚠️ **A sandbox key,
not a production agent directory.** No public registry endpoint; the GitHub sample's
`POST /agents/register` is localhost demo code and **diverges from the spec** (consumes
`Signature-Agent`, which appears nowhere in the published spec, and references non-standard
`directory-agent` components) — **do not treat as normative.**

Consumer recognition is a separate body object `agenticConsumer{nonce, idToken, contextualData, kid,
alg, signature}`, chained to the header signature by reusing the same key and nonce. `idToken` is a
Visa-signed JWT, `typ: JWT+ext.id_token`, PS256 preferred, `None` unsupported; claims
`iss/sub/aud/exp/iat/jti/auth_time/amr` plus **hashed** `phone_number`, `email` and
`phone_number_mask`/`email_mask`. Merchant consequence, quoted: *"must also maintain a mapping table
that can be used to match a hashed phone number or hashed email address to an actual phone number or
email address of their account holder."*

Payment container `agenticPaymentContainer{nonce, kid, alg, signature}` + one of:
`paymentCredentialsHash` (guest form-fill; *"If the hashes do not match, the information being key
entered is most likely fraudulent and the Merchant should decline"*), `payload`
(merchant-public-key-encrypted `Token{paymentToken, expirationMonth, expirationYear, cardholderName,
dynamicData}` + addresses), or `browsingIOU{invoiceId, amount, cardAcceptorId, acquirerId, uri,
sequenceCounter, paymentService, kid, alg, signature}` for `402` paywalls.

⭐ **The mandate is network-side and invisible to the merchant.** VIC: `POST /vacp/v1/instructions`,
`PUT .../{id}`, **`PUT .../{id}/cancel` ← revocation exists here**, `POST .../{id}/credentials`,
`POST .../{id}/confirmations`. Mandate fields: `mandateId`, `preferredMerchantName`,
`merchantCategory`, `merchantCategoryCode`, `declineThreshold{amount,currencyCode}`,
`effectiveUntilTime`, `quantity`, `description`, `recurringFrequency`. Consent via `assuranceData[]`
+ `consumerPrompt`; passkey authentication.

⚠️ **Dispute/liability: TAP IS SILENT — zero occurrences of `dispute`, `chargeback`, `liabilit`,
`reason code`, `refund` in the published spec.** Product Terms are `AS IS`/`AT YOUR OWN RISK` with
the merchant *"solely responsible for… all disclosures to, and collecting any consents."* VIC
gestures at evidence via the `confirmations` endpoint (`responseCode`, `authorizationCode`,
`retrievalReferenceNumber`, `systemTraceAuditNumber`, `cardEntryMode: 'ECOMMERCE'`) — but that is
**evidence held by Visa, sent by the agent, not a merchant retention rule.**

**ISO 8583 / network flags: not published.** Only: *"When authorization requests are received by
VisaNet, controls will be enforce[d] to ensure that the request originates from the intended merchant
for the correct amount."* No DE numbers, no POS-entry-mode value, no agentic indicator. **VIC
documentation is gated** — *"Visa Intelligent Commerce is a restricted product"* — so the agent-side
signature-generation guide is not publicly readable.

### 5.2 Mastercard Agent Pay — ⚠️ the spec is not published at all

A hard finding, not an inference. Six independent checks:
1. `developer.mastercard.com/llms.txt` (512KB, **1,139** product entries): `"Agent Pay"` → **0**,
   `agent-pay` → **0**, `agentpay` → **0**
2. `/agent-pay/documentation/` and `/product/agent-pay` both redirect to portal root
3. `/mastercard-checkout-solutions/documentation/use-cases/agent-pay/index.md` — the link
   Mastercard's own guide gives — returns **404**
4. No agent-pay repo in the `Mastercard` GitHub org
5. Every technical section deflects to the "Agent Pay Acceptance Framework", whose URL returns
   **403 Akamai**
6. `agentpay-key-directory.mastercard.com` — the `Signature-Agent` host in Mastercard's own example —
   **does not resolve**

**Not a login wall. Simply unpublished.** Everything below is from the one public machine-readable
Mastercard-authored source, the Merchant Cloud "Agentic Commerce Guide", which self-labels its scheme
content as *"based on publicly available information from payment networks. Subject to change."*

Web Bot Auth over RFC 9421, with `Signature-Agent` present (unlike Visa). `tag="Agent-pay-auth"` —
⚠️ **capital A, single tag, so no browse/pay intent discriminator.** Same ≤480s window. Its wire
example **reuses Visa's literal `keyid`/`nonce`/`signature` values** — field names likely right,
literal values not. Identity object: `{mastercardIdToken, signature, kid, nonce, alg}`; *"compatible
with OpenID Connect (OIDC) ID Token specifications… aligns with EMVCo Secure Remote Commerce"* —
**individual claims not published.** Payment: `{paymentData, signature, kid, nonce, alg}` carrying a
**DSRP cryptogram** (an existing Mastercard primitive rebound, not a new credential type).

⭐ Mastercard's genuine differentiator is the **Intent API**, whose intent object *is* transmitted to
the merchant: `Intent{intentId, intentSummary, intentStatus, orders, consumer,
digitalAccountCredentials}`; `Order{orderId, orderExecutionType (IMMEDIATE|DEFERRED), orderStatus,
orderExpiry, orderTotalAmount, items, merchants, orderDeliveryDetails}`; `Item{itemId, itemName,
itemDescription, itemUnitPrice, itemQuantity, itemDeliveryMethod, itemUrl, itemImageUrl,
itemMetadata}`; `Merchant{srcDpaId, merchantName, merchantUrl, merchantLogoUrl}`. Prescribed merchant
validation: verify signature, `intentStatus == ACTIVE`, not expired, your `srcDpaId` matches;
**reject** if total > `orderTotalAmount`; **flag for review** if SKUs, quantities, shipping address or
timeframe differ. Endpoints unpublished; no revocation endpoint.

⭐⭐ **Dispute/liability — the most quotable material in the landscape, and the answer is "nothing
has changed":**

> *"Mastercard and Visa have confirmed that existing dispute frameworks and chargeback rules apply to
> agentic commerce transactions. However, the industry increasingly recognizes that current
> frameworks — designed for human-initiated purchases — are not fully adequate for agent-mediated
> transactions. Payment networks are actively developing agentic-specific dispute protocols, and
> merchants should expect rule enhancements as the ecosystem matures."*

`reason code` → **0 hits. No agentic chargeback reason code exists in either program.** The only
liability shift anywhere is **American Express**, not Visa or Mastercard: *"Agent Purchase
Protection… covers eligible cardmembers against losses resulting from agent error when using
registered AI agents"* — and it protects the **cardmember**, shifting merchant risk only as a side
effect. Evidence retention is **recommended, never mandated**, with a self-labelled "conceptual"
structure (`orderId`, `transactionTimestamp`, `agentIdentity{keyId, platform, signatureAgent, tag}`,
`consumerIdentity{…}`, `signatureProof{nonce, signatureInput, paymentContainerHash}`).

⭐ The burden it places on the merchant, **with no scheme rule backing it**: *"you must prove not just
that the transaction was authorized, but that **the agent acted within the consumer's delegated
authority**."*

---

## 6. Web Bot Auth — the IETF layer everything converges on

⚠️ **Our earlier note that it is "an individual Internet-Draft, not WG-adopted" is now stale. There
is a chartered WG (`webbotauth`) and the document is WG-adopted.**

| Draft | Status |
|---|---|
| `draft-meunier-web-bot-auth-architecture-05` (2026-03-02) | Replaced |
| `draft-meunier-webbotauth-httpsig-directory-00` (2026-06-26) | Replaced |
| `draft-meunier-webbotauth-httpsig-protocol-02` (2026-08-18) | Replaced |
| **`draft-ietf-webbotauth-httpsig-protocol-00`** | **Current, WG Document, intended Standards Track** |

"HTTP Message Signatures for automated traffic", published **1 Sept 2026**, expires **5 Mar 2027**,
44 pages, Thibault Meunier (Cloudflare) + Sandor Major (Google). **The `draft-ietf-` prefix is the
load-bearing detail.**
https://datatracker.ietf.org/doc/html/draft-ietf-webbotauth-httpsig-protocol-00

Headers `Signature`, `Signature-Input`, `Signature-Agent` (Dictionary carrying discovery URLs), plus
`Content-Digest` (RFC 9530) and `Accept-Signature`. Required params `created`, `expires`, `keyid`
(base64url JWK SHA-256 thumbprint), `tag`; **`tag` MUST be the literal `web-bot-auth`**. Covered
components: at least one of `@authority`/`@target-uri`, plus `Signature-Agent` as a named component.
Algorithms **not mandated** — deferred to the RFC 9421 registry (`ed25519`, `rsa-pss-sha512`
illustrated); *"Implementations MUST NOT use shared HMAC"*. Discovery:
`/.well-known/http-message-signatures-directory`, media type
`application/http-message-signatures-directory+json`, JWKS content; modes `directory` (default),
`jwks_uri`, `cimd`.

⭐⭐ **Its stated silences are emphatic and are the crux of our build question.** It does not
authenticate human users, does not define authorization or delegation, does not define how trust is
accrued or exchanged, and defines no mechanism for one origin to convey an opinion about an agent to
another. On revocation: **"It is not a revocation mechanism."** Nothing on intent, spend limits, or
payment — those are *"deployment policy."* **It is a pure "who is this client" primitive.**

The registry that would carry agent metadata — `draft-meunier-webbotauth-registry-03`, defining a
"Signature Agent Card" with identity/purpose/rate expectations under a `web_bot_auth` object reusing
OAuth client metadata — is an **individual submission, NOT WG-adopted**, expiring 28 Dec 2026. It has
**no revocation mechanism either**, only webhook change-notification on add/remove.

Deployments named in the draft: Cloudflare (MV3 extension, Workers, Caddy plugin, Apache module),
Stytch, PHP Guzzle, Python scrapy/crawl4ai, Ruby Linzer, HUMAN Security. ⚠️ **Visa TAP and Shopify are
not mentioned in the draft** despite both profiling it.

---

## 7. Shopify (now UCP, not Storefront MCP)

⚠️ **The Storefront MCP surface is largely deprecated.** Catalog tools flipped 22 Apr 2026;
`get_cart`/`update_cart` deprecated 24 Jun 2026 with legacy support ending **31 Aug 2026**. Current
endpoint: **`https://{shop-domain}/api/ucp/mcp`** (JSON-RPC 2.0 over POST). Legacy
`https://{shop}.myshopify.com/api/mcp` retains only `search_shop_policies_and_faqs`.

Tools: `search_catalog`, `lookup_catalog`, `get_product` (`dev.ucp` catalog v2026-04-08);
`create_cart`, `get_cart`, `update_cart` (**PUT semantics — send the complete `line_items` array
every time**), `cancel_cart`; `create_checkout`, `get_checkout`, `update_checkout`,
`complete_checkout`, `cancel_checkout`. `meta["idempotency-key"]` required for
`complete_checkout`/`cancel_checkout`. All tiers must send `meta["ucp-agent"].profile`.

⭐ **Checkout does not complete in-MCP for general partners** — returns `status:
requires_escalation` + `continue_url` to the merchant storefront; **merchant stays merchant of
record.** Three auth tiers: **Token** (`Authorization: Bearer`, JWT via `client_credentials` at
`api.shopify.com/auth/access_token`) → may `complete_checkout` with permission; **Signed** (RFC 9421
with **ECDSA P-256**, key in `/.well-known/ucp`) → may not; **Anonymous** → may not.

⚠️ Note the divergence: Shopify's signed tier is RFC 9421 with **P-256 and keys at
`/.well-known/ucp`**, *not* Web Bot Auth's `/.well-known/http-message-signatures-directory` +
`tag="web-bot-auth"`. **Same RFC, an incompatible profile of it.** Shopify's agent docs mention
**neither ACP, AP2, nor Web Bot Auth.**

---

## 8. Indian primitives — UPI Reserve Pay

Confirmed against Razorpay's own docs
(`razorpay.com/docs/payments/recurring-payments/upi-reserve-pay/`): *"Maximum block amount ₹10,000"*,
*"Token validity Up to 90 days"*, *"Debits per token Multiple (until blocked amount is exhausted or
token expires)"*.

⚠️ **There is no NPCI-published field-level spec.** Field names are PSP-proprietary and differ per
PSP. Cashfree's SBMD binding, for illustration: `POST /pg/subscriptions` with
`subscription_meta.category = "SBMD"`, `plan_details.plan_max_amount`,
`authorization_details.authorization_amount`, `subscription_expiry_time`;
`POST /pg/subscriptions/pay` with `payment_type ∈ {AUTH, CHARGE}`, `payment_amount`,
`payment_schedule_date`; release via `POST /pg/subscriptions/{id}/manage` with `action: "CANCEL"`
(*"Only `CANCEL` is supported for SBMD to release unused blocked funds"*); webhooks
`SUBSCRIPTION_AUTH_STATUS`, `SUBSCRIPTION_PAYMENT_SUCCESS`, `SUBSCRIPTION_PAYMENT_FAILED`,
`SUBSCRIPTION_STATUS_CHANGED`.

⭐⭐ **Consequence for portability:** Reserve Pay is **the only primitive here with a bank-enforced
limit** — the cap is held in the payer's account, not in a token an agent presents. **Everything else
in this brief enforces limits in software held by the party that benefits from ignoring them.**

---

## 9. ⭐⭐ THE KEY DELIVERABLE — field-level comparison

### 9.1 Catalog / product schema

| Concept | ACP `schema.feed.json` | UCP `product.json`/`variant.json` | AP2 `ap2/types/item.json` | x402 | Reserve Pay |
|---|---|---|---|---|---|
| Product id | `Product.id` **req** | `Product.id` **req** (GID) | `Item.id` **req** | — | — |
| Variant id | `Variant.id` **req** | `Variant.id` **req** (*"Used as `item.id` in checkout"*) | — (no variant concept) | — | — |
| Title | `Product.title` opt / `Variant.title` **req** | `Product.title` **req** / `Variant.title` **req** | `Item.title` **req** | `ResourceInfo.description` opt | — |
| Description | `Description{plain,html,markdown}` | `description` **req on both** | — | — | — |
| Price | `Price{amount,currency}` both **req** | `price_range` **req** (Product), `price` **req** (Variant) | `Item.price` **req** (integer minor units, **no currency!**) | `amount` + `asset` **req** | `plan_max_amount` (PSP-specific) |
| Currency | `Price.currency` **req** | on `price`/`price_range` | ⚠️ **absent from `Item`** — inherited from `Checkout.currency` | `asset` = contract address or ISO 4217 | INR implicit |
| List/compare price | `Variant.list_price` | `list_price_range`, `list_price` | — | — | — |
| Unit price | `UnitPrice{amount,currency,measure{value,unit},reference{value,unit}}` all **req** | `unit_price`, `quantity_unit` | — | — | — |
| Images | `Media{type,url,alt_text,width,height}` | `media[]` → `common/types/media.json` | `Item.image_url` opt (**single**) | — | — |
| Stock/availability | `Availability{available, status}` | `Availability{available, status}` — **identical shape** | — | — | — |
| Category | `Category{value, taxonomy}` | `Category{value, taxonomy}` — **identical shape** | — | — | — |
| SKU / barcode | `Barcode{type,value}` | `sku`, `barcodes[]{type,value}` | — | — | — |
| Variant options | `VariantOption{name,value}` | `options[]`, `variant.options[]` | — | — | — |
| Condition | `Condition` (string array) | — | — | — | — |
| Seller/marketplace | `Seller{name,links[]}`, `Variant.marketplace` | `variant.seller{name,links[]}` | `Checkout.merchant` (AP2 extension) | `payTo` (address) | — |
| Rating | — | `rating{value,scale_max,count}` | — | — | — |
| Handle/slug | — | `handle` | — | — | — |
| Tags | `LineItem.tags` (checkout only) | `tags[]` on both | — | — | — |
| Arbitrary metadata | `LineItem.custom_attributes[]{display_name,value}` | `metadata` object on both | — | `extra` object | — |
| **Feed transport** | **`POST /feeds` + `PATCH /feeds/{id}/products`, or `metadata.json` + `products.jsonl`** | **none — pull-only via `POST /catalog/search\|lookup\|product`** | none | none | none |

### 9.2 Authorization model

| Concept | ACP `Allowance` | AP2 constraints | UCP | x402 | Visa VIC mandate | MC Intent | Reserve Pay |
|---|---|---|---|---|---|---|---|
| Credential format | opaque token id | **SD-JWT VC** + KB-JWT | AP2 SD-JWT (opt) + **JWS detached** merchant sig | EIP-712 / EIP-3009 sig | Visa-signed JWT + passkey | signed intent object | **bank-side block** |
| Amount cap | `max_amount` **req** | `payment.amount_range{max,min}` | **none of its own** | `authorization.value` / `upto` max | `declineThreshold{amount,currencyCode}` | `orderTotalAmount` | **₹10,000 hard cap** |
| Cumulative budget | — | **`payment.budget{max,currency}`** | — | — | — | — | blocked amount |
| Currency | `currency` **req** | in `amount_range` | — | `asset` | `currencyCode` | — | INR |
| Merchant scope | `merchant_id` **req** (single) | **`payment.allowed_payees[]`**, `checkout.allowed_merchants[]` (**sets**) | `mandate_scope_mismatch` = wrong checkout | `payTo` (single address) | `preferredMerchantName` | `srcDpaId` | one block per merchant |
| Category scope | — | — | — | — | **`merchantCategoryCode`** | — | — |
| Item scope | — | **`checkout.line_items[]{acceptable_items[], quantity}`** | — | — | `quantity`, `description` | `items[]` reconciliation | — |
| Instrument scope | — | `payment.allowed_payment_instruments[]`, `payment.allowed_pisps[]` | — | — | — | — | — |
| TTL / expiry | `expires_at` **req** | `exp`, `payment.execution_date{not_before,not_after}` | `expires_at` (6h default); `mandate_expired` | `validAfter`/`validBefore` | `effectiveUntilTime` | `orderExpiry` | 90 days |
| Recurrence | `reason: "one_time"` **only** | **`payment.agent_recurrence{frequency, max_occurrences}`** | — | — | `recurringFrequency` | `orderExecutionType` | multi-debit until exhausted |
| Session binding | `checkout_session_id` **req** | `checkout_hash` → `transaction_id` | `binding{type,id}`; JCS over checkout | `nonce` | instruction id | `intentId` | subscription id |
| **Revocation** | **none** | **none** (zero occurrences of "revoke") | key rotation; OAuth RFC 7009 for **sessions only** | **none** | **`PUT /vacp/v1/instructions/{id}/cancel`** | `intentStatus` (no endpoint) | **`action:"CANCEL"` releases funds** |
| Replay defence | `Idempotency-Key` | `sd_hash` + `cnf` PoP | `Idempotency-Key`, fail-closed 503 | `nonce` (32B) | `nonce` + 8-min window | `nonce` | bank ledger |
| Extensibility | closed enums | **open `type` + "unknown MUST fail evaluation"** | reverse-DNS capabilities | `scheme`/`extensions` | closed | closed | closed |

### 9.3 What maps cleanly, and what CANNOT be losslessly mapped

**Maps cleanly — safe to translate:**
- ACP `Availability{available,status}` ↔ UCP `Availability{available,status}` — same names, same
  open-vocabulary status values
- ACP `Category{value,taxonomy}` ↔ UCP `Category{value,taxonomy}` — same well-known taxonomies
- ACP `Barcode{type,value}` ↔ UCP `barcodes[]{type,value}`
- ACP `Media{type,url,alt_text,…}` ↔ UCP `media[]`
- **All four commerce protocols use integer minor currency units** — no scaling errors
- ACP `Total[]` ↔ UCP `totals[]` — same array-of-typed-totals design, both requiring exactly one
  `subtotal` and one `total`
- ⭐ ACP `LineItem{id,item,quantity,totals}` ↔ UCP `LineItem{id,item,quantity,totals}` —
  **byte-identical required sets**, both with `parent_id` for bundles. **Not coincidence; the two were
  aligned.**
- Checkout status: ACP's 11-value enum is a **superset** of UCP's 6. ACP→UCP is lossy; UCP→ACP is clean
- Agent identity: UCP ↔ Visa TAP ↔ Mastercard ↔ x402-with-extension all sit on RFC 9421. **One
  Ed25519 keypair can serve all four** — but see caveat 7

**CANNOT be losslessly mapped — specific fields:**

1. **ACP's entire feed push has no UCP counterpart.** `POST /feeds`,
   `PATCH /feeds/{id}/products`, `FeedMetadata{id,target_country,updated_at}`, `products.jsonl` — UCP
   is **pull-only**. There is no UCP field to receive a feed into. Conversely UCP's `Product.handle`,
   `rating{value,scale_max,count}`, `price_range`/`list_price_range` (**ranges, not scalars**) have
   **no ACP field**: ACP has scalar `Variant.price`, so a UCP product spanning multiple variant prices
   **flattens and loses the range**.
2. ⚠️ **AP2's `Item` is a four-field stub.** `{id, title, price, image_url}` — mapping ACP or UCP into
   it **destroys** `sku`, `barcodes`, `categories`, `availability`, `variant_options`, `unit_price`,
   `condition`, `media[]` (collapses to one `image_url`), `tags`, `seller`, `rating`, `description`.
   And **`Item.price` carries no currency field** — currency lives only on the enclosing
   `Checkout.currency`, so **an item is meaningless outside its checkout**. **Any "signed cart" built
   on AP2 signs a drastically reduced view of the cart.**
3. **ACP `Allowance` cannot express any AP2 constraint but `amount_range`.** No ACP field for
   `payment.budget`, `payment.agent_recurrence` (`reason` is single-valued `"one_time"`),
   `payment.allowed_payees[]` (ACP has scalar `merchant_id` — **a set of allowed merchants is
   unrepresentable**), `checkout.line_items[]{acceptable_items[]}` (no ACP field for "one of these
   SKUs"), `payment.allowed_payment_instruments[]`, `payment.execution_date{not_before}` (ACP has only
   `expires_at`, **no start bound**). **AP2→ACP loses every constraint but the cap and the deadline.**
4. **Reverse: ACP→AP2 loses `checkout_session_id`'s semantics.** AP2's binding is a **cryptographic
   hash of the merchant-signed checkout**; ACP's is an **opaque server-side identifier**. An ACP
   allowance proves **nothing about cart contents**; an AP2 mandate proves **exactly what the user
   saw**. Not the same field wearing different names, and **no lossless direction exists**.
5. **x402 has no field for anything above amount+address+deadline.** No merchant identity beyond
   `payTo`, no line items, no categories, no buyer, no order, no refund. Mapping *into* x402 discards
   essentially the entire commerce object; mapping *out*, you cannot reconstruct what was bought —
   only `resourceUrl`.
6. ⭐ **Card-network mandates are invisible to the merchant, by design.** Visa's `declineThreshold` and
   `merchantCategoryCode` are set by the **consumer** into a **Visa-held** mandate and **never
   transmitted to the merchant**. There is no merchant-side field to read them. Mastercard's Intent
   object *is* transmitted (`orderTotalAmount`, `orderExpiry`, `items[]`) — making Mastercard the
   **only** program giving the merchant machine-checkable consumer limits — **but its endpoints and
   claim names are unpublished, so you cannot build against it today.**
7. ⚠️ **The RFC 9421 convergence is real but the profiles are mutually incompatible at the `tag` and
   covered-components level.** `tag` values: `web-bot-auth` (IETF, MUST),
   `agent-browser-auth`/`agent-payer-auth` (Visa), `Agent-pay-auth` (Mastercard, **capital A — a
   case-sensitive match matters**). Covered components: Visa signs only `("@authority" "@path")`; UCP
   requires `@method`+`@authority`+`@path` plus up to six more. Key discovery paths:
   `/.well-known/http-message-signatures-directory` (IETF/x402), `/.well-known/ucp` (UCP, Shopify),
   `mcp.visa.com/.well-known/jwks` (Visa). Algorithms: Ed25519 (IETF/Visa), **ECDSA P-256** (Shopify's
   signed tier). **One signature cannot satisfy Visa and Shopify simultaneously**; UCP's
   "dual-audience" trick covers only UCP+WBA.
8. ⭐ **Reserve Pay cannot be mapped into any of them, in either direction.** Its limit is enforced by
   the payer's **bank**, against a **blocked balance**, with a **statutory** ₹10,000 / 90-day /
   one-merchant ceiling. **No protocol here has a field for "funds are already sequestered at the
   issuer".** Conversely, none of Reserve Pay's constraints are expressible as an AP2 constraint or an
   ACP `Allowance`: `one block per merchant` and `max 3 retries/24h` have **no counterpart field
   anywhere**, and UPI Circle's `max 5 secondaries` has no analogue in any delegation model here (AP2
   explicitly puts agent-to-agent delegation *"outside the scope of the current specification"*).

---

## 10. Developer tooling — shipped vs TODO

| Protocol | Shipped | Explicitly missing / TODO |
|---|---|---|
| **ACP** | 7 OpenAPI docs + 7 JSON Schemas (2026-04-17), OpenRPC binding, 16 RFCs, worked examples incl. `examples.mcp.agentic_checkout.json`, `examples.multi_item_checkout.json`, order examples (refunded/partial/digital/shipped), consistency-validation CI. Stripe CLI `stripe agent setup`. | **No reference SDK in the repo.** No signing helper. `IntentTrace`, feed-`update_id`, `suggested-pricing`, `fulfillment-details-on-complete` sit in `changelog/unreleased/`. Out of scope: *"PSP authorization/capture semantics, returns/exchanges workflows, tax configuration, fraud modeling details"*; *"multi-use tokens beyond allowance, refund semantics"*; *"Product or catalog discovery… is out of scope"* (of discovery). |
| **AP2** | Python SDK (`ap2.sdk`) with generated Pydantic models, **`constraints.py` reference evaluators**, `checkout_mandate_chain.py` verifier, JSON Schemas, Go sample agents, **Android sample with Digital Payment Credentials**, x402 and card scenarios, human-present + human-not-present runnable flows, sample SD-JWT certs. | **No revocation anything.** No mandate-retrieval API (*"outside the scope of the current version"*). No dispute retention/retrieval rules. Agent-to-agent delegation out of scope. Depends on **`Delegate SD-JWT`, an individual draft** (`github.com/GarethCOliver/gco-delegate-sd-jwt`) — **a non-IETF dependency in the normative references.** Mandate-selection logic *"an implementation detail… outside the scope"*. |
| **UCP** | `ucp` spec repo (3,353★), `python-sdk` (PyPI `ucp-sdk`, Pydantic), `js-sdk` (TS + Zod), **`conformance` suite** (language-agnostic integration tests against a running merchant), `ucp-schema` Rust validator, `samples`, `llms.txt`, playground. | Both SDKs are **type generators only — no signing helper, no mandate builder, no RFC 9421 client.** Literal `* TODO: discuss continue_url destination - cart vs checkout` in the shipped cart spec. Lodging/Food verticals *"coming soon"*. Wallet attestation reserved. WBA freshness enforcement *"application-defined"*. Google-side: quantity adjustments *"coming soon"*, Cart API *"limited to cart creation and transfer"*, risk signals *"may return an empty string or null"* in MVP, `/merchant/ucp/reference` **404s**, `/guides/tools/code-samples` an empty stub, error-code table ships with **three blank rows**. |
| **x402** | Large multi-language SDK matrix: npm `@x402/{core,evm,svm,avm,aptos,stellar,express,hono,fastify,next,fetch,axios,mcp,paywall,extensions}`, PyPI `x402`, Go, Java; audited EVM contracts (`cantina_x402_feb2026.pdf`), Permit2 proxies, e2e conformance harness across 8 clients and 3 facilitators, reference facilitators in TS/Go/Python. **By far the best tooling.** | **Everything about recourse.** Escrow: *"Future spec could add conditional transfers (e.g., HTLCs or hold invoices)"*. Out of scope: *"Client-side budget management; Session handling mechanisms"*. |
| **Visa TAP** | Public merchant spec, `github.com/visa/trusted-agent-protocol` sample, `github.com/visa/mcp` with real npm SDKs `@visa/{api-client,mcp-client,token-manager}`, LangGraph demo, docs MCP at `sandbox.mcp.visa.com/mcp/doc`, live JWKS, free sandbox. | **VIC docs gated** (*"restricted product"*) — agent-side signing guide unreadable. **Sample code diverges from spec.** `/keys` service described abstractly; cross-scheme approach only a *"goal"*. Live JWKS serves a **sandbox-CA** key. Page carries *"This product is in the process of development and deployment. Depictions are representations of potential features."* |
| **Mastercard** | **Nothing Agent Pay–specific.** Third-party npm `web-bot-auth` + CDN verification do the work. `Mastercard/developers-agent-toolkit` is a docs-discovery MCP server, not an SDK. | **The entire spec.** No OpenAPI, no schema, no repo, no sandbox. Merchant validation *"currently in development and not mandatory… this section is directional and subject to change"*. 3DS unresolved: *"the authentication attempt typically fails because the agent cannot complete the interactive challenge"*. |
| **Web Bot Auth** | Cloudflare MV3 extension, Workers, Caddy plugin, Apache module, Rust binaries, test server; Stytch, Guzzle, scrapy/crawl4ai, Linzer, HUMAN Security. | Registry (`Signature Agent Card`) is **individual-submission, not WG-adopted**. **Explicitly not a revocation mechanism.** |

---

## 11. ⭐⭐⭐ THE ANSWER TO THE BUILD-DECIDING QUESTION

**Does any protocol define a merchant-side POLICY / RULES layer — merchant-declared rules like
"agents may buy under ₹X, not category Y", agent allowlists, per-agent limits or eligibility?**

> ## No. Not one of them.
> **All nine stop at consent + agent authentication and leave merchant-side decisioning explicitly
> undefined.**

Per protocol, with evidence:

**ACP — No, and it says so.** Three out-of-scope declarations bound it: *"PSP authorization/capture
semantics, returns/exchanges workflows, tax configuration, fraud modeling details"*; *"multi-use
tokens beyond allowance, refund semantics"*; *"Capabilities that vary per merchant… are out of
scope."* `DiscoveryCapabilities.services[]` is advertisement, not policy. The nearest thing to a rule
is **reactive**: `MessageError.code` includes `region_restricted`, `age_verification_required`,
`approval_required`, `maximum_exceeded`, `quantity_exceeded`, and `LineItem.max_quantity_per_order` —
but these are **rejections after the fact**, per-request, **with no declarative form**. `resolution` ∈
`recoverable`|`requires_buyer_input`|`requires_buyer_review` routes the failure; it does not express
the rule. Agent identity is a bearer key, so an ACP merchant's only "allowlist" is which API keys it
issued — **out of band**.

**AP2 — No, and this is the sharpest finding in the brief.** AP2 has the **richest constraint
language in the entire landscape** — and **every constraint is authored by the user, about the agent,
and evaluated by the verifier on the user's behalf.** `checkout.allowed_merchants` is the *user*
saying which merchants the agent may use; **there is no `merchant.allowed_agents`.** Grep for
merchant policy across all AP2 docs returns **zero hits**. The merchant's role is defined purely as a
verification duty (*"MUST verify the Checkout Mandate as follows…"*) with a **binary outcome**
(`CheckoutReceipt` `result: success|error`). The `Mandate Constraints` extension point exists and is
well-specified (*"To define a new constraint… a uniquely defined `type`, a Schema… the evaluation
algorithm"*) — but it is an extension point for **more user-side constraints**. **Nothing in the spec
contemplates the merchant asserting its own.**

**UCP — No, and the spec says so in normative prose.** The single passage addressing merchant access
policy: *"UCP defines best practices that enable permissionless onboarding, but **businesses retain
full control over their access policies and MAY enforce additional rules based on established trust,
observed behavior, or operational requirements.** Businesses SHOULD maintain a registry of
pre-approved platforms — platforms whose profiles have been validated and whose trust is established
through **out-of-band mechanisms**."* **The merchant allowlist is a recommended concept deliberately
placed outside the protocol.**

And the one machine-readable constraint mechanism **cannot express a value limit.**
`ucp.request_constraints` uses a closed JSON Schema subset with `additionalProperties: false`,
admitting exactly `required`, `properties`, `anyOf` (object position) and `enum`, `const` (value
position), plus a JSONPath `path`. ⚠️ **There is no `maximum`, `minimum`, `exclusiveMaximum`,
`multipleOf`, or `pattern`. "Agents may buy under ₹500" is *not expressible*.** It is also the wrong
layer and advisory: *"This preflight is optional and advisory"*; *"Request Constraints add no outcome
or error code"*; *"Passing validation… establishes only schema validity; **the request can still fail
other Business rules**"*; *"**Execution-time conditions such as inventory availability, fraud
decisions, and payment authorization remain governed by the operation's existing outcomes and
`messages`**."*

`policies[]` is buyer-facing reference text (*"A Platform MAY reason over them for its own decisions…
Presenting a policy is optional"*). `dev.ucp.shopping.buyer_consent` covers exactly four purposes —
`marketing`, `analytics`, `preferences`, `sale_or_sharing` — i.e. **GDPR/CCPA consent, not purchase
authorization**. The nearest closed allowlist anywhere is `identity_linking.config.providers` (*"a
business MUST reject a JWT authorization grant whose `iss` does not match a listed `oauth2` mechanism
entry"*) — but it allowlists **upstream identity providers, not purchasing agents**. Escalation via
`severity: "requires_buyer_review"` → `status: requires_escalation` → `continue_url` is a **human
handoff, not a machine-readable rule**. And **UCP's roadmap contains no policy/decisioning layer and
no refund/dispute API.**

**x402 — No, and it is doubly out of scope.** The spec's own Out of Scope list names *"Client-side
budget management"* and *"Session handling mechanisms."* There is no merchant, no buyer identity, no
category — the only merchant-side control is the price in `accepts[]` and the **binary choice to serve
or return 402**. `extensions` is an escape hatch with no policy extension defined.

**Visa TAP — No, and it hands the decision back as prose.** The two sentences defining the whole
boundary: *"The Merchant may decide to block the message or use some other mechanism to determine
whether the interaction can continue."* And: *"Based on this validation the Merchant can allow the
interaction to continue while still potentially limiting the interaction to these specific steps."*
**No schema, no declaration format, no per-agent limits, no allowlist mechanism, no category rules.**
Note the direction of the constraints that *do* exist: `declineThreshold` and `merchantCategoryCode`
are set by the **consumer** into a **Visa-held** mandate and are **never shown to the merchant**.

**Mastercard Agent Pay — No.** Searches: `merchant-declared` → 0, `spend cap` → 0, `per-agent` → 0,
`allow-list` → 0, `allowlist` → 1 (and that hit **dismisses** IP allowlisting as inadequate). What it
offers instead is **editorial advice**: a five-row trust spectrum (Certified / Platform-Identified /
Consumer-Owned / Anonymous / Malicious → Full access · Standard · Standard · Higher friction + rate
limiting · Block) that is *"a recommendation table, not a schema"*, with generic CNP measures. Its
stated philosophy is explicitly **anti-gate**: *"The goal is not to verify every agent before allowing
access — it is to let purchase intent flow freely while applying proportional security at the point of
transaction."* The one machine-checkable merchant decision either network specifies is Mastercard's
**intent-vs-cart reconciliation** — and even that is the merchant checking the **consumer's**
constraints, not asserting its own.

**Web Bot Auth — No, and it refuses on principle.** It defines no authorization, no delegation, and
*"no mechanism for one origin to convey an opinion about an agent to another."* Merchant-side policy is
*"deployment policy"* by explicit deferral.

**Shopify — Partially, and it is the only "yes" in the landscape — but it is a product surface, not a
protocol.** Real controls exist: **Settings > Sales channels > Agentic** in admin lets merchants choose
which AI channels (ChatGPT, Google AI Mode, Copilot, Meta) may access products and control
direct-checkout options; the three auth tiers *are* the enforcement mechanism; and `complete_checkout`
is gated on **negotiated per-partner capabilities**, i.e. a bilateral allowlist. But **no
merchant-declared spend limits, category restrictions, or agent-specific pricing** were found in
first-party docs. **It is per-channel on/off in an admin UI, not a declarative rules layer, and none of
it is in the spec.**

**Reserve Pay / UPI Circle — No, and note the asymmetry.** The ₹10,000 cap, 90-day validity,
one-block-per-merchant and 3-retries/24h are **regulator-imposed on the payer's bank**, and Circle's
₹15,000 monthly / ₹5,000 per-payment / 5-secondaries likewise. **Nothing lets a *merchant* declare
"agents may spend up to X here".** The limits protect the payer, are enforced by the issuer, and are
**invisible and unconfigurable to the merchant.**

### ⭐⭐⭐ The shape of the gap, stated precisely

Every protocol surveyed answers two questions and **refuses a third**:

1. **"Is this agent who it claims to be?"** — **answered**, converging hard on RFC 9421 / Web Bot Auth
   (UCP, Visa, Mastercard, x402-extension, Shopify's signed tier). ACP alone dissents with bearer tokens.
2. **"Did a human authorize this, and within what limits?"** — **answered**, best by AP2's constraint
   vocabulary, weakest by UCP's baseline (an unverified `buyer.email`) and x402 (nothing above an amount).
3. **"Given a verified agent carrying valid user authorization, will *this merchant* sell *this thing*
   to *this agent* on *these terms*?"** — **UNANSWERED BY EVERY SINGLE ONE.** Four of them say so in
   normative prose (UCP, Visa, ACP's out-of-scope lists, Mastercard's advisory table). **None offers a
   schema.** UCP's `request_constraints` is the only attempt at a declarative rule grammar and it
   **structurally cannot express a number.**

### Two corollaries to carry into the build

- ⭐ **Direction is the invariant.** Every limit primitive in existence — AP2 `constraints`, ACP
  `Allowance`, Visa `declineThreshold`, Mastercard `orderTotalAmount`, Reserve Pay's block — is
  authored by or for the **payer**, and constrains the **agent**. **There is no field in any spec whose
  author is the merchant and whose subject is the agent.** That asymmetry is the gap, and it is uniform.
- ⭐ **Revocation is the second uniform gap, and it is worse than the policy gap.** AP2: zero
  occurrences of the word. ACP: no endpoint, expiry only. x402: zero occurrences. UCP: key rotation and
  OAuth session revocation, **neither of which reaches a mandate**. Web Bot Auth: *"It is not a
  revocation mechanism."* **Only Visa VIC (`PUT /instructions/{id}/cancel`) and Reserve Pay
  (`action: "CANCEL"`) can actually kill a live authorization** — and both are held by the payment
  network or the bank, **not by the merchant, and not by the user's agent.**
