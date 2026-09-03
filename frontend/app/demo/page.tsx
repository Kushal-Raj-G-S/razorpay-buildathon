"use client";

import { useState } from "react";
import {
  tryCheckout,
  revokeAgent,
  unrevokeAgent,
  MERCHANT_ID,
  type Receipt,
  type CartItemInput,
} from "@/lib/api";

const AGENT_ID = "shopping-agent-007";

const CLEAN_CART: CartItemInput[] = [
  { id: "shirt", title: "Blue Cotton Shirt L", price: 45000, category: "clothing", quantity: 1 },
];

const POISONED_CART: CartItemInput[] = [
  { id: "shirt", title: "Blue Cotton Shirt L", price: 45000, category: "clothing", quantity: 1 },
  {
    id: "giftcard",
    title: "Rs 2000 Gift Card",
    price: 200000,
    category: "gift_card",
    quantity: 1,
  },
];

const OVER_LIMIT_CART: CartItemInput[] = [
  { id: "jeans", title: "Denim Jeans 32", price: 1500000, category: "clothing", quantity: 1 },
];

function ReceiptCard({ receipt }: { receipt: Receipt }) {
  const color =
    receipt.decision === "allow"
      ? "border-green-300 bg-green-50"
      : receipt.decision === "block"
        ? "border-red-300 bg-red-50"
        : "border-amber-300 bg-amber-50";

  return (
    <div className={`rounded-lg border ${color} p-5 mt-6`}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-lg font-semibold uppercase tracking-wide">
          {receipt.decision}
        </span>
        <span className="text-sm text-zinc-500">
          Rs {(receipt.cart_total / 100).toFixed(2)}
        </span>
      </div>
      <div className="space-y-1 mb-3">
        {receipt.rules_checked.map((r) => (
          <div key={r.rule_name} className="text-sm flex gap-2">
            <span>{r.passed ? "✅" : "❌"}</span>
            <span className="font-medium">{r.rule_name}:</span>
            <span className="text-zinc-600">{r.detail}</span>
          </div>
        ))}
      </div>
      <div className="text-xs text-zinc-400 font-mono break-all">
        signature: {receipt.signature?.slice(0, 32)}…
      </div>
    </div>
  );
}

export default function DemoPage() {
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [error, setError] = useState("");
  const [revoked, setRevoked] = useState(false);
  const [loading, setLoading] = useState(false);

  async function send(cart: CartItemInput[]) {
    setLoading(true);
    setError("");
    try {
      const result = await tryCheckout(MERCHANT_ID, AGENT_ID, cart);
      setReceipt(result.receipt);
    } catch (e) {
      setError((e as Error).message);
      setReceipt(null);
    } finally {
      setLoading(false);
    }
  }

  async function toggleRevoke() {
    if (revoked) {
      await unrevokeAgent(AGENT_ID);
      setRevoked(false);
    } else {
      await revokeAgent(AGENT_ID);
      setRevoked(true);
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-16">
      <h1 className="text-2xl font-semibold mb-2">Pretend you&apos;re an AI agent</h1>
      <p className="text-sm text-zinc-500 mb-8">
        Pick a cart below. This sends it to the backend exactly like a real shopping agent would,
        and the bouncer decides in real time.{" "}
        <a href="/policy" className="underline">
          Make sure you&apos;ve saved rules first.
        </a>
      </p>

      <div className="flex flex-wrap gap-3 mb-4">
        <button
          onClick={() => send(CLEAN_CART)}
          disabled={loading}
          className="rounded bg-white border border-zinc-300 px-4 py-2 text-sm hover:border-zinc-500"
        >
          Send a clean cart
        </button>
        <button
          onClick={() => send(POISONED_CART)}
          disabled={loading}
          className="rounded bg-white border border-zinc-300 px-4 py-2 text-sm hover:border-zinc-500"
        >
          Send a poisoned cart (hidden gift card)
        </button>
        <button
          onClick={() => send(OVER_LIMIT_CART)}
          disabled={loading}
          className="rounded bg-white border border-zinc-300 px-4 py-2 text-sm hover:border-zinc-500"
        >
          Send an over-limit cart
        </button>
      </div>

      <button
        onClick={toggleRevoke}
        className={`rounded px-4 py-2 text-sm font-medium ${
          revoked ? "bg-green-600 text-white" : "bg-red-600 text-white"
        }`}
      >
        {revoked ? "Un-revoke this agent" : "Revoke this agent right now"}
      </button>

      {error && <p className="text-sm text-red-600 mt-4">{error}</p>}
      {receipt && <ReceiptCard receipt={receipt} />}
    </div>
  );
}
