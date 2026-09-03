const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

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

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options?.headers || {}) },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }
  return res.json();
}

export function getPolicy(merchantId: string) {
  return request<Policy>(`/policy/${merchantId}`);
}

export function savePolicy(policy: Policy) {
  return request<{ status: string }>(`/policy`, {
    method: "POST",
    body: JSON.stringify(policy),
  });
}

export function listReceipts(merchantId: string) {
  return request<Receipt[]>(`/receipts?merchant_id=${merchantId}`);
}

export type CartItemInput = {
  id: string;
  title: string;
  price: number; // paise
  category: string;
  quantity: number;
};

export function tryCheckout(merchantId: string, agentId: string, items: CartItemInput[]) {
  return request<{ receipt: Receipt; payment?: Record<string, unknown> }>(`/checkout-sessions`, {
    method: "POST",
    body: JSON.stringify({ merchant_id: merchantId, agent_id: agentId, items }),
  });
}

export function revokeAgent(agentId: string) {
  return request<{ status: string }>(`/agents/${agentId}/revoke`, { method: "POST" });
}

export function unrevokeAgent(agentId: string) {
  return request<{ status: string }>(`/agents/${agentId}/unrevoke`, { method: "POST" });
}

// ---------- AI-drafted policy (human must approve before it applies) ----------

export type PolicyDraft = {
  merchant_id: string;
  max_order_value: number;
  deny_categories: string[];
  max_units_per_sku: number;
  escalate_above: number | null;
  require_signed_identity: boolean;
};

export function draftPolicyFromText(merchantId: string, plainEnglish: string) {
  return request<{ draft: PolicyDraft; note: string }>(`/policy/draft-from-text`, {
    method: "POST",
    body: JSON.stringify({ merchant_id: merchantId, plain_english: plainEnglish }),
  });
}

// ---------- AI catalog ingestion ----------

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
    { method: "POST", body: JSON.stringify({ merchant_id: merchantId, raw_text: rawText }) }
  );
}

// ---------- Escalations: the human review queue ----------

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
  return request<Escalation[]>(`/escalations?merchant_id=${merchantId}&status=${status}`);
}

export function reviewEscalation(escalationId: number, approve: boolean, note?: string) {
  return request<{ escalation: Escalation; payment?: Record<string, unknown> }>(
    `/escalations/${escalationId}/review`,
    { method: "POST", body: JSON.stringify({ approve, note: note || null }) }
  );
}
