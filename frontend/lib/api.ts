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

export type Receipt = {
  cart_id: string;
  merchant_id: string;
  agent_id: string;
  decision: "allow" | "block" | "escalate";
  rules_checked: RuleResult[];
  cart_total: number;
  timestamp: string;
  signature: string | null;
};

export type Policy = {
  merchant_id: string;
  max_order_value: number;
  deny_categories: string[];
  max_units_per_sku: number;
  escalate_above: number | null;
  require_signed_identity: boolean;
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
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
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

export function tryCheckout(merchantId: string, agentId: string, items: CartItemInput[]) {
  return request<{ receipt: Receipt; payment?: Record<string, unknown> }>(`/checkout-sessions`, {
    method: "POST",
    body: JSON.stringify({ merchant_id: merchantId, agent_id: agentId, items }),
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
  max_units_per_sku: number;
  escalate_above: number | null;
  require_signed_identity: boolean;
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
