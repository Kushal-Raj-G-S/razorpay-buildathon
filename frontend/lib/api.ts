const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

// This dashboard manages ONE demo merchant. In a real multi-merchant
// product this key would come from a login, not an env var -- but the
// backend endpoint it's checked against (app/auth.py) is the same one
// a real merchant login would sit in front of.
const MERCHANT_API_KEY = process.env.NEXT_PUBLIC_MERCHANT_API_KEY || "";

export type RuleResult = {
  rule_name: string;
  passed: boolean;
  detail: string;
};

export type ReceiptCartItem = {
  id: string;
  title: string;
  price: number;
  category: string | null;
  quantity: number;
  listed?: boolean;
};

export type Receipt = {
  cart_id: string;
  merchant_id: string;
  agent_id: string;
  decision: "allow" | "block" | "escalate";
  rules_checked: RuleResult[];
  cart_total: number;
  timestamp: string;
  signature: string | null;
  // What was actually in the cart -- "what did this agent buy" was
  // previously invisible past the total in rupees. Always present from
  // GET /receipts (list_receipts_with_items); absent nowhere it's used.
  cart_items?: ReceiptCartItem[];
};

export type Policy = {
  merchant_id: string;
  max_order_value: number;
  deny_categories: string[];
  // Non-empty means "only these categories" (a whitelist) -- for a
  // large catalog where naming every banned category by hand doesn't
  // scale. Empty (the default) means no allow-list restriction at all.
  allow_categories: string[];
  max_units_per_sku: number;
  escalate_above: number | null;
  require_signed_identity: boolean;
  allow_cod_for_agents: boolean;
  max_orders_per_agent_per_window: number | null;
  velocity_window_minutes: number;
};

export const MERCHANT_ID = "shop_123";

async function request<T>(path: string, options?: RequestInit, authed = false): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (authed) {
    if (!MERCHANT_API_KEY) {
      throw new Error(
        "No merchant API key configured. Register via POST /merchants/register and set " +
          "NEXT_PUBLIC_MERCHANT_API_KEY in frontend/.env.local"
      );
    }
    headers["Authorization"] = `Bearer ${MERCHANT_API_KEY}`;
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: { ...headers, ...(options?.headers || {}) },
  });
  if (!res.ok) {
    // FastAPI error bodies are JSON like {"detail": "..."} -- every error
    // across the whole app used to show that raw, braces and all
    // ("Failed: 503: {\"detail\":\"...\"}"), which is exactly what a
    // merchant saw live when a real Razorpay 429 hit the escalation
    // review endpoint. Unwrap it when it parses; fall back to the raw
    // text untouched otherwise, since not every error body is JSON.
    const bodyText = await res.text();
    let detail = bodyText;
    try {
      const parsed = JSON.parse(bodyText);
      if (parsed && typeof parsed.detail === "string") detail = parsed.detail;
    } catch {
      // not JSON -- use the raw text as-is
    }
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json();
}

// ---------- Merchant account ----------

export function registerMerchant(merchantId: string) {
  return request<{ merchant_id: string; api_key: string; warning: string }>(`/merchants/register`, {
    method: "POST",
    body: JSON.stringify({ merchant_id: merchantId }),
  });
}

// ---------- Policy (write requires the merchant's key; read does not) ----------

export function getPolicy(merchantId: string) {
  return request<Policy>(`/policy/${merchantId}`);
}

export function savePolicy(policy: Policy) {
  return request<{ status: string }>(
    `/policy`,
    { method: "POST", body: JSON.stringify(policy) },
    true
  );
}

export type PolicyHistoryEntry = {
  id: number;
  saved_at: string;
  policy: Policy;
};

export function getPolicyHistory(merchantId: string) {
  return request<PolicyHistoryEntry[]>(`/policy/${merchantId}/history`, undefined, true);
}

// ---------- Receipts (merchant-only -- it's their business data) ----------

export function listReceipts(merchantId: string) {
  return request<Receipt[]>(`/receipts?merchant_id=${merchantId}`, undefined, true);
}

export type CartItemInput = {
  id: string;
  title: string;
  price: number; // paise
  category: string;
  quantity: number;
};

// ---------- Checkout (public -- this is what a shopping agent calls) ----------

export function tryCheckout(
  merchantId: string,
  agentId: string,
  items: CartItemInput[],
  paymentMode: "prepaid" | "cod" = "prepaid"
) {
  return request<{
    receipt: Receipt;
    payment?: Record<string, unknown>;
    order?: Record<string, unknown>;
    escalation_id?: number;
  }>(`/checkout-sessions`, {
    method: "POST",
    body: JSON.stringify({ merchant_id: merchantId, agent_id: agentId, items, payment_mode: paymentMode }),
  });
}

// ---------- Revocation (merchant-only) ----------

export function revokeAgent(agentId: string, merchantId: string) {
  return request<{ status: string }>(
    `/agents/${agentId}/revoke?merchant_id=${merchantId}`,
    { method: "POST" },
    true
  );
}

export function unrevokeAgent(agentId: string, merchantId: string) {
  return request<{ status: string }>(
    `/agents/${agentId}/unrevoke?merchant_id=${merchantId}`,
    { method: "POST" },
    true
  );
}

// ---------- AI-drafted policy (merchant-only; human must still approve before it applies) ----------

export type PolicyDraft = {
  merchant_id: string;
  max_order_value: number;
  deny_categories: string[];
  allow_categories: string[];
  max_units_per_sku: number;
  escalate_above: number | null;
  require_signed_identity: boolean;
  allow_cod_for_agents: boolean;
  max_orders_per_agent_per_window: number | null;
  velocity_window_minutes: number;
};

