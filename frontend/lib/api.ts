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