export function draftPolicyFromText(merchantId: string, plainEnglish: string) {
  return request<{ draft: PolicyDraft; note: string }>(
    `/policy/draft-from-text`,
    { method: "POST", body: JSON.stringify({ merchant_id: merchantId, plain_english: plainEnglish }) },
    true
  );
}

// ---------- AI catalog ingestion (merchant-only) ----------

export type CatalogVariant = {
  id: string;
  title: string;
  price: number;
  category: string | null;
  available: boolean;
  sku: string | null;
};

export type CatalogProduct = {
  id: string;
  title: string;
  description: string | null;
  variants: CatalogVariant[];
};

// Public -- same endpoint a shopping agent calls to browse. Used here so
// the merchant can see what's already saved, not just what they just
// generated -- reloading this page used to show a blank form with no
// sign a catalog existed at all.
export function searchCatalog(merchantId: string, query: string = "") {
  return request<{ products: CatalogProduct[] }>(
    `/catalog/search?merchant_id=${encodeURIComponent(merchantId)}&query=${encodeURIComponent(query)}`,
    { method: "POST" }
  );
}

// Direct upload (merchant-only) -- used by the "load a matching demo
// catalog" helper on the Try It page. A real merchant would normally
// use catalogFromText or the /catalog page's form instead.
export function uploadCatalog(merchantId: string, products: CatalogProduct[]) {
  return request<{ status: string; product_count: number }>(
    `/catalog`,
    {
      method: "POST",
      body: JSON.stringify({ merchant_id: merchantId, catalog: { merchant_id: merchantId, products } }),
    },
    true
  );
}

export function catalogFromText(merchantId: string, rawText: string) {
  return request<{ status: string; product_count: number; catalog: { products: CatalogProduct[] } }>(
    `/catalog/from-text`,
    { method: "POST", body: JSON.stringify({ merchant_id: merchantId, raw_text: rawText }) },
    true
  );
}

// ---------- Escalations: the human review queue (merchant-only) ----------

export type Escalation = {
  id: number;
  receipt_id: number;
  merchant_id: string;
  agent_id: string;
  cart_items: CartItemInput[];
  cart_total: number;
  status: "pending" | "approved" | "rejected";
  reviewer_note: string | null;
  created_at: string;
  reviewed_at: string | null;
};

export function listEscalations(merchantId: string, status: string = "pending") {
  return request<Escalation[]>(
    `/escalations?merchant_id=${merchantId}&status=${status}`,
    undefined,
    true
  );
}

export function reviewEscalation(escalationId: number, approve: boolean, note?: string) {
  return request<{ escalation: Escalation; payment?: Record<string, unknown> }>(
    `/escalations/${escalationId}/review`,
    { method: "POST", body: JSON.stringify({ approve, note: note || null }) },
    true
  );
}

export type EscalationAdvice = {
  recommendation: "approve" | "reject" | "needs_human_judgment";
  reasoning: string;
  confidence: "low" | "medium" | "high";
};

export function getEscalationAdvice(escalationId: number) {
  return request<{ escalation_id: number; advice: EscalationAdvice }>(
    `/escalations/${escalationId}/advice`,
    undefined,
    true
  );
}

// ---------- Red team: an autonomous AI trying to break your own rules ----------

export type RedTeamRound = {
  round: number;
  reasoning: string;
  items: CartItemInput[];
  resolved_items?: CartItemInput[];
  decision: "allow" | "block" | "escalate" | "gave_up";
  rules_failed: string[];
};

export type RedTeamRun = {
  id?: number;
  run_id?: number;
  merchant_id?: string;
  goal: string;
  outcome: "held" | "breached" | "agent_gave_up" | "max_rounds_reached";
  rounds: RedTeamRound[];
  created_at?: string;
};

export function runRedTeam(merchantId: string, goal: string, maxRounds: number = 5) {
  return request<RedTeamRun>(
    `/red-team/run`,
    { method: "POST", body: JSON.stringify({ merchant_id: merchantId, goal, max_rounds: maxRounds }) },
    true
  );
}

export function listRedTeamRuns(merchantId: string) {
  return request<RedTeamRun[]>(`/red-team/runs?merchant_id=${merchantId}`, undefined, true);
}

// ---------- Digest: "what's actually been happening", not a log to read (merchant-only) ----------

export type DigestFlag = {
  severity: "high" | "medium" | "low";
  agent_id: string;
  flag_type: "catalog_mismatch" | "velocity_cap_hit" | "repeated_blocks";
  count: number;
  detail: string;
};

export type AgentFootprint = {
  agent_id: string;
  attempts: number;
  allowed: number;
  blocked: number;
  escalated: number;
  blocked_rules: Record<string, number>;
  first_seen: string;
  last_seen: string;
  revoked: boolean;
};

export type DigestStats = {
  window_hours: number;
  totals: { attempts: number; allowed: number; blocked: number; escalated: number };
  escalations_pending_or_reviewed: number;
  agents: AgentFootprint[];
  flags: DigestFlag[];
};

export type DigestNarrative = {
  headline: string;
  summary: string;
  flag_explanations: { agent_id: string; plain_english: string }[];
};

export function getDigest(merchantId: string, windowHours: number = 168) {
  return request<{ stats: DigestStats }>(
    `/digest?merchant_id=${merchantId}&window_hours=${windowHours}`,
    undefined,
    true
  );
}

// Separate, slower call on purpose -- GET /digest above returns real
// numbers fast (no AI in it); this narrates them afterward, same pattern
// as getEscalationAdvice.
export function narrateDigest(merchantId: string, stats: DigestStats) {
  return request<{ narrative: DigestNarrative }>(
    `/digest/narrate`,
    { method: "POST", body: JSON.stringify({ merchant_id: merchantId, stats }) },
    true
  );
}
